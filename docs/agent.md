# 🤖 AGENT DOCUMENTATION - NBA Analytics Platform

**Projet :** NBA Analytics Platform  
**Dernière mise à jour :** 6 Février 2026  
**Version :** 2.0 (Post NBA-15)  
**Ticket en cours :** NBA-16 - Documentation API

---

## 📋 VUE D'ENSEMBLE

Pipeline Data Engineering complet pour l'analyse de données NBA, combinant Apache Spark, Delta Lake, Git professionnel et JIRA Agile. Le projet couvre l'ingestion multi-saisons (2018-2024) avec 20 transformations avancées incluant les formules officielles NBA (PER, Usage Rate, True Shooting %).

### Objectifs
- Architecture Data Lake moderne (Raw → Silver → Gold)
- Ingestion multi-saisons via API NBA officielle
- 20 métriques avancées avec formules officielles
- Workflow Git/JIRA professionnel
- Scalable pour futures saisons et betting analytics

### Statut Global
- **Tickets complétés :** NBA-11 à NBA-15 (5/14)
- **Progression :** 37% (5 tickets sur 14)
- **Données :** 30 équipes, 532 joueurs, 2624 matchs récupérés

---

## 🏗️ ARCHITECTURE

### Stack Technique
```
┌─────────────────────────────────────────────┐
│  PRÉSENTATION                               │
│  - GitHub (versioning, PR, code review)    │
│  - JIRA Agile (Epics, Stories, Sprints)    │
│  - Documentation Markdown                  │
└─────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────┐
│  PROCESSING                                 │
│  - Apache Spark 3.5 (PySpark)              │
│  - Delta Lake 3.0 (transactions ACID)      │
│  - Python 3.11 + nba-api 1.1.11            │
│  - Schémas évolutifs (MergeSchema)         │
└─────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────┐
│  STOCKAGE                                   │
│  - Delta Lake (data/processed/)            │
│  - JSON brut (data/raw/{type}/)            │
│  - Checkpoints (data/checkpoints/)         │
│  - Parquet (data/exports/) - Futur         │
└─────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────┐
│  SOURCES                                    │
│  - nba-api (NBA.com officiel)              │
│  - Saison 2023-24 complète                 │
│  - 30 équipes, 532 joueurs, 2624 matchs    │
└─────────────────────────────────────────────┘
```

### Structure des Données
```
nba-analytics/
├── src/
│   ├── ingestion/
│   │   ├── fetch_nba_data.py          ✓ (V1 - NBA-11)
│   │   ├── fetch_nba_data_v2.py       ✓ (Multi-saisons - NBA-12)
│   │   ├── fetch_teams_rosters.py     ✓ (NBA-15)
│   │   ├── fetch_schedules.py         ✓ (NBA-15)
│   │   ├── fetch_team_stats.py        ✓ (NBA-15)
│   │   ├── fetch_boxscores.py         ✓ (NBA-15)
│   │   └── nba15_orchestrator.py      ✓ (NBA-15)
│   ├── processing/
│   │   └── batch_ingestion_v2.py      ✓ (20 transfo - NBA-12)
│   ├── utils/
│   │   ├── nba_formulas.py            ✓ (Formules officielles)
│   │   ├── transformations.py         ✓ (20 transfo)
│   │   ├── checkpoint_manager.py      ✓ (NBA-15)
│   │   ├── progress_tracker.py        ✓ (NBA-15)
│   │   ├── schema_manager.py          ✓ (NBA-14)
│   │   └── schema_config.yaml         ✓ (NBA-14)
│   └── config/
│       └── seasons_config.yaml        ✓ (7 saisons)
├── data/
│   ├── raw/                           ✓ (NBA-15 complet)
│   │   ├── teams/                     ✓ (30 équipes)
│   │   ├── rosters/                   ✓ (532 joueurs)
│   │   ├── schedules/                 ✓ (2624 matchs)
│   │   ├── teams_stats/               ✓ (Stats collectives)
│   │   └── games_boxscores/           ✓ (Par mois)
│   ├── processed/                     ✓ (Delta Lake - NBA-12)
│   └── checkpoints/                   ✓ (NBA-15)
├── tests/
│   ├── test_schema_evolution.py       ✓ (NBA-14)
│   └── test_nba15_complete.py         ✓ (NBA-15)
└── docs/
    ├── agent.md                       ✓ (Ce fichier)
    ├── memoir.md                      ✓ (Journal)
    ├── INDEX.md                       ✓ (Navigation)
    ├── JIRA_BACKLOG.md                ✓ (Tous les tickets)
    ├── API_INGESTION.md               ⬜ (NBA-16 - À créer)
    ├── INSTALLATION.md                ⬜ (NBA-16 - À créer)
    └── EXAMPLES.md                    ⬜ (NBA-16 - À créer)
```

---

## 📦 CONFIGURATION REQUISE

### Dépendances Python
```bash
pip install pyspark==3.5.0
pip install delta-spark==3.0.0
pip install nba-api==1.1.11
pip install pyyaml
pip install requests
pip install tqdm          # Pour barre de progression NBA-15
```

### Variables d'environnement
```bash
export SPARK_HOME=/path/to/spark
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
```

### Prérequis système
- Python 3.11+ (Python 3.14 non supporté)
- Java 11+ (pour Spark)
- 4GB RAM minimum
- 10GB espace disque
- Git

---

## 🔧 CONVENTIONS DE CODE

### Nommage
- **Fichiers** : `snake_case.py` (fetch_nba_data.py)
- **Branches Git** : `feature/NBA-XX-description`
- **Fonctions** : `snake_case` avec type hints
- **Classes** : `PascalCase`
- **Constantes** : `UPPER_CASE`

### Structure des Commits
```
NBA-XX: Description courte

- Détail 1
- Détail 2

JIRA: NBA-XX
```

### Patterns Spark
```python
# Utiliser .transform() pour chaîner
df = (df
    .transform(apply_foundation)
    .transform(apply_form)
    .transform(apply_advanced)
)

# Window Functions pour calculs glissants
window = Window.partitionBy("team_id").orderBy("game_date")
window_5 = window.rowsBetween(-4, 0)

# MergeSchema pour évolution schéma (NBA-14)
df.write \
    .format("delta") \
    .option("mergeSchema", "true") \
    .mode("append") \
    .save("data/processed/games_enriched/")
```

---

## 📊 DONNÉES & FORMULES

### Saisons Couvertes
- **2023-24** : 2624 matchs (RS + Playoffs) ✅ NBA-15
- **2018-19 à 2024-25** : 7 saisons (NBA-12)

### Données Récupérées (NBA-15)
- **30 équipes** NBA avec informations complètes
- **532 joueurs** actifs (rosters 2023-24)
- **2624 matchs** (1230 RS + playoffs)
- **Box scores détaillés** partitionnés par mois
- **Stats collectives** Wins/Losses/Win%

### Formules NBA Officielles Implémentées

#### 1. PER (Player Efficiency Rating)
```python
uPER = (1/minutes) × [
    3PM×0.5 + FGM×(2-team_ast/team_FGM) + (2/3)×team_ast +
    FTM×0.5×(1+(1-team_ast/team_FGM)+(2/3)×team_ast/team_FGM) -
    VOP×TOV - VOP×DRBP×(FGA-FGM) - VOP×0.44×(0.44+0.56×DRBP)×(FTA-FTM) +
    VOP×(1-DRBP)×(REB-OREB) + VOP×DRBP×OREB + VOP×STL + VOP×DRBP×BLK -
    PF×((lgFT/lgPF) - 0.44×(lgFTA/lgPF)×VOP)
]

PER = uPER × (lgPace/tmPace) × (15/lgAvgPER)
```

#### 2. Usage Rate (USG%)
```python
USG% = 100 × ((FGA + 0.44×FTA + TOV) × (TmMP/5)) / 
       (MP × (TmFGA + 0.44×TmFTA + TmTOV))
```

#### 3. True Shooting % (TS%)
```python
TS% = PTS / (2 × (FGA + 0.44 × FTA))
```

#### 4. Pace
```python
Pace = 48 × ((TmPoss + OppPoss) / (2 × (TmMP/5)))
Possessions = FGA - OREB + TOV + 0.44 × FTA
```

#### 5. Effective FG% (eFG%)
```python
eFG% = (FGM + 0.5 × 3PM) / FGA
```

#### 6. Game Score
```python
GameScore = PTS + 0.4×FGM - 0.7×FGA - 0.4×(FTA-FTM) + 
            0.7×OREB + 0.3×DREB + STL + 0.7×AST + 0.7×BLK - 0.4×PF - TOV
```

---

## 🎯 TRANSFORMATIONS (20)

### Groupe 1 : Fondations (5)
1. **Typage strict** : Cast explicite (int, float, bool)
2. **Gestion nulls** : `fillna()` avec valeurs par défaut
3. **Timestamps** : `current_timestamp()` pour audit
4. **Déduplication** : `dropDuplicates(["game_id", "team_id"])`
5. **Partitionnement** : `partitionBy("season", "game_year")`

### Groupe 2 : Forme (5)
6. **Moyenne mobile 5 matchs** : `avg().over(Window.rowsBetween(-4, 0))`
7. **Tendance vs saison** : Différence moyennes glissantes
8. **Jours de repos** : `datediff()` avec match précédent
9. **Back-to-back flag** : Boolean si `days_rest == 0`
10. **Face-à-face historique** : Jointure avec historique H2H

### Groupe 3 : Stats Avancées (6)
11. **True Shooting %** : Formule officielle NBA
12. **Effective FG%** : Ajustement paniers 3pts
13. **Game Score** : Évaluation match Hollinger
14. **Efficacité fatigue** : Multiplicateur selon repos
15. **PER** : Formule complète avec ajustements
16. **Usage Rate** : % possessions utilisées

### Groupe 4 : Contexte (4)
17. **Classement** : Win % cumulé par équipe/saison
18. **Record H/A** : Wins/Losses domicile vs extérieur
19. **Marge points** : Différence score absolue
20. **Importance match** : Algo basé sur classement + dates

---

## 🐛 PROBLÈMES RENCONTRÉS & SOLUTIONS

### Problème 1 : Rate Limit API
**Symptôme :** 429 Too Many Requests après ~100 appels  
**Solution :** 
- Délai 2 secondes entre requêtes
- Retry avec backoff exponentiel (2s, 4s, 8s)
- Limite à 1000 requêtes/heure
- Checkpoints pour reprise (NBA-15)

### Problème 2 : Scrambled Data (SportsData.io)
**Symptôme :** Données encodées illisibles  
**Solution :** Migration vers `nba-api` (NBA.com officiel)

### Problème 3 : Formules PER Complexes
**Symptôme :** Nécessite stats équipe + ligue  
**Solution :** Décomposition en uPER + ajustements pace  
**Résolu :** NBA-15 a récupéré les stats équipes détaillées

### Problème 4 : Multi-saisons Volumétrie
**Symptôme :** Timeout sur gros volumes  
**Solution :** Partitionnement Delta Lake + écriture incrémentale

### Problème 5 : Git LF/CRLF
**Symptôme :** Warning Windows sur line endings  
**Solution :** Accepté (non bloquant), config Git locale si besoin

### Problème 6 : Streaming Socket instable (NBA-13)
**Symptôme :** Connexions TCP perdues, scores manquants  
**Solution :** Architecture fichier avec synchronisation

### Problème 7 : Conflits Checkpoint Spark (NBA-13)
**Symptôme :** Erreurs "checkpoint already exists"  
**Solution :** Checkpoint unique par run avec timestamp

### Problème 8 : Schéma évolutif (NBA-14)
**Symptôme :** Ajout colonnes casse les traitements existants  
**Solution :** MergeSchema Delta Lake + versioning schémas

---

## 🚀 WORKFLOW GIT

### Créer une feature
```bash
git checkout master
git pull origin master
git checkout -b feature/NBA-XX-description
```

### Commit & Push
```bash
git add .
git commit -m "NBA-XX: Description

- Détail 1
- Détail 2

JIRA: NBA-XX"
git push origin feature/NBA-XX-description
```

### Pull Request
1. Créer PR sur GitHub
2. Titre : `NBA-XX: Description`
3. Description détaillée avec checklist
4. Merger dans `master`
5. Supprimer branche feature

---

## 📈 JIRA WORKFLOW

### Structure
- **5 Epics** : Data Ingestion, Processing, ML, Quality, Reporting
- **31 Stories** : Total 104 story points
- **Sprint 1** : NBA-11 ✅, NBA-12 ✅, NBA-13 ✅, NBA-14 ✅, NBA-15 ✅ (100%)

### Statuts
- **To Do** → **In Progress** → **In Review** → **Done**
- Lier chaque commit au ticket (message `NBA-XX: ...`)
- Mettre à jour commentaires JIRA après merge

### Tickets Complétés (5/14)
| Ticket | Description | Points |
|--------|-------------|--------|
| NBA-11 | Connexion API nba-api | 5 |
| NBA-12 | Pipeline multi-saisons + 20 transformations | 8 |
| NBA-13 | Spark Streaming Box Score | 5 |
| NBA-14 | Gestion schémas évolutifs | 5 |
| NBA-15 | Données matchs et équipes | 3 |

### Prochains Tickets
- **NBA-16** (En cours) : Documentation API
- **NBA-17** : Nettoyage données
- **NBA-18** : Métriques avancées

---

## 🔍 COMMANDES UTILES

### Exécution NBA-15 (Orchestrateur)
```bash
# Exécution complète avec reprise
python src/ingestion/nba15_orchestrator.py

# Depuis le début
python src/ingestion/nba15_orchestrator.py --from-scratch

# Mode verbose
python src/ingestion/nba15_orchestrator.py --verbose
```

### Module par Module
```bash
# 1. Équipes et Rosters (~10 min)
python src/ingestion/fetch_teams_rosters.py

# 2. Stats Collectives (~2 min)
python src/ingestion/fetch_team_stats.py

# 3. Calendriers (~2 min)
python src/ingestion/fetch_schedules.py

# 4. Box Scores (~20 min)
python src/ingestion/fetch_boxscores.py
```

### Tests
```bash
# Tests NBA-15
pytest tests/test_nba15_complete.py -v

# Tests NBA-14
pytest tests/test_schema_evolution.py -v

# Avec couverture
pytest tests/ --cov=src --cov-report=html
```

### Vérifier données
```bash
# Lister fichiers générés
ls -lh data/raw/*/
ls -lh data/processed/

# Vérifier Delta Lake
python -c "
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()
df = spark.read.format('delta').load('data/processed/games_enriched')
print(f'Records: {df.count()}')
df.printSchema()
"

# Historique schémas (NBA-14)
python -c "
from delta import DeltaTable
dt = DeltaTable.forPath(spark, 'data/processed/games_enriched/')
dt.history().show()
"
```

### Vérification Checkpoint NBA-15
```bash
cat data/checkpoints/nba15/progress.json
```

---

## 📚 RESSOURCES

### Documentation Projet
- [`memoir.md`](memoir.md) - Journal chronologique complet
- [`INDEX.md`](INDEX.md) - Navigation rapide
- [`JIRA_BACKLOG.md`](JIRA_BACKLOG.md) - Tous les tickets détaillés
- [`stories/`](stories/) - Stories NBA-14 à NBA-31

### Documentation Externe
- nba-api : https://github.com/swar/nba_api
- Delta Lake : https://docs.delta.io/
- Spark SQL : https://spark.apache.org/docs/latest/sql-ref.html

### Formules NBA
- PER : https://www.basketball-reference.com/about/per.html
- Advanced Stats : https://www.nba.com/stats/help/glossary

---

## ✅ CHECKLIST AGENT

Avant de travailler sur ce projet :
- [ ] Lire `memoir.md` pour contexte historique
- [ ] Vérifier branche Git actuelle (`git branch`)
- [ ] Lire ticket JIRA actif (NBA-16 en cours)
- [ ] Vérifier espace disque (2-3 GB libres)
- [ ] Tester connexion internet (nécessaire pour fetch)
- [ ] Vérifier installations (`pip list | grep -E "pyspark|delta|nba"`)
- [ ] Consulter `INDEX.md` pour navigation rapide

---

## 🎯 ROADMAP IMMÉDIAT

### NBA-16 (En cours)
Créer la documentation technique complète :
- [ ] `docs/API_INGESTION.md` - Documentation API
- [ ] `docs/INSTALLATION.md` - Guide installation
- [ ] `docs/EXAMPLES.md` - Exemples pratiques
- [ ] Mettre à jour `README.md`

### Prochains Tickets (À venir)
- **NBA-17** : Nettoyage données (suppression doublons, nulls)
- **NBA-18** : Calcul métriques avancées (PER, TS%, USG%)
- **NBA-19** : Agrégations par équipe/saison
- **NBA-20** : Transformation des données matchs

---

**Dernière mise à jour :** 06/02/2026 (NBA-15 terminé)  
**Prochaine révision :** Après NBA-16  
**Version :** 2.0
