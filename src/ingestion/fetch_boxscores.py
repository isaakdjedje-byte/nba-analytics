#!/usr/bin/env python3
"""
Recuperation des box scores detailles par mois
NBA-15: Box scores partitionnes pour analyses ML
"""

import json
import logging
import os
import time
from collections import defaultdict
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


def fetch_all_boxscores(season: str = SEASON, season_type: str = "Regular Season") -> List[Dict]:
    """
    Recupere tous les box scores en une seule requete API
    
    Args:
        season: Saison
        season_type: Type de saison
    
    Returns:
        Liste de tous les matchs avec stats detaillees
    """
    logger.info(f"[PACKAGE] Recuperation box scores {season} ({season_type})...")
    
    try:
        games = fetch_with_retry(
            leaguegamefinder.LeagueGameFinder,
            season_nullable=season,
            season_type_nullable=season_type,
            league_id_nullable="00"
        )
        
        games_data = games.get_normalized_dict()
        games_list = games_data.get('LeagueGameFinderResults', [])
        
        # Formater et enrichir les donnees
        formatted_games = []
        for game in games_list:
            game_entry = {
                'game_id': game.get('GAME_ID'),
                'game_date': game.get('GAME_DATE'),
                'season': season,
                'season_type': season_type,
                'team_id': game.get('TEAM_ID'),
                'team_name': game.get('TEAM_NAME'),
                'team_abbreviation': game.get('TEAM_ABBREVIATION'),
                'matchup': game.get('MATCHUP'),
                'wl': game.get('WL'),
                'points': game.get('PTS'),
                # Stats de base
                'fgm': game.get('FGM'),
                'fga': game.get('FGA'),
                'fg_pct': game.get('FG_PCT'),
                'fg3m': game.get('FG3M'),
                'fg3a': game.get('FG3A'),
                'fg3_pct': game.get('FG3_PCT'),
                'ftm': game.get('FTM'),
                'fta': game.get('FTA'),
                'ft_pct': game.get('FT_PCT'),
                # Rebonds
                'oreb': game.get('OREB'),
                'dreb': game.get('DREB'),
                'reb': game.get('REB'),
                # Autres stats
                'ast': game.get('AST'),
                'stl': game.get('STL'),
                'blk': game.get('BLK'),
                'tov': game.get('TOV'),
                'pf': game.get('PF'),
                'plus_minus': game.get('PLUS_MINUS'),
                # Minutes
                'min': game.get('MIN')
            }
            formatted_games.append(game_entry)
        
        # Trier par date
        formatted_games.sort(key=lambda x: x['game_date'])
        
        logger.info(f"[OK] {len(formatted_games)} box scores recuperes")
        return formatted_games
        
    except Exception as e:
        logger.error(f"[ERROR] Erreur box scores: {e}")
        return []


def partition_by_month(games: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Partitionne les matchs par mois
    
    Args:
        games: Liste des matchs
    
    Returns:
        Dictionnaire {mois: liste_matchs}
    """
    partitions = defaultdict(list)
    
    for game in games:
        game_date = game.get('game_date', '')
        if game_date and len(game_date) >= 7:  # Format: YYYY-MM-DD
            year_month = game_date[:7]  # YYYY-MM
            year, month = year_month.split('-')
            key = f"{year}_{month}"
            partitions[key].append(game)
    
    return dict(partitions)


def partition_by_team(games: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Partitionne les matchs par equipe
    
    Args:
        games: Liste des matchs
    
    Returns:
        Dictionnaire {team_id: liste_matchs}
    """
    partitions = defaultdict(list)
    
    for game in games:
        team_id = game.get('team_id')
        if team_id:
            partitions[str(team_id)].append(game)
    
    return dict(partitions)


def save_partitions(partitions: Dict[str, List[Dict]], base_path: str, prefix: str = ""):
    """
    Sauvegarde les partitions sur disque
    
    Args:
        partitions: Dictionnaire de partitions
        base_path: Chemin de base
        prefix: Prefixe de nom de fichier
    """
    for key, games in partitions.items():
        if games:  # Ne pas sauvegarder les mois vides
            filename = f"{prefix}{key}_games.json" if prefix else f"{key}_games.json"
            filepath = os.path.join(base_path, filename)
            save_json(games, filepath)


def fetch_and_partition_boxscores(season: str = SEASON) -> Dict[str, Any]:
    """
    Orchestration complete: fetch + partitionnement
    
    Args:
        season: Saison cible
    
    Returns:
        Dictionnaire avec stats et chemins des fichiers
    """
    logger.info("="*60)
    logger.info(f"[TARGET] NBA-15: Recuperation Box Scores {season}")
    logger.info("="*60)
    
    base_path = f"{RAW_BASE}/games_boxscores"
    ensure_dir(base_path)
    
    all_games = []
    results = {
        'regular_season': {},
        'playoffs': {},
        'by_month': {},
        'by_team': {},
        'files_created': []
    }
    
    # 1. Regular Season
    logger.info("\n[PACKAGE] Regular Season...")
    rs_games = fetch_all_boxscores(season, "Regular Season")
    
    if rs_games:
        all_games.extend(rs_games)
        
        # Partitionner par mois
        rs_by_month = partition_by_month(rs_games)
        results['regular_season'] = rs_by_month
        
        # Sauvegarder par mois
        logger.info("[SAVE] Sauvegarde par mois (Regular Season)...")
        for month, games in rs_by_month.items():
            filepath = f"{base_path}/{month}_games.json"
            save_json(games, filepath)
            results['files_created'].append(filepath)
            logger.info(f"   {month}: {len(games)} matchs")
    
    # 2. Playoffs
    logger.info("\n[PLAYOFFS] Playoffs...")
    try:
        po_games = fetch_all_boxscores(season, "Playoffs")
        
        if po_games:
            all_games.extend(po_games)
            
            # Partitionner
            po_by_month = partition_by_month(po_games)
            results['playoffs'] = po_by_month
            
            # Sauvegarder
            logger.info("[SAVE] Sauvegarde Playoffs...")
            filepath = f"{base_path}/playoffs_{season.replace('-', '_')}.json"
            save_json(po_games, filepath)
            results['files_created'].append(filepath)
            logger.info(f"   Playoffs: {len(po_games)} matchs")
    except Exception as e:
        logger.warning(f"[WARNING] Pas de playoffs pour {season}: {e}")
    
    # 3. Partition par equipe (pour analyses ML)
    logger.info("\n[STATS] Partitionnement par equipe...")
    by_team = partition_by_team(all_games)
    results['by_team'] = by_team
    
    # 4. Stats finales
    total_games = len(all_games)
    unique_games = len(set(g['game_id'] for g in all_games))
    date_range = {
        'first': min(g['game_date'] for g in all_games) if all_games else None,
        'last': max(g['game_date'] for g in all_games) if all_games else None
    }
    
    results['stats'] = {
        'total_games': total_games,
        'unique_games': unique_games,
        'teams_count': len(by_team),
        'months_count': len(results['regular_season']),
        'date_range': date_range,
        'files_created': len(results['files_created'])
    }
    
    logger.info("\n" + "="*60)
    logger.info("[OK] RECUPERATION TERMINEE")
    logger.info("="*60)
    logger.info(f"[STATS] Total matchs: {total_games}")
    logger.info(f"[STATS] Matchs uniques: {unique_games}")
    logger.info(f"[STATS] Equipes: {len(by_team)}")
    logger.info(f"[STATS] Mois: {len(results['regular_season'])}")
    logger.info(f"[STATS] Fichiers crees: {len(results['files_created'])}")
    if date_range['first']:
        logger.info(f"[DATE] Periode: {date_range['first']} → {date_range['last']}")
    logger.info("="*60)
    
    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    result = fetch_and_partition_boxscores()
    print(f"\n[OK] Fichiers crees dans: data/raw/games_boxscores/")
    for filepath in result['files_created'][:5]:  # Afficher les 5 premiers
        print(f"   - {filepath}")
    if len(result['files_created']) > 5:
        print(f"   ... et {len(result['files_created']) - 5} autres")
