# Guide Utilisateur - NBA-17 Nettoyage Données

Ce guide explique comment utiliser le pipeline de nettoyage des données joueurs NBA.

---

## Installation

### Prérequis
```bash
# Python 3.11+
python --version

# Dépendances déjà installées via requirements.txt
pip install -r requirements.txt
```

### Vérification
```bash
# Vérifier que les données sources existent
ls data/raw/all_players_historical.json
ls data/raw/rosters/roster_2023_24.json
```

---

## Utilisation Rapide

### Exécution Complète (2 commandes)

```bash
# Étape 1: Enrichissement (76 min 1ère fois, instantané ensuite)
python src/ingestion/enrich_players_api.py

# Étape 2: Nettoyage (2-3 min)
python src/processing/clean_data.py

# ✓ Fait! Données dans data/silver/players_cleaned/
```

---

## Utilisation Avancée

### 1. Enrichissement API Seul

```bash
# Enrichir avec API NBA (crée cache)
python src/ingestion/enrich_players_api.py

# Options:
# --cache-file PATH    Chemin fichier cache (défaut: data/raw/players_enriched_cache.json)
# --rate-limit N      Secondes entre appels (défaut: 1)
# --max-retries N     Nombre essais max (défaut: 3)

python src/ingestion/enrich_players_api.py --rate-limit 2
```

### 2. Nettoyage Seul

```bash
# Nettoyer (suppose enrichissement déjà fait)
python src/processing/clean_data.py

# Options:
# --config PATH       Fichier config YAML
# --input PATH        JSON joueurs source
# --output PATH       Dossier output Delta Lake
# --report PATH       Fichier rapport JSON

python src/processing/clean_data.py \
  --config configs/cleaning_rules.yaml \
  --input data/raw/all_players_historical.json \
  --output data/silver/players_cleaned \
  --report data/silver/players_cleaned_stats.json
```

### 3. Exécution Tests

```bash
# Tous les tests
pytest tests/test_cleaning.py -v

# Test spécifique
pytest tests/test_cleaning.py::test_duplicate_removal -v

# Avec couverture
pytest tests/test_cleaning.py --cov=src/processing --cov-report=html
```

---

## Structure Output

### Delta Lake Partitionné

```
data/silver/players_cleaned/
├── is_active=true/           # Joueurs actifs
│   ├── position=C/           # Centers
│   ├── position=F/           # Forwards
│   ├── position=G/           # Guards
│   └── ...
└── is_active=false/          # Joueurs inactifs
    └── ...
```

### Schéma Données

```
root
 |-- id: integer (nullable = true)
 |-- full_name: string (nullable = true)
 |-- first_name: string (nullable = true)
 |-- last_name: string (nullable = true)
 |-- is_active: boolean (nullable = true)
 |-- height_cm: integer (nullable = true)
 |-- weight_kg: integer (nullable = true)
 |-- position: string (nullable = true)
 |-- birth_date: string (nullable = true)
 |-- age: integer (nullable = true)
 |-- from_year: integer (nullable = true)
 |-- to_year: integer (nullable = true)
 |-- data_source: string (nullable = true)  # roster/api/csv/imputed
```

---

## Lecture des Données

### PySpark

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = SparkSession.builder.appName("NBA").getOrCreate()

# Lire tous les joueurs
df = spark.read.format("delta").load("data/silver/players_cleaned/")

# Lire seulement actifs
df_active = spark.read.format("delta").load("data/silver/players_cleaned/is_active=true")

# Lire Guards actifs
df_guards = spark.read.format("delta").load("data/silver/players_cleaned/is_active=true/position=G")

# Requête SQL
spark.sql("SELECT * FROM delta.`data/silver/players_cleaned` WHERE position = 'C' AND height_cm > 210").show()
```

### Pandas

```python
import pandas as pd

# Lire avec PySpark puis convertir
df_pandas = spark.read.format("delta").load("data/silver/players_cleaned/").toPandas()

# Ou utiliser delta-rs
# pip install deltalake
from deltalake import DeltaTable
dt = DeltaTable("data/silver/players_cleaned/")
df = dt.to_pandas()
```

---

## Dépannage

### Problème: Enrichissement API trop lent

**Cause:** 4571 appels API × 1 seconde = 76 minutes

**Solution:**
```bash
# C'est normal! Le cache évite de refaire les appels
# Vérifier que le cache fonctionne:
ls -lh data/raw/players_enriched_cache.json

# Si besoin de forcer refresh:
rm data/raw/players_enriched_cache.json
python src/ingestion/enrich_players_api.py
```

### Problème: Erreur "Rate limit exceeded"

**Solution:**
```bash
# Augmenter délai entre appels
python src/ingestion/enrich_players_api.py --rate-limit 2

# Ou reprendre là où ça s'est arrêté (cache gère la reprise)
python src/ingestion/enrich_players_api.py
```

### Problème: Tests qui échouent

**Vérifications:**
```bash
# Vérifier données présentes
ls data/silver/players_cleaned/_delta_log/

# Vérifier rapport
ls data/silver/players_cleaned_stats.json

# Relancer nettoyage
python src/processing/clean_data.py

# Relancer tests
pytest tests/test_cleaning.py -v
```

### Problème: Permission denied

**Solution:**
```bash
# Vérifier permissions dossiers
ls -la data/silver/

# Créer dossiers si manquants
mkdir -p data/silver/players_cleaned
mkdir -p logs
```

---

## FAQ

**Q: Combien de temps prend l'enrichissement ?**  
R: ~76 minutes la première fois (4571 appels API), instantané ensuite grâce au cache.

**Q: Puis-je interrompre et reprendre ?**  
R: Oui! Le cache sauvegarde la progression. Relancez simplement la commande.

**Q: Que faire si un joueur n'est pas trouvé dans l'API ?**  
R: Il sera automatiquement imputé avec des stats moyennes basées sur sa position et époque.

**Q: Comment ajouter un joueur au CSV critiques ?**  
R: Éditez `data/supplemental/players_critical.csv` et ajoutez une ligne avec les données.

**Q: Puis-je modifier les règles de validation ?**  
R: Oui, éditez `configs/cleaning_rules.yaml` pour ajuster les plages (height, weight, age).

---

## Support

**Documentation technique:** `docs/DATA_CLEANING.md`  
**Tests:** `tests/test_cleaning.py`  
**Logs:** `logs/cleaning_YYYYMMDD.log`

---

**Version:** 1.0  
**Dernière mise à jour:** 2026-02-06
