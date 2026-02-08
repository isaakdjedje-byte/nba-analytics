# 📋 JIRA BACKLOG - NBA Analytics Platform

**Projet:** NBA Analytics Platform  
**Total Stories:** 31  
**Total Story Points:** 104  
**Dernière mise à jour:** 07/02/2026 (NBA-18 ✅)

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

#### NBA-19: Agrégations par équipe et saison [TO DO]
- **Points:** 3
- **Statut:** ⬜ To Do
- **Description:** Créer des agrégations Spark SQL des statistiques
- **Critères d'acceptation:**
  - ✅ DataFrame équipes créé avec stats agrégées
  - ✅ Moyennes par saison calculées
  - ✅ Jointures joueurs-équipes fonctionnelles
  - ✅ Résultats dans `data/gold/team_stats_season`
  - ✅ Optimisation des requêtes SQL

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

#### NBA-21: Feature engineering pour ML [READY]
- **Points:** 8
- **Statut:** ✅ Ready (existe déjà)
- **Description:** Créer les features nécessaires pour les modèles de prédiction
- **Fichier:** `src/ml/feature_engineering.py` (187 lignes, complet)
- **Features existantes:**
  - ✅ Win% cumulative et last 5 games
  - ✅ Points moyens saison et last 5
  - ✅ Rest days et back-to-back
  - ✅ Momentum features (margin)
- **Note:** Code existant, prêt à l'emploi

---

### Epic 3: Machine Learning & Analytics (NBA-8)

#### NBA-22: Modèle de prédiction des résultats de matchs [TO DO]
- **Points:** 8
- **Statut:** ⬜ To Do
- **Description:** Créer un modèle ML Spark pour prédire le gagnant des matchs
- **Critères d'acceptation:**
  - ✅ Features engineering réalisé
  - ✅ Modèle Random Forest entraîné dans `src/ml/predict_games.py`
  - ✅ Précision > 60% sur test set
  - ✅ Modèle sauvegardé dans `models/`
  - ✅ Évaluation avec métriques (accuracy, precision, recall)

#### NBA-23: Clustering des profils de joueurs [TO DO]
- **Points:** 5
- **Statut:** ⬜ To Do
- **Description:** Utiliser K-Means pour classifier les joueurs par profil
- **Critères d'acceptation:**
  - ✅ 5 clusters définis (shooter, défenseur, all-around, etc.)
  - ✅ Caractéristiques de chaque cluster identifiées
  - ✅ Visualization des clusters (export ou notebook)
  - ✅ Interprétation métier validée
  - ✅ Script dans `src/ml/cluster_players.py`

#### NBA-24: Détection des joueurs en progression [TO DO]
- **Points:** 5
- **Statut:** ⬜ To Do
- **Description:** Identifier les joueurs ayant une tendance positive sur la saison
- **Critères d'acceptation:**
  - ✅ Algorithme de détection de tendance implémenté
  - ✅ Comparaison avec moyennes de carrière
  - ✅ Top 10 joueurs en progression identifiés
  - ✅ Rapport généré automatiquement

#### NBA-25: Pipeline ML automatisé [TO DO]
- **Points:** 5
- **Statut:** ⬜ To Do
- **Description:** Créer un pipeline complet d'entraînement et prédiction
- **Critères d'acceptation:**
  - ✅ Pipeline Spark ML réutilisable
  - ✅ Entraînement automatique sur nouvelles données
  - ✅ Prédictions batch sur matchs à venir
  - ✅ Logging des performances des modèles

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

## 📊 Récapitulatif par Epic

| Epic | Stories | Points | Statut |
|------|---------|--------|--------|
| **Epic 1: Data Ingestion** | 4 | 15 | 100% (4/4 done) ✅ |
| **Epic 2: Data Processing** | 5 | 26 | 60% (3/5 done) 🟡 |
| **Epic 3: Machine Learning** | 4 | 23 | 25% (1/4 ready) 🟡 |
| **Epic 4: Data Quality** | 3 | 13 | 0% |
| **Epic 5: Reporting** | 3 | 11 | 0% |
| **TOTAL** | **19** | **88** | **47%** |

**Mise à jour 08/02/2026:**
- ✅ NBA-19: Agrégations équipes (TERMINÉ)
- ✅ NBA-20: Transformation matchs (TERMINÉ)
- ✅ NBA-21: Feature engineering (EXSITE DÉJÀ)
- 🎯 Prochain: NBA-22 (Classification - existe déjà, prêt à utiliser)

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

**Prochain ticket:** NBA-14 (en cours) → NBA-15

**Dernière mise à jour:** 06/02/2026
