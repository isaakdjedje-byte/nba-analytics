---
Story: NBA-20
Epic: Data Processing & Transformation (NBA-7)
Points: 5
Statut: ✅ Done
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
Terminé: 08/Feb/26
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

## 📦 Livrables Réels

- ✅ `src/pipeline/nba20_transform_games.py` - Transformateur principal (270 lignes)
- ✅ `src/pipeline/unified_ml_pipeline.py` - Orchestrateur ML (220 lignes)
- ✅ `data/silver/games_processed/games_structured.json` - 1,230 matchs structurés (889KB)

## 📊 Résultats

| Métrique | Valeur |
|----------|--------|
| **Fichiers traités** | 7 fichiers box scores |
| **Records bruts** | 2,460 (2 équipes × 1,230 matchs) |
| **Matchs structurés** | 1,230 |
| **Home wins** | 668 (54.3%) |
| **Away wins** | 562 (45.7%) |
| **Marge moyenne** | 12.6 points |
| **Marge max** | 62 points |
| **Erreurs** | 0 |
| **Temps d'exécution** | < 2 secondes |

## 🎯 Definition of Done

- [x] Tous les matchs structurés (1,230 matchs sur saison 2023-24)
- [x] Écarts calculés (point_diff, avg_margin)
- [x] Home/away identifiés via parsing champ "matchup"
- [x] Stats équipes incluses (fg_pct, reb, ast, etc.)
- [x] Fichier JSON structuré généré
- [x] 0 erreurs de transformation

## 🚀 Commandes

```bash
# Exécuter uniquement NBA-20
python src/pipeline/nba20_transform_games.py

# Exécuter pipeline complet NBA-20 → NBA-21 → NBA-22
python src/pipeline/unified_ml_pipeline.py
```
