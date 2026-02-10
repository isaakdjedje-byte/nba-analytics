#!/usr/bin/env python3
"""
OddsClient - Client pour The Odds API

API gratuite: https://the-odds-api.com
- 500 requêtes/mois en plan gratuit
- Cotes temps réel NBA
- Moneylines, spreads, totals

Usage:
    from src.betting import OddsClient
    
    client = OddsClient(api_key="votre_cle_api")
    odds = client.get_odds("Boston Celtics", "Lakers")
    print(f"Cote: {odds}")
"""

import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OddsClient:
    """
    Client pour The Odds API.
    
    Gère:
    - Cache local intelligent
    - Fallback sur cotes simulées
    - Rate limiting (500 req/mois)
    """
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    SPORT = "basketball_nba"
    REGIONS = "eu"  # Europe
    MARKETS = "h2h"  # Head-to-head (moneyline)
    ODDS_FORMAT = "decimal"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise le client.
        
        Args:
            api_key: Clé API The Odds API (ou variable d'env ODDS_API_KEY)
        """
        self.api_key = api_key or self._get_api_key_from_env()
        self.cache_file = Path("data/odds_cache.json")
        self.usage_file = Path("data/odds_usage.json")
        self.cache = self._load_cache()
        self.usage = self._load_usage()
        
        if not self.api_key:
            logger.warning("⚠️  Pas de clé API - Mode simulation activé")
        else:
            logger.info("✅ Client Odds API initialisé")
    
    def _get_api_key_from_env(self) -> Optional[str]:
        """Récupère la clé API depuis les variables d'environnement."""
        import os
        return os.getenv('ODDS_API_KEY')
    
    def _load_cache(self) -> Dict:
        """Charge le cache des cotes."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erreur chargement cache: {e}")
        return {}
    
    def _save_cache(self):
        """Sauvegarde le cache."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def _load_usage(self) -> Dict:
        """Charge les stats d'utilisation."""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erreur chargement usage: {e}")
        return {'requests_this_month': 0, 'last_reset': datetime.now().isoformat()}
    
    def _save_usage(self):
        """Sauvegarde les stats d'utilisation."""
        self.usage_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage, f, indent=2)
    
    def _check_rate_limit(self) -> bool:
        """Vérifie si on peut faire une requête (500/mois)."""
        # Reset mensuel
        last_reset = datetime.fromisoformat(self.usage['last_reset'])
        if datetime.now() - last_reset > timedelta(days=30):
            self.usage['requests_this_month'] = 0
            self.usage['last_reset'] = datetime.now().isoformat()
        
        return self.usage['requests_this_month'] < 500
    
    def _increment_usage(self):
        """Incrémente le compteur de requêtes."""
        self.usage['requests_this_month'] += 1
        self._save_usage()
    
    def _get_cache_key(self, home_team: str, away_team: str, 
                      date: Optional[str] = None) -> str:
        """Génère une clé de cache unique."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        return f"{home_team}_vs_{away_team}_{date}"
    
    def get_odds(self, home_team: str, away_team: str, 
                 refresh: bool = False) -> Optional[float]:
        """
        Récupère la cote pour un match.
        
        Args:
            home_team: Nom équipe à domicile
            away_team: Nom équipe à l'extérieur
            refresh: Force le refresh du cache
            
        Returns:
            Cote décimale (ex: 1.85) ou None si erreur
        """
        cache_key = self._get_cache_key(home_team, away_team)
        
        # Vérifie le cache
        if not refresh and cache_key in self.cache:
            cached_odds = self.cache[cache_key]
            cache_time = datetime.fromisoformat(cached_odds['timestamp'])
            
            # Cache valide 2 heures
            if datetime.now() - cache_time < timedelta(hours=2):
                logger.debug(f"🔄 Cache hit: {home_team} vs {away_team}")
                return cached_odds['odds']
        
        # Pas de clé API = mode simulation
        if not self.api_key:
            return self._simulate_odds(home_team, away_team)
        
        # Vérifie rate limit
        if not self._check_rate_limit():
            logger.warning("⚠️  Limite API atteinte (500/mois) - Mode simulation")
            return self._simulate_odds(home_team, away_team)
        
        try:
            # Requête API
            odds = self._fetch_from_api(home_team, away_team)
            
            if odds:
                # Sauvegarde dans le cache
                self.cache[cache_key] = {
                    'odds': odds,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'api'
                }
                self._save_cache()
                self._increment_usage()
                
                logger.info(f"✅ Cote récupérée: {home_team} vs {away_team} = {odds:.2f}")
                return odds
            
        except Exception as e:
            logger.error(f"❌ Erreur API: {e}")
        
        # Fallback sur simulation
        return self._simulate_odds(home_team, away_team)
    
    def _fetch_from_api(self, home_team: str, away_team: str) -> Optional[float]:
        """
        Récupère les cotes depuis l'API.
        
        Returns:
            Cote moyenne des bookmakers
        """
        url = f"{self.BASE_URL}/sports/{self.SPORT}/odds"
        
        params = {
            'apiKey': self.api_key,
            'regions': self.REGIONS,
            'markets': self.MARKETS,
            'oddsFormat': self.ODDS_FORMAT,
            'dateFormat': 'iso'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Cherche le match
            for game in data:
                if self._match_teams(game, home_team, away_team):
                    # Extrait la cote moyenne des bookmakers
                    odds = self._extract_average_odds(game, home_team)
                    return odds
            
            logger.warning(f"⚠️  Match non trouvé: {home_team} vs {away_team}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur requête API: {e}")
            return None
    
    def _match_teams(self, game: Dict, home_team: str, away_team: str) -> bool:
        """Vérifie si le match correspond aux équipes."""
        game_home = game.get('home_team', '').lower()
        game_away = game.get('away_team', '').lower()
        
        # Normalise les noms
        search_home = home_team.lower()
        search_away = away_team.lower()
        
        return (search_home in game_home or game_home in search_home) and \
               (search_away in game_away or game_away in search_away)
    
    def _extract_average_odds(self, game: Dict, target_team: str) -> float:
        """Calcule la cote moyenne des bookmakers pour une équipe."""
        bookmakers = game.get('bookmakers', [])
        odds_list = []
        
        for bm in bookmakers:
            markets = bm.get('markets', [])
            for market in markets:
                if market.get('key') == 'h2h':
                    outcomes = market.get('outcomes', [])
                    for outcome in outcomes:
                        if target_team.lower() in outcome.get('name', '').lower():
                            odds_list.append(outcome.get('price', 0))
        
        if odds_list:
            return sum(odds_list) / len(odds_list)
        
        return 2.0  # Cote par défaut
    
    def _simulate_odds(self, home_team: str, away_team: str) -> float:
        """
        Simule des cotes réalistes quand l'API n'est pas disponible.
        
        Basé sur:
        - Avantage domicile: ~5%
        - Équipes fortes vs faibles
        """
        import random
        
        # Liste des équipes fortes (plus de chances de gagner)
        strong_teams = [
            'Boston', 'Celtics', 'Denver', 'Nuggets', 'Milwaukee', 'Bucks',
            'Phoenix', 'Suns', 'Golden State', 'Warriors', 'Lakers', 'LA'
        ]
        
        # Détermine si équipe à domicile est forte
        home_is_strong = any(team in home_team for team in strong_teams)
        away_is_strong = any(team in away_team for team in strong_teams)
        
        # Cote de base pour équipe à domicile
        if home_is_strong and not away_is_strong:
            base_odds = 1.50  # Forte favorite
        elif home_is_strong and away_is_strong:
            base_odds = 1.80  # Match équilibré, avantage domicile
        elif not home_is_strong and away_is_strong:
            base_odds = 2.40  # Outsider à domicile
        else:
            base_odds = 1.90  # Match équilibré
        
        # Ajoute un peu de variance
        odds = base_odds + random.uniform(-0.10, 0.10)
        
        logger.debug(f"🎲 Cote simulée: {home_team} vs {away_team} = {odds:.2f}")
        
        return round(odds, 2)
    
    def get_usage_stats(self) -> Dict:
        """Retourne les statistiques d'utilisation."""
        return {
            'requests_this_month': self.usage['requests_this_month'],
            'requests_remaining': 500 - self.usage['requests_this_month'],
            'last_reset': self.usage['last_reset'],
            'cache_size': len(self.cache),
            'api_key_configured': bool(self.api_key)
        }
    
    def get_cached_events(self) -> List[Dict]:
        """Retourne tous les événements en cache."""
        events = []
        for key, data in self.cache.items():
            events.append({
                'match': key,
                'odds': data['odds'],
                'timestamp': data['timestamp']
            })
        return events


def demo_odds_client():
    """Démonstration du client Odds API."""
    print("=" * 70)
    print("DÉMONSTRATION ODDS CLIENT")
    print("=" * 70)
    
    client = OddsClient()
    
    # Stats d'utilisation
    stats = client.get_usage_stats()
    print(f"\n📊 Stats API:")
    print(f"   Requêtes ce mois: {stats['requests_this_month']}/500")
    print(f"   Requêtes restantes: {stats['requests_remaining']}")
    print(f"   Clé API configurée: {'✅' if stats['api_key_configured'] else '❌'}")
    print(f"   Éléments en cache: {stats['cache_size']}")
    
    # Test quelques matchs
    matches = [
        ("Boston Celtics", "Los Angeles Lakers"),
        ("Denver Nuggets", "Phoenix Suns"),
        ("Golden State Warriors", "Milwaukee Bucks")
    ]
    
    print(f"\n🎲 Récupération des cotes:")
    for home, away in matches:
        odds = client.get_odds(home, away)
        print(f"   {home} vs {away}: {odds:.2f}")
    
    # Test cache (deuxième appel = cache hit)
    print(f"\n🔄 Test cache (deuxième appel):")
    odds = client.get_odds("Boston Celtics", "Los Angeles Lakers")
    print(f"   Boston vs Lakers: {odds:.2f} (depuis cache)")
    
    print("\n✅ Démonstration terminée!")
    
    return client


if __name__ == "__main__":
    client = demo_odds_client()
