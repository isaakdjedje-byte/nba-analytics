#!/usr/bin/env python3
"""
NBA-25: Réentraînement automatique

Déclenche le réentraînement si les performances baissent
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Import différé pour éviter dépendances circulaires
try:
    from .model_versioning import ModelVersionManager
except ImportError:
    from model_versioning import ModelVersionManager

# Configuration logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class AutoRetrainer:
    """
    Gestionnaire de réentraînement automatique.
    
    Usage:
        retrainer = AutoRetrainer(threshold=0.58)
        if retrainer.should_retrain():
            retrainer.trigger_retrain()
    """
    
    def __init__(self, 
                 threshold: float = 0.58,
                 models_dir: str = "models",
                 features_path: str = "data/gold/ml_features/features_v3.parquet"):
        """
        Initialise le réentraîneur.
        
        Args:
            threshold: Seuil de performance minimum (déclenche réentraînement si en dessous)
            models_dir: Dossier des modèles
            features_path: Chemin vers les features
        """
        self.threshold = threshold
        self.models_dir = Path(models_dir)
        self.features_path = Path(features_path)
        self.version_manager = ModelVersionManager(models_dir)
        
    def check_model_performance(self) -> Optional[float]:
        """
        Vérifie la performance du modèle courant.
        
        Returns:
            Accuracy actuelle ou None si erreur
        """
        try:
            # Charger métriques du modèle courant
            current_version = self.version_manager.get_current_version()
            model_info = self.version_manager.get_model_info(current_version)
            
            if model_info and 'metrics' in model_info:
                accuracy = model_info['metrics'].get('accuracy', 0)
                logger.info(f"Performance modèle {current_version}: {accuracy:.3f}")
                return accuracy
            else:
                # Essayer de charger depuis training_summary.json
                summary_path = self.models_dir / "unified" / "training_summary.json"
                if summary_path.exists():
                    with open(summary_path, 'r') as f:
                        summary = json.load(f)
                        accuracy = summary.get('best_accuracy', 0)
                        logger.info(f"Performance (depuis summary): {accuracy:.3f}")
                        return accuracy
                        
        except Exception as e:
            logger.error(f"Erreur vérification performance: {e}")
        
        return None
    
    def should_retrain(self) -> bool:
        """
        Détermine si un réentraînement est nécessaire.
        
        Returns:
            True si réentraînement nécessaire
        """
        logger.info(f"\nVérification nécessité réentraînement (seuil: {self.threshold:.3f})")
        
        current_accuracy = self.check_model_performance()
        
        if current_accuracy is None:
            logger.warning("Impossible de vérifier performance - réentraînement recommandé")
            return True
        
        if current_accuracy < self.threshold:
            logger.warning(f"⚠️  Performance dégradée: {current_accuracy:.3f} < {self.threshold:.3f}")
            return True
        else:
            logger.info(f"✅ Performance OK: {current_accuracy:.3f} >= {self.threshold:.3f}")
            return False
    
    def trigger_retrain(self, auto_increment: bool = True) -> Optional[str]:
        """
        Déclenche le réentraînement.
        
        Args:
            auto_increment: Incrémenter automatiquement la version
            
        Returns:
            Nouvelle version ou None si échec
        """
        logger.info("\n" + "="*70)
        logger.info("DÉCLENCHEMENT RÉENTRAÎNEMENT")
        logger.info("="*70)
        
        try:
            # Import dynamique pour éviter dépendances circulaires
            from .train_unified import UnifiedTrainer
            
            # Créer trainer
            trainer = UnifiedTrainer(
                hist_path=str(self.features_path),
                output_dir=str(self.models_dir / "unified")
            )
            
            # Lancer entraînement
            logger.info("Lancement entraînement optimisé...")
            result = trainer.run_full_pipeline()
            
            if result and 'metrics' in result:
                new_accuracy = result['metrics'].get('test_accuracy', 0)
                logger.info(f"Nouveau modèle entraîné: accuracy={new_accuracy:.3f}")
                
                # Incrémenter version
                if auto_increment:
                    new_version = self.version_manager.increment_version('minor')
                    self.version_manager.register_model(
                        new_version, 
                        result['metrics'],
                        model_path=str(self.models_dir / "unified" / "model_xgb_unified.joblib")
                    )
                    logger.info(f"Nouvelle version enregistrée: {new_version}")
                    return new_version
                
                return self.version_manager.get_current_version()
            else:
                logger.error("Échec entraînement - pas de métriques retournées")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors du réentraînement: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def auto_retrain_pipeline(self) -> Dict:
        """
        Pipeline complet: vérifie et réentraîne si nécessaire.
        
        Returns:
            Dict avec résultat de l'opération
        """
        logger.info(f"\n{'='*70}")
        logger.info("NBA-25: PIPELINE RÉENTRAÎNEMENT AUTO")
        logger.info(f"{'='*70}\n")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'threshold': self.threshold,
            'retrain_needed': False,
            'retrain_triggered': False,
            'new_version': None,
            'error': None
        }
        
        # Vérifier si réentraînement nécessaire
        if self.should_retrain():
            result['retrain_needed'] = True
            
            # Déclencher réentraînement
            new_version = self.trigger_retrain()
            
            if new_version:
                result['retrain_triggered'] = True
                result['new_version'] = new_version
                logger.info(f"\n✅ Réentraînement réussi: version {new_version}")
            else:
                result['error'] = "Échec réentraînement"
                logger.error("\n❌ Échec réentraînement")
        else:
            logger.info("\n✅ Pas de réentraînement nécessaire")
        
        return result
    
    def log_retrain_event(self, event_type: str, details: Dict):
        """
        Log un événement de réentraînement.
        
        Args:
            event_type: Type d'événement
            details: Détails de l'événement
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details
        }
        
        # Sauvegarder dans fichier de log
        log_file = self.models_dir / "retrain_history.json"
        
        history = []
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    history = json.load(f)
            except:
                pass
        
        history.append(log_entry)
        
        with open(log_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        logger.info(f"Événement loggé: {event_type}")


def main():
    """Point d'entrée pour réentraînement auto."""
    import argparse
    
    parser = argparse.ArgumentParser(description='NBA-25: Réentraînement automatique')
    parser.add_argument('--threshold', type=float, default=0.58,
                       help='Seuil de performance (défaut: 0.58)')
    parser.add_argument('--force', action='store_true',
                       help='Forcer réentraînement même si pas nécessaire')
    
    args = parser.parse_args()
    
    retrainer = AutoRetrainer(threshold=args.threshold)
    
    if args.force:
        logger.info("Mode FORCE - réentraînement demandé manuellement")
        new_version = retrainer.trigger_retrain()
        if new_version:
            print(f"\n✅ Réentraînement forcé terminé: version {new_version}")
        else:
            print("\n❌ Échec réentraînement forcé")
    else:
        result = retrainer.auto_retrain_pipeline()
        
        if result['retrain_triggered']:
            print(f"\n✅ Nouveau modèle créé: {result['new_version']}")
        elif result['retrain_needed'] and result['error']:
            print(f"\n❌ Erreur: {result['error']}")
        else:
            print("\n✅ Aucun réentraînement nécessaire")


if __name__ == "__main__":
    main()
