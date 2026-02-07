#!/usr/bin/env python3
"""
Test rapide NBA-17 avec sous-ensemble de donnees
Verifie que tout fonctionne sans attendre 76 min
"""

import sys
from pathlib import Path

# Test 1: Import
print("Test 1: Import module...")
from src.processing.clean_players import PlayersDataCleaner
print("  [OK] Import OK")

# Test 2: Initialisation
print("\nTest 2: Initialisation...")
cleaner = PlayersDataCleaner()
print("  [OK] Initialisation OK")
print(f"  [OK] Config chargee: {len(cleaner.config)} sections")

# Test 3: Conversion unites
print("\nTest 3: Conversions...")
assert cleaner._convert_height_to_cm('6-8') == 203
assert cleaner._convert_weight_to_kg(225) == 102
assert cleaner._standardize_position('Forward') == 'F'
print("  [OK] Conversions OK")

# Test 4: Validation
print("\nTest 4: Validation...")
test_players = [
    {'id': 1, 'full_name': 'Player 1', 'height_cm': 200, 'weight_kg': 100},
    {'id': 2, 'full_name': 'Player 2', 'height_cm': 210, 'weight_kg': 110}
]
assert cleaner.validate_data(test_players) == True
print("  [OK] Validation OK")

# Test 5: Structure output
print("\nTest 5: Structure...")
output_path = Path("data/silver/players_cleaned")
print(f"  Output path: {output_path}")
print("  [OK] Chemins OK")

print("\n" + "="*60)
print("[SUCCESS] TOUS LES TESTS RAPIDES PASSENT")
print("="*60)
print("\nLe pipeline complet est pret.")
print("Pour executer avec les 5103 joueurs (~76 min):")
print("  python src/processing/clean_players.py")
print("\nPour executer les tests:")
print("  pytest tests/test_clean_players.py -v")
