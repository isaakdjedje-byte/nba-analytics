#!/usr/bin/env python3
"""
Test du notebook NBA-22 sans Jupyter
Execute toutes les cellules du notebook en Python pur
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Mode non-interactif
import matplotlib.pyplot as plt
import seaborn as sns
import json
from pathlib import Path
from sklearn.metrics import confusion_matrix, roc_curve, auc, accuracy_score, classification_report
from sklearn.ensemble import RandomForestClassifier
import joblib

print("="*70)
print("NBA-22: TEST DU NOTEBOOK")
print("="*70)
print()

# Cell 1: Chargement des données
print("1. Chargement des données...")
df = pd.read_parquet("data/gold/ml_features/features_all.parquet")
print(f"   [OK] Dataset: {len(df)} matchs")
print(f"   [OK] Saisons: {sorted(df['season'].unique())}")
print(f"   [OK] Features: {len(df.columns)} colonnes")
print(f"   [OK] Distribution target: {df['target'].value_counts(normalize=True).to_dict()}")
print()

# Cell 2: Chargement des résultats
print("2. Chargement des résultats...")
exp_dir = sorted(Path("models/experiments").glob("nba22_*"))[-1]
metrics_file = exp_dir / "metrics.json"
print(f"   [OK] Expérimentation: {exp_dir.name}")

with open(metrics_file) as f:
    results = json.load(f)

print(f"   [OK] Timestamp: {results['timestamp']}")
print(f"   [OK] Train size: {results['train_size']}")
print(f"   [OK] Test size: {results['test_size']}")
print(f"   [OK] N features: {results['n_features']}")
print()

# Cell 3: Comparaison des modèles
print("3. Comparaison des modèles...")
print()
print("   " + "-"*60)
print(f"   {'Modèle':<20} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}")
print("   " + "-"*60)

for model_name, metrics in results['models'].items():
    print(f"   {metrics['model_name']:<20} "
          f"{metrics['accuracy']:>10.3f} "
          f"{metrics['precision']:>10.3f} "
          f"{metrics['recall']:>10.3f} "
          f"{metrics['f1']:>10.3f}")

print("   " + "-"*60)
print()

# Cell 4: Feature importance
print("4. Feature Importance...")
print()
for model_name, metrics in results['models'].items():
    print(f"   Top 5 features - {metrics['model_name']}:")
    for i, (feat, importance) in enumerate(list(metrics['feature_importance'].items())[:5], 1):
        print(f"      {i}. {feat}: {importance:.4f}")
    print()

# Cell 5-6: Chargement du meilleur modèle et évaluation
print("5. Chargement du meilleur modèle...")
best_model_name = results['best_model']['name']
model_path = exp_dir / f"model_{best_model_name}.joblib"
model = joblib.load(model_path)
print(f"   [OK] Meilleur modèle: {best_model_name.upper()}")
print(f"   [OK] Accuracy: {results['best_model']['accuracy']:.3f}")
print()

# Préparer les données de test
print("6. Évaluation sur test set...")
test_mask = df['season'].isin(['2023-24', '2024-25'])
exclude_cols = [
    'game_id', 'season', 'game_date', 'season_type',
    'home_team_id', 'home_team_name', 'home_team_abbr',
    'away_team_id', 'away_team_name', 'away_team_abbr',
    'home_wl', 'away_wl', 'target', 'point_diff',
    'home_score', 'away_score',
    'home_reb', 'home_ast', 'home_stl', 'home_blk', 'home_tov', 'home_pf',
    'away_reb', 'away_ast', 'away_stl', 'away_blk', 'away_tov', 'away_pf',
    'home_ts_pct', 'home_efg_pct', 'home_game_score', 'home_fatigue_eff',
    'away_ts_pct', 'away_efg_pct', 'away_game_score', 'away_fatigue_eff',
    'ts_pct_diff'
]
feature_cols = [c for c in df.columns if c not in exclude_cols]
X_test = df.loc[test_mask, feature_cols]
y_test = df.loc[test_mask, 'target']

# Prédictions
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

# Métriques
acc = accuracy_score(y_test, y_pred)
print(f"   [OK] Accuracy: {acc:.3f}")
print()

# Matrice de confusion
cm = confusion_matrix(y_test, y_pred)
print("   Matrice de confusion:")
print(f"      TN: {cm[0,0]:4d} | FP: {cm[0,1]:4d}")
print(f"      FN: {cm[1,0]:4d} | TP: {cm[1,1]:4d}")
print()

# Cell 7: Analyse par saison
print("7. Analyse par saison...")
print()
for season in ['2023-24', '2024-25']:
    season_mask = (df['season'] == season) & test_mask
    if season_mask.sum() > 0:
        X_season = df.loc[season_mask, feature_cols]
        y_season = df.loc[season_mask, 'target']
        y_pred_season = model.predict(X_season)
        acc_season = accuracy_score(y_season, y_pred_season)
        print(f"   {season}: Accuracy = {acc_season:.3f} ({len(y_season)} matchs)")
print()

# Cell 8: Résumé
print("="*70)
print("RÉSUMÉ NBA-22")
print("="*70)
print()
print(f"[OK] Expérimentation: {exp_dir.name}")
print(f"[OK] Meilleur modèle: {results['best_model']['name'].upper()}")
print(f"[OK] Accuracy: {results['best_model']['accuracy']:.3f} (Objectif: > 0.60)")
print(f"[OK] Objectif atteint: {'OUI' if results['best_model']['accuracy'] > 0.60 else 'NON'}")
print()
print("Top 5 features importantes:")
for i, feat in enumerate(list(results['models'][best_model_name]['feature_importance'].keys())[:5], 1):
    importance = list(results['models'][best_model_name]['feature_importance'].values())[i-1]
    print(f"  {i}. {feat} ({importance:.4f})")
print()
print("="*70)
print("TEST COMPLÉTÉ AVEC SUCCÈS!")
print("="*70)
