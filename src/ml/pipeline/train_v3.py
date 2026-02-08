#!/usr/bin/env python3
"""
Entrainement avec features V3
Test si on atteint 77.5% accuracy
"""

import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def train_with_v3_features():
    """Entraine XGB avec les nouvelles features."""
    logger.info("=== ENTRAINEMENT AVEC FEATURES V3 ===\n")
    
    # Charger données V3
    df = pd.read_parquet("data/gold/ml_features/features_v3.parquet")
    logger.info(f"Dataset V3: {len(df)} matchs, {len(df.columns)} colonnes")
    
    # Split temporel
    train_mask = ~df['season'].isin(['2023-24', '2024-25'])
    test_mask = df['season'].isin(['2023-24', '2024-25'])
    
    # Features (toutes sauf metadata, target ET data leakage!)
    exclude_cols = [
        'game_id', 'season', 'game_date', 'season_type',
        'home_team_id', 'away_team_id', 'target',
        # DATA LEAKAGE - Stats du match en cours!
        'home_score', 'away_score', 'point_diff',
        'home_reb', 'home_ast', 'home_stl', 'home_blk', 'home_tov', 'home_pf',
        'away_reb', 'away_ast', 'away_stl', 'away_blk', 'away_tov', 'away_pf',
        'home_ts_pct', 'home_efg_pct', 'home_game_score', 'home_fatigue_eff',
        'away_ts_pct', 'away_efg_pct', 'away_game_score', 'away_fatigue_eff',
        'ts_pct_diff'
    ]
    
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    logger.info(f"Features utilisees: {len(feature_cols)}")
    
    X_train = df.loc[train_mask, feature_cols]
    y_train = df.loc[train_mask, 'target']
    X_test = df.loc[test_mask, feature_cols]
    y_test = df.loc[test_mask, 'target']
    
    logger.info(f"Train: {len(X_train)} | Test: {len(X_test)}")
    
    # Charger XGB deja optimise (memes hyperparams)
    logger.info("\nChargement XGB optimise...")
    xgb = joblib.load("models/week1/xgb_optimized.pkl")
    
    # IMPORTANT: XGB garde les memes hyperparams, juste re-entraine avec + de features
    logger.info("Re-entrainement avec features V3...")
    xgb.fit(X_train, y_train)
    
    # Predictions
    y_pred = xgb.predict(X_test)
    y_proba = xgb.predict_proba(X_test)[:, 1]
    
    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, y_proba)
    
    logger.info("\n" + "="*60)
    logger.info("RESULTATS AVEC FEATURES V3")
    logger.info("="*60)
    logger.info(f"Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
    logger.info(f"Precision: {precision:.4f}")
    logger.info(f"Recall:    {recall:.4f}")
    logger.info(f"F1-Score:  {f1:.4f}")
    logger.info(f"AUC:       {auc:.4f}")
    
    # Comparaison avec baseline
    baseline_acc = 0.7676  # XGB avec 24 features
    gain = accuracy - baseline_acc
    
    logger.info(f"\nComparaison baseline (76.76%):")
    logger.info(f"  Gain: {gain:+.4f} ({gain*100:+.2f}%)")
    
    if accuracy >= 0.775:
        logger.info("\n🎯 OBJECTIF 77.5% ATTEINT!")
    else:
        logger.info(f"\n⚠️  Objectif 77.5% non atteint (gap: {0.775 - accuracy:+.4f})")
    
    # Sauvegarder
    results = {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'auc': float(auc),
        'baseline_accuracy': baseline_acc,
        'gain_over_baseline': float(gain),
        'features_count': len(feature_cols),
        'target_77_5_reached': accuracy >= 0.775
    }
    
    with open('results/week1/v3_training_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Sauvegarder le modele V3
    output_path = Path('models/week1/xgb_v3.pkl')
    joblib.dump(xgb, output_path)
    logger.info(f"\n[SAVED] Modele V3 sauvegarde: {output_path}")
    
    # Feature importance top 20
    importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': xgb.feature_importances_
    }).sort_values('importance', ascending=False)
    
    logger.info("\nTop 20 features importantes:")
    for i, row in importance.head(20).iterrows():
        marker = "[NEW]" if row['feature'] in [
            'home_off_eff', 'away_off_eff', 'off_eff_diff',
            'home_consistency', 'away_consistency', 'consistency_diff',
            'home_momentum', 'away_momentum', 'momentum_diff_v3'
        ] else ""
        logger.info(f"  {row['importance']:.4f} - {row['feature']} {marker}")
    
    return results


if __name__ == '__main__':
    results = train_with_v3_features()
    
    print("\n" + "="*60)
    print("ENTRAINEMENT V3 TERMINE")
    print("="*60)
    print(f"Accuracy: {results['accuracy']*100:.2f}%")
    print(f"Target 77.5%: {'✅ ATTEINT' if results['target_77_5_reached'] else '❌ NON ATTEINT'}")
