---
Story: NBA-29
Epic: Reporting & Visualization (NBA-10)
Points: 3
Statut: To Do
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
---

# 🎯 NBA-29: Export des données pour BI

## 📋 Description

Créer des exports dans formats compatibles outils BI (Parquet, CSV) avec documentation des schémas et partitions optimisées.

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-19** : Agrégations
- ✅ **NBA-21** : Features ML

## ✅ Critères d'acceptation

### 1. Export Parquet créé dans data/gold/

```python
def export_to_parquet():
    """Exporter données au format Parquet"""
    
    # Lire données Gold
    df_teams = spark.read.format("delta").load("data/gold/team_stats_season/")
    df_players = spark.read.format("delta").load("data/silver/players_advanced/")
    
    # Export Parquet optimisé
    (df_teams.write
        .format("parquet")
        .mode("overwrite")
        .partitionBy("season")
        .option("compression", "snappy")
        .save("data/exports/team_stats.parquet"))
    
    (df_players.write
        .format("parquet")
        .mode("overwrite")
        .partitionBy("season", "is_active")
        .option("compression", "snappy")
        .save("data/exports/player_stats.parquet"))
    
    print("✅ Exports Parquet créés")
```

---

### 2. Export CSV créé avec headers

```python
def export_to_csv():
    """Exporter données au format CSV"""
    
    # Export CSV avec headers
    (df_teams.write
        .format("csv")
        .mode("overwrite")
        .option("header", "true")
        .option("delimiter", ",")
        .save("data/exports/team_stats.csv"))
    
    print("✅ Exports CSV créés")
```

---

### 3. Documentation des schémas (data dictionary)

**docs/DATA_DICTIONARY.md:**
```markdown
# Data Dictionary

## Table: team_stats

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| team_id | int | Identifiant équipe | 1610612747 |
| team_name | string | Nom équipe | Lakers |
| season | string | Saison | 2023-24 |
| avg_pts_scored | double | Points moyens | 114.5 |
| avg_reb | double | Rebonds moyens | 43.2 |
| ... | ... | ... | ... |

## Table: player_stats

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | int | Identifiant joueur | 2544 |
| full_name | string | Nom joueur | LeBron James |
| per | double | Player Efficiency Rating | 28.5 |
| ts_pct | double | True Shooting % | 0.629 |
| ... | ... | ... | ... |
```

---

### 4. Partitions optimisées pour requêtes

**Stratégie de partitionnement:**
```python
# Parquet partitionné
/partitioned_data/
├── season=2018-19/
│   └── part-00001.snappy.parquet
├── season=2019-20/
│   └── part-00001.snappy.parquet
...

# Avantage: Requêtes filtrées par saison très rapides
```

## 📦 Livrables

- ✅ `src/reporting/export_bi.py`
- ✅ `data/exports/team_stats.parquet`
- ✅ `data/exports/player_stats.parquet`
- ✅ `data/exports/*.csv`
- ✅ `docs/DATA_DICTIONARY.md`

## 🎯 Definition of Done

- [ ] Exports Parquet créés (compressés Snappy)
- [ ] Exports CSV créés avec headers
- [ ] Data dictionary documenté
- [ ] Partitions optimisées (par saison)
