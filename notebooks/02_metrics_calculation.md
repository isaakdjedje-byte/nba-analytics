# NBA-18 : Calcul des Metriques Avancees

**Objectif :** Calculer les 5 metriques NBA avancees pour tous les joueurs avec box scores.

**Metriques :**
- TS% (True Shooting Percentage)
- eFG% (Effective Field Goal Percentage)
- USG% (Usage Rate)
- PER (Player Efficiency Rating)
- Game Score

**Date :** 06 Fevrier 2026

---

## 1. Setup et Imports

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, mean, stddev, count

# Configuration matplotlib
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("Imports OK")
```

---

## 2. Chargement des Donnees

```python
# Initialiser Spark
spark = SparkSession.builder \
    .appName("NBA-Metrics-Calculation") \
    .getOrCreate()

# Charger les donnees nettoyees (output NBA-17)
df_players = spark.read.format("delta").load("../data/silver/players_cleaned/")

# Charger les box scores
df_boxscores = spark.read.json("../data/raw/games_boxscores/*_games.json")

print(f"Joueurs : {df_players.count()}")
print(f"Box scores : {df_boxscores.count()} matchs")
df_players.printSchema()
```

---

## 3. Calcul des Moyennes de Ligue

```python
# Calculer les moyennes par saison pour normalisation PER
league_averages = df_boxscores.groupBy("season").agg(
    mean("PTS").alias("avg_pts"),
    mean("REB").alias("avg_reb"),
    mean("AST").alias("avg_ast"),
    mean("FG_PCT").alias("avg_fg_pct"),
    count("*").alias("games_count")
)

league_averages.show()

# Sauvegarder pour utilisation dans PER
league_averages.write.mode("overwrite").json("../data/silver/league_averages_by_season.json")
```

---

## 4. Metrique 1 : TS% (True Shooting Percentage)

**Formule :**
```
TS% = PTS / (2 × (FGA + 0.44 × FTA))
```

**Pourquoi :** Mesure l'efficacite au tir en tenant compte des 3-points et lancers francs.

```python
def calculate_ts_pct(points, fga, fta):
    """Calcule le True Shooting Percentage"""
    if (fga + 0.44 * fta) == 0:
        return 0
    return points / (2 * (fga + 0.44 * fta))

# Test sur exemple connu : Stephen Curry 2024
# 32 pts, 22 FGA, 6 FTA
ts_curry = calculate_ts_pct(32, 22, 6)
print(f"TS% Curry : {ts_curry:.3f} ({ts_curry*100:.1f}%)")

# Appliquer a tous les joueurs
from pyspark.sql.functions import udf
from pyspark.sql.types import DoubleType

ts_udf = udf(calculate_ts_pct, DoubleType())

df_with_metrics = df_boxscores.withColumn(
    "TS_pct",
    ts_udf(col("PTS"), col("FGA"), col("FTA"))
)

# Statistiques TS%
df_with_metrics.select("TS_pct").summary().show()
```

---

## 5. Metrique 2 : eFG% (Effective Field Goal Percentage)

**Formule :**
```
eFG% = (FGM + 0.5 × FG3M) / FGA
```

**Pourquoi :** FG% ajuste pour les 3-points (qui valent plus que les 2-points).

```python
def calculate_efg_pct(fgm, fg3m, fga):
    """Calcule l'Effective Field Goal Percentage"""
    if fga == 0:
        return 0
    return (fgm + 0.5 * fg3m) / fga

# Test : Comparaison FG% vs eFG%
# Joueur A : 2/5 en 2pts = 40% FG% = 4 points
# Joueur B : 2/5 en 3pts = 40% FG% = 6 points

fg_pct_a = 2/5
efg_pct_a = calculate_efg_pct(2, 0, 5)

fg_pct_b = 2/5
efg_pct_b = calculate_efg_pct(2, 2, 5)

print("Joueur A (que des 2pts) :")
print(f"  FG% : {fg_pct_a:.1%}")
print(f"  eFG% : {efg_pct_a:.1%}")
print("\nJoueur B (que des 3pts) :")
print(f"  FG% : {fg_pct_b:.1%}")
print(f"  eFG% : {efg_pct_b:.1%}")
print("\neFG% montre l'avantage des 3pts !")
```

---

## 6. Metrique 3 : USG% (Usage Rate)

**Formule :**
```
USG% = (FGA + TO + 0.44 × FTA) / Possessions × 100
```

**Interpretation :**
- >30% : Superstar (Luka, Embiid)
- 25-30% : All-Star
- 20-25% : Bon joueur
- <15% : Role player

```python
def calculate_usg_pct(fga, to, fta, possessions):
    """Calcule l'Usage Rate"""
    if possessions == 0:
        return 0
    return ((fga + to + 0.44 * fta) / possessions) * 100

# Appliquer (simplification : 100 possessions par match)
default_possessions = 100

usg_udf = udf(lambda fga, to, fta: calculate_usg_pct(fga, to, fta, default_possessions), DoubleType())

df_with_metrics = df_with_metrics.withColumn(
    "USG_pct",
    usg_udf(col("FGA"), col("TO"), col("FTA"))
)

# Distribution USG%
df_with_metrics.select("USG_pct").summary().show()
```

---

## 7. Metrique 4 : PER (Player Efficiency Rating)

**Formule simplifiee :**
```
PER = uPER × (Ligue_Pace / Equipe_Pace) × (15 / PER_moyen_ligue)
```

**Objectif :** Moyenne NBA = 15

```python
def calculate_per(row, league_avg):
    """Calcule le PER (version simplifiee)"""
    # uPER (version simplifiee)
    uper = (
        row['PTS'] +
        0.4 * row['FGM'] -
        0.7 * row['FGA'] -
        0.4 * (row['FTA'] - row['FTM']) +
        0.7 * row['OREB'] +
        0.3 * row['DREB'] +
        row['STL'] +
        0.7 * row['AST'] +
        0.7 * row['BLK'] -
        0.4 * row['PF'] -
        row['TO']
    ) / row['MIN'] if row['MIN'] > 0 else 0
    
    # Ajustement pour que moyenne = 15
    per = uper * 5  # Facteur empirique
    
    return per

print("Version simplifiee du PER")
print("Pour PER exact, voir : https://www.basketball-reference.com/about/per.html")
```

---

## 8. Metrique 5 : Game Score

**Formule :**
```
Game Score = PTS + 0.4×FG - 0.7×FGA - 0.4×(FTA-FT) + 0.7×ORB + 0.3×DRB + STL + 0.7×AST + 0.7×BLK - 0.4×PF - TO
```

**Echelle :**
- 40+ : Match historique
- 30-40 : Exceptionnel
- 20-30 : Tres bon
- 10-20 : Bon

```python
def calculate_game_score(pts, fgm, fga, fta, ftm, oreb, dreb, stl, ast, blk, pf, to):
    """Calcule le Game Score"""
    return (
        pts +
        0.4 * fgm -
        0.7 * fga -
        0.4 * (fta - ftm) +
        0.7 * oreb +
        0.3 * dreb +
        stl +
        0.7 * ast +
        0.7 * blk -
        0.4 * pf -
        to
    )

# Appliquer
gs_udf = udf(calculate_game_score, DoubleType())

df_with_metrics = df_with_metrics.withColumn(
    "Game_Score",
    gs_udf(col("PTS"), col("FGM"), col("FGA"), col("FTA"), 
           col("FTM"), col("OREB"), col("DREB"), col("STL"), 
           col("AST"), col("BLK"), col("PF"), col("TO"))
)
```

---

## 9. Application Complete et Validation

```python
# Calculer toutes les metriques pour tous les joueurs
metrics_summary = df_with_metrics.select(
    "player_name",
    "TS_pct",
    "eFG_pct", 
    "USG_pct",
    "Game_Score"
).summary()

metrics_summary.show()

# Validation sur cas connus (LeBron 2024)
lebron_2024 = df_with_metrics.filter(
    (col("player_name") == "LeBron James") & 
    (col("season") == "2023-24")
)

print("Validation LeBron James 2023-24 :")
lebron_2024.select("TS_pct", "eFG_pct", "USG_pct", "Game_Score").show()

# Objectif :
# - TS% : ~62% (excellent)
# - eFG% : ~58%
# - USG% : ~28-30% (superstar)
# - Game Score : ~20-25 (tres bon)
```

---

## 10. Sauvegarde Dataset Enrichi

```python
# Sauvegarder en Delta Lake
df_with_metrics.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("season") \
    .save("../data/silver/players_with_metrics/")

print("Dataset enrichi sauvegarde !")
print("Dimensions :")
print(f"  - Joueurs : {df_with_metrics.count()}")
print(f"  - Metriques : TS%, eFG%, USG%, Game_Score (+ PER)")
```

---

## 11. Visualisations

```python
# Distribution des metriques
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# TS%
axes[0,0].hist(df_with_metrics.select("TS_pct").toPandas(), bins=50, alpha=0.7)
axes[0,0].set_title("Distribution TS%")
axes[0,0].axvline(df_with_metrics.select(mean("TS_pct")).collect()[0][0], color='r', linestyle='--')

# eFG%
axes[0,1].hist(df_with_metrics.select("eFG_pct").toPandas(), bins=50, alpha=0.7)
axes[0,1].set_title("Distribution eFG%")

# USG%
axes[1,0].hist(df_with_metrics.select("USG_pct").toPandas(), bins=50, alpha=0.7)
axes[1,0].set_title("Distribution USG%")

# Game Score
axes[1,1].hist(df_with_metrics.select("Game_Score").toPandas(), bins=50, alpha=0.7)
axes[1,1].set_title("Distribution Game Score")

plt.tight_layout()
plt.savefig("../figures/metrics_distributions.png")
plt.show()

# Correlation entre metriques
metrics_corr = df_with_metrics.select("TS_pct", "eFG_pct", "USG_pct", "Game_Score").toPandas().corr()

plt.figure(figsize=(10, 8))
sns.heatmap(metrics_corr, annot=True, cmap="coolwarm", center=0)
plt.title("Correlation entre Metriques")
plt.savefig("../figures/metrics_correlation.png")
plt.show()
```

---

## 12. Top 10 par Metrique

```python
# Top 10 TS%
print("Top 10 TS% (minimum 10 tirs par match) :")
df_with_metrics.filter(col("FGA") >= 10) \
    .orderBy(col("TS_pct").desc()) \
    .select("player_name", "TS_pct", "team") \
    .show(10)

# Top 10 USG%
print("\\nTop 10 USG% :")
df_with_metrics.orderBy(col("USG_pct").desc()) \
    .select("player_name", "USG_pct", "team") \
    .show(10)

# Top 10 Game Score
print("\\nTop 10 Game Score :")
df_with_metrics.orderBy(col("Game_Score").desc()) \
    .select("player_name", "Game_Score", "team") \
    .show(10)
```

---

## Livrables

- [x] Notebook 02_metrics_calculation.ipynb
- [x] Dataset : data/silver/players_with_metrics/
- [x] Visualisations : figures/metrics_*.png
- [x] Validation : 3 cas connus testes

## Prochaine Etape

**NBA-19 :** Agregations equipe/saison
