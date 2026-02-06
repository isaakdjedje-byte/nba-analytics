---
Story: NBA-15
Epic: Data Ingestion & Collection (NBA-6)
Points: 3
Statut: To Do
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
---

# 🎯 NBA-15: Récupération des données matchs et équipes

## 📋 Description

Compléter l'ingestion avec les données des matchs (schedule, scores) et équipes (rosters, stats) pour avoir une base de données complète et relationnelle.

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-11** : Connexion API établie
- ✅ **NBA-12** : Structure de stockage
- 🟡 **NBA-14** : Schémas évolutifs (parallèle)

### Bloque:
- ⬜ **NBA-19** : Agrégations équipes (besoin stats équipes)
- ⬜ **NBA-20** : Transformation matchs (besoin données matchs)
- ⬜ **NBA-22** : ML prédiction (besoin données complètes)

### Parallèle avec:
- 🟡 **NBA-14** : Schémas évolutifs
- ⬜ **NBA-16** : Documentation API

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ NBA-11  │────→│ NBA-15  │────→│ NBA-19  │
│  (API)  │     │(Données)│     │(Aggrég) │
└─────────┘     └────┬────┘     └─────────┘
                     │
                     ├────→ NBA-20 (Transform)
                     │
                     ├────→ NBA-22 (ML)
                     │
                     ├────→ NBA-14 (parallel schémas)
                     └────→ NBA-16 (parallel doc)
```

## 📥📤 Entrées/Sorties

### Données en entrée:
- **API nba-api** : Endpoints teams, schedules, box scores
- **Sources:**
  - `nba_api.stats.static.teams`
  - `nba_api.stats.endpoints.leaguegamefinder`
  - `nba_api.stats.endpoints.teamgamelogs`
  - `nba_api.stats.endpoints.playercareerstats`

### Données en sortie:
- **`data/raw/teams/teams_2024_25.json`** : Informations 30 équipes
- **`data/raw/schedules/schedule_2024_25.json`** : Calendrier complet
- **`data/raw/games_detailed/`** : Box scores détaillés par match
- **`data/raw/rosters/roster_2024_25.json`** : Effectifs équipes
- **`data/raw/teams_stats/team_stats_2024_25.json`** : Stats collectives

### Format:
- **Format**: JSON structuré avec métadonnées
- **Relations:**
  ```
  teams (30) ←→ rosters (15 joueurs/équipe)
  teams (30) ←→ schedules (82 matchs/équipe/saison)
  games ←→ box_scores (détaillés)
  ```

## 🛠️ Stack Technique

- **nba-api 1.1.11** : Wrapper API NBA.com
- **Python 3.11** : Scripts d'ingestion
- **requests** : Gestion rate limiting
- **json** : Sérialisation

### Bibliothèques:
```python
from nba_api.stats.static import teams
from nba_api.stats.endpoints import (
    LeagueGameFinder, TeamGameLogs, PlayerCareerStats
)
import json
import time
from datetime import datetime
```

## ✅ Critères d'acceptation détaillés

### 1. Données matchs récupérées (schedule, scores)

**Test détaillé:**
```python
# TEST RÉCUPÉRATION MATCHS
def test_games_fetch():
    from src.ingestion.fetch_games import fetch_season_games
    
    # Données test : Saison 2023-24
    season = "2023-24"
    games = fetch_season_games(season)
    
    # Vérifications:
    assert games is not None, "Données récupérées"
    assert len(games) >= 1200, f"Nombre matchs: {len(games)} (attendu: ~1230)"
    
    # Structure obligatoire
    required_fields = [
        "GAME_ID", "GAME_DATE", "TEAM_ID", "TEAM_ABBREVIATION",
        "PTS", "FG_PCT", "FG3_PCT", "FT_PCT", "REB", "AST", "STL", "BLK"
    ]
    
    for field in required_fields:
        assert field in games[0], f"Champ {field} manquant"
    
    # Vérifier format dates
    game_date = games[0]["GAME_DATE"]
    datetime.strptime(game_date, "%Y-%m-%d")  # Doit parser sans erreur
    
    print(f"✅ {len(games)} matchs récupérés pour saison {season}")
    print(f"✅ Tous les champs requis présents")
    return True

# EXÉCUTION
test_games_fetch()
```

**Résultat attendu:**
- 1230+ matchs régular season
- 100+ matchs playoffs (si terminés)
- Tous les champs box score présents
- Dates au format ISO (YYYY-MM-DD)

---

### 2. Données équipes récupérées (rosters, stats)

**Test détaillé:**
```python
# TEST ÉQUIPES
def test_teams_fetch():
    from src.ingestion.fetch_teams import fetch_all_teams_data
    
    teams_data = fetch_all_teams_data()
    
    # Vérification nombre équipes
    assert len(teams_data) == 30, f"Nombre équipes: {len(teams_data)} (attendu: 30)"
    
    # Vérification par équipe
    for team in teams_data:
        assert "id" in team, "ID équipe manquant"
        assert "full_name" in team, "Nom équipe manquant"
        assert "abbreviation" in team, "Abréviation manquante"
        assert "roster" in team, "Roster manquant"
        assert len(team["roster"]) >= 12, f"Roster trop petit: {len(team['roster'])}"
    
    # Équipes spécifiques à vérifier
    team_names = [t["full_name"] for t in teams_data]
    assert "Los Angeles Lakers" in team_names
    assert "Golden State Warriors" in team_names
    assert "Boston Celtics" in team_names
    
    print(f"✅ {len(teams_data)} équipes avec rosters complets")
    return True

# TEST STATS ÉQUIPES
def test_team_stats():
    from src.ingestion.fetch_teams import fetch_team_stats
    
    stats = fetch_team_stats(season="2023-24")
    
    assert len(stats) == 30, "Stats pour les 30 équipes"
    
    # Vérifier stats collectives
    required_stats = ["W", "L", "W_PCT", "PTS", "REB", "AST", "STL", "BLK"]
    for stat in required_stats:
        assert stat in stats[0], f"Stat {stat} manquante"
    
    # Vérifier cohérence
    wins = sum([t["W"] for t in stats])
    losses = sum([t["L"] for t in stats])
    assert wins == losses, f"Déséquilibre W/L: {wins} vs {losses}"
    
    print(f"✅ Stats collectives récupérées")
    print(f"   - Total victoires: {wins}")
    print(f"   - Total défaites: {losses}")
    return True

test_teams_fetch()
test_team_stats()
```

**Résultat attendu:**
- 30 équipes complètes
- 15+ joueurs par roster
- Stats collectives (W/L/PCT/PTS/etc.)
- Équilibre W/L (chaque match = 1W + 1L)

---

### 3. Stockage structuré dans data/raw/

**Test détaillé:**
```python
import os
import json

def test_storage_structure():
    base_path = "data/raw"
    
    # Vérifier structure dossiers
    required_dirs = [
        "teams",
        "schedules", 
        "games_detailed",
        "rosters",
        "teams_stats"
    ]
    
    for dir_name in required_dirs:
        dir_path = os.path.join(base_path, dir_name)
        assert os.path.exists(dir_path), f"Dossier {dir_name} manquant"
    
    # Vérifier fichiers JSON valides
    teams_file = os.path.join(base_path, "teams/teams_2024_25.json")
    assert os.path.exists(teams_file), "Fichier teams manquant"
    
    with open(teams_file) as f:
        teams = json.load(f)
        assert "teams" in teams or isinstance(teams, list)
        assert "metadata" in teams or "last_updated" in str(teams)
    
    # Vérifier taille fichiers (> 0 bytes)
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.json'):
                filepath = os.path.join(root, file)
                size = os.path.getsize(filepath)
                assert size > 0, f"Fichier vide: {filepath}"
    
    print("✅ Structure de stockage correcte")
    print("✅ Tous les fichiers JSON valides et non vides")
    return True

test_storage_structure()
```

**Structure attendue:**
```
data/raw/
├── teams/
│   └── teams_2024_25.json          # 30 équipes
├── schedules/
│   └── schedule_2024_25.json       # ~1230 matchs
├── games_detailed/
│   ├── game_0022300001.json        # Box score détaillé
│   ├── game_0022300002.json
│   └── ...
├── rosters/
│   └── roster_2024_25.json         # 30 rosters
└── teams_stats/
    └── team_stats_2024_25.json     # Stats collectives 30 équipes
```

---

### 4. Relations entre tables établies

**Test détaillé:**
```python
def test_relationships():
    import json
    
    # Charger données
    with open("data/raw/teams/teams_2024_25.json") as f:
        teams = json.load(f)
    
    with open("data/raw/rosters/roster_2024_25.json") as f:
        rosters = json.load(f)
    
    with open("data/raw/schedules/schedule_2024_25.json") as f:
        schedules = json.load(f)
    
    # Test 1: Chaque équipe a un roster
    team_ids = {t["id"] for t in teams}
    roster_team_ids = {r["team_id"] for r in rosters}
    
    assert team_ids == roster_team_ids, \
        f"Incohérence équipes/rosters: {team_ids - roster_team_ids}"
    
    # Test 2: Chaque match a 2 équipes valides
    for game in schedules[:100]:  # Échantillon
        home_id = game["HOME_TEAM_ID"]
        away_id = game["VISITOR_TEAM_ID"]
        
        assert home_id in team_ids, f"Équipe home invalide: {home_id}"
        assert away_id in team_ids, f"Équipe away invalide: {away_id}"
        assert home_id != away_id, "Même équipe home et away!"
    
    # Test 3: Joueurs dans rosters ont IDs uniques
    all_players = []
    for roster in rosters:
        for player in roster["players"]:
            all_players.append(player["id"])
    
    assert len(all_players) == len(set(all_players)), \
        "IDs joueurs dupliqués dans rosters!"
    
    print(f"✅ Relations vérifiées:")
    print(f"   - {len(teams)} équipes ←→ {len(rosters)} rosters")
    print(f"   - {len(schedules)} matchs avec équipes valides")
    print(f"   - {len(all_players)} joueurs uniques")
    return True

test_relationships()
```

**Résultat attendu:**
- 30 équipes = 30 rosters
- Chaque match a 2 équipes différentes existantes
- Pas de doublons dans les IDs joueurs
- Intégrité référentielle respectée

## ⚠️ Risques & Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Rate limiting API** | Élevé | Moyen | Délai 2s entre requêtes + retry exponentiel |
| **Données incomplètes** | Moyen | Élevé | Vérification count() après fetch |
| **IDs incohérents** | Faible | Élevé | Tests de relations automatiques |
| **Format API change** | Faible | Moyen | Gestion erreurs + logging détaillé |
| **Timeout sur gros volumes** | Moyen | Moyen | Chunking par saison/équipe |

### Plan de secours:
1. Cache local: Sauvegarder après chaque batch
2. Resume: Reprendre là où ça s'est arrêté
3. Fallback: Données backup si API down

## 📦 Livrables

### Code:
- ✅ `src/ingestion/fetch_teams.py` - Récupération équipes
- ✅ `src/ingestion/fetch_games.py` - Récupération matchs
- ✅ `src/ingestion/fetch_rosters.py` - Récupération rosters
- ✅ `tests/test_fetch_teams.py` - Tests équipes
- ✅ `tests/test_fetch_games.py` - Tests matchs

### Données:
- ✅ `data/raw/teams/teams_2024_25.json`
- ✅ `data/raw/schedules/schedule_2024_25.json`
- ✅ `data/raw/rosters/roster_2024_25.json`
- ✅ `data/raw/teams_stats/team_stats_2024_25.json`
- ✅ `data/raw/games_detailed/*.json` (box scores)

### Documentation:
- ✅ Mise à jour `docs/schema_evolution.log` (relations)

## 🎯 Definition of Done

- [ ] Toutes les équipes (30) récupérées avec rosters
- [ ] Tous les matchs (1230+) récupérés avec box scores
- [ ] Stats collectives complètes
- [ ] Tests de relations passants
- [ ] Structure dossiers respectée
- [ ] Pas de rate limit dépassé
- [ ] Mergé dans master (PR #X)

## 📝 Notes d'implémentation

### Rate limiting:
```python
import time
from functools import wraps

def rate_limited(max_per_hour=1000):
    min_interval = 3600.0 / max_per_hour
    def decorator(func):
        last_called = [0.0]
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator

@rate_limited(max_per_hour=1000)
def fetch_team_data(team_id):
    # Appel API
    pass
```

### Sauvegarde incrémentale:
```python
def fetch_with_checkpoint(season, checkpoint_file=".checkpoint"):
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file) as f:
            last_team = f.read().strip()
        teams_to_fetch = teams[teams.index(last_team)+1:]
    else:
        teams_to_fetch = teams
    
    for team in teams_to_fetch:
        fetch_team(team)
        with open(checkpoint_file, 'w') as f:
            f.write(team)
```

## 🔗 Références

- [nba-api Documentation](https://github.com/swar/nba_api)
- NBA-11: Connexion API existante
- NBA-12: Structure de stockage
- NBA-14: Schémas évolutifs
