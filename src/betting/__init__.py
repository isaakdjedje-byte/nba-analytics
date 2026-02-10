#!/usr/bin/env python3
"""
Module Betting NBA - Système de paris professionnel

Architecture optimisée sans redondance :
- BettingSystem étend ROITracker existant
- Réutilise AlertManager pour les notifications
- Intègre SmartPredictionFilter pour le grading

Usage:
    from src.betting import BettingSystem
    
    betting = BettingSystem(initial_bankroll=100, risk_profile='moderate')
    
    # Trouver les value bets
    for bet, edge, odds in betting.find_value_bets(min_edge=0.05):
        stake = betting.calculate_stake(bet, strategy='kelly')
        print(f"Parier {stake}€ sur {bet['home_team']} (edge: {edge:.1%})")
"""

from .betting_system import BettingSystem
from .odds_client import OddsClient

__all__ = ['BettingSystem', 'OddsClient']
__version__ = '1.0.0'
