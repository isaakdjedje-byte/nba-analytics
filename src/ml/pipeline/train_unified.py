#!/usr/bin/env python3
"""
Entraînement Unifié - Combine historique et live

Combine les données historiques (2018-2025) avec les données live (2025-26)
pour entraîner un modèle unique et plus performant.

Usage:
    python src/ml/pipeline/train_unified.py
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
import numpy as np
import joblib
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, brier_score_loss
from sklearn.calibration import CalibratedClassifierCV

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedTrainer:
    """
    Entraîne un modèle unifié sur toutes les saisons disponibles.
    """
    
    def __init__(self, 
                 hist_path: str = "data/gold/ml_features/features_v3.parquet",
                 live_path: str = "data/gold/ml_features/features_2025-26_v3.parquet",
                 output_dir: str = "models/unified"):
        self.hist_path = Path(hist_path)
        self.live_path = Path(live_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.df_combined = None
        self.selected_features = []
        self.models = {}
        self.results = {}
        
    def load_and_combine_data(self):
        """Charge et combine les données historiques et live."""
        logger.info("="*70)
        logger.info("CHARGEMENT ET COMBINAISON DES DONNÉES")
        logger.info("="*70)
        
        # Charger historique
        logger.info("\n[1/3] Chargement données historiques...")
        df_hist = pd.read_parquet(self.hist_path)
        logger.info(f"  ✓ Historique: {len(df_hist)} matchs")
        logger.info(f"    Saisons: {sorted(df_hist['season'].unique())}")
        
        # Charger live
        logger.info("\n[2/3] Chargement données live 2025-26...")
        df_live = pd.read_parquet(self.live_path)
        logger.info(f"  ✓ Live: {len(df_live)} matchs")
        logger.info(f"    Saison: {df_live['season'].unique()}")
        
        # Vérifier les colonnes
        hist_cols = set(df_hist.columns)
        live_cols = set(df_live.columns)
        common_cols = hist_cols & live_cols
        
        logger.info(f"\n[3/3] Alignement des colonnes...")
        logger.info(f"  Colonnes historique: {len(hist_cols)}")
        logger.info(f"  Colonnes live: {len(live_cols)}")
        logger.info(f"  Colonnes communes: {len(common_cols)}")
        
        # Garder uniquement les colonnes communes
        df_hist_aligned = df_hist[list(common_cols)].copy()
        df_live_aligned = df_live[list(common_cols)].copy()
        
        # Combiner
        self.df_combined = pd.concat([df_hist_aligned, df_live_aligned], ignore_index=True)
        self.df_combined['game_date'] = pd.to_datetime(self.df_combined['game_date'])
        self.df_combined = self.df_combined.sort_values('game_date')
        
        logger.info(f"\n✓ Dataset combiné: {len(self.df_combined)} matchs")
        logger.info(f"  - Historique: {len(df_hist)}")
        logger.info(f"  - Live: {len(df_live)}")
        
        return self.df_combined
    
    def load_selected_features(self):
        """Charge les features sélectionnées par le modèle optimisé."""
        logger.info("\n" + "="*70)
        logger.info("CHARGEMENT DES FEATURES SÉLECTIONNÉES")
        logger.info("="*70)
        
        features_file = Path("models/optimized/selected_features.json")
        if features_file.exists():
            with open(features_file, 'r') as f:
                data = json.load(f)
                self.selected_features = data['features']
            logger.info(f"✓ {len(self.selected_features)} features chargées")
            logger.info(f"  Top 5: {', '.join(self.selected_features[:5])}")
        else:
            # Fallback: utiliser toutes les features sauf metadata
            exclude_cols = [
                'game_id', 'season', 'game_date', 'season_type',
                'home_team_id', 'away_team_id', 'target',
                'home_score', 'away_score', 'point_diff'
            ]
            self.selected_features = [c for c in self.df_combined.columns if c not in exclude_cols]
            logger.info(f"⚠️ Fichier non trouvé, utilisation de {len(self.selected_features)} features")
        
        return self.selected_features
    
    def prepare_splits(self):
        """Prépare les splits train/test temporels."""
        logger.info("\n" + "="*70)
        logger.info("PRÉPARATION DES SPLITS")
        logger.info("="*70)
        
        # Validation croisée temporelle
        # Train: 2018-19 à 2023-24
        # Test: 2024-25 et 2025-26
        test_seasons = ['2024-25', '2025-26']
        
        train_mask = ~self.df_combined['season'].isin(test_seasons)
        test_mask = self.df_combined['season'].isin(test_seasons)
        
        X_train = self.df_combined.loc[train_mask, self.selected_features]
        y_train = self.df_combined.loc[train_mask, 'target']
        X_test = self.df_combined.loc[test_mask, self.selected_features]
        y_test = self.df_combined.loc[test_mask, 'target']
        
        logger.info(f"✓ Train: {len(X_train)} matchs ({min(self.df_combined[train_mask]['season'])} - {max(self.df_combined[train_mask]['season'])})")
        logger.info(f"✓ Test: {len(X_test)} matchs ({min(self.df_combined[test_mask]['season'])} - {max(self.df_combined[test_mask]['season'])})")
        
        return X_train, y_train, X_test, y_test
    
    def train_xgboost(self, X_train, y_train, X_test, y_test):
        """Entraîne le modèle XGBoost."""
        logger.info("\n" + "="*70)
        logger.info("ENTRAÎNEMENT XGBOOST")
        logger.info("="*70)
        
        # Hyperparamètres optimisés
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
            n_jobs=-1,
            eval_metric='logloss'
        )
        
        logger.info("Entraînement en cours...")
        xgb_model.fit(X_train, y_train)
        
        # Prédictions
        y_pred = xgb_model.predict(X_test)
        y_proba = xgb_model.predict_proba(X_test)[:, 1]
        
        # Métriques
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        auc = roc_auc_score(y_test, y_proba)
        
        self.models['xgb'] = xgb_model
        self.results['xgb'] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'auc': auc
        }
        
        logger.info(f"\n✓ Entraînement terminé")
        logger.info(f"  Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
        logger.info(f"  Precision: {precision:.4f}")
        logger.info(f"  Recall: {recall:.4f}")
        logger.info(f"  F1: {f1:.4f}")
        logger.info(f"  AUC: {auc:.4f}")
        
        return xgb_model, self.results['xgb']
    
    def calibrate_model(self, X_calib, y_calib):
        """Calibre les probabilités du modèle."""
        logger.info("\n" + "="*70)
        logger.info("CALIBRATION DES PROBABILITÉS")
        logger.info("="*70)
        
        xgb_model = self.models['xgb']
        
        # Calibration isotonique avec cv=3 (car cv='prefit' non supporte dans cette version)
        calibrated = CalibratedClassifierCV(
            xgb_model, 
            method='isotonic',
            cv=3
        )
        
        logger.info("Calibration...")
        calibrated.fit(X_calib, y_calib)
        
        # Sauvegarder le calibrateur
        self.models['xgb_calibrated'] = calibrated
        
        logger.info("✓ Calibration terminée")
        
        return calibrated
    
    def save_models(self):
        """Sauvegarde les modèles et métadonnées."""
        logger.info("\n" + "="*70)
        logger.info("SAUVEGARDE DES MODÈLES")
        logger.info("="*70)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Sauvegarder modèle XGBoost
        xgb_path = self.output_dir / f'xgb_unified_{timestamp}.joblib'
        joblib.dump(self.models['xgb'], xgb_path)
        logger.info(f"✓ Modèle XGBoost: {xgb_path}")
        
        # Sauvegarder modèle calibré
        if 'xgb_calibrated' in self.models:
            calib_path = self.output_dir / f'xgb_unified_calibrated_{timestamp}.joblib'
            joblib.dump(self.models['xgb_calibrated'], calib_path)
            logger.info(f"✓ Modèle calibré: {calib_path}")
        
        # Sauvegarder métadonnées
        metadata = {
            'created_at': datetime.now().isoformat(),
            'total_matches': len(self.df_combined),
            'train_matches': len(self.df_combined[~self.df_combined['season'].isin(['2024-25', '2025-26'])]),
            'test_matches': len(self.df_combined[self.df_combined['season'].isin(['2024-25', '2025-26'])]),
            'features_used': len(self.selected_features),
            'feature_names': self.selected_features,
            'results': {k: float(v) if isinstance(v, (np.floating, float)) else v 
                       for k, v in self.results['xgb'].items()},
            'model_paths': {
                'xgb': str(xgb_path),
                'calibrated': str(calib_path) if 'xgb_calibrated' in self.models else None
            }
        }
        
        metadata_path = self.output_dir / f'metadata_unified_{timestamp}.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"✓ Métadonnées: {metadata_path}")
        
        # Sauvegarder également sous un nom fixe pour référence facile
        latest_path = self.output_dir / 'xgb_unified_latest.joblib'
        joblib.dump(self.models['xgb'], latest_path)
        logger.info(f"✓ Modèle latest: {latest_path}")
        
        return metadata
    
    def run(self):
        """Exécute le pipeline complet d'entraînement."""
        logger.info("\n" + "="*70)
        logger.info("ENTRAÎNEMENT UNIFIÉ - NBA ANALYTICS")
        logger.info("="*70)
        
        # Étape 1: Charger et combiner
        self.load_and_combine_data()
        
        # Étape 2: Charger features sélectionnées
        self.load_selected_features()
        
        # Étape 3: Préparer splits
        X_train, y_train, X_test, y_test = self.prepare_splits()
        
        # Étape 4: Entraîner
        self.train_xgboost(X_train, y_train, X_test, y_test)
        
        # Étape 5: Calibrer (sur une partie du test)
        calib_mask = self.df_combined['season'] == '2024-25'
        if calib_mask.sum() > 100:
            X_calib = self.df_combined.loc[calib_mask, self.selected_features]
            y_calib = self.df_combined.loc[calib_mask, 'target']
            self.calibrate_model(X_calib, y_calib)
        
        # Étape 6: Sauvegarder
        metadata = self.save_models()
        
        # Résumé final
        logger.info("\n" + "="*70)
        logger.info("RÉSULTATS FINAUX")
        logger.info("="*70)
        logger.info(f"✓ Dataset: {metadata['total_matches']} matchs")
        logger.info(f"  - Entraînement: {metadata['train_matches']}")
        logger.info(f"  - Test: {metadata['test_matches']}")
        logger.info(f"✓ Features: {metadata['features_used']}")
        logger.info(f"✓ Accuracy: {metadata['results']['accuracy']:.4f} ({metadata['results']['accuracy']*100:.2f}%)")
        
        # Comparaison
        baseline = 0.5479  # Ancien système fallback
        improvement = metadata['results']['accuracy'] - baseline
        logger.info(f"\n📊 Comparaison:")
        logger.info(f"  Baseline (fallback): {baseline:.4f} ({baseline*100:.2f}%)")
        logger.info(f"  Nouveau (unifié): {metadata['results']['accuracy']:.4f} ({metadata['results']['accuracy']*100:.2f}%)")
        logger.info(f"  Amélioration: {improvement:+.4f} ({improvement*100:+.2f}%)")
        
        if metadata['results']['accuracy'] >= 0.70:
            logger.info(f"\n🎯 OBJECTIF 70% ATTEINT!")
        elif metadata['results']['accuracy'] >= 0.65:
            logger.info(f"\n⚠️ Proche de l'objectif (gap: {0.70 - metadata['results']['accuracy']:+.2%})")
        else:
            logger.info(f"\n❌ Objectif non atteint (gap: {0.70 - metadata['results']['accuracy']:+.2%})")
        
        logger.info("\n" + "="*70)
        
        return metadata


def main():
    """Point d'entrée principal."""
    trainer = UnifiedTrainer()
    results = trainer.run()
    
    print("\n" + "="*70)
    print("ENTRAÎNEMENT TERMINÉ")
    print("="*70)
    print(f"Accuracy: {results['results']['accuracy']*100:.2f}%")
    print(f"Modèle: {results['model_paths']['xgb']}")


if __name__ == '__main__':
    main()
