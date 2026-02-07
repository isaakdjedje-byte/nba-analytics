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
│   ├── API_INGESTION.md   # Documentation API (NBA-16)
│   ├── INSTALLATION.md    # Guide installation (NBA-16)
│   ├── EXAMPLES.md        # Exemples pratiques (NBA-16)
│   ├── TESTING.md         # Guide tests
│   ├── agent.md           # Architecture
│   ├── memoir.md          # Journal projet
│   └── stories/           # Stories JIRA detaillees
├── data/                  # Donnees
│   ├── raw/              # Donnees brutes
│   └── processed/        # Donnees traitees
├── scripts/              # Scripts utilitaires
├── docker-compose.yml    # Configuration Docker
└── Dockerfile            # Image Docker
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
