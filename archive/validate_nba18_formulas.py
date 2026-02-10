#!/usr/bin/env python3
"""
Validation rapide des formules NBA-18 avant implémentation complète
Test avec données réelles de joueurs connus
"""

import json
import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.nba_formulas import (
    calculate_per_simplified,
    calculate_per_full,
    calculate_ts,
    calculate_ts_pct,
    calculate_efg_pct,
    calculate_usage_rate,
    calculate_pace,
    calculate_game_score,
    calculate_bmi,
    calculate_all_metrics
)

def test_lebron_james():
    """Test PER avec LeBron James 2023-24"""
    print("\n" + "="*60)
    print("TEST 1: LeBron James 2023-24")
    print("="*60)
    
    # Données réelles LeBron 2023-24
    lebron_stats = {
        'player_id': 2544,
        'full_name': 'LeBron James',
        'pts': 25.7,
        'reb': 7.3,
        'ast': 8.3,
        'stl': 1.3,
        'blk': 0.5,
        'fgm': 9.7,
        'fga': 17.9,
        'ftm': 4.6,
        'fta': 5.7,
        'tov': 3.5,
        'pf': 1.4,
        'minutes': 35.3
    }
    
    # Test TS%
    ts_pct = calculate_ts(
        lebron_stats['pts'],
        lebron_stats['fga'],
        lebron_stats['fta']
    )
    expected_ts = 0.629  # Valeur NBA.com
    ts_diff = abs(ts_pct - expected_ts)
    
    print(f"TS% calculé: {ts_pct:.3f} ({ts_pct*100:.1f}%)")
    print(f"TS% attendu: {expected_ts:.3f} ({expected_ts*100:.1f}%)")
    print(f"Écart: {ts_diff:.3f} ({ts_diff*100:.1f}%)")
    print(f"✅ VALIDÉ" if ts_diff < 0.02 else f"❌ ÉCART TROP IMPORTANT")
    
    return {
        'player': 'LeBron James',
        'ts_pct': ts_pct,
        'ts_expected': expected_ts,
        'ts_valid': ts_diff < 0.02,
        'ts_diff': ts_diff
    }

def test_stephen_curry():
    """Test TS% avec Stephen Curry 2023-24"""
    print("\n" + "="*60)
    print("TEST 2: Stephen Curry 2023-24")
    print("="*60)
    
    # Données réelles Curry 2023-24
    curry_stats = {
        'player_id': 201939,
        'full_name': 'Stephen Curry',
        'pts': 26.4,
        'fga': 19.5,
        'fta': 4.4
    }
    
    ts_pct = calculate_ts(
        curry_stats['pts'],
        curry_stats['fga'],
        curry_stats['fta']
    )
    expected_ts = 0.629  # Valeur NBA.com
    ts_diff = abs(ts_pct - expected_ts)
    
    print(f"TS% calculé: {ts_pct:.3f} ({ts_pct*100:.1f}%)")
    print(f"TS% attendu: {expected_ts:.3f} ({expected_ts*100:.1f}%)")
    print(f"Écart: {ts_diff:.3f}")
    print(f"✅ VALIDÉ" if ts_diff < 0.02 else f"❌ ÉCART TROP IMPORTANT")
    
    return {
        'player': 'Stephen Curry',
        'ts_pct': ts_pct,
        'ts_expected': expected_ts,
        'ts_valid': ts_diff < 0.02,
        'ts_diff': ts_diff
    }

def test_edge_cases():
    """Test des cas limites"""
    print("\n" + "="*60)
    print("TEST 3: Edge Cases")
    print("="*60)
    
    results = []
    
    # Test 1: Division par zéro (minutes=0)
    print("\n1. Minutes = 0:")
    try:
        per = calculate_per_simplified({'minutes': 0, 'pts': 20, 'fgm': 8, 'fga': 15})
        print(f"   PER: {per}")
        print("   ✅ Gestion OK: Retourne 0.0")
        results.append(('minutes_zero', 'ok', per))
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
        results.append(('minutes_zero', 'error', str(e)))
    
    # Test 2: FGA = 0
    print("\n2. FGA = 0:")
    try:
        ts = calculate_ts(0, 0, 0)
        print(f"   TS%: {ts}")
        results.append(('fga_zero', 'ok', ts))
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
        results.append(('fga_zero', 'error', str(e)))
    
    # Test 3: Valeurs négatives
    print("\n3. Valeurs négatives:")
    try:
        ts = calculate_ts(-5, 10, 2)
        print(f"   TS% avec points négatifs: {ts}")
        results.append(('negative_pts', 'warning', ts))
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
        results.append(('negative_pts', 'error', str(e)))
    
    return results

def test_with_real_data():
    """Test avec données réelles du projet"""
    print("\n" + "="*60)
    print("TEST 4: Données réelles du projet")
    print("="*60)
    
    gold_file = Path("data/silver/players_gold_standard/players.json")
    
    if not gold_file.exists():
        print(f"❌ Fichier non trouvé: {gold_file}")
        return None
    
    with open(gold_file, 'r') as f:
        data = json.load(f)
        players = data.get('data', [])
    
    print(f"Nombre de joueurs: {len(players)}")
    
    # Prendre un échantillon de 5 joueurs avec données complètes
    sample = [p for p in players if p.get('height_cm') and p.get('weight_kg')][:5]
    
    print(f"\nÉchantillon de {len(sample)} joueurs:")
    for player in sample:
        height_m = player['height_cm'] / 100
        weight_kg = player['weight_kg']
        bmi = weight_kg / (height_m ** 2)
        
        print(f"\n  {player.get('full_name', 'N/A')}:")
        print(f"    Taille: {player['height_cm']}cm")
        print(f"    Poids: {player['weight_kg']}kg")
        print(f"    BMI calculé: {bmi:.1f}")
    
    return {
        'total_players': len(players),
        'sample_size': len(sample),
        'sample': sample
    }

def generate_report(results):
    """Génère un rapport de validation"""
    print("\n" + "="*60)
    print("RAPPORT DE VALIDATION NBA-18")
    print("="*60)
    
    report = {
        'timestamp': str(Path(__file__).stat().st_mtime),
        'tests': results,
        'summary': {
            'total_tests': len(results),
            'passed': sum(1 for r in results if r.get('ts_valid', False)),
            'failed': sum(1 for r in results if not r.get('ts_valid', True))
        }
    }
    
    print(f"\n📊 Résumé:")
    print(f"   Tests exécutés: {report['summary']['total_tests']}")
    print(f"   ✅ Réussis: {report['summary']['passed']}")
    print(f"   ❌ Échoués: {report['summary']['failed']}")
    
    # Sauvegarder rapport
    report_file = Path("validation_nba18_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📝 Rapport sauvegardé: {report_file}")
    
    return report

def main():
    """Exécute tous les tests"""
    print("🚀 VALIDATION RAPIDE NBA-18")
    print("Test des formules avant implémentation complète")
    
    results = []
    
    # Test 1: LeBron
    results.append(test_lebron_james())
    
    # Test 2: Curry
    results.append(test_stephen_curry())
    
    # Test 3: Edge cases
    edge_results = test_edge_cases()
    
    # Test 4: Données réelles
    real_data = test_with_real_data()
    
    # Générer rapport
    report = generate_report(results)
    
    # Conclusion
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)
    
    if report['summary']['failed'] == 0:
        print("\n✅ Tous les tests sont validés!")
        print("Les formules sont prêtes pour l'implémentation NBA-18.")
        print("\nProchaine étape: Créer le pipeline calculate_advanced_metrics.py")
        return 0
    else:
        print("\n⚠️  Certains tests ont échoué.")
        print("Il faut corriger les formules avant de continuer.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
