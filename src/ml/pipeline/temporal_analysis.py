"""
NBA Analytics: Temporal Analysis Module
Analyse temporelle des performances 2025-26 par période
Étend DataDriftMonitor pour réutiliser le monitoring existant

Usage:
    from src.ml.pipeline.temporal_analysis import TemporalAnalyzer
    
    analyzer = TemporalAnalyzer()
    results = analyzer.analyze_2025_26_by_period()
    analyzer.generate_temporal_report()
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import sys

# Import monitoring centralisé (NBA-28)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.monitoring import get_logger, PipelineMetrics

logger = get_logger(__name__)


class TemporalAnalyzer:
    """
    Analyse temporelle des performances par période.
    
    Permet de comprendre comment l'accuracy évolue au fil de la saison
    et d'identifier le seuil minimal d'historique pour des prédictions fiables.
    """
    
    def __init__(self, data_path: str = None):
        """
        Initialise l'analyseur temporel.
        
        Args:
            data_path: Chemin vers les données 2025-26 (default: auto-detect)
        """
        self.data_path = Path(data_path) if data_path else self._auto_detect_data_path()
        self.df = None
        self.metrics = PipelineMetrics("temporal_analysis")
        
        logger.info(f"TemporalAnalyzer initialisé avec: {self.data_path}")
    
    def _auto_detect_data_path(self) -> Path:
        """Détecte automatiquement le chemin des données 2025-26"""
        default_path = Path("data/gold/ml_features/features_2025-26_v3.parquet")
        if default_path.exists():
            return default_path
        
        # Chercher d'autres fichiers
        alternatives = [
            "data/gold/ml_features/features_2025-26_progressive.parquet",
            "data/gold/ml_features/features_2025-26_v3_real.parquet"
        ]
        for alt in alternatives:
            if Path(alt).exists():
                return Path(alt)
        
        return default_path
    
    def load_data(self) -> pd.DataFrame:
        """Charge les données 2025-26"""
        logger.info(f"Chargement des données depuis {self.data_path}...")
        
        if not self.data_path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {self.data_path}")
        
        self.df = pd.read_parquet(self.data_path)
        
        # Convertir game_date en datetime si nécessaire
        if 'game_date' in self.df.columns:
            self.df['game_date'] = pd.to_datetime(self.df['game_date'])
        
        logger.info(f"✅ {len(self.df)} matchs chargés")
        logger.info(f"   Période: {self.df['game_date'].min()} à {self.df['game_date'].max()}")
        
        self.metrics.record_volume("matches_loaded", len(self.df))
        return self.df
    
    def analyze_by_month(self) -> Dict:
        """
        Analyse l'accuracy par mois (Oct, Nov, Dec, Jan, Feb).
        
        Returns:
            Dict avec métriques par mois
        """
        if self.df is None:
            self.load_data()
        
        logger.info("\n📊 Analyse par mois...")
        
        # Créer colonne mois-année
        self.df['month_year'] = self.df['game_date'].dt.to_period('M')
        
        results = {}
        for month_period in sorted(self.df['month_year'].unique()):
            month_df = self.df[self.df['month_year'] == month_period]
            month_str = str(month_period)
            
            metrics = self._calculate_period_metrics(month_df, month_str)
            results[month_str] = metrics
            
            logger.info(f"\n{month_str}:")
            logger.info(f"  Matchs: {metrics['n_matches']}")
            logger.info(f"  Accuracy: {metrics['accuracy']:.2%}")
            logger.info(f"  Games played (moy): {metrics['avg_games_played']:.0f}")
        
        return results
    
    def analyze_by_games_played(self, bins: List[int] = None) -> Dict:
        """
        Analyse l'accuracy par nombre de matchs joués (histogramme).
        
        Args:
            bins: List des seuils de matchs [0, 50, 100, 150, 200]
            
        Returns:
            Dict avec métriques par tranche
        """
        if self.df is None:
            self.load_data()
        
        if bins is None:
            bins = [0, 50, 100, 150, 200, 300]
        
        logger.info(f"\n📊 Analyse par nombre de matchs joués...")
        
        # Estimer le nombre de matchs joués avant chaque match
        # (approximation: utiliser l'index chronologique)
        self.df = self.df.sort_values('game_date')
        self.df['match_number'] = range(1, len(self.df) + 1)
        
        results = {}
        for i in range(len(bins) - 1):
            min_games = bins[i]
            max_games = bins[i + 1]
            
            mask = (self.df['match_number'] >= min_games) & (self.df['match_number'] < max_games)
            period_df = self.df[mask]
            
            if len(period_df) > 0:
                period_name = f"{min_games}-{max_games}_games"
                metrics = self._calculate_period_metrics(period_df, period_name)
                results[period_name] = metrics
                
                logger.info(f"\nMatchs {min_games}-{max_games}:")
                logger.info(f"  Nombre: {metrics['n_matches']}")
                logger.info(f"  Accuracy: {metrics['accuracy']:.2%}")
        
        return results
    
    def find_accuracy_inflection_point(self) -> Dict:
        """
        Trouve le point d'inflexion où l'accuracy devient stable.
        
        Returns:
            Dict avec le seuil minimal recommandé
        """
        if self.df is None:
            self.load_data()
        
        logger.info("\n🔍 Recherche du point d'inflexion...")
        
        # Calculer accuracy cumulée
        self.df = self.df.sort_values('game_date')
        self.df['cumulative_accuracy'] = self.df['target'].expanding().mean()
        self.df['match_number'] = range(1, len(self.df) + 1)
        
        # Trouver où l'accuracy dépasse 60%
        threshold = 0.60
        above_threshold = self.df[self.df['cumulative_accuracy'] >= threshold]
        
        if len(above_threshold) > 0:
            first_above = above_threshold.iloc[0]
            inflection_match = first_above['match_number']
            inflection_date = first_above['game_date']
            
            result = {
                'threshold': threshold,
                'inflection_match': int(inflection_match),
                'inflection_date': inflection_date.strftime('%Y-%m-%d'),
                'accuracy_at_inflection': float(first_above['cumulative_accuracy']),
                'recommendation': f"Attendre ~{inflection_match} matchs pour prédire"
            }
        else:
            result = {
                'threshold': threshold,
                'inflection_match': None,
                'recommendation': "Seuil de 60% non atteint dans la saison"
            }
        
        logger.info(f"✅ Point d'inflexion: {result['inflection_match']} matchs")
        logger.info(f"   Date: {result.get('inflection_date', 'N/A')}")
        
        return result
    
    def _calculate_period_metrics(self, df: pd.DataFrame, period_name: str) -> Dict:
        """
        Calcule les métriques pour une période donnée.
        
        Args:
            df: DataFrame filtré pour la période
            period_name: Nom de la période
            
        Returns:
            Dict avec métriques complètes
        """
        n_matches = len(df)
        
        if n_matches == 0:
            return {
                'period': period_name,
                'n_matches': 0,
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'avg_games_played': 0
            }
        
        # Métriques de base
        accuracy = df['target'].mean() if 'target' in df.columns else 0.0
        
        # Calculer nombre moyen de matchs joués (approximation)
        if 'match_number' in df.columns:
            avg_games = df['match_number'].mean()
        else:
            avg_games = n_matches / 2  # Approximation
        
        return {
            'period': period_name,
            'n_matches': n_matches,
            'accuracy': float(accuracy),
            'avg_games_played': float(avg_games),
            'start_date': df['game_date'].min().strftime('%Y-%m-%d') if 'game_date' in df.columns else None,
            'end_date': df['game_date'].max().strftime('%Y-%m-%d') if 'game_date' in df.columns else None
        }
    
    def generate_temporal_report(self, output_path: str = None) -> str:
        """
        Génère un rapport complet d'analyse temporelle.
        
        Args:
            output_path: Chemin de sortie (default: reports/temporal_analysis_YYYYMMDD.json)
            
        Returns:
            Chemin du rapport généré
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d')
            output_path = f"reports/temporal_analysis_{timestamp}.json"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"\n📝 Génération du rapport temporel...")
        
        # Collecter toutes les analyses
        report = {
            'generated_at': datetime.now().isoformat(),
            'data_source': str(self.data_path),
            'total_matches': len(self.df) if self.df is not None else 0,
            'by_month': self.analyze_by_month(),
            'by_games_played': self.analyze_by_games_played(),
            'inflection_point': self.find_accuracy_inflection_point(),
            'recommendations': self._generate_recommendations()
        }
        
        # Sauvegarder
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✅ Rapport sauvegardé: {output_path}")
        self.metrics.finalize("success")
        
        return str(output_path)
    
    def _generate_recommendations(self) -> List[str]:
        """Génère des recommandations basées sur l'analyse"""
        recommendations = []
        
        # Analyser les résultats par mois
        month_results = self.analyze_by_month()
        
        # Recommandation 1: Quand commencer à prédire
        oct_nov_acc = month_results.get('2025-10', {}).get('accuracy', 0)
        if oct_nov_acc < 0.58:
            recommendations.append(
                "Attendre décembre pour prédire (accuracy Oct-Nov < 58%)"
            )
        
        # Recommandation 2: Période optimale
        best_month = max(month_results.items(), key=lambda x: x[1].get('accuracy', 0))
        recommendations.append(
            f"Meilleure période: {best_month[0]} ({best_month[1].get('accuracy', 0):.1%} accuracy)"
        )
        
        # Recommandation 3: Seuil de confiance
        inflection = self.find_accuracy_inflection_point()
        if inflection.get('inflection_match'):
            recommendations.append(
                f"Utiliser seuil de confiance élevé (≥70%) avant {inflection['inflection_match']} matchs"
            )
        
        return recommendations
    
    def run_full_analysis(self) -> Dict:
        """
        Exécute l'analyse temporelle complète.
        
        Returns:
            Dict avec tous les résultats
        """
        logger.info("=" * 60)
        logger.info("ANALYSE TEMPORELLE COMPLÈTE - NBA 2025-26")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # Charger données
        self.load_data()
        
        # Analyses
        results = {
            'by_month': self.analyze_by_month(),
            'by_games_played': self.analyze_by_games_played(),
            'inflection_point': self.find_accuracy_inflection_point()
        }
        
        # Générer rapport
        report_path = self.generate_temporal_report()
        results['report_path'] = report_path
        
        duration = (datetime.now() - start_time).total_seconds()
        self.metrics.record_timing("full_analysis", duration)
        
        logger.info(f"\n✅ Analyse terminée en {duration:.1f}s")
        logger.info(f"📄 Rapport: {report_path}")
        
        return results


# Point d'entrée pour exécution directe
if __name__ == "__main__":
    analyzer = TemporalAnalyzer()
    results = analyzer.run_full_analysis()
    
    print("\n" + "=" * 60)
    print("RÉSULTATS DE L'ANALYSE TEMPORELLE")
    print("=" * 60)
    
    print("\n📅 Par mois:")
    for month, metrics in results['by_month'].items():
        print(f"  {month}: {metrics['accuracy']:.2%} ({metrics['n_matches']} matchs)")
    
    print("\n🎯 Point d'inflexion:")
    inflection = results['inflection_point']
    print(f"  Seuil: {inflection['threshold']:.0%}")
    print(f"  Atteint après: {inflection.get('inflection_match', 'N/A')} matchs")
    print(f"  Recommandation: {inflection['recommendation']}")
