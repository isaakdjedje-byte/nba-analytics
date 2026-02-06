# 🤖 AGENT DOCUMENTATION - NBA Analytics Platform

**Projet :** NBA Analytics Platform  
**Dernière mise à jour :** 5 Février 2026  
**Version :** 1.0  

---

## 📋 VUE D'ENSEMBLE

Pipeline Data Engineering complet pour l'analyse de données NBA, combinant Apache Spark, Delta Lake, Git professionnel et JIRA Agile. Le projet couvre l'ingestion multi-saisons (2018-2024) avec 20 transformations avancées incluant les formules officielles NBA (PER, Usage Rate, True Shooting %).

### Objectifs
- Architecture Data Lake moderne (Raw → Processed → Gold)
- Ingestion multi-saisons via API NBA officielle
- 20 métriques avancées avec formules officielles
- Workflow Git/JIRA professionnel
- Scalable pour futures saisons et betting analytics

---

## 🏗️ ARCHITECTURE

### Stack Technique
```
┌─────────────────────────────────────────────┐
│  PRÉSENTATION                               │
│  - GitHub (versioning, PR, code review)    │
│  - JIRA Agile (Epics, Stories, Sprints)    │
└─────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────┐
│  PROCESSING                                 │
│  - Apache Spark 3.5 (PySpark)              │
│  - Delta Lake 3.0 (transactions ACID)      │
│  - Python 3.11 + nba-api 1.1.11            │
└─────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────┐
│  STOCKAGE                                   │
│  - Delta Lake (data/processed/)            │
│  - Parquet (data/exports/)                 │
│  - JSON brut (data/raw/{season}/)          │
└─────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────┐
│  SOURCES                                    │
│  - nba-api (NBA.com officiel)              │
│  - 7 saisons : 2018-19 à 2024-25           │
│  - 5103 joueurs, 30 équipes, ~8600 matchs  │
└─────────────────────────────────────────────┘
```

### Structure des Données
```
nba-analytics/
├── src/
│   ├── ingestion/
│   │   ├── fetch_nba_data.py          ✓ (V1 - NBA-11 MERGED)
│   │   ├── fetch_nba_data_v2.py       🟡 (Multi-saisons - En cours)
│   │   └── batch_ingestion_v2.py      🟡 (20 transformations - Dev)
│   ├── processing/
│   ├── utils/
│   │   ├── nba_formulas.py            🟡 (Formules officielles)
│   │   └── transformations.py         🟡 (20 transfo)
│   └── config/
│       └── seasons_config.yaml        ✓ (7 saisons)
├── data/
│   ├── raw/{season}/                  ✓ (JSON)
│   ├── processed/                     🟡 (Delta Lake)
│   └── exports/                       ⬜ (Parquet/CSV)
└── docs/
    ├── agent.md                       ✓ (Ce fichier)
    └── memoir.md                      ✓ (Journal)
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
```

### Variables d'environnement
```bash
export SPARK_HOME=/path/to/spark
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
```

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
```

---

## 📊 DONNÉES & FORMULES

### Saisons Couvertes
- **2018-19** : 1230 matchs (RS) + Playoffs
- **2019-20** : Saison raccourcie (bulle COVID)
- **2020-21** : 72 matchs (RS)
- **2021-22** : 1230 matchs (RS)
- **2022-23** : 1230 matchs (RS)
- **2023-24** : 1230 matchs (RS)
- **2024-25** : En cours (saison actuelle)

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

### Problème 2 : Scrambled Data (SportsData.io)
**Symptôme :** Données encodées illisibles
**Solution :** Migration vers `nba-api` (NBA.com officiel)

### Problème 3 : Formules PER Complexes
**Symptôme :** Nécessite stats équipe + ligue
**Solution :** Décomposition en uPER + ajustements pace

### Problème 4 : Multi-saisons Volumétrie
**Symptôme :** Timeout sur gros volumes
**Solution :** Partitionnement Delta Lake + écriture incrémentale

### Problème 5 : Git LF/CRLF
**Symptôme :** Warning Windows sur line endings
**Solution :** Accepté (non bloquant), config Git locale si besoin

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
- **26 Stories** : Total 104 story points
- **Sprint 1** : NBA-11 (✓ Done), NBA-12 (🟡 In Progress), NBA-13 (⬜ Todo)

### Statuts
- **To Do** → **In Progress** → **In Review** → **Done**
- Lier chaque commit au ticket (message `NBA-XX: ...`)
- Mettre à jour commentaires JIRA après merge

---

## 🔍 COMMANDES UTILES

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
```

### Tests rapides
```bash
# Test fetch
python src/ingestion/fetch_nba_data_v2.py

# Test transformations
python src/ingestion/batch_ingestion_v2.py
```

---

## 📚 RESSOURCES

### Documentation
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
- [ ] Lire ticket JIRA actif (NBA-12 en cours)
- [ ] Vérifier espace disque (2-3 GB libres)
- [ ] Tester connexion internet (nécessaire pour fetch)
- [ ] Vérifier installations (`pip list | grep -E "pyspark|delta|nba"`)

---

**Dernière mise à jour :** 05/02/2026  
**Prochaine révision :** Après merge NBA-12
