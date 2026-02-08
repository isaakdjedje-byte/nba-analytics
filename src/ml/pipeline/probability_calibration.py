"""
NBA-22 Optimization: Probability Calibration Module
Calibrates model probabilities using Isotonic Regression and Platt Scaling
"""

import numpy as np
import pandas as pd
import joblib
import json
from pathlib import Path
from sklearn.calibration import IsotonicRegression, CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ProbabilityCalibrator:
    """
    Calibre les probabilités des modèles ML pour les rendre fiables pour les paris.
    
    Problème actuel: Si le modèle prédit 80% de confiance, il ne gagne pas 80% du temps.
    Solution: Calibrer pour que proba=0.8 => 80% de win rate réel.
    
    Méthodes:
    - Isotonic Regression (recommandée pour données non linéaires)
    - Platt Scaling (sigmoïde paramétrique)
    """
    
    def __init__(self, method='isotonic'):
        self.method = method
        self.calibrator = None
        self.calibration_data = []
        self.is_fitted = False
        
    def fit(self, y_true, y_proba):
        """
        Entraîne le calibrateur sur les données de validation.
        
        Args:
            y_true: Labels réels (0 ou 1)
            y_proba: Probabilités prédites par le modèle
        """
        logger.info(f"Entraînement du calibrateur ({self.method})...")
        
        if self.method == 'isotonic':
            self.calibrator = IsotonicRegression(out_of_bounds='clip')
            self.calibrator.fit(y_proba, y_true)
        elif self.method == 'platt':
            # Platt scaling = logistic regression on probabilities
            self.calibrator = LogisticRegression(C=1e10, solver='lbfgs')
            self.calibrator.fit(y_proba.reshape(-1, 1), y_true)
        else:
            raise ValueError(f"Méthode inconnue: {self.method}")
        
        self.is_fitted = True
        
        # Stocker les données pour analyse
        self.calibration_data = {
            'y_true': y_true.tolist(),
            'y_proba_original': y_proba.tolist(),
            'y_proba_calibrated': self.predict(y_proba).tolist()
        }
        
        logger.info(f"✅ Calibrateur entraîné sur {len(y_true)} échantillons")
        
    def predict(self, y_proba):
        """
        Calibre les probabilités.
        
        Args:
            y_proba: Probabilités brutes du modèle
            
        Returns:
            Probabilités calibrées
        """
        if not self.is_fitted:
            raise ValueError("Calibrateur non entraîné. Appelez fit() d'abord.")
        
        if self.method == 'isotonic':
            return self.calibrator.predict(y_proba)
        elif self.method == 'platt':
            return self.calibrator.predict_proba(y_proba.reshape(-1, 1))[:, 1]
        
    def evaluate_calibration(self, y_true, y_proba_original, y_proba_calibrated=None):
        """
        Évalue la qualité de la calibration avec le Brier score.
        
        Returns:
            Dict avec les métriques de calibration
        """
        from sklearn.metrics import brier_score_loss
        
        if y_proba_calibrated is None:
            y_proba_calibrated = self.predict(y_proba_original)
        
        # Brier score (plus petit = mieux)
        brier_original = brier_score_loss(y_true, y_proba_original)
        brier_calibrated = brier_score_loss(y_true, y_proba_calibrated)
        
        # Reliability diagram bins
        bins = np.linspace(0, 1, 11)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        results = {
            'brier_score_original': float(brier_original),
            'brier_score_calibrated': float(brier_calibrated),
            'brier_improvement': float(brier_original - brier_calibrated),
            'n_samples': len(y_true),
            'method': self.method
        }
        
        # Reliability par bin
        for proba_type, proba_vals in [('original', y_proba_original), ('calibrated', y_proba_calibrated)]:
            bin_accuracies = []
            bin_confidences = []
            bin_counts = []
            
            for i in range(len(bins) - 1):
                mask = (proba_vals >= bins[i]) & (proba_vals < bins[i+1])
                if i == len(bins) - 2:  # Last bin includes 1.0
                    mask = (proba_vals >= bins[i]) & (proba_vals <= bins[i+1])
                
                if mask.sum() > 0:
                    bin_acc = y_true[mask].mean()
                    bin_conf = proba_vals[mask].mean()
                    bin_accuracies.append(bin_acc)
                    bin_confidences.append(bin_conf)
                    bin_counts.append(int(mask.sum()))
                else:
                    bin_accuracies.append(None)
                    bin_confidences.append(None)
                    bin_counts.append(0)
            
            results[f'{proba_type}_bin_accuracies'] = bin_accuracies
            results[f'{proba_type}_bin_confidences'] = bin_confidences
            results[f'{proba_type}_bin_counts'] = bin_counts
        
        return results
    
    def save(self, filepath):
        """Sauvegarde le calibrateur."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            'calibrator': self.calibrator,
            'method': self.method,
            'is_fitted': self.is_fitted,
            'calibration_data': self.calibration_data
        }, filepath)
        logger.info(f"✅ Calibrateur sauvegardé: {filepath}")
        
    def load(self, filepath):
        """Charge le calibrateur."""
        data = joblib.load(filepath)
        self.calibrator = data['calibrator']
        self.method = data['method']
        self.is_fitted = data['is_fitted']
        self.calibration_data = data['calibration_data']
        logger.info(f"✅ Calibrateur chargé: {filepath}")


def calibrate_model(model_path, data_path, output_path=None, method='isotonic', test_size=0.2):
    """
    Pipeline complet de calibration d'un modèle.
    
    Args:
        model_path: Chemin vers le modèle joblib
        data_path: Chemin vers les données features parquet
        output_path: Où sauvegarder le calibrateur
        method: 'isotonic' ou 'platt'
        test_size: Proportion pour validation
        
    Returns:
        Dict avec les résultats de calibration
    """
    logger.info("="*70)
    logger.info("CALIBRATION DES PROBABILITÉS")
    logger.info("="*70)
    
    # Charger le modèle
    model = joblib.load(model_path)
    logger.info(f"Modèle chargé: {model_path}")
    
    # Charger les données
    df = pd.read_parquet(data_path)
    df['game_date'] = pd.to_datetime(df['game_date'])
    df = df.sort_values('game_date')
    
    # Split temporel
    split_idx = int(len(df) * (1 - test_size))
    train_df = df.iloc[:split_idx]
    val_df = df.iloc[split_idx:]
    
    # Colonnes features (mêmes que dans nba22_train.py)
    exclude_cols = [
        'game_id', 'season', 'game_date', 'season_type',
        'home_team_id', 'away_team_id', 'target',
        'home_score', 'away_score', 'point_diff',
        'home_reb', 'home_ast', 'home_stl', 'home_blk', 'home_tov', 'home_pf',
        'away_reb', 'away_ast', 'away_stl', 'away_blk', 'away_tov', 'away_pf',
        'home_ts_pct', 'home_efg_pct', 'home_game_score', 'home_fatigue_eff',
        'away_ts_pct', 'away_efg_pct', 'away_game_score', 'away_fatigue_eff',
        'ts_pct_diff'
    ]
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    # Prédictions sur validation
    X_val = val_df[feature_cols]
    y_val = val_df['target'].values
    y_proba = model.predict_proba(X_val)[:, 1]
    
    logger.info(f"Données: {len(train_df)} train, {len(val_df)} validation")
    logger.info(f"Features: {len(feature_cols)}")
    
    # Entraîner calibrateur
    calibrator = ProbabilityCalibrator(method=method)
    calibrator.fit(y_val, y_proba)
    
    # Évaluer
    y_proba_calibrated = calibrator.predict(y_proba)
    eval_results = calibrator.evaluate_calibration(y_val, y_proba, y_proba_calibrated)
    
    logger.info(f"\nRésultats de calibration:")
    logger.info(f"  Brier score original:    {eval_results['brier_score_original']:.4f}")
    logger.info(f"  Brier score calibré:     {eval_results['brier_score_calibrated']:.4f}")
    logger.info(f"  Amélioration:            {eval_results['brier_improvement']:.4f}")
    
    # Sauvegarder
    if output_path:
        calibrator.save(output_path)
        
        # Sauvegarder aussi le rapport JSON
        report_path = Path(output_path).with_suffix('.json')
        with open(report_path, 'w') as f:
            json.dump(eval_results, f, indent=2)
        logger.info(f"Rapport sauvegardé: {report_path}")
    
    return {
        'calibrator': calibrator,
        'eval_results': eval_results,
        'output_path': output_path
    }


def apply_calibration_to_predictions(predictions_df, calibrator_path):
    """
    Applique la calibration aux prédictions existantes.
    
    Args:
        predictions_df: DataFrame avec colonne 'proba_home_win'
        calibrator_path: Chemin vers le calibrateur sauvegardé
        
    Returns:
        DataFrame avec colonnes 'proba_home_win_calibrated' et 'confidence_calibrated'
    """
    calibrator = ProbabilityCalibrator()
    calibrator.load(calibrator_path)
    
    df = predictions_df.copy()
    df['proba_home_win_calibrated'] = calibrator.predict(df['proba_home_win'].values)
    df['confidence_calibrated'] = df['proba_home_win_calibrated'].apply(lambda x: max(x, 1-x))
    
    # Mettre à jour la recommandation
    def get_recommendation(conf):
        if conf >= 0.70:
            return "HIGH_CONFIDENCE"
        elif conf >= 0.60:
            return "MEDIUM_CONFIDENCE"
        elif conf >= 0.55:
            return "LOW_CONFIDENCE"
        else:
            return "SKIP"
    
    df['recommendation_calibrated'] = df['confidence_calibrated'].apply(get_recommendation)
    
    return df


if __name__ == '__main__':
    # Exemple d'utilisation
    logger.info("Calibration des probabilités pour XGBoost V3")
    
    results = calibrate_model(
        model_path="models/week1/xgb_v3.pkl",
        data_path="data/gold/ml_features/features_v3.parquet",
        output_path="models/week1/calibrator_xgb_v3.joblib",
        method='isotonic'
    )
    
    logger.info("\n✅ Calibration terminée!")
