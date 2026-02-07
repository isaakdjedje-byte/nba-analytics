# NBA-17: Nettoyage des Données Joueurs

**Ticket:** NBA-17  
**Epic:** Data Processing & Transformation (NBA-7)  
**Points:** 5  
**Status:** Done  
**Date:** 2026-02-06

---

## Vue d'ensemble

Ce module réalise le nettoyage et l'enrichissement des données de 5103 joueurs NBA, produisant un dataset propre et fiable dans la couche Silver.

### Objectifs
- ✅ Nettoyer les données brutes (nulls, doublons, valeurs aberrantes)
- ✅ Enrichir 5103 joueurs avec données physiques complètes
- ✅ Standardiser formats et unités
- ✅ Valider la qualité des données (taux nulls < 5%)
- ✅ Produire dataset Delta Lake partitionné

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SOURCES DE DONNÉES                          │
├─────────────────────────────────────────────────────────────────┤
│ 1. Roster 2023-24        │ 532 joueurs │ height, weight, pos   │
│ 2. API NBA (CommonPlayerInfo) │ ~4000 joueurs │ Données complètes    │
│ 3. CSV Critiques         │ ~50 joueurs  │ Légendes NBA manuel  │
│ 4. Imputation Stats      │ ~500 joueurs │ Position + Époque    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PIPELINE NETTOYAGE                          │
├─────────────────────────────────────────────────────────────────┤
│ 1. Chargement JSON       → DataFrame PySpark                    │
│ 2. Enrichissement API    → Cache + Appels API                   │
│ 3. Fusion Sources        → Roster + API + CSV + Imputation      │
│ 4. Suppression Doublons  → dropDuplicates(["id"])               │
│ 5. Conversion Unités     → height: '6-8' → 203cm               │
│                        → weight: 225lbs → 102kg                │
│ 6. Standardisation       → Position: 'Forward' → 'F'           │
│                        → Dates: ISO format                     │
│ 7. Validation            → Plages: 160-240cm, 60-160kg         │
│                        → Taux nulls < 5%                       │
│ 8. Stockage Delta Lake   → Partitionné: is_active/position     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         OUTPUTS                                  │
├─────────────────────────────────────────────────────────────────┤
│ data/silver/players_cleaned/          │ Delta Lake partitionné │
│ data/silver/players_cleaned_stats.json│ Rapport qualité        │
│ logs/cleaning_YYYYMMDD.log            │ Logs détaillés         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fichiers

### Code Source

| Fichier | Description | Lignes |
|---------|-------------|--------|
| `src/ingestion/enrich_players_api.py` | Enrichissement API avec cache | ~200 |
| `src/processing/clean_data.py` | Pipeline principal nettoyage | ~300 |
| `src/processing/impute_stats.py` | Imputation statistique | ~100 |
| `src/processing/cleaning_utils.py` | Fonctions utilitaires | ~150 |

### Configuration

| Fichier | Description |
|---------|-------------|
| `configs/cleaning_rules.yaml` | Règles validation et conversion |
| `data/supplemental/players_critical.csv` | Joueurs légendes (~50) |

### Tests

| Fichier | Description | Tests |
|---------|-------------|-------|
| `tests/test_cleaning.py` | Tests unitaires complets | 13 |

---

## Stratégie d'Enrichissement

### Niveau 1: Roster Local (532 joueurs)
- **Source:** `data/raw/rosters/roster_2023_24.json`
- **Données:** height, weight, position, age, experience
- **Qualité:** Données complètes et fiables

### Niveau 2: API NBA (~4000 joueurs)
- **Endpoint:** `CommonPlayerInfo`
- **Cache:** `data/raw/players_enriched_cache.json`
- **Rate Limit:** 1 requête/seconde
- **Retry:** Backoff exponentiel (3 essais max)

### Niveau 3: CSV Manuel (~50 joueurs)
- **Fichier:** `data/supplemental/players_critical.csv`
- **Contenu:** Légendes NBA (Kareem, Jordan, Bird, Magic, etc.)
- **Source:** Recherche manuelle

### Niveau 4: Imputation Statistique (~500 joueurs)
- **Méthode:** Médiane par position + époque
- **Époques:** early_nba, sixties, seventies, eighties, nineties, two_thousands, modern
- **Bruit:** ±2cm (height), ±2kg (weight)

#### Stats d'Imputation par Époque

```yaml
early_nba (1946-1960):
  G: {height: 185, weight: 80}
  F: {height: 195, weight: 90}
  C: {height: 205, weight: 100}

modern (2010+):
  G: {height: 191, weight: 90}
  F: {height: 203, weight: 102}
  C: {height: 211, weight: 115}
```

---

## Conversions

### Height
```python
# Input: '6-8' (feet-inches)
# Output: 203 (cm)
formule: (feet × 30.48) + (inches × 2.54)
exemple: (6 × 30.48) + (8 × 2.54) = 203.2 ≈ 203cm
```

### Weight
```python
# Input: 225 (lbs)
# Output: 102 (kg)
formule: lbs × 0.453592
exemple: 225 × 0.453592 = 102.058 ≈ 102kg
```

### Position
```python
mapping = {
    'GUARD': 'G', 'FORWARD': 'F', 'CENTER': 'C',
    'GUARD-FORWARD': 'G-F', 'FORWARD-GUARD': 'F-G',
    'FORWARD-CENTER': 'F-C', 'CENTER-FORWARD': 'C-F'
}
```

---

## Validation

### Règles de Validation (configs/cleaning_rules.yaml)

```yaml
validation:
  critical_columns: [id, full_name]  # Suppression si null
  
  ranges:
    height_cm: {min: 160, max: 240}
    weight_kg: {min: 60, max: 160}
    age: {min: 18, max: 45}
  
  null_threshold:
    global: 0.05  # 5% maximum
    per_column: 0.10
```

### Résultats Validation

| Métrique | Valeur | Statut |
|----------|--------|--------|
| Joueurs totaux | 5103 | ✅ |
| Doublons | 0 | ✅ |
| Taux nulls global | < 5% | ✅ |
| Height hors plage | 0 | ✅ |
| Weight hors plage | 0 | ✅ |

---

## Partitionnement Output

### Structure Delta Lake
```
data/silver/players_cleaned/
├── _delta_log/
├── is_active=true/
│   ├── position=C/
│   ├── position=F/
│   ├── position=G/
│   ├── position=F-C/
│   ├── position=F-G/
│   ├── position=G-F/
│   └── position=C-F/
└── is_active=false/
    └── [même structure position]
```

---

## Utilisation

### Exécution Pipeline Complète

```bash
# 1. Enrichissement API (~76 min 1ère fois, instantané ensuite)
python src/ingestion/enrich_players_api.py

# 2. Nettoyage
python src/processing/clean_data.py

# 3. Tests
pytest tests/test_cleaning.py -v
```

### Lecture Données Nettoyées

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("Read-Cleaned-Players") \
    .getOrCreate()

# Lire Delta Lake
df = spark.read.format("delta").load("data/silver/players_cleaned/")

print(f"Total joueurs: {df.count()}")
df.printSchema()
df.show(5)
```

---

## Tests

### Couverture Tests (13 tests)

```bash
pytest tests/test_cleaning.py -v --tb=short
```

| Test | Description |
|------|-------------|
| `test_duplicate_removal` | Vérifie 0 doublons |
| `test_height_conversion` | '6-8' → 203cm |
| `test_weight_conversion` | 225lbs → 102kg |
| `test_position_standardization` | 'Forward' → 'F' |
| `test_null_rate_validation` | Taux < 5% |
| `test_value_range_validation` | Height 160-240cm |
| `test_delta_lake_structure` | Structure correcte |
| `test_imputation_stats` | Imputation fonctionne |
| `test_critical_columns_not_null` | id/full_name présents |
| `test_report_generation` | Rapport créé |
| `test_birth_date_parsing` | Parsing dates |
| `test_age_calculation` | Calcul âge |
| `test_era_determination` | Détection époque |

---

## Rapport Qualité

### Fichier: `data/silver/players_cleaned_stats.json`

```json
{
  "timestamp": "2026-02-06T20:00:00",
  "total_players": 5103,
  "active_players": 532,
  "inactive_players": 4571,
  "enrichment_stats": {
    "from_roster": 532,
    "from_api": 3984,
    "from_csv": 54,
    "from_imputation": 533
  },
  "validation": {
    "duplicates_removed": 0,
    "null_rate_global": 0.02,
    "players_with_complete_data": 5103
  },
  "output": {
    "path": "data/silver/players_cleaned",
    "format": "delta",
    "partitions": ["is_active", "position"]
  }
}
```

---

## Dépendances

- **PySpark 3.5** : Processing distribué
- **Delta Lake 3.0** : Stockage Silver
- **nba-api 1.1.11** : Enrichissement API
- **PyYAML** : Configuration
- **pytest** : Tests

---

## Points d'Attention

### Performance
- **Enrichissement API:** ~76 min (1× seulement grâce au cache)
- **Nettoyage:** ~2-3 min avec PySpark
- **Cache:** 7 jours d'expiration

### Qualité
- **Imputation:** Marquée avec flag `data_source='imputed'`
- **Validation:** Assertions strictes sur plages
- **Logging:** Toutes les opérations tracées

### Maintenance
- **CSV Critiques:** À mettre à jour manuellement
- **Cache API:** Auto-expiration après 7 jours
- **Logs:** Rotation automatique

---

## Prochaines Étapes

- **NBA-18** : Métriques avancées (PER, TS%, USG%)
- **NBA-19** : Agrégations équipe/saison
- **NBA-27** : Data Quality checks additionnels

---

**Auteur:** Isaak  
**Dernière mise à jour:** 2026-02-06  
**Version:** 1.0
