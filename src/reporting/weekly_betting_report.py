#!/usr/bin/env python3
"""
WeeklyBettingReport - Rapport hebdomadaire de betting NBA

Génère un rapport complet avec:
- Performance de la bankroll
- ROI par stratégie
- Value bets détectés
- Recommandations

Usage:
    from src.reporting.weekly_betting_report import WeeklyBettingReport
    
    report = WeeklyBettingReport()
    report.generate_and_save()  # Génère et sauvegarde le rapport
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeeklyBettingReport:
    """
    Générateur de rapport hebdomadaire betting.
    
    Utilise BettingSystem pour récupérer les données.
    Exporte en JSON, CSV et HTML.
    """
    
    def __init__(self, 
                 betting_system=None,
                 output_dir: str = "reports",
                 email: str = "isaakdjedje@gmail.com"):
        """
        Initialise le générateur de rapport.
        
        Args:
            betting_system: Instance BettingSystem (créée si None)
            output_dir: Dossier de sortie
            email: Email pour notifications
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.email = email
        
        # Lazy import pour éviter circular imports
        self._betting = betting_system
        
        self.report_date = datetime.now()
        self.week_start = self.report_date - timedelta(days=7)
    
    @property
    def betting(self):
        """Lazy load du betting system."""
        if self._betting is None:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from src.betting import BettingSystem
            self._betting = BettingSystem(initial_bankroll=100.0, risk_profile='moderate')
        return self._betting
    
    def generate(self) -> Dict:
        """
        Génère le rapport complet.
        
        Returns:
            Dict avec toutes les métriques
        """
        logger.info("Génération du rapport hebdomadaire...")
        
        report = {
            'metadata': self._generate_metadata(),
            'bankroll_summary': self._get_bankroll_summary(),
            'performance': self._get_performance_metrics(),
            'value_bets': self._get_value_bets_summary(),
            'strategy_comparison': self._compare_strategies(),
            'bookmaker_ranking': self._get_bookmaker_ranking(),
            'recommendations': self._generate_recommendations()
        }
        
        logger.info("✅ Rapport généré avec succès")
        return report
    
    def _generate_metadata(self) -> Dict:
        """Génère les métadonnées du rapport."""
        return {
            'report_type': 'weekly_betting_report',
            'generated_at': self.report_date.isoformat(),
            'week_of': self.week_start.strftime('%Y-%m-%d'),
            'week_to': self.report_date.strftime('%Y-%m-%d'),
            'email': self.email,
            'version': '1.0.0'
        }
    
    def _get_bankroll_summary(self) -> Dict:
        """Récupère le résumé de la bankroll."""
        summary = self.betting.bankroll.get_summary()
        
        # Ajoute les évolutions de la semaine
        week_transactions = [
            t for t in self.betting.bankroll.transactions
            if datetime.fromisoformat(t['date']) >= self.week_start
        ]
        
        summary['weekly_transactions'] = len(week_transactions)
        summary['weekly_profit'] = sum(t['profit'] for t in week_transactions)
        
        return summary
    
    def _get_performance_metrics(self) -> Dict:
        """Calcule les métriques de performance."""
        return {
            'overall': self.betting.calculate_all_rois(),
            'threshold_analysis': self.betting.test_confidence_thresholds()
        }
    
    def _get_value_bets_summary(self) -> List[Dict]:
        """Récupère le résumé des value bets."""
        value_bets = list(self.betting.find_value_bets(min_edge=0.05))
        
        summary = []
        for pred, edge, odds in value_bets:
            stake = self.betting.calculate_stake(pred, strategy='kelly', bookmaker_odds=odds)
            summary.append({
                'match': f"{pred['home_team']} vs {pred['away_team']}",
                'prediction': pred['prediction'],
                'confidence': pred.get('confidence', 0),
                'edge': round(edge * 100, 1),  # %
                'odds': odds,
                'recommended_stake': round(stake, 2),
                'expected_value': round(stake * edge, 2)
            })
        
        return summary
    
    def _compare_strategies(self) -> Dict:
        """Compare les performances des 5 stratégies."""
        strategies = ['flat', 'kelly', 'confidence', 'value', 'martingale']
        comparison = {}
        
        # Simule une prédiction pour comparer les mises
        sample_pred = {
            'home_team': 'Sample',
            'away_team': 'Team',
            'prediction': 'Home Win',
            'proba_home_win': 0.70,
            'confidence': 0.70
        }
        bookmaker_odds = 1.85
        
        for strategy in strategies:
            try:
                stake = self.betting.calculate_stake(
                    sample_pred, 
                    strategy=strategy,
                    bookmaker_odds=bookmaker_odds
                )
                
                comparison[strategy] = {
                    'stake_example': round(stake, 2),
                    'stake_pct': round(stake / self.betting.bankroll.current_amount * 100, 1),
                    'description': self._get_strategy_description(strategy)
                }
            except Exception as e:
                logger.warning(f"Erreur comparaison {strategy}: {e}")
                comparison[strategy] = {'error': str(e)}
        
        return comparison
    
    def _get_strategy_description(self, strategy: str) -> str:
        """Retourne la description d'une stratégie."""
        descriptions = {
            'flat': 'Mise fixe % bankroll - Stable et prévisible',
            'kelly': 'Kelly Criterion - Optimale mathématiquement',
            'confidence': 'Confidence-weighted - Plus de confiance = plus gros',
            'value': 'Value betting - Uniquement si edge > 5%',
            'martingale': 'Martingale - Augmente après perte (RISQUÉ)'
        }
        return descriptions.get(strategy, 'Description non disponible')
    
    def _get_bookmaker_ranking(self) -> List[Dict]:
        """Récupère le classement des bookmakers."""
        df = self.betting.get_bookmaker_ranking()
        
        if df.empty:
            return []
        
        return df.head(10).to_dict('records')
    
    def _generate_recommendations(self) -> List[str]:
        """Génère des recommandations basées sur les données."""
        recommendations = []
        
        # Recommandation sur la bankroll
        bankroll_summary = self.betting.bankroll.get_summary()
        
        if bankroll_summary['roi_pct'] > 10:
            recommendations.append("✅ Excellente performance! Envisager d'augmenter légèrement les mises.")
        elif bankroll_summary['roi_pct'] < -5:
            recommendations.append("⚠️ Performance négative. Réduire les mises ou vérifier les modèles.")
        
        if bankroll_summary['max_drawdown_pct'] > 20:
            recommendations.append("⚠️ Drawdown important détecté. Attention au risque.")
        
        # Recommandation stratégie
        perf = self.betting.calculate_all_rois()
        if 'high_confidence' in perf and perf['high_confidence']['accuracy'] > 0.70:
            recommendations.append("🎯 Stratégie HIGH_CONFIDENCE très performante - privilégier ces paris.")
        
        # Recommandation value bets
        value_bets = list(self.betting.find_value_bets(min_edge=0.10))
        if len(value_bets) > 3:
            recommendations.append(f"🎯 {len(value_bets)} value bets détectés cette semaine - Opportunités!")
        
        if not recommendations:
            recommendations.append("📊 Performance stable. Continuer sur la lancée actuelle.")
        
        return recommendations
    
    def generate_and_save(self) -> Dict:
        """
        Génère et sauvegarde le rapport dans tous les formats.
        
        Returns:
            Dict avec les chemins des fichiers générés
        """
        report = self.generate()
        
        # Génère les noms de fichiers
        date_str = self.report_date.strftime('%Y%m%d')
        json_file = self.output_dir / f'weekly_betting_report_{date_str}.json'
        csv_file = self.output_dir / f'weekly_betting_report_{date_str}.csv'
        html_file = self.output_dir / f'weekly_betting_report_{date_str}.html'
        
        # Sauvegarde JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Rapport JSON: {json_file}")
        
        # Sauvegarde CSV (résumé uniquement)
        csv_data = self._prepare_csv_data(report)
        df = pd.DataFrame([csv_data])
        df.to_csv(csv_file, index=False)
        logger.info(f"✅ Rapport CSV: {csv_file}")
        
        # Génère HTML
        html_content = self._generate_html(report)
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"✅ Rapport HTML: {html_file}")
        
        return {
            'json': str(json_file),
            'csv': str(csv_file),
            'html': str(html_file),
            'report': report
        }
    
    def _prepare_csv_data(self, report: Dict) -> Dict:
        """Prépare les données pour l'export CSV."""
        bankroll = report['bankroll_summary']
        
        return {
            'report_date': self.report_date.strftime('%Y-%m-%d'),
            'week_of': self.week_start.strftime('%Y-%m-%d'),
            'initial_bankroll': bankroll['initial'],
            'current_bankroll': bankroll['current'],
            'profit_loss': bankroll['profit_loss'],
            'roi_pct': bankroll['roi_pct'],
            'total_bets': bankroll['total_bets'],
            'weekly_transactions': bankroll.get('weekly_transactions', 0),
            'weekly_profit': bankroll.get('weekly_profit', 0),
            'risk_profile': bankroll['risk_profile'],
            'stop_loss_triggered': bankroll['stop_loss_triggered']
        }
    
    def _generate_html(self, report: Dict) -> str:
        """Génère le rapport en HTML."""
        bankroll = report['bankroll_summary']
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NBA Betting Report - {self.report_date.strftime('%Y-%m-%d')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #17408B; border-bottom: 3px solid #17408B; padding-bottom: 10px; }}
        h2 {{ color: #C9082A; margin-top: 30px; }}
        .metric {{ display: inline-block; margin: 10px 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #17408B; }}
        .metric-label {{ font-size: 12px; color: #666; }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #17408B; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        .recommendation {{ background: #d4edda; padding: 10px; margin: 5px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏀 NBA Weekly Betting Report</h1>
        <p><strong>Week:</strong> {self.week_start.strftime('%Y-%m-%d')} to {self.report_date.strftime('%Y-%m-%d')}</p>
        <p><strong>Profile:</strong> {bankroll['risk_profile'].upper()}</p>
        
        <h2>💰 Bankroll Summary</h2>
        <div class="metric">
            <div class="metric-value">{bankroll['current']:.2f}€</div>
            <div class="metric-label">Current Balance</div>
        </div>
        <div class="metric">
            <div class="metric-value {'positive' if bankroll['profit_loss'] >= 0 else 'negative'}">{bankroll['profit_loss']:+.2f}€</div>
            <div class="metric-label">Profit/Loss</div>
        </div>
        <div class="metric">
            <div class="metric-value {'positive' if bankroll['roi_pct'] >= 0 else 'negative'}">{bankroll['roi_pct']:+.1f}%</div>
            <div class="metric-label">ROI</div>
        </div>
        <div class="metric">
            <div class="metric-value">{bankroll['total_bets']}</div>
            <div class="metric-label">Total Bets</div>
        </div>
        
        <h2>🎯 Recommendations</h2>
        {''.join(f'<div class="recommendation">{rec}</div>' for rec in report['recommendations'])}
        
        <h2>📊 Value Bets This Week</h2>
        <table>
            <tr>
                <th>Match</th>
                <th>Prediction</th>
                <th>Edge</th>
                <th>Odds</th>
                <th>Recommended Stake</th>
            </tr>
            {''.join(f"<tr><td>{vb['match']}</td><td>{vb['prediction']}</td><td>{vb['edge']}%</td><td>{vb['odds']}</td><td>{vb['recommended_stake']}€</td></tr>" for vb in report['value_bets'][:10])}
        </table>
        
        <p style="margin-top: 40px; color: #666; font-size: 12px;">
            Generated by NBA Betting System | {self.email}
        </p>
    </div>
</body>
</html>
        """
        return html
    
    def send_email_report(self):
        """Envoie le rapport par email."""
        try:
            from src.utils.alerts import AlertManager
            
            files = self.generate_and_save()
            report = files['report']
            
            subject = f"NBA Weekly Betting Report - {self.report_date.strftime('%Y-%m-%d')}"
            
            message = f"""
Weekly Betting Report

Bankroll: {report['bankroll_summary']['current']:.2f}€ ({report['bankroll_summary']['profit_loss']:+.2f}€)
ROI: {report['bankroll_summary']['roi_pct']:+.1f}%
Total Bets: {report['bankroll_summary']['total_bets']}

Value Bets This Week: {len(report['value_bets'])}

Recommendations:
{chr(10).join(f"- {rec}" for rec in report['recommendations'])}

Full report attached.
            """
            
            alert_manager = AlertManager()
            alert_manager.send_alert(
                level='info',
                message=message,
                source='weekly_report'
            )
            
            logger.info(f"📧 Rapport envoyé à {self.email}")
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi email: {e}")


def main():
    """Point d'entrée pour générer le rapport hebdomadaire."""
    print("=" * 70)
    print("GENERATION RAPPORT HEBDOMADAIRE BETTING")
    print("=" * 70)
    
    report_gen = WeeklyBettingReport()
    files = report_gen.generate_and_save()
    
    print(f"\n✅ Rapport généré:")
    print(f"   JSON: {files['json']}")
    print(f"   CSV: {files['csv']}")
    print(f"   HTML: {files['html']}")
    
    # Affiche un résumé
    report = files['report']
    bankroll = report['bankroll_summary']
    
    print(f"\n📊 Résumé:")
    print(f"   Bankroll: {bankroll['current']:.2f}€")
    print(f"   P&L: {bankroll['profit_loss']:+.2f}€")
    print(f"   ROI: {bankroll['roi_pct']:+.1f}%")
    print(f"   Value bets: {len(report['value_bets'])}")
    
    # Envoi email optionnel
    send_email = input("\n📧 Envoyer par email? (y/n): ").lower() == 'y'
    if send_email:
        report_gen.send_email_report()
    
    print("\n✅ Terminé!")
    
    return files


if __name__ == "__main__":
    main()
