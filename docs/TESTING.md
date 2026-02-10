# Guide de Tests - NBA Analytics Platform

## 🎉 Nouveau - Suite de Tests Complète (NBA-29)

**Version 2.0** - Suite de tests professionnelle avec **67+ tests** organisés en 3 niveaux :

| Niveau | Nombre | Fichiers | Statut |
|--------|--------|----------|--------|
| **Unitaires** | 33 | `tests/unit/*.py` | ✅ Passent |
| **Intégration** | 34 | `tests/integration/*.py` | ✅ Passent |
| **E2E** | 11 | `tests/e2e/*.py` | ✅ Passent |
| **TOTAL** | **78** | | ✅ **100%** |

### Exécution rapide

```bash
# Tous les tests
./run_all_tests.sh

# Uniquement unitaires
pytest tests/unit/ -v

# Avec Docker
./run_all_tests.sh --docker

# Complet (Docker + E2E)
./run_all_tests.sh --docker --e2e
```

### Structure des tests

```
tests/
├── unit/                    # 33 tests
│   ├── test_config.py      # Configuration Pydantic (12)
│   ├── test_reporting.py   # Catalog/Exporters (9)
│   └── test_exporters_advanced.py # Exporters détaillés (12)
│
├── integration/             # 34 tests
│   ├── test_api.py         # FastAPI (10)
│   ├── test_cli.py         # CLI Typer (18)
│   └── test_catalog_real.py # Catalog données réelles (6)
│
└── e2e/                    # 11 tests
    ├── test_docker.py      # Infrastructure Docker (6)
    └── test_pipeline.py    # Pipeline complet (5)
```

### Couverture

- **nba/config.py** : ~95%
- **nba/cli.py** : ~90%
- **nba/api/main.py** : ~85%
- **nba/reporting/catalog.py** : ~90%
- **nba/reporting/exporters.py** : ~88%

---

## Vue d'ensemble (Legacy)

Ce projet utilise **Docker** pour garantir la cohérence entre les environnements de développement, test et production. Les tests nécessitant Apache Spark et Delta Lake **doivent obligatoirement s'exécuter dans Docker**.

## Pourquoi Docker pour les tests ?

### Architecture du projet
- **Production** : S'exécute dans Docker avec JARs Delta Lake préinstallés
- **Développement** : Jupyter Lab dans Docker sur http://localhost:8888
- **Tests** : Doivent utiliser le même environnement pour garantir la fiabilité

### Problème résolu
Les tests échouaient avec `ClassNotFoundException: delta` car :
- PySpark a besoin des JARs Java pour Delta Lake
- Ces JARs sont installés dans l'image Docker
- Les environnements locaux sans Docker ne les ont pas

## Prérequis

- [Docker](https://docs.docker.com/get-docker/) installé
- [Docker Compose](https://docs.docker.com/compose/install/) installé
- Git Bash (Windows) ou Terminal (Linux/Mac)

## Lancer les tests

### Méthode 1 : Script automatique (Recommandée)

**Linux/Mac :**
```bash
./scripts/run_tests.sh
```

**Windows :**
```batch
scripts\run_tests.bat
```

**Options pytest disponibles :**
```bash
# Lancer un test spécifique
./scripts/run_tests.sh -k test_merge_schema_basic

# Mode verbose
./scripts/run_tests.sh -v

# Avec couverture de code
./scripts/run_tests.sh --cov=src
```

### Méthode 2 : Docker Compose direct

```bash
# Lancer tous les tests
docker-compose run test

# Ou avec le service spark-nba déjà démarré
docker-compose exec spark-nba pytest tests/ -v
```

### Méthode 3 : Commande Docker complète

```bash
docker-compose exec -T spark-nba pytest tests/ -v
```

## Structure des tests

```
tests/
├── conftest.py              # Configuration pytest et fixtures
├── test_schema_evolution.py # Tests NBA-14
└── __init__.py              # (optionnel)
```

### Fixtures disponibles

- `spark_session` : Session Spark configurée avec Delta Lake
- `test_dir` : Répertoire temporaire par test
- `delta_path` : Chemin pour les tests Delta Lake
- `log_path` : Chemin pour les logs YAML

## Tests actuels (NBA-14)

### TestMergeSchema
- `test_merge_schema_basic` : MergeSchema avec ajout de colonne
- `test_merge_schema_multiple_columns` : MergeSchema multi-colonnes

### TestTimeTravel
- `test_read_version_historical` : Lecture version historique
- `test_compare_versions` : Comparaison de versions

### TestFullSchemaEvolution
- `test_full_schema_change_scenario` : Scénario complet V1→V2

### TestSchemaLogger
- `test_log_schema_version` : Logging YAML des versions

### TestSchemaValidation
- `test_validate_schema_success` : Validation réussie
- `test_validate_schema_failure` : Validation échouée

### TestSchemaHistory
- `test_get_schema_history` : Historique des versions Delta

## Workflow de développement

### 1. Démarrer l'environnement
```bash
docker-compose up -d
```

### 2. Accéder à Jupyter (optionnel)
http://localhost:8888

### 3. Lancer les tests
```bash
./scripts/run_tests.sh
```

### 4. Arrêter l'environnement
```bash
docker-compose down
```

## Dépannage

### "Docker n'est pas installé"
Installe Docker Desktop : https://www.docker.com/products/docker-desktop

### "Les conteneurs ne sont pas démarrés"
Le script démarre automatiquement les conteneurs. Sinon :
```bash
docker-compose up -d spark-nba
```

### "Permission denied" sur le script (Linux/Mac)
```bash
chmod +x scripts/run_tests.sh
```

### Tests très lents
C'est normal pour les tests Spark. Le premier test initialise la JVM.

## Bonnes pratiques

1. **Toujours tester dans Docker** pour les opérations Spark/Delta
2. **Utiliser les fixtures** pour la gestion des ressources
3. **Nettoyer après les tests** : les fixtures s'en chargent automatiquement
4. **Documenter les nouveaux tests** avec des docstrings clairs

## Ressources

- [Documentation PySpark Testing](https://spark.apache.org/docs/latest/api/python/getting_started/testing.html)
- [Delta Lake Documentation](https://docs.delta.io/latest/index.html)
- [pytest Documentation](https://docs.pytest.org/)

---

**Dernière mise à jour :** 2026-02-06  
**Auteur :** NBA Analytics Team  
**Version :** 1.0
