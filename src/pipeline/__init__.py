"""
Pipeline Orchestration - Coordination Bronze → Silver → Gold.

Ce module orchestre l'exécution complète du pipeline de données.

NBA-20: Transformation des matchs (GamesTransformer)
NBA-21: Feature Engineering (FeatureEngineer - ml/feature_engineering.py)
NBA-22: Classification (ClassificationModel - ml/classification_model.py)
"""

from .players_pipeline import PlayersPipeline
from .nba20_transform_games import GamesTransformer
from .unified_ml_pipeline import NBAMLPipeline

__all__ = ['PlayersPipeline', 'GamesTransformer', 'NBAMLPipeline']
