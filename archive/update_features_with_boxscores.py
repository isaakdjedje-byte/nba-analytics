#!/usr/bin/env python3
"""
Update Features with Real Box Scores

Met à jour les features 2025-26 avec les vraies données de box scores
récupérées via PlayerGameLogs.

Usage:
    python scripts/update_features_with_boxscores.py
"""

import sys
import logging
from pathlib import Path

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'data'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'ml' / 'pipeline'))

from boxscore_orchestrator_v2 import BoxScoreOrchestratorV2
from feature_engineering_v3 import FeatureEngineeringV3

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def update_features_with_boxscores():
    """Met à jour les features avec les vraies données de box scores."""
    logger.info("="*70)
    logger.info("MISE À JOUR FEATURES AVEC VRAIES DONNÉES BOX SCORES")
    logger.info("="*70)
    
    # Étape 1: Charger les features existantes
    logger.info("\n[1/4] Chargement features existantes...")
    df_features = pd.read_parquet('data/gold/ml_features/features_2025-26_v3.parquet')
    logger.info(f"✓ {len(df_features)} matchs chargés")
    
    # Étape 2: Récupérer les box scores
    logger.info("\n[2/4] Récupération box scores...")
    orchestrator = BoxScoreOrchestratorV2()
    
    # Vérifier si déjà en cache
    # Sinon, les récupérer
    # Note: normalement déjà fait par le test précédent
    
    # Étape 3: Mettre à jour les features avec vraies données
    logger.info("\n[3/4] Mise à jour des features...")
    
    updated_count = 0
    for idx, row in df_features.iterrows():
        game_id = row['game_id']
        
        # Récupérer box scores pour ce match
        home_box, away_box = orchestrator.get_boxscores_for_game(game_id)
        
        if home_box and away_box:
            # Mettre à jour avec vraies données
            df_features.at[idx, 'home_reb'] = home_box.reb
            df_features.at[idx, 'away_reb'] = away_box.reb
            df_features.at[idx, 'home_ast'] = home_box.ast
            df_features.at[idx, 'away_ast'] = away_box.ast
            df_features.at[idx, 'home_stl'] = home_box.stl
            df_features.at[idx, 'away_stl'] = away_box.stl
            df_features.at[idx, 'home_blk'] = home_box.blk
            df_features.at[idx, 'away_blk'] = away_box.blk
            df_features.at[idx, 'home_tov'] = home_box.tov
            df_features.at[idx, 'away_tov'] = away_box.tov
            df_features.at[idx, 'home_pf'] = home_box.pf
            df_features.at[idx, 'away_pf'] = away_box.pf
            
            # Calculer moyennes sur 5 matchs avec vraies données
            # (Nécessite de recalculer les rolling averages)
            
            updated_count += 1
            
            if updated_count % 100 == 0:
                logger.info(f"  Mis à jour: {updated_count}/{len(df_features)}")
    
    logger.info(f"✓ {updated_count} matchs mis à jour avec vraies données")
    
    # Étape 4: Sauvegarder
    logger.info("\n[4/4] Sauvegarde...")
    output_path = Path('data/gold/ml_features/features_2025-26_v3_real.parquet')
    df_features.to_parquet(output_path)
    logger.info(f"✓ Sauvegardé: {output_path}")
    
    logger.info("\n" + "="*70)
    logger.info("Mise à jour terminée")
    logger.info("="*70)
    
    return df_features


if __name__ == '__main__':
    update_features_with_boxscores()
