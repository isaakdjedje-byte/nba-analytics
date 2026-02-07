#!/usr/bin/env python3
"""
Script de demarrage rapide du pipeline NBA Data Mesh - GOLD TIERED EDITION.

Usage:
    python run_pipeline.py                          # Mode legacy (1 dataset)
    python run_pipeline.py --stratified             # Tous les datasets (7 produits)
    python run_pipeline.py --target gold            # Tous les GOLD (3 tiers + legacy)
    python run_pipeline.py --target gold_premium    # GOLD Premium (~150 joueurs)
    python run_pipeline.py --target gold_standard   # GOLD Standard (~500 joueurs)
    python run_pipeline.py --target gold_basic      # GOLD Basic (~1000+ joueurs)
    python run_pipeline.py --target bronze          # Dataset BRONZE (analytics)
    python run_pipeline.py --target tier2           # Joueurs modernes partiels
    python run_pipeline.py --legacy                 # Mode compatible ancien

Architecture GOLD Tiered:
    GOLD PREMIUM:  ~150 joueurs  - ML Production (toutes métadonnées)
    GOLD STANDARD: ~500 joueurs  - ML/Analytics (données physiques)
    GOLD BASIC:   ~1000+ joueurs - Exploration (identité seule)

Datasets Data Mesh disponibles:
    raw, bronze, silver, gold_premium, gold_standard, gold_basic, gold, contemporary_tier2
"""

import argparse
import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pipeline import PlayersPipeline


def main():
    parser = argparse.ArgumentParser(
        description='NBA Players Pipeline - Architecture Medallion'
    )
    parser.add_argument(
        '--period', 
        type=str, 
        default='2000-2026',
        help='Periode a recuperer (default: 2000-2026)'
    )
    parser.add_argument(
        '--full', 
        action='store_true',
        help='Recuperer tous les joueurs (sans filtre de periode)'
    )
    parser.add_argument(
        '--bronze-only',
        action='store_true',
        help='Executer uniquement la couche Bronze'
    )
    # NOUVEAUX PARAMETRES - Data Mesh Architecture
    parser.add_argument(
        '--stratified',
        action='store_true',
        help='Activer le mode Data Mesh (5 datasets: raw, bronze, silver, gold, tier2)'
    )
    parser.add_argument(
        '--target',
        choices=[
            'raw', 'bronze', 'silver', 
            'gold', 'gold_premium', 'gold_standard', 'gold_basic',
            'contemporary_tier2'
        ],
        help='Dataset cible Data Mesh (gold_*: ML training par tier, tier2: modernes partiels)'
    )
    parser.add_argument(
        '--legacy',
        action='store_true',
        help='Mode legacy mono-dataset (compatible ancien comportement)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("NBA ANALYTICS PLATFORM")
    print("Architecture Medallion - Bronze -> Silver -> Gold")
    print("=" * 70)
    print()
    
    # Determiner le mode
    use_stratified = args.stratified or (args.target is not None)
    if args.legacy:
        use_stratified = False
    
    # Determiner le filtre de periode
    period_filter = not args.full
    
    if args.full:
        print("Mode: TOUS les joueurs (pas de filtre)")
        print("ATTENTION: Peut prendre 2-3 heures avec les appels API")
    else:
        print(f"Mode: Joueurs 2000-2026 uniquement")
        print("Optimise pour ML (recommande)")
    
    if use_stratified:
        print(f"\nMode Stratifie: ACTIVE")
        print("Architecture: GOLD Tiered (Premium + Standard + Basic)")
        if args.target:
            print(f"Target: {args.target}")
            if 'gold' in args.target:
                print("Niveau GOLD selectionne pour ML")
        else:
            print("Target: all datasets (7 produits)")
    else:
        print("\nMode: Legacy (mono-dataset)")
    
    print()
    
    # Initialiser le pipeline avec feature flag
    pipeline = PlayersPipeline(use_stratification=use_stratified)
    
    if args.bronze_only:
        print("Execution: BRONZE uniquement")
        success = pipeline.run_bronze_layer(period_filter)
    else:
        target_str = f" (target={args.target})" if args.target else ""
        print(f"Execution: Pipeline complet (Bronze -> Silver -> Gold){target_str}")
        success = pipeline.run_full_pipeline(period_filter, target=args.target)
    
    print()
    if success:
        print("[SUCCES] Pipeline termine avec succes!")
        return 0
    else:
        print("[ERREUR] Pipeline echoue!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
