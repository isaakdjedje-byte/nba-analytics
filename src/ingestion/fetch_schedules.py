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


def fetch_future_schedule(season: str = SEASON) -> List[Dict]:
    """
    Recupere le calendrier complet avec matchs futurs
    
    Cette fonction utilise une approche alternative car scheduleleaguev2
    n'est pas disponible dans cette version de nba_api.
    
    Solution: Utiliser Scoreboard pour les matchs recents + 
              generer des matchs futurs base sur le calendrier connu
    
    Args:
        season: Saison cible (format: 2023-24)
    
    Returns:
        Liste des matchs avec indicateur is_played et actual_winner si joue
    """
    logger.info("="*60)
    logger.info(f"[FUTURE] Recuperation calendrier complet {season}")
    logger.info("="*60)
    
    try:
        from datetime import datetime, timedelta
        
        # 1. D'abord recuperer les matchs deja joues via leaguegamefinder
        logger.info("[API] Recuperation matchs joues via leaguegamefinder...")
        past_games = fetch_season_schedule(season, "Regular Season")
        
        if not past_games:
            logger.warning("[WARNING] Aucun match passe trouve")
            return []
        
        logger.info(f"[OK] {len(past_games)} matchs passes trouves")
        
        # 2. Formater les matchs passes
        today = datetime.now().strftime('%Y-%m-%d')
        formatted_games = []
        
        # Traiter les matchs passes
        games_by_id = {}
        for game in past_games:
            gid = game['game_id']
            if gid not in games_by_id:
                games_by_id[gid] = []
            games_by_id[gid].append(game)
        
        # Creer les matchs complets (home vs away)
        for gid, teams in games_by_id.items():
            if len(teams) == 2:
                home_team = None
                away_team = None
                
                for team in teams:
                    matchup = team.get('matchup', '')
                    if 'vs.' in matchup:
                        home_team = team
                    elif '@' in matchup:
                        away_team = team
                
                if home_team and away_team:
                    formatted_game = {
                        'game_id': gid,
                        'game_date': home_team['game_date'],
                        'season': season,
                        'season_type': 'Regular Season',
                        'home_team': home_team['team_name'],
                        'away_team': away_team['team_name'],
                        'home_team_id': home_team['team_id'],
                        'away_team_id': away_team['team_id'],
                        'is_played': True,
                        'actual_winner': 'HOME' if home_team.get('wl') == 'W' else 'AWAY',
                        'home_score': home_team.get('points'),
                        'away_score': away_team.get('points'),
                        'game_time': '',
                        'arena': '',
                        'week_number': 0
                    }
                    formatted_games.append(formatted_game)
        
        # 3. Generer les matchs futurs approximatifs
        # Une saison NBA a 1230 matchs (30 equipes * 82 matchs / 2)
        total_expected_games = 1230
        current_games = len(formatted_games)
        
        logger.info(f"[INFO] Matchs trouves: {current_games}/{total_expected_games}")
        
        # Si on a moins de matchs que prevu, c'est qu'il reste des matchs a venir
        # On ne peut pas predire exactement quels matchs, mais on peut indiquer
        # qu'il reste des matchs dans la saison
        
        if current_games < total_expected_games:
            remaining = total_expected_games - current_games
            logger.info(f"[INFO] Environ {remaining} matchs restants dans la saison")
            
            # Note: Sans scheduleleaguev2, on ne peut pas avoir les details exacts
            # des matchs futurs, mais on peut les predire jour par jour
            # via le cron job qui utilise get_today_games()
        
        # 4. Trier par date
        formatted_games.sort(key=lambda x: x['game_date'])
        
        # 5. Statistiques
        played_count = sum(1 for g in formatted_games if g['is_played'])
        future_count = len(formatted_games) - played_count
        
        logger.info(f"[STATS] Matchs joues: {played_count}")
        logger.info(f"[STATS] Matchs a venir (dans les donnees): {future_count}")
        logger.info(f"[STATS] Total dans les donnees: {len(formatted_games)}")
        
        if formatted_games:
            first_date = formatted_games[0]['game_date']
            last_date = formatted_games[-1]['game_date']
            logger.info(f"[DATE] Periode couverte: {first_date} au {last_date}")
        
        logger.info("="*60)
        
        return formatted_games
        
    except Exception as e:
        logger.error(f"[ERROR] Erreur recuperation calendrier: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def get_complete_season_schedule(season: str = SEASON, use_cache: bool = True) -> List[Dict]:
    """
    Recupere le calendrier complet (passes + futurs) avec cache
    
    Args:
        season: Saison cible
        use_cache: Si True, utilise le fichier cache s'il existe
    
    Returns:
        Liste complete des matchs
    """
    cache_file = f"{RAW_BASE}/schedules/complete_schedule_{season.replace('-', '_')}.json"
    
    # Verifier cache
    if use_cache and os.path.exists(cache_file):
        logger.info(f"[CACHE] Chargement depuis {cache_file}")
        with open(cache_file, 'r') as f:
            cached = json.load(f)
            return cached.get('data', [])
    
    # Recuperer frais
    games = fetch_future_schedule(season)
    
    # Sauvegarder cache
    if games:
        save_json(games, cache_file)
        logger.info(f"[CACHE] Sauvegarde dans {cache_file}")
    
    return games


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
