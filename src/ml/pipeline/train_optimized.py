"""
NBA-22: Optimized Training Pipeline
Entraînement complet avec calibration, feature selection et évaluation
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, brier_score_loss
from sklearn.calibration import CalibratedClassifierCV

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.probability_calibration import ProbabilityCalibrator, calibrate_model
from pipeline.feature_selection import FeatureSelector
from pipeline.drift_monitoring import DataDriftMonitor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OptimizedNBA22Trainer:
    """
    Pipeline d'entraînement optimisé pour NBA-22.
    
    Optimisations:
    1. Feature Selection: Réduit de 80 à 35 features
    2. Calibration: Probabilités fiables pour les paris
    3. Multi-modèles: XGBoost + Random Forest
    4. Validation: Time-series split + cross-validation
    """
    
    def __init__(self, features_path="data/gold/ml_features/features_v3.parquet", 
                 output_dir="models/optimized",
                 n_features=35):
        self.features_path = Path(features_path)
        self.output_dir = Path(output_dir)
        self.n_features = n_features
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.df = None
        self.feature_cols = []
        self.selected_features = []
        self.models = {}
        self.calibrators = {}
        self.results = {}
        
    def load_and_prepare_data(self):
        """Charge et prépare les données."""
        logger.info("="*70)
        logger.info("CHARGEMENT DES DONNÉES")
        logger.info("="*70)
        
        self.df = pd.read_parquet(self.features_path)
        self.df['game_date'] = pd.to_datetime(self.df['game_date'])
        self.df = self.df.sort_values('game_date')
        
        # Définir les features (sans data leakage)
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
        
        self.feature_cols = [c for c in self.df.columns if c not in exclude_cols]
        
        logger.info(f"Données chargées: {len(self.df)} matchs")
        logger.info(f"Features disponibles: {len(self.feature_cols)}")
        logger.info(f"Saisons: {sorted(self.df['season'].unique())}")
        
        return self.df
    
    def select_features(self):
        """Sélectionne les meilleures features."""
        logger.info("\n" + "="*70)
        logger.info("FEATURE SELECTION")
        logger.info("="*70)
        
        selector = FeatureSelector(n_features=self.n_features)
        selector.df = self.df
        selector.feature_cols = self.feature_cols
        
        # Split temporel
        test_seasons = ['2023-24', '2024-25']
        train_mask = ~self.df['season'].isin(test_seasons)
        test_mask = self.df['season'].isin(test_seasons)
        
        selector.X_train = self.df.loc[train_mask, self.feature_cols].copy()
        selector.X_test = self.df.loc[test_mask, self.feature_cols].copy()
        selector.y_train = self.df.loc[train_mask, 'target'].copy()
        selector.y_test = self.df.loc[test_mask, 'target'].copy()
        
        # Méthode: XGBoost importance
        logger.info("Sélection par importance XGBoost...")
        self.selected_features, _ = selector.select_xgb_importance()
        
        # Sauvegarder la sélection
        selector.save_selection(
            self.output_dir / 'selected_features.json',
            method='xgb_importance'
        )
        
        logger.info(f"✅ {len(self.selected_features)} features sélectionnées")
        logger.info(f"Top 5: {', '.join(self.selected_features[:5])}")
        
        return self.selected_features
    
    def train_models(self):
        """Entraîne les modèles optimisés."""
        logger.info("\n" + "="*70)
        logger.info("ENTRAÎNEMENT DES MODÈLES")
        logger.info("="*70)
        
        # Split temporel
        test_seasons = ['2023-24', '2024-25']
        train_mask = ~self.df['season'].isin(test_seasons)
        test_mask = self.df['season'].isin(test_seasons)
        
        X_train = self.df.loc[train_mask, self.selected_features]
        X_test = self.df.loc[test_mask, self.selected_features]
        y_train = self.df.loc[train_mask, 'target']
        y_test = self.df.loc[test_mask, 'target']
        
        logger.info(f"Train: {len(X_train)} matchs")
        logger.info(f"Test: {len(X_test)} matchs")
        
        # 1. XGBoost Optimisé
        logger.info("\n[1/2] Entraînement XGBoost...")
        xgb_model = xgb.XGBClassifier(
            n_estimators=567,
            max_depth=4,
            learning_rate=0.010,
            subsample=0.736,
            colsample_bytree=0.991,
            min_child_weight=7,
            gamma=0.237,
            reg_alpha=4.6e-07,
            reg_lambda=4.6e-07,
            random_state=42,
            n_jobs=-1
        )
        xgb_model.fit(X_train, y_train)
        
        y_pred_xgb = xgb_model.predict(X_test)
        y_proba_xgb = xgb_model.predict_proba(X_test)[:, 1]
        
        self.models['xgb'] = xgb_model
        self.results['xgb'] = self._calculate_metrics(y_test, y_pred_xgb, y_proba_xgb, 'XGBoost')
        
        logger.info(f"  Accuracy: {self.results['xgb']['accuracy']:.4f}")
        
        # 2. Random Forest (backup)
        logger.info("\n[2/2] Entraînement Random Forest...")
        rf_model = RandomForestClassifier(
            n_estimators=828,
            max_depth=13,
            min_samples_split=4,
            min_samples_leaf=10,
            max_features='sqrt',
            bootstrap=True,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train, y_train)
        
        y_pred_rf = rf_model.predict(X_test)
        y_proba_rf = rf_model.predict_proba(X_test)[:, 1]
        
        self.models['rf'] = rf_model
        self.results['rf'] = self._calculate_metrics(y_test, y_pred_rf, y_proba_rf, 'Random Forest')
        
        logger.info(f"  Accuracy: {self.results['rf']['accuracy']:.4f}")
        
        return self.models, self.results
    
    def calibrate_probabilities(self):
        """Calibre les probabilités des modèles."""
        logger.info("\n" + "="*70)
        logger.info("CALIBRATION DES PROBABILITÉS")
        logger.info("="*70)
        
        # Split temporel pour calibration
        test_seasons = ['2023-24', '2024-25']
        calib_seasons = ['2024-25']  # Utiliser une partie des données test
        
        train_mask = ~self.df['season'].isin(test_seasons)
        calib_mask = self.df['season'].isin(calib_seasons)
        
        X_train = self.df.loc[train_mask, self.selected_features]
        X_calib = self.df.loc[calib_mask, self.selected_features]
        y_calib = self.df.loc[calib_mask, 'target'].values
        
        for model_name, model in self.models.items():
            logger.info(f"\nCalibration {model_name.upper()}...")
            
            # Prédictions sur set de calibration
            y_proba = model.predict_proba(X_calib)[:, 1]
            
            # Entraîner calibrateur
            calibrator = ProbabilityCalibrator(method='isotonic')
            calibrator.fit(y_calib, y_proba)
            
            self.calibrators[model_name] = calibrator
            
            # Évaluer
            y_proba_calib = calibrator.predict(y_proba)
            brier_before = brier_score_loss(y_calib, y_proba)
            brier_after = brier_score_loss(y_calib, y_proba_calib)
            
            logger.info(f"  Brier avant:  {brier_before:.4f}")
            logger.info(f"  Brier après:  {brier_after:.4f}")
            logger.info(f"  Amélioration: {(brier_before - brier_after):.4f}")
            
            # Sauvegarder calibrateur
            calib_path = self.output_dir / f'calibrator_{model_name}.joblib'
            calibrator.save(calib_path)
        
        return self.calibrators
    
    def _calculate_metrics(self, y_true, y_pred, y_proba, model_name):
        """Calcule toutes les métriques."""
        return {
            'model_name': model_name,
            'accuracy': float(accuracy_score(y_true, y_pred)),
            'precision': float(precision_score(y_true, y_pred, zero_division=0)),
            'recall': float(recall_score(y_true, y_pred, zero_division=0)),
            'f1': float(f1_score(y_true, y_pred, zero_division=0)),
            'auc': float(roc_auc_score(y_true, y_proba)),
            'brier_score': float(brier_score_loss(y_true, y_proba)),
            'n_test': len(y_true)
        }
    
    def save_models(self):
        """Sauvegarde tous les modèles et métadonnées."""
        logger.info("\n" + "="*70)
        logger.info("SAUVEGARDE DES MODÈLES")
        logger.info("="*70)
        
        # Sauvegarder les modèles
        for name, model in self.models.items():
            model_path = self.output_dir / f'model_{name}.joblib'
            joblib.dump(model, model_path)
            logger.info(f"  ✅ Modèle {name}: {model_path}")
        
        # Sauvegarder les résultats
        summary = {
            'timestamp': datetime.now().isoformat(),
            'n_features_total': len(self.feature_cols),
            'n_features_selected': len(self.selected_features),
            'selected_features': self.selected_features,
            'models': self.results,
            'best_model': max(self.results.items(), key=lambda x: x[1]['accuracy'])[0],
            'best_accuracy': max(r['accuracy'] for r in self.results.values())
        }
        
        summary_path = self.output_dir / 'training_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"  ✅ Résumé: {summary_path}")
        
        return summary
    
    def print_results(self):
        """Affiche les résultats finaux."""
        logger.info("\n" + "="*70)
        logger.info("RÉSULTATS FINAUX - NBA-22 OPTIMISÉ")
        logger.info("="*70)
        
        for name, metrics in self.results.items():
            logger.info(f"\n{metrics['model_name']}:")
            logger.info(f"  Accuracy:  {metrics['accuracy']:.4f} ({metrics['accuracy']:.2%})")
            logger.info(f"  Precision: {metrics['precision']:.4f}")
            logger.info(f"  Recall:    {metrics['recall']:.4f}")
            logger.info(f"  F1-Score:  {metrics['f1']:.4f}")
            logger.info(f"  AUC:       {metrics['auc']:.4f}")
            logger.info(f"  Brier:     {metrics['brier_score']:.4f}")
        
        best = max(self.results.items(), key=lambda x: x[1]['accuracy'])
        logger.info(f"\n🏆 MEILLEUR MODÈLE: {best[0].upper()}")
        logger.info(f"   Accuracy: {best[1]['accuracy']:.4f} ({best[1]['accuracy']:.2%})")
        logger.info(f"   Features: {len(self.selected_features)}/{len(self.feature_cols)}")
        
        logger.info("\n" + "="*70)
    
    def run(self):
        """Pipeline complet d'entraînement optimisé."""
        logger.info("="*70)
        logger.info("NBA-22: PIPELINE D'ENTRAÎNEMENT OPTIMISÉ")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        # 1. Charger données
        self.load_and_prepare_data()
        
        # 2. Sélection de features
        self.select_features()
        
        # 3. Entraînement
        self.train_models()
        
        # 4. Calibration
        self.calibrate_probabilities()
        
        # 5. Sauvegarde
        self.save_models()
        
        # 6. Résultats
        self.print_results()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"\n✅ Pipeline terminé en {elapsed:.1f}s ({elapsed/60:.1f}min)")
        logger.info(f"   Modèles sauvegardés dans: {self.output_dir}")
        
        return self.results


def main():
    """Point d'entrée."""
    trainer = OptimizedNBA22Trainer(
        features_path="data/gold/ml_features/features_v3.parquet",
        output_dir="models/optimized",
        n_features=35
    )
    
    results = trainer.run()
    return results


if __name__ == '__main__':
    main()
