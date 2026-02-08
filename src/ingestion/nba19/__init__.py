"""
NBA-19: Team Performance Data Product - Ingestion Module

Module d'ingestion des données pour NBA-19 avec:
- Fetching des rosters historiques (2018-2024)
- Auto-discovery des joueurs historiques
- Gestion des checkpoints
"""

from .config import CONFIG
from .checkpoint_manager import CheckpointManager, FetchingStats
from .fetch_historical_rosters import HistoricalRosterFetcher
from .auto_discovery import PlayerTeamDiscovery

__all__ = [
    'CONFIG',
    'CheckpointManager',
    'FetchingStats',
    'HistoricalRosterFetcher',
    'PlayerTeamDiscovery'
]
