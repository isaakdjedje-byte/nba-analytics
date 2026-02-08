"""
NBA-19 Ultimate Discovery - Rate Limiter
Gestion intelligente du rate limiting API avec pauses programmees
"""
import time
from typing import Optional
from dataclasses import dataclass


@dataclass
class RateLimitConfig:
    """Configuration du rate limiting"""
    delay_seconds: float = 2.0  # 1 req / 2 sec
    pause_after_requests: int = 100
    pause_duration: int = 30  # 30 secondes
    burst_size: int = 1  # Pas de burst (conservateur)


class RateLimiter:
    """
    Rate Limiter avec pauses programmees pour respecter les limites API
    
    Usage:
        limiter = RateLimiter(config)
        
        for player in players:
            limiter.wait_if_needed()
            fetch_player_data(player)
            limiter.record_request()
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self.request_count = 0
        self.last_request_time: Optional[float] = None
        self.total_pause_time = 0
    
    def wait_if_needed(self):
        """
        Attendre si necessaire avant la prochaine requete
        Gere a la fois le delai entre requetes et les pauses programmees
        """
        # Verifier si on doit faire une pause programmee
        if self.request_count > 0 and self.request_count % self.config.pause_after_requests == 0:
            self._take_scheduled_pause()
        
        # Attendre le delai minimum entre requetes
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.config.delay_seconds:
                sleep_time = self.config.delay_seconds - elapsed
                time.sleep(sleep_time)
    
    def record_request(self):
        """Enregistrer qu'une requete a ete faite"""
        self.request_count += 1
        self.last_request_time = time.time()
    
    def _take_scheduled_pause(self):
        """Faire une pause programmee"""
        print(f"\n⏸️  Pause programmee apres {self.request_count} requetes")
        print(f"   Duree: {self.config.pause_duration}s")
        print(f"   Reprise a: {time.strftime('%H:%M:%S', time.localtime(time.time() + self.config.pause_duration))}\n")
        
        time.sleep(self.config.pause_duration)
        self.total_pause_time += self.config.pause_duration
    
    def get_stats(self) -> dict:
        """Obtenir les statistiques"""
        elapsed = time.time() - (self.last_request_time or time.time())
        
        return {
            "total_requests": self.request_count,
            "rate_per_minute": (self.request_count / (elapsed / 60)) if elapsed > 0 else 0,
            "total_pause_time": self.total_pause_time,
            "next_pause_at": ((self.request_count // self.config.pause_after_requests + 1) 
                             * self.config.pause_after_requests)
        }


class AdaptiveRateLimiter(RateLimiter):
    """
    Rate Limiter adaptatif qui ajuste le delai en fonction des erreurs
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        super().__init__(config)
        self.error_count = 0
        self.current_delay = self.config.delay_seconds
        self.min_delay = 1.0
        self.max_delay = 5.0
    
    def record_error(self):
        """Enregistrer une erreur et ajuster le delai"""
        self.error_count += 1
        
        # Augmenter le delai si trop d'erreurs
        if self.error_count > 5:
            self.current_delay = min(self.current_delay * 1.2, self.max_delay)
            print(f"[WARN]  Augmentation du delai a {self.current_delay:.1f}s (erreurs: {self.error_count})")
    
    def record_success(self):
        """Enregistrer un succes et potentiellement reduire le delai"""
        if self.error_count > 0:
            self.error_count = max(0, self.error_count - 1)
            
            # Reduire lentement le delai apres des succes
            if self.error_count == 0 and self.current_delay > self.config.delay_seconds:
                self.current_delay = max(self.current_delay * 0.95, self.config.delay_seconds)
    
    def wait_if_needed(self):
        """Surcharge avec le delai adaptatif"""
        if self.request_count > 0 and self.request_count % self.config.pause_after_requests == 0:
            self._take_scheduled_pause()
        
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.current_delay:
                sleep_time = self.current_delay - elapsed
                time.sleep(sleep_time)
