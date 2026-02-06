---
Story: NBA-16
Epic: Data Ingestion & Collection (NBA-6)
Points: 2
Statut: To Do
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
---

# 🎯 NBA-16: Documentation API et ingestion

## 📋 Description

Créer la documentation technique complète de l'ingestion des données NBA, incluant les endpoints utilisés, l'installation des dépendances et des exemples d'utilisation pratiques.

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-11** : Connexion API établie
- ✅ **NBA-12** : Pipeline ingestion
- ⬜ **NBA-15** : Données matchs/équipes (doit documenter aussi)

### Bloque:
- ⬜ **NBA-29** : Export BI (documentation schémas nécessaire)
- ⬜ **NBA-31** : Dashboard (guide utilisateur)

### Parallèle avec:
- ⬜ **NBA-15** : Données matchs/équipes

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ NBA-11  │────→│ NBA-16  │────→│ NBA-29  │
│  (API)  │     │   (Doc) │     │(Export) │
└─────────┘     └────┬────┘     └─────────┘
                     │
                     ├────→ NBA-31 (Dashboard)
                     │
                     └────→ NBA-15 (parallel)
```

## 📥📤 Entrées/Sorties

### Données en entrée:
- **Code source** : `src/ingestion/*.py`
- **Configuration** : `requirements.txt`, `docker-compose.yml`
- **Endpoints API** : Documentation nba-api

### Données en sortie:
- **`docs/API_INGESTION.md`** : Documentation principale
- **`docs/INSTALLATION.md`** : Guide installation
- **`docs/EXAMPLES.md`** : Exemples d'utilisation
- **`README.md`** (mise à jour) : Vue d'ensemble projet

### Format:
- **Markdown** avec code blocks Python
- **Diagrammes** (ASCII ou liens images)
- **Tableaux** pour références API

## 🛠️ Stack Technique

- **Markdown** : Documentation
- **Python 3.11** : Exemples de code
- **nba-api 1.1.11** : Référence endpoints
- **PySpark 3.5** : Exemples traitement

## ✅ Critères d'acceptation détaillés

### 1. README.md dans docs/ expliquant l'API

**Contenu requis:**
```markdown
# API NBA - Guide d'utilisation

## Vue d'ensemble
Cette documentation décrit comment interagir avec l'API NBA 
via le wrapper Python `nba-api`.

## Architecture
```
[nba-api] ←→ [NBA.com] ←→ [Données officielles]
    ↓
[Vos scripts Python]
    ↓
[data/raw/] ←→ [Delta Lake]
```

## Endpoints principaux

### 1. Joueurs
```python
from nba_api.stats.static import players

# Tous les joueurs
all_players = players.get_players()

# Joueur actif
active = [p for p in all_players if p['is_active']]

# Recherche
lebron = players.find_players_by_full_name("LeBron James")
```

### 2. Équipes
```python
from nba_api.stats.static import teams

all_teams = teams.get_teams()
lakers = teams.find_team_by_abbreviation("LAL")
```

### 3. Matchs
```python
from nba_api.stats.endpoints import LeagueGameFinder

gamefinder = LeagueGameFinder(
    season_nullable='2023-24',
    league_id_nullable='00'  # NBA
)
games = gamefinder.get_data_frames()[0]
```

## Rate Limiting
- Maximum: 1000 requêtes/heure
- Délai recommandé: 2 secondes entre requêtes
- Retry: Exponentiel (2s, 4s, 8s)

## Gestion des erreurs
```python
try:
    data = fetch_player_stats(player_id)
except Exception as e:
    logger.error(f"Erreur fetch {player_id}: {e}")
    time.sleep(4)  # Retry après délai
```
```

**Test qualité:**
```python
def test_readme_quality():
    with open("docs/API_INGESTION.md") as f:
        content = f.read()
    
    # Vérifier sections présentes
    required_sections = [
        "## Vue d'ensemble",
        "## Architecture",
        "## Endpoints principaux",
        "## Rate Limiting",
        "## Gestion des erreurs"
    ]
    
    for section in required_sections:
        assert section in content, f"Section {section} manquante"
    
    # Vérifier code Python
    assert "```python" in content, "Exemples Python manquants"
    assert "from nba_api" in content, "Import nba-api manquant"
    
    # Vérifier liens
    assert "[nba-api]" in content or "nba_api" in content
    
    print("✅ README complet et structuré")
    return True

test_readme_quality()
```

---

### 2. Documentation des endpoints utilisés

**Table complète des endpoints:**

```markdown
| Endpoint | Module | Description | Paramètres | Retour |
|----------|--------|-------------|------------|--------|
| `get_players()` | `stats.static.players` | Liste tous les joueurs | - | List[Dict] |
| `get_teams()` | `stats.static.teams` | Liste toutes les équipes | - | List[Dict] |
| `LeagueGameFinder` | `stats.endpoints` | Recherche matchs | season, team_id | DataFrame |
| `PlayerCareerStats` | `stats.endpoints` | Stats carrière joueur | player_id | DataFrame |
| `TeamGameLogs` | `stats.endpoints` | Logs matchs équipe | team_id, season | DataFrame |
| `BoxScoreTraditionalV2` | `stats.endpoints` | Box score détaillé | game_id | DataFrame |
| `ScoreboardV2` | `stats.endpoints` | Scoreboard jour | game_date | DataFrame |
| `CommonTeamRoster` | `stats.endpoints` | Roster équipe | team_id, season | DataFrame |
| `TeamDetails` | `stats.endpoints` | Détails équipe | team_id | DataFrame |
| `LeagueStandingsV3` | `stats.endpoints` | Classement | season | DataFrame |
```

**Exemples par endpoint:**
```python
# LeagueGameFinder - Recherche avancée
from nba_api.stats.endpoints import LeagueGameFinder
from nba_api.stats.library.parameters import SeasonType

gamefinder = LeagueGameFinder(
    team_id_nullable=1610612747,  # LAL
    season_nullable='2023-24',
    season_type_nullable=SeasonType.regular,  # 'Regular Season'
    date_from_nullable='2023-10-24',
    date_to_nullable='2024-04-14'
)

games_df = gamefinder.get_data_frames()[0]
print(f"Matchs trouvés: {len(games_df)}")
```

**Test documentation:**
```python
def test_endpoints_doc():
    with open("docs/API_INGESTION.md") as f:
        content = f.read()
    
    # Vérifier table présente
    assert "| Endpoint |" in content, "Table endpoints manquante"
    assert "| Module |" in content, "Colonne Module manquante"
    
    # Vérifier endpoints critiques
    critical_endpoints = [
        "get_players",
        "get_teams", 
        "LeagueGameFinder",
        "PlayerCareerStats",
        "BoxScore"
    ]
    
    for endpoint in critical_endpoints:
        assert endpoint in content, f"Endpoint {endpoint} non documenté"
    
    print(f"✅ {len(critical_endpoints)} endpoints documentés")
    return True

test_endpoints_doc()
```

---

### 3. Guide d'installation des dépendances

**Contenu requis:**

```markdown
# Installation

## Prérequis
- Python 3.11+
- pip 21.0+
- Git
- 4GB RAM minimum
- 10GB espace disque

## 1. Cloner le repository
```bash
git clone https://github.com/isaakdjedje-byte/nba-analytics.git
cd nba-analytics
```

## 2. Créer environnement virtuel
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

## 3. Installer dépendances
```bash
pip install -r requirements.txt
```

## 4. Vérifier installation
```bash
python -c "import pyspark; print(pyspark.__version__)"
python -c "from nba_api.stats.static import players; print('nba-api OK')"
```

## 5. Configuration environnement
```bash
# Windows (PowerShell)
$env:SPARK_HOME = "C:\path\to\spark"
$env:PYTHONPATH = "$env:PYTHONPATH;$(pwd)\src"

# Linux/Mac
export SPARK_HOME=/path/to/spark
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
```

## Docker (optionnel)
```bash
docker-compose up -d
```

## Dépannage

### Erreur: "No module named 'pyspark'"
→ Vérifier activation venv: `which python`

### Erreur: "JAVA_HOME not set"
→ Installer Java 11: https://adoptium.net/

### Erreur: "Rate limit exceeded"
→ Attendre 1h ou utiliser proxy
```

**Test installation:**
```python
def test_install_doc():
    with open("docs/INSTALLATION.md") as f:
        content = f.read()
    
    # Sections obligatoires
    sections = [
        "## Prérequis",
        "## 1. Cloner",
        "## 2. Créer environnement",
        "## 3. Installer",
        "## 4. Vérifier",
        "## Dépannage"
    ]
    
    for section in sections:
        assert section in content, f"Section {section} manquante"
    
    # Commandes présentes
    assert "pip install" in content
    assert "requirements.txt" in content
    assert "venv" in content or "virtualenv" in content
    
    print("✅ Guide d'installation complet")
    return True

test_install_doc()
```

---

### 4. Exemples d'utilisation

**Fichier docs/EXAMPLES.md:**

```markdown
# Exemples d'utilisation

## Exemple 1: Récupérer stats LeBron James

```python
from nba_api.stats.static import players
from nba_api.stats.endpoints import PlayerCareerStats

# Chercher LeBron
lebron = players.find_players_by_full_name("LeBron James")[0]
player_id = lebron['id']

# Récupérer stats carrière
career = PlayerCareerStats(player_id=player_id)
df = career.get_data_frames()[0]

# Afficher dernière saison
print(df[['SEASON_ID', 'TEAM_ABBREVIATION', 'PTS', 'REB', 'AST']].tail())
```

**Résultat:**
```
     SEASON_ID TEAM_ABBREVIATION   PTS   REB   AST
20  2023-24               LAL  25.7   7.3   8.3
```

## Exemple 2: Analyser tous les matchs d'une saison

```python
from nba_api.stats.endpoints import LeagueGameFinder
import pandas as pd

# Récupérer tous les matchs 2023-24
gamefinder = LeagueGameFinder(season_nullable='2023-24')
games = gamefinder.get_data_frames()[0]

# Stats globales
print(f"Nombre total de matchs: {len(games)}")
print(f"Points moyens par match: {games['PTS'].mean():.1f}")
print(f"Meilleur score: {games['PTS'].max()}")
```

## Exemple 3: Comparer deux équipes

```python
from nba_api.stats.endpoints import TeamGameLogs

# Lakers vs Warriors
lakers_logs = TeamGameLogs(
    team_id_nullable=1610612747,  # LAL
    season_nullable='2023-24'
).get_data_frames()[0]

warriors_logs = TeamGameLogs(
    team_id_nullable=1610612744,  # GSW
    season_nullable='2023-24'
).get_data_frames()[0]

# Comparer moyennes
print(f"Lakers PPG: {lakers_logs['PTS'].mean():.1f}")
print(f"Warriors PPG: {warriors_logs['PTS'].mean():.1f}")
```

## Exemple 4: Pipeline complet Spark

```python
from pyspark.sql import SparkSession
from src.ingestion.fetch_nba_data import fetch_season_games

# Initialiser Spark
spark = SparkSession.builder \
    .appName("NBA-Analytics") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .getOrCreate()

# Récupérer données
games = fetch_season_games("2023-24")

# Créer DataFrame
df = spark.createDataFrame(games)

# Afficher schéma
df.printSchema()

# Stats de base
df.describe(['PTS', 'REB', 'AST']).show()
```
```

**Test exemples:**
```python
def test_examples():
    with open("docs/EXAMPLES.md") as f:
        content = f.read()
    
    # Vérifier exemples présents
    assert "Exemple 1" in content
    assert "Exemple 2" in content
    assert "Exemple 3" in content
    
    # Vérifier code exécutable
    code_blocks = content.count("```python")
    assert code_blocks >= 3, f"Seulement {code_blocks} exemples Python"
    
    # Vérifier imports
    assert "from nba_api" in content
    assert "import pandas" in content or "import pd" in content
    
    print(f"✅ {code_blocks} exemples Python documentés")
    return True

test_examples()
```

## ⚠️ Risques & Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Doc obsolète** | Élevé | Moyen | Date de dernière MAJ, CI/CD check liens |
| **Exemples non testés** | Moyen | Élevé | Exécuter tous les exemples avant release |
| **Incohérence versions** | Moyen | Moyen | Spécifier versions dépendances |
| **Manque contexte** | Faible | Moyen | Review par utilisateur externe |

## 📦 Livrables

### Documentation:
- ✅ `docs/API_INGESTION.md` - Documentation API complète
- ✅ `docs/INSTALLATION.md` - Guide installation
- ✅ `docs/EXAMPLES.md` - Exemples pratiques
- ✅ `README.md` (mise à jour) - Vue d'ensemble

### Code:
- ✅ `docs/scripts/test_examples.py` - Tester tous les exemples

## 🎯 Definition of Done

- [ ] API_INGESTION.md complet avec tous les endpoints
- [ ] INSTALLATION.md avec dépannage
- [ ] EXAMPLES.md avec 4+ exemples testés
- [ ] README.md mis à jour
- [ ] Tous les liens valides
- [ ] Exemples exécutables sans erreur
- [ ] Mergé dans master (PR #X)

## 📝 Notes d'implémentation

### Automatiser tests exemples:
```python
# docs/scripts/test_examples.py
import subprocess
import re

def extract_code_blocks(filepath):
    with open(filepath) as f:
        content = f.read()
    
    # Extraire blocks python
    pattern = r'```python\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    return matches

def test_all_examples():
    examples = extract_code_blocks("docs/EXAMPLES.md")
    
    for i, code in enumerate(examples):
        print(f"Test exemple {i+1}...")
        try:
            exec(code, {"__name__": "__main__"})
            print(f"✅ Exemple {i+1} OK")
        except Exception as e:
            print(f"❌ Exemple {i+1} FAIL: {e}")
            raise

test_all_examples()
```

## 🔗 Références

- [nba-api GitHub](https://github.com/swar/nba_api)
- [NBA-11](NBA-11_api_connection.md) : Connexion API
- [NBA-15](NBA-15_donnees_matchs.md) : Données matchs
