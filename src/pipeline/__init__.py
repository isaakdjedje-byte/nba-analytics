"""
Pipeline Orchestration - Coordination Bronze → Silver → Gold.

Ce module orchestre l'exécution complète du pipeline de données.
"""

from .players_pipeline import PlayersPipeline

__all__ = ['PlayersPipeline']
