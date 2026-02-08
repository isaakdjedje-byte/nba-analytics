"""
Module monitoring central - NBA Analytics Platform

Centralise les patterns de logging, validation et métriques
du projet pour éviter la duplication de code.

Refactorise les patterns dispersés dans :
- src/ml/pipeline/auto_retrain.py
- src/ml/pipeline/model_versioning.py
- src/ml/pipeline/enhanced_pipeline.py
- src/analytics/progression_detector.py
- src/processing/silver/validators.py
- src/processing/bronze/validate_bronze.py

Usage:
    from src.utils.monitoring import get_logger, DataQualityReporter, PipelineMetrics
    
    # Logging standardisé
    logger = get_logger(__name__)
    logger.info("Pipeline démarré")
    
    # Rapport qualité unifié
    reporter = DataQualityReporter()
    reporter.run_full_check(bronze_data, silver_data, gold_data)
    
    # Métriques pipeline
    metrics = PipelineMetrics()
    metrics.record_timing("feature_engineering", 2.5)
"""

import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


# Configuration par défaut
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Crée un logger standardisé pour le projet.
    
    Centralise la configuration logging qui était dupliquée dans :
    - auto_retrain.py (lignes 9-26)
    - model_versioning.py (lignes 13-21)
    - enhanced_pipeline.py (lignes 19-33)
    - progression_detector.py (lignes 20-26)
    
    Args:
        name: Nom du module (__name__)
        level: Niveau de log (default: INFO)
        
    Returns:
        Logger configuré
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Opération réussie")
    """
    logger = logging.getLogger(name)
    
    # Évite d'ajouter des handlers multiples si déjà configuré
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(level)
        
    return logger


class PipelineMetrics:
    """
    Collecte les métriques d'exécution des pipelines.
    
    Suit les performances temporelles et les volumes de données
    pour analyse et optimisation.
    
    Attributes:
        metrics: Dictionnaire des métriques collectées
        start_time: Timestamp de démarrage
        
    Example:
        >>> metrics = PipelineMetrics()
        >>> metrics.record_timing("feature_engineering", 2.5)
        >>> metrics.record_volume("players", 5103)
        >>> metrics.save_report()
    """
    
    def __init__(self, pipeline_name: str = "unknown"):
        """
        Initialise le collecteur de métriques.
        
        Args:
            pipeline_name: Nom identifiant le pipeline
        """
        self.pipeline_name = pipeline_name
        self.start_time = time.time()
        self.metrics = {
            "pipeline": pipeline_name,
            "start_time": datetime.now().isoformat(),
            "timings": {},
            "volumes": {},
            "errors": [],
            "status": "running"
        }
        self.logger = get_logger(__name__)
        
    def record_timing(self, operation: str, duration: float) -> None:
        """
        Enregistre le temps d'exécution d'une opération.
        
        Args:
            operation: Nom de l'opération (ex: "feature_engineering")
            duration: Durée en secondes
        """
        self.metrics["timings"][operation] = {
            "duration_seconds": round(duration, 3),
            "timestamp": datetime.now().isoformat()
        }
        self.logger.debug(f"Timing {operation}: {duration:.3f}s")
        
    def record_volume(self, table: str, count: int) -> None:
        """
        Enregistre le volume de données traité.
        
        Args:
            table: Nom de la table/dataset
            count: Nombre de records
        """
        self.metrics["volumes"][table] = {
            "record_count": count,
            "timestamp": datetime.now().isoformat()
        }
        self.logger.debug(f"Volume {table}: {count} records")
        
    def record_error(self, error_type: str, message: str) -> None:
        """
        Enregistre une erreur survenue pendant l'exécution.
        
        Args:
            error_type: Type d'erreur (ex: "ValidationError", "APIError")
            message: Description de l'erreur
        """
        error = {
            "type": error_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.metrics["errors"].append(error)
        self.logger.error(f"[{error_type}] {message}")
        
    def finalize(self, status: str = "success") -> Dict[str, Any]:
        """
        Finalise la collecte et retourne le rapport complet.
        
        Args:
            status: Statut final ("success", "failure", "partial")
            
        Returns:
            Dictionnaire complet des métriques
        """
        self.metrics["status"] = status
        self.metrics["end_time"] = datetime.now().isoformat()
        self.metrics["total_duration_seconds"] = round(time.time() - self.start_time, 3)
        
        return self.metrics
        
    def save_report(self, path: Optional[str] = None) -> str:
        """
        Sauvegarde le rapport de métriques au format JSON.
        
        Args:
            path: Chemin du fichier (default: logs/metrics/<pipeline_name>_<timestamp>.json)
            
        Returns:
            Chemin du fichier sauvegardé
        """
        # Crée le répertoire logs s'il n'existe pas
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        metrics_dir = LOGS_DIR / "metrics"
        metrics_dir.mkdir(exist_ok=True)
        
        if path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.pipeline_name}_{timestamp}.json"
            path = metrics_dir / filename
        else:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
        # Finalise et sauvegarde
        report = self.finalize()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"Rapport de métriques sauvegardé: {path}")
        return str(path)


class DataQualityReporter:
    """
    Génère des rapports de qualité de données unifiés.
    
    Agrège les validateurs existants (SilverValidator, BronzeValidator, etc.)
    pour fournir une vue d'ensemble de la qualité des données à travers
    les couches Bronze → Silver → Gold.
    
    Attributes:
        checks: Liste des vérifications effectuées
        results: Résultats par couche de données
        
    Example:
        >>> reporter = DataQualityReporter()
        >>> reporter.run_full_check(bronze_data, silver_data, gold_data)
        >>> reporter.save_report("logs/quality_report.json")
    """
    
    def __init__(self):
        """Initialise le rapporteur de qualité."""
        self.checks = []
        self.results = {
            "bronze": {},
            "silver": {},
            "gold": {},
            "summary": {}
        }
        self.logger = get_logger(__name__)
        self.timestamp = datetime.now().isoformat()
        
    def check_bronze(self, data: List[Dict], required_fields: List[str] = None) -> bool:
        """
        Vérifie la qualité des données Bronze.
        
        Args:
            data: Données brutes
            required_fields: Champs requis (default: ["id", "full_name"])
            
        Returns:
            True si qualité acceptable
        """
        if required_fields is None:
            required_fields = ["id", "full_name"]
            
        self.logger.info(f"Vérification qualité Bronze: {len(data)} records")
        
        # Check IDs uniques
        ids = [d.get("id") for d in data if d.get("id")]
        unique_ids = len(set(ids))
        duplicates = len(ids) - unique_ids
        
        # Check champs requis
        missing_fields = 0
        for record in data[:100]:  # Échantillon pour performance
            for field in required_fields:
                if not record.get(field):
                    missing_fields += 1
                    
        # Check complétion
        if len(data) > 0:
            sample = data[0]
            filled_fields = sum(1 for v in sample.values() if v is not None)
            completion_rate = filled_fields / len(sample)
        else:
            completion_rate = 0.0
            
        self.results["bronze"] = {
            "record_count": len(data),
            "unique_ids": unique_ids,
            "duplicates": duplicates,
            "missing_required": missing_fields,
            "completion_rate": round(completion_rate, 3),
            "status": "pass" if duplicates == 0 and completion_rate > 0.3 else "fail"
        }
        
        passed = self.results["bronze"]["status"] == "pass"
        self.logger.info(f"Bronze: {'✓' if passed else '✗'} "
                        f"({len(data)} records, {duplicates} doublons)")
        return passed
        
    def check_silver(self, data: List[Dict], level: str = "contemporary") -> bool:
        """
        Vérifie la qualité des données Silver.
        
        Réutilise SilverValidator si disponible, sinon fait une validation basique.
        
        Args:
            data: Données nettoyées
            level: Niveau de validation ("all", "intermediate", "contemporary")
            
        Returns:
            True si qualité acceptable
        """
        self.logger.info(f"Vérification qualité Silver [{level}]: {len(data)} records")
        
        try:
            # Essaye d'utiliser le validateur existant
            from ..processing.silver.validators import SilverValidator
            validator = SilverValidator(level=level)
            passed = validator.validate(data)
            stats = validator.get_stats()
            
            self.results["silver"] = {
                "record_count": len(data),
                "validation_level": level,
                "null_rate": round(stats.get("null_rate", 0), 3),
                "duplicates": stats.get("duplicates", 0),
                "error_count": stats.get("error_count", 0),
                "status": "pass" if passed else "fail"
            }
        except ImportError:
            # Fallback: validation basique
            self.logger.warning("SilverValidator non disponible, validation basique")
            null_count = sum(1 for d in data for v in d.values() if v is None)
            total_cells = len(data) * len(data[0]) if data else 0
            null_rate = null_count / total_cells if total_cells > 0 else 0
            
            passed = null_rate < 0.05  # Seuil 5%
            self.results["silver"] = {
                "record_count": len(data),
                "validation_level": level,
                "null_rate": round(null_rate, 3),
                "status": "pass" if passed else "fail"
            }
            
        self.logger.info(f"Silver: {'✓' if passed else '✗'} "
                        f"(null_rate: {self.results['silver']['null_rate']:.1%})")
        return passed
        
    def check_gold(self, data: List[Dict], ml_ready: bool = True) -> bool:
        """
        Vérifie la qualité des données Gold (features ML).
        
        Args:
            data: Features ML
            ml_ready: Si True, applique des checks plus stricts
            
        Returns:
            True si qualité acceptable
        """
        self.logger.info(f"Vérification qualité Gold: {len(data)} records")
        
        if not data:
            self.results["gold"] = {"status": "fail", "error": "Aucune donnée"}
            return False
            
        # Check features numériques
        sample = data[0]
        numeric_fields = [k for k, v in sample.items() 
                         if isinstance(v, (int, float)) and k not in ["id", "team_id"]]
        
        # Check NaN/Inf
        nan_count = 0
        inf_count = 0
        for record in data:
            for field in numeric_fields:
                val = record.get(field)
                if val != val:  # NaN check
                    nan_count += 1
                elif isinstance(val, float) and abs(val) == float('inf'):
                    inf_count += 1
                    
        total_values = len(data) * len(numeric_fields)
        nan_rate = nan_count / total_values if total_values > 0 else 0
        
        # Check distributions (outliers simples)
        outlier_count = 0
        for field in numeric_fields[:5]:  # Échantillon
            values = [d.get(field) for d in data if d.get(field) is not None]
            if values:
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                std = variance ** 0.5
                outliers = sum(1 for x in values if abs(x - mean) > 3 * std)
                outlier_count += outliers
                
        passed = nan_rate < 0.01 and inf_count == 0  # Très strict pour ML
        
        self.results["gold"] = {
            "record_count": len(data),
            "feature_count": len(sample),
            "numeric_features": len(numeric_fields),
            "nan_rate": round(nan_rate, 4),
            "inf_count": inf_count,
            "outliers_detected": outlier_count,
            "ml_ready": ml_ready and passed,
            "status": "pass" if passed else "fail"
        }
        
        self.logger.info(f"Gold: {'✓' if passed else '✗'} "
                        f"({len(numeric_fields)} features, nan_rate: {nan_rate:.2%})")
        return passed
        
    def run_full_check(self, bronze_data: List[Dict], 
                      silver_data: List[Dict], 
                      gold_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Exécute une vérification complète de toutes les couches.
        
        Args:
            bronze_data: Données brutes
            silver_data: Données nettoyées
            gold_data: Features ML (optionnel)
            
        Returns:
            Rapport complet de qualité
        """
        self.logger.info("=" * 70)
        self.logger.info("RAPPORT QUALITÉ DONNÉES - VÉRIFICATION COMPLÈTE")
        self.logger.info("=" * 70)
        
        bronze_ok = self.check_bronze(bronze_data)
        silver_ok = self.check_silver(silver_data)
        gold_ok = self.check_gold(gold_data) if gold_data else None
        
        # Résumé global
        overall_status = "pass" if (bronze_ok and silver_ok and (gold_ok is None or gold_ok)) else "fail"
        
        self.results["summary"] = {
            "timestamp": self.timestamp,
            "overall_status": overall_status,
            "bronze_pass": bronze_ok,
            "silver_pass": silver_ok,
            "gold_pass": gold_ok,
            "total_records": {
                "bronze": len(bronze_data),
                "silver": len(silver_data),
                "gold": len(gold_data) if gold_data else 0
            }
        }
        
        self.logger.info("=" * 70)
        self.logger.info(f"RÉSULTAT GLOBAL: {'✓ PASS' if overall_status == 'pass' else '✗ FAIL'}")
        self.logger.info("=" * 70)
        
        return self.results
        
    def save_report(self, path: Optional[str] = None) -> str:
        """
        Sauvegarde le rapport de qualité.
        
        Args:
            path: Chemin du fichier (default: logs/quality/quality_report_<timestamp>.json)
            
        Returns:
            Chemin du fichier sauvegardé
        """
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        quality_dir = LOGS_DIR / "quality"
        quality_dir.mkdir(exist_ok=True)
        
        if path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"quality_report_{timestamp}.json"
            path = quality_dir / filename
        else:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"Rapport qualité sauvegardé: {path}")
        return str(path)


# Fonctions utilitaires pour compatibilité ascendante
def log_pipeline_start(pipeline_name: str) -> None:
    """Log le démarrage d'un pipeline (helper)."""
    logger = get_logger(__name__)
    logger.info(f"\n{'='*70}")
    logger.info(f"{pipeline_name}")
    logger.info(f"{'='*70}\n")
    

def log_pipeline_end(pipeline_name: str, status: str = "success") -> None:
    """Log la fin d'un pipeline (helper)."""
    logger = get_logger(__name__)
    icon = "✅" if status == "success" else "❌"
    logger.info(f"\n{'='*70}")
    logger.info(f"{icon} {pipeline_name} - {status.upper()}")
    logger.info(f"{'='*70}\n")


if __name__ == "__main__":
    # Test du module
    print("Test monitoring.py")
    print("=" * 70)
    
    # Test logger
    logger = get_logger("test")
    logger.info("Test logging OK")
    
    # Test metrics
    metrics = PipelineMetrics("test_pipeline")
    metrics.record_timing("test_op", 1.5)
    metrics.record_volume("test_table", 1000)
    report = metrics.finalize("success")
    print(f"\nMétriques: {json.dumps(report, indent=2)}")
    
    # Test quality reporter
    test_bronze = [{"id": 1, "full_name": "Test", "height_cm": 200}]
    test_silver = [{"id": 1, "full_name": "Test", "height_cm": 200, "weight_kg": 100}]
    
    reporter = DataQualityReporter()
    results = reporter.run_full_check(test_bronze, test_silver)
    print(f"\nQualité: {json.dumps(results['summary'], indent=2)}")
    
    print("\n✓ Tous les tests passent")
