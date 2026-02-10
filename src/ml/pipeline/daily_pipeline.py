#!/usr/bin/env python3
"""
Pipeline Quotidien Complet - Predictions NBA
Combine API Live + Modele ML
"""

import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
from pathlib import Path
try:
    from .nba_live_api import get_today_games
except ImportError:
    from nba_live_api import get_today_games
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DailyPredictionPipeline:
    """Pipeline complet: API -> Features -> Prediction -> Sauvegarde"""
    
    def __init__(self):
        self.model = None
        self.historical_data = None
        self.team_mapping = None
        self.features_cols = None
        
    def load_resources(self):
        """Charge tous les ressources necessaires."""
        logger.info("Chargement des ressources...")
        
        # Modele XGB V3 (sans data leakage)
        self.model = joblib.load("models/week1/xgb_v3.pkl")
        logger.info("[OK] Modele XGB V3 charge")
        
        # Donnees historiques pour features
        self.historical_data = pd.read_parquet("data/gold/ml_features/features_v3.parquet")
        logger.info("[OK] Donnees historiques chargees")
        
        # Mapping equipes (etendu avec variantes)
        with open('data/team_name_to_id.json') as f:
            self.team_name_to_id = json.load(f)
        with open('data/team_mapping_extended.json') as f:
            self.team_mapping_extended = json.load(f)
        logger.info("[OK] Mapping equipes etendu charge")
        
        # Liste des features (memes que pendant l'entrainement)
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
        self.features_cols = [c for c in self.historical_data.columns if c not in exclude_cols]
        logger.info(f"[OK] {len(self.features_cols)} features disponibles")
        
    def get_team_historical_features(self, team_name: str, is_home: bool = True):
        """Recupere les dernieres features d'une equipe."""
        team_id = self.team_name_to_id.get(team_name)
        if not team_id:
            logger.warning(f"Equipe {team_name} non trouvee")
            return None
            
        team_id_int = int(team_id)
        
        if is_home:
            matches = self.historical_data[self.historical_data['home_team_id'] == team_id_int]
        else:
            matches = self.historical_data[self.historical_data['away_team_id'] == team_id_int]
            
        if len(matches) == 0:
            return None
            
        return matches.sort_values('game_date').iloc[-1]
        
    def engineer_features_for_match(self, home_team: str, away_team: str):
        """Cree les features pour un match specifique."""
        home_hist = self.get_team_historical_features(home_team, is_home=True)
        away_hist = self.get_team_historical_features(away_team, is_home=False)
        
        if home_hist is None or away_hist is None:
            return None
            
        # Combiner les features
        match_features = {}
        
        for col in self.features_cols:
            if col.startswith('home_'):
                match_features[col] = home_hist.get(col, 0)
            elif col.startswith('away_'):
                match_features[col] = away_hist.get(col, 0)
            else:
                # Features globales
                match_features[col] = home_hist.get(col, 0)
                
        return pd.DataFrame([match_features])
        
    def predict_match(self, home_team: str, away_team: str):
        """Predire un match."""
        features = self.engineer_features_for_match(home_team, away_team)
        
        if features is None:
            return {
                'home_team': home_team,
                'away_team': away_team,
                'error': 'Donnees historiques insuffisantes'
            }
            
        proba = self.model.predict_proba(features)[0, 1]
        prediction = 1 if proba > 0.5 else 0
        confidence = max(proba, 1 - proba)
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'prediction': 'Home Win' if prediction == 1 else 'Away Win',
            'proba_home_win': float(proba),
            'confidence': float(confidence),
            'recommendation': self._get_recommendation(confidence)
        }
        
    def _get_recommendation(self, confidence: float) -> str:
        """Recommandation basee sur la confidence."""
        if confidence >= 0.70:
            return "HIGH_CONFIDENCE"
        elif confidence >= 0.60:
            return "MEDIUM_CONFIDENCE"
        elif confidence >= 0.55:
            return "LOW_CONFIDENCE"
        else:
            return "SKIP"
            
    def run_daily_predictions(self):
        """Execute les predictions pour tous les matchs du jour."""
        logger.info("\n=== PREDICTIONS QUOTIDIENNES NBA ===\n")
        
        self.load_resources()
        
        # Recuperer matchs du jour
        games = get_today_games()
        
        if not games:
            logger.info("Aucun match aujourd'hui ou erreur API")
            logger.info("Utilisation des exemples de demonstration...")
            games = [
                {'home_team': 'Boston Celtics', 'away_team': 'Los Angeles Lakers'},
                {'home_team': 'Golden State Warriors', 'away_team': 'Phoenix Suns'},
                {'home_team': 'Milwaukee Bucks', 'away_team': 'Miami Heat'}
            ]
            
        # Predictions
        predictions = []
        for game in games:
            logger.info(f"Prediction: {game['home_team']} vs {game['away_team']}")
            pred = self.predict_match(game['home_team'], game['away_team'])
            predictions.append(pred)
            
            if 'error' not in pred:
                logger.info(f"  -> {pred['prediction']} (confiance: {pred['confidence']:.2%})")
            else:
                logger.warning(f"  -> ERREUR: {pred['error']}")
                
        # Sauvegarder
        self._save_predictions(predictions)
        
        return predictions
        
    def _save_predictions(self, predictions):
        """Sauvegarde les predictions."""
        output_dir = Path('predictions')
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Sauvegarde avec timestamp
        df = pd.DataFrame(predictions)
        filename = output_dir / f"predictions_{timestamp}.csv"
        df.to_csv(filename, index=False)
        logger.info(f"\n[SAVED] Predictions: {filename}")
        
        # Fichier latest
        latest = output_dir / "latest_predictions.csv"
        df.to_csv(latest, index=False)
        
        # JSON pour faciliter la lecture
        json_file = output_dir / f"predictions_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                'date': datetime.now().isoformat(),
                'predictions': predictions
            }, f, indent=2)
            
        logger.info(f"[SAVED] JSON: {json_file}")


def main():
    """Point d'entree."""
    pipeline = DailyPredictionPipeline()
    predictions = pipeline.run_daily_predictions()
    
    # Resume
    print("\n" + "="*70)
    print("RESUME DES PREDICTIONS")
    print("="*70)
    
    for pred in predictions:
        if 'error' not in pred:
            print(f"\n{pred['home_team']} vs {pred['away_team']}")
            print(f"  Prediction:  {pred['prediction']}")
            print(f"  Confiance:   {pred['confidence']:.2%}")
            print(f"  Proba Home:  {pred['proba_home_win']:.2%}")
            print(f"  Recommandation: {pred['recommendation']}")
        else:
            print(f"\n{pred['home_team']} vs {pred['away_team']}")
            print(f"  ERREUR: {pred['error']}")
            
    print("\n" + "="*70)
    
    # Stats
    valid_preds = [p for p in predictions if 'error' not in p]
    if valid_preds:
        high_conf = sum(1 for p in valid_preds if p['recommendation'] == 'HIGH_CONFIDENCE')
        med_conf = sum(1 for p in valid_preds if p['recommendation'] == 'MEDIUM_CONFIDENCE')
        low_conf = sum(1 for p in valid_preds if p['recommendation'] == 'LOW_CONFIDENCE')
        
        print(f"\nStatistiques:")
        print(f"  Total matchs:     {len(valid_preds)}")
        print(f"  Haute confiance:  {high_conf}")
        print(f"  Moyenne confiance:{med_conf}")
        print(f"  Basse confiance:  {low_conf}")
        
    return predictions


if __name__ == '__main__':
    main()
