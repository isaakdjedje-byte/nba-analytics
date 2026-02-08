#!/usr/bin/env python3
"""
NBA-23: Benchmark Performance
Mesure temps d'exécution, qualité clustering, et métriques
"""

import time
import numpy as np
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import sys
import psutil
import os

# Ajoute src au path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ml.archetype.feature_engineering import ArchetypeFeatureEngineer
from ml.archetype.auto_clustering import AutoClustering
from ml.archetype.archetype_matcher import HierarchicalArchetypeMatcher


class NBABenchmark:
    """Benchmark complet de NBA-23"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'version': '3.1',
            'tests': {}
        }
        self.process = psutil.Process(os.getpid())
    
    def get_memory_usage(self):
        """Retourne mémoire utilisée en MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def benchmark_feature_engineering(self, df_raw):
        """Benchmark feature engineering"""
        print("\n" + "="*70)
        print("BENCHMARK: Feature Engineering")
        print("="*70)
        
        engineer = ArchetypeFeatureEngineer()
        mem_before = self.get_memory_usage()
        
        start_time = time.time()
        df_features, feature_cols, metadata = engineer.prepare_for_clustering(
            df_raw, min_games=10
        )
        elapsed = time.time() - start_time
        mem_after = self.get_memory_usage()
        
        result = {
            'elapsed_time': elapsed,
            'memory_used_mb': mem_after - mem_before,
            'players_processed': len(df_features),
            'features_created': len(feature_cols),
            'features_list': feature_cols[:10]  # Top 10 seulement
        }
        
        print(f"  ⏱️  Temps: {elapsed:.2f}s")
        print(f"  🧠 Mémoire: {result['memory_used_mb']:.1f} MB")
        print(f"  👥 Joueurs: {result['players_processed']}")
        print(f"  📊 Features: {result['features_created']}")
        
        self.results['tests']['feature_engineering'] = result
        return df_features, feature_cols
    
    def benchmark_clustering_sequential(self, X, k_range):
        """Benchmark clustering séquentiel"""
        print("\n" + "="*70)
        print("BENCHMARK: Clustering (Séquentiel)")
        print("="*70)
        
        clusterer = AutoClustering(random_state=42)
        mem_before = self.get_memory_usage()
        
        start_time = time.time()
        result = clusterer.fit(X, k_range=k_range, min_cluster_size=100, n_jobs=1)
        elapsed = time.time() - start_time
        mem_after = self.get_memory_usage()
        
        metrics = {
            'elapsed_time': elapsed,
            'memory_used_mb': mem_after - mem_before,
            'algorithm': result.algorithm,
            'n_clusters': int(result.n_clusters),
            'silhouette_score': float(result.silhouette),
            'calinski_harabasz': float(result.calinski_harabasz),
            'davies_bouldin': float(result.davies_bouldin),
        }
        
        print(f"  ⏱️  Temps: {elapsed:.2f}s")
        print(f"  🧠 Mémoire: {metrics['memory_used_mb']:.1f} MB")
        print(f"  🎯 Algorithme: {metrics['algorithm']}")
        print(f"  📦 Clusters: {metrics['n_clusters']}")
        print(f"  📈 Silhouette: {metrics['silhouette_score']:.3f}")
        print(f"  📊 Calinski-Harabasz: {metrics['calinski_harabasz']:.0f}")
        
        self.results['tests']['clustering_sequential'] = metrics
        return result
    
    def benchmark_clustering_parallel(self, X, k_range):
        """Benchmark clustering parallèle"""
        print("\n" + "="*70)
        print("BENCHMARK: Clustering (Parallèle)")
        print("="*70)
        
        clusterer = AutoClustering(random_state=42)
        mem_before = self.get_memory_usage()
        
        start_time = time.time()
        result = clusterer.fit(X, k_range=k_range, min_cluster_size=100, n_jobs=-1)
        elapsed = time.time() - start_time
        mem_after = self.get_memory_usage()
        
        metrics = {
            'elapsed_time': elapsed,
            'memory_used_mb': mem_after - mem_before,
            'algorithm': result.algorithm,
            'n_clusters': int(result.n_clusters),
            'silhouette_score': float(result.silhouette),
            'calinski_harabasz': float(result.calinski_harabasz),
            'davies_bouldin': float(result.davies_bouldin),
        }
        
        print(f"  ⏱️  Temps: {elapsed:.2f}s")
        print(f"  🧠 Mémoire: {metrics['memory_used_mb']:.1f} MB")
        print(f"  🎯 Algorithme: {metrics['algorithm']}")
        print(f"  📦 Clusters: {metrics['n_clusters']}")
        print(f"  📈 Silhouette: {metrics['silhouette_score']:.3f}")
        
        self.results['tests']['clustering_parallel'] = metrics
        return result
    
    def benchmark_archetype_matching(self, df_features, labels):
        """Benchmark matching des archétypes"""
        print("\n" + "="*70)
        print("BENCHMARK: Archetype Matching")
        print("="*70)
        
        matcher = HierarchicalArchetypeMatcher()
        df_features['cluster_id'] = labels
        
        mem_before = self.get_memory_usage()
        start_time = time.time()
        
        matches = []
        for _, row in df_features.iterrows():
            match_result = matcher.match_player(row)
            matches.append({
                'archetype_id': match_result[0],
                'confidence': match_result[1],
                'level': match_result[2]
            })
        
        elapsed = time.time() - start_time
        mem_after = self.get_memory_usage()
        
        matches_df = pd.DataFrame(matches)
        
        # Stats
        level_counts = matches_df['level'].value_counts().to_dict()
        arch_counts = matches_df['archetype_id'].value_counts().to_dict()
        
        result = {
            'elapsed_time': elapsed,
            'memory_used_mb': mem_after - mem_before,
            'players_matched': len(matches_df),
            'archetypes_found': len(arch_counts),
            'levels_distribution': level_counts,
            'top_archetypes': dict(list(arch_counts.items())[:5])
        }
        
        print(f"  ⏱️  Temps: {elapsed:.2f}s")
        print(f"  🧠 Mémoire: {result['memory_used_mb']:.1f} MB")
        print(f"  👥 Joueurs matchés: {result['players_matched']}")
        print(f"  🎭 Archétypes: {result['archetypes_found']}")
        print(f"  📊 Distribution niveaux: {level_counts}")
        
        self.results['tests']['archetype_matching'] = result
        return matches_df
    
    def calculate_speedup(self):
        """Calcule le speedup parallèle vs séquentiel"""
        seq_time = self.results['tests']['clustering_sequential']['elapsed_time']
        par_time = self.results['tests']['clustering_parallel']['elapsed_time']
        
        speedup = seq_time / par_time if par_time > 0 else 0
        reduction = ((seq_time - par_time) / seq_time * 100) if seq_time > 0 else 0
        
        self.results['performance_analysis'] = {
            'sequential_time': seq_time,
            'parallel_time': par_time,
            'speedup': speedup,
            'time_reduction_percent': reduction
        }
        
        print("\n" + "="*70)
        print("ANALYSE PERFORMANCE")
        print("="*70)
        print(f"  ⏱️  Séquentiel: {seq_time:.2f}s")
        print(f"  ⚡ Parallèle: {par_time:.2f}s")
        print(f"  🚀 Speedup: {speedup:.2f}x")
        print(f"  📉 Réduction: {reduction:.1f}%")
    
    def run_full_benchmark(self, data_path=None):
        """Exécute benchmark complet"""
        print("\n" + "="*70)
        print("NBA-23 BENCHMARK COMPLET")
        print("="*70)
        print(f"Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Python: {sys.version.split()[0]}")
        print(f"CPU Cores: {psutil.cpu_count()}")
        
        # Chargement données
        if data_path is None:
            data_path = 'data/silver/players_advanced/players_enriched_final.json'
        
        print(f"\n📂 Chargement données: {data_path}")
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df_raw = pd.DataFrame(data['data'])
            print(f"   {len(df_raw)} joueurs chargés")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            print("   Utilisation de données synthétiques...")
            df_raw = self._create_synthetic_data()
        
        # Benchmark 1: Feature Engineering
        df_features, feature_cols = self.benchmark_feature_engineering(df_raw)
        
        # Préparation données clustering
        X = df_features[feature_cols].values
        k_range = range(6, 12)
        
        # Benchmark 2: Clustering Séquentiel
        result_seq = self.benchmark_clustering_sequential(X, k_range)
        
        # Benchmark 3: Clustering Parallèle
        result_par = self.benchmark_clustering_parallel(X, k_range)
        
        # Benchmark 4: Archetype Matching
        matches_df = self.benchmark_archetype_matching(df_features, result_par.labels)
        
        # Analyse performance
        self.calculate_speedup()
        
        # Sauvegarde résultats
        self.save_results()
        
        print("\n" + "="*70)
        print("BENCHMARK TERMINÉ")
        print("="*70)
        
        return self.results
    
    def _create_synthetic_data(self, n_players=500):
        """Crée données synthétiques si vraies données non disponibles"""
        np.random.seed(42)
        return pd.DataFrame({
            'player_id': range(1, n_players + 1),
            'player_name': [f'Player {i}' for i in range(1, n_players + 1)],
            'height_cm': np.random.normal(200, 10, n_players),
            'weight_kg': np.random.normal(100, 15, n_players),
            'pts': np.random.exponential(1000, n_players),
            'reb': np.random.exponential(500, n_players),
            'ast': np.random.exponential(300, n_players),
            'stl': np.random.exponential(80, n_players),
            'blk': np.random.exponential(50, n_players),
            'minutes': np.random.exponential(1500, n_players),
            'games_played': np.random.randint(40, 82, n_players),
            'fga': np.random.exponential(800, n_players),
            'fgm': np.random.exponential(400, n_players),
            'fg3a': np.random.exponential(200, n_players),
            'fta': np.random.exponential(300, n_players),
        })
    
    def save_results(self):
        """Sauvegarde résultats"""
        output_dir = Path('reports')
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f'nba23_benchmark_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Résultats sauvegardés: {output_file}")


def main():
    """Point d'entrée"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NBA-23 Benchmark')
    parser.add_argument('--data', type=str, default=None,
                       help='Chemin vers données (JSON)')
    parser.add_argument('--synthetic', action='store_true',
                       help='Utiliser données synthétiques')
    
    args = parser.parse_args()
    
    benchmark = NBABenchmark()
    
    if args.synthetic:
        # Force données synthétiques
        results = benchmark.run_full_benchmark(data_path='__synthetic__')
    else:
        results = benchmark.run_full_benchmark(data_path=args.data)
    
    return results


if __name__ == "__main__":
    main()
