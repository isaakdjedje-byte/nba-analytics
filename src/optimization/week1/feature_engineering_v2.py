#!/usr/bin/env python3
"""
WEEK 1 - Feature Engineering V2
+10 nouvelles features avancées
Objectif: Améliorer la représentation des données
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FeatureEngineerV2:
    """Crée de nouvelles features avancées pour le modèle NBA."""
    
    def __init__(self):
        self.df = None
        self.new_features = []
    
    def load_data(self):
        """Charge les features existantes."""
        logger.info("Chargement des données...")
        self.df = pd.read_parquet("data/gold/ml_features/features_all.parquet")
        logger.info(f"Dataset chargé: {len(self.df)} matchs, {len(self.df.columns)} features")
        return self.df
    
    def create_momentum_features(self):
        """1-2. Features de momentum avancées."""
        logger.info("Création features momentum...")
        
        # 1. Momentum différentiel (forme relative)
        self.df['momentum_diff'] = (
            self.df['home_wins_last_10'] - self.df['away_wins_last_10']
        )
        
        # 2. Momentum pondéré (récence)
        if 'home_win_pct_last_5' in self.df.columns and 'home_win_pct' in self.df.columns:
            self.df['home_momentum_trend'] = (
                self.df['home_win_pct_last_5'] - self.df['home_win_pct']
            )
            self.df['away_momentum_trend'] = (
                self.df['away_win_pct_last_5'] - self.df['away_win_pct']
            )
            self.df['momentum_trend_diff'] = (
                self.df['home_momentum_trend'] - self.df['away_momentum_trend']
            )
            self.new_features.extend([
                'momentum_diff', 'home_momentum_trend', 
                'away_momentum_trend', 'momentum_trend_diff'
            ])
        else:
            self.new_features.append('momentum_diff')
    
    def create_efficiency_features(self):
        """3-4. Features d'efficacité."""
        logger.info("Création features efficacité...")
        
        # 3. Efficacité offensive relative
        if all(col in self.df.columns for col in ['home_avg_pts_last_5', 'away_avg_pts_last_5']):
            self.df['offensive_efficiency_diff'] = (
                self.df['home_avg_pts_last_5'] - self.df['away_avg_pts_last_5']
            )
            self.new_features.append('offensive_efficiency_diff')
        
        # 4. Différentiel de rebonds (contrôle du terrain)
        if all(col in self.df.columns for col in ['home_avg_reb_last_5', 'away_avg_reb_last_5']):
            self.df['rebounding_diff'] = (
                self.df['home_avg_reb_last_5'] - self.df['away_avg_reb_last_5']
            )
            self.new_features.append('rebounding_diff')
    
    def create_context_features(self):
        """5-6. Features de contexte du match."""
        logger.info("Création features contexte...")
        
        # 5. Avantage de fatigue combiné
        self.df['fatigue_combo'] = (
            self.df['home_is_back_to_back'].astype(int) + 
            self.df['away_is_back_to_back'].astype(int)
        )
        
        # 6. Avantage de repos (carré pour non-linéarité)
        self.df['rest_advantage_squared'] = self.df['rest_advantage'] ** 2
        
        self.new_features.extend(['fatigue_combo', 'rest_advantage_squared'])
    
    def create_interaction_features(self):
        """7-8. Features d'interaction."""
        logger.info("Création features interaction...")
        
        # 7. Win % diff × Momentum (combinaison niveau + forme)
        self.df['win_pct_momentum_interaction'] = (
            self.df['win_pct_diff'] * self.df['momentum_diff']
        )
        
        # 8. Home advantage × H2H (contexte historique local)
        self.df['home_h2h_advantage'] = (
            self.df['h2h_home_win_rate'] * self.df['home_win_pct']
        )
        
        self.new_features.extend(['win_pct_momentum_interaction', 'home_h2h_advantage'])
    
    def create_nonlinear_features(self):
        """9-10. Transformations non-linéaires."""
        logger.info("Création features non-linéaires...")
        
        # 9. Win % diff au carré (effet amplifié aux extrêmes)
        self.df['win_pct_diff_squared'] = self.df['win_pct_diff'] ** 2
        
        # 10. H2H pressure (intensité de la rivalité)
        self.df['h2h_pressure'] = (
            self.df['h2h_games'] * np.abs(self.df['h2h_home_win_rate'] - 0.5)
        )
        
        self.new_features.extend(['win_pct_diff_squared', 'h2h_pressure'])
    
    def create_advanced_h2h(self):
        """11. Feature H2H avancée."""
        logger.info("Création feature H2H avancée...")
        
        # 11. Marge H2H ajustée par nombre de matchs
        self.df['h2h_margin_weighted'] = (
            self.df['h2h_avg_margin'] * np.log1p(self.df['h2h_games'])
        )
        
        self.new_features.append('h2h_margin_weighted')
    
    def validate_features(self):
        """Valide les nouvelles features."""
        logger.info("\n" + "="*70)
        logger.info("VALIDATION DES NOUVELLES FEATURES")
        logger.info("="*70)
        
        for feature in self.new_features:
            if feature in self.df.columns:
                null_count = self.df[feature].isnull().sum()
                logger.info(f"✓ {feature:<30} | Nulls: {null_count:>4} | "
                           f"Range: [{self.df[feature].min():>8.3f}, {self.df[feature].max():>8.3f}]")
            else:
                logger.warning(f"✗ {feature} non créée")
        
        logger.info(f"\nTotal: {len(self.new_features)} nouvelles features créées")
        logger.info(f"Total features dataset: {len(self.df.columns)}")
    
    def save_enhanced_dataset(self):
        """Sauvegarde le dataset enrichi."""
        output_path = "data/gold/ml_features/features_enhanced_v2.parquet"
        
        logger.info(f"\nSauvegarde du dataset enrichi...")
        self.df.to_parquet(output_path, index=False)
        logger.info(f"✓ Dataset sauvegardé: {output_path}")
        logger.info(f"  Dimensions: {len(self.df)} rows × {len(self.df.columns)} columns")
        
        # Sauvegarder la liste des nouvelles features
        import json
        with open('results/week1/new_features_v2.json', 'w') as f:
            json.dump({
                'new_features': self.new_features,
                'total_features': len(self.df.columns),
                'feature_count': len([c for c in self.df.columns if c not in [
                    'game_id', 'season', 'game_date', 'season_type',
                    'home_team_id', 'home_team_name', 'home_team_abbr',
                    'away_team_id', 'away_team_name', 'away_team_abbr',
                    'home_wl', 'away_wl', 'target'
                ]])
            }, f, indent=2)
    
    def run(self):
        """Pipeline complet de feature engineering."""
        logger.info("="*70)
        logger.info("FEATURE ENGINEERING V2 - WEEK 1")
        logger.info("="*70)
        
        self.load_data()
        
        # Créer toutes les features
        self.create_momentum_features()
        self.create_efficiency_features()
        self.create_context_features()
        self.create_interaction_features()
        self.create_nonlinear_features()
        self.create_advanced_h2h()
        
        # Valider et sauvegarder
        self.validate_features()
        self.save_enhanced_dataset()
        
        logger.info("\n" + "="*70)
        logger.info("FEATURE ENGINEERING TERMINÉ!")
        logger.info("="*70)
        
        return self.df


def main():
    """Point d'entrée."""
    engineer = FeatureEngineerV2()
    df = engineer.run()
    return df


if __name__ == "__main__":
    main()
