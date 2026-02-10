#!/usr/bin/env python3
"""
Script d'utilisation des datasets GOLD Tiered.

Usage:
    python use_gold_tiered.py --list              # Lister tous les datasets
    python use_gold_tiered.py --tier standard     # Utiliser GOLD Standard
    python use_gold_tiered.py --tier basic        # Utiliser GOLD Basic
    python use_gold_tiered.py --compare           # Comparer les 3 tiers
    python use_gold_tiered.py --export standard   # Exporter en CSV
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Chemins des datasets
DATASETS = {
    'gold_elite': 'data/silver/players_gold_premium_elite/players.json',
    'gold_standard': 'data/silver/players_gold_standard/players.json',
    'gold_basic': 'data/silver/players_gold_basic/players.json',
    'gold_premium': 'data/silver/players_gold_premium/players.json',
    'silver': 'data/silver/players_silver/players.json',
    'bronze': 'data/silver/players_bronze/players.json'
}


def load_players(dataset_name: str) -> List[Dict[str, Any]]:
    """Charge les joueurs d'un dataset."""
    path = DATASETS.get(dataset_name)
    if not path:
        print(f"ERREUR: Dataset '{dataset_name}' inconnu")
        print(f"Datasets disponibles: {', '.join(DATASETS.keys())}")
        return []
    
    if not Path(path).exists():
        print(f"ERREUR: Fichier non trouve: {path}")
        print("Executez d'abord: python run_pipeline.py --stratified")
        return []
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('data', data.get('players', []))


def list_datasets():
    """Affiche tous les datasets disponibles."""
    print("="*70)
    print("DATASETS GOLD TIERED DISPONIBLES")
    print("="*70)
    print()
    
    for name, path in DATASETS.items():
        if Path(path).exists():
            players = load_players(name)
            size_kb = Path(path).stat().st_size / 1024
            print(f"{name:20} - {len(players):5} joueurs - {size_kb:6.1f} KB")
        else:
            print(f"{name:20} - NON DISPONIBLE")
    
    print()
    print("Recommandations d'utilisation:")
    print("  - gold_standard: ML/Analytics (donnees physiques completes)")
    print("  - gold_basic:    Exploration (identite seule, 4,468 joueurs)")
    print("  - gold_premium:  ML Production (metadonnees completes - actuellement vide)")


def analyze_tier(tier_name: str):
    """Analyse detaillee d'un tier."""
    players = load_players(f'gold_{tier_name}')
    
    if not players:
        print(f"Aucun joueur dans GOLD {tier_name.upper()}")
        return
    
    print(f"\n{'='*70}")
    print(f"ANALYSE GOLD {tier_name.upper()}")
    print(f"{'='*70}")
    print(f"Nombre de joueurs: {len(players)}")
    
    # Statistiques completude
    total_cells = 0
    filled_cells = 0
    field_counts = {}
    
    for player in players:
        for key, value in player.items():
            total_cells += 1
            if value is not None and value != '':
                filled_cells += 1
                field_counts[key] = field_counts.get(key, 0) + 1
    
    completeness = (filled_cells / total_cells * 100) if total_cells > 0 else 0
    print(f"Completude moyenne: {completeness:.1f}%")
    
    # Champs disponibles
    print(f"\nChamps disponibles:")
    for field, count in sorted(field_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(players)) * 100
        print(f"  {field:20} - {count:5}/{len(players)} ({pct:5.1f}%)")
    
    # Exemples
    print(f"\nExemples de joueurs:")
    for i, player in enumerate(players[:5]):
        print(f"  {i+1}. {player.get('full_name', 'N/A')}")
        print(f"     ID: {player.get('id')}, Pos: {player.get('position')}, "
              f"H: {player.get('height_cm')}cm, W: {player.get('weight_kg')}kg")


def compare_tiers():
    """Compare tous les tiers GOLD."""
    print(f"\n{'='*70}")
    print("COMPARAISON GOLD TIERED - PHASE 3")
    print(f"{'='*70}")
    
    tiers = {
        'Elite': load_players('gold_elite'),
        'Premium': load_players('gold_premium'),
        'Standard': load_players('gold_standard'),
        'Basic': load_players('gold_basic')
    }
    
    print(f"\n{'Tier':<12} {'Joueurs':>10} {'% du total':>12} {'Qualite':>12} {'Use case':<25}")
    print("-"*80)
    
    total = sum(len(p) for p in tiers.values())
    for tier_name, players in tiers.items():
        pct = (len(players) / total * 100) if total > 0 else 0
        
        # Calculer qualité moyenne si disponible
        if players and 'position_confidence' in players[0]:
            avg_conf = sum(p.get('position_confidence', 0) for p in players) / len(players)
            quality_str = f"{avg_conf:.1%}"
        else:
            quality_str = "100%" if tier_name == 'Standard' else "N/A"
        
        use_case = {
            'Elite': 'ML Production haute qualite',
            'Premium': 'ML Production general',
            'Standard': 'Validation & benchmark',
            'Basic': 'Exploration & recherche'
        }.get(tier_name, '')
        
        print(f"{tier_name:<12} {len(players):>10} {pct:>11.1f}% {quality_str:>12} {use_case:<25}")
    
    print("-"*80)
    print(f"{'TOTAL':<12} {total:>10} {100.0:>11.1f}%")
    
    # Analyse par position (pour Standard)
    if tiers['Standard']:
        print(f"\nRepartition par position (GOLD Standard):")
        positions = {}
        for p in tiers['Standard']:
            pos = p.get('position', 'Unknown')
            positions[pos] = positions.get(pos, 0) + 1
        
        for pos, count in sorted(positions.items(), key=lambda x: -x[1]):
            pct = (count / len(tiers['Standard'])) * 100
            print(f"  {pos or 'N/A':5} - {count:4} joueurs ({pct:5.1f}%)")


def export_to_csv(tier_name: str, output_file: Optional[str] = None):
    """Exporte un tier en CSV."""
    players = load_players(f'gold_{tier_name}')
    
    if not players:
        print(f"Aucun joueur a exporter dans GOLD {tier_name.upper()}")
        return
    
    if not output_file:
        output_file = f'gold_{tier_name}_export.csv'
    
    # Recuperer tous les champs
    all_fields = set()
    for player in players:
        all_fields.update(player.keys())
    
    all_fields = sorted(all_fields)
    
    # Ecrire CSV
    import csv
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=all_fields)
        writer.writeheader()
        writer.writerows(players)
    
    print(f"Exporte {len(players)} joueurs vers: {output_file}")
    print(f"Champs exportes: {', '.join(all_fields)}")


def demo_ml_usage():
    """Demo d'utilisation ML avec GOLD Standard."""
    players = load_players('gold_standard')
    
    if not players:
        print("GOLD Standard vide - impossible de faire la demo")
        return
    
    print(f"\n{'='*70}")
    print("DEMO: Utilisation ML avec GOLD Standard")
    print(f"{'='*70}")
    print(f"Dataset: {len(players)} joueurs avec donnees physiques completes")
    
    # Features disponibles
    print("\nFeatures disponibles pour ML:")
    features = ['height_cm', 'weight_kg', 'position', 'is_active']
    for feature in features:
        present = sum(1 for p in players if p.get(feature) is not None)
        pct = (present / len(players)) * 100
        print(f"  - {feature:15} : {present:4}/{len(players)} ({pct:5.1f}%)")
    
    # Calcul BMI
    print("\nExemple: Calcul BMI (Body Mass Index)")
    bmis = []
    for p in players[:10]:
        h = p.get('height_cm', 0) / 100  # m
        w = p.get('weight_kg', 0)
        if h > 0 and w > 0:
            bmi = w / (h ** 2)
            bmis.append(bmi)
            print(f"  {p.get('full_name', 'N/A'):25} - BMI: {bmi:.1f}")
    
    if bmis:
        avg_bmi = sum(bmis) / len(bmis)
        print(f"\nBMI moyen (echantillon): {avg_bmi:.1f}")
    
    print("\nProchains pas possibles:")
    print("  1. Clustering par taille/poids")
    print("  2. Prediction position par BMI")
    print("  3. Analyse correlation taille/performance")


def main():
    parser = argparse.ArgumentParser(
        description='Utilisation des datasets GOLD Tiered',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Lister les datasets
  python use_gold_tiered.py --list
  
  # Analyser un tier specifique
  python use_gold_tiered.py --tier standard
  
  # Comparer tous les tiers
  python use_gold_tiered.py --compare
  
  # Exporter en CSV
  python use_gold_tiered.py --export standard --output players.csv
  
  # Demo ML
  python use_gold_tiered.py --demo
        """
    )
    
    parser.add_argument('--list', action='store_true',
                       help='Lister tous les datasets disponibles')
    parser.add_argument('--tier', choices=['standard', 'basic', 'premium'],
                       help='Analyser un tier specifique')
    parser.add_argument('--compare', action='store_true',
                       help='Comparer les 3 tiers')
    parser.add_argument('--export', choices=['standard', 'basic', 'premium'],
                       help='Exporter un tier en CSV')
    parser.add_argument('--output', type=str,
                       help='Fichier de sortie pour export')
    parser.add_argument('--demo', action='store_true',
                       help='Demo utilisation ML')
    
    args = parser.parse_args()
    
    # Action par defaut si aucun argument
    if not any([args.list, args.tier, args.compare, args.export, args.demo]):
        args.compare = True
    
    if args.list:
        list_datasets()
    
    if args.tier:
        analyze_tier(args.tier)
    
    if args.compare:
        compare_tiers()
    
    if args.export:
        export_to_csv(args.export, args.output)
    
    if args.demo:
        demo_ml_usage()


if __name__ == "__main__":
    main()
