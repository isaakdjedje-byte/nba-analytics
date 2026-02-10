# Architecture V2.0 - NBA Analytics Platform

**Version**: 2.0.1  
**Date**: 09/02/2026  
**Statut**: Production Ready + Optimisations

---

## Vue d'Ensemble

L'architecture V2.0 représente une refonte complète du projet NBA Analytics, passant d'une collection de scripts à une **plateforme professionnelle** avec architecture package, API REST, CLI unifiée et infrastructure Docker.

### Philosophy

- **Zero Budget**: 100% open source, tout en local
- **Professional Grade**: Standards enterprise (tests, monitoring, CI/CD ready)
- **Scalable**: Facilement extensible vers le cloud
- **Modular**: Packages indépendants, interfaces claires

### 🎯 Mise à Jour 09/02/2026

**Nouveautés majeures** :
- ✅ **Intégration NBA-23** : Mapping archetypes joueurs → équipes
- ✅ **Features harmonisées** : 94 features identiques sur tous les datasets
- ✅ **Data Leakage corrigé** : Split temporel strict, 83.03% accuracy
- ✅ **Filtre confiance** : Système de grading A+/A/B/C
- ✅ **Analyse temporelle** : Compréhension par période 2025-26

---

## Architecture en Couches

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERFACES UTILISATEUR                    │
├─────────────────────────────────────────────────────────────┤
│  CLI (Typer)        API REST (FastAPI)       Dashboard      │
│  nba/cli.py         nba/api/main.py          Streamlit      │
└────────────────────┬─────────────────────┬──────────────────┘
                     │                     │
┌────────────────────▼─────────────────────▼──────────────────┐
│                    COUCHE MÉTIER (Domain)                    │
├─────────────────────────────────────────────────────────────┤
│  Reporting & BI (NBA-29)       Core Business Logic          │
│  ├── Data Catalog (SQLite)     ├── Ingestion (NBA-11-16)    │
│  ├── Exporters (P/C/J/D)       ├── Processing (NBA-17-21)   │
│  └── Validation                └── ML Pipeline (NBA-22-25)  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    INFRASTRUCTURE                            │
├─────────────────────────────────────────────────────────────┤
│  Configuration (Pydantic)      Database (PostgreSQL/SQLite) │
│  Logging (Rich/JSON)           Cache (Redis)                │
│  Storage (MinIO S3)            Message Queue (RabbitMQ)     │
└─────────────────────────────────────────────────────────────┘
```

---

## Structure des Packages

### Package Principal: `nba/`

```python
nba/
├── __init__.py                 # Version et exports
├── config.py                   # Configuration centralisée
├── cli.py                      # Interface ligne de commande
│
├── api/                        # API REST
│   ├── __init__.py
│   ├── main.py                 # Application FastAPI
│   ├── routers/                # Routeurs endpoints
│   │   ├── datasets.py         # CRUD datasets
│   │   ├── exports.py          # Export endpoints
│   │   └── health.py           # Health checks
│   └── middleware/             # Middleware (auth, CORS)
│       ├── cors.py
│       └── logging.py
│
├── core/                       # Logique métier
│   ├── __init__.py
│   ├── ingestion/              # NBA-11 à NBA-16
│   │   ├── __init__.py
│   │   ├── players.py
│   │   ├── teams.py
│   │   └── games.py
│   ├── processing/             # NBA-17 à NBA-21
│   │   ├── __init__.py
│   │   ├── cleaning.py
│   │   ├── metrics.py          # PER, TS%, USG%
│   │   └── aggregations.py     # NBA-19
│   ├── ml/                     # NBA-22 à NBA-25
│   │   ├── __init__.py
│   │   ├── pipeline.py         # Prédictions
│   │   ├── training.py         # Entraînement
│   │   ├── archetypes.py       # Clustering NBA-23
│   │   └── features.py         # Feature engineering
│   └── utils/                  # Utilitaires
│       ├── __init__.py
│       ├── logger.py
│       └── validators.py
│
├── reporting/                  # NBA-29 - Export BI
│   ├── __init__.py
│   ├── catalog.py              # Data Catalog SQLite
│   ├── exporters.py            # Exporters P/C/J/D
│   ├── validation.py           # Validation qualité
│   └── bi_tools/               # Connecteurs BI
│       ├── tableau.py
│       ├── powerbi.py
│       └── looker.py
│
└── dashboard/                  # Streamlit (NBA-31)
    ├── __init__.py
    ├── main.py
    ├── pages/
    │   ├── overview.py
    │   ├── players.py
    │   ├── teams.py
    │   └── predictions.py
    └── components/
        ├── charts.py
        └── tables.py
```

### Couche Core (Migration depuis `src/`)

Le code legacy dans `src/` sera progressivement migré vers `nba/core/`:

```
Migration plan:
src/ingestion/      → nba/core/ingestion/
src/processing/     → nba/core/processing/
src/ml/            → nba/core/ml/
src/utils/         → nba/core/utils/
```

**Compatibilité**: Phase de transition où les deux coexistent (`nba/` pour nouveau code, `src/` pour legacy).

---

## Composants Clés

### 1. Configuration (Pydantic Settings)

**Fichier**: `nba/config.py`

**Configuration via fichier .env:**
```bash
# .env (NON versionné)
ENVIRONMENT=development
API_PORT=8000
DATABASE_URL=postgresql://nba:nba@localhost:5432/nba
DATA_ROOT=data
MODEL_PATH=models
PREDICTIONS_PATH=predictions
```

**Utilisation dans le code:**
```python
from nba.config import settings

# Chemins de base
settings.data_root                    # data/
settings.data_gold                    # data/gold/

# Chemins ML (calculés automatiquement)
settings.model_optimized_path         # models/optimized/
settings.features_v3_path             # data/gold/ml_features/features_v3.parquet
settings.model_xgb_path               # models/optimized/model_xgb.joblib
settings.predictions_path             # predictions/
settings.latest_predictions_path      # predictions/latest_predictions_optimized.csv

# Configuration API
settings.api_host                     # 0.0.0.0
settings.api_port                     # 8000

# Validation des chemins
result = settings.validate_critical_paths()
if not result['valid']:
    print(f"Chemins manquants: {result['missing']}")
```

**Avantages**:
- ✅ Validation automatique des types
- ✅ Chargement depuis `.env` et variables d'environnement
- ✅ Chemins calculés automatiquement
- ✅ Singleton avec cache (@lru_cache)
- ✅ Validation des chemins critiques
- ✅ Plus de chemins en dur dans le code

### 2. Data Catalog (SQLite)

**Fichier**: `nba/reporting/catalog.py`

**Architecture**:
```
┌─────────────────────────────────────┐
│         Data Catalog                │
│         (SQLite)                    │
├─────────────────────────────────────┤
│  datasets                           │
│  ├── id (PK)                        │
│  ├── name (unique)                  │
│  ├── format (parquet/csv/json)      │
│  ├── path                           │
│  ├── record_count                   │
│  ├── size_bytes                     │
│  ├── schema_json (DDL)              │
│  ├── metadata_json                  │
│  └── updated_at                     │
│                                     │
│  exports                            │
│  ├── id (PK)                        │
│  ├── dataset_name (FK)              │
│  ├── format                         │
│  ├── export_path                    │
│  ├── exported_at                    │
│  └── metadata_json                  │
└─────────────────────────────────────┘
```

**Usage**:
```python
from nba.reporting.catalog import DataCatalog

catalog = DataCatalog()

# Scan automatique
count = catalog.scan_datasets("data/gold/")
print(f"{count} datasets découverts")

# Lister
datasets = catalog.list_datasets()
for ds in datasets:
    print(f"{ds.name}: {ds.record_count} records")

# Historique exports
history = catalog.get_export_history("players")
```

### 3. Exporters

**Pattern**: Factory + Strategy

```python
from nba.reporting.exporters import get_exporter

# Factory
exporter = get_exporter("parquet")  # ou "csv", "json", "delta"

# Export
result = exporter.export(
    dataset="players",
    output_dir=Path("data/exports"),
    partition_by="season",      # Optionnel
    compression="snappy"        # Optionnel
)
```

**Hiérarchie**:
```
BaseExporter (ABC)
    ├── ParquetExporter
    ├── CSVExporter
    ├── JSONExporter
    └── DeltaExporter
```

### 4. API REST (FastAPI)

**Pattern**: Router-based

```python
# nba/api/main.py
from fastapi import FastAPI
from nba.api.routers import datasets, exports, health

app = FastAPI()

app.include_router(health.router)
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(exports.router, prefix="/api/v1")
```

**Endpoints**:

| Méthode | Path | Description | Auth |
|---------|------|-------------|------|
| GET | `/` | Info API | Non |
| GET | `/health` | Health check | Non |
| GET | `/api/v1/datasets` | Lister datasets | Non |
| GET | `/api/v1/datasets/{name}` | Détails dataset | Non |
| POST | `/api/v1/export` | Exporter données | Non |
| POST | `/api/v1/catalog/scan` | Scanner catalogue | Non |

**Documentation auto**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 5. CLI (Typer)

**Pattern**: Commandes imbriquées

```python
# nba/cli.py
import typer

app = typer.Typer()

@app.command()
def export(dataset: str, format: str = "parquet"):
    """Exporter des données"""
    ...

# Sous-commandes
dev_app = typer.Typer()
app.add_typer(dev_app, name="dev")

@dev_app.command("api")
def dev_api():
    """Lancer API dev"""
    ...
```

**Arbre des commandes**:

```
nba
├── version              # Version applicative
├── info                 # Informations détaillées
├── export               # Export BI
│   ├── <dataset>        # Nom du dataset
│   ├── --format         # parquet/csv/json
│   ├── --output         # Répertoire sortie
│   └── --partition      # Colonne partitionnement
├── catalog              # Gestion catalogue
│   ├── list             # Lister datasets
│   ├── scan             # Scanner répertoire
│   └── show             # Détails dataset
├── predict              # Prédictions ML
├── train                # Entraînement
├── dashboard            # Lancer Streamlit
├── pipeline             # Pipelines données
│   ├── ingest
│   ├── process
│   └── full
└── dev                  # Commandes dev
    └── api              # Lancer API
```

---

## Infrastructure Docker

### Services (10 conteneurs)

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Application
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - minio
  
  dashboard:
    build: .
    ports:
      - "8501:8501"
    command: streamlit run nba/dashboard/main.py
  
  # Data
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: nba
      POSTGRES_PASSWORD: nba
  
  redis:
    image: redis:7-alpine
  
  minio:
    image: minio/minio
    command: server /data
    ports:
      - "9000:9000"
      - "9001:9001"
  
  # ML
  mlflow:
    image: python:3.11-slim
    command: mlflow server
    ports:
      - "5000:5000"
  
  # Workers
  worker:
    build: .
    command: celery -A nba.tasks worker
  
  beat:
    build: .
    command: celery -A nba.tasks beat
  
  # Monitoring
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

### Flux de données

```
API Request
    ↓
FastAPI Router
    ↓
Service Layer (nba/core/)
    ↓
Data Access (SQLAlchemy / Pandas)
    ↓
Storage (PostgreSQL / Parquet / MinIO)
```

---

## Patterns de Conception

### 1. Repository Pattern

```python
# nba/core/repositories/base.py
from abc import ABC, abstractmethod

class BaseRepository(ABC):
    @abstractmethod
    def get(self, id: int):
        pass
    
    @abstractmethod
    def list(self, **filters):
        pass
    
    @abstractmethod
    def create(self, data: dict):
        pass

# Implémentation
class PlayerRepository(BaseRepository):
    def __init__(self, db_session):
        self.db = db_session
    
    def get(self, id: int):
        return self.db.query(Player).get(id)
```

### 2. Service Layer

```python
# nba/core/services/export_service.py
class ExportService:
    def __init__(self, catalog: DataCatalog, exporters: Dict):
        self.catalog = catalog
        self.exporters = exporters
    
    async def export_dataset(self, name: str, format: str):
        # Validation
        dataset = self.catalog.get_dataset_info(name)
        if not dataset:
            raise DatasetNotFoundError(name)
        
        # Export
        exporter = self.exporters[format]
        result = exporter.export(name)
        
        # Mise à jour catalogue
        self.catalog.register_export(name, format, result)
        
        return result
```

### 3. Dependency Injection

```python
# nba/api/dependencies.py
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_catalog(db: Session = Depends(get_db)):
    return DataCatalog(db)

# Usage
@app.get("/api/v1/datasets")
def list_datasets(catalog: DataCatalog = Depends(get_catalog)):
    return catalog.list_datasets()
```

---

## Sécurité

### Bonnes pratiques implémentées

1. **Configuration**:
   - Secrets via variables d'environnement
   - Pas de credentials dans le code
   - `.env` fichier ignoré par git

2. **API**:
   - CORS configuré
   - Validation Pydantic (injection SQL impossible)
   - Pas d'exposition de stack trace en production

3. **Docker**:
   - Images basées sur Alpine (surface d'attaque minime)
   - Pas de privilèges root
   - Secrets via Docker Secrets (production)

---

## Performance

### Optimisations

1. **Caching**:
   - Redis pour cache API
   - Cache des settings (singleton)
   - Cache des datasets fréquemment accédés

2. **Base de données**:
   - Index sur colonnes recherchées
   - Partitionnement par saison
   - Lazy loading des relations

3. **Exports**:
   - Compression Snappy (parquet)
   - Partitionnement pour requêtes filtrées
   - Streaming pour gros fichiers

---

## Tests

### Architecture de tests

```
tests/
├── unit/                    # Tests unitaires (33)
│   ├── test_config.py
│   ├── test_services/
│   └── test_repositories/
├── integration/             # Tests intégration (34)
│   ├── test_api/
│   ├── test_cli/
│   └── test_database/
├── e2e/                    # Tests E2E (11)
│   ├── test_docker/
│   └── test_pipeline/
└── fixtures/               # Données de test
    ├── datasets/
    └── mocks/
```

### Couverture

- **Objectif**: > 80%
- **Actuel**: ~90%
- **Outils**: pytest, pytest-cov, pytest-asyncio

---

## Migration depuis V1

### Stratégie

1. **Phase 1**: Créer structure `nba/` ✅
2. **Phase 2**: Implémenter nouvelles fonctionnalités dans `nba/` ✅
3. **Phase 3**: Tests complets ✅
4. **Phase 4**: Migrer code legacy `src/` → `nba/core/` (en cours)
5. **Phase 5**: Supprimer `src/` une fois migration terminée

### Compatibilité

```python
# src/legacy_module.py (ancien)
from processing.clean_data import clean_players

# nba/core/processing/cleaning.py (nouveau)
from nba.core.processing.cleaning import clean_players

# Transition: les deux fonctionnent
```

### 6. Système de Backtest Hybride (NOUVEAU 09/02/2026)

**Fichiers**: `scripts/backtest_hybrid_master.py`, `src/ingestion/external_api_nba.py`

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│  Système de Backtest Hybride                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  2024-25 (Complet)              2025-26 (Via API)           │
│  ┌─────────────────────┐       ┌─────────────────────┐      │
│  │ Features V3         │       │ NBA API             │      │
│  │ (1,309 matchs)      │       │ LeagueGameFinder    │      │
│  │                     │       │                     │      │
│  │ • Données complètes │       │ • 783 matchs        │      │
│  │ • Accuracy 77.77%   │       │ • Temps réel        │      │
│  │ • Métriques fiables │       │ • Sans inscription  │      │
│  └──────────┬──────────┘       └──────────┬──────────┘      │
│             │                             │                 │
│             └──────────────┬──────────────┘                 │
│                            │                                │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Pipeline de Backtest                               │    │
│  │  • Chargement modèle XGB V3                         │    │
│  │  • Prédictions avec calibration                     │    │
│  │  • Comparaison résultats réels                      │    │
│  │  • Calcul métriques complètes                       │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                   │
│                         ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Générateur de Rapports                             │    │
│  │  • 5 graphiques SVG (matplotlib)                    │    │
│  │  • Rapport HTML (thème sombre)                      │    │
│  │  • Données JSON + CSV                               │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Composants**:

1. **Récupération API** (`external_api_nba.py`)
   - Tentatives multiples (LeagueGameFinder → Scoreboard → BoxScore)
   - Fallback automatique sur données locales
   - Pas d'inscription requise

2. **Pipeline de Backtest** (`backtest_hybrid_master.py`)
   ```python
   class HybridBacktester:
       def run_phase_complete():
           # 1. Backtest 2024-25 (features V3)
           results_2024_25 = backtest_season('2024-25')
           
           # 2. Backtest 2025-26 (API externe)
           results_2025_26 = backtest_season_api('2025-26')
           
           # 3. Génération rapports
           generate_report(results)
   ```

3. **Génération de Rapports** (`generate_combined_report.py`)
   - Graphiques SVG : tendance, comparaison, distribution
   - Rapport HTML : thème sombre, responsive, français
   - Exports : JSON (brut) + CSV (détaillé)

**Résultats**:

| Saison | Matchs | Accuracy | Méthode | Fiabilité |
|--------|--------|----------|---------|-----------|
| 2024-25 | 1,309 | **77.77%** | Features V3 | ⭐⭐⭐⭐⭐ |
| 2025-26 | 783 | 54.79% | API NBA | ⭐⭐⭐ |

**Scripts**:
```bash
# Backtest complet (10-15 min)
python scripts/backtest_hybrid_master.py --phase complete

# Génération rapport
python scripts/generate_combined_report.py

# MAJ quotidienne (cron 9h)
python scripts/daily_update_2025-26.py
```

**Documentation**: [BACKTEST_SYSTEM.md](BACKTEST_SYSTEM.md)

---

## Roadmap

### V2.1 (Prochaine)
- [ ] Migration complète `src/` → `nba/core/`
- [ ] Authentification JWT
- [ ] Tests E2E avec Playwright
- [ ] CI/CD GitHub Actions

### V2.2
- [ ] Cache Redis distribué
- [ ] Websockets pour temps réel
- [ ] GraphQL API
- [ ] Kubernetes deployment

### V3.0
- [ ] Multi-tenant (SaaS)
- [ ] Machine Learning auto-ML
- [ ] Mobile app (React Native)
- [ ] Cloud-native (AWS/GCP/Azure)

---

## Références

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/settings/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

*Document créé le 08/02/2026 - Version 2.0.0*
