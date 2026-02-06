#!/usr/bin/env python3
"""
Recuperation du calendrier des matchs NBA
NBA-15: Schedules et resultats des matchs
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

import yaml
from nba_api.stats.endpoints import leaguegamefinder

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


def fetch_season_schedule(season: str = SEASON, season_type: str = "Regular Season") -> List[Dict]:
    """
    Recupere le calendrier complet d'une saison
    
    Args:
        season: Saison (format: 2023-24)
        season_type: Type de saison (Regular Season ou Playoffs)
    
    Returns:
        Liste des matchs avec details
    """
    logger.info(f"[DATE] Recuperation du calendrier {season} ({season_type})...")
    
    try:
        games = fetch_with_retry(
            leaguegamefinder.LeagueGameFinder,
            season_nullable=season,
            season_type_nullable=season_type,
            league_id_nullable="00"  # NBA
        )
        
        games_data = games.get_normalized_dict()
        games_list = games_data.get('LeagueGameFinderResults', [])
        
        # Formater les matchs
        formatted_games = []
        for game in games_list:
            formatted_games.append({
                'game_id': game.get('GAME_ID'),
                'game_date': game.get('GAME_DATE'),
                'season': season,
                'season_type': season_type,
                'team_id': game.get('TEAM_ID'),
                'team_name': game.get('TEAM_NAME'),
                'team_abbreviation': game.get('TEAM_ABBREVIATION'),
                'matchup': game.get('MATCHUP'),
                'wl': game.get('WL'),  # Win/Loss
                'points': game.get('PTS'),
                'fgm': game.get('FGM'),
                'fga': game.get('FGA'),
                'fg_pct': game.get('FG_PCT'),
                'fg3m': game.get('FG3M'),
                'fg3a': game.get('FG3A'),
                'fg3_pct': game.get('FG3_PCT'),
                'ftm': game.get('FTM'),
                'fta': game.get('FTA'),
                'ft_pct': game.get('FT_PCT'),
                'oreb': game.get('OREB'),
                'dreb': game.get('DREB'),
                'reb': game.get('REB'),
                'ast': game.get('AST'),
                'stl': game.get('STL'),
                'blk': game.get('BLK'),
                'tov': game.get('TOV'),
                'pf': game.get('PF'),
                'plus_minus': game.get('PLUS_MINUS')
            })
        
        # Trier par date
        formatted_games.sort(key=lambda x: x['game_date'])
        
        logger.info(f"[OK] {len(formatted_games)} matchs recuperes")
        return formatted_games
        
    except Exception as e:
        logger.error(f"[ERROR] Erreur recuperation calendrier: {e}")
        return []


def fetch_all_schedules(season: str = SEASON) -> Dict[str, Any]:
    """
    Recupere les calendriers Regular Season + Playoffs
    
    Args:
        season: Saison cible
    
    Returns:
        Dictionnaire avec Regular Season et Playoffs
    """
    logger.info("="*60)
    logger.info(f"[TARGET] NBA-15: Recuperation Calendriers {season}")
    logger.info("="*60)
    
    results = {
        'regular_season': [],
        'playoffs': [],
        'stats': {}
    }
    
    # 1. Regular Season
    logger.info("\n[DATE] Regular Season...")
    rs_games = fetch_season_schedule(season, "Regular Season")
    results['regular_season'] = rs_games
    
    # Sauvegarder temporairement
    if rs_games:
        rs_filepath = f"{RAW_BASE}/schedules/schedule_{season.replace('-', '_')}_regular.json"
        save_json(rs_games, rs_filepath)
    
    # 2. Playoffs (peut etre vide si saison en cours)
    logger.info("\n[PLAYOFFS] Playoffs...")
    try:
        po_games = fetch_season_schedule(season, "Playoffs")
        results['playoffs'] = po_games
        
        if po_games:
            po_filepath = f"{RAW_BASE}/schedules/schedule_{season.replace('-', '_')}_playoffs.json"
            save_json(po_games, po_filepath)
    except Exception as e:
        logger.warning(f"[WARNING] Pas de playoffs pour {season}: {e}")
        results['playoffs'] = []
    
    # 3. Combiner et sauvegarder
    all_games = rs_games + results['playoffs']
    
    # Ajouter indicateur playoffs
    for game in all_games:
        game['is_playoff'] = game in results['playoffs']
    
    # Sauvegarder combine
    combined_filepath = f"{RAW_BASE}/schedules/schedule_{season.replace('-', '_')}.json"
    save_json(all_games, combined_filepath)
    
    # Statistiques
    unique_games = len(set(g['game_id'] for g in all_games))
    date_range = {
        'first_game': min(g['game_date'] for g in all_games) if all_games else None,
        'last_game': max(g['game_date'] for g in all_games) if all_games else None
    }
    
    results['stats'] = {
        'regular_season_count': len(rs_games),
        'playoffs_count': len(results['playoffs']),
        'total_games': len(all_games),
        'unique_games': unique_games,
        'date_range': date_range
    }
    
    logger.info("\n" + "="*60)
    logger.info("[OK] RECUPERATION TERMINEE")
    logger.info("="*60)
    logger.info(f"[STATS] Regular Season: {len(rs_games)} matchs")
    logger.info(f"[STATS] Playoffs: {len(results['playoffs'])} matchs")
    logger.info(f"[STATS] Total: {len(all_games)} matchs")
    if date_range['first_game']:
        logger.info(f"[DATE] Du {date_range['first_game']} au {date_range['last_game']}")
    logger.info("="*60)
    
    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    result = fetch_all_schedules()
    print(f"\n[OK] Fichiers crees:")
    print(f"   - data/raw/schedules/schedule_{SEASON.replace('-', '_')}.json")
    print(f"   - data/raw/schedules/schedule_{SEASON.replace('-', '_')}_regular.json")
    if result['playoffs']:
        print(f"   - data/raw/schedules/schedule_{SEASON.replace('-', '_')}_playoffs.json")
