#!/usr/bin/env python3
"""
Analyse des erreurs RF vs XGB - Decision Go/No-Go pour stacking
"""

import joblib
import pandas as pd
import numpy as np
from pathlib import Path

print('=== ANALYSE DES ERREURS RF vs XGB ===\n')

# Charger modèles
rf = joblib.load('models/week1/rf_optimized.pkl')
xgb = joblib.load('models/week1/xgb_optimized.pkl')
print('[OK] Modeles charges')

# Charger données
df = pd.read_parquet('data/gold/ml_features/features_all.parquet')
print(f'[OK] Donnees chargees: {len(df)} matchs')

# Split temporel identique
train_mask = ~df['season'].isin(['2023-24', '2024-25'])
test_mask = df['season'].isin(['2023-24', '2024-25'])

# Features (mêmes exclusions)
exclude_cols = [
    'game_id', 'season', 'game_date', 'season_type',
    'home_team_id', 'home_team_name', 'home_team_abbr',
    'away_team_id', 'away_team_name', 'away_team_abbr',
    'home_wl', 'away_wl', 'target',
    'point_diff', 'home_score', 'away_score',
    'home_reb', 'home_ast', 'home_stl', 'home_blk', 'home_tov', 'home_pf',
    'away_reb', 'away_ast', 'away_stl', 'away_blk', 'away_tov', 'away_pf',
    'home_ts_pct', 'home_efg_pct', 'home_game_score', 'home_fatigue_eff',
    'away_ts_pct', 'away_efg_pct', 'away_game_score', 'away_fatigue_eff',
    'ts_pct_diff'
]

feature_cols = [c for c in df.columns if c not in exclude_cols]
X_test = df.loc[test_mask, feature_cols]
y_test = df.loc[test_mask, 'target']

print(f'[OK] Features: {len(feature_cols)}')
print(f'[OK] Test set: {len(X_test)} matchs\n')

# Prédictions
print('Generation des predictions...')
rf_pred = rf.predict(X_test)
xgb_pred = xgb.predict(X_test)

# Accuracy individuelle
rf_acc = (rf_pred == y_test).mean()
xgb_acc = (xgb_pred == y_test).mean()

print(f'\n[STATS] Accuracy individuelle:')
print(f'   RF:  {rf_acc:.4f} ({rf_acc*100:.2f}%)')
print(f'   XGB: {xgb_acc:.4f} ({xgb_acc*100:.2f}%)')

# Analyse des erreurs
rf_errors = rf_pred != y_test
xgb_errors = xgb_pred != y_test

# Matrice de confusion des erreurs
both_correct = (~rf_errors & ~xgb_errors).sum()
rf_only_wrong = (rf_errors & ~xgb_errors).sum()
xgb_only_wrong = (~rf_errors & xgb_errors).sum()
both_wrong = (rf_errors & xgb_errors).sum()

print(f'\n[STATS] Matrice des erreurs:')
print(f'   Les deux corrects:     {both_correct} ({both_correct/len(y_test)*100:.1f}%)')
print(f'   RF seul se trompe:     {rf_only_wrong} ({rf_only_wrong/len(y_test)*100:.1f}%)')
print(f'   XGB seul se trompe:    {xgb_only_wrong} ({xgb_only_wrong/len(y_test)*100:.1f}%)')
print(f'   Les deux se trompent:  {both_wrong} ({both_wrong/len(y_test)*100:.1f}%)')

# Corrélation des erreurs
correlation = np.corrcoef(rf_errors.astype(int), xgb_errors.astype(int))[0,1]
print(f'\n[STATS] Correlation des erreurs: {correlation:.3f}')

# Décision
print(f'\n[DECISION]:')
if correlation < 0.6:
    print(f'   [OK] Stacking PROMETTEUR (correlation < 0.6)')
    print(f'   Potentiel de gain: Complementarite elevee')
elif correlation < 0.8:
    print(f'   [WARNING] Stacking possible (correlation moyenne)')
    print(f'   Gain attendu: Modere')
else:
    print(f'   [SKIP] Stacking INUTILE (correlation trop elevee)')
    print(f'   Les modeles se trompent pareil -> Pas de complementarite')

# Voting simple test
voting_pred = ((rf.predict_proba(X_test)[:, 1] + xgb.predict_proba(X_test)[:, 1]) / 2 > 0.5).astype(int)
voting_acc = (voting_pred == y_test).mean()
print(f'\n[RESULT] Voting simple (moyenne): {voting_acc:.4f} ({voting_acc*100:.2f}%)')

# Sauvegarder résultats pour le stacking
results = {
    'correlation': float(correlation),
    'rf_accuracy': float(rf_acc),
    'xgb_accuracy': float(xgb_acc),
    'voting_accuracy': float(voting_acc),
    'rf_only_errors': int(rf_only_wrong),
    'xgb_only_errors': int(xgb_only_wrong),
    'both_errors': int(both_wrong),
    'recommendation': 'STACKING' if correlation < 0.8 else 'SKIP'
}

import json
with open('results/week1/error_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f'\n[SAVED] Resultats sauvegardes dans results/week1/error_analysis.json')
