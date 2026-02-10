#!/usr/bin/env python3
"""
Récupération des résultats NBA via API Officielle uniquement
Pas d'inscription requise - Système de backup intégré
"""

import sys
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NBAAPIManager:
    """
    Gestionnaire d'API NBA sans inscription
    Essaie plusieurs méthodes avec fallback automatique
    """
    
    def __init__(self):
        self.season = "2025-26"
        self.methods_tested = []
        
    def fetch_2025_26_results(self) -> Dict:
        """
        Récupère les résultats des matchs 2025-26
        Essaie chaque méthode jusqu'à succès
        
        Returns:
            {
                'results': List[Dict],      # Matchs avec résultats
                'method': str,              # Méthode utilisée
                'count': int,               # Nombre de matchs
                'is_complete': bool,        # Données complètes ?
                'message': str              # Message explicatif
            }
        """
        logger.info("="*70)
        logger.info("RÉCUPÉRATION API NBA - 2025-26")
        logger.info("="*70)
        
        # Méthode 1 : LeagueGameFinder par dates
        logger.info("\n[1/4] Tentative LeagueGameFinder (dates)...")
        try:
            results = self._method_gamefinder_dates()
            if results and len(results) > 10:
                return {
                    'results': results,
                    'method': 'LeagueGameFinder',
                    'count': len(results),
                    'is_complete': True,
                    'message': f'{len(results)} matchs récupérés via LeagueGameFinder'
                }
        except Exception as e:
            logger.warning(f"   Échec: {e}")
        
        # Méthode 2 : Scoreboard (matchs récents)
        logger.info("\n[2/4] Tentative Scoreboard (matchs récents)...")
        try:
            results = self._method_scoreboard()
            if results and len(results) > 0:
                return {
                    'results': results,
                    'method': 'Scoreboard',
                    'count': len(results),
                    'is_complete': False,
                    'message': f'{len(results)} matchs récents via Scoreboard (partiel)'
                }
        except Exception as e:
            logger.warning(f"   Échec: {e}")
        
        # Méthode 3 : BoxScore individuel (lent)
        logger.info("\n[3/4] Tentative BoxScore individuel...")
        try:
            results = self._method_boxscore_individual()
            if results and len(results) > 10:
                return {
                    'results': results,
                    'method': 'BoxScore',
                    'count': len(results),
                    'is_complete': True,
                    'message': f'{len(results)} matchs récupérés via BoxScore (méthode lente)'
                }
        except Exception as e:
            logger.warning(f"   Échec: {e}")
        
        # Méthode 4 : Calendrier local (fallback)
        logger.info("\n[4/4] Fallback sur calendrier local...")
        return self._fallback_local()
    
    def _method_gamefinder_dates(self) -> List[Dict]:
        """Méthode 1 : LeagueGameFinder par plage de dates"""
        from nba_api.stats.endpoints import leaguegamefinder
        
        logger.info("   Appel LeagueGameFinder...")
        games = leaguegamefinder.LeagueGameFinder(
            date_from_nullable="2025-10-21",
            date_to_nullable="2026-02-08",
            season_nullable=self.season,
            league_id_nullable="00",
            season_type_nullable="Regular Season"
        )
        
        data = games.get_normalized_dict()
        games_list = data.get('LeagueGameFinderResults', [])
        
        logger.info(f"   {len(games_list)} entrées brutes reçues")
        
        # Grouper par game_id
        games_by_id = defaultdict(list)
        for game in games_list:
            gid = game.get('GAME_ID')
            if gid:
                games_by_id[gid].append(game)
        
        # Créer matchs complets
        complete_games = []
        for gid, teams in games_by_id.items():
            if len(teams) == 2:
                home_team = None
                away_team = None
                
                for team in teams:
                    matchup = team.get('MATCHUP', '')
                    if 'vs.' in matchup:
                        home_team = team
                    elif '@' in matchup:
                        away_team = team
                
                if home_team and away_team:
                    # Vérifier qu'on a des résultats
                    if home_team.get('WL') is not None:
                        complete_games.append({
                            'game_id': gid,
                            'game_date': home_team.get('GAME_DATE'),
                            'season': self.season,
                            'home_team': home_team.get('TEAM_NAME'),
                            'away_team': away_team.get('TEAM_NAME'),
                            'home_team_id': home_team.get('TEAM_ID'),
                            'away_team_id': away_team.get('TEAM_ID'),
                            'home_score': home_team.get('PTS'),
                            'away_score': away_team.get('PTS'),
                            'actual_winner': 'HOME' if home_team.get('WL') == 'W' else 'AWAY',
                            'is_played': True
                        })
        
        logger.info(f"   {len(complete_games)} matchs complets avec résultats")
        return complete_games
    
    def _method_scoreboard(self) -> List[Dict]:
        """Méthode 2 : Scoreboard pour matchs récents"""
        from nba_api.live.nba.endpoints import scoreboard
        
        logger.info("   Appel Scoreboard...")
        board = scoreboard.ScoreBoard()
        games_data = board.games.get_dict()
        
        logger.info(f"   {len(games_data)} matchs trouvés dans Scoreboard")
        
        results = []
        for game in games_data:
            game_status = game.get('gameStatus', 0)
            # Status 3 = match terminé
            if game_status == 3:
                home = game.get('homeTeam', {})
                away = game.get('awayTeam', {})
                
                results.append({
                    'game_id': game.get('gameId'),
                    'game_date': game.get('gameEt')[:10],  # Format YYYY-MM-DD
                    'season': self.season,
                    'home_team': home.get('teamName'),
                    'away_team': away.get('teamName'),
                    'home_team_id': home.get('teamId'),
                    'away_team_id': away.get('teamId'),
                    'home_score': home.get('score'),
                    'away_score': away.get('score'),
                    'actual_winner': 'HOME' if home.get('score', 0) > away.get('score', 0) else 'AWAY',
                    'is_played': True
                })
        
        logger.info(f"   {len(results)} matchs terminés")
        return results
    
    def _method_boxscore_individual(self) -> List[Dict]:
        """Méthode 3 : BoxScore par game_id individuel (lent)"""
        from nba_api.stats.endpoints import boxscoretraditionalv2
        
        # Charger les game_ids depuis le calendrier local
        logger.info("   Chargement des game_ids locaux...")
        game_ids = self._load_local_game_ids()
        logger.info(f"   {len(game_ids)} IDs à traiter")
        
        results = []
        for i, game_id in enumerate(game_ids):
            try:
                logger.info(f"   Traitement {i+1}/{len(game_ids)}: {game_id}")
                boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
                
                # Parser le boxscore
                game_data = self._parse_boxscore(boxscore, game_id)
                if game_data:
                    results.append(game_data)
                
                # Rate limiting
                time.sleep(1.5)
                
            except Exception as e:
                logger.warning(f"   Erreur game_id {game_id}: {e}")
                continue
        
        logger.info(f"   {len(results)} matchs récupérés via BoxScore")
        return results
    
    def _load_local_game_ids(self) -> List[str]:
        """Charge les game_ids depuis le calendrier local"""
        try:
            schedule_file = Path('data/raw/schedules/schedule_2025_26.json')
            with open(schedule_file, 'r') as f:
                data = json.load(f)
                games = data.get('data', [])
            
            # Extraire IDs uniques
            game_ids = list(set(g['game_id'] for g in games if 'game_id' in g))
            return game_ids
        except Exception as e:
            logger.error(f"Erreur chargement calendrier local: {e}")
            return []
    
    def _parse_boxscore(self, boxscore, game_id) -> Optional[Dict]:
        """Parse un boxscore pour extraire les résultats"""
        try:
            # Récupérer les données du match
            game_data = boxscore.game.get_dict()
            
            # Vérifier si match terminé
            if game_data.get('gameStatus') != 3:
                return None
            
            home = game_data.get('homeTeam', {})
            away = game_data.get('awayTeam', {})
            
            return {
                'game_id': game_id,
                'game_date': game_data.get('gameEt', '')[:10],
                'season': self.season,
                'home_team': home.get('teamName'),
                'away_team': away.get('teamName'),
                'home_team_id': home.get('teamId'),
                'away_team_id': away.get('teamId'),
                'home_score': home.get('score'),
                'away_score': away.get('score'),
                'actual_winner': 'HOME' if home.get('score', 0) > away.get('score', 0) else 'AWAY',
                'is_played': True
            }
        except Exception as e:
            logger.warning(f"Erreur parsing boxscore {game_id}: {e}")
            return None
    
    def _fallback_local(self) -> Dict:
        """Backup final : Retourne calendrier sans résultats"""
        logger.warning("="*70)
        logger.warning("FALLBACK : Aucune API disponible")
        logger.warning("="*70)
        
        try:
            # Charger calendrier local
            schedule_file = Path('data/raw/schedules/schedule_2025_26.json')
            with open(schedule_file, 'r') as f:
                data = json.load(f)
                games = data.get('data', [])
            
            # Grouper par game_id
            games_by_id = defaultdict(list)
            for game in games:
                gid = game.get('game_id')
                if gid:
                    games_by_id[gid].append(game)
            
            # Créer entrées sans résultats
            future_games = []
            for gid, teams in games_by_id.items():
                if len(teams) == 2:
                    home = [t for t in teams if 'vs.' in t.get('matchup', '')]
                    away = [t for t in teams if '@' in t.get('matchup', '')]
                    
                    if home and away:
                        future_games.append({
                            'game_id': gid,
                            'game_date': home[0].get('game_date'),
                            'season': self.season,
                            'home_team': home[0].get('team_name'),
                            'away_team': away[0].get('team_name'),
                            'home_team_id': home[0].get('team_id'),
                            'away_team_id': away[0].get('team_id'),
                            'actual_winner': None,
                            'is_played': False
                        })
            
            return {
                'results': future_games,
                'method': 'Local_Calendar_Only',
                'count': 0,
                'is_complete': False,
                'message': 'APIs NBA indisponibles. Seules les prédictions futures sont possibles.'
            }
            
        except Exception as e:
            logger.error(f"Erreur fallback: {e}")
            return {
                'results': [],
                'method': 'Failed_All_Methods',
                'count': 0,
                'is_complete': False,
                'message': f'Erreur critique: {e}'
            }


def test_api():
    """Test rapide des APIs"""
    print("\n" + "="*70)
    print("TEST DES APIS NBA - 2025-26")
    print("="*70 + "\n")
    
    api = NBAAPIManager()
    result = api.fetch_2025_26_results()
    
    print("\n" + "="*70)
    print("RÉSULTATS")
    print("="*70)
    print(f"Méthode utilisée : {result['method']}")
    print(f"Matchs trouvés   : {result['count']}")
    print(f"Données complètes: {result['is_complete']}")
    print(f"Message          : {result['message']}")
    
    if result['results']:
        print(f"\nExemple de match:")
        print(json.dumps(result['results'][0], indent=2, ensure_ascii=False))
    
    print("="*70)


if __name__ == "__main__":
    test_api()
