# NBA Analytics Platform

Pipeline Data Engineering complet pour l'analyse de données NBA, combinant Apache Spark, Delta Lake, et architecture moderne.

## Etat du programme multi-sessions

- Cloture execution J1 -> J13: DONE
- Resume final et source of truth: `docs/execution/FINAL_CLOSURE_SUMMARY.md`

## 🚀 Démarrage rapide

### Prérequis

- **Python 3.11 ou 3.12** (⚠️ Python 3.14 n'est PAS supporté)
- Docker et Docker Compose (optionnel)
- Git

### Installation

```bash
# Cloner le repository
git clone https://github.com/isaakdjedje-byte/nba-analytics.git
cd nba-analytics

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp .env.example .env
# Modifier .env avec vos valeurs
```

### Lancer l'environnement

```bash
# Démarrer tous les services Docker
docker-compose up -d

# Vérifier que tout fonctionne
docker-compose ps
```

### Utilisation CLI

```bash
# Voir la version
nba version

# Lancer les prédictions
python run_predictions_optimized.py

# Lancer l'API
nba dev api

# Exporter des données
nba export team_season_stats --format csv
```

### Accès aux services

- **🏀 Dashboard React** : http://localhost:5173 (**NOUVEAU**)
- **API Backend** : http://localhost:8000
- **Jupyter Lab** : http://localhost:8888
- **Spark UI** : http://localhost:4040

### 🎮 Dashboard Web (React + TypeScript)

Interface utilisateur moderne avec 4 pages :

1. **Dashboard** : Statistiques générales et aperçu
2. **Predictions Week** : Vue calendrier des matchs avec horaires FR
3. **Paper Trading** : Système de paris virtuels avec bankroll
4. **ML Pipeline** : Visualisation du processus ML (4 étapes)

**Démarrage rapide :**
```bash
# Lancer le script de démarrage
start-dashboard.bat

# Ou manuellement
python -m nba.api.main                    # Backend
npm run dev -- --host                     # Frontend
```

## 🧪 Tests

### Lancer les tests (Méthode recommandée)

**Linux/Mac :**
```bash
./scripts/run_tests.sh
```

**Windows :**
```batch
scripts\run_tests.bat
```

### Options disponibles

```bash
# Test spécifique
./scripts/run_tests.sh -k test_merge_schema_basic

# Mode verbose
./scripts/run_tests.sh -v

# Avec couverture
./scripts/run_tests.sh --cov=src
```

### Méthodes alternatives

```bash
# Via Docker Compose
docker-compose run test

# Directement dans le conteneur
docker-compose exec spark-nba pytest tests/ -v
```

> 📚 **Documentation complète des tests** : [docs/TESTING.md](docs/TESTING.md)

## ⚙️ Configuration

Le projet utilise un **système de configuration centralisée** via Pydantic Settings et fichier `.env`.

```bash
# Copier le template
cp .env.example .env

# Modifier avec vos valeurs
```

**Variables importantes:**
- `ENVIRONMENT`: development/staging/production
- `API_PORT`: Port de l'API (8000)
- `DATABASE_URL`: Connexion PostgreSQL
- `DATA_ROOT`, `MODEL_PATH`, `PREDICTIONS_PATH`: Chemins des données

**Utilisation dans le code:**
```python
from nba.config import settings

# Chemins automatiques
settings.model_xgb_path          # models/optimized/model_xgb.joblib
settings.features_v3_path        # data/gold/ml_features/features_v3.parquet
settings.latest_predictions_path # predictions/latest_predictions_optimized.csv
```

[Voir le guide complet](docs/CONFIGURATION.md)

## 📁 Structure du projet

```
nba-analytics/
├── nba/                     # Package principal (NOUVEAU - Architecture V2)
│   ├── config.py           # Configuration centralisée (Pydantic)
│   ├── cli.py              # CLI unifiée
│   ├── api/                # API REST FastAPI
│   └── reporting/          # Data Catalog & Exporters
├── src/                    # Code source (legacy)
│   ├── ingestion/         # Scripts d'ingestion
│   ├── utils/             # Utilitaires
│   └── config/            # Configuration
├── tests/                 # Tests pytest (82 tests)
├── docs/                  # Documentation
│   ├── CONFIGURATION.md   # Guide configuration
│   ├── API_REFERENCE.md   # Référence API
│   ├── CLI_REFERENCE.md   # Référence CLI
│   ├── INSTALLATION.md    # Guide installation
│   └── stories/           # Stories JIRA détaillées
├── data/                  # Données
│   ├── gold/             # Données traitées
│   └── exports/          # Exports BI
├── .env.example          # Template configuration
├── docker-compose.yml    # Configuration Docker
└── run_predictions_optimized.py  # Pipeline ML
```
nba-analytics/
├── src/                    # Code source
│   ├── ingestion/         # Scripts d'ingestion
│   ├── utils/             # Utilitaires
│   └── config/            # Configuration
├── tests/                 # Tests pytest
├── docs/                  # Documentation
├── data/                  # Données
│   ├── raw/              # Données brutes
│   └── processed/        # Données traitées
├── scripts/              # Scripts utilitaires
├── docker-compose.yml    # Configuration Docker
└── Dockerfile            # Image Docker
```

## 🏗️ Architecture

- **Apache Spark 3.5** : Traitement distribue
- **Delta Lake 3.0** : Stockage ACID
- **nba-api 1.1.11** : Wrapper Python pour l'API NBA officielle
- **Docker** : Conteneurisation
- **Pytest** : Tests unitaires
- **Jupyter** : Exploration interactive

```
[nba-api] ←→ [NBA.com] ←→ [Donnees officielles]
    ↓
[Scripts Python] ←→ [PySpark]
    ↓
[data/raw/] ←→ [Delta Lake] ←→ [Analyses]
```

## 📚 Documentation

### Documentation technique

- [Guide d'installation](docs/INSTALLATION.md) - Installation complète et dépannage
- [Documentation API](docs/API_INGESTION.md) - Guide complet de l'API NBA (endpoints, rate limiting, exemples)
- [Exemples pratiques](docs/EXAMPLES.md) - 6 exemples de code Python testes
- [Guide de tests](docs/TESTING.md) - Comment lancer et écrire des tests

### Architecture et projet

- [Documentation agent](docs/agent.md) - Architecture, conventions, formules NBA
- [Changelog](docs/memoir.md) - Journal du projet
- [Index documentation](docs/INDEX.md) - Navigation rapide

### Stack technique

- **Python 3.11+** (Python 3.14 non supporte)
- **PySpark 3.5** - Traitement distribue
- **Delta Lake 3.0** - Stockage ACID
- **nba-api 1.1.11** - API NBA officielle
- **Docker** - Conteneurisation
- **Pytest** - Tests unitaires
- **Jupyter** - Exploration interactive

## 📝 Notes importantes

- **Python 3.14 n'est pas supporté** - Utiliser Python 3.11 ou 3.12
- Les tests Spark **doivent** s'exécuter dans Docker
- Voir [docs/PYTHON_VERSION_FIX.md](docs/PYTHON_VERSION_FIX.md) pour les détails

## 🎯 Progression Actuelle (06/02/2026)

### ✅ Complété (6 tickets)
- **NBA-11 à NBA-16** : Ingestion données, documentation
- **NBA-15** : 30 équipes, 532 joueurs, 2624 matchs
- **NBA-17** : Nettoyage optimisé (filtre 2000-2026, ~1,100 joueurs)

### 🟡 En Cours
- **NBA-17** : Finalisation (10-12 min restantes)

### 📊 Structure ML Prête
- ✅ 3 notebooks Jupyter (classification, régression, clustering)
- ✅ Module `src/ml/` avec classes PySpark
- ✅ ~1,100 joueurs (2000-2026) avec données complètes

### ⏱️ Prochainement
- **NBA-18** : Métriques avancées (PER, TS%, USG%)
- **NBA-22** : 3 modèles ML (priorité: classification > régression > clustering)

**Statut :** 🟢 42% complété - Phase ML prête à démarrer

## 🤝 Contribution

1. Créer une branche feature : `git checkout -b feature/NBA-XX-description`
2. Commiter avec le format : `NBA-XX: Description`
3. Push et créer une Pull Request

## 📄 Licence

Projet privé - NBA Analytics Team
