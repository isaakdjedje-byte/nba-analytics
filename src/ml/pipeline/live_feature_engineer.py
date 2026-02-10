#!/usr/bin/env python3
"""
Live Feature Engineer - Calcul des features V3 en temps reel pour 2025-26
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LiveFeatureEngineer:
    """Calcule les features V3 en temps reel pour les matchs 2025-26."""
    
    def __init__(self):
        self.historical_data = None
        self.id_to_name = {}
        self.name_to_id = {}
        self._load_historical_data()
        self._load_team_mappings()
        
    def _load_historical_data(self):
        """Charge les donnees historiques des saisons precedentes."""
        logger.info("Chargement des donnees historiques...")
        
        features_paths = [
            'data/gold/ml_features/features_v3.parquet',
            '../data/gold/ml_features/features_v3.parquet',
            '../../data/gold/ml_features/features_v3.parquet',
            '../../../data/gold/ml_features/features_v3.parquet'
        ]
        
        for path in features_paths:
            if Path(path).exists():
                df = pd.read_parquet(path)
                self.historical_data = df[df['season'] != '2025-26'].copy()
                logger.info(f"Charge {len(self.historical_data)} matchs historiques")
                logger.info(f"Saisons: {sorted(self.historical_data['season'].unique())}")
                return
        
        logger.error("Fichier features_v3.parquet non trouve")
        self.historical_data = pd.DataFrame()
    
    def _load_team_mappings(self):
        """Charge les mappings ID <-> nom."""
        mapping_paths = [
            'data/team_mapping_extended.json',
            '../data/team_mapping_extended.json',
            '../../data/team_mapping_extended.json'
        ]
        
        for path in mapping_paths:
            if Path(path).exists():
                with open(path, 'r') as f:
                    mappings = json.load(f)
                
                # Creer mappings ID -> nom et nom -> ID
                for team_id, names in mappings.items():
                    team_id_int = int(team_id)
                    canonical_name = names[0]  # Premier nom = nom canonique
                    self.id_to_name[team_id_int] = canonical_name
                    self.name_to_id[canonical_name] = team_id_int
                    # Ajouter aussi les variantes
                    for name in names:
                        self.name_to_id[name] = team_id_int
                
                logger.info(f"Mappings charges: {len(self.id_to_name)} equipes")
                return
        
        logger.warning("Mapping equipes non trouve")
    
    def _get_team_id(self, team_name: str) -> Optional[int]:
        """Recupere l'ID d'une equipe a partir de son nom."""
        return self.name_to_id.get(team_name)
    
    def _get_team_name(self, team_id: int) -> str:
        """Recupere le nom d'une equipe a partir de son ID."""
        return self.id_to_name.get(team_id, str(team_id))
    
    def _get_team_history(self, team_id: int, before_date: str, n_games: int = 10) -> pd.DataFrame:
        """Recupere l'historique des derniers matchs d'une equipe."""
        before_dt = pd.to_datetime(before_date)
        
        team_matches = self.historical_data[
            ((self.historical_data['home_team_id'] == team_id) |
             (self.historical_data['away_team_id'] == team_id)) &
            (pd.to_datetime(self.historical_data['game_date']) < before_dt)
        ].copy()
        
        return team_matches.sort_values('game_date', ascending=False).head(n_games)
    
    def _calculate_win_pct(self, team_id: int, before_date: str, n_games: int = 10) -> float:
        """Calcule le pourcentage de victoires."""
        history = self._get_team_history(team_id, before_date, n_games)
        if len(history) == 0:
            return 0.5
        
        wins = 0
        for _, match in history.iterrows():
            if match['home_team_id'] == team_id:
                wins += match['target']
            else:
                wins += (1 - match['target'])
        return wins / len(history)
    
    def _calculate_momentum(self, team_id: int, before_date: str, window: int = 5) -> float:
        """Calcule le momentum."""
        short_term = self._calculate_win_pct(team_id, before_date, n_games=window)
        long_term = self._calculate_win_pct(team_id, before_date, n_games=10)
        return short_term - long_term
    
    def _calculate_avg_points(self, team_id: int, before_date: str, n_games: int = 5) -> Tuple[float, float]:
        """Calcule les points moyens marques et encaisses."""
        history = self._get_team_history(team_id, before_date, n_games)
        if len(history) == 0:
            return 110.0, 110.0
        
        points_scored = []
        points_allowed = []
        
        for _, match in history.iterrows():
            if match['home_team_id'] == team_id:
                points_scored.append(match.get('home_score', 110))
                points_allowed.append(match.get('away_score', 110))
            else:
                points_scored.append(match.get('away_score', 110))
                points_allowed.append(match.get('home_score', 110))
        
        return np.mean(points_scored), np.mean(points_allowed)
    
    def _calculate_h2h_stats(self, home_id: int, away_id: int, before_date: str, n_games: int = 5) -> Dict:
        """Calcule les statistiques head-to-head."""
        before_dt = pd.to_datetime(before_date)
        
        h2h_matches = self.historical_data[
            (((self.historical_data['home_team_id'] == home_id) &
              (self.historical_data['away_team_id'] == away_id)) |
             ((self.historical_data['home_team_id'] == away_id) &
              (self.historical_data['away_team_id'] == home_id))) &
            (pd.to_datetime(self.historical_data['game_date']) < before_dt)
        ].copy().sort_values('game_date', ascending=False).head(n_games)
        
        if len(h2h_matches) == 0:
            return {'h2h_home_win_rate': 0.5, 'h2h_avg_margin': 0.0, 'h2h_games': 0}
        
        home_wins = 0
        margins = []
        for _, match in h2h_matches.iterrows():
            if match['home_team_id'] == home_id:
                home_wins += match['target']
                margin = match.get('home_score', 100) - match.get('away_score', 100)
            else:
                home_wins += (1 - match['target'])
                margin = match.get('away_score', 100) - match.get('home_score', 100)
            margins.append(margin)
        
        return {
            'h2h_home_win_rate': home_wins / len(h2h_matches),
            'h2h_avg_margin': np.mean(margins),
            'h2h_games': len(h2h_matches)
        }
    
    def _calculate_rest_days(self, team_id: int, before_date: str) -> int:
        """Calcule les jours de repos."""
        history = self._get_team_history(team_id, before_date, n_games=1)
        if len(history) == 0:
            return 3
        
        last_game_date = pd.to_datetime(history.iloc[0]['game_date'])
        current_date = pd.to_datetime(before_date)
        rest_days = (current_date - last_game_date).days - 1
        return max(0, rest_days)
    
    def _is_back_to_back(self, team_id: int, before_date: str) -> bool:
        """Verifie si l'equipe joue un back-to-back."""
        return self._calculate_rest_days(team_id, before_date) == 0
    
    def calculate_match_features(self, game_id: str, home_team: str, away_team: str, 
                                game_date: str) -> Optional[Dict]:
        """Calcule toutes les features V3 pour un match."""
        try:
            # Convertir noms en IDs
            home_id = self._get_team_id(home_team)
            away_id = self._get_team_id(away_team)
            
            if not home_id or not away_id:
                logger.error(f"Equipes non trouvees: {home_team} ({home_id}) vs {away_team} ({away_id})")
                return None
            
            features = {
                'game_id': game_id,
                'game_date': game_date,
                'home_team_id': home_id,
                'away_team_id': away_id,
                'home_team_name': home_team,
                'away_team_name': away_team,
                'season': '2025-26'
            }
            
            # Win percentages
            features['home_win_pct'] = self._calculate_win_pct(home_id, game_date, 10)
            features['away_win_pct'] = self._calculate_win_pct(away_id, game_date, 10)
            features['win_pct_diff'] = features['home_win_pct'] - features['away_win_pct']
            features['home_win_pct_last_5'] = self._calculate_win_pct(home_id, game_date, 5)
            features['away_win_pct_last_5'] = self._calculate_win_pct(away_id, game_date, 5)
            
            # Momentum
            features['home_momentum'] = self._calculate_momentum(home_id, game_date, 5)
            features['away_momentum'] = self._calculate_momentum(away_id, game_date, 5)
            features['momentum_diff'] = features['home_momentum'] - features['away_momentum']
            
            # Points averages
            home_pts_scored, home_pts_allowed = self._calculate_avg_points(home_id, game_date, 5)
            away_pts_scored, away_pts_allowed = self._calculate_avg_points(away_id, game_date, 5)
            
            features['home_avg_pts_last_5'] = home_pts_scored
            features['home_avg_pts_allowed_last_5'] = home_pts_allowed
            features['away_avg_pts_last_5'] = away_pts_scored
            features['away_avg_pts_allowed_last_5'] = away_pts_allowed
            features['pts_diff'] = home_pts_scored - away_pts_scored
            
            # H2H stats
            h2h_stats = self._calculate_h2h_stats(home_id, away_id, game_date, 5)
            features.update(h2h_stats)
            
            # Rest days
            features['home_rest_days'] = self._calculate_rest_days(home_id, game_date)
            features['away_rest_days'] = self._calculate_rest_days(away_id, game_date)
            features['rest_advantage'] = features['home_rest_days'] - features['away_rest_days']
            
            # Back-to-back
            features['home_is_back_to_back'] = self._is_back_to_back(home_id, game_date)
            features['away_is_back_to_back'] = self._is_back_to_back(away_id, game_date)
            
            # Features V3 avancees
            features['home_weighted_form'] = features['home_win_pct_last_5'] * 0.7 + features['home_win_pct'] * 0.3
            features['away_weighted_form'] = features['away_win_pct_last_5'] * 0.7 + features['away_win_pct'] * 0.3
            features['weighted_form_diff'] = features['home_weighted_form'] - features['away_weighted_form']
            
            # Consistance
            features['home_consistency'] = 1 - abs(features['home_win_pct_last_5'] - features['home_win_pct'])
            features['away_consistency'] = 1 - abs(features['away_win_pct_last_5'] - features['away_win_pct'])
            features['consistency_diff'] = features['home_consistency'] - features['away_consistency']
            
            return features
            
        except Exception as e:
            logger.error(f"Erreur calcul features pour {game_id}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def calculate_season_features(self, games: List[Dict]) -> pd.DataFrame:
        """Calcule les features pour toute une liste de matchs."""
        logger.info(f"Calcul features pour {len(games)} matchs...")
        
        all_features = []
        for game in games:
            features = self.calculate_match_features(
                game_id=game['game_id'],
                home_team=game['home_team'],
                away_team=game['away_team'],
                game_date=game['game_date']
            )
            if features:
                all_features.append(features)
        
        df = pd.DataFrame(all_features)
        logger.info(f"OK {len(df)} matchs avec features calculees")
        return df
    
    def save_features(self, df: pd.DataFrame, output_path: str = None):
        """Sauvegarde les features calculees."""
        if output_path is None:
            output_path = 'data/gold/ml_features/features_2025-26_live.parquet'
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_parquet(output_path)
        logger.info(f"Features sauvegardees: {output_path}")


def main():
    """Test du module."""
    print("\n" + "="*70)
    print("TEST LIVE FEATURE ENGINEER")
    print("="*70 + "\n")
    
    engineer = LiveFeatureEngineer()
    
    if len(engineer.historical_data) == 0:
        print("ERREUR: Pas de donnees historiques disponibles")
        return
    
    test_game = {
        'game_id': 'TEST001',
        'home_team': 'Boston Celtics',
        'away_team': 'New York Knicks',
        'game_date': '2025-10-22'
    }
    
    print(f"Test match: {test_game['home_team']} vs {test_game['away_team']}")
    
    features = engineer.calculate_match_features(**test_game)
    
    if features:
        print("\nTest REUSSI!")
        print(f"Features calculees: {len(features)}")
        print(f"\nExemples:")
        print(f"  home_win_pct: {features['home_win_pct']:.3f}")
        print(f"  momentum_diff: {features['momentum_diff']:.3f}")
        print(f"  weighted_form_diff: {features['weighted_form_diff']:.3f}")
        print(f"  h2h_home_win_rate: {features['h2h_home_win_rate']:.3f}")
    else:
        print("\nECHEC du test")
    
    print("\n" + "="*70)


if __name__ == '__main__':
    main()
