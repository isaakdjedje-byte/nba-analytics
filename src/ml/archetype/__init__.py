#!/usr/bin/env python3
"""
NBA-23: Player Archetypes Clustering Module - Version 3.1 Refactorisé

Module complet pour le clustering des archétypes de joueurs NBA avec:
- Feature engineering avancé (39+ features) - Hérite de BaseFeatureEngineer
- Matching hiérarchique des archétypes (ELITE > STARTER > ROLE > BENCH)
- Validation avec ground truth (41+ joueurs)
- Intégration NBA-22
- ZERO redondance de code
"""

import pandas as pd
import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Version du module
__version__ = '3.1.0'
__author__ = 'NBA Analytics Team'

# Imports des modules
from src.ml.archetype.feature_engineering import ArchetypeFeatureEngineer
from src.ml.archetype.auto_clustering import AutoClustering
from src.ml.archetype.archetype_matcher import HierarchicalArchetypeMatcher
from src.ml.archetype.validation import ArchetypeValidator, quick_validation
from src.ml.archetype.nba22_integration import ArchetypeTeamFeatures

__all__ = [
    # Classes principales
    'ArchetypeFeatureEngineer',
    'AutoClustering',
    'HierarchicalArchetypeMatcher',
    'ArchetypeValidator',
    'ArchetypeTeamFeatures',
    'NBA23ArchetypePipeline',
    
    # Fonctions utilitaires
    'quick_validation',
    
    # Métadonnées
    '__version__',
    '__author__'
]


class NBA23ArchetypePipeline:
    """
    Pipeline complet NBA-23: Clustering des archétypes de joueurs
    Version refactorisée utilisant HierarchicalArchetypeMatcher
    """
    
    def __init__(self, data_path: str = None, output_path: str = None):
        self.data_path = data_path or "data/silver/players_advanced/players_enriched_final.json"
        self.output_path = output_path or "data/gold/player_archetypes/"
        self.report_path = "reports/"
        
        # Composants
        self.feature_engineer = ArchetypeFeatureEngineer()
        self.clusterer = AutoClustering(random_state=42)
        self.matcher = HierarchicalArchetypeMatcher()
        self.validator = ArchetypeValidator()  # NOUVEAU: Validation intégrée
        
        # Données
        self.df_raw = None
        self.df_features = None
        self.df_clustered = None
        self.clustering_result = None
        self.validation_result = None  # NOUVEAU: Stockage résultats validation
        
        Path(self.output_path).mkdir(parents=True, exist_ok=True)
        Path(self.report_path).mkdir(parents=True, exist_ok=True)
    
    def run(self, k_range: range = range(6, 13),
            min_cluster_size: int = 100,
            min_games: int = 10,
            validate: bool = True) -> dict:  # NOUVEAU: Paramètre validation
        """
        Exécute le pipeline complet NBA-23
        
        Args:
            k_range: Range de clusters à tester
            min_cluster_size: Taille minimum d'un cluster
            min_games: Nombre minimum de matchs
            validate: Si True, valide avec ground truth
        
        Returns:
            dict: Résultats et métriques
        """
        print("=" * 70)
        print("NBA-23: Player Archetypes Clustering v3.1")
        print("=" * 70)
        print("Démarrage: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        print()
        
        # Étape 1: Chargement des données
        self._load_data()
        
        # Étape 2: Feature Engineering
        self._engineer_features(min_games)
        
        # Étape 3: Clustering
        self._perform_clustering(k_range, min_cluster_size)
        
        # Étape 4: Matching hiérarchique des archétypes
        self._match_archetypes()
        
        # Étape 5: Validation avec ground truth (NOUVEAU)
        if validate:
            self._validate_results()
        
        # Étape 6: Export des résultats
        self._export_results()
        
        # Étape 7: Génération du rapport
        report = self._generate_report()
        
        print()
        print("=" * 70)
        print("Pipeline NBA-23 terminé avec succès!")
        print("=" * 70)
        
        return report
    
    def _load_data(self):
        """Charge les données NBA-18"""
        print("Étape 1: Chargement des données...")
        
        try:
            # Charge JSON avec structure imbriquée
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extrait les données
            if 'data' in data:
                self.df_raw = pd.DataFrame(data['data'])
                print("   Structure imbriquée détectée")
            else:
                self.df_raw = pd.DataFrame(data)
            
            print("   {} joueurs chargés".format(len(self.df_raw)))
            
        except Exception as e:
            print("   Erreur chargement: {}".format(e))
            raise
    
    def _engineer_features(self, min_games: int):
        """Crée les features avancées"""
        print("\nÉtape 2: Feature Engineering...")
        
        self.df_features, feature_cols, metadata_cols = \
            self.feature_engineer.prepare_for_clustering(self.df_raw, min_games)
        
        self.feature_cols = feature_cols
        self.metadata_cols = metadata_cols
        
        print("   {} joueurs avec données complètes".format(len(self.df_features)))
        print("   {} features créées".format(len(feature_cols)))
        
        # Sauvegarde features
        self.df_features.to_parquet(
            "{}player_features.parquet".format(self.output_path),
            index=False
        )
        
        # Stats features
        print("\n   Top 5 features par variance:")
        X = self.df_features[feature_cols].values
        variances = np.var(X, axis=0)
        top_var_idx = np.argsort(variances)[-5:][::-1]
        for idx in top_var_idx:
            print("      {}: var={:.2f}".format(feature_cols[idx], variances[idx]))
    
    def _perform_clustering(self, k_range: range, min_cluster_size: int):
        """Exécute le clustering automatique"""
        print("\nÉtape 3: Clustering...")
        
        # Prépare les données
        X = self.df_features[self.feature_cols].values
        
        # Clustering
        self.clustering_result = self.clusterer.fit(
            X, 
            k_range=k_range,
            min_cluster_size=min_cluster_size
        )
        
        print("\n   Meilleur algorithme: {}".format(self.clustering_result.algorithm))
        print("   Nombre de clusters: {}".format(self.clustering_result.n_clusters))
        print("   Silhouette Score: {:.3f}".format(self.clustering_result.silhouette))
        print("   Calinski-Harabasz: {:.0f}".format(self.clustering_result.calinski_harabasz))
        print("   Davies-Bouldin: {:.3f}".format(self.clustering_result.davies_bouldin))
        
        # Distribution
        print("\n   Distribution des clusters:")
        for cluster_id, size in sorted(self.clustering_result.cluster_sizes.items()):
            pct = size / len(X) * 100
            if cluster_id == -1:
                print("      Outliers: {} joueurs ({:.1f}%)".format(size, pct))
            else:
                print("      Cluster {}: {} joueurs ({:.1f}%)".format(cluster_id, size, pct))
    
    def _match_archetypes(self):
        """Match les archétypes avec l'algorithme hiérarchique"""
        print("\nÉtape 4: Matching hiérarchique des archétypes...")
        
        # Ajoute les labels au DataFrame
        self.df_features['cluster_id'] = self.clustering_result.labels
        
        # Match chaque joueur avec les archétypes définis
        matches = []
        for idx, row in self.df_features.iterrows():
            match_result = self.matcher.match_player(row)
            matches.append({
                'archetype_id': match_result[0],
                'confidence': match_result[1],
                'level': match_result[2]
            })
        
        # Ajoute les résultats au DataFrame
        matches_df = pd.DataFrame(matches)
        self.df_clustered = pd.concat([self.df_features.reset_index(drop=True), matches_df], axis=1)
        
        # Statistiques
        arch_counts = self.df_clustered['archetype_id'].value_counts()
        print("   {} archétypes identifiés".format(len(arch_counts)))
        
        for arch_id, count in arch_counts.head(10).items():
            arch_def = self.matcher.ARCHETYPES.get(arch_id)
            if arch_def:
                print("      {} ({}): {} joueurs ({:.1f}%)".format(
                    arch_def.name_fr,
                    arch_def.level,
                    count,
                    count / len(self.df_clustered) * 100
                ))
    
    def _validate_results(self):
        """Valide les résultats avec ground truth"""
        print("\nÉtape 5: Validation avec ground truth...")
        
        try:
            self.validation_result = self.validator.validate_with_ground_truth(self.df_clustered)
            
            print("   Précision globale: {:.1f}%".format(self.validation_result['accuracy'] * 100))
            print("   Joueurs validés: {}/{}".format(
                self.validation_result['correct_predictions'],
                self.validation_result['total_ground_truth']
            ))
            
            if 'accuracy_by_level' in self.validation_result:
                print("\n   Précision par niveau:")
                for level, acc in self.validation_result['accuracy_by_level'].items():
                    print("      {}: {:.1f}%".format(level, acc * 100))
            
        except Exception as e:
            print("   Attention: Validation échouée - {}".format(e))
            self.validation_result = None
    
    def _export_results(self):
        """Exporte tous les résultats"""
        print("\nÉtape 6: Export des résultats...")
        
        # 1. Joueurs avec archétypes
        self.df_clustered.to_parquet(
            "{}player_archetypes.parquet".format(self.output_path),
            index=False
        )
        print("   player_archetypes.parquet")
        
        # 2. JSON pour lecture facile
        export_cols = ['player_id', 'player_name', 'cluster_id', 'archetype_id', 'confidence', 'level']
        available_cols = [c for c in export_cols if c in self.df_clustered.columns]
        
        if available_cols:
            json_data = self.df_clustered[available_cols].to_dict('records')
            with open("{}player_archetypes.json".format(self.output_path), 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2)
            print("   player_archetypes.json")
        
        # 3. Rapport d'archétypes
        arch_report = []
        for arch_id in self.df_clustered['archetype_id'].unique():
            arch_def = self.matcher.ARCHETYPES.get(arch_id)
            if arch_def:
                count = (self.df_clustered['archetype_id'] == arch_id).sum()
                arch_report.append({
                    'archetype_id': arch_id,
                    'name': arch_def.name,
                    'name_fr': arch_def.name_fr,
                    'level': arch_def.level,
                    'count': int(count),
                    'percentage': float(count / len(self.df_clustered) * 100)
                })
        
        with open("{}archetype_report.json".format(self.output_path), 'w', encoding='utf-8') as f:
            json.dump(arch_report, f, indent=2)
        print("   archetype_report.json")
        
        # 4. Sauvegarde modèle
        self.clusterer.save("{}clustering_model.joblib".format(self.output_path))
        
        # 5. Validation report (si disponible)
        if self.validation_result:
            with open("{}validation_report.json".format(self.output_path), 'w', encoding='utf-8') as f:
                json.dump(self.validation_result, f, indent=2, default=str)
            print("   validation_report.json")
    
    def _generate_report(self) -> dict:
        """Génère le rapport final"""
        print("\nÉtape 7: Génération du rapport...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'nba23_version': __version__,
            'status': 'COMPLETED',
            'data': {
                'total_players': len(self.df_raw),
                'players_with_features': len(self.df_features),
                'players_clustered': len(self.df_clustered)
            },
            'clustering': {
                'algorithm': self.clustering_result.algorithm,
                'n_clusters': int(self.clustering_result.n_clusters),
                'silhouette_score': float(self.clustering_result.silhouette),
                'calinski_harabasz': float(self.clustering_result.calinski_harabasz),
                'davies_bouldin': float(self.clustering_result.davies_bouldin),
                'cluster_sizes': {str(k): int(v) for k, v in self.clustering_result.cluster_sizes.items()}
            },
            'features': {
                'n_features': len(self.feature_cols),
                'feature_list': self.feature_cols[:20]  # Limite à 20 pour lisibilité
            },
            'validation': self.validation_result if self.validation_result else None,
            'archetypes': {
                'total_defined': len(self.matcher.ARCHETYPES),
                'identified': self.df_clustered['archetype_id'].nunique()
            },
            'files_created': [
                'player_archetypes.parquet',
                'player_archetypes.json',
                'archetype_report.json',
                'clustering_model.joblib',
                'player_features.parquet'
            ]
        }
        
        if self.validation_result:
            report['files_created'].append('validation_report.json')
        
        # Sauvegarde rapport
        with open("{}nba23_report.json".format(self.report_path), 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print("   Rapport sauvegardé: {}nba23_report.json".format(self.report_path))
        
        return report


def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NBA-23: Player Archetypes Clustering v3.1')
    parser.add_argument('--min-clusters', type=int, default=6,
                       help='Nombre minimum de clusters (default: 6)')
    parser.add_argument('--max-clusters', type=int, default=12,
                       help='Nombre maximum de clusters (default: 12)')
    parser.add_argument('--min-cluster-size', type=int, default=100,
                       help='Taille minimum d\'un cluster (default: 100)')
    parser.add_argument('--min-games', type=int, default=10,
                       help='Nombre minimum de matchs (default: 10)')
    parser.add_argument('--no-validation', action='store_true',
                       help='Désactive la validation avec ground truth')
    
    args = parser.parse_args()
    
    # Exécute le pipeline
    pipeline = NBA23ArchetypePipeline()
    report = pipeline.run(
        k_range=range(args.min_clusters, args.max_clusters + 1),
        min_cluster_size=args.min_cluster_size,
        min_games=args.min_games,
        validate=not args.no_validation
    )
    
    # Affiche résumé
    print("\n" + "=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    print("Joueurs traités: {}".format(report['data']['players_clustered']))
    print("Clusters: {}".format(report['clustering']['n_clusters']))
    print("Silhouette Score: {:.3f}".format(report['clustering']['silhouette_score']))
    if report['validation']:
        print("Précision validation: {:.1f}%".format(report['validation']['accuracy'] * 100))


if __name__ == "__main__":
    main()
