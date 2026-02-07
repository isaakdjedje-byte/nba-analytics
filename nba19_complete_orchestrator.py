#!/usr/bin/env python3
"""
NBA-19 COMPLETE ORCHESTRATOR

Lance toutes les phases de NBA-19 en mode complet:
- Phase 1: Pre-validation (deja faite)
- Phase 2: Discovery complet (5 103 joueurs, ~3h)
- Phase 3: Validation multi-source (~15 min)
- Phase 4: Enrichissement (~20 min)
- Phase 5: Consolidation finale (~10 min)

TOTAL: ~3h45 sans intervention

Usage:
    python nba19_complete_orchestrator.py
    
Pour reprise apres interruption:
    python nba19_complete_orchestrator.py --resume
"""
import os
import sys
import time
import argparse
from datetime import datetime

# Ajouter le chemin
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 
                'src/ingestion/nba19/ultimate_discovery'))


def print_header(title):
    """Afficher header"""
    print("\n" + "="*70)
    print(f">>> {title}")
    print("="*70 + "\n")


def run_phase(phase_num, phase_name, module_name, est_minutes):
    """Executer une phase"""
    print_header(f"PHASE {phase_num}: {phase_name.upper()}")
    print(f"Estimation: ~{est_minutes} minutes\n")
    
    start_time = time.time()
    
    try:
        # Importer et executer
        module = __import__(module_name)
        module.main()
        
        elapsed = time.time() - start_time
        print(f"\n[OK] Phase {phase_num} terminee en {int(elapsed//60)}m {int(elapsed%60)}s")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Phase {phase_num} echouee: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_phase1_done():
    """Verifier que Phase 1 est faite"""
    segments_dir = "logs/nba19_discovery/segments"
    required = ['segment_A_gold.json', 'segment_B_silver.json', 'segment_C_bronze.json']
    
    if not os.path.exists(segments_dir):
        return False
    
    existing = os.listdir(segments_dir)
    return all(f in existing for f in required)


def print_summary():
    """Afficher resume final"""
    print("\n" + "="*70)
    print(">>> NBA-19 COMPLETE - RESUME FINAL")
    print("="*70)
    
    output_dir = "data/gold/nba19"
    
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        print(f"\nFichiers crees dans {output_dir}:")
        for f in sorted(files):
            size = os.path.getsize(os.path.join(output_dir, f))
            size_mb = size / (1024*1024)
            print(f"  - {f} ({size_mb:.1f} MB)")
    
    print("\n[TODO] Prochaines etapes:")
    print("  1. Verifier data/gold/nba19/quality_report.json")
    print("  2. Review manuel: data/gold/nba19/manual_review_queue.json")
    print("  3. Integrer avec NBA-20 (feature engineering)")
    
    print("\n" + "="*70)


def main():
    """Orchestrateur principal"""
    parser = argparse.ArgumentParser(description='NBA-19 Complete Orchestrator')
    parser.add_argument('--resume', action='store_true', 
                       help='Reprendre apres interruption')
    args = parser.parse_args()
    
    print("="*70)
    print(">>> NBA-19 COMPLETE ORCHESTRATOR")
    print("="*70)
    print(f"\nDemarre: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Mode: COMPLET (5 103 joueurs)")
    print("Temps estime: ~3h45")
    print("\nPhases:")
    print("  1. Pre-validation: DEJA FAITE")
    print("  2. Discovery: A → B → C (3h)")
    print("  3. Validation (15 min)")
    print("  4. Enrichissement (20 min)")
    print("  5. Consolidation (10 min)")
    print("\n" + "="*70)
    
    # Verifier Phase 1
    if not check_phase1_done():
        print("\n[ERROR] Phase 1 non detectee!")
        print("Executer d'abord:")
        print("  python src/ingestion/nba19/ultimate_discovery/phase1_pre_validation.py")
        return
    
    print("\n[OK] Phase 1 verifiee (5 103 joueurs segmentes)")
    
    # Phases 2-5
    phases = [
        (2, "Discovery complet", "phase2_discovery_all", 180),
        (3, "Validation multi-source", "phase3_validation", 15),
        (4, "Enrichissement", "phase4_enrichment", 20),
        (5, "Consolidation finale", "phase5_consolidation", 10)
    ]
    
    start_total = time.time()
    
    for phase_num, phase_name, module, est_min in phases:
        if not run_phase(phase_num, phase_name, module, est_min):
            print(f"\n[STOP] Arret apres echec Phase {phase_num}")
            return
    
    total_time = time.time() - start_total
    
    print_summary()
    
    print(f"\n[COMPLETE] Toutes les phases terminees!")
    print(f"Temps total: {int(total_time//3600)}h {int((total_time%3600)//60)}m")
    print(f"Termine: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
