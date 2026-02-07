"""
NBA-19 Ultimate Discovery - Circuit Breaker Pattern
Protection contre les cascades d'erreurs
"""
import time
from enum import Enum
from datetime import datetime
from typing import Optional


class CircuitState(Enum):
    """États du circuit breaker"""
    CLOSED = "closed"      # Fonctionnement normal
    OPEN = "open"          # Circuit ouvert (arrêt)
    HALF_OPEN = "half_open"  # Test de récupération


class CircuitBreaker:
    """
    Circuit Breaker Pattern pour protéger contre les erreurs en cascade
    
    Usage:
        cb = CircuitBreaker(threshold=0.05, timeout=300)
        
        if cb.can_execute():
            try:
                result = risky_operation()
                cb.record_success()
            except Exception as e:
                cb.record_failure()
                raise
        else:
            raise CircuitBreakerOpen("Service temporairement indisponible")
    """
    
    def __init__(
        self,
        failure_threshold: float = 0.05,
        timeout_seconds: int = 300,
        min_calls: int = 20
    ):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.min_calls = min_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change = time.time()
    
    def can_execute(self) -> bool:
        """Vérifier si l'exécution est autorisée"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = time.time()
                return True
            return False
        
        # HALF_OPEN: autoriser un test
        return True
    
    def record_success(self):
        """Enregistrer un succès"""
        self.success_count += 1
        
        if self.state == CircuitState.HALF_OPEN:
            # Réinitialiser si le test réussit
            self._reset()
    
    def record_failure(self):
        """Enregistrer un échec"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # Retourner en OPEN si le test échoue
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
        elif self.state == CircuitState.CLOSED:
            # Vérifier si on doit ouvrir le circuit
            if self._should_open():
                self.state = CircuitState.OPEN
                self.last_state_change = time.time()
                self._alert_open()
    
    def get_stats(self) -> dict:
        """Obtenir les statistiques"""
        total = self.success_count + self.failure_count
        failure_rate = self.failure_count / total if total > 0 else 0.0
        
        return {
            "state": self.state.value,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_calls": total,
            "failure_rate": failure_rate,
            "last_failure": datetime.fromtimestamp(self.last_failure_time).isoformat() 
                           if self.last_failure_time else None,
            "time_in_state": time.time() - self.last_state_change
        }
    
    def _should_open(self) -> bool:
        """Déterminer si on doit ouvrir le circuit"""
        total = self.success_count + self.failure_count
        if total < self.min_calls:
            return False
        
        failure_rate = self.failure_count / total
        return failure_rate > self.failure_threshold
    
    def _should_attempt_reset(self) -> bool:
        """Vérifier si on peut tenter une réinitialisation"""
        if self.last_failure_time is None:
            return True
        
        elapsed = time.time() - self.last_failure_time
        return elapsed > self.timeout_seconds
    
    def _reset(self):
        """Réinitialiser le circuit"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = time.time()
    
    def _alert_open(self):
        """Alerter quand le circuit s'ouvre"""
        stats = self.get_stats()
        print(f"🚨 CIRCUIT BREAKER OPENED!")
        print(f"   Failure rate: {stats['failure_rate']:.1%}")
        print(f"   Total calls: {stats['total_calls']}")
        print(f"   Will retry in {self.timeout_seconds}s")


class CircuitBreakerOpen(Exception):
    """Exception levée quand le circuit est ouvert"""
    pass
