# NBA-19 Phase 1: Ingestion des Données Historiques

## 🎯 Objectif
Récupérer les rosters des 7 saisons (2018-2024) et découvrir automatiquement les équipes des joueurs historiques.

## 📁 Structure créée
```
src/ingestion/nba19/
├── __init__.py                    # Module init
├── config.py                      # Configuration
├── checkpoint_manager.py          # Gestion des checkpoints
├── fetch_historical_rosters.py    # Fetching des rosters
├── auto_discovery.py              # Auto-discovery joueurs
└── orchestrator.py                # Orchestrateur principal

data/raw/rosters/historical/       # Dossier de sortie
```

## 🚀 Utilisation

### 1. Fetching complet (rosters + auto-discovery)
```bash
python src/ingestion/nba19/orchestrator.py
```

**Temps estimé:** ~7-10 minutes
- Roster fetching: ~7 minutes (210 requêtes)
- Auto-discovery: ~3 minutes pour 100 joueurs (configurable)

### 2. Fetching rosters uniquement
```bash
python src/ingestion/nba19/orchestrator.py --skip-discovery
```

### 3. Test rapide (limité à 100 joueurs pour discovery)
```bash
python src/ingestion/nba19/orchestrator.py --discovery-batch 100
```

### 4. Relance après interruption
Le système de checkpoints sauvegarde automatiquement la progression.
Relancer la même commande reprendra là où ça s'est arrêté.

```bash
# La reprise est automatique
python src/ingestion/nba19/orchestrator.py
```

## ⚙️ Configuration

Modifier `src/ingestion/nba19/config.py`:

```python
# Rate limiting (conservateur)
REQUEST_DELAY_SECONDS = 2.0  # 1 req / 2 sec

# Saisons à fetcher
SEASONS = ["2018-19", "2019-20", "2020-21", 
           "2021-22", "2022-23", "2023-24", "2024-25"]

# Checkpoints
CHECKPOINT_INTERVAL_TEAMS = 5  # Toutes les 5 équipes
```

## 📊 Output

### Fichiers générés
```
data/raw/rosters/historical/
├── rosters_2018_19.json      # ~30 équipes
├── rosters_2019_20.json      # ~30 équipes
├── rosters_2020_21.json      # ~30 équipes
├── rosters_2021_22.json      # ~30 équipes
├── rosters_2022_23.json      # ~30 équipes
├── rosters_2023_24.json      # ~30 équipes
├── rosters_2024_25.json      # ~30 équipes
├── player_team_discovered.json  # Mappings auto-découverts
└── checkpoint.json           # Checkpoint (effacé à la fin)
```

### Format des données

**Rosters par saison:**
```json
{
  "metadata": {
    "season": "2023-24",
    "fetched_at": "2026-02-08T10:30:00",
    "total_teams": 30,
    "total_players": 540
  },
  "data": [
    {
      "team_id": 1610612747,
      "team_name": "Los Angeles Lakers",
      "season": "2023-24",
      "players": [...],
      "roster_size": 18
    }
  ]
}
```

**Mappings découverts:**
```json
{
  "player_id": 2544,
  "player_name": "LeBron James",
  "season": "2018-19",
  "team_id": 1610612747,
  "team_abbreviation": "LAL",
  "discovery_method": "career_stats_api",
  "confidence": 1.0
}
```

## 🔍 Vérification

```bash
# Vérifier les fichiers générés
ls -lh data/raw/rosters/historical/

# Compter les joueurs par saison
python -c "
import json
import glob

for file in sorted(glob.glob('data/raw/rosters/historical/rosters_*.json')):
    with open(file) as f:
        data = json.load(f)
    print(f'{data[\"metadata\"][\"season\"]}: {data[\"metadata\"][\"total_players\"]} joueurs')
"

# Vérifier les mappings découverts
python -c "
import json
with open('data/raw/rosters/historical/player_team_discovered.json') as f:
    data = json.load(f)
print(f'Découverts: {data[\"metadata\"][\"total_mappings\"]} mappings')
print(f'Méthode: {data[\"metadata\"][\"discovery_method\"]}')
"
```

## ⚠️ Notes importantes

1. **Rate limiting**: Le script utilise 1 requête / 2 secondes pour éviter le blacklisting
2. **Checkpoints**: La progression est sauvegardée toutes les 5 équipes
3. **Reprise**: En cas d'interruption, relancer la commande reprend automatiquement
4. **Erreurs**: Les échecs sont logués mais n'arrêtent pas le processus

## 🐛 Dépannage

### "Connection timeout"
```bash
# Augmenter le timeout dans config.py
REQUEST_TIMEOUT = 60  # au lieu de 30
```

### "Rate limit exceeded"
```bash
# Augmenter le délai entre requêtes
REQUEST_DELAY_SECONDS = 3.0  # plus conservateur
```

### Reprendre depuis le début
```bash
# Effacer le checkpoint
rm data/raw/rosters/historical/checkpoint.json

# Relancer
python src/ingestion/nba19/orchestrator.py
```

## ✅ Prochaine étape

Une fois Phase 1 terminée, passer à **Phase 2**:
```bash
# Architecture de traitement (à venir)
python src/processing/nba19/orchestrator.py
```

---

**Statut**: ✅ Phase 1 prête pour exécution
