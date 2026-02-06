# NBA Analytics Platform

Pipeline Data Engineering complet pour l'analyse de données NBA, combinant Apache Spark, Delta Lake, et architecture moderne.

## 🚀 Démarrage rapide

### Prérequis

- Docker et Docker Compose
- Python 3.11+ (pour utilitaires hors Docker)
- Git

### Lancer l'environnement

```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier que tout fonctionne
docker-compose ps
```

### Accès aux services

- **Jupyter Lab** : http://localhost:8888
- **Spark UI** : http://localhost:4040

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

## 📁 Structure du projet

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

- **Apache Spark 3.5** : Traitement distribué
- **Delta Lake 3.0** : Stockage ACID
- **Docker** : Conteneurisation
- **Pytest** : Tests unitaires
- **Jupyter** : Exploration interactive

## 📚 Documentation

- [Guide de tests](docs/TESTING.md) - Comment lancer et écrire des tests
- [Documentation agent](docs/agent.md) - Architecture et conventions
- [Changelog](docs/memoir.md) - Journal du projet

## 📝 Notes importantes

- **Python 3.14 n'est pas supporté** - Utiliser Python 3.11 ou 3.12
- Les tests Spark **doivent** s'exécuter dans Docker
- Voir [docs/PYTHON_VERSION_FIX.md](docs/PYTHON_VERSION_FIX.md) pour les détails

## 🤝 Contribution

1. Créer une branche feature : `git checkout -b feature/NBA-XX-description`
2. Commiter avec le format : `NBA-XX: Description`
3. Push et créer une Pull Request

## 📄 Licence

Projet privé - NBA Analytics Team
