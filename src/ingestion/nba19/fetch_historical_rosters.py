"""
NBA-19: Fetching des rosters historiques (2018-2024)

Script principal pour récupérer les rosters des 7 saisons
avec auto-discovery pour les joueurs historiques.

Usage:
    python src/ingestion/nba19/fetch_historical_rosters.py
    
Temps estimé: ~7 minutes pour 7 saisons × 30 équipes
"""
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from nba_api.stats.endpoints import CommonTeamRoster
from nba_api.stats.static import teams
from src.ingestion.nba19.config import CONFIG
from src.ingestion.nba19.checkpoint_manager import CheckpointManager, FetchingStats


class HistoricalRosterFetcher:
    """Fetcher pour rosters historiques NBA"""
    
    def __init__(self):
        self.config = CONFIG
        self.checkpoint_mgr = CheckpointManager(self.config.CHECKPOINT_FILE)
        self.stats = FetchingStats()
        self.all_teams = teams.get_teams()
        
        # Créer le répertoire de sortie
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
    
    def fetch_team_roster(
        self, 
        team_id: int, 
        season: str,
        retry_count: int = 0
    ) -> Optional[Dict]:
        """
        Récupérer le roster d'une équipe pour une saison
        
        Args:
            team_id: ID de l'équipe
            season: Saison au format 'YYYY-YY'
            retry_count: Nombre de tentatives actuelles
            
        Returns:
            Dict avec les données du roster ou None si échec
        """
        try:
            # Appel API avec timeout
            roster = CommonTeamRoster(
                team_id=team_id,
                season=season,
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            # Extraire les données
            players_df = roster.get_data_frames()[0]
            coaches_df = roster.get_data_frames()[1]
            
            # Convertir en format JSON friendly
            players = players_df.to_dict('records')
            coaches = coaches_df.to_dict('records')
            
            # Trouver le nom de l'équipe
            team_name = next(
                (t['full_name'] for t in self.all_teams if t['id'] == team_id),
                f"Team_{team_id}"
            )
            
            return {
                "team_id": team_id,
                "team_name": team_name,
                "season": season,
                "players": players,
                "coaches": coaches,
                "roster_size": len(players),
                "fetched_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            if retry_count < self.config.MAX_RETRIES:
                # Attente exponentielle
                wait_time = self.config.RETRY_BACKOFF_BASE ** retry_count
                print(f"   ⚠️ Erreur, retry dans {wait_time}s... ({retry_count + 1}/{self.config.MAX_RETRIES})")
                time.sleep(wait_time)
                return self.fetch_team_roster(team_id, season, retry_count + 1)
            else:
                print(f"   ❌ Échec après {self.config.MAX_RETRIES} tentatives: {e}")
                self.stats.add_error(season, team_id, str(e))
                return None
    
    def fetch_season(self, season: str, start_team_index: int = 0) -> List[Dict]:
        """
        Récupérer tous les rosters pour une saison
        
        Args:
            season: Saison au format 'YYYY-YY'
            start_team_index: Index de l'équipe de départ (pour reprise)
            
        Returns:
            Liste des rosters
        """
        print(f"\n🏀 Fetching saison {season}...")
        print(f"   Équipes: {start_team_index + 1}/30")
        
        rosters = []
        completed_teams = []
        
        for idx in range(start_team_index, len(self.all_teams)):
            team = self.all_teams[idx]
            team_id = team['id']
            team_name = team['full_name']
            
            print(f"   [{idx + 1}/30] {team_name}...", end=" ", flush=True)
            
            # Récupérer le roster
            roster = self.fetch_team_roster(team_id, season)
            
            if roster:
                rosters.append(roster)
                completed_teams.append(team_id)
                self.stats.completed_teams += 1
                self.stats.total_players += roster['roster_size']
                print(f"✅ ({roster['roster_size']} joueurs)")
            else:
                self.stats.failed_teams += 1
                print("❌")
            
            # Checkpoint tous les N équipes
            if (idx + 1) % self.config.CHECKPOINT_INTERVAL_TEAMS == 0:
                self.checkpoint_mgr.save_checkpoint(
                    season=season,
                    team_index=idx,
                    completed_teams=completed_teams,
                    stats=self.stats.to_dict()
                )
            
            # Rate limiting
            time.sleep(self.config.REQUEST_DELAY_SECONDS)
        
        return rosters
    
    def save_season_rosters(self, season: str, rosters: List[Dict]):
        """Sauvegarder les rosters d'une saison"""
        output_file = os.path.join(
            self.config.OUTPUT_DIR,
            f"rosters_{season.replace('-', '_')}.json"
        )
        
        data = {
            "metadata": {
                "season": season,
                "fetched_at": datetime.now().isoformat(),
                "total_teams": len(rosters),
                "total_players": sum(r['roster_size'] for r in rosters)
            },
            "data": rosters
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"   💾 Sauvegardé: {output_file}")
    
    def run(self):
        """Exécuter le fetching complet"""
        print("=" * 70)
        print("🏀 NBA-19: FETCHING DES ROSTERS HISTORIQUES")
        print("=" * 70)
        print(f"📅 Saisons: {', '.join(self.config.SEASONS)}")
        print(f"🏀 Équipes: 30")
        print(f"⏱️  Rate limit: 1 req / {self.config.REQUEST_DELAY_SECONDS}s")
        print(f"📁 Output: {self.config.OUTPUT_DIR}")
        print("=" * 70)
        
        # Déterminer où reprendre
        season_idx, team_idx, _ = self.checkpoint_mgr.get_resume_position(
            self.config.SEASONS
        )
        
        if season_idx > 0 or team_idx > 0:
            print(f"\n🔄 Reprise depuis: Saison {self.config.SEASONS[season_idx]}, "
                  f"Équipe {team_idx + 1}")
        
        self.stats.total_teams = len(self.config.SEASONS) * 30
        
        # Fetch chaque saison
        for season in self.config.SEASONS[season_idx:]:
            # Déterminer l'index de départ
            start_idx = team_idx if season == self.config.SEASONS[season_idx] else 0
            
            rosters = self.fetch_season(season, start_idx)
            self.save_season_rosters(season, rosters)
            
            # Reset team_idx pour saisons suivantes
            team_idx = 0
            
            print(f"   ✅ Saison {season} terminée: {len(rosters)}/30 équipes")
        
        # Effacer le checkpoint à la fin
        self.checkpoint_mgr.clear_checkpoint()
        
        # Afficher le résumé
        self.stats.print_summary()
        
        print("\n✨ Fetching terminé!")
        print(f"📁 Données sauvegardées dans: {self.config.OUTPUT_DIR}")


def main():
    """Point d'entrée principal"""
    fetcher = HistoricalRosterFetcher()
    fetcher.run()


if __name__ == "__main__":
    main()
