"""
Couche Bronze - Données brutes NBA.

Cette couche persiste les données telles qu'elles sont reçues,
sans transformation. Format JSON permissif.
"""

from .players_bronze import PlayersBronze
from .validate_bronze import BronzeValidator

__all__ = ['PlayersBronze', 'BronzeValidator']
