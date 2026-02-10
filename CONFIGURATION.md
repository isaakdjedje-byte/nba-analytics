# Configuration NBA Analytics Platform

## Vue d'ensemble

Ce projet utilise Pydantic Settings pour une gestion centralisee et type-safe de la configuration.

Toute configuration passe par `nba.config.settings` qui lit les variables d'environnement et le fichier `.env`.

## Fichier .env

### Creation

```bash
# Copier le template
cp .env.example .env

# Editer avec vos valeurs
nano .env
```

### Variables importantes

| Variable | Description | Defaut |
|----------|-------------|--------|
| ENVIRONMENT | development/staging/production | development |
| API_PORT | Port de l'API REST | 8000 |
| DATABASE_URL | Connexion PostgreSQL | postgresql://nba:nba@localhost:5432/nba |
| DATA_ROOT | Racine des donnees | data |
| MODEL_PATH | Repertoire des modeles | models |
| PREDICTIONS_PATH | Repertoire des predictions | predictions |

## Utilisation

```python
from nba.config import settings

# Chemins automatiques
settings.data_gold
settings.model_optimized_path
settings.predictions_path
settings.features_v3_path
settings.model_xgb_path
settings.latest_predictions_path
```

## Migration depuis l'ancien systeme

### Avant (hardcoded)
```python
model_path = Path("models/optimized/model_xgb.joblib")
features_path = "data/gold/ml_features/features_v3.parquet"
```

### Apres (config)
```python
from nba.config import settings

model_path = settings.model_xgb_path
features_path = settings.features_v3_path
```

## Bonnes pratiques

1. Ne jamais committer `.env` (deja dans .gitignore)
2. Toujours utiliser `settings` au lieu de chemins en dur
3. Verifier les chemins au demarrage des scripts critiques

## Depannage

### Erreur "No module named 'joblib'"
```bash
python3.11 -m pip install joblib scikit-learn xgboost
```

### Erreur "Path does not exist"
```bash
mkdir -p data/gold/ml_features models/optimized predictions
```
