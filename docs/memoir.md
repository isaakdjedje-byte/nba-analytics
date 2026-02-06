# 📖 MEMOIR - Journal du Projet NBA Analytics

**Projet :** NBA Analytics Platform  
**Début :** Février 2026  
**Dernière mise à jour :** 6 Février 2026 (NBA-16 terminé)  
**Ticket actif :** NBA-17 - Nettoyage données joueurs

---

## 🎯 CONTEXTE INITIAL

### Pourquoi ce projet ?
Formation complète en Data Engineering avec un cas concret :
- Maîtriser Spark + Delta Lake
- Workflow Git professionnel
- Gestion projet Agile avec JIRA
- Créer un portfolio betting NBA

### Besoin métier
Analyser les données NBA pour :
- Identifier les tendances (forme, fatigue, matchups)
- Prédire les résultats de matchs
- Optimiser les paris sportifs (surtout playoffs)

---

## 📅 CHRONOLOGIE

### 05/02/2026 - Phase 0 : Setup
**Réalisations :**
- Création structure projet Git
- Installation PySpark, delta-spark, nba-api
- Configuration JIRA avec 5 Epics et 31 Stories
- Premier commit sur master

**Décisions :**
- Architecture Data Lake (Raw → Silver → Gold)
- 7 saisons : 2018-19 à 2024-25
- Workflow Git feature branch

---

### 05/02/2026 - Ticket NBA-11 : Data Ingestion V1
**Problème initial :** Quelle API choisir ?

**Options évaluées :**
1. SportsData.io → ❌ Scrambled data, payant
2. BallDontLie.io → ⚠️ Simple mais limité
3. nba-api → ✅ **Choisi** : Officiel, gratuit, complet

**Solution retenue :** `nba-api` (wrapper Python NBA.com)

**Code développé :**
- `fetch_nba_data.py` avec gestion d'erreurs
- Logging structuré
- Sauvegarde JSON avec métadonnées

**Résultats :**
- ✅ 5103 joueurs historiques
- ✅ 530 joueurs actifs
- ✅ 30 équipes
- ✅ Saison 2023-24 complète
- ✅ Stats LeBron James (exemple)
- ✅ Scoreboard live

**Merge :** PR créée et fusionnée dans master  
**Commit :** `NBA-11: Add NBA data ingestion with nba-api`

---

### 05/02/2026 - Ticket NBA-12 : Multi-Saisons & Transformations
**Problème :** Comment scaler à 7 saisons avec formules complexes ?

**Évolution des besoins :**
- Départ : Juste récupérer données
- Évolution : 20 transformations avec formules NBA officielles
- Raison : Pour betting, besoin de métriques avancées (PER, Usage, etc.)

**Architecture retenue :**
```
Fetch V2 (multi-saisons)
    ↓
JSON brut par saison (data/raw/2023_24/)
    ↓
Pipeline Spark (20 transformations)
    ↓
Delta Lake partitionné (data/processed/)
    ↓
Export Parquet (data/exports/)
```

**Formules NBA recherchées :**
- PER (Player Efficiency Rating) - Formule Hollinger complète
- Usage Rate (USG%) - Officiel NBA
- True Shooting % (TS%) - Facteur 0.44
- Pace (rythme) - Possessions/48min
- Game Score - Évaluation match
- Effective FG% - Ajustement 3pts

**Difficultés rencontrées :**

#### Difficulté 1 : Rate Limit
**Symptôme :** API bloque après ~100 requêtes rapides
**Messages :** `Timeout`, `Connection reset`

**Solutions testées :**
- ❌ Augmenter timeout → Insuffisant
- ✅ Délai 2s entre requêtes + retry exponentiel → **OK**

**Code solution :**
```python
def fetch_with_retry(func, *args, **kwargs):
    for attempt in range(RETRY):
        try:
            time.sleep(DELAY)  # 2s
            return func(*args, **kwargs)
        except:
            time.sleep(DELAY * (attempt + 1))  # 2s, 4s, 8s
```

#### Difficulté 2 : Formules PER complexes
**Symptôme :** PER nécessite stats équipe + ligue, pas juste joueur

**Analyse :**
- uPER (unadjusted) : calculable avec stats individuelles
- Ajustement pace : nécessite pace équipe vs ligue
- Normalisation : suppose moyenne ligue = 15

**Solutions :**
- Implémenter uPER complet avec toutes les composantes
- Utiliser valeurs moyennes ligue (100 possessions, 110 points)
- Marquer comme "estimate" dans la donnée

#### Difficulté 3 : Architecture Delta Lake
**Question :** Comment organiser 8600+ matchs sur 7 saisons ?

**Options :**
- ❌ Un seul fichier → Trop lourd, pas scalable
- ❌ Par équipe → 30 dossiers, complexe
- ✅ **Par saison + année** → 7 saisons × 2 ans max = logique

**Structure retenue :**
```
data/processed/games_enriched/
├── season=2018-19/
│   ├── game_year=2018/
│   └── game_year=2019/
├── season=2019-20/
...
└── season=2024-25/
    └── game_year=2024/
```

---

### 05/02/2026 - Ticket NBA-13 : Spark Streaming Box Score

**Problème :** Comment traiter les données en temps réel ?

**Architecture retenue (fichiers) :**
- Pipeline streaming avec dossiers uniques par exécution
- Simulateur avec synchronisation automatique
- Stockage Delta Lake avec checkpoint unique par run

**Configuration :**
- Intervalle : 30 secondes
- Timeout : 15 minutes
- Traitement : 13 minutes

**Résultats :**
- ✅ 21 box scores traités en temps réel
- ✅ 44 événements générés
- ✅ 780 secondes de traitement

**Difficultés rencontrées :**

#### Difficulté 1 : Socket instable
**Symptôme :** Connexions TCP perdues, scores manquants  
**Solution :** Architecture fichier avec synchronisation automatique

#### Difficulté 2 : Conflits Checkpoint
**Symptôme :** Erreurs "checkpoint already exists"  
**Solution :** Checkpoint unique par run avec timestamp

#### Difficulté 3 : Score non monotone
**Symptôme :** Scores qui peuvent diminuer (erreurs)  
**Solution :** Algorithme garantissant monotonie

**Merge :** PR #3 créée et fusionnée dans master  
**Commit :** `NBA-13: Spark Streaming Box Score avec architecture fichier`

---

### 06/02/2026 - Ticket NBA-14 : Gestion des Schémas Évolutifs

**Problème :** Comment gérer les changements de schéma sans casser les traitements ?

**Solution retenue :** Delta Lake avec MergeSchema + versioning

**Implémentation :**
- `src/utils/schema_manager.py` - Gestionnaire de schémas
- `src/utils/schema_config.yaml` - Configuration schémas
- `tests/test_schema_evolution.py` - 9 tests unitaires

**Features :**
- ✅ MergeSchema activé sur les écritures Delta
- ✅ Time travel pour versions historiques
- ✅ Documentation automatique des évolutions
- ✅ Tests de changement de schéma réussis

**Exemple d'utilisation :**
```python
# Écriture avec évolution schéma
df.write \
    .format("delta") \
    .option("mergeSchema", "true") \
    .mode("append") \
    .save("data/processed/games_enriched/")

# Lecture version historique
df_v1 = spark.read \
    .format("delta") \
    .option("versionAsOf", 0) \
    .load("data/processed/games_enriched/")
```

**Résultats :**
- ✅ 9/9 tests passants
- ✅ Schéma évolutif sans erreur
- ✅ Time travel fonctionnel
- ✅ Documentation `docs/schema_evolution.log` créée

**Merge :** PR créée et fusionnée dans master  
**Commit :** `NBA-14: Gestion des schémas évolutifs avec Delta Lake`

---

### 06/02/2026 - Ticket NBA-15 : Données Matchs et Équipes

**Objectif :** Compléter l'ingestion avec données complètes des matchs et équipes

**Réalisations :**
- ✅ 30 équipes NBA avec rosters complets (532 joueurs)
- ✅ Calendrier 2023-24 complet (2624 matchs : RS + Playoffs)
- ✅ Stats collectives (Wins/Losses/Win%)
- ✅ Box scores détaillés partitionnés par mois (8 fichiers)
- ✅ Système de checkpoints avec reprise d'exécution
- ✅ Barre de progression temps réel (tqdm)
- ✅ Tests unitaires et d'intégration (9/9 passés)

**Architecture mise en place :**
```
src/ingestion/
├── fetch_teams_rosters.py      # 30 équipes + rosters
├── fetch_schedules.py          # Calendriers
├── fetch_team_stats.py         # Stats collectives
├── fetch_boxscores.py          # Box scores par mois
└── nba15_orchestrator.py       # Orchestrateur complet

src/utils/
├── checkpoint_manager.py       # Gestion reprise
└── progress_tracker.py         # Progression

tests/
└── test_nba15_complete.py      # 9 tests
```

**Données créées :**
- `data/raw/teams/` : 30 équipes
- `data/raw/rosters/` : 532 joueurs (30 équipes × ~18 joueurs)
- `data/raw/schedules/` : 2624 matchs
- `data/raw/teams_stats/` : Stats collectives
- `data/raw/games_boxscores/` : 8 fichiers (par mois)
- `data/checkpoints/nba15/` : Progression sauvegardée

**Validation :**
```bash
pytest tests/test_nba15_complete.py -v
# 9 passed
```

**Exécution :**
```bash
# Orchestrateur complet avec reprise
python src/ingestion/nba15_orchestrator.py

# Depuis le début
python src/ingestion/nba15_orchestrator.py --from-scratch
```

**Temps d'exécution :**
- Équipes + Rosters : ~10 minutes
- Stats collectives : ~2 minutes
- Calendriers : ~2 minutes
- Box scores : ~20 minutes
- **Total : ~45 minutes** (avec rate limiting)

**Débloque :** NBA-17 (nettoyage), NBA-19 (agrégations), NBA-20 (transformation), NBA-22 (ML)

---

## 💡 DÉCOUVERTES IMPORTANTES

### Découverte 1 : nba-api vs API REST
**Avant nba-api :** Pensait devoir faire des requêtes HTTP manuelles
**Réalité :** nba-api encapsule tout avec classes Python

**Avantage :**
```python
# Avant (imaginé)
requests.get("https://nba.com/api/players")

# Après (réalité)
from nba_api.stats.static import players
players.get_players()  # Retourne liste directement
```

### Découverte 2 : Spark Window Functions
**Problème :** Calculer moyenne glissante sur 5 derniers matchs
**Solution :** Window Functions avec `rowsBetween`

```python
window_5 = (Window
    .partitionBy("team_id")
    .orderBy("game_date")
    .rowsBetween(-4, 0)
)

df.withColumn("avg_last_5", avg("points").over(window_5))
```

**Clé :** `rowsBetween(-4, 0)` = lignes -4 à 0 (5 matchs)

### Découverte 3 : Typage PySpark
**Erreur fréquente :** Oublier `.cast()` → colonne reste string
**Impact :** Calculs faux (ex: "100" + "200" = "100200" au lieu de 300)

**Solution systématique :**
```python
.withColumn("points", col("PTS").cast("int"))
.withColumn("fg_pct", col("FG_PCT").cast("double"))
```

### Découverte 4 : Checkpoints pour reprise (NBA-15)
**Problème :** Si l'ingestion s'interrompt après 30 min, tout est perdu
**Solution :** Checkpoints automatiques après chaque étape

```python
# Sauvegarde automatique
self.checkpoint.save_progress("teams_fetched", {
    "teams_count": len(teams),
    "timestamp": datetime.now().isoformat()
})

# Reprise possible
if self.checkpoint.is_step_completed("teams_fetched"):
    print("Étape déjà complétée, passage à la suivante...")
```

### Découverte 5 : Delta Lake MergeSchema (NBA-14)
**Problème :** Ajouter une colonne casse les traitements existants
**Solution :** Option `mergeSchema` de Delta Lake

```python
# Nouvelle colonne ajoutée sans casser l'existant
df.write \
    .format("delta") \
    .option("mergeSchema", "true") \
    .mode("append") \
    .save("data/processed/games_enriched/")
```

---

## 🔄 ÉVOLUTION DES BESOINS

### Itération 1 : Simple
- Récupérer quelques matchs
- JSON simple
- 1 saison

### Itération 2 : Scalable
- 7 saisons complètes
- Multi-threading/rate limit
- Structure organisée

### Itération 3 : Analytics
- 20 transformations
- Formules NBA officielles
- Delta Lake partitionné
- Schémas évolutifs (NBA-14)
- Données complètes (NBA-15)

### Itération 4 : Documentation (NBA-16)
- Documentation API complète
- Guide d'installation
- Exemples pratiques
- README mis à jour

**Pourquoi cette évolution ?**
- Découverte que nba-api permettait données historiques
- Ambition betting → besoin stats avancées
- Portfolio pro → démonstration Delta Lake
- Partage projet → documentation complète nécessaire

---

## 🎯 DÉCISIONS CLÉS

### Décision 1 : Choix API
**Options :** SportsData.io vs BallDontLie vs nba-api
**Critères :** Coût, qualité données, facilité
**Choix :** nba-api (gratuit, officiel, bien documenté)

### Décision 2 : Format Stockage
**Options :** CSV vs Parquet vs Delta Lake
**Choix :** Delta Lake pour processed (ACID, versioning)
**Alternative :** Parquet pour exports (interopérabilité BI)

### Décision 3 : Nombre de Transformations
**Départ :** 5 transformations simples
**Évolution :** 20 transformations (5 groupes × 4)
**Raison :** Couvrir tous les aspects (fondation, forme, stats, contexte)

### Décision 4 : Partitionnement
**Options :** Par équipe vs par saison vs par date
**Choix :** `partitionBy("season", "game_year")`
**Justification :** Requêtes temps-séries naturelles

### Décision 5 : Architecture Streaming (NBA-13)
**Options :** Socket TCP vs Architecture fichier
**Choix :** Architecture fichier avec synchronisation
**Raison :** Plus stable, reproductible, testable

### Décision 6 : Gestion Schémas (NBA-14)
**Options :** Schéma fixe vs évolutif
**Choix :** Schémas évolutifs avec MergeSchema
**Raison :** Flexibilité pour futures métriques

### Décision 7 : Orchestrateur (NBA-15)
**Options :** Scripts séparés vs orchestrateur unifié
**Choix :** Orchestrateur `nba15_orchestrator.py` avec checkpoints
**Raison :** Reprise possible, progression visible, gestion erreurs centralisée

---

## 📊 STATISTIQUES PROJET

### Code
- **~3350 lignes** Python (+2153 avec NBA-15)
- **14 fichiers** principaux (+10 avec NBA-15)
- **20 fonctions** de transformation
- **6 formules** NBA officielles
- **9 tests** unitaires et intégration (NBA-15)
- **9 tests** schémas évolutifs (NBA-14)

### Données
- **Saison 2023-24** : Complète
- **30 équipes** NBA avec rosters complets (532 joueurs actifs)
- **2624 matchs** détaillés (RS + Playoffs)
- **~8,600 matchs** estimés (7 saisons - NBA-12)
- **5103 joueurs** historiques
- **2-3 GB** estimé (Delta Lake)

### Git
- **3 commits** sur NBA-11
- **1 commit** NBA-12 (multi-saisons)
- **1 commit** NBA-13 (streaming)
- **1 commit** NBA-14 (schémas)
- **1 commit** NBA-15 (données complètes)
- **5 merges** dans master
- **5 tickets** complétés (NBA-11 à NBA-15)

### JIRA
- **5 Epics** créés
- **31 Stories** définies
- **104 points** estimés
- **Sprint 1** : 100% complété (NBA-11, NBA-12, NBA-13, NBA-14, NBA-15)
- **37% projet** complété (5/14 tickets)

---

## 🚨 PROBLÈMES RÉSOLUS

### ✅ Problème 1 : Calcul PER complet
**Statut :** **RÉSOLU** (NBA-15 a récupéré les stats équipes)
**Solution :** Données disponibles dans `data/raw/teams_stats/` et `data/raw/games_boxscores/`
**Prochaine étape :** Implémenter le calcul dans NBA-18

### ✅ Problème 2 : Volume données Playoffs
**Statut :** **RÉSOLU** (NBA-15 récupère RS + Playoffs)
**Solution :** 2624 matchs récupérés (1230 RS + playoffs)

### 🟡 Problème 3 : Tests performance
**Statut :** ⬜ Pas encore testé avec 7 saisons complètes
**Risque :** Timeout si > 30 min
**Mitigation :** Partitionnement + checkpoints

### ✅ Problème 4 : Rate Limiting
**Statut :** **RÉSOLU** (NBA-15 avec retry + backoff)
**Solution :** Délai 2s + retry exponentiel + checkpoints

### ✅ Problème 5 : Schémas évolutifs
**Statut :** **RÉSOLU** (NBA-14 avec MergeSchema)
**Solution :** Delta Lake avec versioning et time travel

---

## 🎓 LEÇONS APPRISES

### Technique
1. **Toujours caster les types** en PySpark (sinon chaos)
2. **Rate limit** : mieux vaut lent mais stable que rapide et bloqué
3. **Delta Lake** : game changer pour projets data sérieux
4. **Window Functions** : indispensable pour séries temporelles
5. **Git feature branches** : sauvegarde la santé mentale
6. **Checkpoints** : essentiels pour ingestion longue (NBA-15)
7. **MergeSchema** : flexibilité sans compromettre stabilité (NBA-14)

### Méthodologique
1. **Commencer simple**, complexifier itérativement
2. **Documenter au fur et à mesure** (pas à la fin)
3. **Tester sur échantillon** avant full volume
4. **JIRA + Git** : combinaison puissante pour traçabilité
5. **Checkpoints fréquents** : sauvegarde progression (NBA-15)

### Métier (NBA)
1. **PER** : meilleure métrique globale (mais complexe)
2. **Usage Rate** : qui porte l'attaque (crucial betting)
3. **Pace** : prédicteur clé du total points
4. **Back-to-back** : impact fatigue sous-estimé
5. **Home/Away** : avantage terrain significatif (~60/40)
6. **Box scores** : données les plus riches pour analyse (NBA-15)

---

## 🔮 PROCHAINES ÉTAPES

### Immédiat (Aujourd'hui)
- [ ] **NBA-16** : Documentation API complète
  - [ ] `docs/API_INGESTION.md`
  - [ ] `docs/INSTALLATION.md`
  - [ ] `docs/EXAMPLES.md`
  - [ ] Mise à jour `README.md`

### Court terme (Cette semaine)
- [ ] NBA-17 : Nettoyage des données (suppression doublons, gestion nulls)
- [ ] NBA-18 : Calcul métriques avancées (PER, TS%, USG%)
- [ ] NBA-19 : Agrégations par équipe et saison
- [ ] NBA-20 : Transformation des données matchs

### Moyen terme (Semaine prochaine)
- [ ] NBA-21 : Feature engineering pour ML
- [ ] NBA-22 : Premier modèle ML (Random Forest)
- [ ] NBA-31 : Dashboard et visualisations

---

## 💬 CONVERSATIONS IMPORTANTES

### "Pourquoi pas SportsData.io ?"
**Q :** SportsData.io semble plus pro, pourquoi ne pas l'utiliser ?
**R :** Données scrambled (illisibles), payant après essai, overkill pour apprentissage. nba-api = gratuit + officiel + simple.

### "20 transformations c'est pas trop ?"
**Q :** Est-ce qu'on ne simplifie pas à 5-10 transformations ?
**R :** Non, car pour betting il faut : fondations (5) + forme (5) + stats avancées (6) + contexte (4). Chaque groupe a sa valeur.

### "Pourquoi Delta Lake et pas juste Parquet ?"
**Q :** Parquet suffit non ? Pourquoi ajouter complexité Delta ?
**R :** ACID transactions (pas de corruption), time travel (rollback possible), versioning schéma (évolution données). Indispensable pour production.

### "Pourquoi un orchestrateur NBA-15 ?"
**Q :** Pourquoi pas juste lancer les scripts séparément ?
**R :** Orchestrateur = progression visible, reprise automatique, gestion erreurs centralisée, 45 min d'exécution gérées proprement.

### "Comment gérer les calculs qui nécessitent données futures ?"
**Q :** Ex: moyenne mobile 5 matchs, mais match 1 n'a pas d'historique ?
**R :** Window Functions gèrent ça : matchs 1-4 ont moyenne sur disponible (1-4 matchs), puis standard à partir match 5.

---

## 📚 RESSOURCES DÉCOUVERTES

### Documentation clé
- **nba-api GitHub** : https://github.com/swar/nba_api
- **Delta Lake docs** : https://docs.delta.io/latest/quick-start.html
- **Spark Window Functions** : https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-window.html
- **PER explanation** : https://www.basketball-reference.com/about/per.html

### Articles utiles
- "NBA Advanced Stats Glossary" (NBA.com)
- "Understanding Usage Rate in Basketball"
- "Delta Lake vs Parquet : When to use what"
- "Spark Streaming Best Practices"

### Documentation Projet
- [`agent.md`](agent.md) - Documentation technique
- [`INDEX.md`](INDEX.md) - Navigation rapide
- [`JIRA_BACKLOG.md`](JIRA_BACKLOG.md) - Tous les tickets
- [`stories/`](stories/) - Stories détaillées NBA-14 à NBA-31

---

## ✅ CHECKPOINTS VALIDÉS

- [x] Setup environnement complet
- [x] Connexion API fonctionnelle
- [x] Ingestion première saison réussie
- [x] Architecture Delta Lake définie
- [x] 20 transformations spécifiées
- [x] Formules NBA codées
- [x] Workflow Git/JIRA opérationnel
- [x] Documentation agent/memoir créée
- [x] NBA-13 : Spark Streaming terminé
- [x] NBA-14 : Schémas évolutifs fonctionnels
- [x] **NBA-15 terminé** : 30 équipes, 532 joueurs, 2624 matchs récupérés

---

**Dernière mise à jour :** 06/02/2026 (NBA-16 terminé, NBA-17 en cours)
**Auteur :** Agent/Data Engineer
**Statut projet :** 🟢 En cours (40% - 6/15 tickets terminés)
**Ticket actif :** NBA-17 - Nettoyage données joueurs

---

## ✅ NBA-16 TERMINÉ - Documentation API

**Date de complétion :** 06/02/2026
**Points :** 2
**Statut :** ✅ Terminé

### Livrables créés

1. **`docs/API_INGESTION.md`** (14KB)
   - Vue d'ensemble architecture
   - 9 endpoints documentés avec table complète
   - Rate limiting (1000 req/heure)
   - Gestion des erreurs avec retry exponentiel
   - Optimisations (cache, pagination)

2. **`docs/INSTALLATION.md`** (12KB)
   - Prérequis système complets
   - Installation étape par étape (Windows/Mac/Linux)
   - Configuration Docker
   - Section dépannage avec 8 erreurs courantes
   - Vérification post-installation

3. **`docs/EXAMPLES.md`** (4KB)
   - 6 exemples Python pratiques
   - Récupération stats LeBron James
   - Analyse saison complète
   - Comparaison Lakers vs Warriors
   - Pipeline Spark + Delta Lake
   - Recherche avancée matchs
   - Analyse de roster

4. **`README.md` mis à jour**
   - Nouvelle section Documentation
   - Architecture avec nba-api
   - Structure projet complète

### Métriques
- **Lignes de documentation :** ~800 lignes
- **Fichiers créés :** 3
- **Fichiers modifiés :** 2 (README.md, INDEX.md)
- **Temps estimé :** 45 minutes

### Prochaine étape
→ **NBA-17** : Nettoyage données joueurs
