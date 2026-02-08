#!/usr/bin/env python3
"""
NBA-22 Optimization Launcher
Lance l'entraînement optimisé et vérifie le système
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Exécute une commande et affiche le résultat."""
    print(f"\n{'='*70}")
    print(f"{description}")
    print(f"{'='*70}")
    print(f"Commande: {cmd}")
    print()
    
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    return result.returncode == 0

def main():
    print("="*70)
    print("NBA-22 OPTIMIZATION LAUNCHER")
    print("="*70)
    
    steps = [
        ("python src/ml/pipeline/train_optimized.py", 
         "1/5 - Entraînement du modèle optimisé (Feature Selection + Calibration)"),
        
        ("python run_predictions_optimized.py --health", 
         "2/5 - Vérification de la santé du système"),
        
        ("python run_predictions_optimized.py --drift", 
         "3/5 - Vérification du data drift"),
        
        ("python run_predictions_optimized.py", 
         "4/5 - Test des prédictions optimisées"),
        
        ("python run_predictions_optimized.py --report", 
         "5/5 - Génération du rapport de performance"),
    ]
    
    results = []
    for cmd, desc in steps:
        success = run_command(cmd, desc)
        results.append((desc, success))
        
        if not success:
            print(f"\n⚠️  Étape échouée: {desc}")
            response = input("Continuer quand même? (o/n): ").lower()
            if response != 'o':
                break
    
    # Résumé
    print("\n" + "="*70)
    print("RÉSUMÉ")
    print("="*70)
    
    for desc, success in results:
        status = "✅ OK" if success else "❌ ÉCHEC"
        print(f"{status} - {desc.split(' - ')[1]}")
    
    print("\n" + "="*70)
    print("OPTIMISATIONS ACTIVES:")
    print("="*70)
    print("✅ Feature Selection: 80 → 35 features")
    print("✅ Calibration des probabilités (Isotonic Regression)")
    print("✅ Monitoring Data Drift")
    print("✅ Tracking ROI avancé")
    print("✅ Système de santé automatisé")
    print("\nCommandes disponibles:")
    print("  python run_predictions_optimized.py         # Prédictions")
    print("  python run_predictions_optimized.py --update # Mise à jour résultats")
    print("  python run_predictions_optimized.py --report # Rapport")
    print("  python run_predictions_optimized.py --train  # Réentraîner")
    print("  python run_predictions_optimized.py --health # Check santé")
    print("  python run_predictions_optimized.py --drift  # Check drift")
    print("="*70)

if __name__ == '__main__':
    main()
