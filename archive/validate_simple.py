#!/usr/bin/env python3
"""Validation simplifiee sur 30 matchs"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import accuracy_score

print("="*70)
print("VALIDATION SUR 30 MATCHS RECENTS")
print("="*70)

# Charger donnees
df = pd.read_parquet("data/gold/ml_features/features_2025-26_v3.parquet")
df['game_date'] = pd.to_datetime(df['game_date'])
df = df.sort_values('game_date')

print(f"\nTotal matchs disponibles: {len(df)}")
print(f"Periode: {df['game_date'].min().date()} a {df['game_date'].max().date()}")

# Charger modele
model_path = Path("models/unified/xgb_fixed_latest.joblib")
if not model_path.exists():
    print("Modele non trouve, utilisation ancien modele")
    model_path = Path("models/unified/xgb_unified_latest.joblib")

model = joblib.load(model_path)
print(f"Modele charge: {model_path}")

# Verifier si c'est un dict (nouveau format) ou directement le modele
if isinstance(model, dict):
    feature_cols = model['feature_names']
    model = model['model']
    print(f"Features du modele: {len(feature_cols)}")
else:
    # Ancien format: fallback
    exclude = ['game_id', 'game_date', 'season', 'target', 'home_team_id', 'away_team_id', 'team_id', 'home_score', 'away_score', 'point_diff']
    feature_cols = [c for c in df.columns if c not in exclude and df[c].dtype in ['float64', 'int64']]
    feature_cols = [c for c in feature_cols if df[c].isna().sum() / len(df) < 0.3]
    print(f"Features auto: {len(feature_cols)}")

# Verifier que toutes les features existent
missing = [c for c in feature_cols if c not in df.columns]
if missing:
    print(f"Features manquantes: {missing}")
    # Ajouter colonnes manquantes avec valeur 0
    for col in missing:
        df[col] = 0
    print(f"Features manquantes remplies avec 0")

# Maintenant creer test_df (apres avoir ajoute les colonnes)
test_df = df.tail(30)
print(f"\nValidation sur {len(test_df)} matchs recents")
print(f"Periode test: {test_df['game_date'].min().date()} a {test_df['game_date'].max().date()}")

feature_cols = [c for c in feature_cols if c in df.columns]
print(f"Features disponibles: {len(feature_cols)}")

X = test_df[feature_cols].fillna(test_df[feature_cols].median())
y_true = test_df['target']

# Predire
y_pred = model.predict(X)
y_proba = model.predict_proba(X)[:, 1]

# Accuracy globale
accuracy = accuracy_score(y_true, y_pred)
print(f"\nAccuracy globale: {accuracy:.2%}")

# Analyser par confiance
print("\n" + "="*70)
print("ANALYSE PAR NIVEAU DE CONFIANCE")
print("="*70)

results = pd.DataFrame({
    'actual': y_true.values,
    'predicted': y_pred,
    'confidence': np.maximum(y_proba, 1-y_proba),
    'correct': y_pred == y_true.values
})

for threshold in [0.65, 0.70, 0.75]:
    high_conf = results[results['confidence'] >= threshold]
    if len(high_conf) > 0:
        acc = high_conf['correct'].mean()
        n = len(high_conf)
        pct = n / len(results) * 100
        print(f"Confiance >= {threshold:.0%}: {acc:.2%} accuracy ({n}/{len(results)} matchs, {pct:.1f}%)")

print("\n" + "="*70)
print("VALIDATION TERMINEE")
print("="*70)
