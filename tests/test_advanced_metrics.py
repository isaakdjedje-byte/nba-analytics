#!/usr/bin/env python3
"""
Tests unitaires pour NBA-18: Métriques avancées
"""

import sys
import json
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from processing.calculate_advanced_metrics import AdvancedMetricsCalculator
from utils.nba_formulas import (
    calculate_per_simplified,
    calculate_ts,
    calculate_ts_pct,
    calculate_efg_pct,
    calculate_usage_rate,
    calculate_game_score,
    calculate_bmi
)


class TestNBAMetrics:
    """Tests pour les formules NBA"""
    
    def test_ts_lebron(self):
        """Test TS% avec LeBron James 2023-24"""
        ts = calculate_ts(25.7, 17.9, 5.7)
        expected = 0.629
        diff = abs(ts - expected)
        
        assert diff < 0.02, f"TS% LeBron: {ts:.3f}, attendu: {expected:.3f}"
        print(f"✓ LeBron TS%: {ts:.3f} (OK)")
        return True
    
    def test_ts_curry(self):
        """Test TS% avec Stephen Curry 2023-24"""
        ts = calculate_ts(26.4, 19.5, 4.4)
        expected = 0.629
        diff = abs(ts - expected)
        
        assert diff < 0.02, f"TS% Curry: {ts:.3f}, attendu: {expected:.3f}"
        print(f"✓ Curry TS%: {ts:.3f} (OK)")
        return True
    
    def test_bmi_lebron(self):
        """Test BMI avec LeBron (206cm, 113kg)"""
        bmi = calculate_bmi(206, 113)
        expected = 26.6
        diff = abs(bmi - expected)
        
        assert diff < 0.5, f"BMI LeBron: {bmi:.1f}, attendu: {expected:.1f}"
        print(f"✓ LeBron BMI: {bmi:.1f} (OK)")
        return True
    
    def test_per_range(self):
        """Test que PER est entre 0 et 40"""
        stats = {
            'pts': 20, 'fgm': 8, 'fga': 15, 'ftm': 2, 'fta': 3,
            'oreb': 1, 'dreb': 4, 'ast': 5, 'stl': 1, 'blk': 0.5,
            'pf': 2, 'tov': 3, 'minutes': 30
        }
        per = calculate_per_simplified(stats)
        
        assert 0 <= per <= 40, f"PER hors limites: {per}"
        print(f"✓ PER range: {per:.2f} (OK)")
        return True
    
    def test_ts_percentage(self):
        """Test que TS% est entre 0 et 1"""
        ts = calculate_ts(20, 15, 5)
        
        assert 0 <= ts <= 1, f"TS% hors limites: {ts}"
        print(f"✓ TS% range: {ts:.3f} (OK)")
        return True
    
    def test_division_by_zero(self):
        """Test gestion division par zero"""
        # Minutes = 0
        per = calculate_per_simplified({'minutes': 0, 'pts': 20})
        assert per == 0.0, f"PER avec minutes=0: {per}"
        
        # FGA = 0
        ts = calculate_ts(0, 0, 0)
        assert ts == 0.0, f"TS% avec FGA=0: {ts}"
        
        print("✓ Division by zero handled (OK)")
        return True


class TestPipeline:
    """Tests pour le pipeline"""
    
    def test_load_players(self):
        """Test chargement des joueurs"""
        calc = AdvancedMetricsCalculator()
        
        if not calc.input_path.exists():
            print("⚠ Input file not found, skipping test")
            return True
        
        players = calc.load_players()
        assert len(players) > 0, "Aucun joueur chargé"
        assert len(players) >= 5000, f"Pas assez de joueurs: {len(players)}"
        
        print(f"✓ Loaded {len(players)} players (OK)")
        return True
    
    def test_output_exists(self):
        """Test que le fichier de sortie existe"""
        output_file = Path("data/silver/players_advanced/players.json")
        
        if not output_file.exists():
            print("⚠ Output file not found, run pipeline first")
            return True
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        players = data.get('data', [])
        assert len(players) > 0, "Aucun joueur dans le fichier"
        
        # Vérifier métriques
        required_metrics = ['per', 'ts_pct', 'efg_pct', 'usg_pct', 'game_score', 'bmi']
        sample_player = players[0]
        
        for metric in required_metrics:
            assert metric in sample_player, f"Métrique {metric} manquante"
        
        print(f"✓ Output file valid with {len(players)} players (OK)")
        return True


def run_all_tests():
    """Exécute tous les tests"""
    print("="*60)
    print("TESTS NBA-18: METRIQUES AVANCEES")
    print("="*60)
    
    tests = TestNBAMetrics()
    pipeline_tests = TestPipeline()
    
    results = []
    
    # Tests formules
    print("\n1. Tests des formules:")
    try:
        tests.test_ts_lebron()
        results.append(('ts_lebron', True))
    except AssertionError as e:
        print(f"✗ {e}")
        results.append(('ts_lebron', False))
    
    try:
        tests.test_ts_curry()
        results.append(('ts_curry', True))
    except AssertionError as e:
        print(f"✗ {e}")
        results.append(('ts_curry', False))
    
    try:
        tests.test_bmi_lebron()
        results.append(('bmi_lebron', True))
    except AssertionError as e:
        print(f"✗ {e}")
        results.append(('bmi_lebron', False))
    
    try:
        tests.test_per_range()
        results.append(('per_range', True))
    except AssertionError as e:
        print(f"✗ {e}")
        results.append(('per_range', False))
    
    try:
        tests.test_ts_percentage()
        results.append(('ts_range', True))
    except AssertionError as e:
        print(f"✗ {e}")
        results.append(('ts_range', False))
    
    try:
        tests.test_division_by_zero()
        results.append(('division_zero', True))
    except AssertionError as e:
        print(f"✗ {e}")
        results.append(('division_zero', False))
    
    # Tests pipeline
    print("\n2. Tests du pipeline:")
    try:
        pipeline_tests.test_load_players()
        results.append(('load_players', True))
    except Exception as e:
        print(f"✗ {e}")
        results.append(('load_players', False))
    
    try:
        pipeline_tests.test_output_exists()
        results.append(('output_exists', True))
    except Exception as e:
        print(f"✗ {e}")
        results.append(('output_exists', False))
    
    # Rapport
    print("\n" + "="*60)
    print("RAPPORT DE TESTS")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)
    
    print(f"\nTests passés: {passed}/{len(results)}")
    print(f"Tests échoués: {failed}/{len(results)}")
    
    if failed == 0:
        print("\n✓ TOUS LES TESTS SONT VALIDES!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) ont échoué")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
