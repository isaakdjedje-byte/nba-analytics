#!/usr/bin/env python3
"""
NBA-18 Final: Compilation du dataset complet
Avec agrégation 4 méthodes
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.nba_formulas import calculate_bmi


def compile_final_dataset():
    """Compile le dataset final NBA-18"""
    print("=" * 70)
    print("NBA-18 FINAL: COMPILATION DATASET")
    print("=" * 70)
    
    # Chemins
    gold_file = Path("data/silver/players_gold_standard/players.json")
    cache_dir = Path("data/raw/player_stats_cache_v2")
    output_dir = Path("data/silver/players_advanced")
    
    # Charger joueurs GOLD
    print("\n1. Chargement des joueurs GOLD...")
    with open(gold_file, 'r', encoding='utf-8') as f:
        gold_data = json.load(f)
        players = gold_data['data']
    
    print(f"   {len(players)} joueurs")
    
    # Charger cache V2
    print("\n2. Chargement du cache V2...")
    cache_files = list(cache_dir.glob('player_*_stats.json'))
    print(f"   {len(cache_files)} joueurs enrichis")
    
    cached_data = {}
    for cf in cache_files:
        try:
            pid = int(cf.stem.split('_')[1])
            with open(cf, 'r', encoding='utf-8') as f:
                cached_data[pid] = json.load(f)
        except:
            pass
    
    # Enrichir tous les joueurs
    print("\n3. Enrichissement des joueurs...")
    enriched_players = []
    stats_summary = {
        'total': len(players),
        'with_api': 0,
        'with_bmi_only': 0,
        'methods_used': defaultdict(int)
    }
    
    for i, player in enumerate(players):
        if i % 1000 == 0:
            print(f"   Progression: {i}/{len(players)}")
        
        pid = player.get('id')
        
        if pid in cached_data:
            # Joueur avec stats API
            cache_entry = cached_data[pid]
            
            # Ajouter stats brutes
            raw_stats = cache_entry['aggregated']['raw_stats']
            player.update(raw_stats)
            
            # Ajouter métriques
            metrics = cache_entry['aggregated']['metrics']
            player.update(metrics)
            
            # Métadonnées
            player['stats_source'] = 'api_v2'
            player['aggregation_metadata'] = cache_entry['aggregation_metadata']
            player['breakdown'] = cache_entry['breakdown']
            
            stats_summary['with_api'] += 1
            
            # Compter méthodes
            for method in cache_entry['aggregation_metadata'].get('methods_used', []):
                stats_summary['methods_used'][method] += 1
        else:
            # Joueur sans stats API - juste BMI
            if not player.get('bmi'):
                player['bmi'] = calculate_bmi(
                    player.get('height_cm', 0),
                    player.get('weight_kg', 0)
                )
            player['stats_source'] = 'bmi_only'
            stats_summary['with_bmi_only'] += 1
        
        enriched_players.append(player)
    
    # Sauvegarder dataset final
    print("\n4. Sauvegarde du dataset final...")
    output_file = output_dir / 'players_enriched_final.json'
    
    output_data = {
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'version': 'NBA-18-FINAL-v2.0',
            'total_players': len(enriched_players),
            'with_api_data': stats_summary['with_api'],
            'with_bmi_only': stats_summary['with_bmi_only'],
            'methods_breakdown': dict(stats_summary['methods_used']),
            'aggregation_weights': {
                'complete': 0.35,
                'max_minutes': 0.25,
                'avg_3': 0.20,
                'best_per': 0.20
            }
        },
        'data': enriched_players
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"   Sauvegarde: {output_file}")
    
    # Calculer statistiques finales
    print("\n5. Calcul des statistiques...")
    enriched_only = [p for p in enriched_players if p.get('stats_source') == 'api_v2']
    
    metrics_stats = {}
    for metric in ['per', 'ts_pct', 'usg_pct', 'efg_pct', 'game_score', 'bmi']:
        values = [p.get(metric, 0) for p in enriched_players if p.get(metric, 0) > 0]
        if values:
            metrics_stats[metric] = {
                'count': len(values),
                'mean': sum(values) / len(values),
                'min': min(values),
                'max': max(values)
            }
    
    # Rapport final
    print("\n" + "=" * 70)
    print("NBA-18 FINAL - RAPPORT")
    print("=" * 70)
    print(f"\nTotal joueurs: {stats_summary['total']}")
    print(f"  - Avec API (4 methodes): {stats_summary['with_api']} ({stats_summary['with_api']/stats_summary['total']*100:.1f}%)")
    print(f"  - BMI uniquement: {stats_summary['with_bmi_only']} ({stats_summary['with_bmi_only']/stats_summary['total']*100:.1f}%)")
    print(f"\nMethodes d'aggregation utilisees:")
    for method, count in stats_summary['methods_used'].items():
        pct = count / stats_summary['with_api'] * 100 if stats_summary['with_api'] else 0
        print(f"  - {method}: {count} ({pct:.1f}%)")
    print(f"\nStatistiques cles:")
    for metric, stat in metrics_stats.items():
        if stat['count'] > 0:
            print(f"  {metric}: moy={stat['mean']:.2f}, min={stat['min']:.2f}, max={stat['max']:.2f}, n={stat['count']}")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    success = compile_final_dataset()
    sys.exit(0 if success else 1)
