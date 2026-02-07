"""
Module d'enrichissement ML pour données joueurs NBA.

Permet d'enrichir les datasets avec des métadonnées prédites:
- Position (via K-Means clustering)
- Statut de carrière (actif/inactif)
- Team ID (via API)

Usage:
    from ml.enrichment import SmartEnricher
    
    enricher = SmartEnricher()
    enriched_players = enricher.enrich_dataset(players)
"""

from .position_predictor import PositionPredictor, CareerStatusInferencer
from .smart_enricher import SmartEnricher, EnrichmentResult

__all__ = [
    'PositionPredictor',
    'CareerStatusInferencer', 
    'SmartEnricher',
    'EnrichmentResult'
]
