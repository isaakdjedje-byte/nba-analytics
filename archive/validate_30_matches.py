#!/usr/bin/env python3
"""
Validation rapide sur 30 matchs avec système de grading
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import accuracy_score

from src.utils.monitoring import get_logger
from src.ml.pipeline.smart_filter import SmartPredictionFilter

logger = get_logger(__name__)


def validate_on_recent_matches(n_matches=30):
    """Valide sur les N derniers matchs de 2025-26"""
    logger.info(f"Validation sur {n_matches} matchs récents...")
    
    # Charger données
    df = pd.read_parquet("data/gold/ml_features/features_2025-26_v3.parquet")
    df['game_date'] = pd.to_datetime(df['game_date'])
    df = df.sort_values('game_date')
    
    # Prendre les N derniers
    test_df = df.tail(n_matches)
    logger.info(f"Période test: {test_df['game_date'].min()} à {test_df['game_date'].max()}")
    
    # Charger modèle
    model_path = Path("models/unified/xgb_unified_latest.joblib")
    if not model_path.exists():
        logger.error("Modèle non trouvé")
        return
    
    model = joblib.load(model_path)
    
    # Préparer features
    exclude = ['game_id', 'game_date', 'season', 'target', 'home_team_id', 'away_team_id']
    feature_cols = [c for c in df.columns if c not in exclude and df[c].dtype in ['float64', 'int64']]
    feature_cols = [c for c in feature_cols if df[c].isna().sum() / len(df) < 0.3]
    
    X = test_df[feature_cols].fillna(test_df[feature_cols].median())
    y_true = test_df['target']
    
    # Prédire
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)[:, 1]
    
    # Calculer accuracy
    accuracy = accuracy_score(y_true, y_pred)
    logger.info(f"Accuracy globale: {accuracy:.2%}")
    
    # Analyser par confiance
    results = pd.DataFrame({
        'actual': y_true,
        'predicted': y_pred,
        'confidence': np.maximum(y_proba, 1-y_proba),
        'correct': y_pred == y_true
    })
    
    # Par niveau de confiance
    for threshold in [0.65, 0.70, 0.75]:
        high_conf = results[results['confidence'] >= threshold]
        if len(high_conf) > 0:
            acc = high_conf['correct'].mean()
            n = len(high_conf)
            logger.info(f"Confiance ≥{threshold:.0%}: {acc:.2%} accuracy ({n} matchs)")
    
    return accuracy, results


if __name__ == "__main__":
    acc, results = validate_on_recent_matches(30)
    print(f"\nValidation terminée: {acc:.2%} accuracy")
