---
# Index des Documentations NBA Analytics
# Dernière mise à jour: 2026-02-07 00:15 (Architecture Medallion complète)
# Usage: Référence rapide pour éviter de lire les fichiers complets
---

# 📚 INDEX - Documentation NBA Analytics

## 🆕 NOUVEAU - PHASE 4-7 : Production Ready (07/02/2026)

### 🎉 Résultats Finaux
**GOLD Standard :** 5,103 joueurs (+3,050%)  
**Performance :** 1.7 secondes pipeline  
**Qualité :** 100% données physiques complètes  

### Architecture GOLD Tiered
- [`players_gold_standard`](data/silver/players_gold_standard/) - 5,103 joueurs (100% height/weight)
- [`players_gold_elite`](data/silver/players_gold_premium_elite/) - 3,906 joueurs (98.4% confiance)
- [`players_gold_premium`](data/silver/players_gold_premium/) - 4,468 joueurs (ML général)

### Documentation Phases
- [`IMPROVEMENT_PLAN.md`](../IMPROVEMENT_PLAN.md) - Plan complet 15 jours
- [`PHASE2_RESULTS.md`](../PHASE2_RESULTS.md) - Enrichissement ML
- [`PHASE3_RESULTS.md`](../PHASE3_RESULTS.md) - GOLD Elite
- [`memoir.md`](memoir.md#phase-4-7) - Journal phases 4-7
- [`agent.md`](agent.md#phase-4-7) - Architecture production

### Commandes Rapides
```bash
python run_pipeline.py --stratified      # Pipeline complet
python use_gold_tiered.py --compare      # Comparer tiers
python final_validation.py               # Valider résultats
pytest tests/test_integration.py -v      # Tests
```

---

## 🏗️ Architecture Medallion (07/02/2026)
**Architecture :** Bronze → Silver → Gold  
**Fichiers :** 19 modules + 6 nouveaux (Phase 4-7)  
**Tests :** 5 fichiers de tests  

**Documentation détaillée :**
- [`agent.md:98-145`](agent.md#L98) - Architecture Medallion complète
- [`agent.md:732-780`](agent.md#L732) - Dernières modifications refactor

**Démarrage rapide :**
```bash
python run_pipeline.py              # Pipeline complet
python run_pipeline.py --bronze-only # Bronze uniquement
```

---

## 🗺️ Vue d'ensemble des fichiers

| Fichier | Lignes | Contenu principal | Dernière MAJ |
|---------|--------|-------------------|--------------|
| [`agent.md`](agent.md) | 1000+ | **Architecture Production**, commandes, Phase 4-7 | 2026-02-07 |
| [`memoir.md`](memoir.md) | 1500+ | Journal complet + **Phase 4-7** | 2026-02-07 |
| [`API_INGESTION.md`](API_INGESTION.md) | ~350 | Documentation API NBA (NBA-16) | 2026-02-06 |
| [`INSTALLATION.md`](INSTALLATION.md) | ~300 | Guide installation complète (NBA-16) | 2026-02-06 |
| [`EXAMPLES.md`](EXAMPLES.md) | ~150 | Exemples pratiques Python (NBA-16) | 2026-02-06 |
| [`JIRA_BACKLOG.md`](JIRA_BACKLOG.md) | ~500 | **TOUS les tickets JIRA** | 2026-02-06 |
| [`stories/`](stories/) | 18 fichiers | Stories détaillées NBA-14 à NBA-31 | 2026-02-06 |
| [`IMPROVEMENT_PLAN.md`](../IMPROVEMENT_PLAN.md) | ~400 | **Plan amélioration complet** | 2026-02-07 |
| [`PHASE2_RESULTS.md`](../PHASE2_RESULTS.md) | ~300 | Résultats enrichissement ML | 2026-02-07 |
| [`PHASE3_RESULTS.md`](../PHASE3_RESULTS.md) | ~300 | Résultats GOLD Elite | 2026-02-07 |

---

## 🎯 Navigation par Besoin

### "Je veux comprendre l'architecture"
→ [`agent.md:22-81`](agent.md#L22) - Stack technique et structure données

### "Je veux les formules NBA"
→ [`agent.md:139-193`](agent.md#L139) - PER, USG%, TS%, Pace, Game Score

### "Je veux voir l'historique des tickets"
→ [`memoir.md:26-550`](memoir.md#L26) - Chronologie NBA-11 à NBA-15
→ [`JIRA_BACKLOG.md`](JIRA_BACKLOG.md) - **TOUS les tickets détaillés (NBA-11 à NBA-31)**

### "Je veux les problèmes connus et solutions"
→ [`agent.md:226-270`](agent.md#L226) - Rate limit, Delta Lake, Git
→ [`memoir.md:293-311`](memoir.md#L293) - Problèmes en cours

### "Je veux voir une story spécifique (NBA-14+)"
→ [`stories/NBA-14_schema_evolutif.md`](stories/NBA-14_schema_evolutif.md) - Schémas évolutifs
→ [`stories/NBA-17_nettoyage.md`](stories/NBA-17_nettoyage.md) - Nettoyage données
→ [`stories/NBA-22_ml_prediction.md`](stories/NBA-22_ml_prediction.md) - ML Prédiction
→ [`stories/NBA-31_dashboard.md`](stories/NBA-31_dashboard.md) - Dashboard
→ **Toutes les stories dans [`stories/`](stories/)**

### "Je veux savoir quoi faire ensuite"
→ [`JIRA_BACKLOG.md`](JIRA_BACKLOG.md) - **TOUS les tickets avec détails complets**
→ [`JIRA_BACKLOG.md#ordre-dexécution-recommandé`](JIRA_BACKLOG.md#ordre-dexécution-recommandé) - Roadmap détaillée

### "Je veux les améliorations Phase 4-7"
→ [`memoir.md#phase-4-7`](memoir.md#phase-4-7) - Journal phases 4-7  
→ [`agent.md#phase-4-7`](agent.md#phase-4-7) - Architecture production  
→ [`IMPROVEMENT_PLAN.md`](../IMPROVEMENT_PLAN.md) - Plan complet 15 jours

### "Je veux les résultats des phases"
→ [`PHASE2_RESULTS.md`](../PHASE2_RESULTS.md) - Enrichissement ML (4,468 joueurs)  
→ [`PHASE3_RESULTS.md`](../PHASE3_RESULTS.md) - GOLD Elite (98.4% qualité)  
→ [`final_validation.py`](../final_validation.py) - Script validation

### "Je veux utiliser les données GOLD"
→ [`use_gold_tiered.py --compare`](../use_gold_tiered.py) - Comparer les tiers  
→ [`use_gold_tiered.py --export standard`](../use_gold_tiered.py) - Exporter CSV  
→ `data/silver/players_gold_standard/players.json` - 5,103 joueurs

### "Je veux les commandes Spark"
→ [`agent.md:317-350`](agent.md#L317) - Vérification données, tests rapides

---

## 🏛️ Navigation Architecture Medallion

### "Je veux comprendre l'architecture Bronze → Silver → Gold"
→ [`agent.md:98-145`](agent.md#L98) - Architecture Medallion complète  
→ [`agent.md:732-780`](agent.md#L732) - Dernières modifications refactor

### "Je veux lancer le pipeline"
```bash
python run_pipeline.py              # Pipeline complet
python run_pipeline.py --bronze-only # Bronze uniquement
```

### "Je veux voir les fichiers source"
**Bronze Layer :**
- `src/processing/bronze/players_bronze.py` - Ingestion API
- `src/processing/bronze/validate_bronze.py` - Validation

**Silver Layer :**
- `src/processing/silver/cleaning_functions.py` - Fonctions pures
- `src/processing/silver/players_silver.py` - Transformation
- `src/processing/silver/validators.py` - Validation qualité

**Gold Layer :**
- `src/processing/gold/players_gold.py` - Features ML

**Pipeline :**
- `src/pipeline/players_pipeline.py` - Orchestration
- `run_pipeline.py` - Script de démarrage

**Utils :**
- `src/utils/transformations.py` - Fonctions de conversion
- `src/utils/caching.py` - Gestion cache API

### "Je veux voir les tests"
→ `tests/test_transformations.py` - Tests transformations  
→ `tests/test_caching.py` - Tests cache  
→ `tests/test_bronze_layer.py` - Tests Bronze  
→ `tests/test_silver_layer.py` - Tests Silver  
→ `tests/test_pipeline.py` - Tests pipeline

---

## 🎫 Index des Tickets JIRA

**📍 SOURCE DE VÉRITÉ :** [`JIRA_BACKLOG.md`](JIRA_BACKLOG.md) - Tous les tickets détaillés

### Vue rapide

| Ticket | Statut | Epic | Points | Description |
|--------|--------|------|--------|-------------|
| **NBA-11** | ✅ Done | Ingestion | 5 | API nba-api, 5103 joueurs |
| **NBA-12** | ✅ Done | Ingestion | 8 | Multi-saisons + 20 transformations |
| **NBA-13** | ✅ Done | Ingestion | 5 | Spark Streaming Box Score |
| **NBA-14** | ✅ Done | Ingestion | 5 | Gestion schémas évolutifs |
| **NBA-15** | ✅ Done | Ingestion | 3 | Données matchs et équipes |
| **NBA-16** | ✅ Done | Ingestion | 2 | Documentation API complète |
| **NBA-17** | ✅ Done | Processing | 5 | Nettoyage données + **Architecture Medallion** |
| **NBA-18** | ⬜ Ready | Processing | 5 | Métriques avancées (PER, TS%) |
| **NBA-19** | ⬜ To Do | Processing | 3 | Agrégations équipe/saison |
| **NBA-20** | ⬜ To Do | Processing | 5 | Transformation matchs |
| **NBA-21** | ⬜ To Do | Processing | 8 | Feature engineering ML |
| **NBA-22-1** | ⬜ To Do | ML | 6 | Classification gagnant/perdant |
| **NBA-22-2** | ⬜ To Do | ML | 8 | Régression score exact |
| **NBA-22-3** | ⬜ To Do | ML | 5 | Clustering profils joueurs |
| **NBA-23** | ⬜ To Do | ML | 5 | Clustering joueurs (K-Means) |
| **NBA-24** | ⬜ To Do | ML | 5 | Détection joueurs progression |
| **NBA-25** | ⬜ To Do | ML | 5 | Pipeline ML automatisé |
| **NBA-26** | ⬜ To Do | Quality | 5 | Tests unitaires |
| **NBA-27** | ⬜ To Do | Quality | 3 | Data Quality checks |
| **NBA-17** | 🟡 In Progress | Processing | 5 | Nettoyage données (optimisé 2000-2026) |
| **NBA-18** | ⬜ Ready | Processing | 5 | Métriques avancées (fichiers prêts) |
| **NBA-21** | ⬜ Ready | ML | 8 | Feature engineering (notebook créé) |
| **NBA-22** | ⬜ Ready | ML | 19 | 3 modèles ML (notebooks créés) |
| **NBA-28** | ⬜ To Do | Quality | 5 | Monitoring et alerting |
| **NBA-29** | ⬜ To Do | Reporting | 3 | Export BI (Parquet/CSV) |
| **NBA-30** | ⬜ To Do | Reporting | 3 | Rapport hebdomadaire auto |
| **NBA-31** | ⬜ To Do | Reporting | 5 | Dashboard interactif |

**📊 Total : 31 tickets | 104 points | 47% complété (7/15 done + refactor architecture)**

---

## 🆕 Nouveautés Récentes

### Architecture Medallion (07/02/2026) - **MAJEUR**
**Refactor complet : Monolithique → Bronze → Silver → Gold**

**Nouveaux fichiers (19) :**
- ✅ `src/processing/bronze/` - Couche Bronze (3 fichiers)
- ✅ `src/processing/silver/` - Couche Silver (4 fichiers)
- ✅ `src/processing/gold/` - Couche Gold (2 fichiers)
- ✅ `src/pipeline/` - Orchestration (2 fichiers)
- ✅ `src/utils/transformations.py` - Fonctions pures
- ✅ `src/utils/caching.py` - Cache API
- ✅ `run_pipeline.py` - Script de démarrage

**Tests (5 nouveaux) :**
- ✅ `tests/test_transformations.py`
- ✅ `tests/test_caching.py`
- ✅ `tests/test_bronze_layer.py`
- ✅ `tests/test_silver_layer.py`
- ✅ `tests/test_pipeline.py`

**Avantages :**
- 🔧 Fonctions pures, testables unitairement
- 📦 Séparation claire des responsabilités
- 🐛 Debug facilité (inspection à chaque étape)
- 📈 Évolutivité (ajout facile de transformations)

### Structure ML (Créée le 06/02/2026)
- ✅ `src/ml/` - Module Python avec classes PySpark ML
- ✅ `notebooks/04_model_classification.ipynb` - Random Forest Classifier
- ✅ `notebooks/05_model_regression.ipynb` - Deux modèles RF (home/away)
- ✅ `notebooks/06_model_clustering.ipynb` - K-Means clustering
- ✅ `models/` - Dossier pour sauvegardes modèles

### Optimisation NBA-17
- 🚀 **86% réduction** des appels API (4,541 → 638)
- ⏱️ **Temps** : 76 min → 10-12 min
- 🎯 **Filtre** : Joueurs 2016+ uniquement + 18 légendes critiques

---

## 📋 Index Détaillé - agent.md

### Section 1: Vue d'ensemble (lignes 1-20)
- Objectifs projet
- Stack technique (Spark, Delta Lake, nba-api)
- Architecture Data Lake (Raw → Processed → Gold)

### Section 2: Architecture (lignes 22-81)
- **Ligne 24-52** : Diagramme stack technique
- **Ligne 54-81** : Structure répertoires avec statuts (✓ ⬜)

### Section 3: Configuration (lignes 83-100)
- Dépendances Python (pyspark, delta-spark, nba-api)
- Variables d'environnement

### Section 4: Conventions (lignes 102-135)
- Nommage fichiers/fonctions/classes
- Structure commits Git
- Patterns Spark (transform, Window functions)

### Section 5: Données & Formules (lignes 139-193)
- **Ligne 141-148** : Saisons couvertes (2018-2024)
- **Ligne 152-163** : PER (Player Efficiency Rating)
- **Ligne 165-169** : Usage Rate (USG%)
- **Ligne 171-174** : True Shooting % (TS%)
- **Ligne 176-180** : Pace (rythme)
- **Ligne 182-185** : Effective FG% (eFG%)
- **Ligne 187-191** : Game Score

### Section 6: Transformations (lignes 195-224)
- **Groupe 1 (lignes 197-203)** : Fondations (typage, nulls, timestamps, déduplication, partitionnement)
- **Groupe 2 (lignes 205-210)** : Forme (moyenne mobile 5 matchs, tendance, jours repos, back-to-back, H2H)
- **Groupe 3 (lignes 212-218)** : Stats avancées (TS%, eFG%, Game Score, fatigue, PER, USG%)
- **Groupe 4 (lignes 220-224)** : Contexte (classement, record H/A, marge points, importance match)

### Section 7: Problèmes & Solutions (lignes 226-270)
- **Ligne 229-235** : Rate Limit API → Délai 2s + retry exponentiel
- **Ligne 236-238** : Scrambled Data → Migration nba-api
- **Ligne 239-243** : Formules PER complexes → Décomposition uPER
- **Ligne 244-247** : Multi-saisons volumétrie → Partitionnement Delta Lake
- **Ligne 248-251** : Git LF/CRLF → Config Windows acceptée
- **Ligne 252-259** : Streaming Socket instable → Architecture fichier
- **Ligne 260-266** : Conflits Checkpoint Spark → Checkpoint unique par run
- **Ligne 267-270** : Score non monotone → Algorithme garanti

### Section 8: Workflow Git (lignes 273-300)
- Créer feature branch
- Commit & Push
- Pull Request process

### Section 9: JIRA Workflow (lignes 303-315)
- Structure: 5 Epics, 26 Stories, 104 points
- Sprint 1: 100% complété (NBA-11, NBA-12, NBA-13)
- Statuts: To Do → In Progress → In Review → Done

### Section 10: Commandes Utiles (lignes 317-350)
- **Lignes 320-334** : Vérifier données (ls, pyspark)
- **Lignes 336-350** : Tests rapides (fetch, batch, streaming)

---

## 📋 Index Détaillé - memoir.md

### Section 1: Contexte Initial (lignes 9-24)
- Pourquoi ce projet (formation Data Engineering)
- Besoin métier (analyse, prédiction, betting)

### Section 2: Chronologie

#### Phase 0 - Setup (lignes 26-40)
- Structure projet Git
- Installation dépendances
- Configuration JIRA

#### NBA-11 - Data Ingestion V1 (lignes 42-68)
- **Ligne 45-50** : Choix API (SportsData.io vs BallDontLie vs nba-api)
- **Ligne 52-64** : Code développé et résultats
- **Ligne 65-67** : Merge et commit

#### NBA-12 - Multi-saisons (lignes 70-172)
- **Ligne 73-77** : Évolution besoins (5 → 20 transformations)
- **Ligne 78-89** : Architecture retenue
- **Ligne 91-97** : Formules NBA recherchées
- **Lignes 99-118** : Difficulté 1 - Rate Limit
- **Lignes 120-146** : Difficulté 2 - Formules PER complexes
- **Lignes 148-171** : Difficulté 3 - Architecture Delta Lake

#### NBA-13 - Spark Streaming (lignes 404-480)
- **Ligne 408-412** : Architecture retenue (fichiers)
- **Ligne 414-417** : Fichiers créés
- **Lignes 427-445** : Difficulté 1 - Socket instable
- **Lignes 447-458** : Difficulté 2 - Conflits checkpoint
- **Lignes 459-471** : Difficulté 3 - Score non monotone
- **Lignes 473-478** : Résultats (44 événements, 780 secondes)
- **Ligne 479-480** : Merge et commit

### Section 3: Découvertes Importantes (lignes 174-214)
- **Lignes 176-188** : nba-api vs API REST
- **Lignes 190-202** : Spark Window Functions
- **Lignes 204-214** : Typage PySpark

### Section 4: Évolution des Besoins (lignes 216-239)
- Itération 1: Simple (1 saison, JSON)
- Itération 2: Scalable (7 saisons, multi-threading)
- Itération 3: Analytics (20 transformations, Delta Lake)

### Section 5: Décisions Clés (lignes 241-263)
- Choix API (nba-api)
- Format stockage (Delta Lake)
- Nombre transformations (20)
- Partitionnement (saison + game_year)

### Section 6: Statistiques Projet (lignes 267-291)
- **Code**: ~1200 lignes, 4 fichiers, 20 fonctions, 6 formules
- **Données**: 7 saisons, ~8600 matchs, 5103 joueurs, 2-3 GB
- **Git**: 3 commits NBA-11, 1 branche active
- **JIRA**: 5 Epics, 26 Stories, 104 points, Sprint 1 66%

### Section 7: Problèmes en Cours (lignes 293-311)
- **Lignes 296-300** : PER complet (nécessite stats équipe)
- **Lignes 301-305** : Volume Playoffs (nulls possibles)
- **Lignes 306-310** : Tests performance (pas testé 7 saisons)

### Section 8: Leçons Apprises (lignes 313-334)
- **Technique**: Typage, Rate limit, Delta Lake, Window Functions, Git
- **Méthodologique**: Commencer simple, documenter, tester échantillon
- **Métier**: PER, Usage Rate, Pace, Back-to-back, Home/Away

### Section 9: Prochaines Étapes (lignes 336-354)
- **Immédiat**: Finaliser 7 saisons, valider stats, merge NBA-12
- **Court terme**: NBA-13 tests, NBA-31 ML, Exports BI
- **Moyen terme**: Dashboards, playoffs 2024-25, documentation

---

## 🔍 Recherche Rapide par Mot-clé

| Mot-clé | Fichier | Ligne | Contexte |
|---------|---------|-------|----------|
| **PER** | agent.md | 152 | Formule complète |
| **PER** | memoir.md | 120 | Implémentation uPER |
| **Delta Lake** | agent.md | 24 | Stack technique |
| **Delta Lake** | memoir.md | 148 | Architecture partitionnement |
| **Rate Limit** | agent.md | 229 | Problème API |
| **Rate Limit** | memoir.md | 99 | Solution retry |
| **Streaming** | NBA13_STREAMING.md | 1 | Architecture complète |
| **Streaming** | memoir.md | 404 | Journal NBA-13 |
| **Window Functions** | agent.md | 125 | Pattern Spark |
| **Window Functions** | memoir.md | 190 | Découverte |
| **nba-api** | agent.md | 36 | Dépendance |
| **nba-api** | memoir.md | 176 | Comparaison APIs |

---

## 🛠️ Maintenance de l'Index

### Quand mettre à jour cet index :
1. ✅ Après chaque nouveau ticket JIRA (NBA-XX)
2. ✅ Après ajout de section majeure (>20 lignes)
3. ✅ Après résolution de problème documenté
4. ✅ Quand les numéros de ligne changent significativement

### Comment mettre à jour :
```bash
# Générer stats fichiers
wc -l docs/agent.md docs/memoir.md docs/NBA13_STREAMING.md

# Vérifier les ancres
# Format: [texte](fichier.md#Lnuméro)
```

### Checklist mise à jour :
- [ ] Nombres de lignes à jour
- [ ] Nouvelles sections ajoutées
- [ ] Tickets JIRA mis à jour
- [ ] Tableau navigation par besoin à jour
- [ ] Index mots-clés complété

---

### Section 12: Root Cause Analysis - Données Physiques (lignes 1276-1340)
- **Lignes 1278-1285** : Problème 158 joueurs GOLD au lieu de 1,000+
- **Lignes 1287-1301** : Bug conversion unités (CSV déjà métrique)
- **Lignes 1303-1311** : Imputation jamais activée
- **Lignes 1313-1326** : Filtre SILVER trop strict
- **Lignes 1328-1336** : Solutions appliquées et résultats
- **Lignes 1338-1350** : Architecture Data Mesh état actuel

---

## 📊 Découvertes Techniques Importantes

### Problème: Conversion Unités (07/02/2026)
**Fichier**: `src/utils/transformations.py`

Données CSV déjà en cm/kg mal converties:
```python
height="218" (cm) → null ❌
weight="102" (kg) → 46 kg ❌ (traité comme lbs)
```

**Impact**: ~50 joueurs perdus

### Problème: Imputation Non Activée (07/02/2026)
**Fichier**: `src/processing/silver/players_silver.py`

Fonction `impute_missing_data()` existe mais **jamais appelée**.

**Impact**: ~3,000 joueurs sans données physiques

### Solution: Réduction Critères (07/02/2026)
**Fichier**: `configs/data_products.yaml`

Retirer `position` et `is_active` des champs requis SILVER.

**Résultat**: 158 → 635 joueurs (+301%)

---

## 🛠️ Maintenance de l'Index

### Quand mettre à jour cet index :
1. ✅ Après chaque nouveau ticket JIRA (NBA-XX)
2. ✅ Après ajout de section majeure (>20 lignes)
3. ✅ Après résolution de problème documenté
4. ✅ Quand les numéros de ligne changent significativement

### Comment mettre à jour :
```bash
# Générer stats fichiers
wc -l docs/agent.md docs/memoir.md docs/NBA13_STREAMING.md

# Vérifier les ancres
# Format: [texte](fichier.md#Lnuméro)
```

### Checklist mise à jour :
- [x] Nombres de lignes à jour
- [x] Nouvelles sections ajoutées (Root Cause Analysis)
- [x] Découvertes techniques documentées
- [x] Tableau navigation par besoin à jour
- [x] Index mots-clés complété
- [x] **Phase 4-7 documentées**
- [x] **5,103 joueurs GOLD validés**
- [x] **Architecture production documentée**

---

**Dernière mise à jour**: 2026-02-07 13:20
**Statut**: ✅ **PRODUCTION READY** - 5,103 joueurs GOLD Standard
**Version**: 5.0
