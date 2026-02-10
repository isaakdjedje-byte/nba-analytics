"""
Module ML - Modèles de Machine Learning pour NBA Analytics

Ce module contient:
- Classification (prédiction gagnant/perdant)
- Régression (prédiction score exact)
- Clustering (profils de joueurs)
- Enrichment (enrichissement de données)
"""

# Modèles ML (imports optionnels pour éviter dépendances circulaires)
try:
    from .classification_model import ClassificationModel
    from .feature_engineering import FeatureEngineer
    __all__ = ['ClassificationModel', 'FeatureEngineer']
except ImportError:
    __all__ = []

# Enrichissement (imports optionnels)
try:
    from .enrichment import (
        PositionPredictor,
        CareerStatusInferencer,
        SmartEnricher,
        EnrichmentResult
    )
    __all__.extend(['PositionPredictor', 'CareerStatusInferencer', 'SmartEnricher', 'EnrichmentResult'])
except ImportError:
    pass
