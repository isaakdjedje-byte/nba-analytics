"""
NBA-19 Phase 2: Discovery Engine (Version Test - 100 joueurs)

Moteur de discovery pour trouver les equipes des joueurs via PlayerCareerStats API.
Version limitee a 100 joueurs pour test rapide.

Usage:
    python phase2_discovery_engine.py --segment A --limit 100
"""
import json
import time
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Optional

# Imports relatifs
from circuit_breaker import CircuitBreaker, CircuitBreakerOpen
from rate_limiter import RateLimiter, RateLimitConfig

# Import NBA API
try:
    from nba_api.stats.endpoints import PlayerCareerStats
except ImportError:
    # Si lance depuis le repo principal
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from nba_api.stats.endpoints import PlayerCareerStats


class DiscoveryEngine:
    """Moteur de discovery pour trouver les equipes des joueurs"""
    
    def __init__(self):
        config = RateLimitConfig(delay_seconds=2.0)
        self.rate_limiter = RateLimiter(config)
        self.circuit_breaker = CircuitBreaker(failure_threshold=0.10)
        
        self.successful_mappings = []
        self.failed_players = []
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'teams_found': 0
        }
    
    def discover_player_teams(
        self, 
        player_id: int, 
        player_name: str,
        retry: int = 0
    ) -> Optional[List[Dict]]:
        """
        Decouvrir les equipes d'un joueur via PlayerCareerStats
        
        Returns:
            Liste des mappings saison-equipe ou None si echec
        """
        try:
            # Appel API
            career = PlayerCareerStats(player_id=player_id, timeout=30)
            season_df = career.get_data_frames()[0]  # SeasonTotalsRegularSeason
            
            if season_df.empty:
                return None
            
            mappings = []
            for _, row in season_df.iterrows():
                season = row.get('SEASON_ID', '')
                team_id = row.get('TEAM_ID')
                team_abbr = row.get('TEAM_ABBREVIATION', '')
                games = row.get('GP', 0)
                
                # Filtrer les entrees TOT (team_id = 0)
                if team_id == 0 or team_abbr == 'TOT':
                    continue
                
                # Filtrer pour les saisons qui nous interessent
                if season and team_id:
                    mappings.append({
                        'player_id': player_id,
                        'player_name': player_name,
                        'season': season,
                        'team_id': int(team_id),
                        'team_abbreviation': team_abbr,
                        'games_played': int(games) if games else 0,
                        'discovery_method': 'career_stats_api',
                        'confidence': 1.0,
                        'discovered_at': datetime.now().isoformat()
                    })
            
            return mappings if mappings else None
            
        except Exception as e:
            if retry < 2:  # 3 tentatives max
                wait_time = 2 ** retry
                print(f"      [WARN] Retry {retry + 1}/3 dans {wait_time}s...")
                time.sleep(wait_time)
                return self.discover_player_teams(player_id, player_name, retry + 1)
            else:
                print(f"      [FAIL] Echec apres 3 tentatives: {e}")
                return None
    
    def process_players(self, players: List[Dict], segment_name: str):
        """Traiter une liste de joueurs"""
        total = len(players)
        self.stats['total'] = total
        
        print(f"\n[START] Demarrage du discovery: {total} joueurs (Segment {segment_name})")
        print(f"   Rate limit: 1 req / 2 sec")
        print(f"   Estimation: ~{total * 2 // 60} minutes\n")
        
        for idx, player in enumerate(players, 1):
            player_id = player.get('id')
            player_name = player.get('full_name', f'Player_{player_id}')
            
            # Progress
            if idx % 10 == 0:
                progress = (idx / total) * 100
                print(f"\n[STATS] Progression: {idx}/{total} ({progress:.0f}%)")
            
            print(f"[{idx:3d}/{total}] {player_name[:30]:30}...", end=" ", flush=True)
            
            # Circuit breaker check
            if not self.circuit_breaker.can_execute():
                print("[STOP] CIRCUIT OUVERT - Arret")
                break
            
            # Rate limiting
            self.rate_limiter.wait_if_needed()
            
            try:
                # Discovery
                mappings = self.discover_player_teams(player_id, player_name)
                self.rate_limiter.record_request()
                
                if mappings:
                    self.successful_mappings.extend(mappings)
                    self.stats['success'] += 1
                    self.stats['teams_found'] += len(mappings)
                    self.circuit_breaker.record_success()
                    print(f"[OK] {len(mappings)} equipes")
                else:
                    self.failed_players.append({
                        'player_id': player_id,
                        'player_name': player_name,
                        'reason': 'no_data'
                    })
                    self.stats['failed'] += 1
                    self.circuit_breaker.record_failure()
                    print("[FAIL] Pas de donnees")
                    
            except Exception as e:
                self.rate_limiter.record_request()
                self.failed_players.append({
                    'player_id': player_id,
                    'player_name': player_name,
                    'reason': str(e)
                })
                self.stats['failed'] += 1
                self.circuit_breaker.record_failure()
                print(f"[FAIL] Erreur: {e}")
            
            # Checkpoint tous les 20 joueurs
            if idx % 20 == 0:
                self._save_checkpoint(idx, segment_name)
        
        # Resume final
        self._print_summary()
    
    def _save_checkpoint(self, index: int, segment: str):
        """Sauvegarder un checkpoint"""
        checkpoint_file = f"logs/nba19_discovery/checkpoint_phase2_{segment}_{index}.json"
        os.makedirs(os.path.dirname(checkpoint_file), exist_ok=True)
        
        data = {
            'index': index,
            'segment': segment,
            'successful_mappings': len(self.successful_mappings),
            'failed': len(self.failed_players),
            'stats': self.stats,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(checkpoint_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"   [SAVE] Checkpoint sauvegarde")
    
    def _print_summary(self):
        """Afficher le resume"""
        print("\n" + "=" * 60)
        print("[STATS] RESUME DU DISCOVERY")
        print("=" * 60)
        print(f"[USERS] Total joueurs: {self.stats['total']}")
        print(f"[OK] Succes: {self.stats['success']} ({self.stats['success']/self.stats['total']*100:.1f}%)")
        print(f"[FAIL] Echecs: {self.stats['failed']}")
        print(f"[NBA] Equipes trouvees: {self.stats['teams_found']}")
        
        if self.successful_mappings:
            avg_teams = self.stats['teams_found'] / self.stats['success']
            print(f"[UP] Moyenne equipes/joueur: {avg_teams:.1f}")
        
        print("=" * 60)
    
    def save_results(self, segment: str):
        """Sauvegarder les resultats"""
        output_dir = "logs/nba19_discovery/results"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Mappings reussis
        mappings_file = f"{output_dir}/mappings_{segment}_{timestamp}.json"
        with open(mappings_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'segment': segment,
                    'created_at': datetime.now().isoformat(),
                    'total_mappings': len(self.successful_mappings),
                    'stats': self.stats
                },
                'data': self.successful_mappings
            }, f, indent=2)
        
        # Joueurs en echec
        if self.failed_players:
            failed_file = f"{output_dir}/failed_{segment}_{timestamp}.json"
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': {
                        'segment': segment,
                        'total_failed': len(self.failed_players)
                    },
                    'data': self.failed_players
                }, f, indent=2)
        
        print(f"\n[SAVE] Resultats sauvegardes:")
        print(f"   Mappings: {mappings_file}")
        if self.failed_players:
            print(f"   Echecs: {failed_file}")


def main():
    """Point d'entree principal"""
    parser = argparse.ArgumentParser(description='NBA-19 Discovery Engine (Test)')
    parser.add_argument(
        '--segment', 
        choices=['A', 'B', 'C'],
        default='A',
        help='Segment a traiter (A=GOLD, B=SILVER, C=BRONZE)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Nombre de joueurs a traiter (defaut: 100)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("[SCAN] NBA-19 PHASE 2: DISCOVERY ENGINE (TEST)")
    print("=" * 60)
    print(f"[TARGET] Segment: {args.segment} ({'GOLD' if args.segment=='A' else 'SILVER' if args.segment=='B' else 'BRONZE'})")
    print(f"[USERS] Limite: {args.limit} joueurs")
    
    # Charger les joueurs du segment
    tier = {'A': 'gold', 'B': 'silver', 'C': 'bronze'}[args.segment]
    segment_file = f"logs/nba19_discovery/segments/segment_{args.segment}_{tier}.json"
    
    if not os.path.exists(segment_file):
        print(f"\n[FAIL] Fichier non trouve: {segment_file}")
        print("   Lancer d'abord: python phase1_pre_validation.py")
        return
    
    with open(segment_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    players = data.get('data', [])[:args.limit]
    
    print(f"[OK] {len(players)} joueurs charges\n")
    
    # Lancer le discovery
    engine = DiscoveryEngine()
    engine.process_players(players, args.segment)
    engine.save_results(args.segment)
    
    print("\n[DONE] Phase 2 terminee!")


if __name__ == "__main__":
    main()
