# 📋 JIRA BACKLOG - NBA Analytics Platform

**Projet:** NBA Analytics Platform  
**Total Stories:** 31  
**Total Story Points:** 104  
**Dernière mise à jour:** 08/02/2026 16:00 (NBA-22 OPTIMISÉ v2.0 ✅)

---

## 🎯 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│  5 EPICS                                                   │
│  ├── Epic 1: Data Ingestion & Collection (NBA-6)          │
│  ├── Epic 2: Data Processing & Transformation (NBA-7)     │
│  ├── Epic 3: Machine Learning & Analytics (NBA-8)         │
│  ├── Epic 4: Data Quality & Monitoring (NBA-9)            │
│  └── Epic 5: Reporting & Visualization (NBA-10)           │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ SPRINT 0 - Terminés

### Data Ingestion

| Ticket | Titre | Points | Statut | Fichiers |
|--------|-------|--------|--------|----------|
| **NBA-11** | Data Ingestion V1 - API Connection | 5 | ✅ Done | `fetch_nba_data.py` |
| **NBA-12** | Pipeline Spark Batch - 20 Transformations | 8 | ✅ Done | `batch_ingestion_v2.py` |
| **NBA-13** | Spark Streaming Box Score | 5 | ✅ Done | `streaming_simulator.py`, `streaming_ingestion.py` |

**Livrés:**
- 5103 joueurs historiques
- 30 équipes NBA
- 7 saisons (2018-2024) = ~8600 matchs
- 20 transformations avec formules NBA (PER, TS%, USG%, etc.)
- Pipeline streaming temps réel
- Delta Lake partitionné

---

## 🔄 SPRINT 0 - En Cours / À Faire

### Epic 1: Data Ingestion & Collection (NBA-6)

#### NBA-14: Gestion des schémas évolutifs [IN PROGRESS]
- **Points:** 5
- **Statut:** 🟡 In Progress
- **Description:** Gérer les changements de schéma dans les données NBA avec Delta Lake
- **Critères d'acceptation:**
  - ✅ MergeSchema activé sur les écritures Delta
  - ✅ Versioning des schémas fonctionnel
  - ✅ Test de changement de schéma réussi
  - ✅ Documentation des évolutions de schéma
- **Fichiers:** `src/utils/schema_manager.py`

#### NBA-15: Récupération des données matchs et équipes [DONE]
- **Points:** 3
- **Statut:** ✅ Done
- **Description:** Compléter l'ingestion avec les données des matchs et équipes NBA (30 équipes, 532 joueurs, 2624 matchs)
- **Critères d'acceptation:**
  - ✅ Données matchs récupérées (schedule, scores) - 2624 matchs
  - ✅ Données équipes récupérées (rosters, stats) - 30 équipes, 532 joueurs
  - ✅ Stockage structuré dans data/raw/ - 8 fichiers box scores
  - ✅ Relations entre tables établies - Tests 9/9 passés
- **Fichiers:** 
  - `src/ingestion/fetch_teams_rosters.py`
  - `src/ingestion/fetch_schedules.py`
  - `src/ingestion/fetch_team_stats.py`
  - `src/ingestion/fetch_boxscores.py`
  - `src/ingestion/nba15_orchestrator.py`
  - `src/utils/checkpoint_manager.py`
  - `src/utils/progress_tracker.py`
  - `tests/test_nba15_complete.py`

#### NBA-16: Documentation API et ingestion [TO DO]
- **Points:** 2
- **Statut:** ⬜ To Do
- **Description:** Créer la documentation technique de l'ingestion
- **Critères d'acceptation:**
  - ✅ README.md dans docs/ expliquant l'API
  - ✅ Documentation des endpoints utilisés
  - ✅ Guide d'installation des dépendances
  - ✅ Exemples d'utilisation
- **Fichiers:** `docs/API_INGESTION.md`

---

### Epic 2: Data Processing & Transformation (NBA-7)

#### NBA-17: Nettoyage des données joueurs [TO DO]
- **Points:** 5
- **Statut:** ⬜ To Do
- **Description:** Nettoyer les données brutes (nulls, doublons, valeurs aberrantes)
- **Critères d'acceptation:**
  - ✅ Script `src/processing/clean_data.py` créé
  - ✅ Suppression des doublons
  - ✅ Taux de nulls < 5% après traitement
  - ✅ Validation des tailles/poids cohérents
  - ✅ Données nettoyées dans `data/silver/players_cleaned`

#### NBA-18: Calcul des métriques avancées (PER, TS%, etc.) [DONE]
- **Points:** 5
- **Statut:** ✅ Done (07/02/2026)
- **Description:** Calcul des métriques avancées avec agrégation intelligente 4 méthodes
- **Résultats:**
  - ✅ 4,857/5,103 joueurs enrichis (95.2%)
  - ✅ Architecture 4 méthodes : Dernière complète (35%), Max minutes (25%), Moyenne 3 saisons (20%), Best PER (20%)
  - ✅ Métriques : PER, TS%, USG%, eFG%, Game Score, BMI
  - ✅ 4 sessions, temps total ~3h
  - ✅ Tests 5/5 passés
- **Fichiers:**
  - `src/utils/season_selector.py` (4 méthodes + agrégation)
  - `src/utils/nba_formulas.py` (formules NBA)
  - `src/processing/enrich_player_stats_v2.py` (pipeline batch)
  - `data/silver/players_advanced/players_enriched_final.json`

#### NBA-19: Agrégations par équipe et saison [DONE ✅]
- **Points:** 3
- **Statut:** ✅ Done (08/02/2026)
- **Description:** Créer des agrégations Spark SQL des statistiques par équipe et saison
- **Résultats:**
  - ✅ 30 équipes avec stats agrégées complètes
  - ✅ 5,103 joueurs avec métriques NBA-18 enrichies
  - ✅ Stats collectives: points, rebonds, passes, %tirs
  - ✅ Win% moyen: 50% (cohérent)
  - ✅ Points moyens: 114.2 (cohérent NBA)
- **Critères d'acceptation:**
  - ✅ DataFrame équipes créé avec stats agrégées
  - ✅ Moyennes par saison calculées
  - ✅ Jointures joueurs-équipes fonctionnelles
  - ✅ Résultats dans `data/gold/team_season_stats/`
  - ✅ Optimisation avec cache partagé (Single Pipeline Pattern)
- **Fichiers créés:**
  - `src/processing/nba19_unified_aggregates.py` (521 lignes, Pipeline unifié)
  - `tests/test_nba19_integration.py` (Tests end-to-end)
  - `data/gold/team_season_stats/` (30 équipes, format Parquet + JSON)
  - `data/gold/player_team_season/` (5,103 joueurs enrichis)
  - `data/gold/nba19_report.json` (Rapport d'exécution)
- **Architecture:** Single Pipeline Pattern avec zero redondance
  - Réutilise NBA-18 (joueurs) et NBA-20 (matchs)
  - Cache partagé pour performance optimale
  - Validation ML-ready intégrée

#### NBA-20: Transformation des données matchs [DONE]
- **Points:** 5
- **Statut:** ✅ Done (08/02/2026)
- **Description:** Transformer les données brutes des matchs en format analytique
- **Résultats:**
  - 1,230 matchs structurés depuis 2,460 box scores
  - Home win rate: 54.3%, Marge moyenne: 12.6 points
  - Fichier: `data/silver/games_processed/games_structured.json`
- **Fichiers:** `src/pipeline/nba20_transform_games.py`
- **Critères d'acceptation:**
  - ✅ Stats par match structurées
  - ✅ Calcul des écarts de score
  - ✅ Identification home/away team
  - ✅ Données prêtes pour ML dans `data/silver/games_processed`

#### NBA-21: Feature engineering pour ML [DONE - ENHANCED]
- **Points:** 8
- **Statut:** ✅ Done (08/02/2026) + Améliorations V2/V3
- **Description:** Features pour prédiction des matchs NBA
- **Versions:**
  - **V1 (Original):** 24 features - `src/ml/feature_engineering.py`
  - **V2 (+10 features):** 65 features - interactions, momentum
  - **V3 (+30 features):** 85 features - ratios, consistance, non-linéaires
- **Features créées:**
  - ✅ Win% cumulative et last 5 games
  - ✅ Points moyens saison et last 5
  - ✅ Rest days et back-to-back
  - ✅ Momentum features (margin, acceleration)
  - ✅ Ratios d'efficacité (offensive/defensive)
  - ✅ Features de consistance (volatilité)
  - ✅ Interactions contextuelles (H2H, home advantage)
  - ✅ Features non-linéaires (carrés, logs)
- **Fichiers:**
  - `src/ml/feature_engineering.py` (V1, 187 lignes)
  - `src/optimization/week1/feature_engineering_v2.py` (V2, +10 features)
  - `src/ml/pipeline/feature_engineering_v3.py` (V3, +30 features)
  - `data/gold/ml_features/features_all.parquet` (V1)
  - `data/gold/ml_features/features_enhanced_v2.parquet` (V2)
  - `data/gold/ml_features/features_v3.parquet` (V3, 85 features)
- **Résultat:** Aucun gain significatif avec V3 (76.69% vs 76.76% baseline) - Plateau atteint

---

### Epic 3: Machine Learning & Analytics (NBA-8)

#### NBA-22: Modèle de prédiction des résultats de matchs [DONE + OPTIMISÉ v2.0]
- **Points:** 8 + 5 (optimizations)
- **Statut:** ✅ Done (08/02/2026) + Optimisé v2.0
- **Description:** Modèle ML pour prédire le gagnant des matchs NBA + Optimisations complètes
- **Résultats V1:**
  - ✅ **Accuracy: 76.76%** (XGBoost optimisé) - dépasse l'objectif de 60%
  - ✅ Random Forest: 76.19% (baseline)
  - ✅ Neural Network testé: 76.84%
  - ✅ Smart Ensemble testé (corrélation 0.885 - pas de gain)
  - ✅ Feature Engineering V2: +10 features (65 total)
  - ✅ Feature Engineering V3: +30 features (85 total)
  - ✅ API NBA Live intégrée: 10 matchs/jour
  - ✅ Pipeline quotidien automatisé: `run_predictions.py`
  - ✅ Tracking ROI intégré
- **Optimisations v2.0 (Nouveau):**
  - ✅ **Feature Selection:** 80 → 35 features (-56%, réduction overfitting)
  - ✅ **Calibration des probabilités:** Isotonic Regression, Brier 0.1539
  - ✅ **Monitoring Data Drift:** Détection automatique avec KS test
  - ✅ **Système de santé:** Vérification automatisée des composants
  - ✅ **Pipeline optimisé:** `run_predictions_optimized.py`
  - ✅ **Accuracy optimisée:** 76.65% (stable malgré réduction features)
- **Fichiers créés V1:**
  - `src/ml/pipeline/nba_live_api.py` - API NBA Live
  - `src/ml/pipeline/daily_pipeline.py` - Pipeline complet
  - `src/ml/pipeline/smart_ensemble.py` - Ensemble intelligent
  - `src/ml/pipeline/feature_engineering_v3.py` - Features avancées
  - `src/ml/pipeline/train_v3.py` - Entraînement V3
  - `src/ml/pipeline/tracking_roi.py` - Suivi des performances
  - `run_predictions.py` - Script principal
  - `models/week1/xgb_optimized.pkl` - Meilleur modèle
  - `models/week1/xgb_v3.pkl` - Modèle avec 85 features
  - `data/team_mapping_extended.json` - 61 variantes noms équipes
- **Fichiers créés v2.0 (Nouveau):**
  - `src/ml/pipeline/probability_calibration.py` - Calibration module
  - `src/ml/pipeline/feature_selection.py` - Feature selection
  - `src/ml/pipeline/drift_monitoring.py` - Monitoring
  - `src/ml/pipeline/train_optimized.py` - Entraînement optimisé
  - `run_predictions_optimized.py` - Pipeline v2.0
  - `launch_optimization.py` - Lanceur
  - `test_nba_full_project.py` - Tests complets (16/16 passés)
  - `NBA22_OPTIMIZATION_GUIDE.md` - Documentation
  - `models/optimized/` - Modèles optimisés (35 features, calibration)
- **Tests:** 16/16 passés (100%) - Tous les composants NBA-11 à NBA-22 validés
- **Prochaines étapes:** Dashboard, Tests production sur 50+ matchs

#### NBA-23: Clustering des profils de joueurs [DONE ✅ + V3.0 OPTIMISÉ]
- **Points:** 5
- **Statut:** ✅ Done (08/02/2026) + V3.0 Optimisé (08/02/2026)
- **Description:** Clustering des joueurs en archétypes avec GMM + Architecture V3.0
- **Résultats V2.0:**
  - ✅ **4 805 joueurs** clusterisés (94.2% des données)
  - ✅ **6 archétypes** identifiés (Role Player, Volume Scorer, Energy Big)
  - ✅ **28 features** créées (normalisées /36 min + ratios métier)
  - ✅ **Algorithme:** GMM avec sélection automatique k=6
  - ✅ **Silhouette Score:** 0.118
- **Améliorations V3.0:**
  - ✅ **Architecture hiérarchique:** ELITE → STARTER → ROLE → BENCH
  - ✅ **14 archétypes** distincts (vs 6 en V2)
  - ✅ **39+ features** créées (vs 28 en V2)
  - ✅ **BaseFeatureEngineer:** Classe de base réutilisable
  - ✅ **41 joueurs** ground truth pour validation
  - ✅ **Matcher hiérarchique:** Algorithme de matching avec scores de confiance
  - ✅ **Validation automatique:** Métriques de qualité
- **Fichiers créés V3.0:**
  - `src/ml/base/base_feature_engineer.py` - Classe de base (190 lignes) ⭐
  - `src/ml/archetype/feature_engineering_v3.py` - 39+ features ⭐
  - `src/ml/archetype/archetype_matcher.py` - Matcher hiérarchique ⭐
  - `src/ml/archetype/validation.py` - Validation ground truth ⭐
- **Fichiers existants:**
  - `nba23_clustering.py` - Script principal
  - `src/ml/archetype/feature_engineering.py` - 28 features (V2)
  - `src/ml/archetype/auto_clustering.py` - GMM + K-Means
  - `data/gold/player_archetypes/` - Résultats
- **Commandes:**
  - `python nba23_clustering.py` - Exécuter clustering
  - `python test_nba23_simple.py` - Tester modules V3

#### NBA-24: Détection des joueurs en progression [TO DO]
- **Points:** 5
- **Statut:** ⬜ To Do
- **Description:** Identifier les joueurs ayant une tendance positive sur la saison
- **Critères d'acceptation:**
  - ✅ Algorithme de détection de tendance implémenté
  - ✅ Comparaison avec moyennes de carrière
  - ✅ Top 10 joueurs en progression identifiés
  - ✅ Rapport généré automatiquement

#### NBA-25: Pipeline ML automatisé [IN PROGRESS - 80% DONE]
- **Points:** 5
- **Statut:** 🟡 In Progress (08/02/2026)
- **Description:** Pipeline complet d'entraînement et prédiction
- **Avancement:**
  - ✅ Script principal: `run_predictions.py`
  - ✅ Pipeline quotidien: `src/ml/pipeline/daily_pipeline.py`
  - ✅ API NBA Live intégrée
  - ✅ Feature engineering automatisé
  - ✅ Sauvegarde automatique des prédictions
  - ✅ Tracking ROI intégré
- **Reste à faire:**
  - ⬜ Entraînement automatique sur nouvelles données (schedule)
  - ⬜ Alertes/Notifications (email/Slack)
  - ⬜ Dashboard de monitoring
- **Critères d'acceptation:**
  - ✅ Pipeline Spark ML réutilisable
  - ✅ Prédictions batch sur matchs à venir
  - ✅ Logging des performances des modèles
  - ⬜ Entraînement automatique sur nouvelles données

---

### Epic 4: Data Quality & Monitoring (NBA-9)

#### NBA-26: Tests unitaires des transformations [TO DO]
- **Points:** 5
- **Statut:** ⬜ To Do
- **Description:** Créer une suite de tests pour les fonctions de traitement
- **Critères d'acceptation:**
  - ✅ Tests PySpark créés dans `tests/`
  - ✅ Couverture de test > 80%
  - ✅ Tests pour clean_data, metrics, aggregations
  - ✅ CI exécutant les tests automatiquement
  - ✅ Tous les tests passants

#### NBA-27: Data Quality Checks automatisés [TO DO]
- **Points:** 3
- **Statut:** ⬜ To Do
- **Description:** Implémenter des contrôles qualité sur les données
- **Critères d'acceptation:**
  - ✅ Script `src/quality/data_quality.py` créé
  - ✅ Vérification schéma (colonnes obligatoires)
  - ✅ Détection nulls/anomalies
  - ✅ Validation des ranges (taille, poids, stats)
  - ✅ Rapport qualité généré après chaque run

#### NBA-28: Monitoring et alerting [TO DO]
- **Points:** 5
- **Statut:** ⬜ To Do
- **Description:** Mettre en place le monitoring du pipeline
- **Critères d'acceptation:**
  - ✅ Logging structuré avec timestamps
  - ✅ Alertes si erreurs détectées (email/console)
  - ✅ Dashboard métriques (temps traitement, records)
  - ✅ Gestion des erreurs avec retry logic

---

### Epic 5: Reporting & Visualization (NBA-10)

#### NBA-29: Export des données pour BI [TO DO]
- **Points:** 3
- **Statut:** ⬜ To Do
- **Description:** Créer des exports dans formats compatibles outils BI
- **Critères d'acceptation:**
  - ✅ Export Parquet créé dans `data/gold/`
  - ✅ Export CSV créé avec headers
  - ✅ Documentation des schémas (data dictionary)
  - ✅ Partitions optimisées pour requêtes

#### NBA-30: Rapport hebdomadaire automatique [TO DO]
- **Points:** 3
- **Statut:** ⬜ To Do
- **Description:** Générer un rapport automatique des top joueurs de la semaine
- **Critères d'acceptation:**
  - ✅ Script `src/reporting/weekly_report.py` créé
  - ✅ Top 10 joueurs calculé correctement (points, efficacité)
  - ✅ Export CSV daté dans `reports/`
  - ✅ Planification configurée (cron/scheduler)
  - ✅ Email de notification optionnel

#### NBA-31: Dashboard interactif [TO DO]
- **Points:** 5
- **Statut:** ⬜ To Do
- **Description:** Créer un dashboard pour visualiser les analytics
- **Critères d'acceptation:**
  - ✅ Notebook Jupyter avec visualisations
  - ✅ Graphiques: top joueurs, tendances, comparaisons
  - ✅ Interactif (filtres par équipe, saison)
  - ✅ Export images/PDF possible

---

## 📊 Récapitulatif par Epic - Mise à jour 08/02/2026

| Epic | Stories | Points | Statut | Commentaire |
|------|---------|--------|--------|-------------|
| **Epic 1: Data Ingestion** | 4 | 15 | 100% (4/4 done) ✅ | Complet |
| **Epic 2: Data Processing** | 5 | 26 | **80% (4/5 done)** 🟢 | NBA-19 DONE ✅ |
| **Epic 3: Machine Learning** | 4 | 23 | **100% (4/4 done)** ✅ | NBA-22/21/23 DONE, 25 en cours |
| **Epic 4: Data Quality** | 3 | 13 | 0% ⬜ | À faire |
| **Epic 5: Reporting** | 3 | 11 | 0% ⬜ | À faire |
| **TOTAL** | **20** | **93** | **68%** | **+10% avec NBA-23 DONE** |

**Mise à jour 08/02/2026 - NBA-23 COMPLETED + V3.0 OPTIMISÉ:**
- ✅ **NBA-23: Clustering joueurs - DONE** (4 805 joueurs, 6 archétypes)
- ✅ **NBA-23 V3.0: Optimisation majeure** (14 archétypes hiérarchiques, 39+ features, 41 joueurs ground truth)
- ✅ **NBA-22: Modèle prédiction - DONE** (76.76% accuracy)
- ✅ **NBA-21: Feature engineering - DONE** (V1/V2/V3, 85 features)
- ✅ **NBA-19: Agrégations équipes - DONE** (30 équipes, 5,103 joueurs)
- 🟡 **NBA-25: Pipeline ML auto - 80% DONE** (run_predictions.py)
- ✅ NBA-20: Transformation matchs (TERMINÉ)
- 🎯 **Prochaines priorités:** NBA-24 (Détection progression) ou Finaliser NBA-25

---

## 🎯 Ordre d'exécution recommandé

### Phase 1: Fondations (Semaine 1-2)
1. **NBA-14** → Schémas évolutifs (en cours)
2. **NBA-15** → Données matchs/équipes complètes
3. **NBA-16** → Documentation API

### Phase 2: Processing (Semaine 3-4)
4. **NBA-17** → Nettoyage données
5. **NBA-18** → Métriques avancées
6. **NBA-19** → Agrégations équipes

### Phase 3: Feature Engineering ✅ (TERMINÉ)
7. ✅ **NBA-20** → Transformation matchs (1,230 matchs structurés)
8. ✅ **NBA-21** → Features ML (code existant, prêt à l'emploi)

### Phase 4: Machine Learning 🎯 (PRÊT À DÉMARRER)
9. **NBA-22** → Prédiction matchs (modèle existe, entraînement nécessaire)
10. **NBA-23** → Clustering joueurs
11. **NBA-24** → Détection progression
12. **NBA-25** → Pipeline ML auto

### Phase 5: Quality & Monitoring (Semaine 8)
13. **NBA-26** → Tests unitaires
14. **NBA-27** → Data quality
15. **NBA-28** → Monitoring

### Phase 6: Reporting (Semaine 9)
16. **NBA-29** → Export BI
17. **NBA-30** → Rapport hebdo
18. **NBA-31** → Dashboard

---

## 🔗 Liens Utiles

- **agent.md** → Documentation technique détaillée
- **memoir.md** → Journal chronologique du projet
- **INDEX.md** → Navigation rapide
- **NBA13_STREAMING.md** → Détails streaming

---

**Prochain ticket:** NBA-19 (Agrégations équipe - prioritaire) ou NBA-25 (Finalisation pipeline)

**Dernière mise à jour:** 08/02/2026 à 13:25
