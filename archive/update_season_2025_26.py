#!/usr/bin/env python3
"""
Script de Setup Saison 2025-26
Récupère toutes les données nécessaires pour la saison en cours

Usage:
    python scripts/update_season_2025_26.py
    python scripts/update_season_2025_26.py --skip-fetch  # Utilise données existantes
    python scripts/update_season_2025_26.py --quick       # Mode rapide (sans boxscores)
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Ajouter paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nba.config import SeasonConfig, settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_season_schedule():
    """Récupère le calendrier complet 2025-26"""
    logger.info("\n" + "="*70)
    logger.info("ETAPE 1: RECUPERATION DU CALENDRIER 2025-26")
    logger.info("="*70)
    
    try:
        from src.ingestion.fetch_schedules import fetch_all_schedules, save_json
        
        season = SeasonConfig.CURRENT_SEASON
        schedules = fetch_all_schedules(season=season)
        
        logger.info(f"Calendrier récupéré: {len(schedules.get('regular_season', []))} matchs réguliers")
        logger.info(f"Playoffs: {len(schedules.get('playoffs', []))} matchs")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur récupération calendrier: {e}")
        return False


def fetch_teams_and_rosters():
    """Récupère les équipes et rosters"""
    logger.info("\n" + "="*70)
    logger.info("ETAPE 2: RECUPERATION DES EQUIPES ET ROSTERS")
    logger.info("="*70)
    
    try:
        from src.ingestion.fetch_teams_rosters import fetch_and_save_all_teams
        
        season = SeasonConfig.CURRENT_SEASON
        result = fetch_and_save_all_teams(season=season)
        
        logger.info(f"Équipes récupérées: {result}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur récupération équipes: {e}")
        return False


def fetch_team_stats():
    """Récupère les stats des équipes"""
    logger.info("\n" + "="*70)
    logger.info("ETAPE 3: RECUPERATION DES STATS EQUIPES")
    logger.info("="*70)
    
    try:
        from src.ingestion.fetch_team_stats import fetch_all_teams_stats
        
        season = SeasonConfig.CURRENT_SEASON
        stats = fetch_all_teams_stats(season=season)
        
        logger.info(f"Stats récupérées pour {len(stats)} équipes")
        return True
        
    except Exception as e:
        logger.error(f"Erreur récupération stats: {e}")
        return False


def fetch_boxscores():
    """Récupère les boxscores des matchs déjà joués"""
    logger.info("\n" + "="*70)
    logger.info("ETAPE 4: RECUPERATION DES BOXSCORES")
    logger.info("="*70)
    
    try:
        from src.ingestion.fetch_boxscores import fetch_season_boxscores
        
        season = SeasonConfig.CURRENT_SEASON
        boxscores = fetch_season_boxscores(season=season)
        
        logger.info(f"Boxscores récupérés: {len(boxscores)} matchs")
        return True
        
    except Exception as e:
        logger.error(f"Erreur récupération boxscores: {e}")
        logger.warning("Les boxscores peuvent être récupérés plus tard")
        return False


def generate_full_season_predictions():
    """Génère les prédictions pour toute la saison"""
    logger.info("\n" + "="*70)
    logger.info("ETAPE 5: GENERATION DES PREDICTIONS COMPLETES")
    logger.info("="*70)
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'ml' / 'pipeline'))
        from full_season_pipeline import FullSeasonPipeline
        
        pipeline = FullSeasonPipeline()
        result = pipeline.predict_full_season()
        
        if result:
            logger.info(f"Prédictions générées: {len(result.get('predictions', []))} matchs")
            return True
        else:
            logger.error("Échec génération prédictions")
            return False
            
    except Exception as e:
        logger.error(f"Erreur génération prédictions: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def verify_setup():
    """Vérifie que tout est en place"""
    logger.info("\n" + "="*70)
    logger.info("VERIFICATION DU SETUP")
    logger.info("="*70)
    
    checks = {
        'Schedule file': Path(f"data/raw/schedules/schedule_{SeasonConfig.get_season_file_suffix()}.json").exists(),
        'Teams file': Path("data/raw/teams.json").exists(),
        'Rosters dir': Path("data/raw/rosters").exists(),
        'Predictions file': Path(f"predictions/season_{SeasonConfig.CURRENT_SEASON}_full.json").exists(),
    }
    
    for check, status in checks.items():
        symbol = "✓" if status else "✗"
        logger.info(f"{symbol} {check}: {'OK' if status else 'MANQUANT'}")
    
    all_ok = all(checks.values())
    
    if all_ok:
        logger.info("\n✅ Setup complet! Tous les fichiers sont en place.")
    else:
        logger.warning("\n⚠️  Setup partiel. Certaines étapes ont échoué.")
    
    return all_ok


def main():
    parser = argparse.ArgumentParser(
        description='Setup complet saison 2025-26 NBA'
    )
    parser.add_argument('--skip-fetch', action='store_true',
                       help='Skip la récupération API (utilise données existantes)')
    parser.add_argument('--quick', action='store_true',
                       help='Mode rapide: skip boxscores')
    parser.add_argument('--only-predictions', action='store_true',
                       help='Génère uniquement les prédictions')
    
    args = parser.parse_args()
    
    logger.info("\n" + "="*70)
    logger.info("SETUP SAISON NBA 2025-26")
    logger.info("="*70)
    logger.info(f"Saison: {SeasonConfig.CURRENT_SEASON}")
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*70 + "\n")
    
    success_count = 0
    total_steps = 5
    
    if args.only_predictions:
        # Uniquement générer les prédictions
        if generate_full_season_predictions():
            success_count = 1
        total_steps = 1
    else:
        # Setup complet
        if not args.skip_fetch:
            if fetch_season_schedule():
                success_count += 1
            
            if fetch_teams_and_rosters():
                success_count += 1
            
            if fetch_team_stats():
                success_count += 1
            
            if not args.quick:
                if fetch_boxscores():
                    success_count += 1
            else:
                logger.info("Mode rapide: boxscores ignorés")
                success_count += 1
        else:
            logger.info("Skip fetch: utilisation des données existantes")
            success_count += 4
        
        # Toujours générer les prédictions
        if generate_full_season_predictions():
            success_count += 1
    
    # Vérification finale
    logger.info("\n" + "="*70)
    logger.info("RESUME")
    logger.info("="*70)
    logger.info(f"Étapes réussies: {success_count}/{total_steps}")
    
    verify_setup()
    
    logger.info("\n" + "="*70)
    logger.info("SETUP TERMINE")
    logger.info("="*70)
    logger.info("\nProchaines étapes:")
    logger.info("1. Configurer le cron job à 9h:")
    logger.info("   0 9 * * * cd /path/to/nba-analytics && python src/ml/pipeline/full_season_pipeline.py --daily-update")
    logger.info("\n2. Ou exécuter manuellement:")
    logger.info("   python src/ml/pipeline/full_season_pipeline.py --daily-update")
    logger.info("\n3. Voir le résumé:")
    logger.info("   python src/ml/pipeline/full_season_pipeline.py --summary")
    logger.info("="*70 + "\n")


if __name__ == "__main__":
    main()
