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


def check_phase2_done():
    """Verifier que Phase 2 (discovery) est faite"""
    results_dir = "logs/nba19_discovery/results"
    if not os.path.exists(results_dir):
        return False
    
    # Chercher fichier all_mappings_*.json recent
    files = [f for f in os.listdir(results_dir) if f.startswith('all_mappings_')]
    return len(files) > 0


def check_phase3_done():
    """Verifier que Phase 3 (validation) est faite"""
    results_dir = "logs/nba19_discovery/results"
    if not os.path.exists(results_dir):
        return False
    
    # Chercher fichier validated_mappings_*.json recent
    files = [f for f in os.listdir(results_dir) if f.startswith('validated_mappings_')]
    return len(files) > 0


def check_phase4_done():
    """Verifier que Phase 4 (enrichment) est faite"""
    results_dir = "logs/nba19_discovery/results"
    if not os.path.exists(results_dir):
        return False
    
    # Chercher fichier enriched_careers_*.json ou career_summaries_*.json
    files = [f for f in os.listdir(results_dir) 
             if f.startswith('enriched_careers_') or f.startswith('career_summaries_')]
    return len(files) > 0


def check_phase5_done():
    """Verifier que Phase 5 (consolidation) est faite"""
    output_dir = "data/gold/nba19"
    if not os.path.exists(output_dir):
        return False
    
    # Verifier que player_team_history_complete.json existe
    return os.path.exists(os.path.join(output_dir, "player_team_history_complete.json"))


def get_phase_status():
    """Obtenir le statut de toutes les phases"""
    return {
        1: check_phase1_done(),
        2: check_phase2_done(),
        3: check_phase3_done(),
        4: check_phase4_done(),
        5: check_phase5_done()
    }


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
    """Orchestrateur principal avec detection auto des phases faites"""
    parser = argparse.ArgumentParser(description='NBA-19 Complete Orchestrator')
    parser.add_argument('--resume', action='store_true', 
                       help='Reprendre apres interruption')
    parser.add_argument('--force', action='store_true',
                       help='Forcer la reexecution de toutes les phases')
    args = parser.parse_args()
    
    print("="*70)
    print(">>> NBA-19 COMPLETE ORCHESTRATOR")
    print("="*70)
    print(f"\nDemarre: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Mode: COMPLET (5 103 joueurs)")
    
    # Verifier statut des phases
    phase_status = get_phase_status()
    
    print("\n" + "="*70)
    print(">>> STATUT DES PHASES")
    print("="*70)
    
    for phase_num in range(1, 6):
        status = "[OK] FAITE" if phase_status[phase_num] else "[TODO] A FAIRE"
        phase_names = {
            1: "Pre-validation",
            2: "Discovery complet",
            3: "Validation multi-source",
            4: "Enrichissement",
            5: "Consolidation finale"
        }
        print(f"  Phase {phase_num}: {phase_names[phase_num]:30} {status}")
    
    print("="*70)
    
    # Verifier Phase 1
    if not phase_status[1]:
        print("\n[ERROR] Phase 1 non detectee!")
        print("Executer d'abord:")
        print("  python src/ingestion/nba19/ultimate_discovery/phase1_pre_validation.py")
        return
    
    # Phases 2-5 avec detection auto
    phases = [
        (2, "Discovery complet", "phase2_discovery_all", 180),
        (3, "Validation multi-source", "phase3_validation", 15),
        (4, "Enrichissement", "phase4_enrichment", 20),
        (5, "Consolidation finale", "phase5_consolidation", 10)
    ]
    
    start_total = time.time()
    phases_executed = 0
    
    for phase_num, phase_name, module, est_min in phases:
        if phase_status[phase_num] and not args.force:
            print(f"\n[SKIP] Phase {phase_num} deja completee (utiliser --force pour reexecuter)")
            continue
        
        if not run_phase(phase_num, phase_name, module, est_min):
            print(f"\n[STOP] Arret apres echec Phase {phase_num}")
            return
        
        phases_executed += 1
    
    total_time = time.time() - start_total
    
    print_summary()
    
    if phases_executed == 0:
        print(f"\n[COMPLETE] Toutes les phases etaient deja terminees!")
    else:
        print(f"\n[COMPLETE] {phases_executed} phase(s) executee(s)!")
        print(f"Temps total: {int(total_time//3600)}h {int((total_time%3600)//60)}m")
    
    print(f"Termine: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
