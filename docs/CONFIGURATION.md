# Guide de Configuration - NBA Analytics Platform

## Vue d'ensemble

Ce guide explique comment configurer le projet NBA Analytics Platform en utilisant le **système de configuration centralisé** basé sur Pydantic Settings.

## Fichier .env

### Création

```bash
# À la racine du projet
cp .env.example .env

# Modifier avec vos valeurs
nano .env  # Linux/Mac
# ou
code .env  # VS Code
```

### Variables obligatoires

| Variable | Description | Défaut | Exemple |
|----------|-------------|--------|---------|
| `ENVIRONMENT` | Environnement d'exécution | `development` | `development`, `staging`, `production` |
| `API_HOST` | Host de l'API | `0.0.0.0` | `0.0.0.0`, `localhost` |
| `API_PORT` | Port de l'API | `8000` | `8000`, `8080` |
| `DATABASE_URL` | Connexion PostgreSQL | `postgresql://nba:nba@localhost:5432/nba` | Voir format |
| `DATA_ROOT` | Racine des données | `data` | `data`, `/path/to/data` |
| `MODEL_PATH` | Répertoire des modèles | `models` | `models` |
| `PREDICTIONS_PATH` | Répertoire des prédictions | `predictions` | `predictions` |

### Variables optionnelles

| Variable | Description | Défaut |
|----------|-------------|--------|
| `DEBUG` | Mode debug | `false` |
| `LOG_LEVEL` | Niveau de log | `INFO` |
| `REDIS_URL` | Cache Redis | `redis://localhost:6379` |
| `MLFLOW_TRACKING_URI` | Tracking ML | `http://localhost:5000` |
| `MINIO_ENDPOINT` | Stockage S3 | `localhost:9000` |

## Utilisation dans le Code

### Import

```python
from nba.config import settings
```

### Chemins de base

```python
# Répertoires de données
settings.data_root        # Path("data")
settings.data_raw         # Path("data/raw")
settings.data_silver      # Path("data/silver")
settings.data_gold        # Path("data/gold")
settings.data_exports     # Path("data/exports")

# Répertoires ML
settings.model_path               # Path("models")
settings.model_optimized_path     # Path("models/optimized")
settings.predictions_path         # Path("predictions")
settings.data_ml_features         # Path("data/gold/ml_features")
```

### Chemins spécifiques (calculés)

```python
# Fichiers de features
settings.features_v3_path         # data/gold/ml_features/features_v3.parquet

# Modèles
settings.model_xgb_path           # models/optimized/model_xgb.joblib
settings.model_rf_path            # models/optimized/model_rf.joblib
settings.calibrator_xgb_path      # models/optimized/calibrator_xgb.joblib

# Configuration
settings.selected_features_path   # models/optimized/selected_features.json
settings.training_summary_path    # models/optimized/training_summary.json

# Données
settings.team_mapping_path        # data/team_name_to_id.json

# Prédictions
settings.tracking_history_path    # predictions/tracking_history.csv
settings.latest_predictions_path  # predictions/latest_predictions_optimized.csv
```

### Configuration API

```python
settings.api_host    # "0.0.0.0"
settings.api_port    # 8000
settings.api_workers # 1
```

### Configuration Base de données

```python
settings.database_url           # PostgreSQL DSN
settings.database_async_url     # Version async (asyncpg)
settings.database_pool_size     # 10
settings.database_max_overflow  # 20
```

## Validation

### Vérification des chemins critiques

```python
from nba.config import settings

# Valider que tous les chemins critiques existent
result = settings.validate_critical_paths()

if result['valid']:
    print("✅ Tous les chemins sont valides")
else:
    print(f"❌ Chemins manquants:")
    for missing in result['missing']:
        print(f"  - {missing}")
```

### Propriétés d'environnement

```python
# Vérifier l'environnement
if settings.is_development:
    print("Mode développement")

if settings.is_production:
    print("Mode production")
```

## Migration depuis l'ancien système

### Avant (hardcoded)

```python
# ❌ Ancienne méthode - chemins en dur
model_path = Path("models/optimized/model_xgb.joblib")
features_path = "data/gold/ml_features/features_v3.parquet"
predictions_dir = "predictions/"
```

### Après (configuration)

```python
# ✅ Nouvelle méthode - via settings
from nba.config import settings

model_path = settings.model_xgb_path
features_path = settings.features_v3_path
predictions_dir = settings.predictions_path
```

## Dépannage

### Erreur: "No module named 'joblib'"

**Cause**: Python 3.14 utilisé au lieu de 3.11

**Solution**:
```bash
# Vérifier la version
python --version  # Si 3.14, changer

# Utiliser Python 3.11
python3.11 -m pip install joblib scikit-learn xgboost

# Vérifier
python3.11 -c "import joblib; print('OK')"
```

### Erreur: "Path does not exist"

**Cause**: Répertoires manquants

**Solution**:
```bash
# Créer les répertoires manquants
mkdir -p data/gold/ml_features
mkdir -p models/optimized
mkdir -p predictions
```

### Erreur: "Failed to read .env"

**Cause**: Fichier .env mal formé

**Solution**:
```bash
# Vérifier le format
# ❌ Mauvais
DATABASE_URL = postgresql://nba:nba@localhost:5432/nba  # Espaces!

# ✅ Bon
DATABASE_URL=postgresql://nba:nba@localhost:5432/nba

# Pas de quotes, pas d'espaces autour du =
```

## Bonnes pratiques

1. **Ne jamais committer `.env`** - Déjà dans `.gitignore`
2. **Utiliser `.env.example`** comme template
3. **Toujours utiliser `settings`** au lieu de chemins en dur
4. **Vérifier les chemins** au démarrage des scripts critiques
5. **Documenter** les nouvelles variables dans `.env.example`

## Références

- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [python-dotenv](https://saurabh-kumar.com/python-dotenv/)
- [Fichier .env.example](../.env.example) - Template complet

---

**Dernière mise à jour**: 2026-02-09  
**Version**: 2.0  
**Ticket associé**: NBA-29 (Configuration centralisée)
