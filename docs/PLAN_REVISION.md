# PLAN DE REVISION - NBA Analytics Platform

**Date :** 06 Fevrier 2026  
**Version :** 3.0 (Revision complete post-NBA-17)  
**Auteur :** Agent/Data Engineer  
**Statut :** Approuve pour execution

---

## CONTEXTE

### Situation Initiale
Apres realisation de NBA-16 (Documentation) et demarrage de NBA-17 (Nettoyage), analyse approfondie revelant :
- **Probleme :** Donnees des 5103 joueurs historiques incompletes (pas de taille/poids pour ~90%)
- **Solution adoptee :** Architecture stratifiee avec enrichissement hybride
- **Impact :** Revision complete du planning ML et de la structure JIRA

### Decisions Cles
1. **Architecture Minimaliste** : 1 fichier (clean_players.py) vs 4 fichiers initiaux
2. **Stratification Donnees** : 3 niveaux (All/Basic → Detailed → Modern)
3. **Scission NBA-22** : 3 stories distinctes (Classification + Regression + Clustering)
4. **Approche Hybride** : Respect ordre JIRA mais validation ML precoce

---

## ARCHITECTURE FINALE

### Structure des Donnees

data/
├── bronze/                          # Donnees brutes
│   ├── raw/                         # NBA-11 à NBA-15
│   │   ├── all_players_historical.json
│   │   ├── rosters/roster_2023_24.json
│   │   └── games_boxscores/         # 2018-2025
│   └── supplemental/
│       └── players_critical.csv     # 54 legendes NBA
│
├── silver/                          # Donnees nettoyees
│   ├── players_all_5103/            # NBA-17
│   │   ├── Partition : is_active/position
│   │   ├── Colonnes : id, full_name, height_cm, weight_kg, position
│   │   └── Source : Roster + API + CSV + Imputation
│   │
│   ├── players_detailed_2000_2017/  # NBA-18 Extension (optionnel)
│   │   ├── ~400 joueurs supplementaires
│   │   ├── Box scores 2000-2017
│   │   └── Metriques : PER, TS%, USG%, Game Score
│   │
│   └── players_modern_2018_2025/    # NBA-18 Principal
│       ├── 532 joueurs (roster 2023-24)
│       ├── 7 saisons completes
│       ├── Box scores detailles
│       └── Dataset ML principal
│
└── gold/                            # Features ML
    └── ml_dataset_final.parquet     # NBA-21 + NBA-22
        ├── Features engineered
        ├── Labels (winner, score, clusters)
        └── Train/Test/Validation splits

### Strategie Enrichissement

5103 joueurs totaux
├── 532 joueurs (10%)     → Roster 2023-24 (donnees completes locales)
├── ~50 joueurs (1%)      → CSV manuel (legendes NBA)
├── ~4000 joueurs (78%)   → API NBA (CommonPlayerInfo)
└── ~500 joueurs (10%)    → Imputation statistique (position + epoque)

Sources API : 
- CommonPlayerInfo (height, weight, position, birthdate)
- Rate limit : 1 requete/seconde
- Cache : JSON local pour reprises

---

## PLANNING DETAILLE - 8 JOURS

### JOUR 1 : NBA-18 - Metriques Avancees

**Objectif :** Calculer les 5 metriques NBA pour joueurs avec box scores
**Duree :** 8h

#### Matin (4h) : Setup et Calculs

Commandes :
```bash
# 1. Verifier output NBA-17 (30min)
ls -lh data/silver/players_cleaned/
cat data/silver/players_cleaned_stats.json

python << 'EOF'
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()
df = spark.read.format("delta").load("data/silver/players_cleaned/")
print(f"Total joueurs : {df.count()}")
print(f"Colonnes : {df.columns}")
df.groupBy("data_source").count().show()
EOF

# 2. Creer notebook
mkdir -p notebooks
cp notebooks/template.ipynb notebooks/02_metrics_calculation.ipynb 2>/dev/null || touch notebooks/02_metrics_calculation.ipynb

# 3. Calcul moyennes ligue par saison
python src/metrics/calculate_league_averages.py

# 4. Implementer metriques de base
# - TS% (True Shooting %)
# - eFG% (Effective FG %)
# - USG% (Usage Rate)
```

#### Apres-midi (4h) : PER et Game Score

```bash
# 5. Implementer PER complexe
# Formule : uPER x (Ligue_Pace / Equipe_Pace) x (15 / Moyenne_PER_ligue)

# 6. Implementer Game Score
# Formule ponderee avec validation

# 7. Tests et validation
pytest tests/test_metrics.py -v
# Cas tests : LeBron 2024, Curry 2024, Jokic 2024
```

**Livrables :**
- [ ] notebooks/02_metrics_calculation.ipynb
- [ ] src/metrics/calculator.py
- [ ] data/silver/players_with_metrics/ (Delta Lake)
- [ ] Tests passants (3 cas connus valides)

**Criteres de succes :**
- TS% calcule pour 532+ joueurs
- PER coherent (moyenne ~15, std ~5)
- Validation : LeBron PER ~27, Jokic PER ~32

---

### JOUR 2 : NBA-19 + NBA-20 - Agregations et Transformations

**Objectif :** Preparer donnees pour feature engineering
**Duree :** 8h

#### NBA-19 : Agregations Equipe/Saison (4h)

```python
# Fichier : src/processing/aggregate_team_season.py

# Agregations necessaires :
agg_features = {
    'team_season': {
        'avg_points': 'mean(PTS)',
        'avg_rebounds': 'mean(REB)',
        'avg_assists': 'mean(AST)',
        'win_pct': 'sum(W) / count()',
        'home_win_pct': 'sum(W_home) / count(home_games)',
        'pace': 'mean(pace)',
        'offensive_rating': 'mean(ortg)',
        'defensive_rating': 'mean(drtg)'
    },
    'player_season': {
        'games_played': 'count()',
        'avg_minutes': 'mean(MIN)',
        'avg_points': 'mean(PTS)',
        'shooting_splits': 'FG%, 3P%, FT%',
        'advanced': 'PER, TS%, USG%'
    }
}
```

Commandes :
```bash
# Creer agregations
python src/processing/aggregate_team_season.py --seasons 2018-2025

# Verifier output
ls data/silver/team_season_stats/
ls data/silver/player_season_stats/
```

#### NBA-20 : Transformation Matchs (4h)

```python
# Fichier : src/processing/transform_games.py

# Transformations :
# 1. Creer features matchup
# 2. Calculer differentiels (Team_A - Team_B)
# 3. Historique H2H (5 derniers matchs)
# 4. Forme recente (5 derniers matchs)

features_match = {
    'diff_points_avg': 'avg_pts_A - avg_pts_B',
    'diff_rebounds_avg': 'avg_reb_A - avg_reb_B',
    'h2h_wins_last_5': 'count(wins_A in last 5 matchups)',
    'form_A_last_5': 'wins_A / 5',
    'form_B_last_5': 'wins_B / 5',
    'rest_days_A': 'days since last game',
    'rest_days_B': 'days since last game',
    'travel_distance': 'miles traveled'
}
```

**Livrables :**
- [ ] data/silver/transformed_games/ (features par match)
- [ ] data/silver/team_season_stats/
- [ ] data/silver/player_season_stats/

---

### JOUR 3 : NBA-21 + NBA-22-1 - Features ML + Classification

**Objectif :** Creer features ML et premier modele baseline
**Duree :** 8h

#### NBA-21 : Feature Engineering (4h)

```python
# Fichier : src/ml/feature_engineering.py

# Features pour ML :
ml_features = {
    # Features globales
    'global': [
        'team_a_avg_points_season',
        'team_b_avg_points_season',
        'team_a_win_pct',
        'team_b_win_pct',
        'team_a_rank',
        'team_b_rank'
    ],
    
    # Features contexte match
    'context': [
        'is_home_a',  # 1 si A joue a domicile
        'rest_days_diff',  # rest_A - rest_B
        'travel_distance_a',
        'travel_distance_b',
        'h2h_win_pct_a'  # % victoires A vs B historique
    ],
    
    # Features forme recente
    'momentum': [
        'wins_last_5_a',
        'wins_last_5_b',
        'avg_margin_last_5_a',
        'avg_margin_last_5_b',
        'fatigue_score'  # back-to-back, 3-in-4-nights
    ],
    
    # Features individuelles (joueurs cles)
    'players': [
        'star_player_per_a',  # PER du meilleur joueur A
        'star_player_per_b',
        'injuries_impact_a',  # 0-1, 1 = tous disponibles
        'injuries_impact_b'
    ]
}
```

Commandes :
```bash
# Creer dataset ML
python src/ml/feature_engineering.py --output data/gold/ml_dataset_v1.parquet

# Verifier dimensions
python << 'EOF'
import pandas as pd
df = pd.read_parquet('data/gold/ml_dataset_v1.parquet')
print(f"Shape: {df.shape}")
print(f"Features: {df.columns.tolist()}")
print(f"Missing: {df.isnull().sum().sum()}")
EOF
```

#### NBA-22-1 : Classification Gagnant/Perdant (4h)

```python
# Fichier : src/ml/classification_model.py
# Notebook : notebooks/04_model_classification.ipynb

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score

# Modele baseline
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42
)

# Validation temporelle (CRITIQUE !)
cv = TimeSeriesSplit(n_splits=5)

# Features X et target y
X = df[features_list]
y = df['winner']  # 0 = team_a, 1 = team_b

# Entrainement
model.fit(X_train, y_train)

# Evaluation
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)

print(f"Accuracy: {accuracy:.3f}")  # Objectif : > 0.65
print(f"Precision: {precision:.3f}")
print(f"Recall: {recall:.3f}")
```

**Livrables :**
- [ ] notebooks/04_model_classification.ipynb
- [ ] src/ml/classification_model.py
- [ ] Modele sauvegarde : models/classification_baseline.pkl
- [ ] Accuracy > 65% sur test set

**Criteres de succes :**
- Baseline > 60% (home/away seul ~58%)
- Optimise > 65%
- Feature importance analysee

---

### JOUR 4 : NBA-22-3 - Clustering Profils Joueurs

**Objectif :** Segmentation non-supervisee des joueurs
**Duree :** 8h

```python
# Fichier : src/ml/clustering_model.py
# Notebook : notebooks/06_model_clustering.ipynb

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

# Features pour clustering (normalisees)
features_clustering = [
    'height_cm',
    'weight_kg',
    'points_per_minute',
    'assists_per_minute',
    'rebounds_per_minute',
    'three_point_pct',
    'free_throw_pct',
    'steals_per_minute',
    'blocks_per_minute',
    'turnover_rate'
]

# Normalisation
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[features_clustering])

# Determiner nombre optimal de clusters
inertias = []
for k in range(2, 10):
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(X_scaled)
    inertias.append(kmeans.inertia_)

# Elbow method pour choisir k
plt.plot(range(2, 10), inertias, 'bo-')
plt.xlabel('Nombre de clusters (k)')
plt.ylabel('Inertie')
plt.title('Elbow Method')
plt.savefig('figures/elbow_method.png')

# Clustering final (k=5 ou 6)
kmeans = KMeans(n_clusters=5, random_state=42)
df['cluster'] = kmeans.fit_predict(X_scaled)

# Analyse clusters
for cluster_id in range(5):
    cluster_players = df[df['cluster'] == cluster_id]
    print(f"\nCluster {cluster_id}:")
    print(f"Nombre: {len(cluster_players)}")
    print(f"Caracteristiques:")
    print(f"  - Taille moy: {cluster_players['height_cm'].mean():.1f} cm")
    print(f"  - Poids moy: {cluster_players['weight_kg'].mean():.1f} kg")
    print(f"  - Points/min: {cluster_players['points_per_minute'].mean():.3f}")
    print(f"Exemples: {cluster_players['full_name'].head(3).tolist()}")
```

**Clusters attendus :**
- Cluster 0 : "Interieurs defensifs" (grands, lourds, rebonds)
- Cluster 1 : "Shooters pures" (petits, legers, 3pts)
- Cluster 2 : "Playmakers" (passes, vision)
- Cluster 3 : "Ailiers complets" (equilibre)
- Cluster 4 : "Centres offensifs" (grand, points peinture)

**Livrables :**
- [ ] notebooks/06_model_clustering.ipynb
- [ ] src/ml/clustering_model.py
- [ ] Visualisations clusters (PCA/t-SNE)
- [ ] 4-6 clusters nommes avec exemples

---

### JOUR 5-6 : NBA-22-2 - Regression Score Exact

**Objectif :** Modele de regression pour predire score exact
**Duree :** 2 jours (16h)

**Pourquoi plus difficile :**
- Variance elevee (basket imprevisible)
- Besoin features avancees (pace, ratings)
- Evaluation MAE/RMSE vs classification accuracy

```python
# Fichier : src/ml/regression_model.py
# Notebook : notebooks/05_model_regression.ipynb

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Deux modeles : un pour chaque equipe
model_a = RandomForestRegressor(n_estimators=200, max_depth=15)
model_b = RandomForestRegressor(n_estimators=200, max_depth=15)

# Features supplementaires vs classification
features_regression = features_classification + [
    'pace',  # Rythme du match
    'offensive_rating_a',
    'defensive_rating_a',
    'offensive_rating_b',
    'defensive_rating_b',
    'effective_fg_pct_a',
    'effective_fg_pct_b',
    'turnover_rate_a',
    'turnover_rate_b'
]

# Targets
y_a = df['score_team_a']
y_b = df['score_team_b']

# Entrainement
model_a.fit(X_train, y_a_train)
model_b.fit(X_train, y_b_train)

# Prediction
pred_a = model_a.predict(X_test)
pred_b = model_b.predict(X_test)

# Evaluation
mae_a = mean_absolute_error(y_a_test, pred_a)
mae_b = mean_absolute_error(y_b_test, pred_b)

print(f"MAE Team A: {mae_a:.2f} points")
print(f"MAE Team B: {mae_b:.2f} points")

# Baseline simple : moyenne saison
baseline_mae = mean_absolute_error(y_test, [y_train.mean()] * len(y_test))
print(f"Baseline (moyenne): {baseline_mae:.2f} points")
print(f"Amelioration: {(1 - mae/baseline_mae)*100:.1f}%")

# Objectif : MAE < 10 points
```

**Analyse d'erreurs :**
```python
# Quand le modele echoue ?
errors = pd.DataFrame({
    'actual': y_test,
    'predicted': y_pred,
    'error': abs(y_test - y_pred)
})

# Cas avec erreur > 15 points
high_errors = errors[errors['error'] > 15]
print(f"Matchs avec erreur > 15 pts: {len(high_errors)}")
print("Caracteristiques communes:")
print(high_errors.describe())
```

**Livrables (Jour 6 soir) :**
- [ ] notebooks/05_model_regression.ipynb
- [ ] src/ml/regression_model.py
- [ ] Modele sauvegarde : models/regression_advanced.pkl
- [ ] MAE < 10 points (vs baseline ~12-13)
- [ ] Analyse erreurs complete

---

### JOUR 7 : Architecture & Tests

**Objectif :** Refactoring professionnel et tests
**Duree :** 8h

#### Matin : Refactoring Code (4h)

Structure finale :
```
src/
├── ingestion/          # NBA-11 à NBA-15
│   ├── fetch_nba_data.py
│   └── fetch_historical.py
├── processing/         # NBA-17 à NBA-20
│   ├── clean_players.py
│   ├── calculate_metrics.py
│   ├── aggregate.py
│   └── transform.py
├── metrics/            # NBA-18
│   └── calculator.py
└── ml/                 # NBA-21 à NBA-22
    ├── feature_engineering.py
    ├── classification_model.py
    ├── regression_model.py
    └── clustering_model.py

tests/
├── test_cleaning.py
├── test_metrics.py
├── test_ml.py
└── conftest.py
```

Commandes :
```bash
# Creer structure
mkdir -p src/metrics src/ml tests/models tests/figures

# Tests
pytest tests/ -v --tb=short
pytest tests/ --cov=src --cov-report=html
```

#### Apres-midi : Tests Integration (4h)

```bash
# Test end-to-end
python << 'EOF'
from src.processing.clean_players import PlayersDataCleaner
from src.metrics.calculator import MetricsCalculator
from src.ml.feature_engineering import FeatureEngineer

# 1. Nettoyage
cleaner = PlayersDataCleaner()
players = cleaner.run()

# 2. Metriques
calc = MetricsCalculator()
players_metrics = calc.calculate_all(players)

# 3. Features
fe = FeatureEngineer()
ml_dataset = fe.create_features(players_metrics)

# 4. Verification
assert len(ml_dataset) > 500
assert 'PER' in ml_dataset.columns
assert 'TS_pct' in ml_dataset.columns
print("Pipeline end-to-end OK")
EOF
```

**Livrables :**
- [ ] Architecture modulaire propre
- [ ] Tests unitaires (couverture > 80%)
- [ ] Tests integration passants
- [ ] Rapport couverture HTML

---

### JOUR 8 : Packaging Enterprise

**Objectif :** Packaging professionnel et CI/CD
**Duree :** 8h

#### Matin : Docker et Requirements (4h)

Dockerfile :
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dependances systeme
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code
COPY src/ ./src/
COPY configs/ ./configs/
COPY data/ ./data/

# Entrypoint
CMD ["python", "src/processing/clean_players.py"]
```

Commandes :
```bash
# Build et test
pip freeze > requirements.txt
docker build -t nba-analytics:latest .
docker run -v $(pwd)/data:/app/data nba-analytics:latest
```

#### Apres-midi : CI/CD et Documentation (4h)

GitHub Actions (.github/workflows/ci.yml) :
```yaml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest tests/ --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

**Livrables :**
- [ ] Dockerfile fonctionnel
- [ ] requirements.txt fige
- [ ] .github/workflows/ci.yml
- [ ] README.md complet
- [ ] Push GitHub avec CI verte

---

## RECAPITULATIF STORIES JIRA

| Story | Points | Description | Duree |
|-------|--------|-------------|-------|
| NBA-18 | 8 | Metriques avancees | 1 jour |
| NBA-19 | 5 | Agregations | 0.5 jour |
| NBA-20 | 5 | Transformations | 0.5 jour |
| NBA-21 | 8 | Feature Engineering | 0.5 jour |
| NBA-22-1 | 6 | ML Classification | 0.5 jour |
| NBA-22-2 | 8 | ML Regression | 2 jours |
| NBA-22-3 | 5 | ML Clustering | 1 jour |

**Total ML :** 19 pts (vs 8 initialement)

---

## COMMANDES RAPIDES

```bash
# Verifier progression
ls -lh data/silver/
pytest tests/ -v

# Lancer pipeline
python src/processing/clean_players.py

# Executer notebook
jupyter notebook notebooks/02_metrics_calculation.ipynb

# Build Docker
docker build -t nba-analytics:latest .

# Tests CI
pytest tests/ --cov=src --cov-report=html
```

---

**Derniere mise a jour :** 06/02/2026 21:30
**Statut :** Pret pour execution
**Prochaine etape :** Commencer Jour 1 (NBA-18) des que NBA-17 termine
