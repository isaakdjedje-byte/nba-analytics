#!/usr/bin/env python3
"""
NBA-25: Système de versioning des modèles

Gestion automatique des versions de modèles ML
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import logging

# Configuration logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class ModelVersionManager:
    """
    Gestionnaire de versions de modèles ML.
    
    Usage:
        manager = ModelVersionManager()
        current = manager.get_current_version()
        new_version = manager.increment_version()
        manager.register_model(new_version, metrics)
    """
    
    def __init__(self, models_dir: str = "models", version_file: str = "version_manifest.json"):
        """
        Initialise le gestionnaire de versions.
        
        Args:
            models_dir: Dossier racine des modèles
            version_file: Nom du fichier de manifest
        """
        self.models_dir = Path(models_dir)
        self.version_file = self.models_dir / version_file
        self.manifest = self._load_manifest()
        
    def _load_manifest(self) -> Dict:
        """Charge le manifest des versions."""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erreur chargement manifest: {e}")
        
        # Manifest par défaut
        return {
            'current_version': 'v1.0.0',
            'versions': {},
            'last_updated': datetime.now().isoformat()
        }
    
    def _save_manifest(self):
        """Sauvegarde le manifest."""
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.manifest['last_updated'] = datetime.now().isoformat()
        
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2)
    
    def get_current_version(self) -> str:
        """Retourne la version courante."""
        return self.manifest.get('current_version', 'v1.0.0')
    
    def parse_version(self, version: str) -> tuple:
        """
        Parse une version string en tuple (major, minor, patch).
        
        Args:
            version: Version au format vX.Y.Z
            
        Returns:
            Tuple (major, minor, patch)
        """
        match = re.match(r'v(\d+)\.(\d+)\.(\d+)', version)
        if match:
            return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        return (1, 0, 0)
    
    def increment_version(self, bump: str = 'minor') -> str:
        """
        Incrémente la version.
        
        Args:
            bump: Type d'incrémentation ('major', 'minor', 'patch')
            
        Returns:
            Nouvelle version
        """
        current = self.get_current_version()
        major, minor, patch = self.parse_version(current)
        
        if bump == 'major':
            major += 1
            minor = 0
            patch = 0
        elif bump == 'minor':
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        new_version = f"v{major}.{minor}.{patch}"
        self.manifest['current_version'] = new_version
        self._save_manifest()
        
        logger.info(f"Version incrémentée: {current} -> {new_version}")
        return new_version
    
    def register_model(self, version: str, metrics: Dict, model_path: Optional[str] = None):
        """
        Enregistre un nouveau modèle dans le manifest.
        
        Args:
            version: Version du modèle
            metrics: Métriques du modèle
            model_path: Chemin vers le fichier modèle
        """
        if 'versions' not in self.manifest:
            self.manifest['versions'] = {}
        
        self.manifest['versions'][version] = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'model_path': model_path,
            'status': 'active'
        }
        
        self._save_manifest()
        logger.info(f"Modèle {version} enregistré")
    
    def get_model_info(self, version: Optional[str] = None) -> Optional[Dict]:
        """
        Retourne les informations d'un modèle.
        
        Args:
            version: Version du modèle (None = version courante)
            
        Returns:
            Dict avec les infos ou None
        """
        if version is None:
            version = self.get_current_version()
        
        return self.manifest.get('versions', {}).get(version)
    
    def list_versions(self) -> List[str]:
        """Liste toutes les versions."""
        return list(self.manifest.get('versions', {}).keys())
    
    def compare_versions(self, version1: str, version2: str) -> Dict:
        """
        Compare deux versions de modèles.
        
        Args:
            version1: Première version
            version2: Deuxième version
            
        Returns:
            Dict avec la comparaison
        """
        info1 = self.get_model_info(version1)
        info2 = self.get_model_info(version2)
        
        if not info1 or not info2:
            return {'error': 'Version non trouvée'}
        
        metrics1 = info1.get('metrics', {})
        metrics2 = info2.get('metrics', {})
        
        comparison = {
            'version1': version1,
            'version2': version2,
            'timestamp1': info1.get('timestamp'),
            'timestamp2': info2.get('timestamp'),
            'metrics_diff': {}
        }
        
        # Comparer métriques communes
        all_metrics = set(metrics1.keys()) | set(metrics2.keys())
        for metric in all_metrics:
            val1 = metrics1.get(metric, 0)
            val2 = metrics2.get(metric, 0)
            diff = val2 - val1
            comparison['metrics_diff'][metric] = {
                'v1': val1,
                'v2': val2,
                'diff': diff,
                'improvement': diff > 0
            }
        
        return comparison
    
    def get_best_version(self, metric: str = 'accuracy') -> Optional[str]:
        """
        Retourne la meilleure version selon une métrique.
        
        Args:
            metric: Nom de la métrique à comparer
            
        Returns:
            Version avec meilleure métrique
        """
        versions = self.manifest.get('versions', {})
        if not versions:
            return None
        
        best_version = None
        best_score = -1
        
        for version, info in versions.items():
            score = info.get('metrics', {}).get(metric, 0)
            if score > best_score:
                best_score = score
                best_version = version
        
        return best_version


def main():
    """Test du gestionnaire de versions."""
    manager = ModelVersionManager()
    
    print(f"Version courante: {manager.get_current_version()}")
    print(f"Versions disponibles: {manager.list_versions()}")
    
    # Simuler enregistrement
    new_version = manager.increment_version('minor')
    manager.register_model(new_version, {'accuracy': 0.77, 'f1': 0.76})
    
    print(f"\nNouvelle version: {new_version}")
    print(f"Infos: {manager.get_model_info(new_version)}")


if __name__ == "__main__":
    main()
