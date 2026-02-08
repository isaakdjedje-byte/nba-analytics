#!/usr/bin/env python3
"""
Smart Ensemble - Selection dynamique du meilleur modele

Analyse montre que correlation erreurs RF/XGB = 0.885 (trop elevee)
-> Stacking traditionnel inutile
-> Solution: Selection dynamique basee sur confidence
"""

import joblib
import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SmartEnsemble:
    """
    Ensemble intelligent qui selectionne le meilleur modele
    pour chaque prediction base sur la confidence.
    
    Strategie:
    1. Si un modele a confidence > 0.8 et l'autre < 0.6 -> Choisir le confiant
    2. Si les deux sont proches -> Moyenne ponderee par accuracy historique
    3. Si desaccord fort -> Abstention ou modele le plus fiable (XGB)
    """
    
    def __init__(self, models_dir: str = "models/week1"):
        self.models_dir = Path(models_dir)
        self.rf = None
        self.xgb = None
        self.rf_weight = 0.48  # Poids base sur accuracy relative
        self.xgb_weight = 0.52
        self.confidence_threshold_high = 0.75
        self.confidence_threshold_low = 0.55
        
    def load_models(self):
        """Charge les modeles optimises."""
        logger.info("Chargement des modeles...")
        self.rf = joblib.load(self.models_dir / "rf_optimized.pkl")
        self.xgb = joblib.load(self.models_dir / "xgb_optimized.pkl")
        logger.info("[OK] Modeles charges")
        
    def predict_smart(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """
        Prediction intelligente avec selection dynamique.
        
        Returns:
            predictions: Array de predictions (0/1)
            probabilities: Array de probabilites
            meta_info: Dict avec info sur la strategie utilisee
        """
        # Probabilites de chaque modele
        rf_proba = self.rf.predict_proba(X)[:, 1]
        xgb_proba = self.xgb.predict_proba(X)[:, 1]
        
        # Confidence = distance a 0.5
        rf_conf = np.abs(rf_proba - 0.5) * 2
        xgb_conf = np.abs(xgb_proba - 0.5) * 2
        
        predictions = np.zeros(len(X))
        probabilities = np.zeros(len(X))
        strategies = []
        
        for i in range(len(X)):
            r_conf = rf_conf[i]
            x_conf = xgb_conf[i]
            r_prob = rf_proba[i]
            x_prob = xgb_proba[i]
            
            # Strategie 1: Un modele tres confiant, l'autre non
            if r_conf > self.confidence_threshold_high and x_conf < self.confidence_threshold_low:
                # RF confiant, XGB pas sur -> Choisir RF
                predictions[i] = 1 if r_prob > 0.5 else 0
                probabilities[i] = r_prob
                strategies.append('rf_confident')
                
            elif x_conf > self.confidence_threshold_high and r_conf < self.confidence_threshold_low:
                # XGB confiant, RF pas sur -> Choisir XGB
                predictions[i] = 1 if x_prob > 0.5 else 0
                probabilities[i] = x_prob
                strategies.append('xgb_confident')
                
            # Strategie 2: Les deux sont d'accord
            elif (r_prob > 0.5 and x_prob > 0.5) or (r_prob < 0.5 and x_prob < 0.5):
                # Moyenne ponderee
                prob = (self.rf_weight * r_prob + self.xgb_weight * x_prob)
                predictions[i] = 1 if prob > 0.5 else 0
                probabilities[i] = prob
                strategies.append('weighted_agree')
                
            # Strategie 3: Desaccord - Choisir XGB (meilleur historique)
            else:
                predictions[i] = 1 if x_prob > 0.5 else 0
                probabilities[i] = x_prob
                strategies.append('xgb_disagree')
        
        meta_info = {
            'strategies': strategies,
            'strategy_counts': {
                'rf_confident': strategies.count('rf_confident'),
                'xgb_confident': strategies.count('xgb_confident'),
                'weighted_agree': strategies.count('weighted_agree'),
                'xgb_disagree': strategies.count('xgb_disagree')
            }
        }
        
        return predictions.astype(int), probabilities, meta_info
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
        """Evalue l'ensemble sur le test set."""
        logger.info("Evaluation du Smart Ensemble...")
        
        # Smart predictions
        smart_pred, smart_proba, meta = self.predict_smart(X_test)
        smart_acc = (smart_pred == y_test).mean()
        
        # Comparaisons
        rf_pred = self.rf.predict(X_test)
        xgb_pred = self.xgb.predict(X_test)
        voting_pred = ((self.rf.predict_proba(X_test)[:, 1] + 
                       self.xgb.predict_proba(X_test)[:, 1]) / 2 > 0.5).astype(int)
        
        rf_acc = (rf_pred == y_test).mean()
        xgb_acc = (xgb_pred == y_test).mean()
        voting_acc = (voting_pred == y_test).mean()
        
        results = {
            'smart_ensemble': float(smart_acc),
            'rf': float(rf_acc),
            'xgb': float(xgb_acc),
            'voting': float(voting_acc),
            'strategies': meta['strategy_counts'],
            'improvement_over_xgb': float(smart_acc - xgb_acc),
            'improvement_over_voting': float(smart_acc - voting_acc)
        }
        
        return results


def main():
    """Test du Smart Ensemble."""
    logger.info("=== SMART ENSEMBLE - Test ===\n")
    
    # Charger données
    df = pd.read_parquet("data/gold/ml_features/features_all.parquet")
    test_mask = df['season'].isin(['2023-24', '2024-25'])
    
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
    
    # Creer et evaluer
    ensemble = SmartEnsemble()
    ensemble.load_models()
    results = ensemble.evaluate(X_test, y_test)
    
    # Affichage
    print("\n[RESULTATS]")
    print(f"  Smart Ensemble: {results['smart_ensemble']:.4f} ({results['smart_ensemble']*100:.2f}%)")
    print(f"  XGB (best solo): {results['xgb']:.4f} ({results['xgb']*100:.2f}%)")
    print(f"  Voting simple:   {results['voting']:.4f} ({results['voting']*100:.2f}%)")
    print(f"\n[GAINS]")
    print(f"  vs XGB:    {results['improvement_over_xgb']:+.4f} ({results['improvement_over_xgb']*100:+.2f}%)")
    print(f"  vs Voting: {results['improvement_over_voting']:+.4f} ({results['improvement_over_voting']*100:+.2f}%)")
    print(f"\n[STRATEGIES UTILISEES]")
    for strategy, count in results['strategies'].items():
        pct = count / len(y_test) * 100
        print(f"  {strategy}: {count} ({pct:.1f}%)")
    
    # Sauvegarder
    with open('results/week1/smart_ensemble_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n[SAVED] Resultats sauvegardes")
    
    # Sauvegarder le modele
    output_dir = Path('models/week1')
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(ensemble, output_dir / 'smart_ensemble.pkl')
    print(f"[SAVED] Smart Ensemble sauvegarde dans models/week1/smart_ensemble.pkl")


if __name__ == '__main__':
    main()
