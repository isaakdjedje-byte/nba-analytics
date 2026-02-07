#!/usr/bin/env python3
"""
NBA-18 V2: Enrichissement avec agrégation 4 méthodes
- Dernière complète (35%)
- Max minutes (25%)
- Moyenne 3 saisons (20%)
- Best PER (20%)
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.nba_formulas import calculate_all_metrics
from utils.season_selector import SeasonSelector


class AdvancedStatsEnricherV2:
    """Enrichisseur V2 avec agrégation intelligente"""
    
    def __init__(self, batch_size: int = 50, delay: float = 2.0):
        self.batch_size = batch_size
        self.delay = delay
        self.input_file = Path("data/silver/players_gold_standard/players.json")
        self.output_dir = Path("data/silver/players_advanced_v2")
        self.cache_dir = Path("data/raw/player_stats_cache_v2")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.selector = SeasonSelector()
        self.stats = {
            'total': 0,
            'already_cached': 0,
            'newly_fetched': 0,
            'failed': 0,
            'methods_used': {'complete': 0, 'max_minutes': 0, 'avg_3': 0, 'best_per': 0}
        }
    
    def load_players(self) -> List[Dict]:
        """Charge les joueurs"""
        print("Chargement des joueurs...")
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        players = data.get('data', [])
        self.stats['total'] = len(players)
        print(f"  {len(players)} joueurs charges")
        return players
    
    def get_cached_ids(self) -> set:
        """IDs déjà en cache"""
        cached = set()
        for f in self.cache_dir.glob('player_*_stats.json'):
            try:
                pid = int(f.stem.split('_')[1])
                cached.add(pid)
            except:
                pass
        return cached
    
    def fetch_and_process_player(self, player_id: int, player_name: str) -> Optional[Dict]:
        """Récupère et traite un joueur avec les 4 méthodes"""
        try:
            from nba_api.stats.endpoints import playercareerstats
            
            career = playercareerstats.PlayerCareerStats(
                player_id=player_id,
                timeout=60
            )
            data = career.get_dict()
            
            # Trouver SeasonTotalsRegularSeason
            for rs in data.get('resultSets', []):
                if rs.get('name') == 'SeasonTotalsRegularSeason':
                    headers = rs.get('headers', [])
                    row_set = rs.get('rowSet', [])
                    
                    if not row_set:
                        return None
                    
                    # Obtenir les 4 saisons
                    seasons = self.selector.get_all_four_seasons(row_set, headers)
                    
                    # Agréger
                    aggregated_stats, metadata = self.selector.aggregate_metrics(seasons)
                    
                    if not aggregated_stats:
                        return None
                    
                    # Calculer métriques avancées
                    metrics = calculate_all_metrics(aggregated_stats)
                    
                    # Créer résultat
                    result = {
                        'player_id': player_id,
                        'player_name': player_name,
                        'aggregated': {
                            'raw_stats': aggregated_stats,
                            'metrics': metrics
                        },
                        'breakdown': {
                            method: {
                                'available': data.get('available', False),
                                'season': data.get('season'),
                                'stats': data.get('stats') if data.get('available') else None
                            }
                            for method, data in seasons.items()
                        },
                        'aggregation_metadata': metadata,
                        'api_response': {
                            'total_seasons': len(row_set),
                            'headers': headers[:10]  # Premier 10 pour info
                        }
                    }
                    
                    return result
            
            return None
            
        except Exception as e:
            print(f"    Erreur: {str(e)[:60]}")
            return None
    
    def cache_result(self, player_id: int, result: Dict):
        """Sauvegarde dans cache"""
        cache_file = self.cache_dir / f"player_{player_id}_stats.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    
    def process_batch(self, players: List[Dict], batch_num: int, total_batches: int):
        """Traite un batch"""
        print(f"\nBatch {batch_num}/{total_batches} ({len(players)} joueurs)")
        print("-" * 60)
        
        success = 0
        fail = 0
        
        for i, player in enumerate(players, 1):
            pid = player.get('id')
            name = player.get('full_name', f'ID_{pid}')
            
            # Vérifier cache
            cache_file = self.cache_dir / f"player_{pid}_stats.json"
            if cache_file.exists():
                self.stats['already_cached'] += 1
                continue
            
            # Vérifier moderne
            from_year = player.get('from_year')
            if from_year and from_year < 2000:
                continue
            
            print(f"  [{i}/{len(players)}] {name}...", end=' ')
            
            result = self.fetch_and_process_player(pid, name)
            
            if result:
                self.cache_result(pid, result)
                self.stats['newly_fetched'] += 1
                
                # Compter méthodes utilisées
                methods = result['aggregation_metadata'].get('methods_used', [])
                for m in methods:
                    if m in self.stats['methods_used']:
                        self.stats['methods_used'][m] += 1
                
                per = result['aggregated']['metrics'].get('per', 0)
                print(f"OK PER={per:.1f}")
                success += 1
            else:
                print("ECHEC")
                fail += 1
            
            if i < len(players):
                time.sleep(self.delay)
        
        print(f"\nBatch {batch_num}: {success} OK, {fail} ECHEC")
        return success, fail
    
    def run(self, max_batches: int = None):
        """Exécute l'enrichissement"""
        print("=" * 70)
        print("NBA-18 V2: ENRICHISSEMENT 4 METHODES")
        print("=" * 70)
        print("Methodes: complete(35%), max_minutes(25%), avg_3(20%), best_per(20%)")
        print()
        
        players = self.load_players()
        cached_ids = self.get_cached_ids()
        print(f"  Deja en cache: {len(cached_ids)}")
        
        # Filtrer à traiter
        to_process = [p for p in players if p.get('id') not in cached_ids]
        to_process = [p for p in to_process if not p.get('from_year') or p.get('from_year') >= 2000]
        
        print(f"  A traiter: {len(to_process)}")
        
        if not to_process:
            print("\nTous les joueurs sont enrichis!")
            return True
        
        total_batches = (len(to_process) + self.batch_size - 1) // self.batch_size
        if max_batches:
            total_batches = min(total_batches, max_batches)
        
        print(f"\nTraitement en {total_batches} batchs de {self.batch_size} joueurs")
        
        total_success = 0
        total_fail = 0
        
        for batch_num in range(1, total_batches + 1):
            start_idx = (batch_num - 1) * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(to_process))
            batch = to_process[start_idx:end_idx]
            
            s, f = self.process_batch(batch, batch_num, total_batches)
            total_success += s
            total_fail += f
            
            # Progression
            total_cached = len(cached_ids) + self.stats['newly_fetched']
            progress = total_cached / self.stats['total'] * 100
            print(f"\nProgression: {progress:.1f}% ({total_cached}/{self.stats['total']})")
            
            if batch_num < total_batches:
                print(f"\nPause 10s...")
                time.sleep(10)
        
        # Rapport
        print("\n" + "=" * 70)
        print("RESUME")
        print("=" * 70)
        print(f"Total traité: {total_success + total_fail}")
        print(f"  Succes: {total_success}")
        print(f"  Echecs: {total_fail}")
        print(f"\nNouveaux: {self.stats['newly_fetched']}")
        print(f"Deja cache: {self.stats['already_cached']}")
        print(f"\nMethodes utilisees:")
        for method, count in self.stats['methods_used'].items():
            print(f"  {method}: {count}")
        
        return True


def main():
    enricher = AdvancedStatsEnricherV2(batch_size=50, delay=2.0)
    success = enricher.run(max_batches=20)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
