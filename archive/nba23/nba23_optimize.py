#!/usr/bin/env python3
"""
NBA-23: Script d'optimisation avancée
Clustering avec features avancées, k=8-16, parallélisation
"""

import sys
from pathlib import Path

# Ajoute les chemins
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'ml' / 'archetype'))

import importlib.util

# Charge modules directement
spec = importlib.util.spec_from_file_location("feature_engineering", "src/ml/archetype/feature_engineering.py")
feature_engineering = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feature_engineering)
ArchetypeFeatureEngineer = feature_engineering.ArchetypeFeatureEngineer

spec = importlib.util.spec_from_file_location("auto_clustering", "src/ml/archetype/auto_clustering.py")
auto_clustering = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auto_clustering)
AutoClustering = auto_clustering.AutoClustering

spec = importlib.util.spec_from_file_location("archetype_profiler", "src/ml/archetype/archetype_profiler.py")
archetype_profiler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archetype_profiler)
ArchetypeProfiler = archetype_profiler.ArchetypeProfiler


def main():
    import pandas as pd
    import json
    from datetime import datetime
    import os
    
    print("=" * 70)
    print("NBA-23 OPTIMIZED: Clustering Avance avec k=8-16")
    print("=" * 70)
    print("Demarrage: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print()
    
    # Étape 1: Chargement
    print("Etape 1: Chargement des donnees...")
    with open('data/silver/players_advanced/players_enriched_final.json', 
              'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df_raw = pd.DataFrame(data['data'])
    print("   {} joueurs charges".format(len(df_raw)))
    
    # Étape 2: Features avec métriques avancées
    print("\nEtape 2: Feature Engineering Avance (28+ features)...")
    engineer = ArchetypeFeatureEngineer()
    
    # Utilise moins de restrictions pour garder plus de joueurs
    df_features, feature_cols, metadata_cols = \
        engineer.prepare_for_clustering(df_raw, min_games=5)
    
    print("   {} joueurs valides".format(len(df_features)))
    print("   {} features creees (dont NBA-23 avancees)".format(len(feature_cols)))
    print("   Features: {}...".format(", ".join(feature_cols[:5])))
    
    # Si trop peu de joueurs, relâche les contraintes
    if len(df_features) < 1000:
        print("   Relachement des contraintes...")
        df_features, feature_cols, metadata_cols = \
            engineer.prepare_for_clustering(df_raw, min_games=1)
    
    # Étape 3: Feature Selection
    print("\nEtape 3: Feature Selection...")
    clusterer = AutoClustering(random_state=42)
    X = df_features[feature_cols].values
    X_selected, selected_features = clusterer.select_optimal_features(
        X, feature_cols, n_features=20
    )
    print("   {} features sélectionnées".format(len(selected_features)))
    
    # Étape 4: Clustering k=8 à 16 avec parallélisation
    print("\nEtape 4: Clustering Parallele (k=8-16)...")
    # Ajuste min_cluster_size selon nombre de joueurs
    min_cluster = max(50, len(df_features) // 50)  # Au moins 50 joueurs par cluster
    
    print("   Min cluster size: {}".format(min_cluster))
    
    result = clusterer.fit(
        X_selected, 
        k_range=range(6, 13),  # k=6 à 12 (plus conservateur pour test)
        min_cluster_size=min_cluster,
        n_jobs=1  # Mode séquentiel pour debug
    )
    
    print("\n   Meilleur Modele:")
    print("   - Algorithme: {}".format(result.algorithm))
    print("   - Clusters: {}".format(result.n_clusters))
    print("   - Silhouette: {:.3f}".format(result.silhouette))
    print("   - Calinski-Harabasz: {:.0f}".format(result.calinski_harabasz))
    print("   - Davies-Bouldin: {:.3f}".format(result.davies_bouldin))
    
    # Distribution
    print("\n   Distribution:")
    for cluster_id, size in sorted(result.cluster_sizes.items()):
        if cluster_id >= 0:
            pct = size / len(X_selected) * 100
            print("      Cluster {}: {} joueurs ({:.1f}%)".format(cluster_id, size, pct))
    
    # Étape 5: Profiling
    print("\nEtape 5: Profiling des archetypes...")
    profiler = ArchetypeProfiler()
    cluster_profiles = profiler.analyze_clusters(
        df_features, result.labels, selected_features
    )
    
    df_clustered = profiler.assign_archetypes(
        df_features, result.labels, result.probabilities
    )
    
    print("   {} archetypes identifies".format(len(cluster_profiles)))
    
    # Affiche les archétypes
    print("\n   Archetypes:")
    for _, row in cluster_profiles.iterrows():
        arch_id = row['matched_archetype']
        arch = profiler.ARCHETYPES.get(arch_id)
        if arch:
            print("      {}: {} ({} joueurs, {:.1f}%)".format(
                row['cluster_id'], arch.name_fr, row['n_players'], row['pct_total']))
    
    # Étape 6: Export
    print("\nEtape 6: Export...")
    os.makedirs('data/gold/player_archetypes', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    # Sauvegarde avec suffixe v2
    df_clustered.to_parquet(
        'data/gold/player_archetypes/player_archetypes_v2.parquet',
        index=False
    )
    print("   player_archetypes_v2.parquet")
    
    clusterer.save(
        'data/gold/player_archetypes/clustering_model_v2.joblib'
    )
    print("   clustering_model_v2.joblib")
    
    # Rapport
    report = {
        'timestamp': datetime.now().isoformat(),
        'nba23_status': 'OPTIMIZED_COMPLETED',
        'data': {
            'total_players': len(df_raw),
            'players_clustered': len(df_clustered),
            'features_original': len(feature_cols),
            'features_selected': len(selected_features),
            'selected_features': selected_features
        },
        'clustering': {
            'algorithm': result.algorithm,
            'n_clusters': int(result.n_clusters),
            'silhouette_score': float(result.silhouette),
            'calinski_harabasz': float(result.calinski_harabasz),
            'davies_bouldin': float(result.davies_bouldin),
            'cluster_sizes': {str(k): int(v) for k, v in result.cluster_sizes.items()}
        },
        'archetypes': profiler.get_archetype_report()
    }
    
    with open('reports/nba23_optimized_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print("   nba23_optimized_report.json")
    
    print("\n" + "=" * 70)
    print("NBA-23 OPTIMIZED TERMINE!")
    print("=" * 70)
    print("Joueurs: {}".format(len(df_clustered)))
    print("Features: {} (sélectionnées)".format(len(selected_features)))
    print("Clusters: {}".format(result.n_clusters))
    print("Silhouette: {:.3f} (vs 0.118 avant)".format(result.silhouette))
    print("=" * 70)


if __name__ == "__main__":
    main()
