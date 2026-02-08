#!/usr/bin/env python3
"""
NBA-19 Phase 2: Discovery Complet (Tous segments)

Traite les 5 103 joueurs en ~3h avec reprise automatique.
Segments: A (GOLD) → B (SILVER) → C (BRONZE)

Usage:
    python phase2_discovery_all.py
    
Temps estimé: ~3h
"""
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Imports locaux
from circuit_breaker import CircuitBreaker
from rate_limiter import RateLimiter, RateLimitConfig
from checkpoint_manager import CheckpointManager

try:
    from nba_api.stats.endpoints import PlayerCareerStats
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from nba_api.stats.endpoints import PlayerCareerStats


class CompleteDiscoveryEngine:
    """Moteur de discovery pour tous les segments"""
    
    def __init__(self):
        config = RateLimitConfig(delay_seconds=2.0)
        self.rate_limiter = RateLimiter(config)
        # Augmenter seuil car echecs normaux (joueurs sans data API)
        self.circuit_breaker = CircuitBreaker(failure_threshold=0.25)  # 25% au lieu de 10%
        self.checkpoint_mgr = CheckpointManager("logs/nba19_discovery/checkpoints")
        
        self.successful_mappings = []
        self.failed_players = []
        self.stats = {
            'total_segments': 3,
            'completed_segments': 0,
            'total_players': 0,
            'success': 0,
            'failed': 0,
            'teams_found': 0
        }
    
    def load_segment(self, segment_name: str) -> List[Dict]:
        """Charger les joueurs d'un segment"""
        tier = {'A': 'gold', 'B': 'silver', 'C': 'bronze'}[segment_name]
        filepath = f"logs/nba19_discovery/segments/segment_{segment_name}_{tier}.json"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get('data', [])
    
    def discover_player_teams(self, player_id: int, player_name: str) -> Optional[List[Dict]]:
        """Découvrir les équipes d'un joueur"""
        try:
            career = PlayerCareerStats(player_id=player_id, timeout=30)
            season_df = career.get_data_frames()[0]
            
            if season_df.empty:
                return None
            
            mappings = []
            for _, row in season_df.iterrows():
                season = row.get('SEASON_ID', '')
                team_id = row.get('TEAM_ID')
                team_abbr = row.get('TEAM_ABBREVIATION', '')
                games = row.get('GP', 0)
                
                # Filtrer TOT entries
                if team_id == 0 or team_abbr == 'TOT':
                    continue
                
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
            
            return mappings
            
        except Exception as e:
            return None
    
    def process_segment(self, segment_name: str, tier: str):
        """Traiter un segment complet"""
        print(f"\n{'='*70}")
        print(f">>> SEGMENT {segment_name} ({tier.upper()})")
        print(f"{'='*70}")
        
        players = self.load_segment(segment_name)
        total = len(players)
        self.stats['total_players'] += total
        
        print(f"Joueurs: {total}")
        print(f"Estimation: ~{total * 2 // 60} minutes\n")
        
        # Vérifier s'il y a un checkpoint
        idx, prev_success, prev_failed = self.checkpoint_mgr.get_resume_position(
            f"phase2", segment_name
        )
        
        if idx > 0:
            print(f"[RESUME] Reprise depuis joueur {idx}")
            self.successful_mappings = prev_success
            self.failed_players = prev_failed
        
        segment_start_time = time.time()
        
        for i in range(idx, total):
            player = players[i]
            player_id = player.get('id')
            player_name = player.get('full_name', f'Player_{player_id}')
            
            # Progress
            if (i + 1) % 10 == 0 or i == 0:
                progress = ((i + 1) / total) * 100
                elapsed = time.time() - segment_start_time
                eta = (elapsed / (i + 1)) * (total - i - 1) if i > 0 else 0
                print(f"\n[PROGRESS] {i+1}/{total} ({progress:.0f}%) - ETA: {int(eta//60)}m {int(eta%60)}s")
            
            print(f"[{i+1:4d}/{total}] {player_name[:35]:35}...", end=" ", flush=True)
            
            if not self.circuit_breaker.can_execute():
                print("\n[STOP] Circuit ouvert - Sauvegarde et arret")
                self._save_checkpoint(i, segment_name)
                return False
            
            self.rate_limiter.wait_if_needed()
            
            try:
                mappings = self.discover_player_teams(player_id, player_name)
                self.rate_limiter.record_request()
                
                if mappings:
                    self.successful_mappings.extend(mappings)
                    self.stats['success'] += 1
                    self.stats['teams_found'] += len(mappings)
                    self.circuit_breaker.record_success()
                    print(f"[OK] {len(mappings):2d} equipes")
                else:
                    self.failed_players.append({
                        'player_id': player_id,
                        'player_name': player_name,
                        'segment': segment_name,
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
                    'segment': segment_name,
                    'reason': str(e)
                })
                self.stats['failed'] += 1
                self.circuit_breaker.record_failure()
                print(f"[ERROR] {str(e)[:30]}")
            
            # Checkpoint tous les 50 joueurs
            if (i + 1) % 50 == 0:
                self._save_checkpoint(i + 1, segment_name)
        
        # Checkpoint final du segment
        self._save_checkpoint(total, segment_name)
        self.stats['completed_segments'] += 1
        
        # Résumé segment
        segment_time = time.time() - segment_start_time
        print(f"\n[SEGMENT_DONE] {segment_name} complete en {int(segment_time//60)}m {int(segment_time%60)}s")
        print(f"   Success: {self.stats['success']}, Failed: {self.stats['failed']}")
        
        return True
    
    def _save_checkpoint(self, index: int, segment: str):
        """Sauvegarder checkpoint"""
        # Sauvegarder les mappings reussis du segment en cours
        segment_success = [m for m in self.successful_mappings if m.get('segment') == segment]
        segment_failed = [p for p in self.failed_players if p.get('segment') == segment]
        
        self.checkpoint_mgr.save_checkpoint(
            phase="phase2",
            segment=segment,
            player_index=index,
            successful_mappings=segment_success,
            failed_players=segment_failed
        )
    
    def run_all_segments(self):
        """Exécuter tous les segments"""
        print("="*70)
        print(">>> PHASE 2: DISCOVERY COMPLET (TOUS SEGMENTS)")
        print("="*70)
        print(f"Demarre: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Segments: A (GOLD) → B (SILVER) → C (BRONZE)")
        print("Temps estime: ~3h\n")
        
        segments = [
            ('A', 'gold', 1193),
            ('B', 'silver', 7),
            ('C', 'bronze', 3903)
        ]
        
        for seg_name, tier, count in segments:
            success = self.process_segment(seg_name, tier)
            if not success:
                print(f"\n[STOP] Arret apres echec segment {seg_name}")
                break
        
        # Résumé final
        self._print_final_summary()
        self._save_all_results()
    
    def _print_final_summary(self):
        """Résumé final"""
        print("\n" + "="*70)
        print(">>> RESUME FINAL PHASE 2")
        print("="*70)
        print(f"Segments completes: {self.stats['completed_segments']}/3")
        print(f"Total joueurs: {self.stats['total_players']}")
        print(f"Success: {self.stats['success']} ({self.stats['success']/max(1,self.stats['total_players'])*100:.1f}%)")
        print(f"Failed: {self.stats['failed']}")
        print(f"Equipes trouvees: {self.stats['teams_found']}")
        if self.stats['success'] > 0:
            avg = self.stats['teams_found'] / self.stats['success']
            print(f"Moyenne equipes/joueur: {avg:.1f}")
        print("="*70)
    
    def _save_all_results(self):
        """Sauvegarder tous les résultats"""
        output_dir = "logs/nba19_discovery/results"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Mappings
        with open(f"{output_dir}/all_mappings_{timestamp}.json", 'w') as f:
            json.dump({
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'total': len(self.successful_mappings),
                    'stats': self.stats
                },
                'data': self.successful_mappings
            }, f, indent=2)
        
        # Failed
        if self.failed_players:
            with open(f"{output_dir}/all_failed_{timestamp}.json", 'w') as f:
                json.dump({
                    'metadata': {'total': len(self.failed_players)},
                    'data': self.failed_players
                }, f, indent=2)
        
        print(f"\n[SAVE] Resultats sauvegardes dans: {output_dir}")


def main():
    """Point d'entree"""
    engine = CompleteDiscoveryEngine()
    engine.run_all_segments()
    print("\n[DONE] Phase 2 complete!")


if __name__ == "__main__":
    main()
