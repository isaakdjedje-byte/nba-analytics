"""
NBA-19: Orchestrateur principal

Lance le fetching des rosters historiques puis l'auto-discovery
des joueurs manquants.

Usage:
    python src/ingestion/nba19/orchestrator.py [--skip-discovery]
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.ingestion.nba19.fetch_historical_rosters import HistoricalRosterFetcher
from src.ingestion.nba19.auto_discovery import PlayerTeamDiscovery


def main():
    """Orchestrateur principal"""
    parser = argparse.ArgumentParser(description='NBA-19 Data Ingestion')
    parser.add_argument(
        '--skip-discovery',
        action='store_true',
        help='Sauter l\'auto-discovery (rosters seulement)'
    )
    parser.add_argument(
        '--discovery-batch',
        type=int,
        default=None,
        help='Limiter le nombre de joueurs pour l\'auto-discovery'
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("🏀 NBA-19: ORCHESTRATEUR D'INGESTION")
    print("=" * 70)
    
    # Étape 1: Fetching des rosters historiques
    print("\n📋 ÉTAPE 1: Fetching des rosters historiques")
    print("-" * 70)
    
    fetcher = HistoricalRosterFetcher()
    fetcher.run()
    
    # Étape 2: Auto-discovery (si demandé)
    if not args.skip_discovery:
        print("\n📋 ÉTAPE 2: Auto-discovery des joueurs historiques")
        print("-" * 70)
        
        discovery = PlayerTeamDiscovery()
        discovery.discover_missing_players(batch_size=args.discovery_batch)
        discovery.save_discovered_mappings()
    else:
        print("\n⏭️  Étape 2 sautée (--skip-discovery)")
    
    print("\n" + "=" * 70)
    print("✨ INGESTION NBA-19 TERMINÉE")
    print("=" * 70)
    print("\nProchaine étape:")
    print("   Phase 2: Architecture de traitement")
    print("   Commande: python src/processing/nba19/orchestrator.py")


if __name__ == "__main__":
    main()
