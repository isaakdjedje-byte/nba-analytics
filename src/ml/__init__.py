"""
Module ML - Modèles de Machine Learning pour NBA Analytics

Ce module contient:
- Classification (prédiction gagnant/perdant)
- Régression (prédiction score exact)
- Clustering (profils de joueurs)
- Enrichment (enrichissement de données)
"""

# Modèles ML
from .classification_model import ClassificationModel
from .regression_model import RegressionModel
from .clustering_model import ClusteringModel
from .feature_engineering import FeatureEngineer

# Enrichissement
from .enrichment import (
    PositionPredictor,
    CareerStatusInferencer,
    SmartEnricher,
    EnrichmentResult
)

__all__ = [
    # Modèles ML
    'ClassificationModel',
    'RegressionModel',
    'ClusteringModel',
    'FeatureEngineer',
    # Enrichissement
    'PositionPredictor',
    'CareerStatusInferencer',
    'SmartEnricher',
    'EnrichmentResult'
]
