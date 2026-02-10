#!/usr/bin/env python3
"""
Transform Live Features to V3

Pipeline qui transforme les features de base (55+) en features V3 (85+)
en utilisant feature_engineering_v3.py - ZERO REDONDANCE.

Usage:
    python scripts/transform_live_to_v3.py
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'ml' / 'pipeline'))

from live_base_engineer import LiveBaseEngineer
from feature_engineering_v3 import FeatureEngineeringV3

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def transform_live_to_v3():
    """
    Transforme les features live de base en V3.
    
    Etapes:
        1. Charge les 783 matchs 2025-26 depuis l'API
        2. Calcule les features de base (55+) avec LiveBaseEngineer
        3. Transforme en V3 (85+) avec FeatureEngineeringV3
        4. Sauvegarde le resultat
    """
    logger.info("="*70)
    logger.info("TRANSFORMATION LIVE FEATURES -> V3")
    logger.info("="*70)
    
    # === ÉTAPE 1: Récupérer les matchs 2025-26 ===
    logger.info("\n[1/4] Recuperation des matchs 2025-26...")
    
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'ingestion'))
    try:
        from external_api_nba import NBAAPIManager
        api = NBAAPIManager()
        api_result = api.fetch_2025_26_results()
        games = api_result['results']
        logger.info(f"✓ {len(games)} matchs recuperes via {api_result['method']}")
    except Exception as e:
        logger.error(f"❌ Erreur API: {e}")
        # Fallback: utiliser features deja calculees
        logger.info("Fallback: utilisation des features deja calculees...")
        df_base = pd.read_parquet('data/gold/ml_features/features_2025-26_live.parquet')
        logger.info(f"✓ {len(df_base)} matchs charges depuis features_2025-26_live.parquet")
        
        # Passer directement à l'étape 3
        logger.info("\n[3/4] Transformation en V3...")
        v3_transformer = FeatureEngineeringV3(input_df=df_base)
        df_v3 = v3_transformer.process()
        
        # Étape 4
        logger.info("\n[4/4] Sauvegarde...")
        output_path = Path('data/gold/ml_features/features_2025-26_v3.parquet')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_v3.to_parquet(output_path)
        logger.info(f"✓ Features V3 sauvegardees: {output_path}")
        logger.info(f"  Total: {len(df_v3)} matchs, {len(df_v3.columns)} features")
        
        return df_v3
    
    # === ÉTAPE 2: Calculer features de base ===
    logger.info("\n[2/4] Calcul des features de base (55+)...")
    base_engineer = LiveBaseEngineer()
    
    all_features = []
    for i, game in enumerate(games):
        if i % 100 == 0:
            logger.info(f"  Traitement: {i}/{len(games)}")
        
        if not game.get('is_played'):
            continue
        
        features = base_engineer.calculate_match_features(
            game_id=game['game_id'],
            home_team=game['home_team'],
            away_team=game['away_team'],
            game_date=game['game_date'],
            home_score=game.get('home_score'),
            away_score=game.get('away_score')
        )
        
        if features:
            all_features.append(features)
    
    df_base = pd.DataFrame(all_features)
    logger.info(f"✓ {len(df_base)} matchs avec features de base")
    logger.info(f"  Colonnes: {len(df_base.columns)}")
    
    # Sauvegarder les features de base
    base_path = Path('data/gold/ml_features/features_2025-26_base.parquet')
    base_path.parent.mkdir(parents=True, exist_ok=True)
    df_base.to_parquet(base_path)
    logger.info(f"✓ Features de base sauvegardees: {base_path}")
    
    # === ÉTAPE 3: Transformer en V3 ===
    logger.info("\n[3/4] Transformation en features V3 (85+)...")
    logger.info("Utilisation de FeatureEngineeringV3 avec DataFrame...")
    
    v3_transformer = FeatureEngineeringV3(input_df=df_base)
    df_v3 = v3_transformer.process()
    
    logger.info(f"✓ Transformation terminee")
    logger.info(f"  Total: {len(df_v3)} matchs, {len(df_v3.columns)} features")
    
    # === ÉTAPE 4: Sauvegarder ===
    logger.info("\n[4/4] Sauvegarde des features V3...")
    output_path = Path('data/gold/ml_features/features_2025-26_v3.parquet')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df_v3.to_parquet(output_path)
    logger.info(f"✓ Sauvegarde: {output_path}")
    
    # Metadonnees
    metadata = {
        'created_at': datetime.now().isoformat(),
        'total_matches': len(df_v3),
        'total_features': len(df_v3.columns),
        'base_features': len(df_base.columns),
        'v3_features_added': len(df_v3.columns) - len(df_base.columns),
        'feature_names': list(df_v3.columns),
        'method': 'FeatureEngineeringV3 avec DataFrame live'
    }
    
    import json
    metadata_path = output_path.with_suffix('.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"✓ Metadonnees: {metadata_path}")
    
    # === RÉSULTAT ===
    logger.info("\n" + "="*70)
    logger.info("TRANSFORMATION TERMINEE AVEC SUCCES")
    logger.info("="*70)
    logger.info(f"✓ Matchs traites: {len(df_v3)}")
    logger.info(f"✓ Features V3: {len(df_v3.columns)}")
    logger.info(f"✓ Fichier: {output_path}")
    logger.info("\nProchaine etape: Entrainement du modele avec ces features")
    
    return df_v3


def verify_v3_features():
    """Verifie que toutes les features attendues sont presentes."""
    logger.info("\n" + "="*70)
    logger.info("VERIFICATION DES FEATURES V3")
    logger.info("="*70)
    
    # Charger features V3 historiques pour comparaison
    df_hist = pd.read_parquet('data/gold/ml_features/features_v3.parquet')
    hist_features = set(df_hist.columns)
    logger.info(f"Features historiques: {len(hist_features)}")
    
    # Charger features V3 live
    df_live = pd.read_parquet('data/gold/ml_features/features_2025-26_v3.parquet')
    live_features = set(df_live.columns)
    logger.info(f"Features live: {len(live_features)}")
    
    # Comparer
    common = hist_features & live_features
    missing_in_live = hist_features - live_features
    extra_in_live = live_features - hist_features
    
    logger.info(f"\nFeatures communes: {len(common)}")
    
    if missing_in_live:
        logger.warning(f"\n⚠️  Features MANQUANTES dans live ({len(missing_in_live)}):")
        for f in sorted(missing_in_live)[:10]:
            logger.warning(f"  - {f}")
        if len(missing_in_live) > 10:
            logger.warning(f"  ... et {len(missing_in_live) - 10} autres")
    else:
        logger.info("\n✅ Toutes les features historiques sont presentes dans live!")
    
    if extra_in_live:
        logger.info(f"\nℹ️  Features supplementaires dans live ({len(extra_in_live)}):")
        for f in sorted(extra_in_live)[:5]:
            logger.info(f"  - {f}")
    
    logger.info("\n" + "="*70)
    
    return len(missing_in_live) == 0


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Transforme les features live en V3')
    parser.add_argument('--verify', action='store_true', 
                       help='Verifie les features apres transformation')
    args = parser.parse_args()
    
    # Executer transformation
    df_v3 = transform_live_to_v3()
    
    # Verifier si demande
    if args.verify or True:  # Toujours verifier
        is_valid = verify_v3_features()
        
        if is_valid:
            print("\n✅ VERIFICATION REUSSIE - Pret pour l'entrainement!")
        else:
            print("\n⚠️  VERIFICATION ECHOUEE - Certaines features sont manquantes")
            print("Le modele pourrait ne pas fonctionner correctement")
