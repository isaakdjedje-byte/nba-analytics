# API NBA - Guide d'utilisation

## Vue d'ensemble

Cette documentation décrit comment interagir avec l'API NBA via le wrapper Python `nba-api`. L'API officielle NBA.com est accessible gratuitement grâce à cette bibliothèque Python qui simplifie l'accès aux données statistiques et aux informations des joueurs, équipes et matchs.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   nba-api       │ ←→  │    NBA.com      │ ←→  │ Données NBA     │
│   (Python)      │     │   (API REST)    │     │   officielles   │
└────────┬────────┘     └─────────────────┘     └─────────────────┘
         │
         ↓
┌─────────────────┐
│ Scripts Python  │
│   (Votre code)  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐     ┌─────────────────┐
│  data/raw/      │ ←→  │   Delta Lake    │
│  (JSON/Parquet) │     │  (Stockage      │
│                 │     │   transactionnel)│
└─────────────────┘     └─────────────────┘
```

### Flux de données

1. **Récupération** : `nba-api` interroge les endpoints NBA.com
2. **Transformation** : Les données JSON sont converties en DataFrames pandas/PySpark
3. **Stockage** : Les données sont persistées dans Delta Lake pour analyse
4. **Analyse** : Spark traite les données pour créer des métriques avancées

## Endpoints principaux

### 1. Joueurs

```python
from nba_api.stats.static import players

# Tous les joueurs (actifs et inactifs)
all_players = players.get_players()
print(f"Nombre total de joueurs: {len(all_players)}")

# Joueurs actifs uniquement
active_players = [p for p in all_players if p['is_active']]
print(f"Joueurs actifs: {len(active_players)}")

# Recherche par nom complet
lebron = players.find_players_by_full_name("LeBron James")
print(f"Résultat recherche: {lebron}")

# Recherche par nom partiel
curry = players.find_players_by_first_name("Stephen")
print(f"Joueurs prénommés Stephen: {len(curry)}")
```

**Retour:** Liste de dictionnaires avec `id`, `full_name`, `first_name`, `last_name`, `is_active`

### 2. Équipes

```python
from nba_api.stats.static import teams

# Toutes les équipes
all_teams = teams.get_teams()
print(f"Nombre total d'équipes: {len(all_teams)}")

# Recherche par abréviation
lakers = teams.find_team_by_abbreviation("LAL")
print(f"Lakers: {lakers}")

# Recherche par nom
celtics = teams.find_teams_by_full_name("Boston Celtics")
print(f"Celtics: {celtics}")
```

**Retour:** Dictionnaire avec `id`, `full_name`, `abbreviation`, `nickname`, `city`, `state`, `year_founded`

### 3. Matchs

```python
from nba_api.stats.endpoints import LeagueGameFinder
from nba_api.stats.library.parameters import SeasonType

# Recherche de matchs avec filtres
gamefinder = LeagueGameFinder(
    season_nullable='2023-24',
    league_id_nullable='00',  # '00' = NBA
    season_type_nullable=SeasonType.regular  # 'Regular Season'
)

# Récupération des données
games_df = gamefinder.get_data_frames()[0]
print(f"Nombre de matchs trouvés: {len(games_df)}")
print(f"Colonnes disponibles: {list(games_df.columns)}")
```

**Paramètres importants:**
- `season_nullable`: Saison au format 'YYYY-YY' (ex: '2023-24')
- `team_id_nullable`: ID de l'équipe (optionnel)
- `date_from_nullable`: Date début 'YYYY-MM-DD'
- `date_to_nullable`: Date fin 'YYYY-MM-DD'
- `season_type_nullable`: SeasonType.regular, SeasonType.playoffs, SeasonType.preseason

### 4. Statistiques carrière joueur

```python
from nba_api.stats.endpoints import PlayerCareerStats

# Récupérer ID joueur
from nba_api.stats.static import players
player = players.find_players_by_full_name("Kevin Durant")[0]
player_id = player['id']

# Stats carrière
career = PlayerCareerStats(player_id=player_id)
career_df = career.get_data_frames()[0]

# Afficher dernières saisons
print(career_df[['SEASON_ID', 'TEAM_ABBREVIATION', 'GP', 'PTS', 'REB', 'AST']].tail())
```

**Retour:** DataFrame avec statistiques par saison (points, rebonds, passes, etc.)

### 5. Logs de matchs par équipe

```python
from nba_api.stats.endpoints import TeamGameLogs

# Logs de matchs Lakers 2023-24
lakers_id = 1610612747  # ID Lakers
logs = TeamGameLogs(
    team_id_nullable=lakers_id,
    season_nullable='2023-24'
)

logs_df = logs.get_data_frames()[0]
print(f"Matchs joués: {len(logs_df)}")
print(f"Moyenne points: {logs_df['PTS'].mean():.1f}")
```

### 6. Box Score détaillé

```python
from nba_api.stats.endpoints import BoxScoreTraditionalV2

# Box score d'un match spécifique (nécessite game_id)
game_id = "0022300001"  # Exemple ID match
boxscore = BoxScoreTraditionalV2(game_id=game_id)

# Stats joueurs
player_stats = boxscore.get_data_frames()[0]
print(f"Joueurs dans le box score: {len(player_stats)}")

# Stats équipe
team_stats = boxscore.get_data_frames()[1]
print(team_stats)
```

### 7. Scoreboard du jour

```python
from nba_api.stats.endpoints import ScoreboardV2
from datetime import datetime

# Scoreboard d'une date spécifique
today = datetime.now().strftime('%Y-%m-%d')
scoreboard = ScoreboardV2(game_date=today)

# Matchs du jour
games = scoreboard.get_data_frames()[0]
print(f"Matchs aujourd'hui: {len(games)}")

# Scores en direct (si matchs en cours)
line_score = scoreboard.get_data_frames()[1]
print(line_score[['GAME_ID', 'TEAM_ABBREVIATION', 'PTS']])
```

### 8. Roster équipe

```python
from nba_api.stats.endpoints import CommonTeamRoster

# Roster Lakers 2023-24
roster = CommonTeamRoster(
    team_id=1610612747,
    season='2023-24'
)

players_roster = roster.get_data_frames()[0]
coaches = roster.get_data_frames()[1]

print(f"Joueurs dans le roster: {len(players_roster)}")
print(players_roster[['PLAYER', 'POSITION', 'HEIGHT', 'WEIGHT']].head())
```

### 9. Détails équipe

```python
from nba_api.stats.endpoints import TeamDetails

# Informations détaillées sur une équipe
details = TeamDetails(team_id=1610612747)

# Historique équipe
team_history = details.get_data_frames()[0]
print(team_history[['ABBREVIATION', 'YEARFOUNDED', 'CITY', 'ARENA']])

# Champions NBA
titles = details.get_data_frames()[2]
print(f"Titres NBA: {len(titles)}")
```

## Table complète des endpoints

| Endpoint | Module | Description | Paramètres clés | Retour |
|----------|--------|-------------|-----------------|--------|
| `get_players()` | `stats.static.players` | Liste tous les joueurs | - | List[Dict] |
| `get_teams()` | `stats.static.teams` | Liste toutes les équipes | - | List[Dict] |
| `find_players_by_full_name()` | `stats.static.players` | Recherche joueur par nom | `full_name` | List[Dict] |
| `find_team_by_abbreviation()` | `stats.static.teams` | Recherche équipe par abréviation | `abbreviation` | Dict |
| `LeagueGameFinder` | `stats.endpoints` | Recherche avancée matchs | `season`, `team_id`, `date_from`, `date_to` | DataFrame |
| `PlayerCareerStats` | `stats.endpoints` | Stats carrière joueur | `player_id` | DataFrame |
| `TeamGameLogs` | `stats.endpoints` | Logs matchs équipe | `team_id`, `season` | DataFrame |
| `BoxScoreTraditionalV2` | `stats.endpoints` | Box score détaillé | `game_id` | DataFrame |
| `ScoreboardV2` | `stats.endpoints` | Scoreboard jour | `game_date` | DataFrame |
| `CommonTeamRoster` | `stats.endpoints` | Roster équipe | `team_id`, `season` | DataFrame |
| `TeamDetails` | `stats.endpoints` | Détails équipe | `team_id` | DataFrame |
| `LeagueStandingsV3` | `stats.endpoints` | Classement ligue | `season` | DataFrame |

## Rate Limiting

### Limites de l'API

- **Maximum** : 1000 requêtes/heure par IP
- **Délai recommandé** : 2 secondes entre requêtes
- **Stratégie de retry** : Exponentiel (2s, 4s, 8s, 16s)

### Bonnes pratiques

```python
import time
import random

def fetch_with_rate_limit(endpoint_func, *args, **kwargs):
    """
    Appelle un endpoint avec gestion du rate limiting.
    """
    # Délai aléatoire entre 1.5 et 2.5 secondes
    time.sleep(random.uniform(1.5, 2.5))
    
    try:
        return endpoint_func(*args, **kwargs)
    except Exception as e:
        if "rate limit" in str(e).lower():
            print("Rate limit atteint, attente 60s...")
            time.sleep(60)
            return endpoint_func(*args, **kwargs)
        raise

# Utilisation
gamefinder = fetch_with_rate_limit(
    LeagueGameFinder,
    season_nullable='2023-24'
)
```

### Gestion parallèle sécurisée

```python
from concurrent.futures import ThreadPoolExecutor
import time

def fetch_seasons_parallel(seasons, max_workers=2):
    """
    Récupère plusieurs saisons en parallèle avec rate limiting.
    """
    def fetch_one(season):
        time.sleep(2)  # Respect rate limit
        finder = LeagueGameFinder(season_nullable=season)
        return finder.get_data_frames()[0]
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(fetch_one, seasons))
    
    return results
```

## Gestion des erreurs

### Erreurs courantes

```python
import logging
import time
from nba_api.stats.endpoints import PlayerCareerStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_player_stats_safe(player_id, max_retries=3):
    """
    Récupère les stats d'un joueur avec retry exponentiel.
    """
    for attempt in range(max_retries):
        try:
            career = PlayerCareerStats(player_id=player_id)
            df = career.get_data_frames()[0]
            logger.info(f"✅ Stats récupérées pour joueur {player_id}")
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur fetch {player_id}: {e}")
            
            if attempt < max_retries - 1:
                # Retry exponentiel : 2s, 4s, 8s
                wait_time = 2 ** (attempt + 1)
                logger.info(f"⏳ Retry dans {wait_time}s... (tentative {attempt + 2}/{max_retries})")
                time.sleep(wait_time)
            else:
                logger.error(f"❌ Échec après {max_retries} tentatives")
                raise
    
    return None

# Utilisation
try:
    stats = fetch_player_stats_safe(2544)  # LeBron James ID
    print(stats[['SEASON_ID', 'PTS']].tail())
except Exception as e:
    print(f"Impossible de récupérer les stats: {e}")
```

### Gestion des données manquantes

```python
import pandas as pd

def safe_dataframe_conversion(api_response):
    """
    Convertit la réponse API en DataFrame avec gestion d'erreurs.
    """
    try:
        df = api_response.get_data_frames()[0]
        
        # Vérifier si DataFrame vide
        if df.empty:
            logger.warning("⚠️ DataFrame vide retourné")
            return pd.DataFrame()
        
        return df
        
    except IndexError:
        logger.error("❌ Pas de DataFrame dans la réponse")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"❌ Erreur conversion DataFrame: {e}")
        return pd.DataFrame()
```

## Optimisations

### Cache des données statiques

```python
# Les données statiques (joueurs, équipes) ne changent pas souvent
# Les mettre en cache pour éviter les appels répétés

_players_cache = None
_teams_cache = None

def get_players_cached():
    """Retourne la liste des joueurs (avec cache)."""
    global _players_cache
    if _players_cache is None:
        from nba_api.stats.static import players
        _players_cache = players.get_players()
    return _players_cache

def get_teams_cached():
    """Retourne la liste des équipes (avec cache)."""
    global _teams_cache
    if _teams_cache is None:
        from nba_api.stats.static import teams
        _teams_cache = teams.get_teams()
    return _teams_cache
```

### Pagination pour grands volumes

```python
def fetch_all_seasons_games(start_season=2018, end_season=2024):
    """
    Récupère tous les matchs sur plusieurs saisons avec gestion de la mémoire.
    """
    all_games = []
    
    for season_year in range(start_season, end_season + 1):
        season_str = f"{season_year}-{str(season_year + 1)[-2:]}"
        
        try:
            finder = LeagueGameFinder(season_nullable=season_str)
            games = finder.get_data_frames()[0]
            all_games.append(games)
            
            print(f"✅ Saison {season_str}: {len(games)} matchs")
            time.sleep(2)  # Respect rate limit
            
        except Exception as e:
            print(f"❌ Erreur saison {season_str}: {e}")
            continue
    
    # Concaténer tous les DataFrames
    if all_games:
        return pd.concat(all_games, ignore_index=True)
    return pd.DataFrame()
```

## Références

- [Documentation officielle nba-api](https://github.com/swar/nba_api)
- [Endpoints disponibles](https://github.com/swar/nba_api/tree/master/docs/nba_api)
- [NBA.com API (officiel)](https://stats.nba.com/)

---

**Dernière mise à jour** : 2026-02-06  
**Version nba-api** : 1.1.11  
**Ticket associé** : NBA-16
