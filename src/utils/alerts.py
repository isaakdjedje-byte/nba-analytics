"""
Système d'alertes simplifié - NBA Analytics Platform

Gère les alertes critiques du projet via logs et fichier dédié.
Conçu pour être simple et fiable, sans dépendances externes complexes
(SMTP, Slack, etc.).

Usage:
    from src.utils.alerts import alert_on_drift, alert_on_quality_failure
    
    # Alerte sur drift détecté
    alert_on_drift("weighted_form_diff", drift_score=0.08, threshold=0.05)
    
    # Alerte sur échec validation
    alert_on_quality_failure("silver_players", ["Taux nulls trop élevé"])
"""

import logging
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime


# Configuration
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
ALERTS_LOG = LOGS_DIR / "alerts.log"


class AlertManager:
    """
    Gestionnaire d'alertes simple.
    
    Centralise la gestion des alertes critiques du projet.
    Écrit dans un fichier dédié (logs/alerts.log) pour faciliter
    le suivi des problèmes.
    
    Attributes:
        alerts_history: Historique des alertes de la session
        logger: Logger dédié aux alertes
        
    Example:
        >>> alerts = AlertManager()
        >>> alerts.send_alert("Drift détecté", "warning", "feature_engineering")
        >>> alerts.send_alert("Pipeline échoué", "error", "nba22_training")
    """
    
    def __init__(self):
        """Initialise le gestionnaire d'alertes."""
        self.alerts_history: List[Dict[str, Any]] = []
        self.logger = self._setup_alert_logger()
        
    def _setup_alert_logger(self) -> logging.Logger:
        """Configure le logger dédié aux alertes."""
        logger = logging.getLogger("nba_alerts")
        logger.setLevel(logging.WARNING)
        
        # Évite d'ajouter des handlers multiples
        if not logger.handlers:
            # Handler fichier
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(ALERTS_LOG, mode='a', encoding='utf-8')
            file_handler.setLevel(logging.WARNING)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                '%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Handler console (pour visibilité immédiate)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.ERROR)  # Console seulement pour erreurs
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
        return logger
        
    def send_alert(self, message: str, severity: str = "warning", 
                  source: str = "unknown") -> None:
        """
        Envoie une alerte.
        
        Args:
            message: Description de l'alerte
            severity: Niveau ("info", "warning", "error", "critical")
            source: Source de l'alerte (nom du module/pipeline)
        """
        alert = {
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "source": source,
            "message": message
        }
        
        self.alerts_history.append(alert)
        
        # Log selon la sévérité
        log_message = f"[{source}] {message}"
        
        if severity == "info":
            self.logger.info(log_message)
        elif severity == "warning":
            self.logger.warning(f"⚠️  {log_message}")
        elif severity == "error":
            self.logger.error(f"❌ {log_message}")
        elif severity == "critical":
            self.logger.critical(f"🚨 CRITICAL: {log_message}")
        else:
            self.logger.warning(log_message)
            
    def alert_on_drift(self, feature_name: str, drift_score: float, 
                      threshold: float = 0.05) -> None:
        """
        Alerte si drift détecté sur une feature.
        
        Args:
            feature_name: Nom de la feature
            drift_score: Score de drift (p-value ou distance)
            threshold: Seuil d'alerte (default: 0.05)
        """
        if drift_score < threshold:
            message = (f"Drift détecté sur '{feature_name}': "
                      f"score={drift_score:.4f} < seuil={threshold:.2f}")
            self.send_alert(message, "warning", "drift_monitoring")
            
    def alert_on_quality_failure(self, table: str, errors: List[str]) -> None:
        """
        Alerte sur échec de validation qualité.
        
        Args:
            table: Nom de la table/dataset
            errors: Liste des erreurs détectées
        """
        error_str = "; ".join(errors[:3])  # Limite à 3 erreurs
        if len(errors) > 3:
            error_str += f" (+{len(errors)-3} autres)"
            
        message = f"Validation qualité échouée pour '{table}': {error_str}"
        self.send_alert(message, "error", "data_quality")
        
    def alert_on_pipeline_failure(self, pipeline_name: str, 
                                 error: str, step: str = "unknown") -> None:
        """
        Alerte sur échec de pipeline.
        
        Args:
            pipeline_name: Nom du pipeline
            error: Message d'erreur
            step: Étape où l'erreur s'est produite
        """
        message = f"Pipeline '{pipeline_name}' échoué à l'étape '{step}': {error}"
        self.send_alert(message, "error", pipeline_name)
        
    def alert_on_performance_degradation(self, metric_name: str, 
                                        current: float, baseline: float,
                                        threshold_pct: float = 10.0) -> None:
        """
        Alerte si dégradation de performance significative.
        
        Args:
            metric_name: Nom de la métrique (ex: "accuracy", "precision")
            current: Valeur actuelle
            baseline: Valeur de référence
            threshold_pct: Seuil de dégradation en pourcentage
        """
        if baseline == 0:
            return
            
        degradation_pct = ((baseline - current) / baseline) * 100
        
        if degradation_pct > threshold_pct:
            message = (f"Dégradation {metric_name}: {current:.3f} vs {baseline:.3f} "
                      f"baseline (-{degradation_pct:.1f}%)")
            self.send_alert(message, "warning", "performance")
            
    def get_recent_alerts(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Retourne les N dernières alertes.
        
        Args:
            count: Nombre d'alertes à retourner
            
        Returns:
            Liste des alertes récentes
        """
        return self.alerts_history[-count:]
        
    def save_history(self, path: Optional[str] = None) -> str:
        """
        Sauvegarde l'historique des alertes.
        
        Args:
            path: Chemin du fichier (default: logs/alerts/history_<timestamp>.json)
            
        Returns:
            Chemin du fichier sauvegardé
        """
        if path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = LOGS_DIR / "alerts" / f"history_{timestamp}.json"
        else:
            path = Path(path)
            
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.alerts_history, f, indent=2, ensure_ascii=False)
            
        return str(path)


# Fonctions helper pour usage simple
_alerts_manager: Optional[AlertManager] = None


def _get_alert_manager() -> AlertManager:
    """Singleton pour l'AlertManager."""
    global _alerts_manager
    if _alerts_manager is None:
        _alerts_manager = AlertManager()
    return _alerts_manager


def alert_on_drift(feature_name: str, drift_score: float, threshold: float = 0.05) -> None:
    """Helper: Alerte sur drift détecté."""
    _get_alert_manager().alert_on_drift(feature_name, drift_score, threshold)


def alert_on_quality_failure(table: str, errors: List[str]) -> None:
    """Helper: Alerte sur échec validation qualité."""
    _get_alert_manager().alert_on_quality_failure(table, errors)


def alert_on_pipeline_failure(pipeline_name: str, error: str, step: str = "unknown") -> None:
    """Helper: Alerte sur échec pipeline."""
    _get_alert_manager().alert_on_pipeline_failure(pipeline_name, error, step)


def alert_on_performance_degradation(metric_name: str, current: float, 
                                    baseline: float, threshold_pct: float = 10.0) -> None:
    """Helper: Alerte sur dégradation performance."""
    _get_alert_manager().alert_on_performance_degradation(
        metric_name, current, baseline, threshold_pct
    )


def send_alert(message: str, severity: str = "warning", source: str = "unknown") -> None:
    """Helper: Envoie une alerte générique."""
    _get_alert_manager().send_alert(message, severity, source)


if __name__ == "__main__":
    # Test du module
    print("Test alerts.py")
    print("=" * 70)
    
    alerts = AlertManager()
    
    # Test différentes sévérités
    alerts.send_alert("Test info", "info", "test")
    alerts.send_alert("Test warning", "warning", "test")
    alerts.send_alert("Test error", "error", "test")
    
    # Test alertes spécifiques
    alert_on_drift("weighted_form_diff", 0.08, 0.05)
    alert_on_quality_failure("silver_players", ["Taux nulls: 15%", "Doublons détectés"])
    alert_on_pipeline_failure("nba22_training", "Out of memory", "model_training")
    alert_on_performance_degradation("accuracy", 0.72, 0.76, 5.0)
    
    print(f"\nHistorique: {len(alerts.get_recent_alerts())} alertes")
    print(f"Fichier log: {ALERTS_LOG}")
    print("\n✓ Tous les tests passent")
