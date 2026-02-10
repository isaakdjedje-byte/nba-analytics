#!/usr/bin/env python3
"""
Backtest Hybride Master v2.0 - Avec VRAIES features 2025-26

Ce script remplace le fallback (moyennes 2024-25) par des features réelles
calculées en temps réel pour chaque match 2025-26.

Usage:
    python backtest_hybrid_master_v2.py --phase complete
"""

import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from nba.config import settings
from live_feature_engineer import LiveFeatureEngineer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HybridBacktesterV2:
    """Système de backtest avec vraies features 2025-26."""
    
    def __init__(self):
        self.model = None
        self.calibrator = None
        self.selected_features = None
        self.feature_engineer = None
        self._load_model()
        self._init_feature_engineer()
        
    def _load_model(self):
        """Charge le modèle optimisé."""
        logger.info("Chargement du modèle...")
        
        model_path = settings.model_xgb_path
        if Path(model_path).exists():
            self.model = joblib.load(model_path)
            logger.info(f"✓ Modèle chargé: {model_path}")
        else:
            logger.error(f"❌ Modèle non trouvé: {model_path}")
            
        # Charger calibrateur
        calib_path = settings.calibrator_xgb_path
        if Path(calib_path).exists():
            calib_data = joblib.load(calib_path)
            self.calibrator = calib_data.get('calibrator')
            logger.info("✓ Calibrateur chargé")
        
        # Charger features sélectionnées
        features_path = settings.selected_features_path
        if Path(features_path).exists():
            with open(features_path, 'r') as f:
                features_data = json.load(f)
                self.selected_features = features_data.get('features', [])
            logger.info(f"✓ {len(self.selected_features)} features sélectionnées")
    
    def _init_feature_engineer(self):
        """Initialise l'ingénieur de features."""
        logger.info("Initialisation du Live Feature Engineer...")
        self.feature_engineer = LiveFeatureEngineer()
        logger.info("✓ Feature Engineer prêt")
    
    def run_backtest_complete(self):
        """Exécute le backtest complet sur les deux saisons."""
        logger.info("\n" + "="*70)
        logger.info("BACKTEST HYBRIDE v2.0 - AVEC VRAIES FEATURES")
        logger.info("="*70)
        
        results = {}
        
        # 1. Backtest 2024-25 (complet)
        logger.info("\n1. Backtest 2024-25 (features existantes)...")
        results['2024-25'] = self._backtest_2024_25()
        
        # 2. Backtest 2025-26 (avec VRAIES features)
        logger.info("\n2. Backtest 2025-26 (features calculées en temps réel)...")
        results['2025-26'] = self._backtest_2025_26_with_real_features()
        
        # 3. Comparaison et rapport
        logger.info("\n3. Génération du rapport comparatif...")
        self._generate_comparison_report(results)
        
        # 4. Sauvegarde
        self._save_results(results)
        
        return results
    
    def _backtest_2024_25(self):
        """Backtest 2024-25 avec features existantes."""
        logger.info("Chargement des features 2024-25...")
        
        df = pd.read_parquet(settings.features_v3_path)
        season_data = df[df['season'] == '2024-25'].copy()
        
        logger.info(f"✓ {len(season_data)} matchs 2024-25 chargés")
        
        predictions = []
        for idx, row in tqdm(season_data.iterrows(), total=len(season_data), desc="Prédiction 2024-25"):
            pred = self._predict_with_features(row)
            if pred:
                predictions.append(pred)
        
        metrics = self._calculate_metrics(predictions)
        
        return {
            'metrics': metrics,
            'predictions': predictions,
            'total_games': len(season_data)
        }
    
    def _backtest_2025_26_with_real_features(self):
        """Backtest 2025-26 avec vraies features calculées."""
        logger.info("Récupération des matchs 2025-26...")
        
        # Récupérer les matchs via API
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'ingestion'))
        try:
            from external_api_nba import NBAAPIManager
            api = NBAAPIManager()
            api_result = api.fetch_2025_26_results()
            
            games = api_result['results']
            logger.info(f"✓ {len(games)} matchs 2025-26 récupérés via {api_result['method']}")
            
        except Exception as e:
            logger.error(f"❌ Erreur API: {e}")
            games = []
        
        if len(games) == 0:
            logger.warning("⚠️ Aucun match trouvé pour 2025-26")
            return {'metrics': {}, 'predictions': [], 'total_games': 0}
        
        # Calculer les features réelles pour chaque match
        logger.info("Calcul des features réelles pour chaque match...")
        
        predictions = []
        for game in tqdm(games, desc="Prédiction 2025-26"):
            if not game.get('is_played'):
                continue
                
            # Calculer les features réelles
            features = self.feature_engineer.calculate_match_features(
                game_id=game['game_id'],
                home_team=game['home_team'],
                away_team=game['away_team'],
                game_date=game['game_date']
            )
            
            if features:
                pred = self._predict_with_live_features(features, game)
                if pred:
                    predictions.append(pred)
        
        metrics = self._calculate_metrics(predictions)
        
        return {
            'metrics': metrics,
            'predictions': predictions,
            'total_games': len(games),
            'method': 'Live Feature Engineer'
        }
    
    def _predict_with_features(self, row):
        """Prédit avec les features d'une ligne de dataframe."""
        try:
            features = row[self.selected_features].values.reshape(1, -1)
            proba_raw = self.model.predict_proba(features)[0, 1]
            
            if self.calibrator:
                proba = self.calibrator.predict(np.array([[proba_raw]]))[0]
            else:
                proba = proba_raw
            
            pred_class = 1 if proba > 0.5 else 0
            actual_class = row['target']
            
            return {
                'game_id': row['game_id'],
                'game_date': str(row['game_date']),
                'predicted': pred_class,
                'actual': actual_class,
                'proba_home_win': float(proba),
                'confidence': float(max(proba, 1 - proba)),
                'is_correct': pred_class == actual_class
            }
        except Exception as e:
            logger.warning(f"Erreur prédiction: {e}")
            return None
    
    def _predict_with_live_features(self, features: Dict, game: Dict):
        """Prédit avec les features calculées en temps réel."""
        try:
            # Extraire les features nécessaires
            feature_values = []
            for feat in self.selected_features:
                if feat in features:
                    feature_values.append(features[feat])
                else:
                    # Feature manquante, utiliser valeur par défaut
                    feature_values.append(0.0)
            
            features_array = np.array(feature_values).reshape(1, -1)
            proba_raw = self.model.predict_proba(features_array)[0, 1]
            
            if self.calibrator:
                proba = self.calibrator.predict(np.array([[proba_raw]]))[0]
            else:
                proba = proba_raw
            
            pred_class = 1 if proba > 0.5 else 0
            actual_winner = 1 if game['actual_winner'] == 'HOME' else 0
            
            return {
                'game_id': game['game_id'],
                'game_date': game['game_date'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'predicted': pred_class,
                'actual': actual_winner,
                'proba_home_win': float(proba),
                'confidence': float(max(proba, 1 - proba)),
                'is_correct': pred_class == actual_winner,
                'home_score': game.get('home_score'),
                'away_score': game.get('away_score')
            }
        except Exception as e:
            logger.warning(f"Erreur prédiction live: {e}")
            return None
    
    def _calculate_metrics(self, predictions):
        """Calcule les métriques de performance."""
        if not predictions:
            return {}
        
        y_true = [p['actual'] for p in predictions]
        y_pred = [p['predicted'] for p in predictions]
        y_proba = [p['proba_home_win'] for p in predictions]
        
        return {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1': f1_score(y_true, y_pred, zero_division=0),
            'auc': roc_auc_score(y_true, y_proba) if len(set(y_true)) > 1 else 0.5,
            'total_predictions': len(predictions),
            'correct_predictions': sum(1 for p in predictions if p['is_correct'])
        }
    
    def _generate_comparison_report(self, results):
        """Génère un rapport comparatif entre les deux saisons."""
        logger.info("\n" + "="*70)
        logger.info("RÉSULTATS COMPARATIFS")
        logger.info("="*70)
        
        for season, data in results.items():
            if 'metrics' in data and data['metrics']:
                metrics = data['metrics']
                logger.info(f"\n{season}:")
                logger.info(f"  Matchs: {metrics.get('total_predictions', 0)}")
                logger.info(f"  Accuracy: {metrics.get('accuracy', 0):.2%}")
                logger.info(f"  Precision: {metrics.get('precision', 0):.2%}")
                logger.info(f"  Recall: {metrics.get('recall', 0):.2%}")
                logger.info(f"  F1: {metrics.get('f1', 0):.2%}")
                logger.info(f"  AUC: {metrics.get('auc', 0):.3f}")
        
        # Comparaison
        if '2024-25' in results and '2025-26' in results:
            acc_2024 = results['2024-25'].get('metrics', {}).get('accuracy', 0)
            acc_2025 = results['2025-26'].get('metrics', {}).get('accuracy', 0)
            diff = acc_2025 - acc_2024
            
            logger.info(f"\nDifférence 2025-26 vs 2024-25: {diff:+.2%}")
            
            if diff > -0.05:  # Si différence < 5%
                logger.info("✅ Performance similaire entre les saisons!")
            else:
                logger.warning(f"⚠️ Performance différente: {diff:.2%}")
    
    def _save_results(self, results):
        """Sauvegarde les résultats."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Sauvegarder en JSON
        output_dir = Path('reports/v2_backtest')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = output_dir / f'backtest_v2_{timestamp}.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\n✓ Résultats sauvegardés: {results_file}")
        
        # Sauvegarder les prédictions en CSV
        for season, data in results.items():
            if 'predictions' in data:
                df = pd.DataFrame(data['predictions'])
                csv_file = output_dir / f'predictions_{season}_{timestamp}.csv'
                df.to_csv(csv_file, index=False)


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description='Backtest Hybride v2.0 avec vraies features')
    parser.add_argument('--phase', choices=['test', 'complete'], default='complete',
                       help='Phase à exécuter')
    args = parser.parse_args()
    
    logger.info("="*70)
    logger.info("NBA ANALYTICS - BACKTEST HYBRIDE v2.0")
    logger.info("Avec vraies features calculées en temps réel")
    logger.info("="*70)
    
    backtester = HybridBacktesterV2()
    results = backtester.run_backtest_complete()
    
    logger.info("\n" + "="*70)
    logger.info("BACKTEST TERMINÉ")
    logger.info("="*70)


if __name__ == '__main__':
    main()
