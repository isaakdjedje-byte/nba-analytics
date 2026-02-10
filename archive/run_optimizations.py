#!/usr/bin/env python3
"""
Lancer les optimisations en parallèle avec Python
"""

import subprocess
import sys
import time
from threading import Thread
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_script(script_name, log_file):
    """Exécute un script et log la sortie."""
    logger.info(f"Démarrage {script_name}...")
    
    with open(log_file, 'w') as f:
        process = subprocess.Popen(
            [sys.executable, script_name],
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        logger.info(f"  PID: {process.pid}")
        process.wait()
        
    logger.info(f"Terminé: {script_name}")


def main():
    logger.info("="*70)
    logger.info("LANCEMENT DES OPTIMISATIONS EN PARALLÈLE")
    logger.info("="*70)
    
    # Créer les threads
    xgb_thread = Thread(
        target=run_script,
        args=("src/optimization/week1/optimize_xgb.py", "results/week1/xgb_log.txt")
    )
    
    rf_thread = Thread(
        target=run_script,
        args=("src/optimization/week1/optimize_rf.py", "results/week1/rf_log.txt")
    )
    
    # Démarrer
    logger.info("\n🚀 Démarrage XGBoost (4-6h)...")
    xgb_thread.start()
    time.sleep(2)  # Petit délai
    
    logger.info("🚀 Démarrage Random Forest (3-4h)...")
    rf_thread.start()
    
    logger.info("\n✅ Les deux optimisations sont lancées!")
    logger.info("📁 Logs dans: results/week1/")
    logger.info("⏳ Temps total estimé: 4-6 heures")
    logger.info("\nPour arrêter: Ctrl+C (2 fois)")
    logger.info("Les logs continueront d'être écrits même si tu fermes ce terminal.\n")
    
    # Attendre
    try:
        xgb_thread.join()
        rf_thread.join()
        
        logger.info("\n" + "="*70)
        logger.info("✅ OPTIMISATIONS TERMINÉES!")
        logger.info("="*70)
        logger.info("\nRésultats:")
        logger.info("  - results/week1/xgb_best_params.json")
        logger.info("  - results/week1/rf_best_params.json")
        
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ Interrompu par l'utilisateur")
        logger.info("Les processus continuent en arrière-plan!")


if __name__ == "__main__":
    main()
