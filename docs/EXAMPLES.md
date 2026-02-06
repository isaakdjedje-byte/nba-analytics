# Exemples d'utilisation - NBA Analytics Platform

Ce document contient des exemples pratiques et testes d'utilisation de la plateforme NBA Analytics.

## Exemple 1 : Recuperer les statistiques de LeBron James

```python
from nba_api.stats.static import players
from nba_api.stats.endpoints import PlayerCareerStats

# Chercher LeBron
lebron = players.find_players_by_full_name("LeBron James")[0]
player_id = lebron['id']

# Recuperer stats carriere
career = PlayerCareerStats(player_id=player_id)
df = career.get_data_frames()[0]

# Afficher dernieres saisons
print(df[['SEASON_ID', 'TEAM_ABBREVIATION', 'PTS', 'REB', 'AST']].tail())
```

**Resultat:**
```
     SEASON_ID TEAM_ABBREVIATION   PTS   REB   AST
20  2023-24               LAL  25.7   7.3   8.3
```

## Exemple 2 : Analyser tous les matchs d'une saison

```python
from nba_api.stats.endpoints import LeagueGameFinder
import pandas as pd

# Recuperer tous les matchs 2023-24
gamefinder = LeagueGameFinder(season_nullable='2023-24')
games = gamefinder.get_data_frames()[0]

# Stats globales
print(f"Nombre total de matchs: {len(games)}")
print(f"Points moyens par match: {games['PTS'].mean():.1f}")
print(f"Meilleur score: {games['PTS'].max()}")
```

## Exemple 3 : Comparer deux equipes

```python
from nba_api.stats.endpoints import TeamGameLogs

# Lakers vs Warriors
lakers_logs = TeamGameLogs(
    team_id_nullable=1610612747,
    season_nullable='2023-24'
).get_data_frames()[0]

warriors_logs = TeamGameLogs(
    team_id_nullable=1610612744,
    season_nullable='2023-24'
).get_data_frames()[0]

# Comparer moyennes
print(f"Lakers PPG: {lakers_logs['PTS'].mean():.1f}")
print(f"Warriors PPG: {warriors_logs['PTS'].mean():.1f}")
```

## Exemple 4 : Pipeline complet Spark

```python
from pyspark.sql import SparkSession
from src.ingestion.fetch_nba_data import fetch_season_games

# Initialiser Spark
spark = SparkSession.builder \
    .appName("NBA-Analytics") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .getOrCreate()

# Recuperer donnees
games = fetch_season_games("2023-24")

# Creer DataFrame
df = spark.createDataFrame(games)

# Afficher schema
df.printSchema()

# Stats de base
df.describe(['PTS', 'REB', 'AST']).show()
```

## Exemple 5 : Recherche avancee de matchs

```python
from nba_api.stats.endpoints import LeagueGameFinder
from nba_api.stats.library.parameters import SeasonType

# Recherche avec filtres multiples
gamefinder = LeagueGameFinder(
    team_id_nullable=1610612747,  # LAL
    season_nullable='2023-24',
    season_type_nullable=SeasonType.regular,
    date_from_nullable='2023-10-24',
    date_to_nullable='2024-04-14'
)

games_df = gamefinder.get_data_frames()[0]
print(f"Matchs trouves: {len(games_df)}")
```

## Exemple 6 : Analyse de roster

```python
from nba_api.stats.endpoints import CommonTeamRoster

# Roster Lakers
roster = CommonTeamRoster(
    team_id=1610612747,
    season='2023-24'
)

players = roster.get_data_frames()[0]
coaches = roster.get_data_frames()[1]

print(f"Joueurs: {len(players)}")
print(players[['PLAYER', 'POSITION', 'HEIGHT']].head())
```

## Bonnes pratiques

### Gestion du rate limiting

```python
import time

# Toujours attendre entre les requetes
time.sleep(2)

# Fonction avec retry
def fetch_with_retry(endpoint_func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return endpoint_func()
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 1))
            else:
                raise
```

### Gestion des erreurs

```python
try:
    data = fetch_player_stats(player_id)
except Exception as e:
    print(f"Erreur: {e}")
    time.sleep(4)
```

---

**Derniere mise a jour** : 2026-02-06  
**Ticket associe** : NBA-16
