#!/usr/bin/env python3
"""
Récupération des données NBA multi-saisons (2018-19 à 2024-25)
Sépare Regular Season et Playoffs
"""
import os
import json
import logging
import time
from datetime import datetime
from typing import List, Optional
import yaml
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import (
    playergamelog, teamgamelog, leaguegamefinder
)
from nba_api.live.nba.endpoints import scoreboard
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Charger config
with open('src/config/seasons_config.yaml', 'r') as f:
    CONFIG = yaml.safe_load(f)
RAW_BASE = CONFIG['paths']['raw_base']
SAISONS = CONFIG['saisons']
DELAY = CONFIG['parametres_fetch']['delay_seconds']
RETRY = CONFIG['parametres_fetch']['retry_attempts']
def ensure_dir(path):
    """Crée le répertoire s'il n'existe pas"""
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"📁 Créé: {path}")
def save_json(data, filepath):
    """Sauvegarde avec métadonnées"""
    output = {
        'data': data,
        'metadata': {
            'export_date': datetime.now().isoformat(),
            'record_count': len(data) if isinstance(data, list) else 1,
            'source': 'nba-api'
        }
    }
    ensure_dir(os.path.dirname(filepath))
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    logger.info(f"💾 Sauvegardé: {filepath} ({len(data)} records)")
def fetch_with_retry(func, *args, **kwargs):
    """Exécute avec retry en cas d'erreur"""
    for attempt in range(RETRY):
        try:
            time.sleep(DELAY)  # Rate limit
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"⚠️  Tentative {attempt+1}/{RETRY} échouée: {e}")
            time.sleep(DELAY * (attempt + 1))  # Backoff exponentiel
    raise Exception(f"Échec après {RETRY} tentatives")
def fetch_all_players():
    """Récupère tous les joueurs (historique)"""
    logger.info("🏀 Récupération joueurs...")
    all_players = players.get_players()
    save_json(all_players, f"{RAW_BASE}/all_players_historical.json")
    return all_players
def fetch_active_players():
    """Récupère joueurs actifs"""
    logger.info("🏀 Récupération joueurs actifs...")
    active = players.get_active_players()
    save_json(active, f"{RAW_BASE}/active_players.json")
    return active
def fetch_teams():
    """Récupère équipes"""
    logger.info("🏀 Récupération équipes...")
    all_teams = teams.get_teams()
    save_json(all_teams, f"{RAW_BASE}/teams.json")
    return all_teams
def fetch_games_for_season(season: str, season_type: str = "Regular Season"):
    """
    Récupère tous les matchs d'une saison
    
    Args:
        season: Format "2023-24"
        season_type: "Regular Season" ou "Playoffs"
    """
    logger.info(f"🎮 Récupération {season} - {season_type}...")
    
    try:
        games = fetch_with_retry(
            leaguegamefinder.LeagueGameFinder,
            season_nullable=season,
            season_type_nullable=season_type,
            league_id_nullable="00"  # NBA
        )
        
        games_dict = games.get_normalized_dict()
        games_list = games_dict.get('LeagueGameFinderResults', [])
        
        # Sauvegarde par saison/type
        season_dir = f"{RAW_BASE}/{season.replace('-', '_')}"
        filename = f"games_{season_type.lower().replace(' ', '_')}.json"
        filepath = f"{season_dir}/{filename}"
        
        save_json(games_list, filepath)
        
        return games_list
        
    except Exception as e:
        logger.error(f"❌ Erreur {season} {season_type}: {e}")
        return []
def fetch_player_career_stats(player_id: int, player_name: str = ""):
    """Récupère stats carrière d'un joueur"""
    logger.info(f"📊 Stats carrière: {player_name or player_id}")
    
    try:
        career = fetch_with_retry(
            playercareerstats.PlayerCareerStats,
            player_id=player_id
        )
        return career.get_normalized_dict()
    except Exception as e:
        logger.error(f"❌ Erreur stats carrière: {e}")
        return None
def fetch_live_games():
    """Récupère matchs en cours"""
    logger.info("🔴 Récupération matchs live...")
    try:
        live = scoreboard.ScoreBoard()
        live_data = live.get_dict()
        save_json(live_data, f"{RAW_BASE}/live_scoreboard.json")
        return live_data
    except Exception as e:
        logger.error(f"❌ Erreur live: {e}")
        return None
def main():
    """Orchestration complète"""
    logger.info("="*70)
    logger.info("🚀 DÉMARRAGE FETCH MULTI-SAISONS")
    logger.info("="*70)
    
    start_time = datetime.now()
    
    try:
        # 1. Données statiques (une fois)
        fetch_all_players()
        fetch_active_players()
        fetch_teams()
        
        # 2. Pour chaque saison
        total_games = 0
        for season in SAISONS:
            logger.info(f"\n📅 Saison: {season}")
            
            # Regular Season
            games_rs = fetch_games_for_season(season, "Regular Season")
            total_games += len(games_rs)
            
            # Playoffs (sauf si saison en cours sans playoffs)
            try:
                games_po = fetch_games_for_season(season, "Playoffs")
                total_games += len(games_po)
            except Exception as e:
                logger.warning(f"⚠️  Pas de playoffs pour {season} (normal si saison en cours)")
        
        # 3. Live (bonus)
        fetch_live_games()
        
        # Résumé
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("\n" + "="*70)
        logger.info("✅ FETCH TERMINÉ")
        logger.info("="*70)
        logger.info(f"⏱️  Durée: {duration:.1f}s")
        logger.info(f"📊 Total matchs: {total_games}")
        logger.info(f"📁 Données dans: {RAW_BASE}/")
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        raise
if __name__ == "__main__":
    main()

