---
Story: NBA-17
Epic: Data Processing & Transformation (NBA-7)
Points: 5
Statut: To Do
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
---

# 🎯 NBA-17: Nettoyage des données joueurs

## 📋 Description

Nettoyer les données brutes des joueurs (nulls, doublons, valeurs aberrantes) pour produire un dataset propre et fiable dans la couche Silver.

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-11** : Données brutes joueurs
- ✅ **NBA-15** : Données complètes (matchs/équipes)
- 🟡 **NBA-14** : Schémas évolutifs

### Bloque:
- ⬜ **NBA-18** : Métriques avancées (besoin données propres)
- ⬜ **NBA-19** : Agrégations (qualité requise)
- ⬜ **NBA-21** : Feature engineering (données nettoyées)

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ NBA-15  │────→│ NBA-17  │────→│ NBA-18  │
│(Données)│     │(Clean)  │     │(Métriques)
└─────────┘     └────┬────┘     └─────────┘
                     │
                     ├────→ NBA-19 (Aggrég)
                     │
                     └────→ NBA-21 (Features)
```

## 📥📤 Entrées/Sorties

### Données en entrée:
- **`data/raw/players.json`** : Données brutes (5103 joueurs)
- **`data/raw/all_players_historical.json`** : Historique complet
- **`data/raw/active_players.json`** : Joueurs actifs (530)

### Données en sortie:
- **`data/silver/players_cleaned/`** : Delta Lake nettoyé
- **`data/silver/players_cleaned_stats.json`** : Rapport nettoyage
- **`logs/cleaning_YYYYMMDD.log`** : Log détaillé opérations

### Format:
- **Format**: Delta Lake partitionné par `is_active`, `position`
- **Qualité**: Taux de nulls < 5%, 0 doublons

## 🛠️ Stack Technique

- **PySpark 3.5** : DataFrame operations
- **Delta Lake 3.0** : Stockage Silver
- **Pandas** : Analyse exploratoire (optionnel)
- **Great Expectations** : Data quality (optionnel)

## ✅ Critères d'acceptation détaillés

### 1. Script src/processing/clean_data.py créé

**Structure du script:**
```python
#!/usr/bin/env python3
"""
Script de nettoyage des données joueurs NBA
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, isnan, count, lit, 
    trim, lower, regexp_replace
)
from delta import configure_spark_with_delta_pip
import logging
import json
from datetime import datetime

class PlayersDataCleaner:
    def __init__(self, input_path, output_path):
        self.spark = self._init_spark()
        self.input_path = input_path
        self.output_path = output_path
        self.stats = {}
        
    def _init_spark(self):
        """Initialiser session Spark avec Delta"""
        builder = SparkSession.builder \
            .appName("NBA-Players-Cleaning") \
            .config("spark.sql.extensions", 
                   "io.delta.sql.DeltaSparkSessionExtension")
        return configure_spark_with_delta_pip(builder).getOrCreate()
    
    def load_data(self):
        """Charger données brutes"""
        self.df_raw = self.spark.read.json(self.input_path)
        self.stats['initial_count'] = self.df_raw.count()
        self.stats['initial_columns'] = len(self.df_raw.columns)
        return self
    
    def remove_duplicates(self):
        """Supprimer doublons basés sur player_id"""
        initial = self.df_raw.count()
        self.df_clean = self.df_raw.dropDuplicates(["id"])
        final = self.df_clean.count()
        self.stats['duplicates_removed'] = initial - final
        return self
    
    def handle_nulls(self):
        """Gérer valeurs manquantes"""
        # Colonnes critiques (doivent être non-null)
        critical_cols = ["id", "full_name"]
        self.df_clean = self.df_clean.dropna(subset=critical_cols)
        
        # Colonnes numériques (imputation ou suppression)
        numeric_cols = ["height", "weight", "pts", "reb", "ast"]
        for col_name in numeric_cols:
            null_count = self.df_clean.filter(col(col_name).isNull()).count()
            if null_count > 0:
                # Si >50% null, supprimer colonne
                if null_count / self.df_clean.count() > 0.5:
                    self.df_clean = self.df_clean.drop(col_name)
                    self.stats[f'{col_name}_dropped'] = True
                else:
                    # Sinon imputer avec médiane
                    median = self.df_clean.approxQuantile(
                        col_name, [0.5], 0.01
                    )[0]
                    self.df_clean = self.df_clean.fillna({col_name: median})
                    self.stats[f'{col_name}_imputed'] = median
        
        return self
    
    def remove_outliers(self):
        """Supprimer valeurs aberrantes"""
        # Taille: entre 1.60m et 2.40m
        self.df_clean = self.df_clean.filter(
            (col("height") >= 160) & (col("height") <= 240) |
            col("height").isNull()
        )
        
        # Poids: entre 60kg et 160kg
        self.df_clean = self.df_clean.filter(
            (col("weight") >= 60) & (col("weight") <= 160) |
            col("weight").isNull()
        )
        
        # Stats: pas de valeurs négatives
        stat_cols = ["pts", "reb", "ast", "stl", "blk"]
        for col_name in stat_cols:
            self.df_clean = self.df_clean.filter(
                (col(col_name) >= 0) | col(col_name).isNull()
            )
        
        return self
    
    def standardize_formats(self):
        """Standardiser formats"""
        # Nom: majuscule première lettre
        self.df_clean = self.df_clean.withColumn(
            "full_name", 
            trim(col("full_name"))
        )
        
        # Position: majuscules
        self.df_clean = self.df_clean.withColumn(
            "position",
            upper(col("position"))
        )
        
        return self
    
    def validate_data(self):
        """Valider qualité données"""
        # Calculer taux de nulls par colonne
        null_rates = {}
        for col_name in self.df_clean.columns:
            null_count = self.df_clean.filter(col(col_name).isNull()).count()
            null_rate = null_count / self.df_clean.count()
            null_rates[col_name] = null_rate
        
        self.stats['null_rates'] = null_rates
        
        # Vérifier taux global < 5%
        overall_null = sum(null_rates.values()) / len(null_rates)
        assert overall_null < 0.05, f"Taux nulls trop élevé: {overall_null:.2%}"
        
        return self
    
    def save_clean_data(self):
        """Sauvegarder données nettoyées"""
        self.df_clean.write \
            .format("delta") \
            .mode("overwrite") \
            .partitionBy("is_active", "position") \
            .save(self.output_path)
        
        self.stats['final_count'] = self.df_clean.count()
        self.stats['final_columns'] = len(self.df_clean.columns)
        
        return self
    
    def generate_report(self):
        """Générer rapport nettoyage"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "input": self.input_path,
            "output": self.output_path,
            "stats": self.stats
        }
        
        with open("data/silver/players_cleaned_stats.json", "w") as f:
            json.dump(report, f, indent=2)
        
        return report

# Point d'entrée
if __name__ == "__main__":
    cleaner = PlayersDataCleaner(
        input_path="data/raw/all_players_historical.json",
        output_path="data/silver/players_cleaned"
    )
    
    report = (cleaner
        .load_data()
        .remove_duplicates()
        .handle_nulls()
        .remove_outliers()
        .standardize_formats()
        .validate_data()
        .save_clean_data()
        .generate_report()
    )
    
    print(f"✅ Nettoyage terminé!")
    print(f"   - Initial: {report['stats']['initial_count']} joueurs")
    print(f"   - Final: {report['stats']['final_count']} joueurs")
    print(f"   - Doublons supprimés: {report['stats']['duplicates_removed']}")
```

---

### 2. Suppression des doublons

**Test détaillé:**
```python
def test_duplicate_removal():
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    
    # Données test avec doublons
    data = [
        (1, "LeBron James", "LAL", 39),
        (1, "LeBron James", "LAL", 39),  # Doublon
        (2, "Stephen Curry", "GSW", 35),
        (2, "Stephen Curry", "GSW", 35),  # Doublon
        (3, "Kevin Durant", "PHX", 35)
    ]
    
    df = spark.createDataFrame(data, ["id", "name", "team", "age"])
    initial = df.count()
    
    # Supprimer doublons
    df_clean = df.dropDuplicates(["id"])
    final = df_clean.count()
    
    assert initial == 5, f"Données initiales: {initial}"
    assert final == 3, f"Doublons non supprimés: {final}"
    assert df_clean.filter(col("id") == 1).count() == 1, "Doublon ID=1 persistant"
    
    print(f"✅ Doublons supprimés: {initial - final} lignes")
    return True

test_duplicate_removal()
```

**Résultat attendu:**
- 0 doublons sur `id` joueur
- Journal: nombre de doublons détectés et supprimés

---

### 3. Taux de nulls < 5% après traitement

**Test détaillé:**
```python
def test_null_rate():
    # Après nettoyage
    df_clean = spark.read.format("delta").load("data/silver/players_cleaned/")
    
    total_rows = df_clean.count()
    null_rates = {}
    
    for col_name in df_clean.columns:
        null_count = df_clean.filter(col(col_name).isNull()).count()
        null_rate = null_count / total_rows
        null_rates[col_name] = null_rate
        
        print(f"{col_name}: {null_rate:.2%} nulls")
    
    # Vérifier chaque colonne < 5%
    for col_name, rate in null_rates.items():
        assert rate < 0.05, f"{col_name}: {rate:.2%} nulls > 5%!"
    
    # Taux global
    overall = sum(null_rates.values()) / len(null_rates)
    assert overall < 0.05, f"Taux global: {overall:.2%} > 5%!"
    
    print(f"✅ Taux nulls global: {overall:.2%}")
    return True

test_null_rate()
```

**Résultat attendu:**
- Chaque colonne: < 5% nulls
- Taux global: < 5%
- Rapport JSON avec détail par colonne

---

### 4. Validation des tailles/poids cohérents

**Règles de validation:**
```python
VALIDATION_RULES = {
    "height": {"min": 160, "max": 240, "unit": "cm"},      # 1.60m - 2.40m
    "weight": {"min": 60, "max": 160, "unit": "kg"},       # 60kg - 160kg
    "pts": {"min": 0, "max": 50, "unit": "points/match"},  # 0-50 PPG
    "reb": {"min": 0, "max": 20, "unit": "reb/match"},     # 0-20 RPG
    "ast": {"min": 0, "max": 15, "unit": "ast/match"},     # 0-15 APG
}
```

**Test détaillé:**
```python
def test_value_ranges():
    df = spark.read.format("delta").load("data/silver/players_cleaned/")
    
    errors = []
    
    # Tester chaque règle
    for col_name, rules in VALIDATION_RULES.items():
        if col_name in df.columns:
            # Valeurs hors limites
            outliers = df.filter(
                (col(col_name) < rules["min"]) | 
                (col(col_name) > rules["max"])
            )
            
            count = outliers.count()
            if count > 0:
                errors.append(f"{col_name}: {count} valeurs hors limites")
                print(f"❌ {col_name}: {count} outliers")
                outliers.show(5)
    
    assert len(errors) == 0, f"Erreurs validation: {errors}"
    
    print("✅ Toutes les valeurs dans les plages valides")
    return True

test_value_ranges()
```

**Exemples de valeurs aberrantes détectées:**
- Taille: 0cm, 300cm, -180cm
- Poids: 0kg, 250kg, -90kg
- Points: -5, 100

---

### 5. Données nettoyées dans data/silver/players_cleaned

**Vérification structure:**
```python
def test_silver_structure():
    import os
    
    path = "data/silver/players_cleaned"
    
    # Vérifier Delta Lake
    assert os.path.exists(f"{path}/_delta_log"), "Pas un Delta Lake!"
    
    # Vérifier partitionnement
    partitions = [d for d in os.listdir(path) if d.startswith("is_active")]
    assert len(partitions) >= 2, f"Partitionnement incorrect: {partitions}"
    
    # Lire et vérifier
    df = spark.read.format("delta").load(path)
    
    # Vérifier colonnes clés
    required_cols = ["id", "full_name", "is_active", "position"]
    for col_name in required_cols:
        assert col_name in df.columns, f"Colonne {col_name} manquante!"
    
    # Vérifier nombre joueurs cohérent
    count = df.count()
    assert 5000 < count < 5100, f"Nombre joueurs incohérent: {count}"
    
    print(f"✅ Structure Silver correcte: {count} joueurs")
    return True

test_silver_structure()
```

## ⚠️ Risques & Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Perte données critiques** | Faible | Critique | Backup avant nettoyage, tests validation |
| **Over-cleaning** | Moyen | Moyen | Sauvegarder données brutes, log détaillé |
| **Règles trop strictes** | Moyen | Moyen | Review règles métier, exceptions documentées |
| **Performance lente** | Moyen | Faible | Partitionnement, caching, monitoring temps |

## 📦 Livrables

### Code:
- ✅ `src/processing/clean_data.py` - Script principal
- ✅ `src/processing/cleaning_utils.py` - Fonctions utilitaires
- ✅ `tests/test_cleaning.py` - Tests unitaires
- ✅ `configs/cleaning_rules.yaml` - Règles de validation

### Données:
- ✅ `data/silver/players_cleaned/` - Delta Lake nettoyé
- ✅ `data/silver/players_cleaned_stats.json` - Rapport qualité
- ✅ `logs/cleaning_YYYYMMDD.log` - Logs détaillés

### Documentation:
- ✅ `docs/DATA_CLEANING.md` - Guide nettoyage

## 🎯 Definition of Done

- [ ] Script clean_data.py exécutable sans erreur
- [ ] 0 doublons dans données finales
- [ ] Taux nulls < 5% global
- [ ] Toutes les valeurs dans plages valides
- [ ] Rapport JSON généré
- [ ] Tests passants (pytest tests/test_cleaning.py)
- [ ] Mergé dans master (PR #X)

## 📝 Notes d'implémentation

### Great Expectations (optionnel):
```python
# Pour data quality avancée
import great_expectations as ge

# Définir expectations
batch = ge.dataset.SparkDFDataset(df)
batch.expect_column_values_to_be_between("height", 160, 240)
batch.expect_column_values_to_not_be_null("full_name")

# Validation
results = batch.validate()
assert results["success"], "Data quality checks failed"
```

### Monitoring qualité:
```python
def log_data_quality(df, stage):
    """Log métriques qualité"""
    metrics = {
        "stage": stage,
        "row_count": df.count(),
        "null_rates": {c: df.filter(col(c).isNull()).count()/df.count() 
                      for c in df.columns},
        "timestamp": datetime.now().isoformat()
    }
    
    with open(f"logs/quality_{stage}.json", "w") as f:
        json.dump(metrics, f)
```

## 🔗 Références

- [NBA-11](NBA-11_api_connection.md) : Données brutes
- [NBA-15](NBA-15_donnees_matchs.md) : Données complètes
- [NBA-27](NBA-27_data_quality.md) : Data Quality checks
