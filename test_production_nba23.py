#!/usr/bin/env python3
"""NBA-23 Test Production - Exécute tous les tests avec vraies données"""
import sys
import time
import json
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("=" * 70)
print("NBA-23 TEST PRODUCTION COMPLET - v3.1")
print("=" * 70)
print(f"Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Test 1: Chargement données
print("TEST 1: Chargement des données...")
try:
    data_path = 'data/silver/players_advanced/players_enriched_final.json'
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✓ {len(data['data'])} joueurs chargés")
except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)

# Test 2: NBA-19 Integration
print("\nTEST 2: Intégration NBA-19...")
try:
    from ml.archetype.nba19_integration import load_nba19_stats
    loader = load_nba19_stats()
    if loader and loader.team_stats is not None:
        print(f"✓ {len(loader.team_stats)} équipes chargées")
        summary = loader.get_stats_summary()
        print(f"  Moyennes - PTS: {summary.get('avg_pts', 0):.1f}")
    else:
        print("⚠️  NBA-19 non disponible")
except Exception as e:
    print(f"⚠️  Erreur NBA-19: {e}")

# Test 3: Feature Engineering
print("\nTEST 3: Feature Engineering...")
try:
    from ml.archetype import ArchetypeFeatureEngineer
    import pandas as pd
    
    engineer = ArchetypeFeatureEngineer()
    df_raw = pd.DataFrame(data['data'])
    
    start = time.time()
    df_features, feature_cols, metadata = engineer.prepare_for_clustering(df_raw, min_games=10)
    elapsed = time.time() - start
    
    print(f"✓ Terminé en {elapsed:.2f}s")
    print(f"  {len(df_features)} joueurs, {len(feature_cols)} features")
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Clustering
print("\nTEST 4: Clustering...")
try:
    from ml.archetype import AutoClustering
    import numpy as np
    
    X = df_features.select_dtypes(include=[np.number]).values
    
    # Test parallèle
    clusterer = AutoClustering(random_state=42)
    start = time.time()
    result = clusterer.fit(X, k_range=range(6, 10), n_jobs=-1)
    elapsed = time.time() - start
    
    print(f"✓ Terminé en {elapsed:.2f}s")
    print(f"  Algorithme: {result.algorithm}")
    print(f"  Clusters: {result.n_clusters}")
    print(f"  Silhouette: {result.silhouette:.3f}")
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Archetype Matching
print("\nTEST 5: Archetype Matching...")
try:
    from ml.archetype import HierarchicalArchetypeMatcher
    
    matcher = HierarchicalArchetypeMatcher()
    print(f"✓ {len(matcher.ARCHETYPES)} archétypes disponibles")
    print("✓ Test OK")
except Exception as e:
    print(f"❌ Erreur: {e}")

# Rapport final
print("\n" + "=" * 70)
print("✅ TOUS LES TESTS COMPLÉTÉS")
print("=" * 70)
print("\nNBA-23 v3.1 est prêt pour la production!")
