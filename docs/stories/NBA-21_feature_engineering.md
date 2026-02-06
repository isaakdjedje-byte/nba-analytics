---
Story: NBA-21
Epic: Data Processing & Transformation (NBA-7)
Points: 8
Statut: To Do
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
---

# 🎯 NBA-21: Feature engineering pour ML

## 📋 Description

Créer les features historiques, de forme et de matchup nécessaires pour les modèles de prédiction.

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-20** : Matchs transformés
- ✅ **NBA-18** : Métriques avancées

### Bloque:
- ⬜ **NBA-22** : Modèle ML

## 📥📤 Entrées/Sorties

### Entrées:
- **`data/silver/games_processed/`** : Matchs structurés
- **`data/silver/players_advanced/`** : Stats joueurs

### Sorties:
- **`data/gold/ml_features/`** : Dataset ML final avec features

## ✅ Critères d'acceptation

### 1. Features historiques calculées (moyennes glissantes)

```python
from pyspark.sql.window import Window
from pyspark.sql.functions import avg, lag, row_number

def calculate_historical_features():
    """Calculer moyennes glissantes sur 5/10/20 derniers matchs"""
    
    df = spark.read.format("delta").load("data/silver/games_processed/")
    
    # Window functions par équipe
    window_5 = (Window
        .partitionBy("team_id")
        .orderBy("game_date")
        .rowsBetween(-4, 0))
    
    window_10 = (Window
        .partitionBy("team_id")
        .orderBy("game_date")
        .rowsBetween(-9, 0))
    
    window_20 = (Window
        .partitionBy("team_id")
        .orderBy("game_date")
        .rowsBetween(-19, 0))
    
    df_features = (df
        .withColumn("avg_pts_last_5", avg("pts").over(window_5))
        .withColumn("avg_pts_last_10", avg("pts").over(window_10))
        .withColumn("avg_pts_last_20", avg("pts").over(window_20))
        .withColumn("avg_reb_last_5", avg("reb").over(window_5))
        .withColumn("avg_ast_last_5", avg("ast").over(window_5))
        .withColumn("win_rate_last_5", avg(when(col("winner") == "home", 1.0).otherwise(0.0)).over(window_5))
    )
    
    return df_features
```

---

### 2. Features de forme (last 5 games)

```python
def calculate_form_features():
    """Calculer forme récente équipe"""
    
    df = calculate_historical_features()
    
    df_form = (df
        .withColumn("form_trend", col("avg_pts_last_5") - col("avg_pts_last_20"))
        .withColumn("is_hot", col("win_rate_last_5") > 0.7)
        .withColumn("is_struggling", col("win_rate_last_5") < 0.3)
    )
    
    return df_form
```

---

### 3. Features de matchup (face-à-face)

```python
def calculate_matchup_features():
    """Calculer historique face-à-face entre 2 équipes"""
    
    df = spark.read.format("delta").load("data/silver/games_processed/")
    
    # Historique H2H
    h2h_stats = (df
        .groupBy("home_team_id", "away_team_id")
        .agg(
            count("*").alias("h2h_games"),
            avg(when(col("winner") == "home", 1.0).otherwise(0.0)).alias("h2h_home_win_rate"),
            avg(abs(col("point_diff"))).alias("h2h_avg_margin")
        )
    )
    
    return h2h_stats
```

---

### 4. Dataset ML final

```python
def create_ml_dataset():
    """Créer dataset final ML avec toutes les features"""
    
    df = calculate_form_features()
    h2h = calculate_matchup_features()
    
    # Merge toutes les features
    df_ml = (df
        .join(h2h, ["home_team_id", "away_team_id"], "left")
        .withColumn("target", when(col("winner") == "home", 1).otherwise(0))
    )
    
    # Sélectionner features finales
    feature_cols = [
        "home_avg_pts_last_5", "home_avg_pts_last_10", "home_avg_pts_last_20",
        "away_avg_pts_last_5", "away_avg_pts_last_10", "away_avg_pts_last_20",
        "home_win_rate_last_5", "away_win_rate_last_5",
        "home_form_trend", "away_form_trend",
        "h2h_home_win_rate", "h2h_avg_margin",
        "days_since_last_game_home", "days_since_last_game_away",
        "is_back_to_back_home", "is_back_to_back_away",
        "target"
    ]
    
    df_final = df_ml.select(*feature_cols)
    
    # Sauvegarder
    df_final.write \
        .format("delta") \
        .mode("overwrite") \
        .save("data/gold/ml_features/")
    
    return df_final
```

## Features créées:

| Feature | Description | Type |
|---------|-------------|------|
| `avg_pts_last_5/10/20` | Moyenne points | Float |
| `win_rate_last_5` | Taux victoire | Float |
| `form_trend` | Tendance vs moyenne | Float |
| `h2h_home_win_rate` | Win rate historique H2H | Float |
| `days_since_last_game` | Jours repos | Int |
| `is_back_to_back` | Match consécutif | Boolean |
| `target` | 1=home win, 0=away win | Int |

## 📦 Livrables

- ✅ `src/processing/feature_engineering.py`
- ✅ `data/gold/ml_features/`
- ✅ `docs/FEATURES.md` (documentation features)

## 🎯 Definition of Done

- [ ] Features historiques calculées (5/10/20 matchs)
- [ ] Features forme créées (trend, hot/struggling)
- [ ] Features H2H calculées
- [ ] Dataset ML complet avec 15+ features
- [ ] Pas de fuite de données future (leakage)
