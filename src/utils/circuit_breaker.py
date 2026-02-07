"""
Circuit Breaker Pattern pour gestion API NBA.

Évite de surcharger l'API en cas d'erreurs répétées.
"""

import time
import logging
from enum import Enum
from typing import Callable, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """États du circuit breaker."""
    CLOSED = "closed"      # Fonctionnement normal
    OPEN = "open"          # Circuit ouvert, refus appels
    HALF_OPEN = "half_open"  # Test récupération


class CircuitBreakerOpenError(Exception):
    """Exception levée quand circuit est ouvert."""
    pass


class APICircuitBreaker:
    """
    Circuit breaker pour appels API NBA.
    
    Usage:
        cb = APICircuitBreaker(failure_threshold=5, timeout=60)
        
        try:
            result = cb.call(fetch_player_data, player_id)
        except CircuitBreakerOpenError:
            logger.error("API temporairement indisponible")
    """
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 timeout: int = 60,
                 half_open_max_calls: int = 3):
        """
        Initialise le circuit breaker.
        
        Args:
            failure_threshold: Nb d'échecs avant ouverture
            timeout: Temps avant tentative récupération (s)
            half_open_max_calls: Nb appels en mode half-open
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.half_open_calls = 0
        
        # Stats
        self.success_count = 0
        self.total_calls = 0
        
    def _on_success(self):
        """Appelé quand fonction réussit."""
        self.failure_count = 0
        self.success_count += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                logger.info("Circuit refermé - service récupéré")
                self.state = CircuitState.CLOSED
                self.half_open_calls = 0
    
    def _on_failure(self):
        """Appelé quand fonction échoue."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # Échec en half-open -> retour à OPEN
            logger.warning("Échec en half-open - circuit réouvert")
            self.state = CircuitState.OPEN
            self.half_open_calls = 0
        elif self.failure_count >= self.failure_threshold:
            # Dépassement seuil -> ouverture circuit
            logger.error(f"Circuit ouvert après {self.failure_count} échecs")
            self.state = CircuitState.OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Exécute fonction avec protection circuit breaker.
        
        Args:
            func: Fonction à appeler
            *args, **kwargs: Arguments fonction
            
        Returns:
            Résultat fonction
            
        Raises:
            CircuitBreakerOpenError: Si circuit ouvert
            Exception: Erreur originale si échec
        """
        self.total_calls += 1
        
        # Vérifier si on peut passer
        if self.state == CircuitState.OPEN:
            # Vérifier si timeout écoulé
            if time.time() - self.last_failure_time > self.timeout:
                logger.info("Timeout écoulé - passage en half-open")
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit ouvert - réessayez dans "
                    f"{self.timeout - (time.time() - self.last_failure_time):.0f}s"
                )
        
        # Exécuter fonction
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def get_stats(self) -> dict:
        """Retourne statistiques circuit breaker."""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'total_calls': self.total_calls,
            'success_rate': (self.success_count / self.total_calls * 100) 
                           if self.total_calls > 0 else 0
        }


class RetryWithCircuitBreaker:
    """Combine retry et circuit breaker."""
    
    def __init__(self, 
                 max_retries: int = 3,
                 backoff_seconds: float = 1.0,
                 circuit_breaker: Optional[APICircuitBreaker] = None):
        """
        Initialise retry avec circuit breaker.
        
        Args:
            max_retries: Nombre max tentatives
            backoff_seconds: Délai entre tentatives
            circuit_breaker: Instance circuit breaker (optionnel)
        """
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.circuit_breaker = circuit_breaker or APICircuitBreaker()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Appelle fonction avec retry et circuit breaker."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return self.circuit_breaker.call(func, *args, **kwargs)
            except CircuitBreakerOpenError:
                # Circuit ouvert - ne pas retry
                raise
            except Exception as e:
                last_exception = e
                logger.warning(f"Tentative {attempt + 1}/{self.max_retries} échouée: {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.backoff_seconds * (attempt + 1))
        
        # Toutes tentatives échouées
        raise last_exception


# Instance globale pour réutilisation
_default_circuit_breaker = None

def get_circuit_breaker() -> APICircuitBreaker:
    """Retourne instance globale circuit breaker."""
    global _default_circuit_breaker
    if _default_circuit_breaker is None:
        _default_circuit_breaker = APICircuitBreaker(
            failure_threshold=5,
            timeout=60
        )
    return _default_circuit_breaker


if __name__ == "__main__":
    # Test circuit breaker
    print("Test Circuit Breaker")
    
    cb = APICircuitBreaker(failure_threshold=3, timeout=5)
    
    # Fonction test
    def flaky_function(should_fail):
        if should_fail:
            raise Exception("Erreur simulée")
        return "Succès"
    
    # Test succès
    result = cb.call(flaky_function, False)
    print(f"1. Succès: {result}")
    print(f"   Stats: {cb.get_stats()}")
    
    # Test échecs
    for i in range(4):
        try:
            cb.call(flaky_function, True)
        except Exception as e:
            print(f"{i+2}. Échec: {e}")
    
    print(f"   Stats: {cb.get_stats()}")
    
    # Test circuit ouvert
    try:
        cb.call(flaky_function, False)
    except CircuitBreakerOpenError as e:
        print(f"6. Circuit ouvert: {e}")
