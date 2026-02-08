#!/usr/bin/env python3
"""
Feature Engineering V3 - Nouvelles features pour atteindre 77.5%

Strategie:
1. Ratios avances (efficacite, consistance)
2. Rolling windows plus larges (10, 20 matchs)
3. Features de momentum (acceleration)
4. Interactions contextuelles
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FeatureEngineeringV3:
    """Cree de nouvelles features avancees."""
    
    def __init__(self, input_path: str = "data/gold/ml_features/features_all.parquet"):
        self.input_path = Path(input_path)
        self.df = None
        
    def load_data(self):
        """Charge les features existantes."""
        logger.info("Chargement des features V1...")
        self.df = pd.read_parquet(self.input_path)
        logger.info(f"[OK] {len(self.df)} matchs charges")
        
    def create_efficiency_ratios(self):
        """Ratios d'efficacite."""
        logger.info("Creation des ratios d'efficacite...")
        
        # Points par possession (approximation)
        self.df['home_pts_per_100'] = self.df['home_avg_pts_last_5'] * 100 / 100  # Normalise
        self.df['away_pts_per_100'] = self.df['away_avg_pts_last_5'] * 100 / 100
        
        # Efficacite offensive vs defensive
        self.df['home_off_eff'] = self.df['home_avg_pts_last_5'] / (self.df['home_avg_reb_last_5'] + 1)
        self.df['away_off_eff'] = self.df['away_avg_pts_last_5'] / (self.df['away_avg_reb_last_5'] + 1)
        
        # Differential d'efficacite
        self.df['off_eff_diff'] = self.df['home_off_eff'] - self.df['away_off_eff']
        
        logger.info("[OK] 5 ratios efficacite crees")
        
    def create_consistency_features(self):
        """Features de consistance (volatilite)."""
        logger.info("Creation des features de consistance...")
        
        # Volatilite du win rate (ecart-type des derniers resultats)
        # Approximation: base sur wins_last_10 et win_pct
        self.df['home_consistency'] = 1 - abs(self.df['home_wins_last_10'] / 10 - self.df['home_win_pct'])
        self.df['away_consistency'] = 1 - abs(self.df['away_wins_last_10'] / 10 - self.df['away_win_pct'])
        
        # Consistance relative
        self.df['consistency_diff'] = self.df['home_consistency'] - self.df['away_consistency']
        
        # Ecart entre performance recente et moyenne
        self.df['home_form_vs_avg'] = (self.df['home_wins_last_10'] / 10) - self.df['home_win_pct']
        self.df['away_form_vs_avg'] = (self.df['away_wins_last_10'] / 10) - self.df['away_win_pct']
        
        logger.info("[OK] 5 features consistance crees")
        
    def create_momentum_features(self):
        """Features de momentum (acceleration/deceleration)."""
        logger.info("Creation des features de momentum...")
        
        # Momentum = tendance recente vs tendance moyenne
        self.df['home_momentum'] = self.df['home_trend'] * self.df['home_form_vs_avg']
        self.df['away_momentum'] = self.df['away_trend'] * self.df['away_form_vs_avg']
        
        # Momentum differentiel
        self.df['momentum_diff_v3'] = self.df['home_momentum'] - self.df['away_momentum']
        
        # Acceleration: changement de momentum
        # Approximation via trend_diff
        self.df['momentum_acceleration'] = self.df['trend_diff'] * self.df['home_form_vs_avg']
        
        logger.info("[OK] 3 features momentum crees")
        
    def create_contextual_interactions(self):
        """Interactions contextuelles."""
        logger.info("Creation des interactions contextuelles...")
        
        # H2H poids par importance
        self.df['h2h_weighted'] = self.df['h2h_home_win_rate'] * np.log1p(self.df['h2h_games'])
        
        # Avantage domicile contextuel
        self.df['home_advantage'] = self.df['home_win_pct'] - self.df['away_win_pct']
        
        # Rest advantage combine avec forme
        self.df['rest_form_interaction'] = self.df['rest_advantage'] * (self.df['home_form_vs_avg'] - self.df['away_form_vs_avg'])
        
        # Back-to-back impact
        self.df['fatigue_impact'] = (self.df['home_is_back_to_back'].astype(int) - 
                                     self.df['away_is_back_to_back'].astype(int))
        
        # Clutch performance (approximation via trend)
        self.df['clutch_diff'] = self.df['home_trend'] * self.df['home_win_pct'] - \
                                  self.df['away_trend'] * self.df['away_win_pct']
        
        logger.info("[OK] 5 interactions contextuelles crees")
        
    def create_extended_windows(self):
        """Fenetres temporelles etendues (simulees a partir des donnees existantes)."""
        logger.info("Creation des fenetres etendues...")
        
        # Moyenne ponderee: recent pese plus
        self.df['home_weighted_form'] = (self.df['home_wins_last_10'] * 0.7 + 
                                          self.df['home_win_pct'] * 10 * 0.3) / 10
        self.df['away_weighted_form'] = (self.df['away_wins_last_10'] * 0.7 + 
                                          self.df['away_win_pct'] * 10 * 0.3) / 10
        
        # Differential pondere
        self.df['weighted_form_diff'] = self.df['home_weighted_form'] - self.df['away_weighted_form']
        
        # Performance sur differentes echelles de temps
        self.df['home_short_vs_long'] = self.df['home_wins_last_10'] / 10 - self.df['home_win_pct']
        self.df['away_short_vs_long'] = self.df['away_wins_last_10'] / 10 - self.df['away_win_pct']
        
        logger.info("[OK] 5 features fenetres etendues crees")
        
    def create_non_linear_features(self):
        """Features non-lineaires."""
        logger.info("Creation des features non-lineaires...")
        
        # Carres (capturer relations non-lineaires)
        self.df['win_pct_diff_squared'] = self.df['win_pct_diff'] ** 2
        self.df['h2h_margin_squared'] = self.df['h2h_avg_margin'] ** 2
        
        # Ratios avec protection division par zero
        self.df['pts_reb_ratio_home'] = self.df['home_avg_pts_last_5'] / (self.df['home_avg_reb_last_5'] + 1)
        self.df['pts_reb_ratio_away'] = self.df['away_avg_pts_last_5'] / (self.df['away_avg_reb_last_5'] + 1)
        self.df['pts_reb_ratio_diff'] = self.df['pts_reb_ratio_home'] - self.df['pts_reb_ratio_away']
        
        # Log transforms
        self.df['h2h_games_log'] = np.log1p(self.df['h2h_games'])
        
        logger.info("[OK] 5 features non-lineaires crees")
        
    def process(self):
        """Execute tout le feature engineering."""
        logger.info("\n=== FEATURE ENGINEERING V3 ===\n")
        
        self.load_data()
        
        nb_features_before = len(self.df.columns)
        
        # Creer toutes les nouvelles features
        self.create_efficiency_ratios()
        self.create_consistency_features()
        self.create_momentum_features()
        self.create_contextual_interactions()
        self.create_extended_windows()
        self.create_non_linear_features()
        
        nb_features_after = len(self.df.columns)
        nb_new = nb_features_after - nb_features_before
        
        logger.info(f"\n[OK] {nb_new} nouvelles features creees")
        logger.info(f"Total: {nb_features_before} -> {nb_features_after} features")
        
        return self.df
        
    def save(self, output_path: str = "data/gold/ml_features/features_v3.parquet"):
        """Sauvegarde le dataset enrichi."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.df.to_parquet(output_path)
        logger.info(f"[SAVED] Dataset sauvegarde: {output_path}")
        
        # Sauvegarder la liste des nouvelles features
        new_features = [c for c in self.df.columns if c not in 
                       ['game_id', 'season', 'game_date', 'season_type', 'target']]
        
        import json
        with open('results/week1/features_v3_list.json', 'w') as f:
            json.dump({
                'total_features': len(new_features),
                'feature_names': new_features,
                'new_features_v3': [c for c in self.df.columns if c.endswith(('_v3', '_diff', '_ratio', '_squared', '_log', '_impact', '_weighted'))]
            }, f, indent=2)
        
        logger.info("[SAVED] Liste des features sauvegardee")


def main():
    """Point d'entree."""
    fe = FeatureEngineeringV3()
    fe.process()
    fe.save()
    
    print("\n" + "="*60)
    print("FEATURE ENGINEERING V3 TERMINE")
    print("="*60)


if __name__ == '__main__':
    main()
