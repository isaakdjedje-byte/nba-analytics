"""
NBA-22 Optimization: Data Drift Monitoring
Surveille la dérive des données et des prédictions
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
from scipy import stats
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataDriftMonitor:
    """
    Surveille la dérive des données et des performances du modèle.
    
    Détecte:
    - Data drift: Changement dans la distribution des features
    - Concept drift: Changement dans la relation features-target
    - Performance drift: Baisse de l'accuracy
    """
    
    def __init__(self, reference_data_path, alert_threshold=0.05):
        """
        Args:
            reference_data_path: Chemin vers les données de référence (train)
            alert_threshold: Seuil pour l'alerte (p-value < threshold)
        """
        self.reference_data = pd.read_parquet(reference_data_path)
        self.alert_threshold = alert_threshold
        self.drift_history = []
        
        logger.info(f"Monitoring initialisé avec {len(self.reference_data)} échantillons de référence")
        
    def detect_feature_drift(self, current_data, feature_cols):
        """
        Détecte la dérive des features avec le test de Kolmogorov-Smirnov.
        
        Returns:
            Dict avec les features driftées et leurs p-values
        """
        drifted_features = []
        p_values = {}
        
        for col in feature_cols:
            if col in self.reference_data.columns and col in current_data.columns:
                ref_values = self.reference_data[col].dropna()
                curr_values = current_data[col].dropna()
                
                if len(ref_values) > 0 and len(curr_values) > 0:
                    # Test KS
                    ks_stat, p_value = stats.ks_2samp(ref_values, curr_values)
                    p_values[col] = p_value
                    
                    if p_value < self.alert_threshold:
                        drifted_features.append({
                            'feature': col,
                            'p_value': p_value,
                            'ks_statistic': ks_stat
                        })
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'n_features_checked': len(feature_cols),
            'n_features_drifted': len(drifted_features),
            'drifted_features': drifted_features,
            'p_values': p_values,
            'drift_detected': len(drifted_features) > 0
        }
        
        self.drift_history.append(result)
        
        if result['drift_detected']:
            logger.warning(f"🚨 DRIFT DÉTECTÉ: {len(drifted_features)} features affectées")
            for feat in drifted_features[:5]:  # Top 5
                logger.warning(f"  - {feat['feature']}: p={feat['p_value']:.4f}")
        else:
            logger.info(f"✅ Pas de drift détecté (seuil: {self.alert_threshold})")
        
        return result
    
    def detect_prediction_drift(self, predictions_history, window_size=50):
        """
        Détecte la dérive dans les prédictions.
        
        Surveille:
        - Distribution des probabilités
        - Taux de confiance élevée
        - Accuracy glissante
        """
        if len(predictions_history) < window_size:
            logger.info("Pas assez d'historique pour détecter le drift")
            return {'drift_detected': False, 'reason': 'insufficient_data'}
        
        recent = predictions_history[-window_size:]
        older = predictions_history[:-window_size][-window_size:] if len(predictions_history) > 2*window_size else predictions_history[:window_size]
        
        # Distribution des probabilités
        recent_proba = [p['proba_home_win'] for p in recent if 'proba_home_win' in p]
        older_proba = [p['proba_home_win'] for p in older if 'proba_home_win' in p]
        
        if len(recent_proba) > 0 and len(older_proba) > 0:
            ks_stat, p_value = stats.ks_2samp(older_proba, recent_proba)
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'window_size': window_size,
                'proba_drift_pvalue': p_value,
                'proba_drift_detected': p_value < self.alert_threshold,
                'recent_mean_proba': np.mean(recent_proba),
                'older_mean_proba': np.mean(older_proba)
            }
            
            if result['proba_drift_detected']:
                logger.warning(f"🚨 DRIFT dans les prédictions: p={p_value:.4f}")
            
            return result
        
        return {'drift_detected': False}
    
    def check_performance_degradation(self, tracker, min_predictions=20):
        """
        Vérifie si la performance baisse par rapport au baseline.
        
        Args:
            tracker: Instance de ROITracker
            min_predictions: Nombre minimum de prédictions pour l'analyse
        """
        df = tracker.history.copy()
        df = df[df['actual_result'].notna()]
        
        if len(df) < min_predictions:
            return {'degradation_detected': False, 'reason': 'insufficient_data'}
        
        # Accuracy récente vs globale
        recent_acc = df.tail(min_predictions)['correct'].mean()
        global_acc = df['correct'].mean()
        
        # Accuracy par stratégie
        high_conf = df[df['recommendation'] == 'HIGH_CONFIDENCE']
        recent_high = high_conf.tail(min_predictions//3)['correct'].mean() if len(high_conf) > min_predictions//3 else None
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'recent_accuracy': float(recent_acc),
            'global_accuracy': float(global_acc),
            'accuracy_drop': float(global_acc - recent_acc),
            'recent_high_conf_accuracy': float(recent_high) if recent_high is not None else None,
            'degradation_detected': recent_acc < global_acc - 0.1,  # Drop > 10%
            'n_predictions': len(df)
        }
        
        if result['degradation_detected']:
            logger.warning(f"🚨 DÉGRADATION DE PERFORMANCE: {result['accuracy_drop']:.1%} de baisse")
            logger.warning(f"  Accuracy récente: {recent_acc:.1%}")
            logger.warning(f"  Accuracy globale: {global_acc:.1%}")
        else:
            logger.info(f"✅ Performance stable: récente={recent_acc:.1%}, globale={global_acc:.1%}")
        
        return result
    
    def generate_drift_report(self):
        """Génère un rapport de drift complet."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'n_checks': len(self.drift_history),
            'drift_detected_count': sum(1 for d in self.drift_history if d.get('drift_detected', False)),
            'history': self.drift_history[-10:]  # Derniers 10 checks
        }
        
        return report
    
    def save_report(self, filepath):
        """Sauvegarde le rapport de drift."""
        report = self.generate_drift_report()
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Rapport de drift sauvegardé: {filepath}")


class PerformanceTracker:
    """
    Suit les performances du modèle dans le temps.
    """
    
    def __init__(self, tracking_dir="predictions"):
        self.tracking_dir = Path(tracking_dir)
        self.metrics_history = []
        
    def log_prediction(self, prediction_result, actual_result=None):
        """Log une prédiction avec métadonnées."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'home_team': prediction_result.get('home_team'),
            'away_team': prediction_result.get('away_team'),
            'predicted_winner': prediction_result.get('prediction'),
            'confidence': prediction_result.get('confidence'),
            'proba_home_win': prediction_result.get('proba_home_win'),
            'actual_result': actual_result,
            'correct': None
        }
        
        if actual_result:
            predicted_home_win = entry['predicted_winner'] == 'Home Win'
            actual_home_win = actual_result == 'HOME_WIN'
            entry['correct'] = predicted_home_win == actual_home_win
        
        self.metrics_history.append(entry)
        return entry
    
    def get_rolling_metrics(self, window=50):
        """Calcule les métriques glissantes."""
        if len(self.metrics_history) < window:
            return None
        
        recent = self.metrics_history[-window:]
        with_result = [r for r in recent if r['correct'] is not None]
        
        if len(with_result) == 0:
            return None
        
        accuracy = sum(r['correct'] for r in with_result) / len(with_result)
        avg_confidence = sum(r['confidence'] for r in recent) / len(recent)
        
        return {
            'window': window,
            'accuracy': accuracy,
            'avg_confidence': avg_confidence,
            'n_evaluated': len(with_result),
            'n_total': len(recent)
        }
    
    def should_retrain(self, min_predictions=100, accuracy_threshold=0.65):
        """
        Détermine si le modèle doit être réentraîné.
        
        Returns:
            Bool + raison
        """
        with_result = [r for r in self.metrics_history if r['correct'] is not None]
        
        if len(with_result) < min_predictions:
            return False, "Pas assez de données"
        
        recent = with_result[-min_predictions:]
        recent_accuracy = sum(r['correct'] for r in recent) / len(recent)
        
        if recent_accuracy < accuracy_threshold:
            return True, f"Accuracy récente ({recent_accuracy:.1%}) < seuil ({accuracy_threshold:.1%})"
        
        # Vérifier la tendance
        if len(with_result) >= 2 * min_predictions:
            older = with_result[-2*min_predictions:-min_predictions]
            older_accuracy = sum(r['correct'] for r in older) / len(older)
            
            if recent_accuracy < older_accuracy - 0.05:  # Drop de 5%
                return True, f"Baisse de performance: {older_accuracy:.1%} → {recent_accuracy:.1%}"
        
        return False, "Performance acceptable"


def check_system_health(features_path, predictions_dir="predictions", reference_path=None):
    """
    Vérifie la santé globale du système.
    
    Returns:
        Rapport de santé complet
    """
    logger.info("="*70)
    logger.info("CHECK DE SANTÉ DU SYSTÈME NBA-22")
    logger.info("="*70)
    
    health_report = {
        'timestamp': datetime.now().isoformat(),
        'status': 'OK',
        'checks': {}
    }
    
    # 1. Vérifier les données
    try:
        df = pd.read_parquet(features_path)
        health_report['checks']['data'] = {
            'status': 'OK',
            'n_matches': len(df),
            'n_features': len(df.columns)
        }
    except Exception as e:
        health_report['checks']['data'] = {'status': 'ERROR', 'error': str(e)}
        health_report['status'] = 'WARNING'
    
    # 2. Vérifier les prédictions récentes
    latest_pred = Path(predictions_dir) / "latest_predictions.csv"
    if latest_pred.exists():
        try:
            pred_df = pd.read_csv(latest_pred)
            health_report['checks']['predictions'] = {
                'status': 'OK',
                'n_predictions': len(pred_df),
                'last_update': datetime.fromtimestamp(latest_pred.stat().st_mtime).isoformat()
            }
        except Exception as e:
            health_report['checks']['predictions'] = {'status': 'ERROR', 'error': str(e)}
    else:
        health_report['checks']['predictions'] = {'status': 'MISSING'}
    
    # 3. Vérifier le tracking
    tracking_file = Path(predictions_dir) / "tracking_history.csv"
    if tracking_file.exists():
        try:
            track_df = pd.read_csv(tracking_file)
            with_result = track_df[track_df['actual_result'].notna()]
            health_report['checks']['tracking'] = {
                'status': 'OK',
                'total_predictions': len(track_df),
                'evaluated': len(with_result),
                'accuracy': float(with_result['correct'].mean()) if len(with_result) > 0 else None
            }
        except Exception as e:
            health_report['checks']['tracking'] = {'status': 'ERROR', 'error': str(e)}
    else:
        health_report['checks']['tracking'] = {'status': 'MISSING'}
    
    # Résumé
    logger.info("\nRésultats des checks:")
    for check, result in health_report['checks'].items():
        status = result.get('status', 'UNKNOWN')
        symbol = "✅" if status == 'OK' else ("⚠️" if status == 'WARNING' else "❌")
        logger.info(f"  {symbol} {check}: {status}")
    
    return health_report


if __name__ == '__main__':
    # Exemple d'utilisation
    logger.info("Démonstration du monitoring de drift")
    
    # Créer un moniteur
    monitor = DataDriftMonitor(
        reference_data_path="data/gold/ml_features/features_v3.parquet",
        alert_threshold=0.05
    )
    
    # Simuler une détection
    current_data = pd.read_parquet("data/gold/ml_features/features_v3.parquet").tail(100)
    feature_cols = [c for c in current_data.columns if c.startswith(('home_', 'away_'))][:20]
    
    drift_result = monitor.detect_feature_drift(current_data, feature_cols)
    
    logger.info(f"\nRésultat: {drift_result['n_features_drifted']} features en drift")
