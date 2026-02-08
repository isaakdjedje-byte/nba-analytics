#!/usr/bin/env python3
"""
Tracking ROI - Systeme de suivi des performances des predictions
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ROITracker:
    """
    Suivi des performances des predictions NBA.
    
    Fonctionnalites:
    - Enregistrement des predictions et resultats reels
    - Calcul du ROI pour differentes strategies
    - Generation de rapports de performance
    """
    
    def __init__(self, tracking_dir: str = "predictions"):
        self.tracking_dir = Path(tracking_dir)
        self.tracking_file = self.tracking_dir / "tracking_history.csv"
        self.load_history()
        
    def load_history(self):
        """Charge l'historique des predictions."""
        if self.tracking_file.exists():
            self.history = pd.read_csv(self.tracking_file)
            logger.info(f"[OK] Historique charge: {len(self.history)} predictions")
        else:
            self.history = pd.DataFrame(columns=[
                'date', 'home_team', 'away_team', 'prediction', 
                'proba_home_win', 'confidence', 'recommendation',
                'actual_result', 'home_won', 'correct', 'roi'
            ])
            logger.info("[OK] Nouvel historique cree")
            
    def add_prediction(self, prediction: dict, actual_result: str = None):
        """
        Ajoute une prediction a l'historique.
        
        Args:
            prediction: Dict avec les infos de prediction
            actual_result: 'HOME_WIN', 'AWAY_WIN', ou None si pas encore joue
        """
        entry = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'home_team': prediction['home_team'],
            'away_team': prediction['away_team'],
            'prediction': prediction['prediction'],
            'proba_home_win': prediction['proba_home_win'],
            'confidence': prediction['confidence'],
            'recommendation': prediction['recommendation'],
            'actual_result': actual_result,
            'home_won': 1 if actual_result == 'HOME_WIN' else (0 if actual_result == 'AWAY_WIN' else None),
            'correct': None,
            'roi': None
        }
        
        # Calculer si correct (si resultat connu)
        if actual_result:
            predicted_home_win = prediction['prediction'] == 'Home Win'
            actual_home_win = actual_result == 'HOME_WIN'
            entry['correct'] = 1 if predicted_home_win == actual_home_win else 0
            
            # Calcul ROI simple (1 si correct, -1 si faux)
            entry['roi'] = 1 if entry['correct'] == 1 else -1
        
        # Ajouter a l'historique
        self.history = pd.concat([self.history, pd.DataFrame([entry])], ignore_index=True)
        
    def update_result(self, home_team: str, away_team: str, date: str, actual_result: str):
        """
        Met a jour le resultat reel d'une prediction.
        
        Args:
            home_team: Nom equipe domicile
            away_team: Nom equipe exterieur
            date: Date du match (YYYY-MM-DD)
            actual_result: 'HOME_WIN' ou 'AWAY_WIN'
        """
        mask = (
            (self.history['home_team'] == home_team) & 
            (self.history['away_team'] == away_team) &
            (self.history['date'] == date)
        )
        
        if mask.sum() == 0:
            logger.warning(f"Prediction non trouvee: {home_team} vs {away_team} ({date})")
            return
            
        # Mettre a jour
        self.history.loc[mask, 'actual_result'] = actual_result
        self.history.loc[mask, 'home_won'] = 1 if actual_result == 'HOME_WIN' else 0
        
        # Recalculer correct et ROI
        for idx in self.history[mask].index:
            pred = self.history.loc[idx, 'prediction']
            predicted_home_win = pred == 'Home Win'
            actual_home_win = actual_result == 'HOME_WIN'
            self.history.loc[idx, 'correct'] = 1 if predicted_home_win == actual_home_win else 0
            self.history.loc[idx, 'roi'] = 1 if self.history.loc[idx, 'correct'] == 1 else -1
            
        logger.info(f"[OK] Resultat mis a jour: {home_team} vs {away_team} -> {actual_result}")
        
    def calculate_roi(self, strategy: str = 'all', days: int = None) -> dict:
        """
        Calcule le ROI pour une strategie donnee.
        
        Args:
            strategy: 'all', 'high_confidence', 'medium_confidence', 'low_confidence'
            days: Nombre de jours a considerer (None = tout l'historique)
            
        Returns:
            Dict avec les metriques de performance
        """
        df = self.history.copy()
        
        # Filtrer les predictions avec resultats connus
        df = df[df['actual_result'].notna()]
        
        if len(df) == 0:
            return {'error': 'Aucun resultat connu'}
            
        # Filtrer par periode
        if days:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            df = df[df['date'] >= cutoff_date]
            
        # Filtrer par strategie
        if strategy == 'high_confidence':
            df = df[df['recommendation'] == 'HIGH_CONFIDENCE']
        elif strategy == 'medium_confidence':
            df = df[df['recommendation'] == 'MEDIUM_CONFIDENCE']
        elif strategy == 'low_confidence':
            df = df[df['recommendation'] == 'LOW_CONFIDENCE']
            
        if len(df) == 0:
            return {'error': f'Aucune prediction pour strategie {strategy}'}
            
        # Calculs
        total_predictions = len(df)
        correct_predictions = df['correct'].sum()
        accuracy = correct_predictions / total_predictions
        total_roi = df['roi'].sum()
        avg_roi = df['roi'].mean()
        
        # Par categorie de confiance
        high_conf_acc = df[df['recommendation'] == 'HIGH_CONFIDENCE']['correct'].mean() if len(df[df['recommendation'] == 'HIGH_CONFIDENCE']) > 0 else 0
        med_conf_acc = df[df['recommendation'] == 'MEDIUM_CONFIDENCE']['correct'].mean() if len(df[df['recommendation'] == 'MEDIUM_CONFIDENCE']) > 0 else 0
        low_conf_acc = df[df['recommendation'] == 'LOW_CONFIDENCE']['correct'].mean() if len(df[df['recommendation'] == 'LOW_CONFIDENCE']) > 0 else 0
        
        return {
            'strategy': strategy,
            'total_predictions': int(total_predictions),
            'correct_predictions': int(correct_predictions),
            'accuracy': float(accuracy),
            'total_roi': float(total_roi),
            'avg_roi_per_bet': float(avg_roi),
            'high_conf_accuracy': float(high_conf_acc),
            'medium_conf_accuracy': float(med_conf_acc),
            'low_conf_accuracy': float(low_conf_acc),
            'period_days': days if days else 'all'
        }
        
    def generate_report(self) -> str:
        """Genere un rapport de performance."""
        logger.info("Generation du rapport...")
        
        report_lines = []
        report_lines.append("="*70)
        report_lines.append("RAPPORT DE PERFORMANCE NBA PREDICTIONS")
        report_lines.append("="*70)
        report_lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report_lines.append(f"Total predictions dans l'historique: {len(self.history)}")
        report_lines.append(f"Predictions avec resultats: {len(self.history[self.history['actual_result'].notna()])}")
        report_lines.append("")
        
        # ROI par strategie
        strategies = ['all', 'high_confidence', 'medium_confidence']
        for strategy in strategies:
            roi = self.calculate_roi(strategy=strategy)
            if 'error' not in roi:
                report_lines.append(f"\nStrategie: {strategy.upper()}")
                report_lines.append(f"  Predictions: {roi['total_predictions']}")
                report_lines.append(f"  Accuracy:    {roi['accuracy']:.2%}")
                report_lines.append(f"  ROI Total:   {roi['total_roi']:+.0f} (sur {roi['total_predictions']} paris)")
                report_lines.append(f"  ROI Moyen:   {roi['avg_roi_per_bet']:+.2f} par pari")
                
        # Details par niveau de confiance
        report_lines.append("\n" + "="*70)
        report_lines.append("PERFORMANCE PAR NIVEAU DE CONFIANCE")
        report_lines.append("="*70)
        
        for conf_level in ['HIGH_CONFIDENCE', 'MEDIUM_CONFIDENCE', 'LOW_CONFIDENCE']:
            df_conf = self.history[self.history['recommendation'] == conf_level]
            df_conf = df_conf[df_conf['actual_result'].notna()]
            
            if len(df_conf) > 0:
                acc = df_conf['correct'].mean()
                roi = df_conf['roi'].sum()
                report_lines.append(f"\n{conf_level}:")
                report_lines.append(f"  Nombre:   {len(df_conf)}")
                report_lines.append(f"  Accuracy: {acc:.2%}")
                report_lines.append(f"  ROI:      {roi:+.0f}")
            else:
                report_lines.append(f"\n{conf_level}: Aucune donnee")
                
        report_lines.append("\n" + "="*70)
        
        return "\n".join(report_lines)
        
    def save(self):
        """Sauvegarde l'historique."""
        self.tracking_dir.mkdir(exist_ok=True)
        self.history.to_csv(self.tracking_file, index=False)
        logger.info(f"[SAVED] Historique sauvegarde: {self.tracking_file}")
        
    def export_results(self, output_file: str = "predictions/performance_report.txt"):
        """Exporte le rapport."""
        report = self.generate_report()
        
        with open(output_file, 'w') as f:
            f.write(report)
            
        logger.info(f"[SAVED] Rapport exporte: {output_file}")
        print("\n" + report)


def demo_tracking():
    """Demonstration du tracking."""
    logger.info("=== DEMONSTRATION TRACKING ROI ===\n")
    
    tracker = ROITracker()
    
    # Simuler quelques predictions avec resultats
    predictions = [
        {'home_team': 'Boston Celtics', 'away_team': 'Lakers', 'prediction': 'Home Win', 
         'proba_home_win': 0.80, 'confidence': 0.80, 'recommendation': 'HIGH_CONFIDENCE'},
        {'home_team': 'Warriors', 'away_team': 'Suns', 'prediction': 'Home Win',
         'proba_home_win': 0.66, 'confidence': 0.66, 'recommendation': 'MEDIUM_CONFIDENCE'},
        {'home_team': 'Bucks', 'away_team': 'Heat', 'prediction': 'Home Win',
         'proba_home_win': 0.57, 'confidence': 0.57, 'recommendation': 'LOW_CONFIDENCE'}
    ]
    
    # Ajouter les predictions
    for pred in predictions:
        tracker.add_prediction(pred)
        
    # Simuler des resultats (apres les matchs)
    tracker.update_result('Boston Celtics', 'Lakers', datetime.now().strftime('%Y-%m-%d'), 'HOME_WIN')
    tracker.update_result('Warriors', 'Suns', datetime.now().strftime('%Y-%m-%d'), 'AWAY_WIN')
    tracker.update_result('Bucks', 'Heat', datetime.now().strftime('%Y-%m-%d'), 'HOME_WIN')
    
    # Sauvegarder
    tracker.save()
    
    # Generer rapport
    tracker.export_results()
    
    return tracker


if __name__ == '__main__':
    tracker = demo_tracking()
    
    # Exemple d'utilisation pour l'utilisateur
    print("\n" + "="*70)
    print("UTILISATION")
    print("="*70)
    print("""
1. Apres avoir fait des predictions:
   tracker = ROITracker()
   tracker.add_prediction(prediction_dict)
   
2. Apres les matchs, mettre a jour les resultats:
   tracker.update_result('Team A', 'Team B', '2026-02-08', 'HOME_WIN')
   
3. Voir le ROI:
   roi = tracker.calculate_roi(strategy='high_confidence')
   
4. Generer rapport:
   tracker.export_results()
    """)
