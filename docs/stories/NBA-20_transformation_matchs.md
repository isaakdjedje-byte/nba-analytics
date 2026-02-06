---
Story: NBA-20
Epic: Data Processing & Transformation (NBA-7)
Points: 5
Statut: To Do
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
---

# 🎯 NBA-20: Transformation des données matchs

## 📋 Description

Transformer les données brutes des matchs en format analytique structuré, prêt pour le machine learning, avec calcul des écarts de score et identification home/away.

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-15** : Données matchs brutes
- ✅ **NBA-19** : Stats équipes

### Bloque:
- ⬜ **NBA-21** : Feature engineering
- ⬜ **NBA-22** : ML prédiction

## 📥📤 Entrées/Sorties

### Entrées:
- **`data/raw/games_detailed/`** : Box scores matchs
- **`data/gold/team_stats_season/`** : Stats équipes

### Sorties:
- **`data/silver/games_processed/`** : Matchs structurés pour ML

## ✅ Critères d'acceptation

### 1. Stats par match structurées

**Structure du DataFrame:**
```python
game_schema = {
    "game_id": "string",
    "season": "string",
    "game_date": "date",
    "home_team_id": "int",
    "away_team_id": "int",
    "home_team_name": "string",
    "away_team_name": "string",
    "home_score": "int",
    "away_score": "int",
    "winner": "string",  # 'home' ou 'away'
    "point_diff": "int",
    "overtime": "boolean",
    "is_playoff": "boolean"
}
```

**Script:**
```python
def transform_games():
    """Transformer box scores en matchs structurés"""
    
    # Lire box scores
    df_games = spark.read.json("data/raw/games_detailed/*.json")
    
    # Structurer
    df_structured = (df_games
        .select(
            col("GAME_ID").alias("game_id"),
            col("SEASON_ID").alias("season"),
            to_date(col("GAME_DATE"), "yyyy-MM-dd").alias("game_date"),
            col("TEAM_ID_HOME").alias("home_team_id"),
            col("TEAM_ID_AWAY").alias("away_team_id"),
            col("PTS_HOME").alias("home_score"),
            col("PTS_AWAY").alias("away_score"),
            col("GAME_STATUS_TEXT").alias("status")
        )
        .withColumn("point_diff", col("home_score") - col("away_score"))
        .withColumn("winner",
            when(col("point_diff") > 0, lit("home"))
            .when(col("point_diff") < 0, lit("away"))
            .otherwise(lit("tie"))
        )
        .withColumn("overtime", col("status").contains("OT"))
    )
    
    return df_structured
```

---

### 2. Calcul des écarts de score

```python
def calculate_score_diffs():
    """Calculer statistiques écarts"""
    
    df = transform_games()
    
    stats = (df
        .agg(
            avg(abs(col("point_diff"))).alias("avg_margin"),
            max(abs(col("point_diff"))).alias("max_margin"),
            stddev(abs(col("point_diff"))).alias("std_margin"),
            count(when(col("point_diff") > 0, True)).alias("home_wins"),
            count(when(col("point_diff") < 0, True)).alias("away_wins")
        )
        .collect()[0]
    )
    
    print(f"✅ Écarts calculés:")
    print(f"   - Marge moyenne: {stats['avg_margin']:.1f} points")
    print(f"   - Home win rate: {stats['home_wins']/(stats['home_wins']+stats['away_wins'])*100:.1f}%")
```

---

### 3. Identification home/away team

Déjà inclus dans la transformation avec `home_team_id` et `away_team_id`.

---

### 4. Données prêtes pour ML

```python
def prepare_ml_dataset():
    """Créer dataset ML avec toutes les features matchs"""
    
    df_games = transform_games()
    df_teams = spark.read.format("delta").load("data/gold/team_stats_season/")
    
    # Join stats équipes home
    df_ml = (df_games
        .join(df_teams, 
              (df_games.home_team_id == df_teams.team_id) & 
              (df_games.season == df_teams.season), 
              "left")
        .withColumnRenamed("avg_pts_scored", "home_avg_pts")
        .withColumnRenamed("avg_reb", "home_avg_reb")
        .drop(df_teams.team_id)
        .drop(df_teams.season)
    )
    
    # Join stats équipes away
    df_ml = (df_ml
        .join(df_teams.alias("away"),
              (df_games.away_team_id == col("away.team_id")) &
              (df_games.season == col("away.season")),
              "left")
        .withColumn("away_avg_pts", col("away.avg_pts_scored"))
        .withColumn("away_avg_reb", col("away.avg_reb"))
    )
    
    return df_ml
```

## ⚠️ Risques & Mitigations

| Risque | Mitigation |
|--------|------------|
| Matchs sans scores | Filter status != 'Final' |
| IDs équipes inconnus | Vérification jointure |

## 📦 Livrables

- ✅ `src/processing/transform_games.py`
- ✅ `data/silver/games_processed/`

## 🎯 Definition of Done

- [ ] Tous les matchs structurés (~8600)
- [ ] Écarts calculés
- [ ] Home/away identifiés
- [ ] Dataset ML créé
