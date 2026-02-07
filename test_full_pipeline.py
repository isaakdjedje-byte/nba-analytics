#!/usr/bin/env python3
"""
Test complet du pipeline NBA-11 à NBA-18
Vérifie que tout fonctionne sans erreur
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, 'src')

def test_nba_formulas():
    """Test NBA-18: Formules"""
    print("\n" + "="*60)
    print("TEST NBA-18: FORMULES")
    print("="*60)
    
    from utils.nba_formulas import (
        calculate_per_simplified, calculate_ts, calculate_bmi,
        calculate_efg_pct, calculate_usage_rate, calculate_game_score
    )
    
    # Test PER
    stats = {'pts': 25.7, 'fgm': 9.7, 'fga': 17.9, 'ftm': 4.6, 'fta': 5.7,
             'oreb': 0.8, 'dreb': 6.5, 'ast': 8.3, 'stl': 1.3, 'blk': 0.5,
             'pf': 1.4, 'tov': 3.5, 'minutes': 35.3}
    per = calculate_per_simplified(stats)
    assert 0 <= per <= 40, f"PER hors limites: {per}"
    print(f"  PER: {per:.2f} - OK")
    
    # Test TS%
    ts = calculate_ts(25.7, 17.9, 5.7)
    assert 0 <= ts <= 1, f"TS% hors limites: {ts}"
    print(f"  TS%: {ts:.3f} - OK")
    
    # Test BMI
    bmi = calculate_bmi(206, 113)
    assert 20 <= bmi <= 30, f"BMI anormal: {bmi}"
    print(f"  BMI: {bmi:.1f} - OK")
    
    print("  [PASS]")
    return True

def test_season_selector():
    """Test NBA-18 V2: Season Selector"""
    print("\n" + "="*60)
    print("TEST NBA-18 V2: SEASON SELECTOR")
    print("="*60)
    
    from utils.season_selector import SeasonSelector
    
    selector = SeasonSelector()
    
    headers = ['SEASON_ID', 'GP', 'MIN', 'PTS', 'FGM', 'FGA', 'FG3M', 'FTM', 'FTA', 
               'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
    
    row_set = [
        ['2021-22', 55, 1500, 20.5, 8.0, 16.0, 2.0, 2.5, 3.0, 1.0, 4.0, 5.0, 5.0, 1.0, 0.5, 2.5, 2.0],
        ['2022-23', 72, 2400, 25.7, 9.7, 17.9, 2.4, 4.6, 5.7, 0.8, 6.5, 7.3, 8.3, 1.3, 0.5, 3.5, 1.4],
        ['2023-24', 71, 2504, 25.7, 9.7, 17.9, 2.4, 4.6, 5.7, 0.8, 6.5, 7.3, 8.3, 1.3, 0.5, 3.5, 1.4]
    ]
    
    seasons = selector.get_all_four_seasons(row_set, headers)
    assert all(seasons[m].get('available') for m in ['complete', 'max_minutes', 'avg_3', 'best_per'])
    print("  4 methodes disponibles - OK")
    
    agg, meta = selector.aggregate_metrics(seasons)
    assert len(agg) > 0
    assert 'weights' in meta
    print(f"  Aggregation: {len(meta['methods_used'])} methodes - OK")
    
    print("  [PASS]")
    return True

def test_data_files():
    """Test NBA-11 à NBA-17: Fichiers de données"""
    print("\n" + "="*60)
    print("TEST NBA-11 A NBA-17: FICHIERS DE DONNEES")
    print("="*60)
    
    files_to_check = [
        ("data/silver/players_gold_standard/players.json", "Dataset GOLD Standard"),
        ("docs/INDEX.md", "Documentation INDEX"),
        ("docs/JIRA_BACKLOG.md", "Backlog JIRA"),
        ("docs/agent.md", "Documentation Agent"),
    ]
    
    for filepath, desc in files_to_check:
        path = Path(filepath)
        if path.exists():
            size = path.stat().st_size
            print(f"  {desc}: {size} bytes - OK")
        else:
            print(f"  {desc}: MANQUANT - WARNING")
    
    # Verifier GOLD
    gold_file = Path("data/silver/players_gold_standard/players.json")
    if gold_file.exists():
        with open(gold_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            count = len(data.get('data', []))
            print(f"  Joueurs GOLD: {count} - OK")
            assert count >= 5000, "Pas assez de joueurs GOLD"
    
    print("  [PASS]")
    return True

def test_pipeline_scripts():
    """Test que les scripts existent"""
    print("\n" + "="*60)
    print("TEST SCRIPTS PIPELINE")
    print("="*60)
    
    scripts = [
        "src/utils/nba_formulas.py",
        "src/utils/season_selector.py",
        "src/processing/enrich_player_stats_v2.py",
        "src/processing/compile_nba18_final.py",
    ]
    
    for script in scripts:
        path = Path(script)
        if path.exists():
            print(f"  {script}: OK")
        else:
            print(f"  {script}: MANQUANT - ERROR")
            return False
    
    print("  [PASS]")
    return True

def test_imports():
    """Test que tous les imports fonctionnent"""
    print("\n" + "="*60)
    print("TEST IMPORTS")
    print("="*60)
    
    try:
        from utils.nba_formulas import calculate_all_metrics
        print("  nba_formulas: OK")
        
        from utils.season_selector import SeasonSelector
        print("  season_selector: OK")
        
        print("  [PASS]")
        return True
    except Exception as e:
        print(f"  ERREUR: {e}")
        return False

def main():
    """Exécute tous les tests"""
    print("="*60)
    print("TEST COMPLET PIPELINE NBA-11 A NBA-18")
    print("="*60)
    
    tests = [
        ("Imports", test_imports),
        ("NBA Formules", test_nba_formulas),
        ("Season Selector", test_season_selector),
        ("Fichiers de données", test_data_files),
        ("Scripts pipeline", test_pipeline_scripts),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\nERREUR dans {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Rapport final
    print("\n" + "="*60)
    print("RAPPORT FINAL")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {name}")
    
    print(f"\nTotal: {passed}/{len(results)} tests reussis")
    
    if failed == 0:
        print("\n✓ TOUS LES TESTS SONT VALIDES!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) ont echoue")
        return 1

if __name__ == "__main__":
    sys.exit(main())
