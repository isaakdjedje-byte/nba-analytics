"""
Récupération des positions réelles depuis NBA API.

Améliore la qualité des données en récupérant les vraies positions.
"""

import logging
import json
import time
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class RealPositionFetcher:
    """
    Récupère les positions réelles depuis NBA API.
    
    Usage:
        fetcher = RealPositionFetcher()
        real_positions = fetcher.fetch_for_players(player_ids)
        fetcher.save_positions(real_positions)
    """
    
    def __init__(self, cache_file: str = "data/cache/real_positions.json"):
        """
        Initialise le fetcher.
        
        Args:
            cache_file: Fichier cache pour positions
        """
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()
        self.failed_ids = []
        
    def _load_cache(self) -> Dict:
        """Charge le cache existant."""
        if self.cache_file.exists():
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        """Sauvegarde le cache."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def fetch_for_player(self, player_id: int) -> Optional[Dict]:
        """
        Récupère position réelle pour un joueur.
        
        Args:
            player_id: ID joueur NBA
            
        Returns:
            Dict avec position, team_id, etc. ou None
        """
        # Vérifier cache
        if str(player_id) in self.cache:
            return self.cache[str(player_id)]
        
        try:
            from nba_api.stats.endpoints import commonplayerinfo
            from src.utils.circuit_breaker import get_circuit_breaker
            
            # Appel API avec circuit breaker
            cb = get_circuit_breaker()
            info = cb.call(commonplayerinfo.CommonPlayerInfo, 
                          player_id=player_id)
            
            data = info.get_normalized_dict()
            
            if data.get('CommonPlayerInfo'):
                player_info = data['CommonPlayerInfo'][0]
                
                result = {
                    'player_id': player_id,
                    'position': player_info.get('POSITION'),
                    'team_id': player_info.get('TEAM_ID'),
                    'team_name': player_info.get('TEAM_NAME'),
                    'from_year': player_info.get('FROM_YEAR'),
                    'to_year': player_info.get('TO_YEAR'),
                    'source': 'nba_api_real',
                    'fetched_at': datetime.now().isoformat(),
                    'confidence': 1.0  # Données réelles = confiance 100%
                }
                
                # Mettre en cache
                self.cache[str(player_id)] = result
                
                return result
                
        except Exception as e:
            logger.warning(f"Erreur récupération position {player_id}: {e}")
            self.failed_ids.append(player_id)
        
        return None
    
    def fetch_for_players(self, player_ids: List[int], 
                         delay: float = 0.6) -> Dict[int, Dict]:
        """
        Récupère positions pour plusieurs joueurs.
        
        Args:
            player_ids: Liste IDs joueurs
            delay: Délai entre appels API (rate limiting)
            
        Returns:
            Dict {player_id: position_data}
        """
        results = {}
        
        logger.info(f"Récupération positions pour {len(player_ids)} joueurs...")
        
        for i, player_id in enumerate(player_ids):
            if i % 10 == 0:
                logger.info(f"  Progression: {i}/{len(player_ids)}")
            
            result = self.fetch_for_player(player_id)
            if result:
                results[player_id] = result
            
            # Rate limiting
            if delay > 0 and i < len(player_ids) - 1:
                time.sleep(delay)
        
        # Sauvegarder cache
        self._save_cache()
        
        logger.info(f"✅ {len(results)}/{len(player_ids)} positions récupérées")
        
        if self.failed_ids:
            logger.warning(f"⚠️ {len(self.failed_ids)} échecs")
        
        return results
    
    def enrich_players_with_real_positions(self, 
                                          players: List[Dict]) -> List[Dict]:
        """
        Enrichit une liste de joueurs avec positions réelles.
        
        Args:
            players: Liste joueurs à enrichir
            
        Returns:
            Liste joueurs enrichis
        """
        enriched = []
        
        for player in players:
            player_id = player.get('id')
            
            if player_id:
                real_data = self.fetch_for_player(player_id)
                
                if real_data:
                    # Enrichir avec données réelles
                    player['position'] = real_data.get('position') or player.get('position')
                    player['team_id'] = real_data.get('team_id') or player.get('team_id')
                    player['position_source'] = 'nba_api_real'
                    player['position_confidence'] = 1.0
                else:
                    # Garder prédiction existante
                    player['position_source'] = player.get('position_source', 'predicted')
            
            enriched.append(player)
        
        return enriched
    
    def get_failed_ids(self) -> List[int]:
        """Retourne IDs pour lesquels la récupération a échoué."""
        return self.failed_ids


def fetch_and_update_positions(players_file: str, output_file: str):
    """
    Fonction utilitaire pour récupérer et mettre à jour positions.
    
    Args:
        players_file: Fichier JSON avec joueurs
        output_file: Fichier JSON de sortie
    """
    # Charger joueurs
    with open(players_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        players = data.get('data', data.get('players', []))
    
    logger.info(f"Chargement: {len(players)} joueurs")
    
    # Récupérer positions
    fetcher = RealPositionFetcher()
    enriched = fetcher.enrich_players_with_real_positions(players)
    
    # Sauvegarder
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({'data': enriched}, f, indent=2, ensure_ascii=False)
    
    # Stats
    real_count = sum(1 for p in enriched if p.get('position_source') == 'nba_api_real')
    logger.info(f"✅ Sauvegardé: {len(enriched)} joueurs")
    logger.info(f"   Positions réelles: {real_count}")
    logger.info(f"   Positions prédites: {len(enriched) - real_count}")


if __name__ == "__main__":
    print("Test Real Position Fetcher")
    
    # Test avec quelques IDs connus
    test_ids = [2544, 201939, 1628989]  # LeBron, Curry, Luka
    
    fetcher = RealPositionFetcher()
    results = fetcher.fetch_for_players(test_ids, delay=1.0)
    
    for player_id, data in results.items():
        print(f"\nPlayer {player_id}:")
        print(f"  Position: {data.get('position')}")
        print(f"  Team: {data.get('team_name')}")
