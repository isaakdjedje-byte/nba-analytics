#!/usr/bin/env python3
"""
NBA-23: Tests Unitaires Complets
Teste tous les composants du clustering d'archétypes
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Ajoute src au path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ml.archetype.feature_engineering import ArchetypeFeatureEngineer
from ml.archetype.auto_clustering import AutoClustering, ClusteringResult
from ml.archetype.archetype_matcher import HierarchicalArchetypeMatcher, ArchetypeDefinition


class TestArchetypeFeatureEngineer:
    """Tests pour le feature engineering"""
    
    @pytest.fixture
    def sample_data(self):
        """Données de test représentatives"""
        return pd.DataFrame({
            'player_id': [1, 2, 3, 4, 5],
            'player_name': ['Player A', 'Player B', 'Player C', 'Player D', 'Player E'],
            'height_cm': [201, 198, 211, 185, 206],
            'weight_kg': [102, 95, 115, 88, 108],
            'pts': [1500, 800, 400, 1200, 600],
            'reb': [400, 600, 900, 350, 750],
            'ast': [300, 200, 100, 450, 150],
            'stl': [80, 120, 40, 90, 60],
            'blk': [30, 80, 200, 25, 150],
            'minutes': [2000, 1800, 1500, 2200, 1600],
            'games_played': [70, 65, 50, 72, 55],
            'fga': [1200, 600, 300, 1000, 400],
            'fgm': [550, 280, 140, 480, 190],
            'fg3a': [400, 200, 20, 350, 50],
            'fta': [300, 150, 80, 280, 100],
            'per': [22.5, 18.3, 15.2, 20.1, 16.8]
        })
    
    def test_inheritance_base_feature_engineer(self):
        """Vérifie que ArchetypeFeatureEngineer hérite de BaseFeatureEngineer"""
        from ml.base.base_feature_engineer import BaseFeatureEngineer
        engineer = ArchetypeFeatureEngineer()
        assert isinstance(engineer, BaseFeatureEngineer)
        assert hasattr(engineer, 'calculate_ts_pct')
        assert hasattr(engineer, 'normalize_per_36')
    
    def test_engineer_features_creates_expected_features(self, sample_data):
        """Vérifie création des features attendues"""
        engineer = ArchetypeFeatureEngineer()
        df_result = engineer.engineer_features(sample_data)
        
        # Features physiques
        assert 'bmi' in df_result.columns
        assert 'wingspan_estimated' in df_result.columns
        
        # Features offensives
        assert 'pts_per_36' in df_result.columns
        assert 'ts_pct' in df_result.columns
        assert 'efg_pct' in df_result.columns
        
        # Features défensives
        assert 'reb_per_36' in df_result.columns
        assert 'stl_per_36' in df_result.columns
        assert 'blk_per_36' in df_result.columns
        
        # Features avancées NBA-23
        assert 'ast_pct' in df_result.columns
        assert 'stl_pct' in df_result.columns
        assert 'vorp' in df_result.columns
    
    def test_normalize_per_36_calculations(self, sample_data):
        """Vérifie calcul de normalisation par 36 minutes"""
        engineer = ArchetypeFeatureEngineer()
        df_result = engineer.engineer_features(sample_data)
        
        # Vérifie que pts_per_36 = (pts / minutes) * 36
        expected_pts_36 = (sample_data['pts'] / sample_data['minutes']) * 36
        pd.testing.assert_series_equal(
            df_result['pts_per_36'].reset_index(drop=True),
            expected_pts_36.reset_index(drop=True),
            check_names=False
        )
    
    def test_prepare_for_clustering_filters(self, sample_data):
        """Vérifie filtrage des joueurs"""
        engineer = ArchetypeFeatureEngineer()
        df_clean, features, metadata = engineer.prepare_for_clustering(
            sample_data, min_games=10
        )
        
        # Tous les joueurs devraient passer (min_games=10)
        assert len(df_clean) == len(sample_data)
        assert len(features) > 0
        assert 'player_id' in metadata or 'player_name' in metadata
    
    def test_feature_registry(self, sample_data):
        """Vérifie enregistrement des features"""
        engineer = ArchetypeFeatureEngineer()
        engineer.engineer_features(sample_data)
        
        # Vérifie que des features ont été enregistrées
        doc = engineer.get_feature_documentation()
        assert len(doc) > 0
        assert 'bmi' in doc['feature_name'].values


class TestAutoClustering:
    """Tests pour le clustering automatique"""
    
    @pytest.fixture
    def sample_features(self):
        """Features de test"""
        np.random.seed(42)
        X = np.random.randn(200, 15)
        # Crée 3 clusters artificiels
        X[:70] += np.array([2, 2] + [0]*13)
        X[70:140] += np.array([0, 0, 2, 2] + [0]*11)
        X[140:] += np.array([-2, -2] + [0]*13)
        return X
    
    def test_clustering_returns_valid_result(self, sample_features):
        """Vérifie que le clustering retourne un résultat valide"""
        clusterer = AutoClustering(random_state=42)
        result = clusterer.fit(sample_features, k_range=range(3, 6), n_jobs=1)
        
        assert isinstance(result, ClusteringResult)
        assert result.n_clusters >= 3
        assert result.n_clusters <= 5
        assert -1 <= result.silhouette <= 1
        assert result.calinski_harabasz > 0
        assert result.davies_bouldin > 0
        assert len(result.labels) == len(sample_features)
    
    def test_parallel_clustering(self, sample_features):
        """Vérifie que la parallélisation fonctionne"""
        clusterer = AutoClustering(random_state=42)
        
        # Test avec n_jobs=-1 (tous les cores)
        result = clusterer.fit(sample_features, k_range=range(3, 6), n_jobs=-1)
        assert result is not None
        assert len(result.labels) == len(sample_features)
    
    def test_feature_selection_option(self, sample_features):
        """Vérifie feature selection optionnelle"""
        clusterer = AutoClustering(random_state=42)
        feature_names = [f'feature_{i}' for i in range(sample_features.shape[1])]
        
        # Avec feature selection
        result = clusterer.fit(
            sample_features, 
            k_range=range(3, 5),
            use_feature_selection=True,
            feature_names=feature_names
        )
        assert result is not None
    
    def test_clustering_metrics_consistency(self, sample_features):
        """Vérifie cohérence des métriques"""
        clusterer = AutoClustering(random_state=42)
        result = clusterer.fit(sample_features, k_range=range(3, 6), n_jobs=1)
        
        # Silhouette doit être entre -1 et 1
        assert -1 <= result.silhouette <= 1
        
        # Calinski-Harabasz doit être positive
        assert result.calinski_harabasz > 0
        
        # Davies-Bouldin doit être positive
        assert result.davies_bouldin > 0
        
        # Tous les échantillons doivent avoir un label
        assert len(result.labels) == len(sample_features)
        assert all(label >= -1 for label in result.labels)  # -1 = outlier


class TestHierarchicalArchetypeMatcher:
    """Tests pour le matching hiérarchique des archétypes"""
    
    @pytest.fixture
    def sample_player_data(self):
        """Données d'un joueur type"""
        return pd.Series({
            'per': 26.0,
            'pts_per_36': 28.0,
            'ts_pct': 0.60,
            'usg_pct': 32.0,
            'ast_per_36': 8.0,
            'stl_per_36': 1.5,
            'defensive_activity': 3.0,
            'versatility_score': 0.8
        })
    
    def test_matcher_initialization(self):
        """Vérifie initialisation du matcher"""
        matcher = HierarchicalArchetypeMatcher()
        assert len(matcher.ARCHETYPES) > 0
        assert 'ELITE_SCORER' in matcher.ARCHETYPES
    
    def test_match_player_returns_tuple(self, sample_player_data):
        """Vérifie que match_player retourne un tuple"""
        matcher = HierarchicalArchetypeMatcher()
        result = matcher.match_player(sample_player_data)
        
        assert isinstance(result, tuple)
        assert len(result) == 3
        archetype_id, confidence, level = result
        assert isinstance(archetype_id, str)
        assert isinstance(confidence, float)
        assert isinstance(level, str)
    
    def test_elite_player_matches_elite_level(self, sample_player_data):
        """Vérifie qu'un joueur ELITE est bien matché comme tel"""
        matcher = HierarchicalArchetypeMatcher()
        result = matcher.match_player(sample_player_data)
        
        archetype_id, confidence, level = result
        # Un joueur avec PER 26 devrait être ELITE
        assert level == 'ELITE'
        assert confidence > 0.5


class TestIntegration:
    """Tests d'intégration end-to-end"""
    
    @pytest.fixture
    def full_pipeline_data(self):
        """Données complètes pour test pipeline"""
        np.random.seed(42)
        n_players = 50
        
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
    
    def test_full_pipeline_execution(self, full_pipeline_data):
        """Test pipeline complet: Features → Clustering → Matching"""
        # Étape 1: Feature Engineering
        engineer = ArchetypeFeatureEngineer()
        df_features, feature_cols, metadata = engineer.prepare_for_clustering(
            full_pipeline_data, min_games=10
        )
        assert len(df_features) > 0
        assert len(feature_cols) > 0
        
        # Étape 2: Clustering
        X = df_features[feature_cols].values
        clusterer = AutoClustering(random_state=42)
        result = clusterer.fit(X, k_range=range(4, 7), n_jobs=1)
        assert result is not None
        assert len(result.labels) == len(df_features)
        
        # Étape 3: Matching
        matcher = HierarchicalArchetypeMatcher()
        df_features['cluster_id'] = result.labels
        
        matches = []
        for _, row in df_features.iterrows():
            match_result = matcher.match_player(row)
            matches.append({
                'archetype_id': match_result[0],
                'confidence': match_result[1],
                'level': match_result[2]
            })
        
        matches_df = pd.DataFrame(matches)
        assert len(matches_df) == len(df_features)
        assert matches_df['archetype_id'].nunique() > 0
    
    def test_pipeline_with_parallel_clustering(self, full_pipeline_data):
        """Test pipeline avec clustering parallèle"""
        engineer = ArchetypeFeatureEngineer()
        df_features, feature_cols, _ = engineer.prepare_for_clustering(
            full_pipeline_data, min_games=10
        )
        
        X = df_features[feature_cols].values
        clusterer = AutoClustering(random_state=42)
        
        # Clustering parallèle
        result = clusterer.fit(X, k_range=range(4, 7), n_jobs=-1)
        assert result is not None
        assert result.silhouette > -1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
