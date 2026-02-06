#!/usr/bin/env python3
"""
Recuperation des statistiques collectives des equipes
NBA-15: Win/Loss records et stats d'equipe
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

import yaml
from nba_api.stats.endpoints import leaguedashteamstats

logger = logging.getLogger(__name__)

# Charger configuration
CONFIG_PATH = "src/config/seasons_config.yaml"
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r') as f:
        CONFIG = yaml.safe_load(f)
else:
    CONFIG = {
        'parametres_fetch': {'delay_seconds': 2, 'retry_attempts': 3},
        'paths': {'raw_base': 'data/raw'}
    }

DELAY = CONFIG['parametres_fetch']['delay_seconds']
RETRY = CONFIG['parametres_fetch']['retry_attempts']
RAW_BASE = CONFIG['paths']['raw_base']

SEASON = "2023-24"  # Saison cible


def ensure_dir(path: str):
    """Cree le repertoire s'il n'existe pas"""
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"[DIR] Cree: {path}")


def save_json(data: Any, filepath: str):
    """Sauvegarde les donnees avec metadonnees"""
    output = {
        'data': data,
        'metadata': {
            'export_date': datetime.now().isoformat(),
            'record_count': len(data) if isinstance(data, list) else 1,
            'source': 'nba-api',
            'season': SEASON,
            'ticket': 'NBA-15'
        }
    }
    
    ensure_dir(os.path.dirname(filepath))
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    logger.info(f"[SAVE] Sauvegarde: {filepath}")


def fetch_with_retry(func, *args, **kwargs):
    """Execute une fonction avec retry en cas d'erreur"""
    for attempt in range(RETRY):
        try:
            time.sleep(DELAY)  # Rate limiting
            return func(*args, **kwargs)
        except Exception as e:
            if attempt < RETRY - 1:
                wait_time = DELAY * (attempt + 1)
                logger.warning(f"[WARNING] Tentative {attempt + 1}/{RETRY} echouee: {e}")
                logger.info(f"⏳ Attente {wait_time}s avant retry...")
                time.sleep(wait_time)
            else:
                logger.error(f"[ERROR] Echec apres {RETRY} tentatives: {e}")
                raise


def fetch_team_stats(season: str = SEASON, season_type: str = "Regular Season") -> List[Dict]:
    """
    Recupere les statistiques collectives des equipes
    
    Args:
        season: Saison (format: 2023-24)
        season_type: Type de saison
    
    Returns:
        Liste des stats par equipe (W, L, PCT, etc.)
    """
    logger.info(f"[STATS] Recuperation stats equipes {season} ({season_type})...")
    
    try:
        stats = fetch_with_retry(
            leaguedashteamstats.LeagueDashTeamStats,
            season=season,
            season_type_all_star=season_type,
            measure_type_detailed_defense="Base",
            per_mode_detailed="Totals"
        )
        
        stats_data = stats.get_normalized_dict()
        teams_stats = stats_data.get('LeagueDashTeamStats', [])
        
        # Formater les stats
        formatted_stats = []
        for team in teams_stats:
            formatted_stats.append({
                'team_id': team.get('TEAM_ID'),
                'team_name': team.get('TEAM_NAME'),
                'team_abbreviation': team.get('TEAM_ABBREVIATION'),
                'season': season,
                'season_type': season_type,
                'games_played': team.get('GP'),
                'wins': team.get('W'),
                'losses': team.get('L'),
                'win_pct': team.get('W_PCT'),
                'minutes': team.get('MIN'),
                'points': team.get('PTS'),
                'fgm': team.get('FGM'),
                'fga': team.get('FGA'),
                'fg_pct': team.get('FG_PCT'),
                'fg3m': team.get('FG3M'),
                'fg3a': team.get('FG3A'),
                'fg3_pct': team.get('FG3_PCT'),
                'ftm': team.get('FTM'),
                'fta': team.get('FTA'),
                'ft_pct': team.get('FT_PCT'),
                'oreb': team.get('OREB'),
                'dreb': team.get('DREB'),
                'reb': team.get('REB'),
                'ast': team.get('AST'),
                'tov': team.get('TOV'),
                'stl': team.get('STL'),
                'blk': team.get('BLK'),
                'pf': team.get('PF'),
                'plus_minus': team.get('PLUS_MINUS')
            })
        
        logger.info(f"[OK] {len(formatted_stats)} equipes")
        return formatted_stats
        
    except Exception as e:
        logger.error(f"[ERROR] Erreur stats equipes: {e}")
        return []


def fetch_all_team_stats(season: str = SEASON) -> Dict[str, Any]:
    """
    Recupere les stats Regular Season et Playoffs
    
    Args:
        season: Saison cible
    
    Returns:
        Dictionnaire avec RS et Playoffs
    """
    logger.info("="*60)
    logger.info(f"[TARGET] NBA-15: Recuperation Stats Equipes {season}")
    logger.info("="*60)
    
    results = {
        'regular_season': [],
        'playoffs': [],
        'consolidated': []
    }
    
    # 1. Regular Season
    logger.info("\n[STATS] Regular Season...")
    rs_stats = fetch_team_stats(season, "Regular Season")
    results['regular_season'] = rs_stats
    
    # 2. Playoffs
    logger.info("\n[PLAYOFFS] Playoffs...")
    try:
        po_stats = fetch_team_stats(season, "Playoffs")
        results['playoffs'] = po_stats
    except Exception as e:
        logger.warning(f"[WARNING] Pas de stats playoffs pour {season}: {e}")
        results['playoffs'] = []
    
    # 3. Consolider (RS + indicateur playoffs)
    consolidated = []
    
    # Ajouter RS
    for stat in rs_stats:
        stat['is_playoff'] = False
        consolidated.append(stat)
    
    # Ajouter Playoffs si existent
    if results['playoffs']:
        for stat in results['playoffs']:
            stat['is_playoff'] = True
            consolidated.append(stat)
    
    results['consolidated'] = consolidated
    
    # Sauvegarder
    filepath = f"{RAW_BASE}/teams_stats/team_stats_{season.replace('-', '_')}.json"
    save_json(consolidated, filepath)
    
    # Statistiques de validation
    if rs_stats:
        total_wins = sum(s['wins'] for s in rs_stats if s['wins'])
        total_losses = sum(s['losses'] for s in rs_stats if s['losses'])
        
        logger.info("\n" + "="*60)
        logger.info("[OK] RECUPERATION TERMINEE")
        logger.info("="*60)
        logger.info(f"[STATS] Equipes: {len(rs_stats)}")
        logger.info(f"[STATS] Victoires totales: {total_wins}")
        logger.info(f"[STATS] Defaites totales: {total_losses}")
        
        # Verification coherence
        if total_wins == total_losses:
            logger.info("[OK] Coherence W/L verifiee")
        else:
            logger.warning(f"[WARNING] Desequilibre W/L: {total_wins} vs {total_losses}")
        
        logger.info("="*60)
    
    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    result = fetch_all_team_stats()
    print(f"\n[OK] Fichier cree:")
    print(f"   - data/raw/teams_stats/team_stats_{SEASON.replace('-', '_')}.json")
