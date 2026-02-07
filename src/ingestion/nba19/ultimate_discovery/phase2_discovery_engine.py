"""
NBA-19 Phase 2: Discovery Engine (Version Test - 100 joueurs)

Moteur de discovery pour trouver les équipes des joueurs via PlayerCareerStats API.
Version limitée à 100 joueurs pour test rapide.

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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from nba_api.stats.endpoints import PlayerCareerStats
from src.ingestion.nba19.ultimate_discovery.circuit_breaker import CircuitBreaker, CircuitBreakerOpen
from src.ingestion.nba19.ultimate_discovery.rate_limiter import RateLimiter


class DiscoveryEngine:
    """Moteur de discovery pour trouver les équipes des joueurs"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(delay_seconds=2.0)
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
        Découvrir les équipes d'un joueur via PlayerCareerStats
        
        Returns:
            Liste des mappings saison-équipe ou None si échec
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
                
                # Filtrer les entrées TOT (team_id = 0)
                if team_id == 0 or team_abbr == 'TOT':
                    continue
                
                # Filtrer pour les saisons qui nous intéressent
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
                print(f"      ⚠️ Retry {retry + 1}/3 dans {wait_time}s...")
                time.sleep(wait_time)
                return self.discover_player_teams(player_id, player_name, retry + 1)
            else:
                print(f"      ❌ Échec après 3 tentatives: {e}")
                return None
    
    def process_players(self, players: List[Dict], segment_name: str):
        """Traiter une liste de joueurs"""
        total = len(players)
        self.stats['total'] = total
        
        print(f"\n🚀 Démarrage du discovery: {total} joueurs (Segment {segment_name})")
        print(f"   Rate limit: 1 req / 2 sec")
        print(f"   Estimation: ~{total * 2 // 60} minutes\n")
        
        for idx, player in enumerate(players, 1):
            player_id = player.get('id')
            player_name = player.get('full_name', f'Player_{player_id}')
            
            # Progress
            if idx % 10 == 0:
                progress = (idx / total) * 100
                print(f"\n📊 Progression: {idx}/{total} ({progress:.0f}%)")
            
            print(f"[{idx:3d}/{total}] {player_name[:30]:30}...", end=" ", flush=True)
            
            # Circuit breaker check
            if not self.circuit_breaker.can_execute():
                print("⛔ CIRCUIT OUVERT - Arrêt")
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
                    print(f"✅ {len(mappings)} équipes")
                else:
                    self.failed_players.append({
                        'player_id': player_id,
                        'player_name': player_name,
                        'reason': 'no_data'
                    })
                    self.stats['failed'] += 1
                    self.circuit_breaker.record_failure()
                    print("❌ Pas de données")
                    
            except Exception as e:
                self.rate_limiter.record_request()
                self.failed_players.append({
                    'player_id': player_id,
                    'player_name': player_name,
                    'reason': str(e)
                })
                self.stats['failed'] += 1
                self.circuit_breaker.record_failure()
                print(f"❌ Erreur: {e}")
            
            # Checkpoint tous les 20 joueurs
            if idx % 20 == 0:
                self._save_checkpoint(idx, segment_name)
        
        # Résumé final
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
        
        print(f"   💾 Checkpoint sauvegardé")
    
    def _print_summary(self):
        """Afficher le résumé"""
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DU DISCOVERY")
        print("=" * 60)
        print(f"👥 Total joueurs: {self.stats['total']}")
        print(f"✅ Succès: {self.stats['success']} ({self.stats['success']/self.stats['total']*100:.1f}%)")
        print(f"❌ Échecs: {self.stats['failed']}")
        print(f"🏀 Équipes trouvées: {self.stats['teams_found']}")
        
        if self.successful_mappings:
            avg_teams = self.stats['teams_found'] / self.stats['success']
            print(f"📈 Moyenne équipes/joueur: {avg_teams:.1f}")
        
        print("=" * 60)
    
    def save_results(self, segment: str):
        """Sauvegarder les résultats"""
        output_dir = "logs/nba19_discovery/results"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Mappings réussis
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
        
        # Joueurs en échec
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
        
        print(f"\n💾 Résultats sauvegardés:")
        print(f"   Mappings: {mappings_file}")
        if self.failed_players:
            print(f"   Échecs: {failed_file}")


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='NBA-19 Discovery Engine (Test)')
    parser.add_argument(
        '--segment', 
        choices=['A', 'B', 'C'],
        default='A',
        help='Segment à traiter (A=GOLD, B=SILVER, C=BRONZE)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Nombre de joueurs à traiter (défaut: 100)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔍 NBA-19 PHASE 2: DISCOVERY ENGINE (TEST)")
    print("=" * 60)
    print(f"🎯 Segment: {args.segment} ({'GOLD' if args.segment=='A' else 'SILVER' if args.segment=='B' else 'BRONZE'})")
    print(f"👥 Limite: {args.limit} joueurs")
    
    # Charger les joueurs du segment
    segment_file = f"logs/nba19_discovery/segments/segment_{args.segment}_{args.segment.lower()}.json"
    
    if not os.path.exists(segment_file):
        print(f"\n❌ Fichier non trouvé: {segment_file}")
        print("   Lancer d'abord: python phase1_pre_validation.py")
        return
    
    with open(segment_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    players = data.get('data', [])[:args.limit]
    
    print(f"✅ {len(players)} joueurs chargés\n")
    
    # Lancer le discovery
    engine = DiscoveryEngine()
    engine.process_players(players, args.segment)
    engine.save_results(args.segment)
    
    print("\n✨ Phase 2 terminée!")


if __name__ == "__main__":
    main()
