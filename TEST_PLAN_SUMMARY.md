# 🧪 Plan de Tests Complet - NBA-29

## 📊 Vue d'Ensemble

**Total:** 58+ tests créés sur 7 fichiers

| Catégorie | Fichiers | Tests | Statut |
|-----------|----------|-------|--------|
| **Tests Unitaires** | 3 | 23 | ✅ Créé |
| **Tests Intégration** | 3 | 24 | ✅ Créé |
| **Tests Docker** | 1 | 6 | ✅ Créé |
| **Tests E2E** | 1 | 5 | ✅ Créé |
| **TOTAL** | **8** | **58** | ✅ **Prêt** |

---

## 📁 Structure des Tests

```
tests/
├── unit/                           # Tests unitaires (isolés)
│   ├── test_config.py             # ✅ 8 tests - Configuration
│   ├── test_reporting.py          # ✅ 9 tests - Catalog & Exporters
│   └── test_exporters_advanced.py # ✅ 6 tests - Exporters avancés
│
├── integration/                    # Tests intégration
│   ├── test_api.py                # ✅ 10 tests - FastAPI
│   ├── test_cli.py                # ✅ 8 tests - CLI Typer
│   └── test_catalog_real.py       # ✅ 6 tests - Catalog données réelles
│
├── e2e/                           # Tests end-to-end
│   ├── test_docker.py             # ✅ 6 tests - Infrastructure Docker
│   └── test_pipeline.py           # ✅ 5 tests - Pipeline complet
│
└── conftest.py                    # Configuration pytest
```

---

## 🚀 Commandes d'Exécution

### Option 1: Script Automatisé (Recommandé)

```bash
# Tests de base (sans Docker)
./run_all_tests.sh

# Tests avec Docker
./run_all_tests.sh --docker

# Tests complets (Docker + E2E)
./run_all_tests.sh --docker --e2e
```

### Option 2: Manuel par Phase

#### Phase 1: Installation
```bash
# Installer dépendances
pip install pydantic-settings typer fastapi uvicorn rich pandas pyarrow pytest httpx

# Rendre le script exécutable (Unix/Mac)
chmod +x run_all_tests.sh
```

#### Phase 2: Tests Unitaires
```bash
# Test Configuration
pytest tests/unit/test_config.py -v

# Test Reporting (Catalog & Exporters)
pytest tests/unit/test_reporting.py -v

# Test Exporters Avancés
pytest tests/unit/test_exporters_advanced.py -v
```

#### Phase 3: Tests Intégration
```bash
# Test API
pytest tests/integration/test_api.py -v

# Test CLI
pytest tests/integration/test_cli.py -v

# Test Catalog avec données réelles
pytest tests/integration/test_catalog_real.py -v
```

#### Phase 4: Tests Docker (si Docker disponible)
```bash
# Démarrer stack
docker-compose up -d postgres redis api
sleep 20

# Lancer tests
pytest tests/e2e/test_docker.py -v

# Arrêter
docker-compose down
```

#### Phase 5: Tests E2E
```bash
# Pipeline end-to-end
pytest tests/e2e/test_pipeline.py -v
```

#### Phase 6: Démonstration
```bash
# Script démo
python demo_nba29.py
```

---

## 📋 Détails des Tests

### 📝 Tests Unitaires (23 tests)

#### `test_config.py` (8 tests)
- ✅ `test_settings_default_values` - Valeurs par défaut
- ✅ `test_settings_from_env_vars` - Chargement env vars
- ✅ `test_database_url_parsing` - Parsing URL DB
- ✅ `test_paths_creation` - Création chemins auto
- ✅ `test_environment_detection` - Détection environnement
- ✅ `test_settings_singleton` - Pattern singleton
- ✅ `test_invalid_environment` - Validation erreurs
- ✅ `test_database_async_url` - URL async

#### `test_reporting.py` (9 tests)
- ✅ `test_init_creates_database` - Création BDD
- ✅ `test_register_and_retrieve_dataset` - CRUD datasets
- ✅ `test_list_datasets` - Listage
- ✅ `test_export_history` - Historique exports
- ✅ `test_parquet_exporter` - Export Parquet
- ✅ `test_csv_exporter` - Export CSV
- ✅ `test_json_exporter` - Export JSON
- ✅ `test_partitioned_export` - Partitionnement
- ✅ `test_get_exporter_factory` - Factory pattern

#### `test_exporters_advanced.py` (6 tests)
- ✅ `test_parquet_compression_options` - Options compression
- ✅ `test_export_with_null_values` - Valeurs null
- ✅ `test_export_large_dataset` - Performance volume
- ✅ `test_csv_encoding_utf8` - Encodage UTF-8
- ✅ `test_json_datetime_handling` - Gestion dates
- ✅ `test_exporter_error_handling` - Gestion erreurs

### 🔗 Tests Intégration (24 tests)

#### `test_api.py` (10 tests)
- ✅ `test_api_root_endpoint` - Endpoint racine
- ✅ `test_health_check` - Health check
- ✅ `test_list_datasets_empty` - Liste vide
- ✅ `test_list_datasets_with_data` - Liste avec données
- ✅ `test_get_dataset_info_not_found` - Dataset inexistant
- ✅ `test_get_dataset_info_success` - Dataset trouvé
- ✅ `test_export_endpoint_parquet` - Export Parquet
- ✅ `test_export_endpoint_csv` - Export CSV
- ✅ `test_export_endpoint_invalid_format` - Format invalide
- ✅ `test_scan_catalog_endpoint` - Scan catalog

#### `test_cli.py` (8 tests)
- ✅ `test_cli_version` - Commande version
- ✅ `test_cli_info` - Commande info
- ✅ `test_cli_catalog_list` - Catalog list
- ✅ `test_cli_catalog_scan` - Catalog scan
- ✅ `test_cli_export_command` - Export command
- ✅ `test_cli_pipeline_ingest` - Pipeline ingest
- ✅ `test_cli_main_help` - Help principal
- ✅ `test_cli_subcommand_help` - Help sous-commandes

#### `test_catalog_real.py` (6 tests)
- ✅ `test_scan_real_datasets` - Scan datasets réels
- ✅ `test_register_real_export` - Export réel
- ✅ `test_export_history_persistence` - Persistance
- ✅ `test_catalog_with_existing_data` - Données existantes
- ✅ `test_dataset_schema_extraction` - Extraction schéma
- ✅ `test_multiple_exports_same_dataset` - Multi-exports

### 🐳 Tests Docker (6 tests)

#### `test_docker.py` (6 tests)
- ✅ `test_postgres_connection` - Connexion PostgreSQL
- ✅ `test_redis_connection` - Connexion Redis
- ✅ `test_api_health_via_docker` - Health API via Docker
- ✅ `test_services_up` - Services démarrés
- ✅ `test_docker_compose_syntax` - Syntaxe compose
- ✅ `test_services_defined` - Services définis

### 🎯 Tests E2E (5 tests)

#### `test_pipeline.py` (5 tests)
- ✅ `test_full_export_workflow` - Workflow complet
- ✅ `test_multi_format_export` - Multi-formats
- ✅ `test_partitioned_export_e2e` - Export partitionné
- ✅ `test_catalog_to_export_flow` - Flux catalog→export
- ✅ `test_incremental_export` - Export incrémental

---

## ⚙️ Prérequis

### Dépendances Python
```bash
pip install pydantic-settings typer fastapi uvicorn rich pandas pyarrow pytest httpx
```

### Dépendances Optionnelles (pour Docker)
- Docker Engine 20.10+
- Docker Compose 2.0+

---

## 🎯 Objectifs de Tests

### Couverture Attendue
- **nba/config.py**: 95%
- **nba/cli.py**: 90%
- **nba/api/main.py**: 85%
- **nba/reporting/catalog.py**: 90%
- **nba/reporting/exporters.py**: 88%
- **MOYENNE**: 90%

### Critères de Réussite
- ✅ Tous les tests passent (100%)
- ✅ Couverture > 85%
- ✅ Pas d'erreurs critiques
- ✅ Pas de régressions

---

## 🐛 Dépannage

### Erreur: ModuleNotFoundError
```bash
# Installer les dépendances manquantes
pip install pydantic-settings typer fastapi uvicorn rich pandas pyarrow
```

### Erreur: Docker non disponible
```bash
# Sauter les tests Docker
pytest tests/unit tests/integration -v
```

### Erreur: Tests lents
```bash
# Exclure tests lents
pytest tests/unit -v -m "not slow"
```

---

## 📊 Rapport de Tests

### Format de Sortie
```bash
# Sortie détaillée
pytest tests/ -v --tb=short

# Avec couverture
pytest tests/ --cov=nba --cov-report=html

# Uniquement échecs
pytest tests/ -v --tb=line --lf
```

### Métriques
- **Temps d'exécution estimé**: 2-5 minutes
- **Tests unitaires**: ~30s
- **Tests intégration**: ~1min
- **Tests Docker**: ~2min (si actifs)
- **Tests E2E**: ~1min

---

## ✅ Checklist Validation

Avant de marquer NBA-29 comme terminé:

- [ ] Tests unitaires: 23/23 passent
- [ ] Tests intégration: 24/24 passent
- [ ] Tests Docker: 6/6 passent (si applicable)
- [ ] Tests E2E: 5/5 passent
- [ ] Script `run_all_tests.sh` s'exécute sans erreur
- [ ] Démonstration `demo_nba29.py` fonctionne
- [ ] Couverture > 85%
- [ ] Documentation à jour

---

## 🚀 Prochaines Étapes

### Exécuter les tests maintenant:
```bash
# Mode rapide (sans Docker)
./run_all_tests.sh

# Mode complet (avec Docker)
./run_all_tests.sh --docker --e2e
```

### Après validation:
1. ✅ Valider que tous les tests passent
2. ✅ Merger dans la branche principale
3. ✅ Passer à NBA-30 (Rapports hebdomadaires)

---

**🏆 NBA-29 PRÊT POUR TESTS!**

Tous les fichiers sont créés et prêts à être exécutés.
Lancez `./run_all_tests.sh` pour valider l'implémentation!
