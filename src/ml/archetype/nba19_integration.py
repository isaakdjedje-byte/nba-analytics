#!/usr/bin/env python3
"""
NBA-19 Integration: Chargement et utilisation des vraies stats d'équipe
Remplace les approximations par des données réelles
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, Optional, Tuple


class NBA19TeamStatsLoader:
    """
    Charge et fournit les statistiques d'équipe de NBA-19
    Pour calculs précis des métriques avancées (AST%, STL%, BLK%, etc.)
    """
    
    def __init__(self, stats_path: str = None):
        """
        Initialise le loader
        
        Args:
            stats_path: Chemin vers team_season_stats.json
        """
        if stats_path is None:
            stats_path = 'data/gold/team_season_stats/team_season_stats.json'
        
        self.stats_path = Path(stats_path)
        self.team_stats = None
        self.team_stats_dict = None
        self.avg_stats = None
        
        self._load_stats()
    
    def _load_stats(self):
        """Charge les stats d'équipe depuis JSON"""
        try:
            with open(self.stats_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.team_stats = pd.DataFrame(data['data'])
            
            # Crée un dictionnaire pour accès rapide par team_id
            self.team_stats_dict = self.team_stats.set_index('team_id').to_dict('index')
            
            # Calcule les moyennes globales (pour fallback si team_id non trouvé)
            numeric_cols = self.team_stats.select_dtypes(include=[np.number]).columns
            self.avg_stats = self.team_stats[numeric_cols].mean().to_dict()
            
            print(f"✓ NBA-19: {len(self.team_stats)} équipes chargées")
            
        except Exception as e:
            print(f"⚠️  Erreur chargement NBA-19: {e}")
            print("   Utilisation des approximations")
            self.team_stats = None
            self.team_stats_dict = {}
            self.avg_stats = {}
    
    def get_team_stats(self, team_id: int) -> Dict:
        """
        Retourne les stats d'une équipe spécifique
        
        Args:
            team_id: ID de l'équipe
            
        Returns:
            Dict avec les stats ou moyennes si non trouvé
        """
        if self.team_stats_dict and team_id in self.team_stats_dict:
            return self.team_stats_dict[team_id]
        
        # Fallback sur moyennes
        return self.avg_stats if self.avg_stats else self._get_default_stats()
    
    def _get_default_stats(self) -> Dict:
        """Stats par défaut si aucune donnée disponible"""
        return {
            'avg_pts_scored': 110.0,
            'avg_pts_allowed': 110.0,
            'avg_reb': 44.0,
            'avg_ast': 25.0,
            'avg_fg_pct': 0.47,
            'avg_fg3_pct': 0.36,
            'avg_ft_pct': 0.78,
            'games_played': 82
        }
    
    def calculate_team_possessions(self, team_id: int) -> float:
        """
        Calcule les possessions d'équipe (estimation NBA standard)
        Formula: 0.5 * (FGA + 0.44*FTA - ORB + TOV) * 2
        
        Simplifié: utilise avg_pts_scored comme proxy
        """
        stats = self.get_team_stats(team_id)
        
        # Estimation basée sur points marqués
        # En NBA, ~1 possession = ~1.05 points en moyenne
        avg_pts = stats.get('avg_pts_scored', 110.0)
        possessions = avg_pts / 1.05
        
        return possessions * stats.get('games_played', 82)  # Total saison
    
    def get_opponent_stats(self, team_id: int) -> Dict:
        """
        Retourne les stats adverses (approximation par moyennes ligue)
        """
        # Pour l'instant, utilise les moyennes globales comme proxy
        # Dans une version future, on pourrait avoir les vraies stats adverses
        return self.avg_stats if self.avg_stats else self._get_default_stats()
    
    def enrich_player_data(self, df: pd.DataFrame, team_id_col: str = 'team_id') -> pd.DataFrame:
        """
        Enrichit un DataFrame de joueurs avec les stats d'équipe
        
        Args:
            df: DataFrame avec colonne team_id
            team_id_col: Nom de la colonne team_id
            
        Returns:
            DataFrame enrichi avec stats équipe
        """
        if self.team_stats is None or team_id_col not in df.columns:
            print("⚠️  Impossible d'enrichir - pas de stats ou colonne team_id manquante")
            return df
        
        df = df.copy()
        
        # Ajoute les stats d'équipe pour chaque joueur
        stats_to_add = [
            'avg_pts_scored', 'avg_pts_allowed', 'avg_reb', 'avg_ast',
            'avg_fg_pct', 'avg_fg3_pct', 'avg_ft_pct', 'games_played'
        ]
        
        for stat in stats_to_add:
            df[f'team_{stat}'] = df[team_id_col].map(
                lambda x: self.get_team_stats(x).get(stat, self.avg_stats.get(stat, 0))
            )
        
        # Calcule possessions équipe
        df['team_possessions'] = df[team_id_col].map(
            lambda x: self.calculate_team_possessions(x)
        )
        
        # Ajoute stats adverses (moyennes ligue)
        opp_stats = self.get_opponent_stats(0)  # 0 = moyennes
        df['opp_avg_pts_scored'] = opp_stats.get('avg_pts_scored', 110.0)
        df['opp_avg_reb'] = opp_stats.get('avg_reb', 44.0)
        df['opp_possessions'] = df['opp_avg_pts_scored'] / 1.05 * 82
        
        return df
    
    def calculate_advanced_metrics_with_real_data(
        self, 
        df: pd.DataFrame,
        player_minutes: pd.Series,
        team_id_col: str = 'team_id'
    ) -> pd.DataFrame:
        """
        Calcule les métriques avancées avec vraies données équipe
        
        Args:
            df: DataFrame avec stats joueurs
            player_minutes: Série avec minutes jouées
            team_id_col: Colonne team_id
            
        Returns:
            DataFrame avec métriques avancées
        """
        from src.utils.nba_formulas import (
            calculate_ast_pct, calculate_stl_pct, calculate_blk_pct,
            calculate_tov_pct, calculate_trb_pct, calculate_vorp_estimated,
            calculate_ws_per_48
        )
        
        df = df.copy()
        
        # Enrichit avec stats équipe
        df = self.enrich_player_data(df, team_id_col)
        
        # Récupère stats nécessaires
        minutes = player_minutes.fillna(0)
        
        # Team stats (totales pour la saison)
        team_minutes = df['team_games_played'] * 48 * 5  # 5 joueurs * 48 min
        team_fg = df['team_avg_pts_scored'] * df['team_games_played'] / 2  # Approx pts = 2 * FG
        team_reb = df['team_avg_reb'] * df['team_games_played']
        team_poss = df['team_possessions']
        
        # Opponent stats
        opp_reb = df['opp_avg_reb'] * 82
        opp_poss = df['opp_possessions']
        opp_fga = df['opp_avg_pts_scored'] * 82 / 2
        opp_3pa = opp_fga * 0.35  # Approximation 35% des tirs sont à 3pts
        
        # Calcule métriques avancées avec vraies données
        df['ast_pct_real'] = calculate_ast_pct(
            df.get('ast', 0), team_fg, df.get('fgm', 0), minutes, team_minutes
        )
        
        df['stl_pct_real'] = calculate_stl_pct(
            df.get('stl', 0), opp_poss, minutes, team_minutes
        )
        
        df['blk_pct_real'] = calculate_blk_pct(
            df.get('blk', 0), opp_fga, opp_3pa, minutes, team_minutes
        )
        
        df['tov_pct_real'] = calculate_tov_pct(
            df.get('tov', 0), df.get('fga', 0), df.get('fta', 0)
        )
        
        df['trb_pct_real'] = calculate_trb_pct(
            df.get('reb', 0), team_reb, opp_reb, minutes, team_minutes
        )
        
        # VORP et WS/48 estimés
        df['vorp_real'] = calculate_vorp_estimated(df.get('per', 0), minutes)
        df['ws_per_48_real'] = calculate_ws_per_48(df.get('per', 0), minutes)
        
        # Compare avec approximations
        df['ast_pct_diff'] = df['ast_pct_real'] - df.get('ast_pct', 0)
        df['stl_pct_diff'] = df['stl_pct_real'] - df.get('stl_pct', 0)
        
        return df
    
    def get_stats_summary(self) -> Dict:
        """Retourne un résumé des stats chargées"""
        if self.team_stats is None:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "n_teams": len(self.team_stats),
            "seasons": self.team_stats['season'].unique().tolist() if 'season' in self.team_stats.columns else [],
            "avg_pts": self.avg_stats.get('avg_pts_scored', 0),
            "avg_reb": self.avg_stats.get('avg_reb', 0),
            "avg_ast": self.avg_stats.get('avg_ast', 0)
        }


# Fonction utilitaire pour intégration rapide
def load_nba19_stats() -> NBA19TeamStatsLoader:
    """Charge les stats NBA-19 avec gestion d'erreurs"""
    try:
        loader = NBA19TeamStatsLoader()
        summary = loader.get_stats_summary()
        if summary['status'] == 'loaded':
            print(f"✓ NBA-19 chargé: {summary['n_teams']} équipes")
            print(f"  Moyennes - PTS: {summary['avg_pts']:.1f}, "
                  f"REB: {summary['avg_reb']:.1f}, AST: {summary['avg_ast']:.1f}")
        return loader
    except Exception as e:
        print(f"⚠️  Erreur NBA-19: {e}")
        return None


if __name__ == "__main__":
    # Test
    print("NBA-19 Integration Test")
    print("=" * 50)
    
    loader = load_nba19_stats()
    
    if loader:
        # Test récupération stats équipe
        test_team_id = 1610612743  # Denver Nuggets
        stats = loader.get_team_stats(test_team_id)
        print(f"\nStats Denver Nuggets:")
        print(f"  Points: {stats.get('avg_pts_scored', 0):.1f}")
        print(f"  Rebonds: {stats.get('avg_reb', 0):.1f}")
        print(f"  Passes: {stats.get('avg_ast', 0):.1f}")
        
        # Test possessions
        poss = loader.calculate_team_possessions(test_team_id)
        print(f"  Possessions (estimées): {poss:.0f}")
