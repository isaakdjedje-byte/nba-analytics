"""
Configuration NBA-19 Team Performance Data Product
"""
from dataclasses import dataclass
from typing import List
import os

@dataclass
class NBA19Config:
    """Configuration pour NBA-19"""
    
    # Seasons à fetcher
    SEASONS: List[str] = None
    
    # Rate limiting
    REQUEST_DELAY_SECONDS: float = 2.0  # 1 req / 2 sec = 30 req/min
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_BASE: float = 2.0
    REQUEST_TIMEOUT: int = 30
    
    # Parallelisme
    MAX_WORKERS: int = 1  # Séquentiel pour respecter rate limit global
    
    # Checkpoints
    CHECKPOINT_INTERVAL_TEAMS: int = 5
    CHECKPOINT_FILE: str = "data/raw/rosters/historical/checkpoint.json"
    
    # Output
    OUTPUT_DIR: str = "data/raw/rosters/historical"
    
    # Auto-discovery
    AUTO_DISCOVERY_BATCH_SIZE: int = 50
    AUTO_DISCOVERY_MAX_WORKERS: int = 1  # Séquentiel pour les joueurs
    
    def __post_init__(self):
        if self.SEASONS is None:
            self.SEASONS = [
                "2018-19", "2019-20", "2020-21", "2021-22", 
                "2022-23", "2023-24", "2024-25"
            ]

# Instance globale
CONFIG = NBA19Config()
