#!/usr/bin/env python3
"""
NBA-18: Enrichissement batch des stats joueurs
Version avec gestion améliorée des rate limits
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.nba_formulas import calculate_all_metrics


class BatchStatsEnricher:
    """Enrichit les stats joueurs en batch avec gestion rate limit"""
    
    def __init__(self, batch_size: int = 50, delay: float = 2.0):
        self.batch_size = batch_size
        self.delay = delay
        self.input_file = Path("data/silver/players_gold_standard/players.json")
        self.cache_dir = Path("data/raw/player_stats_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            'total': 0,
            'already_cached': 0,
            'newly_fetched': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def load_players(self) -> List[Dict]:
        """Charge tous les joueurs"""
        print("Chargement des joueurs...")
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        players = data.get('data', [])
        self.stats['total'] = len(players)
        print(f"  {len(players)} joueurs chargés")
        return players
    
    def get_cached_ids(self) -> set:
        """Retourne les IDs des joueurs déjà en cache"""
        cached_ids = set()
        for cache_file in self.cache_dir.glob('player_*_stats.json'):
            try:
                player_id = int(cache_file.stem.split('_')[1])
                cached_ids.add(player_id)
            except:
                pass
        return cached_ids
    
    def fetch_player_stats(self, player_id: int, player_name: str) -> Optional[Dict]:
        """Récupère les stats d'un joueur depuis l'API"""
        try:
            from nba_api.stats.endpoints import playercareerstats
            import requests
            
            # Timeout plus long
            career = playercareerstats.PlayerCareerStats(
                player_id=player_id,
                timeout=60
            )
            data = career.get_dict()
            
            # Extraire stats régulières saison
            for rs in data.get('resultSets', []):
                if rs.get('name') == 'SeasonTotalsRegularSeason':
                    headers = rs.get('headers', [])
                    row_set = rs.get('rowSet', [])
                    
                    if not row_set:
                        return None
                    
                    # Dernière saison
                    latest = row_set[-1]
                    stats = dict(zip(headers, latest))
                    
                    return {
                        'pts': stats.get('PTS', 0) or 0,
                        'fgm': stats.get('FGM', 0) or 0,
                        'fga': stats.get('FGA', 0) or 0,
                        'ftm': stats.get('FTM', 0) or 0,
                        'fta': stats.get('FTA', 0) or 0,
                        '3pm': stats.get('FG3M', 0) or 0,
                        'oreb': stats.get('OREB', 0) or 0,
                        'dreb': stats.get('DREB', 0) or 0,
                        'reb': stats.get('REB', 0) or 0,
                        'ast': stats.get('AST', 0) or 0,
                        'stl': stats.get('STL', 0) or 0,
                        'blk': stats.get('BLK', 0) or 0,
                        'tov': stats.get('TOV', 0) or 0,
                        'pf': stats.get('PF', 0) or 0,
                        'minutes': stats.get('MIN', 0) or 1,
                        'gp': stats.get('GP', 0) or 0,
                        'season': stats.get('SEASON_ID', 'N/A')
                    }
            
            return None
            
        except requests.exceptions.ReadTimeout:
            print(f"    Timeout pour {player_name}")
            return None
        except Exception as e:
            print(f"    Erreur API {player_name}: {str(e)[:50]}")
            return None
    
    def cache_stats(self, player_id: int, stats: Dict):
        """Sauvegarde dans le cache"""
        cache_file = self.cache_dir / f"player_{player_id}_stats.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
    
    def process_batch(self, players: List[Dict], batch_num: int, total_batches: int):
        """Traite un batch de joueurs"""
        print(f"\nBatch {batch_num}/{total_batches} ({len(players)} joueurs)")
        print("-" * 60)
        
        success_count = 0
        fail_count = 0
        
        for i, player in enumerate(players, 1):
            player_id = player.get('id')
            player_name = player.get('full_name', f'ID_{player_id}')
            
            # Vérifier déjà en cache
            cache_file = self.cache_dir / f"player_{player_id}_stats.json"
            if cache_file.exists():
                self.stats['already_cached'] += 1
                continue
            
            # Vérifier si on doit appeler API
            from_year = player.get('from_year')
            if from_year and from_year < 2000:
                self.stats['skipped'] += 1
                continue
            
            print(f"  [{i}/{len(players)}] {player_name}...", end=' ')
            
            # Appel API
            stats = self.fetch_player_stats(player_id, player_name)
            
            if stats:
                self.cache_stats(player_id, stats)
                self.stats['newly_fetched'] += 1
                success_count += 1
                print(f"OK (PTS={stats['pts']}, PER={stats['pts']/stats['minutes']*48:.1f})")
            else:
                self.stats['failed'] += 1
                fail_count += 1
                print("ECHEC")
            
            # Délai entre appels
            if i < len(players):
                time.sleep(self.delay)
        
        print(f"\nBatch {batch_num}: {success_count} OK, {fail_count} ECHEC")
        return success_count, fail_count
    
    def run(self, max_batches: int = None):
        """Exécute l'enrichissement en batchs"""
        print("=" * 60)
        print("NBA-18: ENRICHISSEMENT BATCH DES STATS")
        print("=" * 60)
        
        # Charger joueurs
        players = self.load_players()
        
        # Joueurs déjà en cache
        cached_ids = self.get_cached_ids()
        print(f"  Déjà en cache: {len(cached_ids)}")
        
        # Filtrer joueurs à traiter
        players_to_process = [p for p in players if p.get('id') not in cached_ids]
        
        # Filtrer joueurs modernes (après 2000)
        players_to_process = [
            p for p in players_to_process 
            if not p.get('from_year') or p.get('from_year') >= 2000
        ]
        
        print(f"  À traiter: {len(players_to_process)}")
        
        if not players_to_process:
            print("\nTous les joueurs sont déjà enrichis!")
            return True
        
        # Calculer nombre de batchs
        total_batches = (len(players_to_process) + self.batch_size - 1) // self.batch_size
        if max_batches:
            total_batches = min(total_batches, max_batches)
        
        print(f"\nTraitement en {total_batches} batchs de {self.batch_size} joueurs")
        print(f"Délai entre appels: {self.delay}s")
        print()
        
        # Traiter les batchs
        total_success = 0
        total_fail = 0
        
        for batch_num in range(1, total_batches + 1):
            start_idx = (batch_num - 1) * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(players_to_process))
            batch = players_to_process[start_idx:end_idx]
            
            success, fail = self.process_batch(batch, batch_num, total_batches)
            total_success += success
            total_fail += fail
            
            # Progression globale
            progress = (self.stats['already_cached'] + self.stats['newly_fetched']) / self.stats['total'] * 100
            print(f"\nProgression globale: {progress:.1f}%")
            print(f"  Nouveaux: {self.stats['newly_fetched']}, Cache: {self.stats['already_cached']}")
            
            # Pause entre batchs
            if batch_num < total_batches:
                pause = 10
                print(f"\nPause de {pause}s entre batchs...")
                time.sleep(pause)
        
        # Rapport final
        print("\n" + "=" * 60)
        print("ENRICHISSEMENT TERMINE")
        print("=" * 60)
        print(f"\nTotal traité: {total_success + total_fail}")
        print(f"  Succès: {total_success}")
        print(f"  Échecs: {total_fail}")
        print(f"\nCumul:")
        print(f"  Total en cache: {self.stats['already_cached'] + self.stats['newly_fetched']}")
        print(f"  Taux enrichissement: {(self.stats['already_cached'] + self.stats['newly_fetched'])/self.stats['total']*100:.1f}%")
        
        return True


def main():
    # Paramètres
    batch_size = 50  # Joueurs par batch
    delay = 2.0      # Secondes entre appels
    max_batches = 20  # Limite pour cette session (1000 joueurs)
    
    enricher = BatchStatsEnricher(batch_size=batch_size, delay=delay)
    success = enricher.run(max_batches=max_batches)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
