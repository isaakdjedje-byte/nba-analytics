---
# Index des Documentations NBA Analytics
# Dernière mise à jour: 2026-02-06 17:05 (NBA-15 terminé)
# Usage: Référence rapide pour éviter de lire les fichiers complets
---

# 📚 INDEX - Documentation NBA Analytics

## 🗺️ Vue d'ensemble des fichiers

| Fichier | Lignes | Contenu principal | Dernière MAJ |
|---------|--------|-------------------|--------------|
| [`agent.md`](agent.md) | 400+ | Documentation technique, architecture, commandes | 2026-02-06 |
| [`memoir.md`](memoir.md) | 550+ | Journal chronologique, leçons apprises | 2026-02-06 |
| [`API_INGESTION.md`](API_INGESTION.md) | ~350 | **Documentation API NBA (NBA-16)** | 2026-02-06 |
| [`INSTALLATION.md`](INSTALLATION.md) | ~300 | **Guide installation complète (NBA-16)** | 2026-02-06 |
| [`EXAMPLES.md`](EXAMPLES.md) | ~150 | **Exemples pratiques Python (NBA-16)** | 2026-02-06 |
| [`NBA15_SUMMARY.md`](NBA15_SUMMARY.md) | ~200 | Résumé NBA-15 | 2026-02-06 |
| [`NBA13_STREAMING.md`](NBA13_STREAMING.md) | ~100 | Détails streaming NBA-13 | 2026-02-06 |
| [`TESTING.md`](TESTING.md) | ~150 | Guide testing pytest + Docker | 2026-02-06 |
| [`PYTHON_VERSION_FIX.md`](PYTHON_VERSION_FIX.md) | ~50 | Fix Python 3.14 → 3.11 | 2026-02-06 |
| [`JIRA_BACKLOG.md`](JIRA_BACKLOG.md) | ~500 | **TOUS les tickets JIRA (NBA-11 à NBA-31)** | 2026-02-06 |
| [`stories/`](stories/) | 18 fichiers | **Stories détaillées NBA-14 à NBA-31** | 2026-02-06 |

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

### "Je veux les commandes Spark"
→ [`agent.md:317-350`](agent.md#L317) - Vérification données, tests rapides

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
| **NBA-17** | ⬜ To Do | Processing | 5 | Nettoyage données joueurs |
| **NBA-18** | ⬜ To Do | Processing | 5 | Métriques avancées (PER, TS%) |
| **NBA-19** | ⬜ To Do | Processing | 3 | Agrégations équipe/saison |
| **NBA-20** | ⬜ To Do | Processing | 5 | Transformation matchs |
| **NBA-21** | ⬜ To Do | Processing | 8 | Feature engineering ML |
| **NBA-22** | ⬜ To Do | ML | 8 | Prédiction résultats matchs |
| **NBA-23** | ⬜ To Do | ML | 5 | Clustering joueurs (K-Means) |
| **NBA-24** | ⬜ To Do | ML | 5 | Détection joueurs progression |
| **NBA-25** | ⬜ To Do | ML | 5 | Pipeline ML automatisé |
| **NBA-26** | ⬜ To Do | Quality | 5 | Tests unitaires |
| **NBA-27** | ⬜ To Do | Quality | 3 | Data Quality checks |
| **NBA-28** | ⬜ To Do | Quality | 5 | Monitoring et alerting |
| **NBA-29** | ⬜ To Do | Reporting | 3 | Export BI (Parquet/CSV) |
| **NBA-30** | ⬜ To Do | Reporting | 3 | Rapport hebdomadaire auto |
| **NBA-31** | ⬜ To Do | Reporting | 5 | Dashboard interactif |

**📊 Total : 31 tickets | 104 points | 37% complété**

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

**Dernière mise à jour**: 2026-02-06 17:05
**Prochaine révision**: Après NBA-17
