"""
NBA-19 Ultimate Discovery System

Systeme de discovery complet pour trouver les equipes des joueurs NBA.
Version iterative (test sur 100 joueurs puis expansion).

Modules:
    - config: Configuration centralisee
    - circuit_breaker: Protection contre les erreurs en cascade
    - rate_limiter: Gestion du rate limiting API
    - checkpoint_manager: Reprise d'execution
    - phase1_pre_validation: Segmentation des joueurs
    - phase2_discovery_engine: Discovery via API
    - orchestrator: Orchestration complete
"""

from .config import CONFIG, QualityTier, DiscoverySegment
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpen
from .rate_limiter import RateLimiter, AdaptiveRateLimiter
from .checkpoint_manager import CheckpointManager, RecoveryManager

__version__ = "2.0.0"
__all__ = [
    'CONFIG',
    'QualityTier',
    'DiscoverySegment',
    'CircuitBreaker',
    'CircuitBreakerOpen',
    'RateLimiter',
    'AdaptiveRateLimiter',
    'CheckpointManager',
    'RecoveryManager'
]
