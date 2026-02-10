#!/usr/bin/env python3
"""
Progressive Feature Engineer

Calcule les features pour 2025-26 UNIQUEMENT à partir des matchs déjà joués
dans la saison 2025-26 (pas d'historique 2018-2025).

Cela reproduit les vraies conditions de prédiction et résout le data drift.
"""

import sys
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

import pandas as pd
import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))

from boxscore_orchestrator_v2 import BoxScoreOrchestratorV2, TeamBoxScore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ProgressiveFeatureEngineer:
    """
    Calcule les features de manière progressive pour la saison 2025-26.
    
    Pour chaque match, utilise UNIQUEMENT les matchs précédents de 2025-26
    pour calculer : win_pct, trend, momentum, h2h, etc.
    """
    
    def __init__(self, season: str = '2025-26'):
        self.season = season
        self.orchestrator = BoxScoreOrchestratorV2()
        self.team_history = defaultdict(list)  # Historique par équipe
        self.h2h_history = defaultdict(list)   # Historique H2H
        
    def load_all_games(self) -> pd.DataFrame:
        """Charge tous les matchs de la saison ordonnés par date."""
        logger.info(f"Chargement des matchs {self.season}...")
        
        # Charger depuis les features existantes
        df = pd.read_parquet(f'data/gold/ml_features/features_{self.season}_v3.parquet')
        df['game_date'] = pd.to_datetime(df['game_date'])
        df = df.sort_values('game_date')
        
        logger.info(f"✓ {len(df)} matchs chargés ({df['game_date'].min()} - {df['game_date'].max()})")
        return df
    
    def _get_team_matches_before(self, team_id: int, before_date: datetime) -> List[Dict]:
        """Récupère les matchs d'une équipe avant une date donnée."""
        matches = []
        for match in self.team_history[team_id]:
            if match['date'] < before_date:
                matches.append(match)
        return matches
    
    def _calculate_win_pct(self, team_id: int, before_date: datetime, n_games: int = 10) -> float:
        """Calcule le win% sur les n derniers matchs AVANT la date."""
        matches = self._get_team_matches_before(team_id, before_date)
        
        if len(matches) == 0:
            return 0.5  # Valeur neutre si pas d'historique
        
        # Prendre les n derniers
        recent_matches = matches[-n_games:]
        wins = sum(1 for m in recent_matches if m['won'])
        return wins / len(recent_matches)
    
    def _calculate_trend(self, team_id: int, before_date: datetime, n_games: int = 5) -> float:
        """Calcule la tendance (pente des résultats)."""
        matches = self._get_team_matches_before(team_id, before_date)
        
        if len(matches) < 3:
            return 0.0
        
        recent_matches = matches[-n_games:]
        if len(recent_matches) < 3:
            return 0.0
        
        # Résultats binaires (1=gagné, 0=perdu)
        results = [1 if m['won'] else 0 for m in recent_matches]
        
        # Régression linéaire
        x = np.arange(len(results))
        slope, _, _, _, _ = stats.linregress(x, results)
        return slope
    
    def _calculate_avg_stats(self, team_id: int, before_date: datetime, 
                            stat_type: str, n_games: int = 5) -> float:
        """Calcule la moyenne d'une stat sur les n derniers matchs."""
        matches = self._get_team_matches_before(team_id, before_date)
        
        if len(matches) == 0:
            return 0.0
        
        recent_matches = matches[-n_games:]
        values = [m.get(stat_type, 0) for m in recent_matches]
        return np.mean(values) if values else 0.0
    
    def _calculate_h2h_stats(self, home_id: int, away_id: int, 
                            before_date: datetime, n_games: int = 5) -> Dict:
        """Calcule les stats H2H entre deux équipes."""
        key = tuple(sorted([home_id, away_id]))
        matches = []
        
        for match in self.h2h_history[key]:
            if match['date'] < before_date:
                matches.append(match)
        
        if len(matches) == 0:
            return {
                'h2h_games': 0,
                'h2h_home_wins': 0,
                'h2h_home_win_rate': 0.5,
                'h2h_avg_margin': 0.0
            }
        
        recent_matches = matches[-n_games:]
        home_wins = sum(1 for m in recent_matches 
                       if (m['home_id'] == home_id and m['home_won']) or
                          (m['away_id'] == home_id and not m['home_won']))
        
        margins = []
        for m in recent_matches:
            if m['home_id'] == home_id:
                margins.append(m['home_pts'] - m['away_pts'])
            else:
                margins.append(m['away_pts'] - m['home_pts'])
        
        return {
            'h2h_games': len(recent_matches),
            'h2h_home_wins': home_wins,
            'h2h_home_win_rate': home_wins / len(recent_matches),
            'h2h_avg_margin': np.mean(margins)
        }
    
    def _calculate_rest_days(self, team_id: int, before_date: datetime) -> int:
        """Calcule les jours de repos depuis le dernier match."""
        matches = self._get_team_matches_before(team_id, before_date)
        
        if len(matches) == 0:
            return 3  # Valeur par défaut
        
        last_match = matches[-1]
        last_date = last_match['date']
        rest_days = (before_date - last_date).days - 1
        return max(0, rest_days)
    
    def _is_back_to_back(self, team_id: int, before_date: datetime) -> bool:
        """Vérifie si l'équipe joue un back-to-back."""
        return self._calculate_rest_days(team_id, before_date) == 0
    
    def calculate_match_features(self, game_id: str, game_date: datetime,
                                home_team_id: int, away_team_id: int,
                                boxscore_home: TeamBoxScore, boxscore_away: TeamBoxScore) -> Dict:
        """
        Calcule toutes les features pour un match de manière progressive.
        """
        features = {
            'game_id': game_id,
            'game_date': game_date.strftime('%Y-%m-%d'),
            'season': self.season,
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            
            # Target (résultat du match)
            'target': 1 if boxscore_home.pts > boxscore_away.pts else 0,
            
            # Scores réels
            'home_score': boxscore_home.pts,
            'away_score': boxscore_away.pts,
            'point_diff': boxscore_home.pts - boxscore_away.pts,
        }
        
        # === STATS RÉELLES DU MATCH (depuis box scores) ===
        features['home_reb'] = boxscore_home.reb
        features['away_reb'] = boxscore_away.reb
        features['home_ast'] = boxscore_home.ast
        features['away_ast'] = boxscore_away.ast
        features['home_stl'] = boxscore_home.stl
        features['away_stl'] = boxscore_away.stl
        features['home_blk'] = boxscore_home.blk
        features['away_blk'] = boxscore_away.blk
        features['home_tov'] = boxscore_home.tov
        features['away_tov'] = boxscore_away.tov
        features['home_pf'] = boxscore_home.pf
        features['away_pf'] = boxscore_away.pf
        
        # Shooting percentages
        features['home_fg_pct'] = boxscore_home.fg_pct
        features['away_fg_pct'] = boxscore_away.fg_pct
        features['home_ts_pct'] = boxscore_home.fg_pct  # Approximation
        features['away_ts_pct'] = boxscore_away.fg_pct
        
        # === STATS PROGRESSIVES (calculées depuis début saison) ===
        
        # Win percentages (format pourcentage 0-100)
        features['home_win_pct'] = self._calculate_win_pct(home_team_id, game_date, 10) * 100
        features['away_win_pct'] = self._calculate_win_pct(away_team_id, game_date, 10) * 100
        features['win_pct_diff'] = features['home_win_pct'] - features['away_win_pct']
        
        features['home_win_pct_last_5'] = self._calculate_win_pct(home_team_id, game_date, 5) * 100
        features['away_win_pct_last_5'] = self._calculate_win_pct(away_team_id, game_date, 5) * 100
        
        # Nombre de victoires (absolu) - nécessaire pour feature_engineering_v3
        features['home_wins_last_10'] = int(features['home_win_pct'] / 10)
        features['away_wins_last_10'] = int(features['away_win_pct'] / 10)
        features['home_wins_last_5'] = int(features['home_win_pct_last_5'] / 20)
        features['away_wins_last_5'] = int(features['away_win_pct_last_5'] / 20)
        
        # Momentum / Trend
        features['home_trend'] = self._calculate_trend(home_team_id, game_date, 5)
        features['away_trend'] = self._calculate_trend(away_team_id, game_date, 5)
        features['trend_diff'] = features['home_trend'] - features['away_trend']
        
        features['home_momentum'] = features['home_trend'] * (features['home_win_pct_last_5'] / 100 - features['home_win_pct'] / 100)
        features['away_momentum'] = features['away_trend'] * (features['away_win_pct_last_5'] / 100 - features['away_win_pct'] / 100)
        features['momentum_diff'] = features['home_momentum'] - features['away_momentum']
        
        # Average points
        features['home_avg_pts_last_5'] = self._calculate_avg_stats(home_team_id, game_date, 'pts', 5)
        features['away_avg_pts_last_5'] = self._calculate_avg_stats(away_team_id, game_date, 'pts', 5)
        features['pts_diff_last_5'] = features['home_avg_pts_last_5'] - features['away_avg_pts_last_5']
        
        features['home_avg_pts_allowed_last_5'] = self._calculate_avg_stats(home_team_id, game_date, 'pts_allowed', 5)
        features['away_avg_pts_allowed_last_5'] = self._calculate_avg_stats(away_team_id, game_date, 'pts_allowed', 5)
        
        # Rebounds, assists, etc.
        features['home_avg_reb_last_5'] = self._calculate_avg_stats(home_team_id, game_date, 'reb', 5)
        features['away_avg_reb_last_5'] = self._calculate_avg_stats(away_team_id, game_date, 'reb', 5)
        
        features['home_avg_ast_last_5'] = self._calculate_avg_stats(home_team_id, game_date, 'ast', 5)
        features['away_avg_ast_last_5'] = self._calculate_avg_stats(away_team_id, game_date, 'ast', 5)
        
        # H2H stats
        h2h_stats = self._calculate_h2h_stats(home_team_id, away_team_id, game_date, 5)
        features.update(h2h_stats)
        
        # Rest days
        features['home_rest_days'] = self._calculate_rest_days(home_team_id, game_date)
        features['away_rest_days'] = self._calculate_rest_days(away_team_id, game_date)
        features['rest_advantage'] = features['home_rest_days'] - features['away_rest_days']
        
        # Back-to-back
        features['home_is_back_to_back'] = self._is_back_to_back(home_team_id, game_date)
        features['away_is_back_to_back'] = self._is_back_to_back(away_team_id, game_date)
        
        # === FEATURES AVANCÉES ===
        features['home_weighted_form'] = (features['home_win_pct_last_5'] * 0.7 + features['home_win_pct'] * 0.3) / 100
        features['away_weighted_form'] = (features['away_win_pct_last_5'] * 0.7 + features['away_win_pct'] * 0.3) / 100
        features['weighted_form_diff'] = features['home_weighted_form'] - features['away_weighted_form']
        
        features['home_consistency'] = 1 - abs(features['home_win_pct_last_5'] - features['home_win_pct']) / 100
        features['away_consistency'] = 1 - abs(features['away_win_pct_last_5'] - features['away_win_pct']) / 100
        features['consistency_diff'] = features['home_consistency'] - features['away_consistency']
        
        return features
    
    def process_season(self) -> pd.DataFrame:
        """
        Traite toute la saison de manière progressive.
        """
        logger.info("="*70)
        logger.info("CALCUL PROGRESSIF DES FEATURES 2025-26")
        logger.info("="*70)
        
        # 1. Charger tous les matchs
        df_games = self.load_all_games()
        
        # 2. Traiter chaque match dans l'ordre chronologique
        all_features = []
        
        for idx, row in df_games.iterrows():
            game_id = row['game_id']
            game_date = row['game_date']
            home_id = row['home_team_id']
            away_id = row['away_team_id']
            
            if idx % 100 == 0:
                logger.info(f"Traitement: {idx}/{len(df_games)} - {game_date.strftime('%Y-%m-%d')}")
            
            # Récupérer box scores
            box_home, box_away = self.orchestrator.get_boxscores_for_game(game_id)
            
            if box_home is None or box_away is None:
                logger.warning(f"Pas de box score pour {game_id}, ignoré")
                continue
            
            # Calculer features
            features = self.calculate_match_features(
                game_id, game_date, home_id, away_id, box_home, box_away
            )
            all_features.append(features)
            
            # Mettre à jour l'historique pour les matchs suivants
            home_won = box_home.pts > box_away.pts
            
            match_data_home = {
                'date': game_date,
                'won': home_won,
                'pts': box_home.pts,
                'pts_allowed': box_away.pts,
                'reb': box_home.reb,
                'ast': box_home.ast,
                'stl': box_home.stl,
                'blk': box_home.blk,
                'tov': box_home.tov,
                'pf': box_home.pf
            }
            
            match_data_away = {
                'date': game_date,
                'won': not home_won,
                'pts': box_away.pts,
                'pts_allowed': box_home.pts,
                'reb': box_away.reb,
                'ast': box_away.ast,
                'stl': box_away.stl,
                'blk': box_away.blk,
                'tov': box_away.tov,
                'pf': box_away.pf
            }
            
            self.team_history[home_id].append(match_data_home)
            self.team_history[away_id].append(match_data_away)
            
            # Historique H2H
            h2h_key = tuple(sorted([home_id, away_id]))
            self.h2h_history[h2h_key].append({
                'date': game_date,
                'home_id': home_id,
                'away_id': away_id,
                'home_won': home_won,
                'home_pts': box_home.pts,
                'away_pts': box_away.pts
            })
        
        # 3. Créer DataFrame
        df_features = pd.DataFrame(all_features)
        
        logger.info(f"\n✓ {len(df_features)} matchs traités avec features progressives")
        
        # 4. Sauvegarder
        output_path = Path(f'data/gold/ml_features/features_{self.season}_progressive.parquet')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_features.to_parquet(output_path)
        logger.info(f"✓ Sauvegardé: {output_path}")
        
        return df_features


def main():
    """Point d'entrée principal."""
    print("\n" + "="*70)
    print("PROGRESSIVE FEATURE ENGINEER")
    print("="*70 + "\n")
    
    engineer = ProgressiveFeatureEngineer(season='2025-26')
    df = engineer.process_season()
    
    print(f"\n✅ TERMINÉ: {len(df)} matchs avec features progressives calculées")
    print(f"✅ Les features utilisent UNIQUEMENT l'historique 2025-26")
    print("\n" + "="*70)


if __name__ == '__main__':
    main()
