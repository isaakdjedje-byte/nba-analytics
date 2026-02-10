#!/usr/bin/env python3
"""
WEEK 1 LAUNCHER - Orchestrateur
Lance tous les optimisations en parallèle
"""

import subprocess
import sys
import time
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_feature_engineering():
    """Étape 1: Feature Engineering (rapide)."""
    logger.info("="*70)
    logger.info("ÉTAPE 1: FEATURE ENGINEERING V2")
    logger.info("="*70)
    
    result = subprocess.run([
        sys.executable, 
        "src/optimization/week1/feature_engineering_v2.py"
    ], capture_output=True, text=True)
    
    logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(f"Erreur: {result.stderr}")
        return False
    return True


def launch_optimization(script_name, name):
    """Lance une optimisation en arrière-plan."""
    logger.info(f"\nLancement {name}...")
    
    process = subprocess.Popen([
        sys.executable,
        f"src/optimization/week1/{script_name}"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return process


def main():
    """Orchestrateur principal."""
    logger.info("="*70)
    logger.info("WEEK 1 - OPTIMISATION COMPLETE")
    logger.info("="*70)
    logger.info("Ce script va:")
    logger.info("  1. Créer 11 nouvelles features")
    logger.info("  2. Optimiser Random Forest (3-4h)")
    logger.info("  3. Optimiser XGBoost (4-6h)")
    logger.info("  4. Tout sauvegarder dans results/week1/")
    logger.info("="*70)
    
    # Étape 1: Feature Engineering (rapide)
    logger.info("\n🚀 Démarrage dans 5 secondes...")
    time.sleep(5)
    
    success = run_feature_engineering()
    if not success:
        logger.error("Feature engineering échoué!")
        return
    
    # Étape 2 & 3: Optimisations en parallèle
    logger.info("\n" + "="*70)
    logger.info("ÉTAPES 2 & 3: OPTIMISATIONS EN PARALLÈLE")
    logger.info("="*70)
    logger.info("Ces calculs vont prendre 4-6 heures...")
    logger.info("Tu peux fermer ce terminal, les processus continuent en arrière-plan.")
    logger.info("Résultats dans: results/week1/")
    logger.info("="*70 + "\n")
    
    # Lancer les deux optimisations
    rf_process = launch_optimization("optimize_rf.py", "Random Forest Optimization")
    xgb_process = launch_optimization("optimize_xgb.py", "XGBoost Optimization")
    
    logger.info("✅ Processus lancés!")
    logger.info(f"  - Random Forest (PID: {rf_process.pid})")
    logger.info(f"  - XGBoost (PID: {xgb_process.pid})")
    logger.info("\nPour voir la progression:")
    logger.info("  tail -f results/week1/*.log (quand les logs seront créés)")
    logger.info("\nPour arrêter:")
    logger.info("  taskkill /PID <PID> /F (Windows)")
    
    # Attendre la fin (optionnel)
    logger.info("\n⏳ Attente de la fin des calculs...")
    logger.info("(Ctrl+C pour arrêter ce script sans arrêter les calculs)")
    
    try:
        rf_process.wait()
        xgb_process.wait()
        
        logger.info("\n" + "="*70)
        logger.info("✅ TOUS LES CALCULS TERMINÉS!")
        logger.info("="*70)
        logger.info("\nRésultats disponibles dans:")
        logger.info("  - results/week1/rf_best_params.json")
        logger.info("  - results/week1/xgb_best_params.json")
        logger.info("  - models/week1/*_optimized.pkl")
        
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ Script interrompu par l'utilisateur")
        logger.info("Les calculs continuent en arrière-plan!")
        logger.info(f"  RF PID: {rf_process.pid}")
        logger.info(f"  XGB PID: {xgb_process.pid}")


if __name__ == "__main__":
    main()
