#!/usr/bin/env python3
"""
DEPRECATED - NBA Predictions Legacy Wrapper
    Ce script est un wrapper de compatibilite temporaire.
    
    Date de suppression: 2026-03-10
    
    Migration:
    ---------
    Ancien: python run_predictions.py [options]
    Nouveau: python run_predictions_optimized.py [options]
    
    Options supportees:
    --update  ->  --update
    --report  ->  --report
    (default) ->  (default)
"""

import sys
import subprocess
import warnings
from pathlib import Path

def main():
    # Afficher le warning de deprecation
    print("="*70)
    print("ATTENTION: Script obsolete")
    print("="*70)
    print()
    print("Ce script (run_predictions.py) est obsolete et sera supprime")
    print("le 10 mars 2026.")
    print()
    print("Migration recommandee:")
    print("   Ancien: python run_predictions.py [options]")
    print("   Nouveau: python run_predictions_optimized.py [options]")
    print()
    print("Options disponibles dans le nouveau script:")
    print("   --update     Mettre a jour les resultats")
    print("   --report     Generer le rapport de performance")
    print("   --health     Verifier la sante du systeme")
    print("   --drift      Verifier le data drift")
    print("   --train      Reentrainer le modele")
    print()
    print("Redirection vers run_predictions_optimized.py...")
    print("="*70)
    print()
    
    # Redirection vers le script canonique
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # Mapping des arguments legacy vers nouveaux
    # run_predictions.py --update -> run_predictions_optimized.py --update
    # run_predictions.py --report -> run_predictions_optimized.py --report
    # run_predictions.py (default) -> run_predictions_optimized.py (default)
    
    cmd = [sys.executable, "run_predictions_optimized.py"] + args
    
    try:
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\nInterrompu par l'utilisateur.")
        sys.exit(130)
    except Exception as e:
        print(f"\nErreur lors de l'execution: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
