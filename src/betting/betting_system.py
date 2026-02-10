#!/usr/bin/env python3
"""
BettingSystem - Système de paris NBA professionnel

Architecture optimisée sans redondance :
- Étend ROITracker (src/ml/pipeline/tracking_roi.py)
- Utilise AlertManager existant (src/utils/alerts.py)
- Intègre SmartPredictionFilter pour grading
- 5 stratégies de mise en méthodes (pas classes séparées)

Usage:
    betting = BettingSystem(initial_bankroll=100.0, risk_profile='moderate')
    
    # Trouver les value bets
    for prediction, edge, odds in betting.find_value_bets(min_edge=0.05):
        stake = betting.calculate_stake(prediction, strategy='kelly')
        print(f"Parier {stake:.2f}€ sur {prediction['home_team']} (edge: {edge:.1%})")
    
    # Générer rapport
    report = betting.generate_betting_report()
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Generator
from dataclasses import dataclass
import logging

# Import composants existants
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.pipeline.tracking_roi import ROITracker
from utils.alerts import AlertManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Bankroll:
    """Gestion de la bankroll avec 3 profils de risque."""
    initial_amount: float = 100.0
    risk_profile: str = 'moderate'  # 'conservative', 'moderate', 'aggressive'
    current_amount: float = None
    
    # Configuration des profils
    PROFILES = {
        'conservative': {
            'base_stake_pct': 0.01,      # 1% de la bankroll
            'max_stake_pct': 0.02,       # Max 2%
            'stop_loss': -10.0,          # Stop à -10€
            'target_roi': 0.05,          # Objectif +5% mensuel
            'min_confidence': 0.70       # Seuil de confiance minimum
        },
        'moderate': {
            'base_stake_pct': 0.02,      # 2% de la bankroll
            'max_stake_pct': 0.04,       # Max 4%
            'stop_loss': -20.0,          # Stop à -20€
            'target_roi': 0.10,          # Objectif +10% mensuel
            'min_confidence': 0.65
        },
        'aggressive': {
            'base_stake_pct': 0.05,      # 5% de la bankroll
            'max_stake_pct': 0.10,       # Max 10%
            'stop_loss': -30.0,          # Stop à -30€
            'target_roi': 0.20,          # Objectif +20% mensuel
            'min_confidence': 0.60
        }
    }
    
    def __post_init__(self):
        if self.current_amount is None:
            self.current_amount = self.initial_amount
        
        if self.risk_profile not in self.PROFILES:
            raise ValueError(f"Profil inconnu: {self.risk_profile}")
        
        self.config = self.PROFILES[self.risk_profile]
        self.transactions = []
        self.max_drawdown = 0.0
        self.peak = self.initial_amount
    
    @property
    def profit_loss(self) -> float:
        """P&L actuel."""
        return self.current_amount - self.initial_amount
    
    @property
    def roi(self) -> float:
        """ROI en pourcentage."""
        return (self.profit_loss / self.initial_amount) * 100
    
    @property
    def is_stop_loss_triggered(self) -> bool:
        """Vérifie si le stop-loss est atteint."""
        return self.profit_loss <= self.config['stop_loss']
    
    def record_bet(self, stake: float, result: str, odds: float = 2.0):
        """Enregistre un pari."""
        profit = stake * (odds - 1) if result == 'win' else -stake
        self.current_amount += profit
        
        # Track peak and drawdown
        if self.current_amount > self.peak:
            self.peak = self.current_amount
        drawdown = (self.peak - self.current_amount) / self.peak
        self.max_drawdown = max(self.max_drawdown, drawdown)
        
        self.transactions.append({
            'date': datetime.now().isoformat(),
            'stake': stake,
            'result': result,
            'profit': profit,
            'balance': self.current_amount
        })
    
    def get_stake_range(self) -> Tuple[float, float]:
        """Retourne la fourchette de mise (min, max)."""
        min_stake = self.current_amount * self.config['base_stake_pct']
        max_stake = self.current_amount * self.config['max_stake_pct']
        return min_stake, max_stake
    
    def get_summary(self) -> Dict:
        """Résumé de la bankroll."""
        return {
            'initial': self.initial_amount,
            'current': self.current_amount,
            'profit_loss': self.profit_loss,
            'roi_pct': self.roi,
            'max_drawdown_pct': self.max_drawdown * 100,
            'total_bets': len(self.transactions),
            'risk_profile': self.risk_profile,
            'stop_loss_triggered': self.is_stop_loss_triggered,
            'target_roi_pct': self.config['target_roi'] * 100
        }


class BettingSystem(ROITracker):
    """
    Système de betting NBA professionnel.
    
    Étend ROITracker pour réutiliser :
    - Historique des prédictions
    - Calcul du ROI
    - Génération de rapports
    
    Ajoute :
    - Gestion bankroll (3 profils)
    - 5 stratégies de mise
    - Intégration cotes (The Odds API)
    - Email alerts
    """
    
    def __init__(self, 
                 initial_bankroll: float = 100.0,
                 risk_profile: str = 'moderate',
                 tracking_dir: str = "predictions",
                 email: str = "isaakdjedje@gmail.com"):
        """
        Initialise le système de betting.
        
        Args:
            initial_bankroll: Capital initial (défaut: 100€)
            risk_profile: 'conservative', 'moderate', 'aggressive'
            tracking_dir: Dossier pour l'historique
            email: Email pour les notifications
        """
        # Initialise ROITracker (parent)
        super().__init__(tracking_dir)
        
        # Initialise composants betting
        self.bankroll = Bankroll(initial_bankroll, risk_profile)
        self.alert_manager = AlertManager()
        self.email = email
        
        # Lazy imports pour éviter dépendances circulaires
        self._odds_client = None
        self._smart_filter = None
        
        logger.info(f"BettingSystem initialisé: {initial_bankroll}€ ({risk_profile})")
    
    @property
    def odds_client(self):
        """Lazy load de l'odds client."""
        if self._odds_client is None:
            from .odds_client import OddsClient
            self._odds_client = OddsClient()
        return self._odds_client
    
    # =========================================================================
    # STRATÉGIES DE MISE (5 stratégies en méthodes)
    # =========================================================================
    
    def calculate_stake(self, prediction: Dict, strategy: str = 'kelly', 
                       bookmaker_odds: float = None) -> float:
        """
        Calcule la mise selon la stratégie choisie.
        
        Args:
            prediction: Dict avec 'proba_home_win', 'confidence'
            strategy: 'flat', 'kelly', 'confidence', 'value', 'martingale'
            bookmaker_odds: Cote du bookmaker (pour value betting)
            
        Returns:
            Montant à miser
        """
        strategies = {
            'flat': self._stake_flat,
            'kelly': self._stake_kelly,
            'confidence': self._stake_confidence_weighted,
            'value': self._stake_value_betting,
            'martingale': self._stake_martingale
        }
        
        if strategy not in strategies:
            raise ValueError(f"Stratégie inconnue: {strategy}")
        
        stake = strategies[strategy](prediction, bookmaker_odds)
        
        # Respecte les limites du profil
        min_stake, max_stake = self.bankroll.get_stake_range()
        return max(min_stake, min(stake, max_stake))
    
    def _stake_flat(self, prediction: Dict, bookmaker_odds: float = None) -> float:
        """Stratégie Flat: mise fixe % bankroll."""
        return self.bankroll.current_amount * self.bankroll.config['base_stake_pct']
    
    def _stake_kelly(self, prediction: Dict, bookmaker_odds: float = None) -> float:
        """
        Kelly Criterion: mise optimale f(probabilité, cote).
        
        f* = (bp - q) / b
        où b = cote - 1, p = probabilité, q = 1 - p
        """
        p = prediction.get('proba_home_win', 0.5)
        
        # Si pas de cote bookmaker, assume cote équitable
        if bookmaker_odds is None:
            bookmaker_odds = 1 / p if p > 0 else 2.0
        
        b = bookmaker_odds - 1
        q = 1 - p
        
        # Kelly fraction
        kelly_fraction = (b * p - q) / b if b > 0 else 0
        
        # Kelly fractionnel (plus prudent: 1/4 Kelly)
        kelly_fraction = max(0, kelly_fraction * 0.25)
        
        return self.bankroll.current_amount * kelly_fraction
    
    def _stake_confidence_weighted(self, prediction: Dict, 
                                   bookmaker_odds: float = None) -> float:
        """Stratégie Confidence-Weighted: mise ∝ confiance."""
        confidence = prediction.get('confidence', 0.5)
        min_conf = self.bankroll.config['min_confidence']
        
        # Normalise la confiance entre 0 et 1
        normalized_conf = max(0, (confidence - min_conf) / (1 - min_conf))
        
        min_stake, max_stake = self.bankroll.get_stake_range()
        return min_stake + (max_stake - min_stake) * normalized_conf
    
    def _stake_value_betting(self, prediction: Dict, 
                            bookmaker_odds: float = None) -> float:
        """
        Stratégie Value Betting: mise si value > 5%.
        
        Value = Probabilité réelle - Probabilité implicite
        """
        if bookmaker_odds is None:
            return self._stake_flat(prediction)
        
        true_prob = prediction.get('proba_home_win', 0.5)
        implied_prob = 1 / bookmaker_odds
        
        edge = true_prob - implied_prob
        
        if edge < 0.05:  # Moins de 5% value = pas de mise
            return 0
        
        # Mise proportionnelle à la value
        min_stake, max_stake = self.bankroll.get_stake_range()
        value_factor = min(edge / 0.10, 1.0)  # Max à 10% value
        
        return min_stake + (max_stake - min_stake) * value_factor
    
    def _stake_martingale(self, prediction: Dict, 
                         bookmaker_odds: float = None) -> float:
        """
        Stratégie Martingale: augmente après une perte.
        ⚠️ RISQUÉ - À utiliser avec précaution!
        """
        # Récupère dernière transaction
        if not self.bankroll.transactions:
            return self._stake_flat(prediction)
        
        last_transaction = self.bankroll.transactions[-1]
        base_stake = self._stake_flat(prediction)
        
        if last_transaction['result'] == 'loss':
            # Double la mise après une perte (limité à 4x)
            consecutive_losses = 1
            for t in reversed(self.bankroll.transactions[-4:]):
                if t['result'] == 'loss':
                    consecutive_losses += 1
                else:
                    break
            
            multiplier = min(2 ** consecutive_losses, 4)
            return base_stake * multiplier
        
        return base_stake
    
    # =========================================================================
    # VALUE BETTING & COTES
    # =========================================================================
    
    def find_value_bets(self, min_edge: float = 0.05) -> Generator:
        """
        Trouve les value bets (cotes sous-évaluées par le marché).
        
        Args:
            min_edge: Seuil minimum de value (défaut: 5%)
            
        Yields:
            Tuple (prediction, edge, bookmaker_odds)
        """
        logger.info(f"Recherche de value bets (edge > {min_edge:.1%})...")
        
        # Récupère prédictions du jour
        predictions = self._get_today_predictions()
        value_bets_found = 0
        
        for pred in predictions:
            true_prob = pred.get('proba_home_win', 0.5)
            
            try:
                # Récupère cotes bookmaker
                odds = self.odds_client.get_odds(
                    pred['home_team'], 
                    pred['away_team']
                )
                
                implied_prob = 1 / odds if odds > 1 else 0.5
                edge = true_prob - implied_prob
                
                if edge >= min_edge:
                    value_bets_found += 1
                    logger.info(f"✅ Value bet trouvé: {pred['home_team']} vs {pred['away_team']} "
                              f"(edge: {edge:.1%}, odds: {odds:.2f})")
                    
                    # Envoie alerte email si edge > 10%
                    if edge >= 0.10:
                        self._send_value_alert(pred, edge, odds)
                    
                    yield pred, edge, odds
                    
            except Exception as e:
                logger.warning(f"Erreur récupération cotes pour {pred['home_team']}: {e}")
                continue
        
        logger.info(f"{value_bets_found} value bets trouvés")
    
    def _get_today_predictions(self) -> List[Dict]:
        """Récupère les prédictions du jour."""
        # Charge depuis le fichier de prédictions
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Cherche fichier de prédictions le plus récent
        pred_files = list(Path('predictions').glob('predictions_optimized_*.csv'))
        if not pred_files:
            logger.warning("Aucun fichier de prédictions trouvé")
            return []
        
        # Prend le plus récent
        latest_file = max(pred_files, key=lambda p: p.stat().st_mtime)
        df = pd.read_csv(latest_file)
        
        # Convertit en liste de dicts
        return df.to_dict('records')
    
    def _send_value_alert(self, prediction: Dict, edge: float, odds: float):
        """Envoie une alerte email pour un value bet."""
        try:
            subject = f"🎯 Value Bet Détecté - {prediction['home_team']} vs {prediction['away_team']}"
            
            message = f"""
            Value Bet Détecté!
            
            Match: {prediction['home_team']} vs {prediction['away_team']}
            Prédiction: {prediction['prediction']}
            Probabilité modèle: {prediction.get('proba_home_win', 0):.1%}
            Cote bookmaker: {odds:.2f}
            Edge: {edge:.1%}
            
            Recommandation: FORTE VALUE
            
            ---
            NBA Betting System
            """
            
            # Utilise AlertManager existant
            self.alert_manager.send_alert(
                level='info',
                message=message,
                source='value_betting'
            )
            
            logger.info(f"📧 Alerte email envoyée pour value bet ({edge:.1%})")
            
        except Exception as e:
            logger.error(f"Erreur envoi alerte: {e}")
    
    # =========================================================================
    # BOOKMAKER TRACKING
    # =========================================================================
    
    def get_bookmaker_ranking(self) -> pd.DataFrame:
        """
        Classe les bookmakers par rentabilité.
        
        Returns:
            DataFrame avec ranking des bookmakers
        """
        # TODO: Implémenter quand plusieurs bookmakers disponibles
        # Pour l'instant, retourne classement basé sur ROI
        
        if self.history.empty or 'actual_result' not in self.history.columns:
            return pd.DataFrame()
        
        df = self.history[self.history['actual_result'].notna()].copy()
        
        # Calcule ROI par équipe (simule bookmakers)
        team_performance = df.groupby('home_team').agg({
            'correct': ['count', 'sum', 'mean'],
            'roi': 'sum'
        }).reset_index()
        
        team_performance.columns = ['team', 'total_bets', 'wins', 'accuracy', 'total_roi']
        team_performance = team_performance.sort_values('total_roi', ascending=False)
        
        return team_performance
    
    # =========================================================================
    # RAPPORTS & ANALYSES
    # =========================================================================
    
    def generate_betting_report(self) -> Dict:
        """
        Génère un rapport complet de betting.
        
        Returns:
            Dict avec métriques complètes
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'bankroll': self.bankroll.get_summary(),
            'performance': self.calculate_all_rois(),
            'value_bets_today': list(self.find_value_bets(min_edge=0.05)),
            'bookmaker_ranking': self.get_bookmaker_ranking().to_dict('records'),
            'threshold_analysis': self.test_confidence_thresholds()
        }
        
        return report
    
    def calculate_all_rois(self) -> Dict:
        """Calcule le ROI pour toutes les stratégies."""
        strategies = ['all', 'high_confidence', 'medium_confidence']
        results = {}
        
        for strategy in strategies:
            roi_data = self.calculate_roi(strategy=strategy)
            if 'error' not in roi_data:
                results[strategy] = roi_data
        
        return results
    
    def save_betting_state(self, filepath: str = "predictions/betting_state.json"):
        """Sauvegarde l'état complet du système."""
        state = {
            'bankroll': self.bankroll.get_summary(),
            'transactions': self.bankroll.transactions,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"État betting sauvegardé: {filepath}")
    
    def load_betting_state(self, filepath: str = "predictions/betting_state.json"):
        """Charge l'état du système."""
        if not Path(filepath).exists():
            logger.warning(f"Fichier état non trouvé: {filepath}")
            return
        
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        # Restore bankroll
        self.bankroll.current_amount = state['bankroll']['current']
        self.bankroll.transactions = state['transactions']
        
        logger.info(f"État betting chargé: {self.bankroll.current_amount:.2f}€")


def demo_betting_system():
    """Démonstration du système de betting."""
    print("=" * 70)
    print("DÉMONSTRATION BETTING SYSTEM")
    print("=" * 70)
    
    # Initialise avec 100€ profil modéré
    betting = BettingSystem(initial_bankroll=100.0, risk_profile='moderate')
    
    print(f"\n💰 Bankroll initiale: {betting.bankroll.initial_amount}€")
    print(f"📊 Profil: {betting.bankroll.risk_profile}")
    print(f"🎯 Mise min-max: {betting.bankroll.get_stake_range()}")
    
    # Simule une prédiction
    prediction = {
        'home_team': 'Boston Celtics',
        'away_team': 'Los Angeles Lakers',
        'prediction': 'Home Win',
        'proba_home_win': 0.75,
        'confidence': 0.75
    }
    
    print(f"\n📈 Prédiction: {prediction['home_team']} vs {prediction['away_team']}")
    print(f"   Probabilité: {prediction['proba_home_win']:.1%}")
    print(f"   Confiance: {prediction['confidence']:.1%}")
    
    # Calcule mises pour chaque stratégie
    strategies = ['flat', 'kelly', 'confidence', 'value']
    bookmaker_odds = 1.80  # Cote bookmaker
    
    print(f"\n💵 Mises recommandées (cote bookmaker: {bookmaker_odds}):")
    for strategy in strategies:
        stake = betting.calculate_stake(prediction, strategy, bookmaker_odds)
        print(f"   {strategy.upper():12s}: {stake:.2f}€")
    
    # Simule quelques paris
    print("\n🎲 Simulation de paris:")
    
    # Pari 1: Gagnant
    stake = 2.0
    betting.bankroll.record_bet(stake, 'win', odds=1.90)
    print(f"   + Pari gagnant: +{stake * 0.90:.2f}€")
    
    # Pari 2: Perdant
    betting.bankroll.record_bet(stake, 'loss')
    print(f"   - Pari perdant: -{stake:.2f}€")
    
    # Pari 3: Gagnant
    betting.bankroll.record_bet(stake, 'win', odds=2.10)
    print(f"   + Pari gagnant: +{stake * 1.10:.2f}€")
    
    # Résumé
    summary = betting.bankroll.get_summary()
    print(f"\n📊 Résumé:")
    print(f"   Bankroll actuelle: {summary['current']:.2f}€")
    print(f"   P&L: {summary['profit_loss']:+.2f}€")
    print(f"   ROI: {summary['roi_pct']:+.1f}%")
    
    print("\n✅ Démonstration terminée!")
    
    return betting


if __name__ == "__main__":
    betting = demo_betting_system()
