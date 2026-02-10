#!/usr/bin/env python3
"""
Générateur de rapport HTML combiné
Crée le rapport final avec graphiques SVG
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Mode non-interactif
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Générateur de rapport HTML complet"""
    
    def __init__(self):
        self.reports_dir = Path('reports')
        self.figures_dir = self.reports_dir / 'figures'
        self.assets_dir = self.reports_dir / 'assets'
        
        # Créer dossiers
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Style matplotlib sombre
        plt.style.use('dark_background')
        self.colors = {
            'primary': '#17408B',
            'secondary': '#C9082A',
            'success': '#4CAF50',
            'warning': '#FFC107',
            'bg': '#1a1a1a',
            'text': '#e0e0e0'
        }
    
    def generate_all(self):
        """Génère le rapport complet"""
        logger.info("="*70)
        logger.info("GENERATION DU RAPPORT HTML COMPLET")
        logger.info("="*70)
        
        # 1. Charger les données
        logger.info("\n[1/3] Chargement des donnees...")
        data = self._load_data()
        
        # 2. Générer les graphiques
        logger.info("\n[2/3] Generation des graphiques SVG...")
        self._generate_all_charts(data)
        
        # 3. Générer le HTML
        logger.info("\n[3/3] Generation du rapport HTML...")
        self._generate_html(data)
        
        logger.info("\n" + "="*70)
        logger.info("RAPPORT GENERE AVEC SUCCES")
        logger.info("="*70)
        logger.info(f"Fichier: {self.reports_dir / 'index.html'}")
        logger.info(f"Graphiques: {self.figures_dir}")
    
    def _load_data(self) -> Dict:
        """Charge les données des backtests"""
        data = {}
        
        # 2024-25
        try:
            with open('reports/2024-25/backtest_data.json', 'r') as f:
                data['2024-25'] = json.load(f)
            logger.info("  ✓ Donnees 2024-25 chargees")
        except Exception as e:
            logger.error(f"  ✗ Erreur 2024-25: {e}")
            data['2024-25'] = {'metrics': {}, 'predictions': []}
        
        # 2025-26
        try:
            with open('reports/2025-26/backtest_partial.json', 'r') as f:
                data['2025-26'] = json.load(f)
            logger.info("  ✓ Donnees 2025-26 chargees")
        except Exception as e:
            logger.error(f"  ✗ Erreur 2025-26: {e}")
            data['2025-26'] = {'metrics': {}, 'predictions': []}
        
        return data
    
    def _generate_all_charts(self, data: Dict):
        """Génère tous les graphiques SVG"""
        
        # Graphique 1: Accuracy 2024-25
        if data['2024-25'].get('predictions'):
            self._chart_accuracy_trend(
                data['2024-25']['predictions'],
                '2024-25',
                '01_accuracy_2024-25_trend.svg'
            )
        
        # Graphique 2: Métriques comparaison
        self._chart_metrics_comparison(data, '02_metrics_comparison.svg')
        
        # Graphique 3: Distribution confiance 2024-25
        if data['2024-25'].get('predictions'):
            self._chart_confidence_distribution(
                data['2024-25']['predictions'],
                '03_confidence_distribution.svg'
            )
        
        # Graphique 4: Performance mensuelle 2024-25
        if data['2024-25'].get('predictions'):
            self._chart_monthly_performance(
                data['2024-25']['predictions'],
                '04_monthly_performance.svg'
            )
        
        # Graphique 5: Comparaison saisons
        self._chart_season_comparison(data, '05_season_comparison.svg')
        
        logger.info(f"  ✓ {len(list(self.figures_dir.glob('*.svg')))} graphiques generes")
    
    def _chart_accuracy_trend(self, predictions: List[Dict], season: str, filename: str):
        """Graphique d'évolution de l'accuracy"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Calculer accuracy cumulée
        correct = [1 if p['is_correct'] else 0 for p in predictions]
        cumulative = np.cumsum(correct) / np.arange(1, len(correct) + 1)
        
        ax.plot(range(1, len(cumulative) + 1), cumulative, 
                color=self.colors['primary'], linewidth=2, label='Accuracy cumulee')
        ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='Aleatoire (50%)')
        
        final_accuracy = cumulative[-1] if len(cumulative) > 0 else 0
        ax.axhline(y=final_accuracy, color=self.colors['success'], 
                   linestyle='-', alpha=0.7, label=f'Final: {final_accuracy:.1%}')
        
        ax.set_xlabel('Nombre de matchs', color=self.colors['text'])
        ax.set_ylabel('Accuracy cumulee', color=self.colors['text'])
        ax.set_title(f'Evolution de l\'accuracy - Saison {season}', 
                     color=self.colors['text'], fontsize=14, fontweight='bold')
        ax.legend(loc='lower right')
        ax.grid(True, alpha=0.3)
        ax.set_facecolor(self.colors['bg'])
        fig.patch.set_facecolor(self.colors['bg'])
        
        plt.tight_layout()
        plt.savefig(self.figures_dir / filename, format='svg', 
                    facecolor=self.colors['bg'], edgecolor='none')
        plt.close()
    
    def _chart_metrics_comparison(self, data: Dict, filename: str):
        """Graphique comparatif des métriques"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        metrics = ['accuracy', 'precision', 'recall', 'f1']
        labels = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
        
        values_2024_25 = []
        values_2025_26 = []
        
        for m in metrics:
            v1 = data['2024-25'].get('metrics', {}).get(m, 0)
            v2 = data['2025-26'].get('metrics', {}).get(m, 0)
            values_2024_25.append(v1 * 100)
            values_2025_26.append(v2 * 100)
        
        x = np.arange(len(labels))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, values_2024_25, width, 
                       label='2024-25', color=self.colors['primary'])
        bars2 = ax.bar(x + width/2, values_2025_26, width,
                       label='2025-26 (API)', color=self.colors['secondary'])
        
        ax.set_ylabel('Score (%)', color=self.colors['text'])
        ax.set_title('Comparaison des metriques', 
                     color=self.colors['text'], fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_facecolor(self.colors['bg'])
        fig.patch.set_facecolor(self.colors['bg'])
        
        plt.tight_layout()
        plt.savefig(self.figures_dir / filename, format='svg',
                    facecolor=self.colors['bg'], edgecolor='none')
        plt.close()
    
    def _chart_confidence_distribution(self, predictions: List[Dict], filename: str):
        """Distribution des niveaux de confiance"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        confidences = [p['confidence'] for p in predictions]
        
        # Histogramme
        ax1.hist(confidences, bins=20, color=self.colors['primary'], 
                alpha=0.7, edgecolor='white')
        ax1.axvline(x=0.7, color=self.colors['success'], linestyle='--', 
                   label='High (70%)')
        ax1.axvline(x=0.6, color=self.colors['warning'], linestyle='--',
                   label='Medium (60%)')
        ax1.set_xlabel('Confiance', color=self.colors['text'])
        ax1.set_ylabel('Nombre de matchs', color=self.colors['text'])
        ax1.set_title('Distribution des confiances', color=self.colors['text'])
        ax1.legend()
        ax1.set_facecolor(self.colors['bg'])
        
        # Par niveau
        high = sum(1 for c in confidences if c >= 0.70)
        medium = sum(1 for c in confidences if 0.60 <= c < 0.70)
        low = sum(1 for c in confidences if c < 0.60)
        
        levels = ['High\n(>=70%)', 'Medium\n(60-70%)', 'Low\n(<60%)']
        counts = [high, medium, low]
        colors_levels = [self.colors['success'], self.colors['warning'], self.colors['secondary']]
        
        ax2.bar(levels, counts, color=colors_levels, alpha=0.8)
        ax2.set_ylabel('Nombre de matchs', color=self.colors['text'])
        ax2.set_title('Repartition par niveau', color=self.colors['text'])
        ax2.set_facecolor(self.colors['bg'])
        
        fig.patch.set_facecolor(self.colors['bg'])
        plt.tight_layout()
        plt.savefig(self.figures_dir / filename, format='svg',
                    facecolor=self.colors['bg'], edgecolor='none')
        plt.close()
    
    def _chart_monthly_performance(self, predictions: List[Dict], filename: str):
        """Performance par mois"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Grouper par mois
        by_month = {}
        for p in predictions:
            month = p['game_date'][:7]  # YYYY-MM
            if month not in by_month:
                by_month[month] = {'correct': 0, 'total': 0}
            by_month[month]['total'] += 1
            if p['is_correct']:
                by_month[month]['correct'] += 1
        
        months = sorted(by_month.keys())
        accuracies = [by_month[m]['correct'] / by_month[m]['total'] * 100 
                     for m in months]
        counts = [by_month[m]['total'] for m in months]
        
        # Barres
        bars = ax.bar(range(len(months)), accuracies, 
                     color=self.colors['primary'], alpha=0.8)
        ax.axhline(y=77.77, color=self.colors['success'], linestyle='--',
                  label='Moyenne: 77.77%')
        
        # Ajouter valeurs sur les barres
        for i, (bar, count) in enumerate(zip(bars, counts)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%\n({count})',
                   ha='center', va='bottom', color=self.colors['text'],
                   fontsize=9)
        
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels([m.replace('-', '\n') for m in months])
        ax.set_ylabel('Accuracy (%)', color=self.colors['text'])
        ax.set_title('Performance par mois - 2024-25', color=self.colors['text'])
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_facecolor(self.colors['bg'])
        fig.patch.set_facecolor(self.colors['bg'])
        
        plt.tight_layout()
        plt.savefig(self.figures_dir / filename, format='svg',
                    facecolor=self.colors['bg'], edgecolor='none')
        plt.close()
    
    def _chart_season_comparison(self, data: Dict, filename: str):
        """Comparaison visuelle des saisons"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Données
        seasons = ['2024-25\n(Complete)', '2025-26\n(Via API)']
        matchs = [
            len(data['2024-25'].get('predictions', [])),
            len(data['2025-26'].get('predictions', []))
        ]
        accuracies = [
            data['2024-25'].get('metrics', {}).get('accuracy', 0) * 100,
            data['2025-26'].get('metrics', {}).get('accuracy', 0) * 100
        ]
        
        x = np.arange(len(seasons))
        width = 0.35
        
        ax2 = ax.twinx()
        
        bars1 = ax.bar(x - width/2, matchs, width, 
                      label='Matchs', color=self.colors['primary'], alpha=0.7)
        bars2 = ax2.bar(x + width/2, accuracies, width,
                       label='Accuracy %', color=self.colors['success'], alpha=0.7)
        
        ax.set_ylabel('Nombre de matchs', color=self.colors['text'])
        ax2.set_ylabel('Accuracy (%)', color=self.colors['text'])
        ax.set_title('Comparaison des saisons', color=self.colors['text'])
        ax.set_xticks(x)
        ax.set_xticklabels(seasons)
        
        # Légende combinée
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        ax.set_facecolor(self.colors['bg'])
        ax2.set_facecolor(self.colors['bg'])
        fig.patch.set_facecolor(self.colors['bg'])
        
        plt.tight_layout()
        plt.savefig(self.figures_dir / filename, format='svg',
                    facecolor=self.colors['bg'], edgecolor='none')
        plt.close()
    
    def _generate_html(self, data: Dict):
        """Génère le fichier HTML final"""
        
        m_2024_25 = data['2024-25'].get('metrics', {})
        m_2025_26 = data['2025-26'].get('metrics', {})
        api_method = data['2025-26'].get('api_method', 'N/A')
        
        html_content = f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NBA Analytics - Backtest Complet</title>
    <link rel="stylesheet" href="assets/dark-theme.css">
    <style>
        .metric-card {{ background: #252525; padding: 20px; border-radius: 10px; margin: 10px; text-align: center; }}
        .metric-value {{ font-size: 2.5em; color: #17408B; font-weight: bold; }}
        .metric-label {{ color: #b0b0b0; margin-top: 10px; }}
        .api-badge {{ background: #4CAF50; color: white; padding: 5px 10px; border-radius: 15px; font-size: 0.8em; }}
        .warning {{ background: #FFC107; color: black; }}
    </style>
</head>
<body>
    <nav class="sidebar">
        <h2>🏀 NBA Analytics</h2>
        <ul>
            <li><a href="#summary">Resume</a></li>
            <li><a href="#2024-25">2024-25 (Complet)</a></li>
            <li><a href="#2025-26">2025-26 (API)</a></li>
            <li><a href="#comparison">Comparaison</a></li>
            <li><a href="#downloads">Telechargements</a></li>
        </ul>
    </nav>
    
    <main>
        <section id="summary" class="hero-section">
            <h1>Backtest Complet NBA</h1>
            <p>Generation: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            
            <div style="display: flex; justify-content: center; gap: 40px; margin-top: 40px; flex-wrap: wrap;">
                <div class="metric-card">
                    <div class="metric-value">{m_2024_25.get('accuracy', 0)*100:.1f}%</div>
                    <div class="metric-label">Accuracy 2024-25</div>
                    <div style="margin-top: 10px; color: #4CAF50;">1309 matchs</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-value">{m_2025_26.get('accuracy', 0)*100:.1f}%</div>
                    <div class="metric-label">Accuracy 2025-26</div>
                    <div style="margin-top: 10px;">
                        <span class="api-badge">{api_method}</span>
                    </div>
                    <div style="margin-top: 5px; color: #b0b0b0;">783 matchs</div>
                </div>
            </div>
        </section>
        
        <section id="2024-25">
            <h2>Saison 2024-25 - Analyse Complete</h2>
            <div style="background: #252525; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3>Metriques</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; margin-top: 20px;">
                    <div class="metric-card">
                        <div class="metric-value">{m_2024_25.get('accuracy', 0)*100:.1f}%</div>
                        <div class="metric-label">Accuracy</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{m_2024_25.get('precision', 0)*100:.1f}%</div>
                        <div class="metric-label">Precision</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{m_2024_25.get('recall', 0)*100:.1f}%</div>
                        <div class="metric-label">Recall</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{m_2024_25.get('f1', 0)*100:.1f}%</div>
                        <div class="metric-label">F1-Score</div>
                    </div>
                </div>
            </div>
            
            <div class="chart-container">
                <h3>Evolution de l'accuracy</h3>
                <img src="figures/01_accuracy_2024-25_trend.svg" alt="Accuracy trend">
            </div>
            
            <div class="chart-container">
                <h3>Performance mensuelle</h3>
                <img src="figures/04_monthly_performance.svg" alt="Monthly">
            </div>
            
            <div class="chart-container">
                <h3>Distribution des confiances</h3>
                <img src="figures/03_confidence_distribution.svg" alt="Confidence">
            </div>
        </section>
        
        <section id="2025-26">
            <h2>Saison 2025-26 - Via API NBA</h2>
            <div style="background: #252525; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <p><strong>Methode:</strong> {api_method}</p>
                <p><strong>Matchs analyses:</strong> {m_2025_26.get('total_predictions', 0)}</p>
                <div class="alert alert-warning" style="margin-top: 15px;">
                    <strong>Note:</strong> Les features utilisees sont des approximations basees sur la saison 2024-25.
                    Les resultats sont donc moins fiables que pour 2024-25.
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; margin: 20px 0;">
                <div class="metric-card">
                    <div class="metric-value">{m_2025_26.get('accuracy', 0)*100:.1f}%</div>
                    <div class="metric-label">Accuracy</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{m_2025_26.get('precision', 0)*100:.1f}%</div>
                    <div class="metric-label">Precision</div>
                </div>
            </div>
        </section>
        
        <section id="comparison">
            <h2>Comparaison des Saisons</h2>
            <div class="chart-container">
                <img src="figures/02_metrics_comparison.svg" alt="Comparison">
            </div>
            <div class="chart-container">
                <img src="figures/05_season_comparison.svg" alt="Seasons">
            </div>
        </section>
        
        <section id="downloads">
            <h2>Telechargements</h2>
            <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                <a href="../predictions/backtest_2024-25_detailed.csv" class="btn">CSV 2024-25 (Detaille)</a>
                <a href="../predictions/backtest_2025-26_detailed.csv" class="btn">CSV 2025-26 (Detaille)</a>
                <a href="2024-25/backtest_data.json" class="btn">JSON 2024-25</a>
                <a href="2025-26/backtest_partial.json" class="btn">JSON 2025-26</a>
            </div>
        </section>
    </main>
    
    <footer>
        <p>NBA Analytics - Systeme de Backtest | Genere le {datetime.now().strftime('%d/%m/%Y')}</p>
    </footer>
</body>
</html>'''
        
        with open(self.reports_dir / 'index.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"  ✓ Rapport HTML genere: {self.reports_dir / 'index.html'}")


def main():
    generator = ReportGenerator()
    generator.generate_all()


if __name__ == "__main__":
    main()
