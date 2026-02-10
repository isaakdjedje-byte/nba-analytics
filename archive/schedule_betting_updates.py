#!/usr/bin/env python3
"""
Schedule Betting Updates - Planification automatique des mises à jour betting

Exécute 2 fois par jour:
- 9h00: Mise à jour matinale des cotes et value bets
- 18h00: Mise à jour soir avant les matchs

Usage:
    # Exécution manuelle
    python scripts/schedule_betting_updates.py
    
    # Configuration du cron (Linux/Mac)
    crontab -e
    # Ajouter: 0 9,18 * * * /usr/bin/python3 /path/to/nba-analytics/scripts/schedule_betting_updates.py
    
    # Planificateur Windows (à exécuter en admin)
    scripts/setup_windows_schedule.bat
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
from datetime import datetime
from typing import Dict, List

from src.betting import BettingSystem, OddsClient
from src.reporting.weekly_betting_report import WeeklyBettingReport

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BettingScheduler:
    """
    Planificateur de mises à jour betting.
    
    Gère:
    - Mise à jour des cotes 2x/jour
    - Détection des value bets
    - Envoi d'alertes email
    - Génération de rapports hebdomadaires (lundi)
    """
    
    def __init__(self, 
                 bankroll: float = 100.0,
                 risk_profile: str = 'moderate',
                 email: str = "isaakdjedje@gmail.com"):
        """
        Initialise le planificateur.
        
        Args:
            bankroll: Capital initial
            risk_profile: Profil de risque
            email: Email pour notifications
        """
        self.betting = BettingSystem(
            initial_bankroll=bankroll,
            risk_profile=risk_profile,
            email=email
        )
        self.email = email
        self.log_file = Path("logs/betting_scheduler.log")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Scheduler initialisé: {bankroll}€ ({risk_profile})")
    
    def run_morning_update(self):
        """
        Mise à jour matinale (9h00).
        
        Effectue:
        - Rafraîchissement des cotes
        - Détection des value bets
        - Alertes email si opportunités > 10% edge
        """
        logger.info("="*70)
        logger.info("MISE À JOUR MATINALE - 9h00")
        logger.info("="*70)
        
        try:
            # 1. Récupère les value bets
            logger.info("Recherche des value bets...")
            value_bets = list(self.betting.find_value_bets(min_edge=0.05))
            
            high_value_bets = [vb for vb in value_bets if vb[1] >= 0.10]
            
            if high_value_bets:
                logger.info(f"🎯 {len(high_value_bets)} value bets > 10% détectés!")
                self._send_alert_email(high_value_bets, "morning")
            else:
                logger.info(f"✅ {len(value_bets)} value bets détectés (edge < 10%)")
            
            # 2. Sauvegarde l'état
            self.betting.save_betting_state()
            
            # 3. Log
            self._log_update("morning", {
                'value_bets_count': len(value_bets),
                'high_value_count': len(high_value_bets),
                'bankroll': self.betting.bankroll.current_amount
            })
            
            logger.info("✅ Mise à jour matinale terminée")
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour matinale: {e}")
            self._send_error_alert("morning", str(e))
    
    def run_evening_update(self):
        """
        Mise à jour soir (18h00).
        
        Effectue:
        - Rafraîchissement des cotes avant matchs
        - Mise à jour des résultats des matchs précédents
        - Alertes si bankroll critique
        """
        logger.info("="*70)
        logger.info("MISE À JOUR SOIR - 18h00")
        logger.info("="*70)
        
        try:
            # 1. Met à jour les résultats si disponibles
            logger.info("Mise à jour des résultats...")
            # TODO: Intégrer avec l'API NBA pour récupérer les résultats
            
            # 2. Vérifie la bankroll
            summary = self.betting.bankroll.get_summary()
            
            if summary['stop_loss_triggered']:
                logger.warning("🚨 STOP-LOSS ATTEINT!")
                self._send_bankroll_alert("STOP-LOSS ATTEINT", summary)
            elif summary['roi_pct'] < -15:
                logger.warning("⚠️ ROI négatif important")
                self._send_bankroll_alert("ROI négatif", summary)
            
            # 3. Value bets du soir
            logger.info("Recherche des value bets soir...")
            value_bets = list(self.betting.find_value_bets(min_edge=0.05))
            
            if value_bets:
                evening_bets = [vb for vb in value_bets]
                logger.info(f"🎯 {len(evening_bets)} opportunités pour ce soir")
            
            # 4. Sauvegarde
            self.betting.save_betting_state()
            
            # 5. Log
            self._log_update("evening", {
                'value_bets_count': len(value_bets),
                'bankroll': summary['current'],
                'roi_pct': summary['roi_pct']
            })
            
            logger.info("✅ Mise à jour soir terminée")
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour soir: {e}")
            self._send_error_alert("evening", str(e))
    
    def run_weekly_report(self):
        """
        Génère le rapport hebdomadaire (lundi).
        
        Envoie par email le résumé de la semaine.
        """
        logger.info("="*70)
        logger.info("RAPPORT HEBDOMADAIRE")
        logger.info("="*70)
        
        try:
            report_gen = WeeklyBettingReport(self.betting, email=self.email)
            files = report_gen.generate_and_save()
            
            # Envoie par email
            report_gen.send_email_report()
            
            logger.info(f"✅ Rapport hebdomadaire envoyé à {self.email}")
            logger.info(f"   JSON: {files['json']}")
            logger.info(f"   HTML: {files['html']}")
            
            # Log
            self._log_update("weekly_report", {
                'files_generated': list(files.keys()),
                'bankroll': self.betting.bankroll.current_amount
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur rapport hebdomadaire: {e}")
            self._send_error_alert("weekly", str(e))
    
    def _send_alert_email(self, value_bets: List, update_type: str):
        """Envoie une alerte email pour les value bets."""
        try:
            from src.utils.alerts import AlertManager
            
            subject = f"🎯 Value Bets Détectés - {update_type.upper()}"
            
            message = f"""
Bonjour,

{len(value_bets)} value bets ont été détectés lors de la mise à jour {update_type}.

Détails:
"""
            for i, (pred, edge, odds) in enumerate(value_bets[:5], 1):
                stake = self.betting.calculate_stake(pred, 'kelly', odds)
                message += f"""
{i}. {pred['home_team']} vs {pred['away_team']}
   Prédiction: {pred['prediction']}
   Edge: {edge:.1%}
   Cote: {odds:.2f}
   Mise recommandée: {stake:.2f}€
"""
            
            message += """
Bonne chance!

---
NBA Betting System
"""
            
            alert_manager = AlertManager()
            alert_manager.send_alert(
                level='info',
                message=message,
                source=f'betting_{update_type}'
            )
            
            logger.info(f"📧 Alerte email envoyée ({len(value_bets)} value bets)")
            
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
    
    def _send_bankroll_alert(self, alert_type: str, summary: Dict):
        """Envoie une alerte pour problème de bankroll."""
        try:
            from src.utils.alerts import AlertManager
            
            subject = f"🚨 Alerte Bankroll - {alert_type}"
            
            message = f"""
ALERTE BANKROLL

Type: {alert_type}

État actuel:
- Balance: {summary['current']:.2f}€
- P&L: {summary['profit_loss']:+.2f}€
- ROI: {summary['roi_pct']:+.1f}%
- Max Drawdown: {summary['max_drawdown_pct']:.1f}%

Recommandation: {self._get_bankroll_recommendation(summary)}

---
NBA Betting System
"""
            
            alert_manager = AlertManager()
            alert_manager.send_alert(
                level='warning' if 'STOP-LOSS' not in alert_type else 'critical',
                message=message,
                source='bankroll_monitor'
            )
            
            logger.info(f"📧 Alerte bankroll envoyée: {alert_type}")
            
        except Exception as e:
            logger.error(f"Erreur envoi alerte bankroll: {e}")
    
    def _get_bankroll_recommendation(self, summary: Dict) -> str:
        """Génère une recommandation basée sur l'état de la bankroll."""
        if summary['stop_loss_triggered']:
            return "ARRÊTER IMMÉDIATEMENT. Stop-loss atteint."
        elif summary['roi_pct'] < -15:
            return "Réduire les mises de moitié. Vérifier les stratégies."
        elif summary['max_drawdown_pct'] > 25:
            return "Attention au risque. Considérer une pause."
        else:
            return "Surveillance active."
    
    def _send_error_alert(self, update_type: str, error: str):
        """Envoie une alerte en cas d'erreur."""
        try:
            from src.utils.alerts import AlertManager
            
            subject = f"❌ Erreur Betting - {update_type.upper()}"
            
            message = f"""
Une erreur s'est produite lors de la mise à jour {update_type}.

Erreur: {error}

Heure: {datetime.now().isoformat()}

Veuillez vérifier les logs pour plus de détails.

---
NBA Betting System
"""
            
            alert_manager = AlertManager()
            alert_manager.send_alert(
                level='error',
                message=message,
                source=f'error_{update_type}'
            )
            
        except Exception as e:
            logger.error(f"Erreur envoi alerte erreur: {e}")
    
    def _log_update(self, update_type: str, data: Dict):
        """Log les mises à jour dans un fichier."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': update_type,
            'data': data
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')


def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Planificateur de mises à jour betting NBA'
    )
    parser.add_argument(
        '--type',
        choices=['morning', 'evening', 'weekly', 'all'],
        default='all',
        help='Type de mise à jour à exécuter'
    )
    parser.add_argument(
        '--bankroll',
        type=float,
        default=100.0,
        help='Capital initial (défaut: 100€)'
    )
    parser.add_argument(
        '--profile',
        choices=['conservative', 'moderate', 'aggressive'],
        default='moderate',
        help='Profil de risque'
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("NBA BETTING SCHEDULER")
    print("="*70)
    print(f"Type: {args.type}")
    print(f"Bankroll: {args.bankroll}€")
    print(f"Profil: {args.profile}")
    print("="*70)
    
    scheduler = BettingScheduler(
        bankroll=args.bankroll,
        risk_profile=args.profile
    )
    
    if args.type == 'morning' or args.type == 'all':
        scheduler.run_morning_update()
    
    if args.type == 'evening' or args.type == 'all':
        scheduler.run_evening_update()
    
    if args.type == 'weekly':
        scheduler.run_weekly_report()
    
    print("\n✅ Terminé!")


if __name__ == "__main__":
    main()
