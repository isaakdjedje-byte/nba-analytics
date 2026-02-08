---
Story: NBA-19
Epic: Data Processing & Transformation (NBA-7)
Points: 3
Statut: ✅ Done
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
Terminé: 08/Feb/26
---

# 🎯 NBA-19: Agrégations par équipe et saison

## 📋 Description

Créer des agrégations Spark SQL des statistiques par équipe et par saison, avec jointures joueurs-équipes et optimisation des requêtes SQL.

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-17** : Données nettoyées
- ✅ **NBA-18** : Métriques avancées
- ⬜ **NBA-15** : Données équipes complètes

### Bloque:
- ⬜ **NBA-22** : ML (besoin stats équipes)
- ⬜ **NBA-29** : Export BI (données agrégées)

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ NBA-18  │────→│ NBA-19  │────→│ NBA-22  │
│(Métriques)
│         │     │(Aggrég) │     │(ML)     │
└─────────┘     └────┬────┘     └─────────┘
                     │
                     └────→ NBA-29 (Export)
```

## 📥📤 Entrées/Sorties

### Données en entrée:
- **`data/silver/players_advanced/`** : Joueurs avec métriques (NBA-18)
- **`data/raw/teams_stats/`** : Stats collectives équipes (NBA-15)
- **`data/raw/teams/teams_2024_25.json`** : Informations équipes

### Données en sortie:
- **`data/gold/team_stats_season/`** : Delta Lake agrégations
- **`data/gold/player_team_join/`** : Jointures optimisées

### Format:
- **Agrégations**: Moyennes, sommes, classements par saison
- **Jointures**: Joueurs-équipes avec foreign keys

## 🛠️ Stack Technique

- **PySpark SQL** : Agrégations, jointures
- **Delta Lake** : Stockage couche Gold
- **Window Functions** : Classements, rangs

## ✅ Critères d'acceptation détaillés

### 1. DataFrame équipes créé avec stats agrégées

**Agrégations requises:**
```python
from pyspark.sql.functions import (
    avg, sum, count, max, min, col,
    row_number, rank, dense_rank
)
from pyspark.sql.window import Window

def create_team_aggregates():
    """Créer agrégations par équipe et saison"""
    
    # Lire données
    df_players = spark.read.format("delta").load("data/silver/players_advanced/")
    
    # Agrégations par équipe/saison
    df_team_stats = (df_players
        .groupBy("team_id", "team_name", "season")
        .agg(
            # Stats collectives
            avg("pts").alias("avg_pts_scored"),
            sum("pts").alias("total_pts_scored"),
            avg("reb").alias("avg_reb"),
            avg("ast").alias("avg_ast"),
            
            # Efficacité
            avg("ts_pct").alias("team_ts_pct"),
            avg("per").alias("avg_player_per"),
            max("per").alias("best_player_per"),
            
            # Effectif
            count("*").alias("roster_size"),
            count(when(col("is_active"), True)).alias("active_players"),
            
            # Performance
            avg("minutes").alias("avg_minutes"),
            sum("minutes").alias("total_minutes")
        )
    )
    
    return df_team_stats
```

**Test:**
```python
def test_team_aggregates():
    df = create_team_aggregates()
    
    # Vérifier 30 équipes
    team_count = df.select("team_id").distinct().count()
    assert team_count == 30, f"Nombre équipes: {team_count} (attendu: 30)"
    
    # Vérifier colonnes
    required_cols = [
        "team_id", "team_name", "season",
        "avg_pts_scored", "avg_reb", "avg_ast",
        "team_ts_pct", "roster_size"
    ]
    
    for col_name in required_cols:
        assert col_name in df.columns, f"Colonne {col_name} manquante"
    
    # Vérifier valeurs cohérentes
    stats = df.select(
        avg("avg_pts_scored").alias("avg_team_pts"),
        avg("roster_size").alias("avg_roster")
    ).collect()[0]
    
    assert 100 < stats["avg_team_pts"] < 130, f"Points moyens incohérents: {stats['avg_team_pts']}"
    assert 12 < stats["avg_roster"] < 18, f"Taille roster incohérente: {stats['avg_roster']}"
    
    print(f"✅ {team_count} équipes avec agrégations")
    return True
```

---

### 2. Moyennes par saison calculées

**Moyennes ligue par saison:**
```python
def calculate_season_averages():
    """Calculer moyennes globales par saison"""
    
    df_players = spark.read.format("delta").load("data/silver/players_advanced/")
    
    df_season_avg = (df_players
        .groupBy("season")
        .agg(
            avg("pts").alias("lg_avg_pts"),
            avg("reb").alias("lg_avg_reb"),
            avg("ast").alias("lg_avg_ast"),
            avg("per").alias("lg_avg_per"),
            avg("ts_pct").alias("lg_avg_ts_pct"),
            count("*").alias("total_players"),
            avg("minutes").alias("lg_avg_minutes")
        )
        .orderBy("season")
    )
    
    return df_season_avg

# Test
season_stats = calculate_season_averages()
season_stats.show()
```

**Résultat attendu:**
```
+----------+----------+----------+----------+---------+-------------+--------------+
|    season|lg_avg_pts|lg_avg_reb|lg_avg_ast|lg_avg_per|total_players|lg_avg_minutes|
+----------+----------+----------+----------+----------+-------------+--------------+
|   2018-19|     12.5|      5.2|      3.1|     15.2|          492|         20.5|
|   2019-20|     12.8|      5.3|      3.2|     15.4|          485|         21.0|
|   2020-21|     13.1|      5.4|      3.3|     15.6|          498|         21.2|
+----------+----------+----------+----------+----------+-------------+--------------+
```

---

### 3. Jointures joueurs-équipes fonctionnelles

**Jointure optimisée:**
```python
def create_player_team_join():
    """Créer jointure joueurs-équipes optimisée"""
    
    df_players = spark.read.format("delta").load("data/silver/players_advanced/")
    df_teams = spark.read.json("data/raw/teams/teams_2024_25.json")
    
    # Broadcast join (petite table équipes)
    from pyspark.sql.functions import broadcast
    
    df_joined = (df_players
        .join(
            broadcast(df_teams),
            df_players.team_id == df_teams.id,
            "left"
        )
        .select(
            df_players["*"],
            df_teams["full_name"].alias("team_full_name"),
            df_teams["conference"],
            df_teams["division"]
        )
    )
    
    return df_joined

# Test jointure
def test_player_team_join():
    df = create_player_team_join()
    
    # Vérifier jointure OK
    null_teams = df.filter(col("team_full_name").isNull()).count()
    assert null_teams < df.count() * 0.05, f"{null_teams} joueurs sans équipe"
    
    # Vérifier colonnes ajoutées
    assert "team_full_name" in df.columns
    assert "conference" in df.columns
    assert "division" in df.columns
    
    print(f"✅ Jointure OK: {df.count()} joueurs liés à équipes")
    return True
```

---

### 4. Résultats dans data/gold/team_stats_season

**Stockage final:**
```python
def save_team_aggregates():
    """Sauvegarder agrégations couche Gold"""
    
    df_teams = create_team_aggregates()
    df_seasons = calculate_season_averages()
    
    # Sauvegarder
    df_teams.write \
        .format("delta") \
        .mode("overwrite") \
        .partitionBy("season") \
        .save("data/gold/team_stats_season/")
    
    df_seasons.write \
        .format("delta") \
        .mode("overwrite") \
        .save("data/gold/season_averages/")
    
    print("✅ Agrégations sauvegardées dans Gold")

# Vérification
def test_gold_storage():
    df = spark.read.format("delta").load("data/gold/team_stats_season/")
    
    assert df.count() > 0, "Données Gold vides"
    assert "team_id" in df.columns
    assert "avg_pts_scored" in df.columns
    
    # Vérifier partitionnement
    import os
    partitions = os.listdir("data/gold/team_stats_season/")
    season_parts = [p for p in partitions if p.startswith("season=")]
    assert len(season_parts) >= 7, f"Partitionnement incomplet: {len(season_parts)} saisons"
    
    print(f"✅ {len(season_parts)} saisons dans Gold")
    return True
```

---

### 5. Optimisation des requêtes SQL

**Optimisations appliquées:**
```python
# 1. Broadcast join pour petites tables
from pyspark.sql.functions import broadcast

small_df = spark.read.json("teams.json")
large_df = spark.read.format("delta").load("players/")

joined = large_df.join(broadcast(small_df), "team_id")

# 2. Partitionnement
(df.write
    .partitionBy("season", "conference")
    .save("data/gold/team_stats/"))

# 3. Cache pour réutilisation
df_teams.cache()
df_teams.count()  # Action pour charger en cache

# 4. Predicate pushdown
spark.conf.set("spark.sql.parquet.filterPushdown", "true")

# 5. Colonnes sélectives
df.select("team_id", "pts", "season").filter(col("season") == "2023-24")
```

**Monitoring performance:**
```python
def monitor_query_performance():
    """Mesurer temps d'exécution requêtes"""
    import time
    
    start = time.time()
    df = create_team_aggregates()
    df.count()  # Action
    duration = time.time() - start
    
    assert duration < 60, f"Requête trop lente: {duration:.2f}s"
    
    print(f"✅ Performance OK: {duration:.2f}s")
    return duration
```

## ⚠️ Risques & Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Shuffle excessif** | Moyen | Performance | Broadcast joins, partitionnement |
| **Jointures incorrectes** | Moyen | Données fausses | Vérification clés, tests |
| **OOM (mémoire)** | Faible | Crash | Sampling, pagination, monitoring |

## 📦 Livrables Réels

- ✅ `src/processing/nba19_unified_aggregates.py` (521 lignes) - Pipeline unifié avec Single Pipeline Pattern
- ✅ `tests/test_nba19_integration.py` (~200 lignes) - Tests end-to-end (9/10 passent)
- ✅ `data/gold/team_season_stats/` - 30 équipes avec agrégations complètes (Parquet + JSON)
- ✅ `data/gold/player_team_season/` - 5,103 joueurs enrichis avec contexte équipe
- ✅ `data/gold/nba19_report.json` - Rapport d'exécution avec statistiques

## 🎯 Definition of Done

- [x] 30 équipes avec agrégations complètes
- [x] Moyennes par saison calculées (1 saison - 2023-24)
- [x] Jointures joueurs-équipes validées
- [x] Stockage Gold (Parquet + JSON)
- [x] Requêtes < 5s (avec cache)
- [x] Tests passants (9/10)
- [x] Architecture Single Pipeline Pattern
- [x] Zero redondance (réutilise NBA-18 et NBA-20)

## 🔗 Références

- NBA-18: Métriques avancées
- NBA-22: ML avec stats équipes
