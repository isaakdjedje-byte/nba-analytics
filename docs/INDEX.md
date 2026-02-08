# 📚 INDEX - Documentation NBA Analytics

**Dernière mise à jour :** 2026-02-08 10:20  
**Statut :** NBA-20 ✅ TERMINÉ - 1,230 matchs structurés

---

## ✅ NBA-20 - TERMINÉ (08/02/2026)

### Résultats
- **1,230 matchs** structurés depuis 2,460 box scores
- **Home win rate** : 54.3% (668 wins)
- **Marge moyenne** : 12.6 points
- **0 erreurs** de transformation
- **Fichier généré** : 889KB

### Fichiers
| Fichier | Description | Lignes |
|---------|-------------|--------|
| [src/pipeline/nba20_transform_games.py](../src/pipeline/nba20_transform_games.py) | Transformateur matchs | ~270 |
| [src/pipeline/unified_ml_pipeline.py](../src/pipeline/unified_ml_pipeline.py) | Orchestrateur ML | ~220 |
| [data/silver/games_processed/games_structured.json](../data/silver/games_processed/games_structured.json) | Matchs structurés | 1,230 |

### Commandes
```bash
# NBA-20 uniquement
python src/pipeline/nba20_transform_games.py

# Pipeline complet
python src/pipeline/unified_ml_pipeline.py
```

---

## ✅ NBA-18 V2 - TERMINÉ

### Résultats
- **4,857 joueurs** enrichis avec stats API (95.2%)
- **4 sessions** de ~45 min, temps total ~3h
- **Architecture :** 4 méthodes d'agrégation (35/25/20/20)
- **Tests :** 5/5 validés

### Documentation
- **[memoir.md](memoir.md)** - Journal projet
- **[agent.md](agent.md)** - Architecture et commandes
- **[JIRA_BACKLOG.md](JIRA_BACKLOG.md)** - Tous les tickets

### Commandes
```bash
# Lancer l'enrichissement
python src/processing/enrich_player_stats_v2.py

# Vérifier progression
cd data/raw/player_stats_cache_v2 && ls -1 | wc -l

# Tests validation
python test_full_pipeline.py
```

---

## 📖 Fichiers Principaux

| Fichier | Description | Lignes |
|---------|-------------|--------|
| [memoir.md](memoir.md) | Journal projet | ~200 |
| [agent.md](agent.md) | Architecture + commandes | ~150 |
| [JIRA_BACKLOG.md](JIRA_BACKLOG.md) | Tickets JIRA | ~500 |

### Code Source NBA-18
| Fichier | Description |
|---------|-------------|
| [src/utils/season_selector.py](../src/utils/season_selector.py) | 4 méthodes + agrégation |
| [src/utils/nba_formulas.py](../src/utils/nba_formulas.py) | PER, TS%, USG%, etc. |
| [src/processing/enrich_player_stats_v2.py](../src/processing/enrich_player_stats_v2.py) | Pipeline batch |
| [test_full_pipeline.py](../test_full_pipeline.py) | Tests validation |

### Stories
- [stories/NBA-18_metriques_avancees.md](stories/NBA-18_metriques_avancees.md) - NBA-18 détaillé
- [stories/](stories/) - Toutes les stories (NBA-14 à NBA-31)

---

## 🚀 Navigation Rapide

### "Je veux comprendre l'architecture"
→ [agent.md](agent.md) - Stack technique et structure

### "Je veux l'historique"
→ [memoir.md](memoir.md) - Chronologie complète

### "Je veux les commandes"
→ [agent.md](agent.md) - Section "Commandes Essentielles"

### "Je veux voir un ticket"
→ [JIRA_BACKLOG.md](JIRA_BACKLOG.md) - Tous les tickets

---

## 📊 Rappel Commandes

```bash
# Pipeline
python run_pipeline.py --stratified

# NBA-18
python src/processing/enrich_player_stats_v2.py

# Tests
python test_full_pipeline.py
pytest tests/test_integration.py -v
```
