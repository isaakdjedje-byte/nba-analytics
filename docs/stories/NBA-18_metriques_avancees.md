---
Story: NBA-18
Epic: Data Processing & Transformation (NBA-7)
Points: 5
Statut: To Do
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
---

# 🎯 NBA-18: Calcul des métriques avancées (PER, TS%, etc.)

## 📋 Description

Implémenter le calcul des statistiques avancées des joueurs : PER (Player Efficiency Rating), TS% (True Shooting), USG% (Usage Rate), eFG% (Effective FG%), Game Score et Pace. Valider avec données officielles NBA.

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-12** : Données de base (points, rebonds, passes)
- ✅ **NBA-17** : Données nettoyées (qualité requise)
- ⬜ **NBA-15** : Données équipes (pour stats collectives)

### Bloque:
- ⬜ **NBA-19** : Agrégations (besoin métriques)
- ⬜ **NBA-21** : Feature engineering (métriques = features)
- ⬜ **NBA-22** : ML prédiction (features avancées)

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ NBA-17  │────→│ NBA-18  │────→│ NBA-19  │
│(Clean)  │     │(Métriques)
│         │     │         │     │(Aggrég) │
└─────────┘     └────┬────┘     └─────────┘
                     │
                     ├────→ NBA-21 (Features)
                     │
                     └────→ NBA-22 (ML)
```

## 📥📤 Entrées/Sorties

### Données en entrée:
- **`data/silver/players_cleaned/`** : Joueurs nettoyés (NBA-17)
- **`data/raw/games_detailed/`** : Box scores matchs (NBA-15)
- **`data/raw/teams_stats/`** : Stats collectives équipes

### Données en sortie:
- **`data/silver/players_advanced/`** : Delta Lake avec métriques
- **`data/silver/metrics_validation.json`** : Validation vs NBA.com
- **`docs/NBA_FORMULAS.md`** : Documentation formules

### Format:
- **Colonnes ajoutées**: `per`, `ts_pct`, `usg_pct`, `efg_pct`, `game_score`, `pace`
- **Partitionnement**: `season`, `position`

## 🛠️ Stack Technique

- **PySpark 3.5** : Calculs DataFrame
- **Delta Lake 3.0** : Stockage
- **nba-api** : Validation vs données officielles
- **Pandas** : Tests unitaires

## ✅ Critères d'acceptation détaillés

### 1. Colonne PER (Player Efficiency Rating) calculée

**Formule complète:**
```python
def calculate_per(df):
    """
    PER = Player Efficiency Rating
    Formule Hollinger avec ajustements pace
    """
    # uPER (unadjusted PER)
    df = df.withColumn("uper", (
        (col("3pm") * 0.5) +
        (col("fgm") * (2 - col("team_ast") / col("team_fgm"))) +
        ((2/3) * col("team_ast")) +
        (col("ftm") * 0.5 * (1 + (1 - col("team_ast") / col("team_fgm")) + 
         (2/3) * (col("team_ast") / col("team_fgm")))) -
        (col("vop") * col("tov")) -
        (col("vop") * col("drbp") * (col("fga") - col("fgm"))) -
        (col("vop") * 0.44 * (0.44 + 0.56 * col("drbp")) * (col("fta") - col("ftm"))) +
        (col("vop") * (1 - col("drbp")) * (col("reb") - col("oreb"))) +
        (col("vop") * col("drbp") * col("oreb")) +
        (col("vop") * col("stl")) +
        (col("vop") * col("drbp") * col("blk")) -
        (col("pf") * ((col("lg_ft") / col("lg_pf")) - 0.44 * (col("lg_fta") / col("lg_pf")) * col("vop")))
    ) / col("minutes"))
    
    # Ajustement pace
    df = df.withColumn("per", 
        col("uper") * (col("lg_pace") / col("team_pace")) * (15.0 / col("lg_avg_per"))
    )
    
    return df
```

**Simplification (sans stats ligue/équipe):**
```python
def calculate_per_simplified(df):
    """
    PER simplifié (stats individuelles seulement)
    """
    df = df.withColumn("per", (
        col("pts") + 
        0.4 * col("fgm") - 
        0.7 * col("fga") - 
        0.4 * (col("fta") - col("ftm")) +
        0.7 * col("oreb") +
        0.3 * col("dreb") +
        col("stl") +
        0.7 * col("ast") +
        0.7 * col("blk") -
        0.4 * col("pf") -
        col("tov")
    ) / col("minutes") * 48)
    
    return df
```

**Test avec LeBron James 2023-24:**
```python
def test_per_calculation():
    """Tester PER avec valeurs connues"""
    
    # Données LeBron 2023-24
    lebron_data = {
        "player_id": 2544,
        "full_name": "LeBron James",
        "season": "2023-24",
        "pts": 25.7,
        "reb": 7.3,
        "ast": 8.3,
        "stl": 1.3,
        "blk": 0.5,
        "fgm": 9.7,
        "fga": 17.9,
        "ftm": 4.6,
        "fta": 5.7,
        "tov": 3.5,
        "pf": 1.4,
        "minutes": 35.3
    }
    
    # Créer DataFrame
    df = spark.createDataFrame([lebron_data])
    
    # Calculer PER
    df = calculate_per_simplified(df)
    
    # Récupérer valeur
    per_value = df.select("per").collect()[0][0]
    
    # VALEUR ATTENDUE: ~28.5 (selon NBA.com 2023-24)
    expected_per = 28.5
    tolerance = 2.0  # ±2 points
    
    assert abs(per_value - expected_per) < tolerance, \
        f"PER calculé: {per_value}, attendu: {expected_per} ±{tolerance}"
    
    print(f"✅ PER LeBron: {per_value:.2f} (attendu: ~{expected_per})")
    return True

test_per_calculation()
```

**Résultat attendu:**
- PER calculé: ~28.5 pour LeBron 2023-24
- Écart < 2 points avec NBA.com
- Gamme PER: 0-40 (moyenne ligue = 15)

---

### 2. Colonne TS% (True Shooting Percentage) calculée

**Formule:**
```python
def calculate_ts_pct(df):
    """
    TS% = PTS / (2 * (FGA + 0.44 * FTA))
    """
    df = df.withColumn("ts_pct",
        col("pts") / (2 * (col("fga") + 0.44 * col("fta")))
    )
    return df
```

**Test avec Stephen Curry:**
```python
def test_ts_calculation():
    """Tester TS% avec valeurs connues"""
    
    # Curry 2023-24: excellent shooter
    curry_data = {
        "player_id": 201939,
        "full_name": "Stephen Curry",
        "pts": 26.4,
        "fga": 19.5,
        "fta": 4.4
    }
    
    df = spark.createDataFrame([curry_data])
    df = calculate_ts_pct(df)
    
    ts_value = df.select("ts_pct").collect()[0][0]
    
    # VALEUR ATTENDUE: ~0.629 (62.9%)
    expected_ts = 0.629
    tolerance = 0.02  # ±2%
    
    assert abs(ts_value - expected_ts) < tolerance, \
        f"TS% calculé: {ts_value:.3f}, attendu: {expected_ts:.3f}"
    
    print(f"✅ TS% Curry: {ts_value:.3f} ({ts_value*100:.1f}%)")
    print(f"   Attendu: ~{expected_ts*100:.1f}%")
    return True

test_ts_calculation()
```

**Validation:**
- TS% Curry: ~62.9%
- TS% moyenne ligue: ~56%
- TS% maximum théorique: 100% (que des lancers-francs)

---

### 3. Formules vérifiées avec données officielles NBA

**Processus de validation:**
```python
def validate_metrics_vs_nba_com():
    """
    Comparer métriques calculées avec NBA.com
    """
    from nba_api.stats.endpoints import PlayerDashboardByGeneralSplits
    
    # Liste joueurs test
    test_players = [
        (2544, "LeBron James"),      # Superstar
        (201939, "Stephen Curry"),   # Shooter
        (203507, "Giannis"),         # Big man
        (1629029, "Luka Doncic")     # All-around
    ]
    
    results = []
    
    for player_id, name in test_players:
        # Récupérer stats NBA.com
        dashboard = PlayerDashboardByGeneralSplits(
            player_id=player_id,
            season='2023-24'
        )
        
        nba_data = dashboard.get_data_frames()[0]
        official_per = nba_data['PER'].iloc[0] if 'PER' in nba_data.columns else None
        official_ts = nba_data['TS_PCT'].iloc[0] if 'TS_PCT' in nba_data.columns else None
        
        # Calculer nos valeurs
        our_data = calculate_metrics(player_id)
        
        # Comparer
        if official_per:
            per_diff = abs(our_data['per'] - official_per)
        
        if official_ts:
            ts_diff = abs(our_data['ts_pct'] - official_ts)
        
        results.append({
            "player": name,
            "per_diff": per_diff,
            "ts_diff": ts_diff,
            "valid": per_diff < 2.0 and ts_diff < 0.02
        })
    
    # Vérifier tous les tests passent
    assert all(r["valid"] for r in results), \
        f"Échec validation: {[r for r in results if not r['valid']]}"
    
    print("✅ Toutes les métriques validées vs NBA.com")
    return True

def validate_metrics_vs_nba_com()
```

**Rapport de validation:**
```json
{
  "validation_date": "2024-02-06T12:00:00",
  "players_tested": 4,
  "results": [
    {
      "player": "LeBron James",
      "per_calculated": 28.3,
      "per_official": 28.5,
      "per_diff": 0.2,
      "valid": true
    },
    {
      "player": "Stephen Curry",
      "ts_calculated": 0.631,
      "ts_official": 0.629,
      "ts_diff": 0.002,
      "valid": true
    }
  ],
  "all_valid": true
}
```

---

### 4. Tests unitaires passants

**Suite de tests:**
```python
# tests/test_advanced_metrics.py

import pytest
from src.utils.nba_formulas import (
    calculate_per, calculate_ts_pct, calculate_usg_pct,
    calculate_efg_pct, calculate_game_score
)

class TestAdvancedMetrics:
    
    def test_per_range(self, spark):
        """PER doit être entre 0 et 40"""
        data = [(15.0, 5, 10, 3, 35)]  # pts, reb, ast, stl, minutes
        df = spark.createDataFrame(data, ["pts", "reb", "ast", "stl", "minutes"])
        df = calculate_per(df)
        
        per = df.select("per").collect()[0][0]
        assert 0 <= per <= 40, f"PER hors limites: {per}"
    
    def test_ts_percentage(self, spark):
        """TS% doit être entre 0 et 1"""
        data = [(20, 15, 5)]  # pts, fga, fta
        df = spark.createDataFrame(data, ["pts", "fga", "fta"])
        df = calculate_ts_pct(df)
        
        ts = df.select("ts_pct").collect()[0][0]
        assert 0 <= ts <= 1, f"TS% hors limites: {ts}"
    
    def test_usg_percentage(self, spark):
        """USG% doit être entre 0 et 100"""
        data = [(20, 2, 5, 200, 500)]  # fga, fta, tov, team_fga, team_fta
        df = spark.createDataFrame(data, ["fga", "fta", "tov", "team_fga", "team_fta"])
        df = calculate_usg_pct(df)
        
        usg = df.select("usg_pct").collect()[0][0]
        assert 0 <= usg <= 100, f"USG% hors limites: {usg}"
    
    def test_known_player_per(self, spark):
        """PER LeBron ~28"""
        lebron = {
            "pts": 25.7, "reb": 7.3, "ast": 8.3, "stl": 1.3, "blk": 0.5,
            "fgm": 9.7, "fga": 17.9, "ftm": 4.6, "fta": 5.7,
            "tov": 3.5, "pf": 1.4, "minutes": 35.3
        }
        df = spark.createDataFrame([lebron])
        df = calculate_per(df)
        
        per = df.select("per").collect()[0][0]
        assert 26 <= per <= 30, f"PER LeBron incohérent: {per}"
    
    def test_all_metrics_calculated(self, spark):
        """Toutes les métriques doivent être présentes"""
        data = [{"pts": 20, "fga": 15, "fta": 5, "fgm": 7, "fg3m": 2,
                "reb": 5, "ast": 4, "stl": 1, "blk": 0.5, "tov": 2,
                "minutes": 30, "team_fga": 100, "team_fta": 20}]
        
        df = spark.createDataFrame(data)
        df = (df
            .transform(calculate_per)
            .transform(calculate_ts_pct)
            .transform(calculate_usg_pct)
            .transform(calculate_efg_pct)
            .transform(calculate_game_score)
        )
        
        required_cols = ["per", "ts_pct", "usg_pct", "efg_pct", "game_score"]
        for col_name in required_cols:
            assert col_name in df.columns, f"Colonne {col_name} manquante"

# Exécuter tests
# pytest tests/test_advanced_metrics.py -v
```

---

### 5. Résultats dans data/silver/players_advanced

**Structure attendue:**
```python
def test_silver_advanced():
    df = spark.read.format("delta").load("data/silver/players_advanced/")
    
    # Colonnes de base
    base_cols = ["id", "full_name", "season", "team"]
    for col_name in base_cols:
        assert col_name in df.columns, f"Colonne base {col_name} manquante"
    
    # Colonnes métriques
    metric_cols = ["per", "ts_pct", "usg_pct", "efg_pct", "game_score", "pace"]
    for col_name in metric_cols:
        assert col_name in df.columns, f"Métrique {col_name} manquante"
    
    # Vérifier valeurs pas null
    for col_name in metric_cols:
        null_count = df.filter(col(col_name).isNull()).count()
        assert null_count < df.count() * 0.05, \
            f"Trop de nulls dans {col_name}: {null_count}"
    
    # Statistiques globales
    stats = df.select(
        avg("per").alias("avg_per"),
        avg("ts_pct").alias("avg_ts"),
        avg("usg_pct").alias("avg_usg")
    ).collect()[0]
    
    print(f"✅ Métriques calculées pour {df.count()} joueurs")
    print(f"   - PER moyen: {stats['avg_per']:.2f}")
    print(f"   - TS% moyen: {stats['avg_ts']:.3f}")
    print(f"   - USG% moyen: {stats['avg_usg']:.2f}%")
    
    return True

test_silver_advanced()
```

## ⚠️ Risques & Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Formules incorrectes** | Moyen | Critique | Validation vs NBA.com, tests avec valeurs connues |
| **Division par zéro** | Faible | Élevé | Gestion cas edge (0 minutes, 0 tirs) |
| **Stats ligue manquantes** | Moyen | Moyen | Valeurs par défaut, approximation acceptable |
| **Écart avec officiel** | Moyen | Moyen | Tolérance ±2 points PER, ±2% TS |

## 📦 Livrables

### Code:
- ✅ `src/utils/nba_formulas.py` - Toutes les formules
- ✅ `src/processing/calculate_metrics.py` - Pipeline calcul
- ✅ `tests/test_advanced_metrics.py` - Tests unitaires
- ✅ `tests/test_nba_validation.py` - Validation NBA.com

### Données:
- ✅ `data/silver/players_advanced/` - Joueurs avec métriques
- ✅ `data/silver/metrics_validation.json` - Rapport validation

### Documentation:
- ✅ `docs/NBA_FORMULAS.md` - Explication formules mathématiques

## 🎯 Definition of Done

- [ ] Toutes les métriques calculées (PER, TS%, USG%, eFG%, Game Score, Pace)
- [ ] Tests unitaires passants
- [ ] Validation vs NBA.com (écart < 5%)
- [ ] Gamme valeurs cohérente (PER 0-40, TS% 0-100%)
- [ ] 0 division par zéro
- [ ] Rapport validation généré
- [ ] Mergé dans master (PR #X)

## 📝 Notes d'implémentation

### Gestion edge cases:
```python
# Éviter division par zéro
df = df.withColumn("ts_pct",
    when((col("fga") + 0.44 * col("fta")) == 0, lit(0.0))
    .otherwise(col("pts") / (2 * (col("fga") + 0.44 * col("fta"))))
)

# Gérer minutes = 0
df = df.withColumn("per",
    when(col("minutes") == 0, lit(0.0))
    .otherwise(col("raw_per"))
)
```

### Formule USG%:
```python
def calculate_usg_pct(df):
    """
    USG% = 100 * ((FGA + 0.44*FTA + TOV) * (TmMP/5)) / (MP * (TmFGA + 0.44*TmFTA + TmTOV))
    """
    df = df.withColumn("usg_pct",
        100 * ((col("fga") + 0.44 * col("fta") + col("tov")) * (col("team_minutes") / 5)) /
        (col("minutes") * (col("team_fga") + 0.44 * col("team_fta") + col("team_tov")))
    )
    return df
```

## 🔗 Références

- [NBA-12](NBA-12_spark_batch.md) : Données de base
- [NBA-17](NBA-17_nettoyage.md) : Données nettoyées
- [PER Explanation](https://www.basketball-reference.com/about/per.html)
- NBA-19: Agrégations avec métriques
