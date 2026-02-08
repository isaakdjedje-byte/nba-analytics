#!/usr/bin/env python3
"""
NBA-25: Pipeline ML Automatisé (Enhanced)

Étend DailyPredictionPipeline avec:
- Réentraînement automatique
- Versioning des modèles
- Détection de nouvelles données
- Logging complet

Usage:
    from enhanced_pipeline import EnhancedPredictionPipeline
    
    pipeline = EnhancedPredictionPipeline()
    pipeline.run_auto_pipeline()  # Vérifie, réentraîne si besoin, prédit
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Import du pipeline existant
from .daily_pipeline import DailyPredictionPipeline
from .model_versioning import ModelVersionManager
from .auto_retrain import AutoRetrainer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedPredictionPipeline(DailyPredictionPipeline):
    """
    Pipeline de prédiction amélioré avec auto-retrain et versioning.
    
    Hérite de DailyPredictionPipeline et ajoute:
    - Vérification automatique des performances
    - Réentraînement si nécessaire (seuil < 58%)
    - Versioning des modèles
    - Détection de nouvelles données
    """
    
    def __init__(self, 
                 auto_retrain_threshold: float = 0.58,
                 models_dir: str = "models",
                 **kwargs):
        """
        Initialise le pipeline amélioré.
        
        Args:
            auto_retrain_threshold: Seuil pour déclencher réentraînement
            models_dir: Dossier des modèles
            **kwargs: Arguments pour DailyPredictionPipeline parent
        """
        super().__init__()
        
        self.auto_retrain_threshold = auto_retrain_threshold
        self.models_dir = Path(models_dir)
        
        # Composants NBA-25
        self.version_manager = ModelVersionManager(models_dir)
        self.retrainer = AutoRetrainer(
            threshold=auto_retrain_threshold,
            models_dir=models_dir
        )
        
        self.pipeline_log = []
        
    def check_system_health(self) -> Dict:
        """
        Vérifie la santé du système ML.
        
        Returns:
            Dict avec statut de toutes les composantes
        """
        logger.info("\nVérification santé système ML...")
        
        health = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'overall_status': 'OK'
        }
        
        # 1. Vérifier modèle existe
        model_path = self.models_dir / "optimized" / "model_xgb.joblib"
        health['checks']['model_exists'] = model_path.exists()
        if not health['checks']['model_exists']:
            health['overall_status'] = 'CRITICAL'
            logger.error(f"❌ Modèle non trouvé: {model_path}")
        else:
            logger.info(f"✅ Modèle trouvé: {model_path}")
        
        # 2. Vérifier features existent
        features_path = Path("data/gold/ml_features/features_v3.parquet")
        health['checks']['features_exist'] = features_path.exists()
        if not health['checks']['features_exist']:
            health['overall_status'] = 'WARNING'
            logger.warning(f"⚠️  Features non trouvées: {features_path}")
        else:
            logger.info(f"✅ Features trouvées: {features_path}")
        
        # 3. Vérifier performance modèle
        current_acc = self.retrainer.check_model_performance()
        health['checks']['current_accuracy'] = current_acc
        
        if current_acc is None:
            health['overall_status'] = 'WARNING'
            logger.warning("⚠️  Impossible de vérifier performance")
        elif current_acc < self.auto_retrain_threshold:
            health['checks']['performance_ok'] = False
            health['overall_status'] = 'DEGRADED'
            logger.warning(f"⚠️  Performance faible: {current_acc:.3f}")
        else:
            health['checks']['performance_ok'] = True
            logger.info(f"✅ Performance OK: {current_acc:.3f}")
        
        # 4. Vérifier version
        current_version = self.version_manager.get_current_version()
        health['checks']['current_version'] = current_version
        logger.info(f"✅ Version courante: {current_version}")
        
        return health
    
    def check_for_new_data(self, reference_date: Optional[str] = None) -> bool:
        """
        Vérifie si de nouvelles données sont disponibles.
        
        Args:
            reference_date: Date de référence (None = dernière prédiction)
            
        Returns:
            True si nouvelles données détectées
        """
        logger.info("\nVérification nouvelles données...")
        
        # Récupérer date dernière prédiction
        predictions_dir = Path("predictions")
        if not predictions_dir.exists():
            logger.info("✅ Pas de prédiction précédente - nouvelles données")
            return True
        
        latest_files = list(predictions_dir.glob("predictions_*.json"))
        if not latest_files:
            logger.info("✅ Pas de fichier prédiction - nouvelles données")
            return True
        
        # Trier par date
        latest_file = max(latest_files, key=lambda p: p.stat().st_mtime)
        last_pred_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
        
        logger.info(f"Dernière prédiction: {last_pred_time}")
        
        # Vérifier si +24h écoulées
        time_diff = datetime.now() - last_pred_time
        has_new_data = time_diff.total_seconds() > 24 * 3600
        
        if has_new_data:
            logger.info(f"✅ Nouvelles données disponibles ({time_diff.days} jours)")
        else:
            logger.info(f"⏳ Pas de nouvelles données ({time_diff.seconds // 3600}h écoulées)")
        
        return has_new_data
    
    def auto_retrain_if_needed(self) -> Optional[str]:
        """
        Réentraîne automatiquement si nécessaire.
        
        Returns:
            Nouvelle version si réentraînement, None sinon
        """
        logger.info(f"\n{'='*70}")
        logger.info("NBA-25: AUTO-RETRAIN CHECK")
        logger.info(f"{'='*70}")
        
        if self.retrainer.should_retrain():
            new_version = self.retrainer.trigger_retrain()
            
            if new_version:
                logger.info(f"✅ Réentraînement terminé: {new_version}")
                self._log_event('auto_retrain', {'new_version': new_version})
                return new_version
            else:
                logger.error("❌ Échec réentraînement")
                return None
        else:
            logger.info("✅ Pas de réentraînement nécessaire")
            return None
    
    def run_auto_pipeline(self, 
                         force_retrain: bool = False,
                         skip_if_no_new_data: bool = True) -> Dict:
        """
        Pipeline complet: vérifie, réentraîne si besoin, prédit.
        
        Args:
            force_retrain: Forcer réentraînement
            skip_if_no_new_data: Sauter si pas de nouvelles données
            
        Returns:
            Dict avec résultats complets
        """
        logger.info(f"\n{'='*70}")
        logger.info("NBA-25: PIPELINE ML AUTOMATISÉ")
        logger.info(f"{'='*70}\n")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'version': self.version_manager.get_current_version(),
            'health_check': None,
            'new_data_detected': True,
            'retrain_triggered': False,
            'new_version': None,
            'predictions': None,
            'status': 'SUCCESS'
        }
        
        try:
            # 1. Vérifier santé système
            logger.info("\n📊 PHASE 1: Vérification santé système")
            health = self.check_system_health()
            results['health_check'] = health
            
            if health['overall_status'] == 'CRITICAL':
                logger.error("❌ Système en état critique - arrêt")
                results['status'] = 'CRITICAL_ERROR'
                return results
            
            # 2. Vérifier nouvelles données
            logger.info("\n📊 PHASE 2: Détection nouvelles données")
            has_new_data = self.check_for_new_data()
            results['new_data_detected'] = has_new_data
            
            if skip_if_no_new_data and not has_new_data and not force_retrain:
                logger.info("\n⏳ Pas de nouvelles données - pipeline terminé")
                results['status'] = 'NO_NEW_DATA'
                return results
            
            # 3. Réentraînement si nécessaire
            logger.info("\n📊 PHASE 3: Vérification réentraînement")
            if force_retrain:
                logger.info("Mode FORCE - réentraînement demandé")
                new_version = self.retrainer.trigger_retrain()
            else:
                new_version = self.auto_retrain_if_needed()
            
            if new_version:
                results['retrain_triggered'] = True
                results['new_version'] = new_version
                results['version'] = new_version
            
            # 4. Prédictions
            logger.info("\n📊 PHASE 4: Prédictions")
            predictions = self.run_daily_predictions()
            results['predictions'] = {
                'count': len(predictions),
                'successful': len([p for p in predictions if 'error' not in p])
            }
            
            # 5. Sauvegarder rapport
            self._save_pipeline_report(results)
            
            logger.info(f"\n{'='*70}")
            logger.info("✅ PIPELINE TERMINÉ AVEC SUCCÈS")
            logger.info(f"{'='*70}\n")
            
        except Exception as e:
            logger.error(f"\n❌ Erreur pipeline: {e}")
            import traceback
            logger.error(traceback.format_exc())
            results['status'] = 'ERROR'
            results['error'] = str(e)
        
        return results
    
    def _log_event(self, event_type: str, details: Dict):
        """Log un événement du pipeline."""
        self.pipeline_log.append({
            'timestamp': datetime.now().isoformat(),
            'event': event_type,
            'details': details
        })
    
    def _save_pipeline_report(self, results: Dict):
        """Sauvegarde le rapport du pipeline."""
        reports_dir = Path("reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = reports_dir / f"ml_pipeline_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"📄 Rapport sauvegardé: {report_file}")


def main():
    """Point d'entrée pour pipeline NBA-25."""
    import argparse
    
    parser = argparse.ArgumentParser(description='NBA-25: Pipeline ML Automatisé')
    parser.add_argument('--threshold', type=float, default=0.58,
                       help='Seuil réentraînement (défaut: 0.58)')
    parser.add_argument('--force-retrain', action='store_true',
                       help='Forcer réentraînement')
    parser.add_argument('--skip-if-no-data', action='store_true', default=True,
                       help="Sauter si pas de nouvelles données")
    parser.add_argument('--predict-only', action='store_true',
                       help="Uniquement prédictions (pas de réentraînement)")
    
    args = parser.parse_args()
    
    pipeline = EnhancedPredictionPipeline(
        auto_retrain_threshold=args.threshold
    )
    
    if args.predict_only:
        # Mode prédiction uniquement
        logger.info("Mode PREDICT ONLY")
        predictions = pipeline.run_daily_predictions()
        print(f"\n✅ {len(predictions)} prédictions générées")
    else:
        # Mode pipeline complet
        results = pipeline.run_auto_pipeline(
            force_retrain=args.force_retrain,
            skip_if_no_new_data=args.skip_if_no_data
        )
        
        # Résumé
        print(f"\n{'='*70}")
        print("RÉSULTATS")
        print(f"{'='*70}")
        print(f"Status: {results['status']}")
        print(f"Version: {results['version']}")
        print(f"Nouvelles données: {results['new_data_detected']}")
        print(f"Réentraînement: {results['retrain_triggered']}")
        if results['new_version']:
            print(f"Nouvelle version: {results['new_version']}")
        if results['predictions']:
            print(f"Prédictions: {results['predictions']['count']}")
        print(f"{'='*70}")


if __name__ == "__main__":
    main()
