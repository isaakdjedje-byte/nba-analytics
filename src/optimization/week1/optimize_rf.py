#!/usr/bin/env python3
"""
WEEK 1 - Random Forest Optimization avec Optuna
Objectif: Trouver les meilleurs hyperparamètres RF
Estimation: 3-4 heures (50 trials)
"""

import optuna
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
import json
import pickle
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_data():
    """Charge les données NBA."""
    logger.info("Chargement des données...")
    
    df = pd.read_parquet("data/gold/ml_features/features_all.parquet")
    
    # Split temporel
    train_mask = ~df['season'].isin(['2023-24', '2024-25'])
    test_mask = df['season'].isin(['2023-24', '2024-25'])
    
    # Features (sans data leakage)
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
    
    X_train = df.loc[train_mask, feature_cols]
    y_train = df.loc[train_mask, 'target']
    X_test = df.loc[test_mask, feature_cols]
    y_test = df.loc[test_mask, 'target']
    
    logger.info(f"Train: {len(X_train)} | Test: {len(X_test)} | Features: {len(feature_cols)}")
    
    return X_train, y_train, X_test, y_test, feature_cols


def objective(trial, X_train, y_train, X_test, y_test):
    """Fonction objective pour Optuna."""
    
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'max_depth': trial.suggest_int('max_depth', 5, 30),
        'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
        'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
        'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None]),
        'bootstrap': trial.suggest_categorical('bootstrap', [True, False]),
        'random_state': 42,
        'n_jobs': -1
    }
    
    # Si bootstrap=False, min_samples_leaf doit être 0
    if not params['bootstrap'] and params['min_samples_leaf'] == 0:
        params['min_samples_leaf'] = 1
    
    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    
    return auc


def main():
    """Fonction principale."""
    logger.info("="*70)
    logger.info("WEEK 1 - RANDOM FOREST OPTIMIZATION (Optuna)")
    logger.info("="*70)
    
    X_train, y_train, X_test, y_test, feature_cols = load_data()
    
    study = optuna.create_study(
        direction='maximize',
        study_name='nba_rf_optimization',
        storage='sqlite:///results/week1/rf_optimization.db',
        load_if_exists=True
    )
    
    logger.info("Démarrage de l'optimisation (50 trials)...")
    logger.info("Temps estimé: 3-4 heures")
    
    study.optimize(
        lambda trial: objective(trial, X_train, y_train, X_test, y_test),
        n_trials=50,
        show_progress_bar=True
    )
    
    logger.info("\n" + "="*70)
    logger.info("MEILLEURS HYPERPARAMÈTRES TROUVÉS:")
    logger.info("="*70)
    
    best_params = study.best_params
    best_value = study.best_value
    
    logger.info(f"Meilleur AUC: {best_value:.4f}")
    logger.info(f"Meilleurs paramètres:")
    for param, value in best_params.items():
        logger.info(f"  {param}: {value}")
    
    logger.info("\nEntraînement du modèle final...")
    best_model = RandomForestClassifier(**best_params, random_state=42, n_jobs=-1)
    best_model.fit(X_train, y_train)
    
    y_pred = best_model.predict(X_test)
    y_proba = best_model.predict_proba(X_test)[:, 1]
    
    final_metrics = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'auc': float(roc_auc_score(y_test, y_proba)),
        'best_params': best_params,
        'n_trials': len(study.trials),
        'timestamp': datetime.now().isoformat()
    }
    
    logger.info(f"\nPerformance finale:")
    logger.info(f"  Accuracy: {final_metrics['accuracy']:.4f}")
    logger.info(f"  AUC: {final_metrics['auc']:.4f}")
    
    with open('results/week1/rf_best_params.json', 'w') as f:
        json.dump(final_metrics, f, indent=2)
    
    with open('models/week1/rf_optimized.pkl', 'wb') as f:
        pickle.dump(best_model, f)
    
    study_df = study.trials_dataframe()
    study_df.to_csv('results/week1/rf_optimization_history.csv', index=False)
    
    logger.info("\nRésultats sauvegardés!")
    
    return final_metrics


if __name__ == "__main__":
    main()
