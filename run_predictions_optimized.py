#!/usr/bin/env python3
"""
NBA Predictions - Script Principal Optimisé (NBA-22 v2.0)
Pipeline complet avec calibration, feature selection et monitoring

Usage:
    python run_predictions_optimized.py              # Prédictions avec modèle optimisé
    python run_predictions_optimized --update        # Mise à jour résultats
    python run_predictions_optimized --report        # Rapport performance
    python run_predictions_optimized --train         # Réentraîner le modèle
    python run_predictions_optimized --health        # Check santé système
    python run_predictions_optimized --drift         # Vérifier data drift
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'ml' / 'pipeline'))

import pandas as pd
import numpy as np
import joblib
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from daily_pipeline import DailyPredictionPipeline
from tracking_roi import ROITracker
from nba_live_api import get_today_games
from probability_calibration import ProbabilityCalibrator
from drift_monitoring import DataDriftMonitor, check_system_health


class OptimizedPredictionPipeline:
    """
    Pipeline de prédiction optimisé avec calibration et sélection de features.
    """
    
    def __init__(self, use_optimized=True):
        self.use_optimized = use_optimized
        self.model = None
        self.calibrator = None
        self.selected_features = None
        self.historical_data = None
        self.team_name_to_id = None
        
    def load_resources(self):
        """Charge les ressources optimisées."""
        logger.info("Chargement des ressources...")
        
        # Charger la sélection de features
        features_file = Path("models/optimized/selected_features.json")
        if features_file.exists() and self.use_optimized:
            with open(features_file) as f:
                features_data = json.load(f)
                self.selected_features = features_data['features']
            logger.info(f"✅ {len(self.selected_features)} features sélectionnées chargées")
        else:
            self.selected_features = None
            logger.info("ℹ️ Utilisation de toutes les features")
        
        # Charger le modèle optimisé
        model_path = Path("models/optimized/model_xgb.joblib")
        if model_path.exists() and self.use_optimized:
            self.model = joblib.load(model_path)
            logger.info("✅ Modèle optimisé chargé")
            
            # Charger le calibrateur
            calib_path = Path("models/optimized/calibrator_xgb.joblib")
            if calib_path.exists():
                self.calibrator = ProbabilityCalibrator()
                self.calibrator.load(calib_path)
                logger.info("✅ Calibrateur chargé")
        else:
            # Fallback sur modèle V3
            logger.info("ℹ️ Modèle optimisé non trouvé, utilisation du modèle V3")
            self.model = joblib.load("models/week1/xgb_v3.pkl")
            self.selected_features = None
        
        # Charger données historiques
        self.historical_data = pd.read_parquet("data/gold/ml_features/features_v3.parquet")
        logger.info("✅ Données historiques chargées")
        
        # Mapping équipes
        with open('data/team_name_to_id.json') as f:
            self.team_name_to_id = json.load(f)
        with open('data/team_mapping_extended.json') as f:
            self.team_mapping_extended = json.load(f)
        logger.info("✅ Mapping équipes chargé")
        
    def get_team_historical_features(self, team_name, is_home=True):
        """Récupère les dernières features d'une équipe."""
        team_id = self.team_name_to_id.get(team_name)
        if not team_id:
            logger.warning(f"Équipe {team_name} non trouvée")
            return None
        
        team_id_int = int(team_id)
        
        if is_home:
            matches = self.historical_data[self.historical_data['home_team_id'] == team_id_int]
        else:
            matches = self.historical_data[self.historical_data['away_team_id'] == team_id_int]
        
        if len(matches) == 0:
            return None
        
        return matches.sort_values('game_date').iloc[-1]
    
    def engineer_features_for_match(self, home_team, away_team):
        """Crée les features pour un match."""
        home_hist = self.get_team_historical_features(home_team, is_home=True)
        away_hist = self.get_team_historical_features(away_team, is_home=False)
        
        if home_hist is None or away_hist is None:
            return None
        
        # Définir les colonnes features
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
        
        if self.selected_features:
            feature_cols = self.selected_features
        else:
            feature_cols = [c for c in self.historical_data.columns if c not in exclude_cols]
        
        # Combiner les features
        match_features = {}
        for col in feature_cols:
            if col.startswith('home_'):
                match_features[col] = home_hist.get(col, 0)
            elif col.startswith('away_'):
                match_features[col] = away_hist.get(col, 0)
            else:
                match_features[col] = home_hist.get(col, 0)
        
        return pd.DataFrame([match_features])
    
    def predict_match(self, home_team, away_team):
        """Prédit un match avec calibration."""
        features = self.engineer_features_for_match(home_team, away_team)
        
        if features is None:
            return {
                'home_team': home_team,
                'away_team': away_team,
                'error': 'Données historiques insuffisantes'
            }
        
        # Prédiction
        proba = self.model.predict_proba(features)[0, 1]
        prediction = 1 if proba > 0.5 else 0
        confidence = max(proba, 1 - proba)
        
        # Calibration si disponible
        proba_calibrated = None
        confidence_calibrated = None
        recommendation_calibrated = None
        
        if self.calibrator:
            proba_calibrated = self.calibrator.predict(np.array([proba]))[0]
            confidence_calibrated = max(proba_calibrated, 1 - proba_calibrated)
            recommendation_calibrated = self._get_recommendation(confidence_calibrated)
        
        result = {
            'home_team': home_team,
            'away_team': away_team,
            'prediction': 'Home Win' if prediction == 1 else 'Away Win',
            'proba_home_win': float(proba),
            'confidence': float(confidence),
            'recommendation': self._get_recommendation(confidence),
        }
        
        # Ajouter les valeurs calibrées si disponibles
        if proba_calibrated is not None:
            result['proba_home_win_calibrated'] = float(proba_calibrated)
            result['confidence_calibrated'] = float(confidence_calibrated)
            result['recommendation_calibrated'] = recommendation_calibrated
            # Utiliser les valeurs calibrées comme principales
            result['confidence'] = float(confidence_calibrated)
            result['recommendation'] = recommendation_calibrated
        
        return result
    
    def _get_recommendation(self, confidence):
        """Recommandation basée sur la confiance."""
        if confidence >= 0.70:
            return "HIGH_CONFIDENCE"
        elif confidence >= 0.60:
            return "MEDIUM_CONFIDENCE"
        elif confidence >= 0.55:
            return "LOW_CONFIDENCE"
        else:
            return "SKIP"
    
    def run_predictions(self):
        """Exécute les prédictions pour tous les matchs du jour."""
        logger.info("\n" + "="*70)
        logger.info("NBA PREDICTIONS OPTIMISÉES - V2.0")
        logger.info("="*70)
        
        self.load_resources()
        
        # Récupérer matchs du jour
        games = get_today_games()
        
        if not games:
            logger.info("Aucun match aujourd'hui ou erreur API")
            logger.info("Utilisation des exemples de démonstration...")
            games = [
                {'home_team': 'Boston Celtics', 'away_team': 'Los Angeles Lakers'},
                {'home_team': 'Golden State Warriors', 'away_team': 'Phoenix Suns'},
                {'home_team': 'Milwaukee Bucks', 'away_team': 'Miami Heat'}
            ]
        
        # Prédictions
        predictions = []
        for game in games:
            logger.info(f"\nPrédiction: {game['home_team']} vs {game['away_team']}")
            pred = self.predict_match(game['home_team'], game['away_team'])
            predictions.append(pred)
            
            if 'error' not in pred:
                logger.info(f"  → {pred['prediction']}")
                if 'confidence_calibrated' in pred:
                    logger.info(f"  Confiance (calibrée): {pred['confidence_calibrated']:.2%}")
                else:
                    logger.info(f"  Confiance: {pred['confidence']:.2%}")
                logger.info(f"  Recommandation: {pred['recommendation']}")
            else:
                logger.warning(f"  → ERREUR: {pred['error']}")
        
        # Sauvegarder
        self._save_predictions(predictions)
        
        # Tracking ROI
        tracker = ROITracker()
        for pred in predictions:
            if 'error' not in pred:
                tracker.add_prediction(pred)
        tracker.save()
        
        # Résumé
        self._print_summary(predictions)
        
        return predictions
    
    def _save_predictions(self, predictions):
        """Sauvegarde les prédictions."""
        output_dir = Path('predictions')
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # CSV
        df = pd.DataFrame(predictions)
        df.to_csv(output_dir / f"predictions_optimized_{timestamp}.csv", index=False)
        df.to_csv(output_dir / "latest_predictions_optimized.csv", index=False)
        
        # JSON
        with open(output_dir / f"predictions_optimized_{timestamp}.json", 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'model': 'optimized_xgb',
                'predictions': predictions
            }, f, indent=2)
        
        logger.info(f"\n✅ Prédictions sauvegardées dans predictions/")
    
    def _print_summary(self, predictions):
        """Affiche le résumé."""
        valid_preds = [p for p in predictions if 'error' not in p]
        
        if not valid_preds:
            return
        
        print("\n" + "="*70)
        print("RÉSUMÉ DES PRÉDICTIONS")
        print("="*70)
        
        high_conf = sum(1 for p in valid_preds if p['recommendation'] == 'HIGH_CONFIDENCE')
        med_conf = sum(1 for p in valid_preds if p['recommendation'] == 'MEDIUM_CONFIDENCE')
        low_conf = sum(1 for p in valid_preds if p['recommendation'] == 'LOW_CONFIDENCE')
        skip = sum(1 for p in valid_preds if p['recommendation'] == 'SKIP')
        
        print(f"\nTotal matchs:       {len(valid_preds)}")
        print(f"Haute confiance:    {high_conf}")
        print(f"Moyenne confiance:  {med_conf}")
        print(f"Basse confiance:    {low_conf}")
        print(f"Ignorer:            {skip}")
        
        if self.calibrator:
            print("\n[OK] Probabilités calibrées activées")
        if self.selected_features:
            print(f"[OK] Feature selection: {len(self.selected_features)} features")
        
        print("="*70)


def update_results():
    """Met à jour les résultats des matchs."""
    print("="*70)
    print("MISE À JOUR DES RÉSULTATS")
    print("="*70)
    
    tracker = ROITracker()
    
    # Charger prédictions optimisées ou normales
    latest_file = Path('predictions/latest_predictions_optimized.csv')
    if not latest_file.exists():
        latest_file = Path('predictions/latest_predictions.csv')
    
    if not latest_file.exists():
        print("[ERREUR] Aucune prédiction trouvée")
        return
    
    predictions = pd.read_csv(latest_file)
    
    print(f"\nPrédictions à mettre à jour: {len(predictions)}")
    
    for idx, row in predictions.iterrows():
        home = row['home_team']
        away = row['away_team']
        date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n{idx+1}. {home} vs {away}")
        
        result = input("Résultat (h=Home Win, a=Away Win, s=Skip): ").lower().strip()
        
        if result == 'h':
            tracker.update_result(home, away, date, 'HOME_WIN')
        elif result == 'a':
            tracker.update_result(home, away, date, 'AWAY_WIN')
        elif result == 's':
            print("  [SKIP]")
    
    tracker.save()
    print("\n✅ Mise à jour terminée")


def generate_report():
    """Génère le rapport de performance."""
    tracker = ROITracker()
    tracker.export_results()


def train_model():
    """Lance l'entraînement optimisé."""
    logger.info("Lancement de l'entraînement optimisé...")
    
    from train_optimized import OptimizedNBA22Trainer
    
    trainer = OptimizedNBA22Trainer()
    results = trainer.run()
    
    return results


def check_health():
    """Vérifie la santé du système."""
    health = check_system_health(
        features_path="data/gold/ml_features/features_v3.parquet",
        predictions_dir="predictions",
        reference_path="data/gold/ml_features/features_v3.parquet"
    )
    
    # Sauvegarder le rapport
    with open('predictions/health_report.json', 'w') as f:
        json.dump(health, f, indent=2)
    
    return health


def check_drift():
    """Vérifie le data drift."""
    logger.info("Vérification du data drift...")
    
    monitor = DataDriftMonitor(
        reference_data_path="data/gold/ml_features/features_v3.parquet",
        alert_threshold=0.05
    )
    
    # Charger données récentes (30 derniers matchs)
    current_data = pd.read_parquet("data/gold/ml_features/features_v3.parquet").tail(30)
    
    # Sélectionner quelques features importantes
    important_features = [
        'home_win_pct', 'away_win_pct', 'win_pct_diff',
        'home_avg_pts_last_5', 'away_avg_pts_last_5'
    ]
    
    drift_result = monitor.detect_feature_drift(current_data, important_features)
    
    # Sauvegarder le rapport
    monitor.save_report('predictions/drift_report.json')
    
    return drift_result


def main():
    parser = argparse.ArgumentParser(description='NBA Predictions Optimized v2.0')
    parser.add_argument('--update', action='store_true',
                       help='Mettre à jour les résultats des matchs')
    parser.add_argument('--report', action='store_true',
                       help='Générer le rapport de performance')
    parser.add_argument('--train', action='store_true',
                       help='Réentraîner le modèle optimisé')
    parser.add_argument('--health', action='store_true',
                       help='Vérifier la santé du système')
    parser.add_argument('--drift', action='store_true',
                       help='Vérifier le data drift')
    parser.add_argument('--legacy', action='store_true',
                       help='Utiliser le modèle V3 (non optimisé)')
    
    args = parser.parse_args()
    
    if args.update:
        update_results()
    elif args.report:
        generate_report()
    elif args.train:
        train_model()
    elif args.health:
        check_health()
    elif args.drift:
        check_drift()
    else:
        # Mode par défaut: prédictions
        use_optimized = not args.legacy
        pipeline = OptimizedPredictionPipeline(use_optimized=use_optimized)
        pipeline.run_predictions()


if __name__ == '__main__':
    main()
