# 🤖 AGENT DOCUMENTATION - NBA Analytics Platform

**Version :** 4.1 (NBA-18 V2 - TERMINÉ)  
**Mise à jour :** 7 Février 2026 à 19:30  
**Statut :** ✅ NBA-18 COMPLET - 4,857/5,103 joueurs enrichis (95.2%)

---

## 📋 Vue d'Ensemble

Pipeline Data Engineering complet : ingestion multi-saisons (2018-2024), 20+ transformations, architecture Medallion, agrégation intelligente 4 méthodes pour ML.

**Stack :** PySpark 3.5, Delta Lake 3.0, nba-api 1.1.11, Python 3.11

---

## 🏗️ Architecture

### Medallion (Bronze → Silver → Gold)
```
Bronze : Données brutes API (JSON)
Silver : Nettoyées, validées (Delta Lake)
Gold   : Features ML, agrégations 4 méthodes
```

### Métriques NBA-18 (4 Méthodes)
| Méthode | Poids | Description |
|---------|-------|-------------|
| Dernière complète | 35% | Saison ≥40 matchs |
| Max minutes | 25% | Plus de temps de jeu |
| Moyenne 3 saisons | 20% | Lissage temporel |
| Best PER | 20% | Meilleure performance |

---

## 🎯 Modules Clés

### Ingestion (NBA-11 à NBA-15)
```python
src/ingestion/
├── fetch_nba_data.py          # API connection
├── fetch_nba_data_v2.py       # Multi-saisons
├── fetch_teams_rosters.py     # 30 équipes
├── fetch_schedules.py         # 2,624 matchs
├── fetch_boxscores.py         # Box scores
└── nba15_orchestrator.py      # Orchestrateur
```

### Processing (NBA-17, NBA-18)
```python
src/processing/
├── enrich_player_stats_v2.py  # Pipeline API 4 méthodes ⏳
├── compile_nba18_final.py     # Compilation dataset
└── batch_ingestion_v2.py      # 20 transformations
```

### Utils
```python
src/utils/
├── season_selector.py         # Sélection 4 méthodes + agrégation
├── nba_formulas.py            # PER, TS%, USG%, eFG%, Game Score, BMI
├── circuit_breaker.py         # Protection API
└── transformations.py         # Fonctions pures
```

---

## 🚀 Commandes Essentielles

### NBA-18 - Enrichissement ✅ TERMINÉ
**Résultats :** 4,857/5,103 joueurs (95.2%), 4 sessions, ~3h

```bash
# Compiler le dataset final
python src/processing/compile_nba18_final.py

# Vérifier cache
cd data/raw/player_stats_cache_v2 && ls -1 | wc -l

# Compiler le dataset final
python src/processing/compile_nba18_final.py

# Tests validation
python test_full_pipeline.py
```

### Pipeline Complet
```bash
# Exécution pipeline Medallion
python run_pipeline.py --stratified

# Vérifier résultats
python use_gold_tiered.py --compare

# Validation finale
python final_validation.py
```

### Tests
```bash
# Tous les tests
pytest tests/ -v

# Tests NBA-18
python test_full_pipeline.py

# Tests intégration
pytest tests/test_integration.py -v
```

---

## 📊 Données

| Dataset | Joueurs | Description |
|---------|---------|-------------|
| GOLD Standard | 5,103 | 100% height/weight |
| GOLD Elite | 3,906 | 98.4% confiance |
| NBA-18 (en cours) | 143+ | Stats API agrégées |

**Métriques calculées :** PER, TS%, USG%, eFG%, Game Score, BMI

---

## 📚 Documentation

- **[memoir.md](memoir.md)** - Journal projet
- **[INDEX.md](INDEX.md)** - Navigation rapide
- **[JIRA_BACKLOG.md](JIRA_BACKLOG.md)** - Tous les tickets
- **stories/** - Stories détaillées NBA-14 à NBA-31

---

## 🎯 Prochaines Étapes

### Immédiat
1. ⏳ Finaliser NBA-18 (~5h enrichissement restant)
2. Compiler dataset final
3. Valider vs NBA.com

### Suite
4. NBA-19 : Agrégations équipe/saison
5. NBA-20 : Feature engineering ML
6. NBA-22 : Modèles prédiction

---

**Résultats :** 5,103 joueurs GOLD, infrastructure NBA-18 validée (5/5 tests), prêt pour ML
