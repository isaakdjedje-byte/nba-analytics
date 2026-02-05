# 📖 MEMOIR - Journal du Projet NBA Analytics

**Projet :** NBA Analytics Platform  
**Début :** Février 2026  
**Dernière mise à jour :** 5 Février 2026  

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
- Configuration JIRA avec 5 Epics et 26 Stories
- Premier commit sur master

**Décisions :**
- Architecture Data Lake (Raw → Processed → Gold)
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

**Formule implémentée :**
```python
def calculate_uper(stats):
    # 15+ composantes avec ajustements assists, VOP, DRBP
    uper = (1/minutes) × [
        3PM×0.5 + FGM×ast_factor + (2/3)×team_ast +
        FTM×ft_factor - VOP×TOV - ...
    ]
    return uper

def calculate_per(uper, team_pace, league_pace):
    return uper × (league_pace/team_pace) × (15/15)
```

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

**Avantages :**
- Requête rapide : `WHERE season = '2023-24'`
- Ajout futures saisons : juste nouveau dossier
- Time travel possible : `VERSION AS OF`

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
- Export BI (Parquet)

**Pourquoi cette évolution ?**
- Découverte que nba-api permettait données historiques
- Ambition betting → besoin stats avancées
- Portfolio pro → démonstration Delta Lake

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

---

## 📊 STATISTIQUES PROJET

### Code
- **~1200 lignes** Python
- **4 fichiers** principaux
- **20 fonctions** de transformation
- **6 formules** NBA officielles

### Données
- **7 saisons** (2018-2024)
- **~8,600 matchs** (RS + Playoffs)
- **5103 joueurs** historiques
- **30 équipes** NBA
- **2-3 GB** estimé (Delta Lake)

### Git
- **3 commits** sur NBA-11
- **1 merge** dans master
- **1 branche** active (feature/NBA-12)

### JIRA
- **5 Epics** créés
- **26 Stories** définies
- **104 points** estimés
- **Sprint 1** : 66% complété (2/3 tickets)

---

## 🚨 PROBLÈMES EN COURS

### Problème 1 : Calcul PER complet
**Statut :** 🟡 Nécessite stats équipe détaillées
**Impact :** Valeurs estimées pour l'instant
**Solution envisagée :** Joindre table teams dans transformation

### Problème 2 : Volume données Playoffs
**Statut :** 🟡 Certaines saisons sans playoffs (en cours)
**Impact :** Union RS + PO peut créer nulls
**Solution :** `allowMissingColumns=True` dans union

### Problème 3 : Tests performance
**Statut :** ⬜ Pas encore testé avec 7 saisons complètes
**Risque :** Timeout si > 30 min
**Mitigation :** Partitionnement + checkpoints

---

## 🎓 LEÇONS APPRISES

### Technique
1. **Toujours caster les types** en PySpark (sinon chaos)
2. **Rate limit** : mieux vaut lent mais stable que rapide et bloqué
3. **Delta Lake** : game changer pour projets data sérieux
4. **Window Functions** : indispensable pour séries temporelles
5. **Git feature branches** : sauvegarde la santé mentale

### Méthodologique
1. **Commencer simple**, complexifier itérativement
2. **Documenter au fur et à mesure** (pas à la fin)
3. **Tester sur échantillon** avant full volume
4. **JIRA + Git** : combinaison puissante pour traçabilité

### Métier (NBA)
1. **PER** : meilleure métrique globale (mais complexe)
2. **Usage Rate** : qui porte l'attaque (crucial betting)
3. **Pace** : prédicteur clé du total points
4. **Back-to-back** : impact fatigue sous-estimé
5. **Home/Away** : avantage terrain significatif (~60/40)

---

## 🔮 PROCHAINES ÉTAPES

### Immédiat (Cette semaine)
- [ ] Finaliser fetch multi-saisons (7 saisons complètes)
- [ ] Exécuter batch_ingestion_v2 sur toutes les saisons
- [ ] Valider cohérence stats (PER 0-40, USG 0-100, etc.)
- [ ] Merge NBA-12 dans master

### Court terme (Semaine prochaine)
- [ ] Ticket NBA-13 : Tests unitaires + Data Quality
- [ ] Ticket NBA-31 : Premier modèle ML (Random Forest)
- [ ] Exports BI : Parquet vers Tableau/Power BI

### Moyen terme (Dans 2 semaines)
- [ ] Dashboard Jupyter avec visualisations
- [ ] Analyse prédictive pour playoffs 2024-25
- [ ] Documentation finale et présentation

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

---

**Prochaine mise à jour :** Après merge NBA-12  
**Auteur :** Agent/Data Engineer  
**Statut projet :** 🟡 En cours (65%)
