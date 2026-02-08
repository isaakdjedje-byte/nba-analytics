#!/usr/bin/env python3
"""
NBA-17: Nettoyage des données joueurs - Point d'entrée officiel

Conformément aux critères d'acceptation NBA-17, ce fichier est le point 
d'entrée standard pour le nettoyage des données joueurs.

Ce fichier est un wrapper léger qui délègue à PlayersDataCleaner.
Il permet d'avoir un point d'entrée standard 'clean_data.py' sans 
duplication de code, conforme aux best practices.

Usage:
    python src/processing/clean_data.py
    python src/processing/clean_data.py --full
    python src/processing/clean_data.py --period 2000-2026

Dépendances:
    - src/processing/clean_players.py (classe PlayersDataCleaner)
    - src/processing/silver/cleaning_functions.py
    - src/utils/transformations.py
    - configs/cleaning_rules.yaml

Sortie:
    - data/silver/players_cleaned/ (Delta Lake partitionné)
    - data/silver/players_cleaned_stats.json (rapport qualité)
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.processing.clean_players import PlayersDataCleaner


def main():
    """
    Point d'entrée principal pour le nettoyage des données NBA.
    
    Returns:
        int: Code de sortie (0 = succès, 1 = erreur)
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='NBA-17: Nettoyage des données joueurs NBA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
    %(prog)s                     # Nettoyage standard (2000-2026)
    %(prog)s --full              # Tous les joueurs sans filtre
    %(prog)s --period 2010-2024  # Période personnalisée

Notes:
    - Les données sont sauvegardées dans data/silver/players_cleaned/
    - Un rapport JSON est généré dans data/silver/players_cleaned_stats.json
    - Le processus utilise Delta Lake pour le stockage partitionné
        """
    )
    
    parser.add_argument(
        '--period', 
        type=str, 
        default='2000-2026',
        help='Période à traiter (format: YYYY-YYYY, défaut: 2000-2026)'
    )
    
    parser.add_argument(
        '--full', 
        action='store_true',
        help='Traiter tous les joueurs sans filtre de période (1947-2026)'
    )
    
    parser.add_argument(
        '--skip-api',
        action='store_true',
        help='Ignorer les appels API (utilise uniquement les données locales)'
    )
    
    args = parser.parse_args()
    
    # Affichage bannière
    print("=" * 70)
    print("NBA-17: Nettoyage des données joueurs")
    print("=" * 70)
    print(f"Input:  data/raw/all_players_historical.json")
    print(f"Output: data/silver/players_cleaned/")
    
    if args.full:
        print(f"Periode: Tous les joueurs (1947-2026)")
        period_filter = False
    else:
        print(f"Periode: {args.period}")
        period_filter = True
    
    if args.skip_api:
        print(f"Mode: Sans API (donnees locales uniquement)")
    
    print("=" * 70)
    
    try:
        # Exécuter le nettoyage
        cleaner = PlayersDataCleaner()
        success = cleaner.run(period_filter=period_filter)
        
        if success:
            print("\n" + "=" * 70)
            print("Nettoyage termine avec succes!")
            print("=" * 70)
            print(f"Donnees sauvegardees dans: data/silver/players_cleaned/")
            print(f"Rapport genere: data/silver/players_cleaned_stats.json")
            print("\nPour verifier les resultats:")
            print("  ls -la data/silver/players_cleaned/")
            print("  cat data/silver/players_cleaned_stats.json")
            return 0
        else:
            print("\n" + "=" * 70)
            print("Erreur pendant le nettoyage")
            print("=" * 70)
            print("\nVerifiez les logs pour plus de details.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\nInterruption par l'utilisateur")
        return 130
    except Exception as e:
        print(f"\n\nErreur fatale: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
