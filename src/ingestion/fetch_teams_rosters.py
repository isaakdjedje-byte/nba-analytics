#!/usr/bin/env python3
"""
Recuperation des equipes NBA et de leurs rosters
NBA-15: Donnees equipes completes
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

import yaml
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster

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


def fetch_all_teams() -> List[Dict]:
    """
    Recupere toutes les equipes NBA (30 equipes)
    
    Returns:
        Liste des 30 equipes avec leurs informations
    """
    logger.info("[NBA] Recuperation des 30 equipes NBA...")
    
    all_teams = teams.get_teams()
    
    # Formater les donnees
    formatted_teams = []
    for team in all_teams:
        formatted_teams.append({
            'id': team['id'],
            'full_name': team['full_name'],
            'abbreviation': team['abbreviation'],
            'nickname': team['nickname'],
            'city': team['city'],
            'state': team.get('state', ''),
            'year_founded': team.get('year_founded', None)
        })
    
    logger.info(f"[OK] {len(formatted_teams)} equipes recuperees")
    return formatted_teams


def fetch_team_roster(team_id: int, team_name: str) -> List[Dict]:
    """
    Recupere le roster d'une equipe
    
    Args:
        team_id: ID de l'equipe
        team_name: Nom de l'equipe (pour logging)
    
    Returns:
        Liste des joueurs dans l'equipe
    """
    logger.debug(f"[STEP] Roster {team_name} (ID: {team_id})...")
    
    try:
        roster = fetch_with_retry(
            commonteamroster.CommonTeamRoster,
            team_id=team_id,
            season=SEASON
        )
        
        roster_data = roster.get_normalized_dict()
        players = roster_data.get('CommonTeamRoster', [])
        
        # Formater les joueurs
        formatted_players = []
        for player in players:
            formatted_players.append({
                'player_id': player.get('PLAYER_ID'),
                'player_name': player.get('PLAYER'),
                'number': player.get('NUM', ''),
                'position': player.get('POSITION', ''),
                'height': player.get('HEIGHT', ''),
                'weight': player.get('WEIGHT', ''),
                'birth_date': player.get('BIRTH_DATE', ''),
                'age': player.get('AGE'),
                'experience': player.get('EXP', ''),
                'school': player.get('SCHOOL', '')
            })
        
        return formatted_players
        
    except Exception as e:
        logger.error(f"[ERROR] Erreur roster {team_name}: {e}")
        return []


def fetch_all_rosters(teams_data: List[Dict]) -> List[Dict]:
    """
    Recupere les rosters de toutes les equipes
    
    Args:
        teams_data: Liste des equipes
    
    Returns:
        Liste des rosters par equipe
    """
    logger.info(f"[NBA] Recuperation des rosters pour {len(teams_data)} equipes...")
    
    all_rosters = []
    total_players = 0
    
    for i, team in enumerate(teams_data, 1):
        team_id = team['id']
        team_name = team['full_name']
        
        logger.info(f"[{i}/{len(teams_data)}] {team_name}")
        
        players = fetch_team_roster(team_id, team_name)
        
        roster_entry = {
            'team_id': team_id,
            'team_name': team_name,
            'team_abbreviation': team['abbreviation'],
            'season': SEASON,
            'players': players,
            'roster_size': len(players)
        }
        
        all_rosters.append(roster_entry)
        total_players += len(players)
        
        logger.info(f"   [OK] {len(players)} joueurs")
    
    logger.info(f"[OK] Total: {total_players} joueurs dans {len(all_rosters)} equipes")
    return all_rosters


def fetch_teams_and_rosters() -> Dict[str, Any]:
    """
    Orchestration complete: equipes + rosters
    
    Returns:
        Dictionnaire avec teams et rosters
    """
    logger.info("="*60)
    logger.info("[TARGET] NBA-15: Recuperation Equipes et Rosters")
    logger.info("="*60)
    
    # 1. Recuperer les equipes
    teams_data = fetch_all_teams()
    
    if len(teams_data) != 30:
        logger.warning(f"[WARNING] Nombre d'equipes inhabituel: {len(teams_data)} (attendu: 30)")
    
    # Sauvegarder les equipes
    teams_filepath = f"{RAW_BASE}/teams/teams_{SEASON.replace('-', '_')}.json"
    save_json(teams_data, teams_filepath)
    
    # 2. Recuperer les rosters
    rosters_data = fetch_all_rosters(teams_data)
    
    # Sauvegarder les rosters
    rosters_filepath = f"{RAW_BASE}/rosters/roster_{SEASON.replace('-', '_')}.json"
    save_json(rosters_data, rosters_filepath)
    
    # Statistiques
    total_players = sum(r['roster_size'] for r in rosters_data)
    avg_roster = total_players / len(rosters_data) if rosters_data else 0
    
    logger.info("\n" + "="*60)
    logger.info("[OK] RECUPERATION TERMINEE")
    logger.info("="*60)
    logger.info(f"[STATS] Equipes: {len(teams_data)}")
    logger.info(f"[STATS] Rosters: {len(rosters_data)}")
    logger.info(f"[STATS] Joueurs totaux: {total_players}")
    logger.info(f"[STATS] Moyenne joueurs/equipe: {avg_roster:.1f}")
    logger.info("="*60)
    
    return {
        'teams': teams_data,
        'rosters': rosters_data,
        'stats': {
            'teams_count': len(teams_data),
            'rosters_count': len(rosters_data),
            'total_players': total_players,
            'avg_roster_size': avg_roster
        }
    }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    result = fetch_teams_and_rosters()
    print(f"\n[OK] Fichiers crees:")
    print(f"   - data/raw/teams/teams_{SEASON.replace('-', '_')}.json")
    print(f"   - data/raw/rosters/roster_{SEASON.replace('-', '_')}.json")
