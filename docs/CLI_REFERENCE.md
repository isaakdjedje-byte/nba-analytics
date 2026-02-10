# Référence CLI - NBA Analytics Platform

**Version**: 2.0.0  
**Commande**: `nba`  
**Aide**: `nba --help`

---

## Installation

```bash
# Installation des dépendances
pip install pydantic-settings typer fastapi uvicorn rich pandas pyarrow

# Rendre exécutable (optionnel)
chmod +x nba/cli.py

# Configuration (IMPORTANT)
cp .env.example .env
# Modifier .env avec vos valeurs
```

---

## Commandes Principales

### `nba version`
Affiche la version de l'application.

```bash
$ nba version

NBA Analytics Platform v2.0.0
Environment: development
```

**Options**: Aucune

---

### `nba info`
Affiche les informations détaillées du projet.

```bash
$ nba info

NBA Analytics Platform
Version: 2.0.0
Environment: development
Debug: False
```

**Options**: Aucune

---

### `nba export`
Exporte les données pour BI (NBA-29).

**Usage**:
```bash
nba export <DATASET> [OPTIONS]
```

**Arguments**:
| Argument | Description | Obligatoire |
|----------|-------------|-------------|
| `DATASET` | Nom du dataset (players, teams, games, all) | ✅ |

**Options**:
| Option | Description | Défaut |
|--------|-------------|--------|
| `-f, --format` | Format d'export (parquet, csv, json) | parquet |
| `-o, --output` | Répertoire de sortie | data/exports |
| `-p, --partition` | Colonne de partitionnement | None |

**Exemples**:

```bash
# Export joueurs en Parquet (défaut)
nba export players

# Export équipes en CSV
nba export teams --format csv

# Export avec partitionnement par saison
nba export players --partition season

# Export dans répertoire personnalisé
nba export teams --output ./mes_exports

# Tous les datasets
nba export all

# Combiner options
nba export players --format csv --partition season --output ./exports
```

**Sortie**:
```
📊 Export players en csv...
✅ Exporté: data/exports/players.csv
```

---

### `nba catalog`
Gère le catalogue de données.

#### `nba catalog list`
Liste tous les datasets disponibles.

```bash
$ nba catalog list

╭────────────────────────────────────────────────╮
│          Catalogue de Données                  │
├──────────────┬─────────┬──────────┬────────────┤
│ Dataset      │ Format  │ Records  │ Dernière   │
│              │         │          │ MAJ        │
├──────────────┼─────────┼──────────┼────────────┤
│ players      │ parquet │ 5103     │ 2024-02-08 │
│ teams        │ parquet │ 30       │ 2024-02-08 │
│ games        │ json    │ 1230     │ 2024-02-08 │
╰──────────────┴─────────┴──────────┴────────────╯
```

---

#### `nba catalog scan`
Scanne les datasets et met à jour le catalogue.

```bash
$ nba catalog scan

🔍 Scan des datasets...
✅ Catalogue mis à jour!
```

**Action**: Scanne `data/gold/` et enregistre les datasets trouvés.

---

#### `nba catalog show`
Affiche les détails d'un dataset.

```bash
$ nba catalog show --dataset players

players
Format: parquet
Records: 5103
Schema: {'id': 'int64', 'name': 'object', 'season': 'object', ...}
```

**Options**:
| Option | Description | Obligatoire |
|--------|-------------|-------------|
| `-d, --dataset` | Nom du dataset | ✅ |

---

### `nba predict`
Lance les prédictions de matchs.

```bash
# Prédictions du jour
nba predict

# Prédictions pour une date spécifique
nba predict --date 2024-02-08

# Mise à jour des résultats
nba predict --update
```

**Options**:
| Option | Description | Défaut |
|--------|-------------|--------|
| `-d, --date` | Date (YYYY-MM-DD) | Aujourd'hui |
| `-u, --update` | Mettre à jour résultats | False |

---

### `nba train`
Entraîne les modèles ML.

```bash
# Entraînement standard
nba train

# Random Forest
nba train --model rf

# Avec optimisation
nba train --optimize

# Forcer réentraînement
nba train --force
```

**Options**:
| Option | Description | Défaut |
|--------|-------------|--------|
| `-m, --model` | Type (xgboost, rf, nn) | xgboost |
| `-o, --optimize` | Optimiser hyperparamètres | False |
| `-f, --force` | Forcer réentraînement | False |

---

### `nba dashboard`
Lance le dashboard Streamlit.

```bash
# Port par défaut (8501)
nba dashboard

# Port personnalisé
nba dashboard --port 8080

# Sans ouvrir navigateur
nba dashboard --no-browser
```

**Options**:
| Option | Description | Défaut |
|--------|-------------|--------|
| `-p, --port` | Port | 8501 |
| `--browser/--no-browser` | Ouvrir navigateur | True |

**Accès**: http://localhost:8501

---

### `nba pipeline`
Exécute les pipelines de données.

```bash
# Pipeline complet
nba pipeline full

# Ingestion seule
nba pipeline ingest

# Processing
nba pipeline process

# Simulation (dry-run)
nba pipeline full --dry-run

# Séquentiel (pas parallèle)
nba pipeline full --sequential
```

**Arguments**:
| Argument | Description | Valeurs |
|----------|-------------|---------|
| `STEP` | Étape à exécuter | ingest, process, train, predict, full |

**Options**:
| Option | Description | Défaut |
|--------|-------------|--------|
| `--dry-run` | Simulation | False |
| `--parallel/--sequential` | Mode exécution | parallel |

---

## Commandes de Développement

### `nba dev api`
Lance l'API en mode développement (Uvicorn + FastAPI).

```bash
# Configuration par défaut
nba dev api

# Personnalisé
nba dev api --host 0.0.0.0 --port 8080

# Mode développement avec auto-reload
nba dev api --reload
```

**Options**:
| Option | Description | Défaut |
|--------|-------------|--------|
| `-h, --host` | Host | 0.0.0.0 |
| `-p, --port` | Port | 8000 |
| `-r, --reload` | Auto-reload | False |

**Accès**: 
- API: http://localhost:8000
- Documentation Swagger: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

**Vérification**:
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test API datasets
curl http://localhost:8000/api/v1/datasets
```

---

## Commandes Globales

### `--help`
Affiche l'aide générale ou d'une commande.

```bash
# Aide générale
nba --help

# Aide commande spécifique
nba export --help
nba catalog --help
```

---

## Flux de Travail Typiques

### Workflow 1: Premier Export

```bash
# 1. Scanner les datasets
nba catalog scan

# 2. Vérifier ce qui est disponible
nba catalog list

# 3. Exporter en Parquet
nba export players

# 4. Exporter en CSV pour Excel
nba export teams --format csv
```

### Workflow 2: Mise à jour Pipeline

```bash
# 1. Exécuter pipeline complet
nba pipeline full

# 2. Vérifier résultats
nba catalog list

# 3. Exporter nouvelles données
nba export all --output ./exports/$(date +%Y%m%d)
```

### Workflow 3: Développement

```bash
# Terminal 1: Lancer API
nba dev api

# Terminal 2: Lancer dashboard
nba dashboard

# Terminal 3: Tester exports
nba export players --format json
```

---

## Codes de Retour

| Code | Signification |
|------|---------------|
| 0 | Succès |
| 1 | Erreur métier (dataset inexistant, validation échouée) |
| 2 | Erreur parsing arguments |

---

## Configuration

### Variables d'environnement

```bash
# Configuration
export ENVIRONMENT=development
export DEBUG=true

# Base de données
export DATABASE_URL=postgresql://nba:nba@localhost:5432/nba

# Chemins
export DATA_EXPORTS=/path/to/exports

# Logging
export LOG_LEVEL=INFO
```

### Fichier .env

```bash
# .env
ENVIRONMENT=development
DEBUG=false
API_PORT=8000
```

---

## Dépannage

### Erreur: "Dataset non trouvé"

```bash
# Solution 1: Scanner d'abord
nba catalog scan

# Solution 2: Vérifier nom
nba catalog list
```

### Erreur: "Port déjà utilisé"

```bash
# Changer port
nba dev api --port 8080
nba dashboard --port 8502
```

### Permission refusée (Linux/Mac)

```bash
chmod +x nba/cli.py
```

---

## Exemples Avancés

### Script d'automatisation

```bash
#!/bin/bash
# daily_export.sh

DATE=$(date +%Y-%m-%d)
OUTPUT_DIR="./exports/$DATE"

# Pipeline
nba pipeline full

# Exports multiples
nba export players --format parquet --output $OUTPUT_DIR
nba export teams --format csv --output $OUTPUT_DIR
nba export games --format json --output $OUTPUT_DIR

# Compression
zip -r "$OUTPUT_DIR.zip" $OUTPUT_DIR

echo "Exports terminés: $OUTPUT_DIR"
```

### Intégration CI/CD

```yaml
# .github/workflows/export.yml
name: Daily Export

on:
  schedule:
    - cron: '0 6 * * *'  # 6h du matin

jobs:
  export:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run pipeline
        run: nba pipeline full
      
      - name: Export data
        run: |
          nba export players --format parquet
          nba export teams --format csv
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v2
        with:
          name: exports
          path: data/exports/
```

---

## Ressources

- [Documentation Typer](https://typer.tiangolo.com/)
- [Rich Console](https://rich.readthedocs.io/)
- [Code source](nba/cli.py)

---

*Dernière mise à jour: 08/02/2026*
