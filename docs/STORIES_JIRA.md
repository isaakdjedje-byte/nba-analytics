# STORIES JIRA - Plan 8 Jours

**Date :** 06 Fevrier 2026  
**Projet :** NBA Analytics Platform  
**Total Points :** 19 points ML + 13 points Data = 32 points

---

## NBA-18 : Metriques Avancees (8 points)

**Statut :** To Do  
**Priorite :** Haute  
**Depend de :** NBA-17  

### Description
En tant que Data Scientist, je veux calculer les metriques avancees NBA pour tous les joueurs avec box scores afin d'evaluer leur performance objectivement.

### Sous-taches
1. Calculer moyennes de ligue par saison (necessaire pour PER)
2. Implementer TS% (True Shooting Percentage)
3. Implementer eFG% (Effective FG Percentage)  
4. Implementer USG% (Usage Rate)
5. Implementer PER (Player Efficiency Rating) - version simplifiee
6. Implementer Game Score
7. Creer dataset avec metriques pour 532+ joueurs
8. Creer notebook explicatif avec exemples

### Formules

**TS%** = PTS / (2 x (FGA + 0.44 x FTA))

**eFG%** = (FGM + 0.5 x FG3M) / FGA

**USG%** = (FGA + TO + 0.44 x FTA) / Possessions x 100

**PER** = uPER x (Ligue_Pace / Equipe_Pace) x (15 / PER_moyen_ligue)

**Game Score** = PTS + 0.4xFG - 0.7xFGA - 0.4x(FTA-FT) + 0.7xORB + 0.3xDRB + STL + 0.7xAST + 0.7xBLK - 0.4xPF - TO

### Criteres d'acceptation
- [ ] TS% calcule pour 532+ joueurs
- [ ] PER coherent (moyenne ~15, ecart-type ~5)
- [ ] Validation sur cas connus : LeBron PER ~27, Jokic PER ~32
- [ ] Notebook 02_metrics_calculation.ipynb cree
- [ ] Dataset enrichi sauvegarde en Delta Lake

### Temps estime : 1 jour

---

## NBA-19 : Agregations Equipe/Saison (5 points)

**Statut :** To Do  
**Priorite :** Haute  
**Depend de :** NBA-18  

### Description
En tant que Data Engineer, je veux agreger les statistiques par equipe et par saison pour preparer les features ML.

### Sous-taches
1. Calculer moyennes equipe par saison (points, rebonds, passes)
2. Calculer pourcentages victoire global/home/away
3. Calculer classements par conference
4. Calculer pace, offensive/defensive rating
5. Creer features agreges joueur (moyennes carriere)

### Features a creer
```python
team_season_stats = {
    'avg_points': 'mean(PTS)',
    'avg_rebounds': 'mean(REB)',
    'avg_assists': 'mean(AST)',
    'win_pct': 'sum(W) / count()',
    'home_win_pct': 'sum(W_home) / count(home_games)',
    'pace': 'mean(pace)',
    'offensive_rating': 'mean(ortg)',
    'defensive_rating': 'mean(drtg)'
}

player_season_stats = {
    'games_played': 'count()',
    'avg_minutes': 'mean(MIN)',
    'avg_points': 'mean(PTS)',
    'shooting_splits': 'FG%, 3P%, FT%',
    'advanced': 'PER, TS%, USG%'
}
```

### Criteres d'acceptation
- [ ] Dataset team_season_stats/ cree
- [ ] Dataset player_season_stats/ cree
- [ ] 30 equipes x 7 saisons = 210 lignes
- [ ] Tests de coherence (win_pct entre 0 et 1)

### Temps estime : 0.5 jour

---

## NBA-20 : Transformations Matchs (5 points)

**Statut :** To Do  
**Priorite :** Haute  
**Depend de :** NBA-19  

### Description
En tant que Data Engineer, je veux transformer les donnees de matchs pour creer des features exploitables par le ML.

### Sous-taches
1. Creer features matchup (comparaison equipe A vs B)
2. Calculer differentiels (points, rebonds, etc.)
3. Creer historique H2H (5 derniers matchs)
4. Creer features forme recente (5 derniers matchs)
5. Calculer fatigue (back-to-back, rest days)

### Features a creer
```python
match_features = {
    'diff_points_avg': 'avg_pts_A - avg_pts_B',
    'diff_rebounds_avg': 'avg_reb_A - avg_reb_B',
    'diff_assists_avg': 'avg_ast_A - avg_ast_B',
    'h2h_wins_last_5': 'count(wins_A in last 5 matchups)',
    'form_A_last_5': 'wins_A / 5',
    'form_B_last_5': 'wins_B / 5',
    'rest_days_A': 'days since last game',
    'rest_days_B': 'days since last game',
    'travel_distance_A': 'miles traveled',
    'travel_distance_B': 'miles traveled',
    'fatigue_score_A': 'back-to-back flag',
    'fatigue_score_B': 'back-to-back flag'
}
```

### Criteres d'acceptation
- [ ] Dataset transformed_games/ cree
- [ ] Features calculees pour tous les matchs 2018-2025
- [ ] Pas de valeurs manquantes sur features critiques
- [ ] Tests temporels (pas de fuite de donnees future)

### Temps estime : 0.5 jour

---

## NBA-21 : Feature Engineering ML (8 points)

**Statut :** To Do  
**Priorite :** Haute  
**Depend de :** NBA-20  

### Description
En tant que Data Scientist, je veux creer les features finales pour l'entrainement des modeles ML.

### Sous-taches
1. Assembler toutes les sources (joueurs, equipes, matchs)
2. Creer features globales (stats saison)
3. Creer features contexte (home/away, H2H)
4. Creer features momentum (forme recente)
5. Creer features joueurs (stars, blessures)
6. Normaliser/encoder les variables
7. Creer train/validation/test sets
8. Sauvegarder dataset ML final

### Features ML
```python
ml_features = {
    # Features globales
    'global': [
        'team_a_avg_points_season',
        'team_b_avg_points_season',
        'team_a_win_pct',
        'team_b_win_pct',
        'team_a_rank',
        'team_b_rank',
        'team_a_offensive_rating',
        'team_b_offensive_rating'
    ],
    
    # Features contexte match
    'context': [
        'is_home_a',  # 1 si A joue a domicile
        'rest_days_diff',  # rest_A - rest_B
        'travel_distance_a',
        'travel_distance_b',
        'h2h_win_pct_a',  # % victoires A vs B historique
        'h2h_avg_margin'  # moyenne difference points H2H
    ],
    
    # Features forme recente
    'momentum': [
        'wins_last_5_a',
        'wins_last_5_b',
        'avg_margin_last_5_a',
        'avg_margin_last_5_b',
        'fatigue_score_a',  # back-to-back, 3-in-4-nights
        'fatigue_score_b'
    ],
    
    # Features individuelles (joueurs cles)
    'players': [
        'star_player_per_a',  # PER du meilleur joueur A
        'star_player_per_b',
        'star_player_usg_a',  # Usage rate star
        'star_player_usg_b',
        'injuries_impact_a',  # 0-1, 1 = tous disponibles
        'injuries_impact_b'
    ]
}
```

### Criteres d'acceptation
- [ ] Dataset ml_dataset_v1.parquet cree
- [ ] > 1000 matchs avec features completes
- [ ] Split train/val/test temporel (pas aleatoire)
- [ ] Pas de fuite de donnees ( leakage )
- [ ] Documentation features dans notebook 03

### Temps estime : 0.5 jour

---

## NBA-22-1 : ML Classification (6 points)

**Statut :** To Do  
**Priorite :** Haute  
**Depend de :** NBA-21  

### Description
En tant que Data Scientist, je veux construire un modele de classification pour predire le gagnant d'un match.

### Algorithme
- Random Forest Classifier (baseline)
- XGBoost Classifier (optimisation)

### Features
Toutes les features creees dans NBA-21

### Target
- winner : 0 = equipe A gagne, 1 = equipe B gagne

### Metriques
- Accuracy
- Precision
- Recall
- F1-Score
- ROC-AUC

### Criteres d'acceptation
- [ ] Baseline > 60% accuracy (home/away seul ~58%)
- [ ] Modele optimise > 65% accuracy
- [ ] Validation croisee temporelle (TimeSeriesSplit)
- [ ] Feature importance analysee et documentee
- [ ] Notebook 04_model_classification.ipynb cree
- [ ] Modele sauvegarde : models/classification_baseline.pkl

### Validation temporelle (CRITIQUE)
```python
from sklearn.model_selection import TimeSeriesSplit

# PAS de train_test_split aleatoire !
# Utiliser TimeSeriesSplit pour respecter la temporalite
cv = TimeSeriesSplit(n_splits=5)

for train_idx, test_idx in cv.split(X):
    # Train sur passe, test sur futur
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
```

### Temps estime : 0.5 jour

---

## NBA-22-2 : ML Regression (8 points)

**Statut :** To Do  
**Priorite :** Haute  
**Depend de :** NBA-22-1  

### Description
En tant que Data Scientist, je veux construire un modele de regression pour predire le score exact d'un match (challenge technique).

### Algorithme
- Random Forest Regressor
- XGBoost Regressor

### Pourquoi plus difficile que classification ?
- Variance elevee (basket est imprevisible)
- Erreur quantitative (MAE) vs binaire (accuracy)
- Besoin features avancees (pace, ratings)

### Features supplementaires vs classification
```python
features_regression = features_classification + [
    'pace',  # Rythme du match
    'offensive_rating_a',
    'defensive_rating_a',
    'offensive_rating_b',
    'defensive_rating_b',
    'effective_fg_pct_a',
    'effective_fg_pct_b',
    'turnover_rate_a',
    'turnover_rate_b',
    'star_player_ts_a',  # True shooting % star
    'star_player_ts_b'
]
```

### Targets
- score_team_a : float (points equipe A)
- score_team_b : float (points equipe B)

### Metriques
- MAE (Mean Absolute Error) : objectif < 10 points
- RMSE (Root Mean Squared Error)
- R² (coefficient de determination)

### Criteres d'acceptation
- [ ] MAE < 10 points (vs baseline ~12-13 points)
- [ ] Amelioration > 15% vs baseline (moyenne saison)
- [ ] Analyse des erreurs : quand ca echoue ?
- [ ] Modele sauvegarde : models/regression_advanced.pkl
- [ ] Notebook 05_model_regression.ipynb avec comparaisons

### Analyse d'erreurs
```python
# Identifier les matchs ou le modele echoue
errors = pd.DataFrame({
    'actual': y_test,
    'predicted': y_pred,
    'error': abs(y_test - y_pred),
    'context': X_test[['is_home', 'back_to_back', 'star_injured']]
})

# Cas avec erreur > 15 points
high_errors = errors[errors['error'] > 15]
print(f"Matchs avec erreur > 15 pts : {len(high_errors)}")
print("Caracteristiques communes :")
print(high_errors.describe())
```

### Temps estime : 2 jours

---

## NBA-22-3 : ML Clustering (5 points)

**Statut :** To Do  
**Priorite :** Moyenne  
**Depend de :** NBA-18  

### Description
En tant que Data Scientist, je veux identifier les profils de joueurs via clustering non-supervise.

### Algorithme
- K-Means (elbow method pour choisir k)
- DBSCAN (alternative, detection outliers)

### Features (normalisees)
```python
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
    'turnover_rate',
    'assist_to_turnover_ratio',
    'true_shooting_pct'
]
```

### Nombre de clusters
- Determiner avec Elbow Method (2-10 clusters)
- Objectif : 4-6 clusters interpretables

### Criteres d'acceptation
- [ ] 4-6 clusters interpretables
- [ ] Clusters nommes avec descriptions : 
  - "Interieurs defensifs" (grands, rebonds, blocks)
  - "Shooters purs" (petits, 3pts, peu de passes)
  - "Playmakers" (passes, vision, controle)
  - "Ailiers complets" (equilibre stats)
  - "Centres offensifs" (grand, points peinture)
- [ ] Visualisation clusters (PCA ou t-SNE)
- [ ] Exemples de joueurs par cluster (3-5 par cluster)
- [ ] Notebook 06_model_clustering.ipynb cree

### Clusters attendus
| Cluster | Description | Exemples |
|---------|-------------|----------|
| 0 | Interieurs defensifs | Gobert, Lopez |
| 1 | Shooters purs | Curry, Thompson |
| 2 | Playmakers | Paul, Young |
| 3 | Ailiers complets | James, Durant |
| 4 | Centres offensifs | Embiid, Jokic |

### Temps estime : 1 jour

---

## RECAPITULATIF

### Planning 8 Jours

| Jour | Story | Points | Description |
|------|-------|--------|-------------|
| 1 | NBA-18 | 8 | Metriques avancees |
| 2 | NBA-19 | 5 | Agregations |
| 2 | NBA-20 | 5 | Transformations |
| 3 | NBA-21 | 8 | Feature Engineering |
| 3 | NBA-22-1 | 6 | Classification |
| 4 | NBA-22-3 | 5 | Clustering |
| 5-6 | NBA-22-2 | 8 | Regression |
| 7 | Architecture | - | Refactoring + Tests |
| 8 | Packaging | - | Docker + CI/CD |

### Total Points
- Data Engineering : 18 points (NBA-18, 19, 20, 21)
- Machine Learning : 19 points (NBA-22-1, 22-2, 22-3)
- **Total : 37 points**

### Dependances
```
NBA-17 (Nettoyage)
    |
    v
NBA-18 (Metriques)
    |
    +----> NBA-19 (Agregations)
    |          |
    |          v
    |      NBA-20 (Transformations)
    |          |
    |          v
    |      NBA-21 (Features ML)
    |          |
    +----> NBA-22-1 (Classification)
    |          |
    |          v
    |      NBA-22-2 (Regression)
    |
    +----> NBA-22-3 (Clustering)
```

### Notes
- NBA-22-1 et NBA-22-3 peuvent etre faits en parallele apres NBA-21
- NBA-22-2 (Regression) depend de NBA-22-1 pour les features optimisees
- Architecture et Packaging (Jours 7-8) sont independants des stories JIRA

---

**Derniere mise a jour :** 06/02/2026 21:30  
**Statut :** Pret pour execution  
**Prochaine etape :** NBA-18 (demain matin)
