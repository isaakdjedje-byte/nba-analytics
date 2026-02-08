"""
NBA-19 Ultimate Discovery System - Configuration
Configuration complete pour le systeme de discovery ultime
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import os


class QualityTier(Enum):
    """Niveaux de qualite des donnees"""
    GOLD = "gold"       # API verifiee + cross-validee
    SILVER = "silver"   # API avec incertitudes
    BRONZE = "bronze"   # Inference/heuristique
    UNKNOWN = "unknown" # Pas de donnees trouvees


class DiscoverySegment(Enum):
    """Segments de discovery"""
    SEGMENT_A = "segment_a"  # api_cached + roster + csv (GOLD)
    SEGMENT_B = "segment_b"  # imputed avec season data (SILVER)
    SEGMENT_C = "segment_c"  # imputed sans season data (BRONZE)


@dataclass
class DiscoveryConfig:
    """Configuration principale du discovery"""
    
    # === Parametres API ===
    REQUEST_DELAY_SECONDS: float = 2.0  # 1 req / 2 sec = 30 req/min
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_BASE: float = 2.0  # 2s, 4s, 8s
    
    # === Rate Limiting Global ===
    RATE_LIMIT_PAUSE_AFTER: int = 100  # Pause apres 100 requetes
    RATE_LIMIT_PAUSE_DURATION: int = 30  # 30 secondes de pause
    MAX_WORKERS: int = 1  # Sequentiel pour respecter rate limit global
    
    # === Checkpoints ===
    CHECKPOINT_INTERVAL: int = 50  # Toutes les 50 joueurs
    CHECKPOINT_DIR: str = "logs/nba19_discovery/checkpoints"
    
    # === Circuit Breaker ===
    CIRCUIT_BREAKER_THRESHOLD: float = 0.05  # 5% erreurs
    CIRCUIT_BREAKER_TIMEOUT: int = 300  # 5 minutes
    
    # === Fichiers Source ===
    PLAYERS_FILE: str = "data/silver/players_advanced/players.json"
    PLAYERS_ENRICHED_FILE: str = "data/silver/players_advanced/players_enriched_final.json"
    ROSTERS_DIR: str = "data/raw/rosters/historical"
    
    # === Output ===
    OUTPUT_DIR: str = "data/gold/nba19"
    LOGS_DIR: str = "logs/nba19_discovery"
    
    # === Saisons ===
    SEASONS: List[str] = field(default_factory=lambda: [
        "2018-19", "2019-20", "2020-21", "2021-22",
        "2022-23", "2023-24", "2024-25"
    ])
    
    # === Qualite ===
    QUALITY_THRESHOLDS: Dict[str, float] = field(default_factory=lambda: {
        "gold_min_confidence": 0.95,
        "silver_min_confidence": 0.70,
        "bronze_min_confidence": 0.40
    })
    
    def __post_init__(self):
        # Creer les repertoires necessaires
        os.makedirs(self.CHECKPOINT_DIR, exist_ok=True)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.LOGS_DIR, exist_ok=True)
        os.makedirs(f"{self.LOGS_DIR}/errors", exist_ok=True)
        os.makedirs(f"{self.LOGS_DIR}/metrics", exist_ok=True)


# Instance globale
CONFIG = DiscoveryConfig()
