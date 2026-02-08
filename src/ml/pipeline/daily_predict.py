#!/usr/bin/env python3
"""
NBA Daily Predictions - Production MVP
Pipeline quotidien de predictions de matchs NBA
"""

import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DailyPredictor:
    """
    Predicteur quotidien de matchs NBA.
    
    Usage:
        predictor = DailyPredictor()
        predictions = predictor.predict_today()
    """
    
    def __init__(self, models_dir: str = "models/week1"):
        self.models_dir = Path(models_dir)
        self.model = None
        self.features_cols = None
        self.historical_data = None
        self.team_mapping = None
        
    def load_team_mapping(self):
        """Charge le mapping team_id -> nom."""
        with open('data/team_mapping.json') as f:
            self.team_mapping = json.load(f)
        # Inverser pour recherche par nom
        self.team_name_to_id = {v: k for k, v in self.team_mapping.items()}
        
    def load_model(self):
        """Charge le meilleur modele (XGB optimisé)."""
        logger.info("Chargement du modele XGB optimise...")
        self.model = joblib.load(self.models_dir / "xgb_optimized.pkl")
        logger.info("[OK] Modele charge")
        
    def load_historical_features(self):
        """Charge les features historiques pour reference."""
        logger.info("Chargement des features historiques...")
        self.historical_data = pd.read_parquet("data/gold/ml_features/features_all.parquet")
        
        # Identifier les colonnes features (memes exclusions que pendant l'entrainement)
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
        
        self.features_cols = [c for c in self.historical_data.columns if c not in exclude_cols]
        logger.info(f"[OK] {len(self.features_cols)} features chargees")
        
    def get_team_features(self, team_name: str, is_home: bool = True) -> pd.Series:
        """
        Recupere les dernieres features connues pour une equipe.
        
        Args:
            team_name: Nom de l'equipe
            is_home: True si equipe a domicile
            
        Returns:
            Series avec les features de l'equipe
        """
        # Convertir nom en ID
        team_id = self.team_name_to_id.get(team_name)
        if team_id is None:
            logger.warning(f"Equipe {team_name} non trouvee dans le mapping")
            return None
        
        team_id_int = int(team_id)
        
        # Chercher les derniers matchs de cette equipe
        if is_home:
            team_matches = self.historical_data[self.historical_data['home_team_id'] == team_id_int]
        else:
            team_matches = self.historical_data[self.historical_data['away_team_id'] == team_id_int]
        
        if len(team_matches) == 0:
            logger.warning(f"Equipe {team_name} (ID: {team_id}) non trouvee dans les donnees historiques")
            return None
            
        # Prendre le match le plus recent
        latest_match = team_matches.sort_values('game_date').iloc[-1]
        
        return latest_match
        
    def predict_match(self, home_team: str, away_team: str) -> Dict:
        """
        Predire un match specifique.
        
        Args:
            home_team: Nom equipe domicile
            away_team: Nom equipe exterieur
            
        Returns:
            Dict avec prediction et metadonnees
        """
        # Recuperer features des deux equipes
        home_features = self.get_team_features(home_team, is_home=True)
        away_features = self.get_team_features(away_team, is_home=False)
        
        if home_features is None or away_features is None:
            return {
                'home_team': home_team,
                'away_team': away_team,
                'error': 'Equipe non trouvee dans les donnees historiques'
            }
        
        # Combiner les features
        match_features = {}
        
        # Features home
        for col in self.features_cols:
            if col.startswith('home_'):
                match_features[col] = home_features.get(col, 0)
            elif col.startswith('away_'):
                match_features[col] = away_features.get(col, 0)
            else:
                # Features globales (prendre moyenne ou valeur home)
                match_features[col] = home_features.get(col, 0)
        
        # Creer DataFrame
        X = pd.DataFrame([match_features])
        
        # Prediction
        proba = self.model.predict_proba(X)[0, 1]
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
        """Genere une recommandation basee sur la confidence."""
        if confidence >= 0.70:
            return "HIGH_CONFIDENCE"
        elif confidence >= 0.60:
            return "MEDIUM_CONFIDENCE"
        elif confidence >= 0.55:
            return "LOW_CONFIDENCE"
        else:
            return "SKIP"
    
    def predict_today(self, matches: Optional[List[Dict]] = None) -> pd.DataFrame:
        """
        Predire les matchs du jour.
        
        Args:
            matches: Liste de dicts {'home_team': str, 'away_team': str}
                    Si None, tente de fetch depuis l'API NBA
                    
        Returns:
            DataFrame avec les predictions
        """
        logger.info("=== PREDICTIONS QUOTIDIENNES NBA ===\n")
        
        self.load_model()
        self.load_historical_features()
        self.load_team_mapping()
        
        # Si pas de matches fournis, creer des exemples
        if matches is None:
            logger.info("Aucun match fourni - Mode demonstration avec exemples")
            matches = [
                {'home_team': 'Boston Celtics', 'away_team': 'Los Angeles Lakers'},
                {'home_team': 'Golden State Warriors', 'away_team': 'Phoenix Suns'},
                {'home_team': 'Milwaukee Bucks', 'away_team': 'Miami Heat'}
            ]
        
        # Predictions
        predictions = []
        for match in matches:
            logger.info(f"Prediction: {match['home_team']} vs {match['away_team']}")
            pred = self.predict_match(match['home_team'], match['away_team'])
            predictions.append(pred)
            
            if 'error' not in pred:
                logger.info(f"  -> {pred['prediction']} (confiance: {pred['confidence']:.2%})")
            else:
                logger.warning(f"  -> ERREUR: {pred['error']}")
        
        # Creer DataFrame
        df = pd.DataFrame(predictions)
        
        # Sauvegarder
        self._save_predictions(df)
        
        return df
    
    def _save_predictions(self, df: pd.DataFrame):
        """Sauvegarde les predictions."""
        output_dir = Path('predictions')
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = output_dir / f"predictions_{timestamp}.csv"
        
        df.to_csv(filename, index=False)
        logger.info(f"\n[SAVED] Predictions sauvegardees: {filename}")
        
        # Mettre a jour le fichier latest
        latest_file = output_dir / "latest_predictions.csv"
        df.to_csv(latest_file, index=False)


def main():
    """Point d'entree principal."""
    predictor = DailyPredictor()
    predictions = predictor.predict_today()
    
    # Affichage resume
    print("\n" + "="*60)
    print("RESUME DES PREDICTIONS")
    print("="*60)
    
    for _, row in predictions.iterrows():
        if 'error' not in row:
            print(f"\n{row['home_team']} vs {row['away_team']}")
            print(f"  Prediction: {row['prediction']}")
            print(f"  Confiance:  {row['confidence']:.2%}")
            print(f"  Recommandation: {row['recommendation']}")
        else:
            print(f"\n{row['home_team']} vs {row['away_team']}")
            print(f"  ERREUR: {row['error']}")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    main()
