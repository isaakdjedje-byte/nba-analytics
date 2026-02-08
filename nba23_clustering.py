#!/usr/bin/env python3
"""
NBA-23: Script principal refactorisé
Clustering des archétypes de joueurs - Version standardisée
"""

from src.ml.archetype import (
    ArchetypeFeatureEngineer,
    AutoClustering,
    HierarchicalArchetypeMatcher,
    NBA23ArchetypePipeline
)

import pandas as pd
import json
from datetime import datetime
import os


class NBA23PipelineRunner:
    """Wrapper simple pour exécuter NBA-23"""
    
    def __init__(self):
        self.engineer = ArchetypeFeatureEngineer()
        self.clusterer = AutoClustering(random_state=42)
        self.matcher = HierarchicalArchetypeMatcher()
    
    def run(self, data_path=None, use_parallel=True, use_feature_selection=False):
        """
        Exécute le pipeline complet
        
        Args:
            data_path: Chemin vers données (défaut: data/silver/players_advanced/players_enriched_final.json)
            use_parallel: Si True, utilise clustering parallèle
            use_feature_selection: Si True, active feature selection
        """
        if data_path is None:
            data_path = 'data/silver/players_advanced/players_enriched_final.json'
        
        print("=" * 70)
        print("NBA-23: Player Archetypes Clustering v3.1")
        print("=" * 70)
        print("Démarrage: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        print()
        
        # Étape 1: Chargement
        print("Étape 1: Chargement des données...")
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        df_raw = pd.DataFrame(data['data'])
        print("   {} joueurs chargés".format(len(df_raw)))
        
        # Étape 2: Features
        print("\nÉtape 2: Feature Engineering...")
        df_features, feature_cols, metadata = \
            self.engineer.prepare_for_clustering(df_raw, min_games=10)
        
        print("   {} joueurs valides".format(len(df_features)))
        print("   {} features créées".format(len(feature_cols)))
        
        # Étape 3: Clustering
        print("\nÉtape 3: Clustering...")
        X = df_features[feature_cols].values
        
        n_jobs = -1 if use_parallel else 1
        feature_names = feature_cols if use_feature_selection else None
        
        result = self.clusterer.fit(
            X, 
            k_range=range(6, 12),
            min_cluster_size=100,
            n_jobs=n_jobs,
            use_feature_selection=use_feature_selection,
            feature_names=feature_names
        )
        
        print("   Algorithme: {}".format(result.algorithm))
        print("   Clusters: {}".format(result.n_clusters))
        print("   Silhouette: {:.3f}".format(result.silhouette))
        
        # Étape 4: Matching hiérarchique
        print("\nÉtape 4: Matching hiérarchique...")
        df_features['cluster_id'] = result.labels
        
        matches = []
        for _, row in df_features.iterrows():
            match_result = self.matcher.match_player(row)
            matches.append({
                'archetype_id': match_result[0],
                'confidence': match_result[1],
                'level': match_result[2]
            })
        
        matches_df = pd.DataFrame(matches)
        df_clustered = pd.concat([df_features.reset_index(drop=True), matches_df], axis=1)
        
        print("   {} archétypes identifiés".format(matches_df['archetype_id'].nunique()))
        
        # Distribution des niveaux
        level_counts = matches_df['level'].value_counts()
        print("\n   Distribution:")
        for level, count in level_counts.items():
            print("      {}: {} joueurs ({:.1f}%)".format(
                level, count, count/len(matches_df)*100))
        
        # Étape 5: Export
        print("\nÉtape 5: Export...")
        os.makedirs('data/gold/player_archetypes', exist_ok=True)
        os.makedirs('reports', exist_ok=True)
        
        df_clustered.to_parquet(
            'data/gold/player_archetypes/player_archetypes.parquet',
            index=False
        )
        print("   player_archetypes.parquet")
        
        # Sauvegarde modèle
        self.clusterer.save(
            'data/gold/player_archetypes/clustering_model.joblib'
        )
        print("   clustering_model.joblib")
        
        # Rapport
        report = {
            'timestamp': datetime.now().isoformat(),
            'nba23_version': '3.1',
            'status': 'COMPLETED',
            'config': {
                'parallel': use_parallel,
                'feature_selection': use_feature_selection
            },
            'data': {
                'total_players': len(df_raw),
                'players_clustered': len(df_clustered)
            },
            'clustering': {
                'algorithm': result.algorithm,
                'n_clusters': int(result.n_clusters),
                'silhouette_score': float(result.silhouette),
                'calinski_harabasz': float(result.calinski_harabasz),
                'davies_bouldin': float(result.davies_bouldin)
            },
            'archetypes': {
                'n_archetypes': matches_df['archetype_id'].nunique(),
                'level_distribution': level_counts.to_dict()
            }
        }
        
        with open('reports/nba23_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print("   reports/nba23_report.json")
        
        print("\n" + "=" * 70)
        print("Terminé avec succès!")
        print("=" * 70)
        
        return df_clustered, report


def main():
    """Point d'entrée"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NBA-23: Player Archetypes Clustering v3.1')
    parser.add_argument('--data', type=str, default=None,
                       help='Chemin vers données JSON')
    parser.add_argument('--sequential', action='store_true',
                       help='Désactive la parallélisation')
    parser.add_argument('--feature-selection', action='store_true',
                       help='Active la sélection de features')
    parser.add_argument('--pipeline', action='store_true',
                       help='Utilise le pipeline complet (NBA23ArchetypePipeline)')
    
    args = parser.parse_args()
    
    if args.pipeline:
        # Utilise le pipeline complet avec validation
        print("Utilisation du pipeline complet avec validation...")
        pipeline = NBA23ArchetypePipeline(data_path=args.data)
        report = pipeline.run(
            validate=True,
            min_games=10
        )
        print("\nRésumé:")
        print("  Joueurs: {}".format(report['data']['players_clustered']))
        print("  Clusters: {}".format(report['clustering']['n_clusters']))
        if report.get('validation'):
            print("  Précision: {:.1f}%".format(
                report['validation']['accuracy'] * 100))
    else:
        # Utilise le runner simple
        runner = NBA23PipelineRunner()
        df_clustered, report = runner.run(
            data_path=args.data,
            use_parallel=not args.sequential,
            use_feature_selection=args.feature_selection
        )


if __name__ == "__main__":
    main()
