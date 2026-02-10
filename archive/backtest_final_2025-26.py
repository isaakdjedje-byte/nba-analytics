#!/usr/bin/env python3
"""
Backtest Final 2025-26

Évalue le modèle unifié sur la saison 2025-26 avec les vraies features V3.
Compare avec l'ancien système (fallback).

Usage:
    python scripts/backtest_final_2025-26.py
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backtest_2025_26():
    """Backtest sur la saison 2025-26."""
    logger.info("="*70)
    logger.info("BACKTEST FINAL - SAISON 2025-26")
    logger.info("="*70)
    
    # === ÉTAPE 1: Charger le modèle ===
    logger.info("\n[1/4] Chargement du modèle unifié...")
    model_path = Path("models/unified/xgb_unified_latest.joblib")
    if not model_path.exists():
        logger.error(f"❌ Modèle non trouvé: {model_path}")
        return
    
    model = joblib.load(model_path)
    logger.info(f"✓ Modèle chargé: {model_path}")
    
    # === ÉTAPE 2: Charger les features ===
    logger.info("\n[2/4] Chargement des features 2025-26...")
    features_path = Path("data/gold/ml_features/features_2025-26_v3.parquet")
    if not features_path.exists():
        logger.error(f"❌ Features non trouvées: {features_path}")
        return
    
    df = pd.read_parquet(features_path)
    logger.info(f"✓ {len(df)} matchs chargés")
    logger.info(f"✓ {len(df.columns)} features disponibles")
    
    # === ÉTAPE 3: Charger les features sélectionnées ===
    logger.info("\n[3/4] Sélection des features...")
    selected_features_file = Path("models/optimized/selected_features.json")
    if selected_features_file.exists():
        with open(selected_features_file, 'r') as f:
            selected_features = json.load(f)['features']
    else:
        # Fallback: utiliser toutes les features sauf metadata
        exclude_cols = ['game_id', 'season', 'game_date', 'season_type', 
                       'home_team_id', 'away_team_id', 'target']
        selected_features = [c for c in df.columns if c not in exclude_cols]
    
    logger.info(f"✓ {len(selected_features)} features sélectionnées")
    
    # === ÉTAPE 4: Préparer les données ===
    X = df[selected_features]
    y_true = df['target']
    
    # Filtrer uniquement les matchs joués (avec target)
    mask_played = y_true.notna()
    X_played = X[mask_played]
    y_played = y_true[mask_played]
    
    logger.info(f"✓ {len(X_played)} matchs avec résultats connus")
    
    # === ÉTAPE 5: Prédictions ===
    logger.info("\n[4/4] Prédictions...")
    y_pred = model.predict(X_played)
    y_proba = model.predict_proba(X_played)[:, 1]
    
    # === ÉTAPE 6: Calculer métriques ===
    accuracy = accuracy_score(y_played, y_pred)
    precision = precision_score(y_played, y_pred, zero_division=0)
    recall = recall_score(y_played, y_pred, zero_division=0)
    f1 = f1_score(y_played, y_pred, zero_division=0)
    auc = roc_auc_score(y_played, y_proba)
    
    # Matrice de confusion
    cm = confusion_matrix(y_played, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    # === ÉTAPE 7: Afficher résultats ===
    logger.info("\n" + "="*70)
    logger.info("RÉSULTATS BACKTEST 2025-26")
    logger.info("="*70)
    logger.info(f"✓ Matchs évalués: {len(y_played)}")
    logger.info(f"")
    logger.info(f"📊 Métriques:")
    logger.info(f"  Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
    logger.info(f"  Precision: {precision:.4f}")
    logger.info(f"  Recall:    {recall:.4f}")
    logger.info(f"  F1-Score:  {f1:.4f}")
    logger.info(f"  AUC:       {auc:.4f}")
    logger.info(f"")
    logger.info(f"📊 Matrice de confusion:")
    logger.info(f"  Vrais négatifs (TN): {tn}")
    logger.info(f"  Faux positifs (FP):  {fp}")
    logger.info(f"  Faux négatifs (FN):  {fn}")
    logger.info(f"  Vrais positifs (TP): {tp}")
    
    # === ÉTAPE 8: Comparaison ===
    baseline = 0.5479  # Fallback 2025-26
    improvement = accuracy - baseline
    
    logger.info(f"")
    logger.info(f"📈 Comparaison:")
    logger.info(f"  Ancien (fallback):  {baseline:.4f} ({baseline*100:.2f}%)")
    logger.info(f"  Nouveau (V3 live):  {accuracy:.4f} ({accuracy*100:.2f}%)")
    logger.info(f"  Amélioration:       {improvement:+.4f} ({improvement*100:+.2f}%)")
    
    # Objectif
    if accuracy >= 0.70:
        logger.info(f"")
        logger.info(f"🎯 OBJECTIF 70% ATTEINT!")
    elif accuracy >= 0.65:
        logger.info(f"")
        logger.info(f"⚠️ Proche de l'objectif (gap: {0.70 - accuracy:.2%})")
    else:
        logger.info(f"")
        logger.info(f"❌ Objectif non atteint (gap: {0.70 - accuracy:.2%})")
    
    # === ÉTAPE 9: Sauvegarder résultats ===
    results = {
        'timestamp': datetime.now().isoformat(),
        'season': '2025-26',
        'total_matches': len(df),
        'evaluated_matches': len(y_played),
        'metrics': {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1),
            'auc': float(auc)
        },
        'confusion_matrix': {
            'tn': int(tn),
            'fp': int(fp),
            'fn': int(fn),
            'tp': int(tp)
        },
        'comparison': {
            'baseline': float(baseline),
            'new_accuracy': float(accuracy),
            'improvement': float(improvement),
            'improvement_pct': float(improvement * 100),
            'target_reached': accuracy >= 0.70,
            'target_gap': float(0.70 - accuracy)
        }
    }
    
    results_path = Path("reports/backtest_2025-26_results.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"")
    logger.info(f"✓ Résultats sauvegardés: {results_path}")
    
    # Sauvegarder aussi prédictions détaillées
    predictions_df = pd.DataFrame({
        'game_id': df.loc[mask_played, 'game_id'],
        'game_date': df.loc[mask_played, 'game_date'],
        'home_team_id': df.loc[mask_played, 'home_team_id'],
        'away_team_id': df.loc[mask_played, 'away_team_id'],
        'actual': y_played.values,
        'predicted': y_pred,
        'proba_home_win': y_proba,
        'confidence': np.maximum(y_proba, 1 - y_proba),
        'is_correct': (y_pred == y_played.values)
    })
    
    predictions_path = Path("reports/backtest_2025-26_predictions.csv")
    predictions_df.to_csv(predictions_path, index=False)
    logger.info(f"✓ Prédictions sauvegardées: {predictions_path}")
    
    logger.info("\n" + "="*70)
    logger.info("BACKTEST TERMINÉ")
    logger.info("="*70)
    
    return results


if __name__ == '__main__':
    results = backtest_2025_26()
    
    print("\n" + "="*70)
    print("RÉSUMÉ")
    print("="*70)
    print(f"Accuracy 2025-26: {results['metrics']['accuracy']*100:.2f}%")
    print(f"Amélioration: +{results['comparison']['improvement_pct']:.2f}%")
    print(f"Objectif 70%: {'✅ ATTEINT' if results['comparison']['target_reached'] else '⚠️ NON ATTEINT'}")
