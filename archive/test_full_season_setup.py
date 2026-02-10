#!/usr/bin/env python3
"""
Script de test pour le pipeline Full Season 2025-26
Teste la nouvelle architecture avec modèle optimisé et calendrier futur

Usage:
    python test_full_season_setup.py
"""

import sys
from pathlib import Path

# Ajouter paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nba.config import SeasonConfig

def test_season_config():
    """Teste la configuration saison"""
    print("\n" + "="*70)
    print("TEST 1: SeasonConfig")
    print("="*70)
    
    print(f"Current season: {SeasonConfig.CURRENT_SEASON}")
    print(f"Year start: {SeasonConfig.get_season_year_start()}")
    print(f"Year end: {SeasonConfig.get_season_year_end()}")
    print(f"File suffix: {SeasonConfig.get_season_file_suffix()}")
    print("OK: SeasonConfig")

def test_fetch_future_schedule():
    """Teste la récupération du calendrier futur"""
    print("\n" + "="*70)
    print("TEST 2: fetch_future_schedule")
    print("="*70)
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'src' / 'ingestion'))
        from fetch_schedules import fetch_future_schedule
        
        print("Récupération du calendrier 2025-26...")
        games = fetch_future_schedule("2025-26")
        
        if games:
            print(f"OK: {len(games)} matchs recuperes")
            
            # Stats
            played = sum(1 for g in games if g.get('is_played'))
            future = len(games) - played
            print(f"  - Joués: {played}")
            print(f"  - À venir: {future}")
            
            # Exemple
            if future > 0:
                future_games = [g for g in games if not g.get('is_played')]
                print(f"\nProchain match:")
                print(f"  {future_games[0]['game_date']}: "
                      f"{future_games[0]['home_team']} vs "
                      f"{future_games[0]['away_team']}")
            
            return True
        else:
            print("ERROR: Aucun match récupéré")
            return False
            
    except Exception as e:
        print(f"ERROR: Erreur: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_full_season_pipeline():
    """Teste le pipeline complet"""
    print("\n" + "="*70)
    print("TEST 3: FullSeasonPipeline")
    print("="*70)
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'src' / 'ml' / 'pipeline'))
        from full_season_pipeline import FullSeasonPipeline
        
        print("Initialisation du pipeline...")
        pipeline = FullSeasonPipeline()
        
        print("OK: Pipeline initialise")
        print(f"  Saison: {pipeline.season}")
        print(f"  Modele: {pipeline.model_path}")
        
        # Test de génération
        print("\nGénération des prédictions (mode test - 5 premiers matchs)...")
        
        # On ne génère que pour 5 matchs pour le test
        import json
        from datetime import datetime
        
        # Charger le calendrier
        schedule = pipeline.fetch_season_schedule()
        
        if schedule:
            future_games = [g for g in schedule if not g.get('is_played')][:5]
            print(f"\n{len(future_games)} matchs à venir trouvés")
            
            if future_games:
                pipeline.load_resources()
                
                for game in future_games:
                    home = game['home_team']
                    away = game['away_team']
                    print(f"\n{game['game_date']}: {home} vs {away}")
                    
                    pred = pipeline.predict_match(home, away)
                    if 'error' not in pred:
                        print(f"  Prédiction: {pred['prediction']}")
                        print(f"  Confiance: {pred['confidence']:.2%}")
                        print(f"  Proba home: {pred['proba_home_win']:.2%}")
                    else:
                        print(f"  Erreur: {pred['error']}")
                
                return True
            else:
                print("Aucun match futur trouvé (saison terminée?)")
                return True
        else:
            print("ERROR: Impossible de récupérer le calendrier")
            return False
            
    except Exception as e:
        print(f"ERROR: Erreur: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    print("\n" + "="*70)
    print("TEST COMPLET - FULL SEASON PIPELINE 2025-26")
    print("="*70)
    
    results = []
    
    # Test 1
    try:
        test_season_config()
        results.append(("SeasonConfig", True))
    except Exception as e:
        print(f"ERROR: Test 1 échoué: {e}")
        results.append(("SeasonConfig", False))
    
    # Test 2
    try:
        success = test_fetch_future_schedule()
        results.append(("fetch_future_schedule", success))
    except Exception as e:
        print(f"ERROR: Test 2 échoué: {e}")
        results.append(("fetch_future_schedule", False))
    
    # Test 3
    try:
        success = test_full_season_pipeline()
        results.append(("FullSeasonPipeline", success))
    except Exception as e:
        print(f"ERROR: Test 3 échoué: {e}")
        results.append(("FullSeasonPipeline", False))
    
    # Résumé
    print("\n" + "="*70)
    print("RÉSUMÉ DES TESTS")
    print("="*70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, success in results:
        status = "OK: PASS" if success else "ERROR: FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests réussis")
    print("="*70)
    
    if passed == total:
        print("\nOK: Tous les tests ont réussi!")
        print("\nProchaine étape: Exécuter le setup complet")
        print("  python scripts/update_season_2025_26.py")
    else:
        print("\nATTENTION: Certains tests ont echoue")

if __name__ == "__main__":
    main()
