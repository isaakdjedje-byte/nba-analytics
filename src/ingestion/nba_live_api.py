#!/usr/bin/env python3
"""
NBA Live API - Recuperation des matchs du jour
"""

from datetime import datetime, timedelta
from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_today_games():
    """
    Recupere les matchs du jour via NBA API Live.
    Retourne une liste de matchs avec home_team et away_team.
    """
    try:
        from nba_api.live.nba.endpoints import scoreboard
        
        logger.info("Recuperation des matchs du jour...")
        
        # Scoreboard du jour
        board = scoreboard.ScoreBoard()
        games = board.get_data_frames()[0]
        
        if len(games) == 0:
            logger.info("Aucun match aujourd'hui")
            return []
        
        # Filtrer les matchs non commences
        upcoming_games = []
        for _, game in games.iterrows():
            # Statut: 1 = Scheduled, 2 = Pre-game, 3 = In progress, etc.
            status = game.get('GAME_STATUS_ID', 1)
            
            if status in [1, 2]:  # Matchs a venir
                upcoming_games.append({
                    'game_id': game['GAME_ID'],
                    'home_team': game['HOME_TEAM_NAME'],
                    'away_team': game['AWAY_TEAM_NAME'],
                    'game_time': game.get('GAME_STATUS_TEXT', 'TBD'),
                    'home_team_id': game['HOME_TEAM_ID'],
                    'away_team_id': game['AWAY_TEAM_ID']
                })
        
        logger.info(f"[OK] {len(upcoming_games)} matchs trouves")
        return upcoming_games
        
    except Exception as e:
        logger.error(f"Erreur API: {e}")
        return []


def get_schedule_next_days(days: int = 3):
    """
    Recupere le calendrier pour les prochains jours.
    
    Args:
        days: Nombre de jours a recuperer (defaut: 3)
    """
    try:
        from nba_api.stats.endpoints import scheduleleaguev2
        
        logger.info(f"Recuperation calendrier ({days} jours)...")
        
        # Recuperer tout le calendrier de la saison
        schedule = scheduleleaguev2.ScheduleLeagueV2()
        df = schedule.get_data_frames()[0]
        
        # Filtrer pour les prochains jours
        today = datetime.now().date()
        end_date = today + timedelta(days=days)
        
        upcoming = []
        for _, game in df.iterrows():
            game_date = pd.to_datetime(game['GAME_DATE']).date()
            
            if today <= game_date <= end_date:
                upcoming.append({
                    'date': game_date.strftime('%Y-%m-%d'),
                    'home_team': game['HOME_TEAM_NAME'],
                    'away_team': game['VISITOR_TEAM_NAME'],
                    'game_time': game.get('GAME_TIME', 'TBD')
                })
        
        logger.info(f"[OK] {len(upcoming)} matchs dans les {days} prochains jours")
        return upcoming
        
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return []


def test_api_connection():
    """Test la connexion a l'API NBA."""
    logger.info("=== TEST CONNEXION API NBA ===\n")
    
    try:
        games = get_today_games()
        
        if games:
            print("\nMatchs trouves:")
            for game in games:
                print(f"  {game['home_team']} vs {game['away_team']} ({game['game_time']})")
            return True
        else:
            print("\nAucun match aujourd'hui ou erreur de connexion")
            return False
            
    except Exception as e:
        logger.error(f"Erreur de connexion: {e}")
        return False


if __name__ == '__main__':
    import pandas as pd
    
    # Test
    success = test_api_connection()
    
    if not success:
        print("\nMode demonstration active (exemples de matchs)")
        demo_games = [
            {'home_team': 'Boston Celtics', 'away_team': 'Los Angeles Lakers', 'game_time': '19:00'},
            {'home_team': 'Golden State Warriors', 'away_team': 'Phoenix Suns', 'game_time': '20:30'},
            {'home_team': 'Milwaukee Bucks', 'away_team': 'Miami Heat', 'game_time': '22:00'}
        ]
        for g in demo_games:
            print(f"  {g['home_team']} vs {g['away_team']} ({g['game_time']})")
