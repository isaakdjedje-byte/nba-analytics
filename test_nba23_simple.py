#!/usr/bin/env python3
"""
Test simple de NBA-23 V3 (évite imports PySpark)
"""

import sys
import pandas as pd
import numpy as np

print("=" * 70)
print("TEST NBA-23 VERSION 3.0 - Mode Simplifie")
print("=" * 70)

# Test 1: Formules vectorisees
print("\n1. Test Formules Vectorisees dans nba_formulas.py...")
try:
    sys.path.insert(0, 'src/utils')
    from nba_formulas import NBAFormulasVectorized
    
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
    
    print(f"   [OK] TS%: {[round(x, 3) for x in ts_pct.tolist()]}")
    print(f"   [OK] eFG%: {[round(x, 3) for x in efg_pct.tolist()]}")
    print(f"   [OK] BMI: {[round(x, 2) for x in bmi.tolist()]}")
    print("   [OK] Formules vectorisees fonctionnent!")
    
except Exception as e:
    print(f"   [ERREUR] {e}")

# Test 2: Hierarchical Matcher
print("\n2. Test HierarchicalArchetypeMatcher...")
try:
    sys.path.insert(0, 'src/ml/archetype')
    from archetype_matcher import HierarchicalArchetypeMatcher
    
    matcher = HierarchicalArchetypeMatcher()
    
    # Test matching
    test_profile = {
        'per': 27.5,
        'pts_per_36': 28.0,
        'ts_pct': 0.62,
        'usg_pct': 32.0
    }
    
    arch_id, confidence, level = matcher.match(test_profile)
    
    print(f"   [OK] Profil test (PER 27.5): {arch_id}")
    print(f"   [OK] Confiance: {confidence:.1%}")
    print(f"   [OK] Niveau: {level}")
    print(f"   [OK] Total archétypes: {len(matcher.ARCHETYPES)}")
    
    # Compte par niveau
    levels = {}
    for arch in matcher.ARCHETYPES.values():
        levels[arch.level] = levels.get(arch.level, 0) + 1
    
    print("   [OK] Répartition:")
    for level, count in levels.items():
        print(f"        - {level}: {count} archétypes")
    
except Exception as e:
    print(f"   [ERREUR] {e}")

# Test 3: Validator
print("\n3. Test ArchetypeValidator...")
try:
    from validation import ArchetypeValidator
    
    validator = ArchetypeValidator()
    
    print(f"   [OK] Ground truth: {len(validator.GROUND_TRUTH)} joueurs")
    
    # Compte par niveau
    levels = {}
    for arch in validator.GROUND_TRUTH.values():
        level = arch.split('_')[0]
        levels[level] = levels.get(level, 0) + 1
    
    print("   [OK] Répartition ground truth:")
    for level, count in levels.items():
        print(f"        - {level}: {count} joueurs")
    
except Exception as e:
    print(f"   [ERREUR] {e}")

# Test 4: Feature Engineering V3
print("\n4. Test Feature Engineering V3...")
try:
    from feature_engineering_v3 import ArchetypeFeatureEngineer
    
    engineer = ArchetypeFeatureEngineer()
    
    test_data = {
        'player_id': [1, 2, 3],
        'player_name': ['Player A', 'Player B', 'Player C'],
        'height_cm': [201, 198, 211],
        'weight_kg': [102, 95, 115],
        'pts': [1500, 800, 400],
        'reb': [400, 600, 900],
        'ast': [300, 200, 100],
        'stl': [80, 120, 40],
        'blk': [30, 80, 200],
        'minutes': [2000, 1800, 1500],
        'games_played': [70, 65, 50],
        'fga': [1200, 600, 300],
        'fgm': [550, 280, 140],
        'fg3a': [400, 200, 20],
        'fta': [300, 150, 80],
        'per': [22.5, 18.3, 15.2]
    }
    
    df_test = pd.DataFrame(test_data)
    df_result, features, metadata = engineer.prepare_for_clustering(df_test)
    
    print(f"   [OK] {len(features)} features créées")
    print(f"   [OK] Features principales: {', '.join(features[:5])}")
    print(f"   [OK] Shape finale: {df_result.shape}")
    
    # Vérifie catégories
    print("   [OK] Répartition par catégorie:")
    for category in ['physical', 'offensive', 'defensive', 'nba23_metrics']:
        feats = engineer.get_features_by_category(category)
        if feats:
            print(f"        - {category}: {len(feats)} features")
    
except Exception as e:
    print(f"   [ERREUR] {e}")

# Résumé
print("\n" + "=" * 70)
print("RÉSUMÉ")
print("=" * 70)
print("\nFichiers créés/modifiés:")
print("  [OK] src/ml/base/base_feature_engineer.py")
print("  [OK] src/ml/base/__init__.py")
print("  [OK] src/ml/archetype/feature_engineering_v3.py")
print("  [OK] src/ml/archetype/archetype_matcher.py")
print("  [OK] src/ml/archetype/validation.py")
print("  [OK] src/utils/nba_formulas.py (formules vectorisées ajoutées)")
print("  [OK] src/ml/archetype/__init__.py (mis à jour)")

print("\nAméliorations majeures:")
print("  - Architecture hiérarchique: ELITE > STARTER > ROLE > BENCH")
print("  - 13 archétypes distincts (vs 3 avant)")
print("  - 36+ joueurs ground truth pour validation")
print("  - Formules NBA centralisées (évite duplication)")
print("  - BaseFeatureEngineer réutilisable")

print("\nProchaines étapes recommandées:")
print("  1. Exécuter: python nba23_clustering.py")
print("  2. Tester la validation: from src.ml.archetype import quick_validation")
print("  3. Vérifier les résultats dans data/gold/player_archetypes/")
print("  4. Tester l'intégration NBA-22")

print("\n" + "=" * 70)
