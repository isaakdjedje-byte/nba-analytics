"""
NBA-19: Auto-discovery des joueurs historiques

Pour les joueurs qui n'apparaissent pas dans les rosters 2018-2024,
ce script utilise PlayerCareerStats pour retrouver leur historique d'équipes.

Stratégie:
1. Identifier les joueurs sans roster
2. Pour chaque joueur, fetch PlayerCareerStats
3. Extraire les équipes et saisons
4. Créer un mapping player-team historique

Usage:
    python src/ingestion/nba19/auto_discovery.py
"""
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional, Set
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from nba_api.stats.endpoints import PlayerCareerStats
from nba_api.stats.static import players
from src.ingestion.nba19.config import CONFIG


class PlayerTeamDiscovery:
    """Découverte automatique des équipes par joueur"""
    
    def __init__(self):
        self.config = CONFIG
        self.discovered_mappings = []
        self.failed_players = []
        self.stats = {
            "total_players": 0,
            "discovered": 0,
            "failed": 0,
            "skipped": 0
        }
    
    def load_all_players(self) -> List[Dict]:
        """Charger tous les joueurs du dataset enrichi"""
        enriched_file = "data/silver/players_advanced/players_enriched_final.json"
        
        if not os.path.exists(enriched_file):
            print(f"⚠️ Fichier non trouvé: {enriched_file}")
            print("   Utilisation de l'API statique players.get_players()")
            return players.get_players()
        
        with open(enriched_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convertir au format standard
        player_list = []
        for player in data.get('players', []):
            player_list.append({
                'id': player.get('id'),
                'full_name': player.get('full_name', ''),
                'first_name': player.get('first_name', ''),
                'last_name': player.get('last_name', '')
            })
        
        return player_list
    
    def load_existing_rosters(self) -> Set[int]:
        """
        Charger tous les player_id déjà présents dans les rosters historiques
        
        Returns:
            Set des player_id couverts
        """
        covered_players = set()
        
        for season in self.config.SEASONS:
            roster_file = os.path.join(
                self.config.OUTPUT_DIR,
                f"rosters_{season.replace('-', '_')}.json"
            )
            
            if os.path.exists(roster_file):
                with open(roster_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for team in data.get('data', []):
                    for player in team.get('players', []):
                        player_id = player.get('PLAYER_ID')
                        if player_id:
                            covered_players.add(player_id)
        
        return covered_players
    
    def fetch_player_career(self, player_id: int, retry: int = 0) -> Optional[Dict]:
        """
        Récupérer la carrière d'un joueur
        
        Args:
            player_id: ID du joueur
            retry: Nombre de tentatives
            
        Returns:
            Dict avec l'historique des équipes ou None
        """
        try:
            career = PlayerCareerStats(
                player_id=player_id,
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            # Season totals (index 0)
            season_df = career.get_data_frames()[0]
            
            if season_df.empty:
                return None
            
            # Extraire l'historique équipe/saison
            history = []
            for _, row in season_df.iterrows():
                season = row.get('SEASON_ID', '')
                team_id = row.get('TEAM_ID')
                team_name = row.get('TEAM_ABBREVIATION', '')
                
                if season and team_id and season in self.config.SEASONS:
                    history.append({
                        'season': season,
                        'team_id': int(team_id),
                        'team_abbreviation': team_name
                    })
            
            return {
                'player_id': player_id,
                'history': history
            }
            
        except Exception as e:
            if retry < self.config.MAX_RETRIES:
                wait_time = self.config.RETRY_BACKOFF_BASE ** retry
                time.sleep(wait_time)
                return self.fetch_player_career(player_id, retry + 1)
            else:
                return None
    
    def discover_missing_players(self, batch_size: Optional[int] = None):
        """
        Découvrir les équipes des joueurs manquants
        
        Args:
            batch_size: Nombre max de joueurs à traiter (None = tous)
        """
        print("\n" + "=" * 70)
        print("🔍 AUTO-DISCOVERY: Joueurs historiques")
        print("=" * 70)
        
        # Charger tous les joueurs
        all_players = self.load_all_players()
        self.stats['total_players'] = len(all_players)
        print(f"📊 Total joueurs: {len(all_players)}")
        
        # Charger les joueurs déjà couverts
        covered = self.load_existing_rosters()
        print(f"✅ Déjà couverts par rosters: {len(covered)}")
        
        # Identifier les joueurs manquants
        missing_players = [
            p for p in all_players 
            if p.get('id') and p['id'] not in covered
        ]
        
        print(f"❓ Joueurs à découvrir: {len(missing_players)}")
        
        if batch_size:
            missing_players = missing_players[:batch_size]
            print(f"   (Limité à {batch_size} pour ce run)")
        
        print("=" * 70)
        
        # Traiter chaque joueur manquant
        for idx, player in enumerate(missing_players, 1):
            player_id = player['id']
            player_name = player.get('full_name', f"Player_{player_id}")
            
            print(f"[{idx}/{len(missing_players)}] {player_name}...", end=" ", flush=True)
            
            # Fetch carrière
            career = self.fetch_player_career(player_id)
            
            if career and career['history']:
                # Ajouter les mappings découverts
                for entry in career['history']:
                    self.discovered_mappings.append({
                        'player_id': player_id,
                        'player_name': player_name,
                        'season': entry['season'],
                        'team_id': entry['team_id'],
                        'team_abbreviation': entry['team_abbreviation'],
                        'discovery_method': 'career_stats_api',
                        'confidence': 1.0,
                        'discovered_at': datetime.now().isoformat()
                    })
                
                self.stats['discovered'] += 1
                print(f"✅ ({len(career['history'])} saisons)")
            else:
                self.stats['failed'] += 1
                self.failed_players.append({
                    'player_id': player_id,
                    'player_name': player_name
                })
                print("❌")
            
            # Rate limiting
            time.sleep(self.config.REQUEST_DELAY_SECONDS)
        
        # Afficher le résumé
        self._print_summary()
    
    def _print_summary(self):
        """Afficher le résumé du discovery"""
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ AUTO-DISCOVERY")
        print("=" * 70)
        print(f"👥 Total joueurs: {self.stats['total_players']}")
        print(f"✅ Découverts: {self.stats['discovered']}")
        print(f"❌ Échecs: {self.stats['failed']}")
        coverage = (self.stats['discovered'] / self.stats['total_players']) * 100
        print(f"📈 Couverture: {coverage:.1f}%")
        print("=" * 70)
    
    def save_discovered_mappings(self):
        """Sauvegarder les mappings découverts"""
        output_file = os.path.join(
            self.config.OUTPUT_DIR,
            "player_team_discovered.json"
        )
        
        data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "discovery_method": "PlayerCareerStats API",
                "total_mappings": len(self.discovered_mappings),
                "stats": self.stats
            },
            "data": self.discovered_mappings,
            "failed_players": self.failed_players
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Mappings sauvegardés: {output_file}")


def main():
    """Point d'entrée principal"""
    discovery = PlayerTeamDiscovery()
    
    # Lancer le discovery (limité à 100 joueurs pour test)
    discovery.discover_missing_players(batch_size=100)
    
    # Sauvegarder
    discovery.save_discovered_mappings()
    
    print("\n✨ Auto-discovery terminé!")


if __name__ == "__main__":
    main()
