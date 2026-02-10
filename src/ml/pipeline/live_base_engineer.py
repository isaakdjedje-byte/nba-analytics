#!/usr/bin/env python3
"""
Live Base Engineer - Calcule les 55+ features de base pour 2025-26

Ce module calcule toutes les features de base necessaires pour que
feature_engineering_v3.py puisse les transformer en 85 features V3.

Usage:
    from live_base_engineer import LiveBaseEngineer
    
    engineer = LiveBaseEngineer()
    features = engineer.calculate_match_features(
        game_id='0022500001',
        home_team='Boston Celtics',
        away_team='New York Knicks',
        game_date='2025-10-22',
        home_score=118,  # Si match joue
        away_score=105   # Si match joue
    )
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np
from scipy import stats

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LiveBaseEngineer:
    """
    Calcule les features de base (55+ colonnes) pour les matchs 2025-26.
    
    Ces features sont necessaires pour que feature_engineering_v3.py
    puisse creer les 85 features V3 completes.
    """
    
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
                
                for team_id, names in mappings.items():
                    team_id_int = int(team_id)
                    canonical_name = names[0]
                    self.id_to_name[team_id_int] = canonical_name
                    self.name_to_id[canonical_name] = team_id_int
                    for name in names:
                        self.name_to_id[name] = team_id_int
                
                logger.info(f"Mappings charges: {len(self.id_to_name)} equipes")
                return
        
        logger.warning("Mapping equipes non trouve")
    
    def _get_team_id(self, team_name: str) -> Optional[int]:
        """Recupere l'ID d'une equipe."""
        return self.name_to_id.get(team_name)
    
    def _get_team_history(self, team_id: int, before_date: str, n_games: int = 10) -> pd.DataFrame:
        """Recupere l'historique des derniers matchs."""
        before_dt = pd.to_datetime(before_date)
        
        team_matches = self.historical_data[
            ((self.historical_data['home_team_id'] == team_id) |
             (self.historical_data['away_team_id'] == team_id)) &
            (pd.to_datetime(self.historical_data['game_date']) < before_dt)
        ].copy()
        
        return team_matches.sort_values('game_date', ascending=False).head(n_games)
    
    def _calculate_wins_last_n(self, team_id: int, before_date: str, n_games: int = 10) -> int:
        """Compte les victoires sur les N derniers matchs."""
        history = self._get_team_history(team_id, before_date, n_games)
        if len(history) == 0:
            return n_games // 2  # Default 0.500
        
        wins = 0
        for _, match in history.iterrows():
            if match['home_team_id'] == team_id:
                wins += match['target']
            else:
                wins += (1 - match['target'])
        return wins
    
    def _calculate_avg_stat(self, team_id: int, before_date: str, 
                           stat_type: str, n_games: int = 5) -> float:
        """Calcule la moyenne d'une statistique (pts, reb, ast, etc.)."""
        history = self._get_team_history(team_id, before_date, n_games)
        if len(history) == 0:
            return 0.0
        
        values = []
        for _, match in history.iterrows():
            is_home = match['home_team_id'] == team_id
            
            if stat_type == 'pts':
                val = match.get('home_score' if is_home else 'away_score', 0)
            elif stat_type == 'reb':
                val = match.get('home_reb' if is_home else 'away_reb', 0)
            elif stat_type == 'ast':
                val = match.get('home_ast' if is_home else 'away_ast', 0)
            elif stat_type == 'stl':
                val = match.get('home_stl' if is_home else 'away_stl', 0)
            elif stat_type == 'blk':
                val = match.get('home_blk' if is_home else 'away_blk', 0)
            elif stat_type == 'tov':
                val = match.get('home_tov' if is_home else 'away_tov', 0)
            elif stat_type == 'pf':
                val = match.get('home_pf' if is_home else 'away_pf', 0)
            else:
                val = 0
            
            values.append(val)
        
        return np.mean(values) if values else 0.0
    
    def _calculate_trend(self, team_id: int, before_date: str, n_games: int = 5) -> float:
        """Calcule la tendance (pente des resultats)."""
        history = self._get_team_history(team_id, before_date, n_games)
        if len(history) < 3:
            return 0.0
        
        # Creer serie temporelle des resultats (1=gagne, 0=perdu)
        results = []
        for _, match in history.iloc[::-1].iterrows():  # Ordre chronologique
            if match['home_team_id'] == team_id:
                results.append(match['target'])
            else:
                results.append(1 - match['target'])
        
        if len(results) < 3:
            return 0.0
        
        # Regression lineaire simple
        x = np.arange(len(results))
        slope, _, _, _, _ = stats.linregress(x, results)
        return slope
    
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
    
    def _calculate_h2h_stats(self, home_id: int, away_id: int, 
                            before_date: str, n_games: int = 5) -> Dict:
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
            return {
                'h2h_games': 0,
                'h2h_home_wins': 0,
                'h2h_home_win_rate': 0.5,
                'h2h_avg_margin': 0.0
            }
        
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
            'h2h_games': len(h2h_matches),
            'h2h_home_wins': home_wins,
            'h2h_home_win_rate': (home_wins / len(h2h_matches)) * 100,  # Pourcentage
            'h2h_avg_margin': np.mean(margins)
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
                                game_date: str, home_score: Optional[int] = None,
                                away_score: Optional[int] = None) -> Optional[Dict]:
        """
        Calcule toutes les features de base (55+) pour un match.
        
        Args:
            game_id: ID du match
            home_team: Nom de l'equipe a domicile
            away_team: Nom de l'equipe a l'exterieur
            game_date: Date du match (YYYY-MM-DD)
            home_score: Score domicile (si match joue)
            away_score: Score exterieur (si match joue)
            
        Returns:
            Dict avec 55+ features de base
        """
        try:
            # Convertir noms en IDs
            home_id = self._get_team_id(home_team)
            away_id = self._get_team_id(away_team)
            
            if not home_id or not away_id:
                logger.error(f"Equipes non trouvees: {home_team} ({home_id}) vs {away_team} ({away_id})")
                return None
            
            # === FEATURES DE BASE ===
            features = {
                # Identifiants
                'game_id': game_id,
                'game_date': game_date,
                'season': '2025-26',
                'season_type': 'Regular Season',
                'home_team_id': home_id,
                'away_team_id': away_id,
                
                # Target (si scores fournis)
                'target': 1 if home_score and away_score and home_score > away_score else 
                         (0 if home_score and away_score and home_score < away_score else None),
                
                # Scores (si match joue)
                'home_score': home_score,
                'away_score': away_score,
                'point_diff': home_score - away_score if home_score and away_score else None,
            }
            
            # === STATS WIN/LOSS ===
            # Multiplier par 100 pour aligner avec l'echelle historique (pourcentages)
            features['home_win_pct'] = self._calculate_win_pct(home_id, game_date, 10) * 100
            features['away_win_pct'] = self._calculate_win_pct(away_id, game_date, 10) * 100
            features['win_pct_diff'] = features['home_win_pct'] - features['away_win_pct']
            
            features['home_wins_last_10'] = self._calculate_wins_last_n(home_id, game_date, 10)
            features['away_wins_last_10'] = self._calculate_wins_last_n(away_id, game_date, 10)
            
            # === STATS POINTS ===
            features['home_avg_pts_last_5'] = self._calculate_avg_stat(home_id, game_date, 'pts', 5)
            features['away_avg_pts_last_5'] = self._calculate_avg_stat(away_id, game_date, 'pts', 5)
            features['pts_diff_last_5'] = features['home_avg_pts_last_5'] - features['away_avg_pts_last_5']
            
            # === STATS REBONDS ===
            features['home_avg_reb_last_5'] = self._calculate_avg_stat(home_id, game_date, 'reb', 5)
            features['away_avg_reb_last_5'] = self._calculate_avg_stat(away_id, game_date, 'reb', 5)
            features['home_reb'] = features['home_avg_reb_last_5']  # Alias pour compatibilite
            features['away_reb'] = features['away_avg_reb_last_5']
            
            # === STATS PASSES ===
            features['home_avg_ast_last_5'] = self._calculate_avg_stat(home_id, game_date, 'ast', 5)
            features['away_avg_ast_last_5'] = self._calculate_avg_stat(away_id, game_date, 'ast', 5)
            features['home_ast'] = features['home_avg_ast_last_5']
            features['away_ast'] = features['away_avg_ast_last_5']
            
            # === AUTRES STATS ===
            features['home_stl'] = self._calculate_avg_stat(home_id, game_date, 'stl', 5)
            features['away_stl'] = self._calculate_avg_stat(away_id, game_date, 'stl', 5)
            features['home_blk'] = self._calculate_avg_stat(home_id, game_date, 'blk', 5)
            features['away_blk'] = self._calculate_avg_stat(away_id, game_date, 'blk', 5)
            features['home_tov'] = self._calculate_avg_stat(home_id, game_date, 'tov', 5)
            features['away_tov'] = self._calculate_avg_stat(away_id, game_date, 'tov', 5)
            features['home_pf'] = self._calculate_avg_stat(home_id, game_date, 'pf', 5)
            features['away_pf'] = self._calculate_avg_stat(away_id, game_date, 'pf', 5)
            
            # === TENDANCES ===
            features['home_trend'] = self._calculate_trend(home_id, game_date, 5)
            features['away_trend'] = self._calculate_trend(away_id, game_date, 5)
            features['trend_diff'] = features['home_trend'] - features['away_trend']
            
            # === H2H ===
            h2h_stats = self._calculate_h2h_stats(home_id, away_id, game_date, 10)
            features.update(h2h_stats)
            
            # === REPOS ===
            features['home_rest_days'] = self._calculate_rest_days(home_id, game_date)
            features['away_rest_days'] = self._calculate_rest_days(away_id, game_date)
            features['rest_advantage'] = features['home_rest_days'] - features['away_rest_days']
            
            # === BACK-TO-BACK ===
            features['home_is_back_to_back'] = self._is_back_to_back(home_id, game_date)
            features['away_is_back_to_back'] = self._is_back_to_back(away_id, game_date)
            
            # === STATS AVANCEES (approximation depuis donnees disponibles) ===
            # TS% approxime
            features['home_ts_pct'] = features['home_avg_pts_last_5'] / 100  # Normalise
            features['away_ts_pct'] = features['away_avg_pts_last_5'] / 100
            features['ts_pct_diff'] = features['home_ts_pct'] - features['away_ts_pct']
            
            # EFG% approxime
            features['home_efg_pct'] = features['home_win_pct'] * 0.5 + 0.25
            features['away_efg_pct'] = features['away_win_pct'] * 0.5 + 0.25
            
            # Game Score approxime
            features['home_game_score'] = (
                features['home_avg_pts_last_5'] * 0.4 +
                features['home_avg_reb_last_5'] * 0.2 +
                features['home_avg_ast_last_5'] * 0.2
            )
            features['away_game_score'] = (
                features['away_avg_pts_last_5'] * 0.4 +
                features['away_avg_reb_last_5'] * 0.2 +
                features['away_avg_ast_last_5'] * 0.2
            )
            
            # Fatigue efficiency
            features['home_fatigue_eff'] = 1.0 - (features['home_is_back_to_back'] * 0.1)
            features['away_fatigue_eff'] = 1.0 - (features['away_is_back_to_back'] * 0.1)
            
            logger.debug(f"Features calculees: {len(features)}")
            return features
            
        except Exception as e:
            logger.error(f"Erreur calcul features pour {game_id}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def calculate_season_features(self, games: List[Dict]) -> pd.DataFrame:
        """
        Calcule les features pour toute une liste de matchs.
        
        Args:
            games: Liste de dicts avec game_id, home_team, away_team, game_date
                  Optionnel: home_score, away_score
            
        Returns:
            DataFrame avec toutes les features de base
        """
        logger.info(f"Calcul features pour {len(games)} matchs...")
        
        all_features = []
        for i, game in enumerate(games):
            if i % 100 == 0:
                logger.info(f"  Traitement: {i}/{len(games)}")
            
            features = self.calculate_match_features(
                game_id=game['game_id'],
                home_team=game['home_team'],
                away_team=game['away_team'],
                game_date=game['game_date'],
                home_score=game.get('home_score'),
                away_score=game.get('away_score')
            )
            if features:
                all_features.append(features)
        
        df = pd.DataFrame(all_features)
        logger.info(f"OK {len(df)} matchs avec features calculees")
        logger.info(f"Colonnes: {len(df.columns)}")
        return df
    
    def save_features(self, df: pd.DataFrame, output_path: str = None):
        """Sauvegarde les features calculees."""
        if output_path is None:
            output_path = 'data/gold/ml_features/features_2025-26_base.parquet'
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_parquet(output_path)
        logger.info(f"Features sauvegardees: {output_path}")
        
        # Sauvegarder aussi liste des colonnes
        metadata = {
            'total_matches': len(df),
            'total_features': len(df.columns),
            'feature_names': list(df.columns),
            'created_at': datetime.now().isoformat()
        }
        
        metadata_path = output_path.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Metadonnees: {metadata_path}")


def main():
    """Test du module."""
    print("\n" + "="*70)
    print("TEST LIVE BASE ENGINEER")
    print("="*70 + "\n")
    
    engineer = LiveBaseEngineer()
    
    if len(engineer.historical_data) == 0:
        print("ERREUR: Pas de donnees historiques disponibles")
        return
    
    # Test sur un match
    test_game = {
        'game_id': 'TEST001',
        'home_team': 'Boston Celtics',
        'away_team': 'New York Knicks',
        'game_date': '2025-10-22',
        'home_score': 118,
        'away_score': 105
    }
    
    print(f"Test match: {test_game['home_team']} vs {test_game['away_team']}")
    
    features = engineer.calculate_match_features(**test_game)
    
    if features:
        print(f"\nOK! {len(features)} features calculees")
        print("\nExemples de features cles:")
        key_features = [
            'home_win_pct', 'away_win_pct', 'home_wins_last_10', 'away_wins_last_10',
            'home_avg_pts_last_5', 'away_avg_pts_last_5', 'home_avg_reb_last_5',
            'home_trend', 'away_trend', 'trend_diff', 'h2h_home_win_rate'
        ]
        for feat in key_features[:10]:
            if feat in features:
                print(f"  {feat}: {features[feat]:.3f}")
        
        print("\n" + "="*70)
        print("TEST REUSSI!")
        print("="*70)
    else:
        print("\nECHEC du test")


if __name__ == '__main__':
    main()
