#!/usr/bin/env python3
"""
Script de test rapide pour NBA-23 V3
Vérifie que tous les nouveaux modules sont fonctionnels
"""

import sys
from pathlib import Path

print("=" * 70)
print("TEST NBA-23 VERSION 3.0")
print("=" * 70)

# Test 1: Base Feature Engineer
print("\n1. Test BaseFeatureEngineer...")
try:
    from src.ml.base.base_feature_engineer import BaseFeatureEngineer, NBAFormulasVectorized
    
    # Test formules vectorisées
    import pandas as pd
    test_df = pd.DataFrame({
        'pts': [20, 25, 15],
        'fga': [15, 18, 12],
        'fta': [5, 6, 4],
        'fgm': [8, 10, 6],
        'fg3m': [2, 3, 1],
        'height_cm': [200, 198, 205],
        'weight_kg': [100, 95, 110]
    })
    
    formulas = NBAFormulasVectorized()
    ts_pct = formulas.calculate_ts_pct(test_df)
    efg_pct = formulas.calculate_efg_pct(test_df)
    bmi = formulas.calculate_bmi(test_df)
    
    print(f"   ✓ TS% calculé: {ts_pct.tolist()}")
    print(f"   ✓ eFG% calculé: {efg_pct.tolist()}")
    print(f"   ✓ BMI calculé: {bmi.tolist()}")
    print("   ✓ BaseFeatureEngineer OK")
    
except Exception as e:
    print(f"   ✗ Erreur: {e}")

# Test 2: Hierarchical Matcher
print("\n2. Test HierarchicalArchetypeMatcher...")
try:
    from src.ml.archetype import HierarchicalArchetypeMatcher
    
    matcher = HierarchicalArchetypeMatcher()
    
    # Test matching
    test_profile = {
        'per': 27.5,
        'pts_per_36': 28.0,
        'ts_pct': 0.62,
        'usg_pct': 32.0
    }
    
    arch_id, confidence, level = matcher.match(test_profile)
    
    print(f"   ✓ Profil test (PER 27.5): {arch_id}")
    print(f"   ✓ Confiance: {confidence:.2%}")
    print(f"   ✓ Niveau: {level}")
    print(f"   ✓ Total archétypes: {len(matcher.ARCHETYPES)}")
    print("   ✓ HierarchicalArchetypeMatcher OK")
    
except Exception as e:
    print(f"   ✗ Erreur: {e}")

# Test 3: Validator
print("\n3. Test ArchetypeValidator...")
try:
    from src.ml.archetype import ArchetypeValidator
    
    validator = ArchetypeValidator()
    
    print(f"   ✓ Ground truth: {len(validator.GROUND_TRUTH)} joueurs")
    
    # Compte par niveau
    levels = {}
    for arch in validator.GROUND_TRUTH.values():
        level = arch.split('_')[0]
        levels[level] = levels.get(level, 0) + 1
    
    for level, count in levels.items():
        print(f"   ✓   {level}: {count} joueurs")
    
    print("   ✓ ArchetypeValidator OK")
    
except Exception as e:
    print(f"   ✗ Erreur: {e}")

# Test 4: Module Info
print("\n4. Test Module Info...")
try:
    from src.ml.archetype import get_module_info, __version__
    
    info = get_module_info()
    print(f"   ✓ Version: {info['version']}")
    print(f"   ✓ Features: {info['features']}")
    print(f"   ✓ Archétypes: {info['archetypes']}")
    print(f"   ✓ Niveaux: {', '.join(info['levels'])}")
    print("   ✓ Module Info OK")
    
except Exception as e:
    print(f"   ✗ Erreur: {e}")

# Résumé
print("\n" + "=" * 70)
print("RÉSUMÉ DES TESTS")
print("=" * 70)
print("\nNouveaux composants créés:")
print("  ✓ src/ml/base/base_feature_engineer.py")
print("  ✓ src/ml/archetype/feature_engineering_v3.py")
print("  ✓ src/ml/archetype/archetype_matcher.py")
print("  ✓ src/ml/archetype/validation.py")
print("  ✓ Formules vectorisées dans src/utils/nba_formulas.py")
print("\nAméliorations:")
print("  • 13 archétypes hiérarchiques (ELITE > STARTER > ROLE > BENCH)")
print("  • 36+ joueurs ground truth pour validation")
print("  • Centralisation des formules NBA (évite duplication)")
print("  • Architecture héritée pour Feature Engineering")
print("\nProchaines étapes:")
print("  1. Exécuter nba23_clustering.py avec la nouvelle version")
print("  2. Valider avec quick_validation()")
print("  3. Intégrer dans NBA-22 pour tester l'impact")
print("=" * 70)
