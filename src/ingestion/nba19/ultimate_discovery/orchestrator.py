"""
NBA-19 Ultimate Discovery - Orchestrateur

Orchestre Phase 1 (segmentation) et Phase 2 (discovery test sur 100 joueurs)

Usage:
    python orchestrator.py
    
Équivalent à:
    python phase1_pre_validation.py
    python phase2_discovery_engine.py --segment A --limit 100
"""
import os
import sys
import subprocess
from datetime import datetime

# Ajouter le chemin
sys.path.insert(0, os.path.dirname(__file__))


def run_phase1():
    """Exécuter Phase 1: Pré-validation"""
    print("\n" + "=" * 70)
    print("🚀 LANCEMENT PHASE 1: PRÉ-VALIDATION ET SEGMENTATION")
    print("=" * 70 + "\n")
    
    try:
        from phase1_pre_validation import main as phase1_main
        phase1_main()
        return True
    except Exception as e:
        print(f"\n❌ Erreur Phase 1: {e}")
        return False


def run_phase2():
    """Exécuter Phase 2: Discovery (100 joueurs)"""
    print("\n" + "=" * 70)
    print("🚀 LANCEMENT PHASE 2: DISCOVERY TEST (100 joueurs)")
    print("=" * 70 + "\n")
    
    try:
        from phase2_discovery_engine import main as phase2_main
        import argparse
        
        # Simuler les arguments
        sys.argv = ['phase2_discovery_engine.py', '--segment', 'A', '--limit', '100']
        phase2_main()
        return True
    except Exception as e:
        print(f"\n❌ Erreur Phase 2: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_final_summary():
    """Afficher le résumé final"""
    print("\n" + "=" * 70)
    print("✨ NBA-19 ULTIMATE DISCOVERY - TEST COMPLET TERMINÉ")
    print("=" * 70)
    
    print("\n📁 Fichiers générés:")
    
    # Vérifier les segments
    segments_dir = "logs/nba19_discovery/segments"
    if os.path.exists(segments_dir):
        files = os.listdir(segments_dir)
        print(f"\n   Segments ({len(files)} fichiers):")
        for f in sorted(files):
            print(f"   - {f}")
    
    # Vérifier les résultats
    results_dir = "logs/nba19_discovery/results"
    if os.path.exists(results_dir):
        files = os.listdir(results_dir)
        print(f"\n   Résultats ({len(files)} fichiers):")
        for f in sorted(files):
            print(f"   - {f}")
    
    print("\n📊 Prochaines étapes possibles:")
    print("   1. Analyser les résultats du test (100 joueurs)")
    print("   2. Si OK → lancer sur tous les joueurs:")
    print("      python phase2_discovery_engine.py --segment A --limit 0")
    print("   3. Ou traiter les segments B et C")
    print("      python phase2_discovery_engine.py --segment B --limit 100")
    
    print("\n" + "=" * 70)


def main():
    """Orchestrateur principal"""
    print("=" * 70)
    print("🏀 NBA-19 ULTIMATE DISCOVERY SYSTEM - VERSION TEST")
    print("=" * 70)
    print(f"\nDémarré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Mode: Test sur 100 joueurs (Segment A - GOLD)\n")
    
    # Phase 1
    if not run_phase1():
        print("\n⛔ Arrêt après échec Phase 1")
        return
    
    # Phase 2
    if not run_phase2():
        print("\n⛔ Arrêt après échec Phase 2")
        return
    
    # Résumé final
    print_final_summary()


if __name__ == "__main__":
    main()
