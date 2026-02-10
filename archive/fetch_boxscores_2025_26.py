#!/usr/bin/env python3
"""
Fetch Box Scores 2025-26

Récupère tous les box scores pour la saison 2025-26.
Usage:
    python scripts/fetch_boxscores_2025_26.py
"""

import sys
import logging
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'data'))

from boxscore_orchestrator import BoxScoreOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_all_boxscores():
    """Récupère tous les box scores pour 2025-26."""
    logger.info("="*70)
    logger.info("RÉCUPÉRATION BOX SCORES 2025-26")
    logger.info("="*70)
    
    # Charger les matchs 2025-26
    logger.info("\n[1/3] Chargement des matchs...")
    df_games = pd.read_parquet('data/gold/ml_features/features_2025-26_v3.parquet')
    game_ids = df_games['game_id'].tolist()
    logger.info(f"✓ {len(game_ids)} matchs à traiter")
    
    # Vérifier cache existant
    logger.info("\n[2/3] Vérification du cache...")
    orchestrator = BoxScoreOrchestrator(max_workers=3, delay=1.2)
    cache_stats = orchestrator.cache.get_stats()
    logger.info(f"✓ Cache: {cache_stats['total_cached']} box scores déjà présents")
    
    # Filtrer les matchs déjà en cache
    games_to_fetch = []
    for game_id in game_ids:
        if not orchestrator.cache.get(game_id):
            games_to_fetch.append(game_id)
    
    if len(games_to_fetch) == 0:
        logger.info("\n✓ Tous les box scores sont déjà en cache!")
        return
    
    logger.info(f"✓ {len(games_to_fetch)} matchs à récupérer")
    
    # Récupérer les box scores
    logger.info("\n[3/3] Récupération des box scores...")
    logger.info(f"   Workers: 3 | Délai: 1.2s | Temps estimé: {len(games_to_fetch) * 1.5 / 60:.1f} minutes")
    
    results = orchestrator.fetch_batch(games_to_fetch)
    
    # Rapport final
    successful = len([r for r in results if r is not None])
    logger.info("\n" + "="*70)
    logger.info("RÉSULTATS")
    logger.info("="*70)
    logger.info(f"✓ Récupérés: {successful}/{len(games_to_fetch)}")
    logger.info(f"✓ Échecs: {len(games_to_fetch) - successful}")
    
    # Stats finales
    final_stats = orchestrator.cache.get_stats()
    logger.info(f"✓ Total en cache: {final_stats['total_cached']}")
    
    if successful == len(games_to_fetch):
        logger.info("\n🎉 TOUS LES BOX SCORES RÉCUPÉRÉS AVEC SUCCÈS!")
    else:
        logger.warning(f"\n⚠️ {len(games_to_fetch) - successful} échecs - relancer le script pour réessayer")
    
    logger.info("="*70)


if __name__ == '__main__':
    fetch_all_boxscores()
