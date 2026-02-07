#!/usr/bin/env python3
"""
Enrichissement des stats joueurs pour NBA-18
Récupère les stats de carrière depuis l'API NBA
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.nba_formulas import calculate_all_metrics
from utils.circuit_breaker import APICircuitBreaker


class PlayerStatsEnricher:
    """Enrichit les données joueurs avec leurs stats réelles"""
    
    def __init__(self):
        self.input_file = Path("data/silver/players_advanced/players.json")
        self.output_file = Path("data/silver/players_advanced/players_enriched.json")
        self.cache_dir = Path("data/raw/player_stats_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.circuit_breaker = APICircuitBreaker()
        self.stats = {
            'total': 0,
            'enriched': 0,
            'from_cache': 0,
            'from_api': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def load_players(self) -> List[Dict]:
        """Charge les joueurs existants"""
        print("Chargement des joueurs...")
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        players = data.get('data', [])
        self.stats['total'] = len(players)
        print(f"  {len(players)} joueurs charges")
        return players
    
    def get_cached_stats(self, player_id: int) -> Optional[Dict]:
        """Récupère les stats depuis le cache"""
        cache_file = self.cache_dir / f"player_{player_id}_stats.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        
        return None
    
    def cache_stats(self, player_id: int, stats: Dict):
        """Sauvegarde les stats dans le cache"""
        cache_file = self.cache_dir / f"player_{player_id}_stats.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
    
    def fetch_player_stats(self, player_id: int) -> Optional[Dict]:
        """Récupère les stats depuis l'API NBA"""
        try:
            from nba_api.stats.endpoints import playercareerstats
            
            # Appel API avec circuit breaker
            def api_call():
                return playercareerstats.PlayerCareerStats(player_id=player_id)
            
            career = self.circuit_breaker.call(api_call)
            data = career.get_dict()
            
            # Extraire stats de la dernière saison
            result_sets = data.get('resultSets', [])
            
            for rs in result_sets:
                if rs.get('name') == 'SeasonTotalsRegularSeason':
                    headers = rs.get('headers', [])
                    row_set = rs.get('rowSet', [])
                    
                    if not row_set:
                        return None
                    
                    # Prendre la dernière saison
                    latest_season = row_set[-1]
                    
                    # Créer dict avec headers
                    stats = dict(zip(headers, latest_season))
                    
                    # Convertir en format standard
                    return {
                        'pts': stats.get('PTS', 0),
                        'fgm': stats.get('FGM', 0),
                        'fga': stats.get('FGA', 0),
                        'ftm': stats.get('FTM', 0),
                        'fta': stats.get('FTA', 0),
                        '3pm': stats.get('FG3M', 0),
                        'oreb': stats.get('OREB', 0),
                        'dreb': stats.get('DREB', 0),
                        'reb': stats.get('REB', 0),
                        'ast': stats.get('AST', 0),
                        'stl': stats.get('STL', 0),
                        'blk': stats.get('BLK', 0),
                        'tov': stats.get('TOV', 0),
                        'pf': stats.get('PF', 0),
                        'minutes': stats.get('MIN', 0) or 1,
                        'gp': stats.get('GP', 0),
                        'season': stats.get('SEASON_ID', 'N/A')
                    }
            
            return None
            
        except Exception as e:
            print(f"    Erreur API pour {player_id}: {e}")
            return None
    
    def should_fetch_api(self, player: Dict) -> bool:
        """Détermine si on doit appeler l'API pour ce joueur"""
        # Ne pas appeler API pour joueurs historiques (avant 2000)
        from_year = player.get('from_year')
        if from_year and from_year < 2000:
            return False
        
        # Ne pas appeler API si données manquantes essentielles
        if not player.get('id'):
            return False
        
        return True
    
    def enrich_player(self, player: Dict) -> Dict:
        """Enrichit un joueur avec ses stats"""
        player_id = player.get('id')
        
        if not player_id:
            self.stats['skipped'] += 1
            return player
        
        # 1. Vérifier cache
        cached_stats = self.get_cached_stats(player_id)
        if cached_stats:
            player['stats_source'] = 'cache'
            player.update(cached_stats)
            self.stats['from_cache'] += 1
            return player
        
        # 2. Vérifier si on doit appeler API
        if not self.should_fetch_api(player):
            # Utiliser données existantes (BMI déjà calculé)
            player['stats_source'] = 'existing'
            self.stats['skipped'] += 1
            return player
        
        # 3. Appeler API
        print(f"  Fetching stats for {player.get('full_name', player_id)}...")
        api_stats = self.fetch_player_stats(player_id)
        
        if api_stats:
            # Sauvegarder dans cache
            self.cache_stats(player_id, api_stats)
            
            # Calculer métriques avancées
            metrics = calculate_all_metrics(api_stats)
            
            # Mettre à jour joueur
            player.update(api_stats)
            player.update(metrics)
            player['stats_source'] = 'api'
            player['stats_season'] = api_stats.get('season')
            
            self.stats['from_api'] += 1
            print(f"    OK Stats fetched: PTS={api_stats['pts']}, PER={metrics['per']:.2f}")
        else:
            self.stats['failed'] += 1
            player['stats_source'] = 'failed'
        
        return player
    
    def enrich_all_players(self, players: List[Dict]) -> List[Dict]:
        """Enrichit tous les joueurs"""
        print("\nEnrichissement des stats joueurs...")
        
        enriched = []
        
        for i, player in enumerate(players, 1):
            # Afficher progression tous les 100 joueurs
            if i % 100 == 0:
                print(f"\n  Progression: {i}/{len(players)} ({i/len(players)*100:.1f}%)")
                print(f"    Enrichis: {self.stats['enriched']}, API: {self.stats['from_api']}, Cache: {self.stats['from_cache']}")
            
            enriched_player = self.enrich_player(player)
            enriched.append(enriched_player)
            
            # Petite pause pour respecter rate limit
            if self.stats['from_api'] % 10 == 0 and self.stats['from_api'] > 0:
                time.sleep(0.5)
        
        return enriched
    
    def calculate_enriched_statistics(self, players: List[Dict]) -> Dict:
        """Calcule les stats sur les données enrichies"""
        print("\nCalcul des statistiques...")
        
        metrics_data = {
            'per': [],
            'ts_pct': [],
            'usg_pct': [],
            'efg_pct': [],
            'bmi': [],
            'pts': []
        }
        
        sources = {'api': 0, 'cache': 0, 'existing': 0, 'failed': 0}
        
        for player in players:
            source = player.get('stats_source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
            
            for metric in metrics_data.keys():
                value = player.get(metric, 0)
                if value and value > 0:
                    metrics_data[metric].append(value)
        
        # Calculer stats
        stats = {}
        for metric, values in metrics_data.items():
            if values:
                stats[metric] = {
                    'count': len(values),
                    'mean': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values)
                }
        
        print("\n  Statistiques des metriques:")
        for metric, stat in stats.items():
            print(f"    {metric}: moy={stat['mean']:.2f}, min={stat['min']:.2f}, max={stat['max']:.2f}, n={stat['count']}")
        
        print("\n  Sources des donnees:")
        for source, count in sources.items():
            print(f"    {source}: {count}")
        
        return stats
    
    def save_results(self, players: List[Dict], stats: Dict):
        """Sauvegarde les résultats"""
        print(f"\nSauvegarde des resultats...")
        
        # Sauvegarder joueurs enrichis
        output_data = {
            'metadata': {
                'created_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'version': 'NBA-18-ENRICHED-v1.0',
                'total_players': len(players),
                'metrics': ['per', 'ts_pct', 'efg_pct', 'usg_pct', 'game_score', 'bmi'],
                'enriched_count': self.stats['from_api'] + self.stats['from_cache'],
                'api_calls': self.stats['from_api'],
                'from_cache': self.stats['from_cache']
            },
            'data': players
        }
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Sauvegarde: {self.output_file}")
        
        # Sauvegarder stats
        stats_file = Path("data/silver/players_advanced/enrichment_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'statistics': stats,
                'enrichment_stats': self.stats
            }, f, indent=2)
        
        print(f"  ✓ Stats: {stats_file}")
    
    def run(self):
        """Exécute l'enrichissement complet"""
        print("="*60)
        print("NBA-18: ENRICHISSEMENT DES STATS JOUEURS")
        print("="*60)
        
        try:
            # 1. Charger joueurs
            players = self.load_players()
            
            # 2. Enrichir
            enriched_players = self.enrich_all_players(players)
            
            # 3. Calculer stats
            stats = self.calculate_enriched_statistics(enriched_players)
            
            # 4. Sauvegarder
            self.save_results(enriched_players, stats)
            
            print("\n" + "="*60)
            print("✓ ENRICHISSEMENT TERMINE")
            print("="*60)
            print(f"\n  Total: {self.stats['total']}")
            print(f"  Depuis API: {self.stats['from_api']}")
            print(f"  Depuis cache: {self.stats['from_cache']}")
            print(f"  Existant: {self.stats['skipped']}")
            print(f"  Echecs: {self.stats['failed']}")
            
            return True
            
        except Exception as e:
            print(f"\nERREUR: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    enricher = PlayerStatsEnricher()
    success = enricher.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
