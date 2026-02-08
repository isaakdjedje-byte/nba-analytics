# 🤖 AGENT DOCUMENTATION - NBA Analytics Platform

**Version :** 7.1 (NBA-23 V3.1 - Refactoring Complet)  
**Mise à jour :** 8 Février 2026 à 18:00  
**Statut :** ✅ Production Ready - NBA-23 Optimisé (-67% temps, 14 tests)

**Meilleur modèle** : XGBoost V3 76.76% - Pipeline quotidien + Tracking ROI  
**NBA-23** : 4 805 joueurs clusterisés, 14 archétypes, -1 630 lignes nettes

---

## 📋 Vue d'Ensemble

Pipeline Data Engineering complet : ingestion multi-saisons (2018-2024), 20+ transformations, architecture Medallion, agrégation intelligente 4 méthodes pour ML.

**Stack :** PySpark 3.5, Delta Lake 3.0, nba-api 1.1.11, Python 3.11, XGBoost, PyTorch

**Performance actuelle** : 76.84% accuracy (Neural Network), 85.09% AUC
**Objectif** : 80-82% avec stacking et features avancées

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

## 🧠 Machine Learning (NBA-22 - TERMINÉ)

### Résultats Finaux

| Modèle | Accuracy | AUC | Temps | Statut |
|--------|----------|-----|-------|--------|
| **XGBoost V3** | **76.76%** | **84.93%** | 2s | 🏆 **Production** |
| Neural Network | 76.84% | 85.09% | 5s | Testé |
| XGBoost V1 | 76.76% | 84.99% | 3min | Baseline |
| Random Forest | 76.19% | 84.33% | 3min | Backup |
| Smart Ensemble | 76.76% | - | - | Pas de gain |

**Découverte** : Stacking inutile (corrélation erreurs 0.885)

### Production (Nouveau)

```bash
# Prédictions quotidiennes
python run_predictions.py

# Mettre à jour résultats après matchs
python run_predictions.py --update

# Voir rapport ROI
python run_predictions.py --report
```

### Production Optimisée v2.0 🆕

**Optimisations:**
- **Feature Selection**: 80 → 35 features (-56%)
- **Calibration**: Probabilités fiables (Brier 0.1539)
- **Monitoring**: Data drift & système de santé
- **Performance**: 76.65% accuracy (stable)

```bash
# Lancer optimisation complète
python launch_optimization.py

# Prédictions optimisées
python run_predictions_optimized.py

# Monitoring
python run_predictions_optimized.py --health
python run_predictions_optimized.py --drift

# Réentraîner
python src/ml/pipeline/train_optimized.py
```

**Fichiers:**
- `run_predictions_optimized.py` - Pipeline v2.0
- `src/ml/pipeline/train_optimized.py` - Entraînement optimisé
- `models/optimized/` - Modèles calibrés (35 features)
- `NBA22_OPTIMIZATION_GUIDE.md` - Documentation

### Optimisation (Historique)

```bash
# Optimisation XGBoost (100 trials, ~3min)
python src/optimization/week1/optimize_xgb.py

# Optimisation Random Forest (50 trials, ~3min)
python src/optimization/week1/optimize_rf.py

# Feature Engineering V3 (+30 features)
python src/ml/pipeline/feature_engineering_v3.py

# Voir les résultats
cat results/week1/xgb_best_params.json
```

### Architecture ML
```
src/ml/
├── classification_model.py      # Modèles RF/GBT (PySpark)
├── nba22_train.py              # Pipeline entraînement V1
├── nba22_orchestrator.py       # CLI
└── pipeline/                   # 🆕 Production
    ├── nba_live_api.py         # API NBA Live
    ├── daily_pipeline.py       # Pipeline quotidien
    ├── feature_engineering_v3.py # Features V3
    ├── tracking_roi.py         # Tracking ROI
    ├── probability_calibration.py  # 🆕 Calibration
    ├── feature_selection.py    # 🆕 Feature selection
    ├── drift_monitoring.py     # 🆕 Monitoring
    └── train_optimized.py      # 🆕 Entraînement v2.0

models/week1/                   # Modèles V1
├── xgb_optimized.pkl           # Meilleur modèle V1
└── xgb_v3.pkl                  # Modèle V3 (85 features)

models/optimized/               # 🆕 Modèles v2.0
├── model_xgb.joblib            # Modèle optimisé (35 features)
├── calibrator_xgb.joblib       # Calibrateur
└── selected_features.json      # Features sélectionnées

predictions/
├── predictions_*.csv           # Prédictions quotidiennes
├── predictions_optimized_*.csv # 🆕 Prédictions v2.0
├── tracking_history.csv        # Historique ROI
├── health_report.json          # 🆕 Rapport santé
└── performance_report.txt      # Rapport performance
```

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

### Clustering (NBA-23 V3.1) ⭐ NOUVEAU
```python
src/ml/archetype/               # Module clustering (6 fichiers)
├── __init__.py                # Pipeline complet v3.1
├── feature_engineering.py     # 39+ features (hérite BaseFeatureEngineer)
├── auto_clustering.py         # GMM + K-Means (parallèle, -65% temps)
├── archetype_matcher.py       # Matcher hiérarchique (14 archétypes)
├── validation.py              # Validation 41 joueurs ground truth
├── nba19_integration.py       # Intégration stats équipe NBA-19
└── nba22_integration.py       # Intégration features équipe

src/ml/base/
└── base_feature_engineer.py   # Classe de base réutilisable

tests/
└── test_nba23_clustering.py   # 14 tests unitaires

# Scripts
nba23_clustering.py            # Script principal
benchmark_nba23.py             # Benchmark performance
test_production_nba23.py       # Test production
```

**Résultats V3.1:**
- **Performance:** 35s → 12s (-67% temps d'exécution)
- **Code:** -1 630 lignes nettes, zero duplication
- **Tests:** 14 tests unitaires (couverture >80%)
- **Joueurs:** 4 805 clusterisés en 14 archétypes hiérarchiques
- **Features:** 39+ avec AST%, VORP, WS/48 estimés
- **Validation:** 41 joueurs ground truth

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
