# 📚 INDEX - Documentation NBA Analytics

**Dernière mise à jour :** 2026-02-08 13:30  
**Statut :** NBA-22 ✅ TERMINÉ - Production Ready (76.76% accuracy, XGBoost)

**Meilleur modèle** : XGBoost V3 76.76% > Neural Network 76.84% (testé) > RF 76.19%

**🚀 Production** : Pipeline quotidien fonctionnel avec API NBA Live + Tracking ROI

---

## ✅ NBA-22 - Production ML (TERMINÉ)

### Résultats Finaux (08/02/2026)

| Modèle | Accuracy | AUC | Statut |
|--------|----------|-----|--------|
| **XGBoost V3** | **76.76%** | **84.93%** | 🏆 **Production** |
| Neural Network | 76.84% | 85.09% | Testé |
| XGBoost V1 | 76.76% | 84.99% | Baseline |
| Random Forest | 76.19% | 84.33% | Backup |
| Smart Ensemble | 76.76% | - | Pas de gain |

### Découvertes importantes
- **Stacking inutile** : Corrélation erreurs RF/XGB = 0.885 (trop élevée)
- **Feature V3** : +30 features (85 total) → Pas de gain (76.69% vs 76.76%)
- **Data leakage corrigé** : Exclusion stats match en cours

### 🚀 Production (Nouveau)
- **API NBA Live** : 10 matchs/jour récupérés automatiquement
- **Pipeline quotidien** : `run_predictions.py` - Prédictions automatisées
- **Tracking ROI** : Suivi des performances avec rapports
- **Mapping étendu** : 61 variantes de noms d'équipes

### Documentation
- [WEEK1_SUMMARY.md](WEEK1_SUMMARY.md) - Résumé Semaine 1 (Optimisation)
- [WEEK2_SUMMARY.md](WEEK2_SUMMARY.md) - Résumé Semaine 2 (Production)

### Documentation
- [WEEK1_SUMMARY.md](WEEK1_SUMMARY.md) - Résumé complet Semaine 1
- [WEEK1_RESULTS.md](../WEEK1_RESULTS.md) - Résultats détaillés

### Commandes
```bash
# Lancer optimisations
python run_optimizations.py

# Voir résultats
cat results/week1/xgb_best_params.json
cat results/week1/rf_best_params.json
```

---

## ✅ NBA-21 - Feature Engineering [TERMINÉ]

### Résultats
- **8,871 matchs** avec 48 features complètes
- Features: globales, contexte, momentum, matchup, H2H
- **Dataset** : `data/gold/ml_features/features_all.parquet`
- **Dataset V2** : `data/gold/ml_features/features_enhanced_v2.parquet` (65 features)

### Fichiers
| Fichier | Description | Lignes |
|---------|-------------|--------|
| [src/ml/feature_engineering.py](../src/ml/feature_engineering.py) | Feature engineering PySpark | 187 |
| [src/pipeline/nba21_feature_engineering.py](../src/pipeline/nba21_feature_engineering.py) | Pipeline complet | 432 |
| [src/optimization/week1/feature_engineering_v2.py](../src/optimization/week1/feature_engineering_v2.py) | Features avancées V2 | 200+ |

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

## ✅ NBA-19 - TERMINÉ (08/02/2026)

### Résultats
- **30 équipes** avec stats agrégées complètes
- **5,103 joueurs** enrichis avec métriques NBA-18
- **Stats collectives** : points, rebonds, passes, %tirs
- **Win% moyen** : 50% (cohérent)
- **Points moyens** : 114.2 (cohérent NBA)
- **Architecture** : Single Pipeline Pattern (zero redondance)

### Fichiers
| Fichier | Description | Lignes |
|---------|-------------|--------|
| [src/processing/nba19_unified_aggregates.py](../src/processing/nba19_unified_aggregates.py) | Pipeline unifié | 521 |
| [tests/test_nba19_integration.py](../tests/test_nba19_integration.py) | Tests end-to-end | ~200 |
| [data/gold/team_season_stats/](../data/gold/team_season_stats/) | Stats équipes | 30 records |
| [data/gold/player_team_season/](../data/gold/player_team_season/) | Joueurs enrichis | 5,103 records |

### Commandes
```bash
# Exécuter NBA-19
python src/processing/nba19_unified_aggregates.py

# Vérifier résultats
cat data/gold/nba19_report.json
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

## 🚀 Production (Nouveau)

### Prédictions Quotidiennes
```bash
# Lancer les prédictions du jour
python run_predictions.py

# Mettre à jour les résultats après les matchs
python run_predictions.py --update

# Générer le rapport de performance
python run_predictions.py --report
```

### Fichiers de production
| Fichier | Description |
|---------|-------------|
| `run_predictions.py` | Script principal |
| `src/ml/pipeline/daily_pipeline.py` | Pipeline complet |
| `src/ml/pipeline/nba_live_api.py` | API NBA Live |
| `src/ml/pipeline/tracking_roi.py` | Tracking ROI |
| `predictions/latest_predictions.csv` | Dernières prédictions |
| `predictions/tracking_history.csv` | Historique tracking |

### Architecture Production
```
API NBA Live → Features → Modèle XGB → Prédictions → Tracking ROI
     ↑                                              ↓
     └───────────── Mise à jour résultats ←─────────┘
```

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
