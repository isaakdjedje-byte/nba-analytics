#!/usr/bin/env python3
"""
NBA Predictions - Script Principal
Pipeline complet: Predictions + Tracking

Usage:
    python run_predictions.py              # Faire des predictions
    python run_predictions.py --update     # Mettre a jour les resultats
    python run_predictions.py --report     # Generer rapport de performance
"""

import argparse
import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'ml' / 'pipeline'))

from daily_pipeline import DailyPredictionPipeline
from tracking_roi import ROITracker
from nba_live_api import get_today_games
import pandas as pd
from datetime import datetime


def run_predictions():
    """Execute les predictions du jour."""
    print("="*70)
    print("NBA PREDICTIONS - PIPELINE QUOTIDIEN")
    print("="*70)
    print()
    
    # Pipeline de predictions
    pipeline = DailyPredictionPipeline()
    predictions = pipeline.run_daily_predictions()
    
    # Tracking
    tracker = ROITracker()
    for pred in predictions:
        if 'error' not in pred:
            tracker.add_prediction(pred)
    tracker.save()
    
    print("\n" + "="*70)
    print("PREDICTIONS TERMINEES")
    print("="*70)
    print(f"\nFichiers sauvegardes dans: predictions/")
    print("  - predictions_YYYYMMDD_HHMMSS.csv")
    print("  - predictions_YYYYMMDD_HHMMSS.json")
    print("  - latest_predictions.csv")
    print("  - tracking_history.csv")
    
    return predictions


def update_results():
    """Interface pour mettre a jour les resultats."""
    print("="*70)
    print("MISE A JOUR DES RESULTATS")
    print("="*70)
    print()
    
    tracker = ROITracker()
    
    # Charger les predictions recentes
    latest_file = Path('predictions/latest_predictions.csv')
    if not latest_file.exists():
        print("[ERREUR] Aucune prediction trouvee. Lancez d'abord: python run_predictions.py")
        return
        
    predictions = pd.read_csv(latest_file)
    
    print(f"Predictions a mettre a jour: {len(predictions)}")
    print()
    
    # Pour chaque prediction sans resultat
    for idx, row in predictions.iterrows():
        home = row['home_team']
        away = row['away_team']
        date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n{idx+1}. {home} vs {away}")
        print(f"   Prediction: {row['prediction']} (confiance: {row['confidence']:.1%})")
        
        # Demander le resultat
        result = input("   Resultat (h=Home Win, a=Away Win, s=Skip): ").lower().strip()
        
        if result == 'h':
            tracker.update_result(home, away, date, 'HOME_WIN')
        elif result == 'a':
            tracker.update_result(home, away, date, 'AWAY_WIN')
        elif result == 's':
            print("   [SKIP]")
        else:
            print("   [SKIP - Entree invalide]")
            
    tracker.save()
    
    print("\n" + "="*70)
    print("MISE A JOUR TERMINEE")
    print("="*70)
    

def generate_report():
    """Genere le rapport de performance."""
    tracker = ROITracker()
    tracker.export_results()


def main():
    parser = argparse.ArgumentParser(description='NBA Predictions Pipeline')
    parser.add_argument('--update', action='store_true', 
                       help='Mettre a jour les resultats des matchs')
    parser.add_argument('--report', action='store_true',
                       help='Generer le rapport de performance')
    parser.add_argument('--demo', action='store_true',
                       help='Mode demonstration avec exemples fictifs')
    
    args = parser.parse_args()
    
    if args.update:
        update_results()
    elif args.report:
        generate_report()
    elif args.demo:
        print("Mode demonstration - Utilisation de matchs fictifs")
        run_predictions()
    else:
        # Mode par defaut: faire les predictions
        run_predictions()


if __name__ == '__main__':
    main()
