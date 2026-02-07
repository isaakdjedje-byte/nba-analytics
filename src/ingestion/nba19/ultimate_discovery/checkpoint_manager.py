"""
NBA-19 Ultimate Discovery - Checkpoint Manager
Gestion des checkpoints granulaires pour reprise d'exécution
"""
import json
import os
import gzip
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class CheckpointManager:
    """
    Gestionnaire de checkpoints avancé pour le discovery
    
    Features:
    - Sauvegarde compressée (gzip)
    - Rotation automatique des checkpoints
    - Récupération granulaire par segment
    - Validation d'intégrité
    """
    
    def __init__(self, checkpoint_dir: str, max_checkpoints: int = 10):
        self.checkpoint_dir = checkpoint_dir
        self.max_checkpoints = max_checkpoints
        
        # Créer le répertoire
        os.makedirs(checkpoint_dir, exist_ok=True)
    
    def save_checkpoint(
        self,
        phase: str,
        segment: str,
        player_index: int,
        successful_mappings: List[Dict],
        failed_players: List[Dict],
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Sauvegarder un checkpoint
        
        Returns:
            Chemin du fichier checkpoint créé
        """
        checkpoint = {
            "version": "2.0",
            "created_at": datetime.now().isoformat(),
            "phase": phase,
            "segment": segment,
            "player_index": player_index,
            "successful_mappings": successful_mappings,
            "failed_players": failed_players,
            "metadata": metadata or {},
            "stats": {
                "total_success": len(successful_mappings),
                "total_failed": len(failed_players),
                "success_rate": len(successful_mappings) / (len(successful_mappings) + len(failed_players)) 
                               if (len(successful_mappings) + len(failed_players)) > 0 else 0
            }
        }
        
        # Nom de fichier avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"checkpoint_{phase}_{segment}_{timestamp}.json.gz"
        filepath = os.path.join(self.checkpoint_dir, filename)
        
        # Sauvegarde compressée
        with gzip.open(filepath, 'wt', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2)
        
        # Nettoyer les vieux checkpoints
        self._rotate_checkpoints()
        
        print(f"💾 Checkpoint sauvegardé: {filename}")
        print(f"   Phase: {phase}, Segment: {segment}, Index: {player_index}")
        print(f"   Mappings: {len(successful_mappings)}, Failed: {len(failed_players)}")
        
        return filepath
    
    def load_latest_checkpoint(
        self,
        phase: Optional[str] = None,
        segment: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Charger le checkpoint le plus récent
        
        Args:
            phase: Filtrer par phase (optionnel)
            segment: Filtrer par segment (optionnel)
            
        Returns:
            Données du checkpoint ou None
        """
        checkpoints = self._list_checkpoints(phase, segment)
        
        if not checkpoints:
            return None
        
        # Prendre le plus récent
        latest = checkpoints[0]
        
        try:
            with gzip.open(latest, 'rt', encoding='utf-8') as f:
                checkpoint = json.load(f)
            
            print(f"📂 Checkpoint chargé: {os.path.basename(latest)}")
            print(f"   Créé le: {checkpoint.get('created_at')}")
            print(f"   Phase: {checkpoint.get('phase')}, Segment: {checkpoint.get('segment')}")
            print(f"   Index: {checkpoint.get('player_index')}")
            
            return checkpoint
            
        except (json.JSONDecodeError, gzip.BadGzipFile, IOError) as e:
            print(f"⚠️ Erreur chargement checkpoint: {e}")
            return None
    
    def get_resume_position(
        self,
        phase: str,
        segment: str
    ) -> tuple:
        """
        Déterminer la position de reprise pour un segment
        
        Returns:
            tuple: (player_index, successful_mappings, failed_players)
        """
        checkpoint = self.load_latest_checkpoint(phase, segment)
        
        if checkpoint is None:
            return 0, [], []
        
        return (
            checkpoint.get('player_index', 0),
            checkpoint.get('successful_mappings', []),
            checkpoint.get('failed_players', [])
        )
    
    def list_all_checkpoints(self) -> List[Dict]:
        """Lister tous les checkpoints avec métadonnées"""
        checkpoints = self._list_checkpoints()
        result = []
        
        for filepath in checkpoints:
            try:
                with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                
                result.append({
                    "file": os.path.basename(filepath),
                    "phase": data.get('phase'),
                    "segment": data.get('segment'),
                    "created_at": data.get('created_at'),
                    "player_index": data.get('player_index'),
                    "size_mb": os.path.getsize(filepath) / (1024 * 1024)
                })
            except Exception:
                continue
        
        return result
    
    def clear_all_checkpoints(self):
        """Effacer tous les checkpoints"""
        checkpoints = self._list_checkpoints()
        for filepath in checkpoints:
            os.remove(filepath)
        print(f"🗑️ {len(checkpoints)} checkpoints effacés")
    
    def _list_checkpoints(
        self,
        phase: Optional[str] = None,
        segment: Optional[str] = None
    ) -> List[str]:
        """Lister les fichiers checkpoints"""
        if not os.path.exists(self.checkpoint_dir):
            return []
        
        files = []
        for filename in os.listdir(self.checkpoint_dir):
            if filename.startswith('checkpoint_') and filename.endswith('.json.gz'):
                # Filtrer si nécessaire
                if phase and not filename.startswith(f'checkpoint_{phase}_'):
                    continue
                if segment and segment not in filename:
                    continue
                
                filepath = os.path.join(self.checkpoint_dir, filename)
                files.append((filepath, os.path.getmtime(filepath)))
        
        # Trier par date (plus récent en premier)
        files.sort(key=lambda x: x[1], reverse=True)
        return [f[0] for f in files]
    
    def _rotate_checkpoints(self):
        """Supprimer les vieux checkpoints si trop nombreux"""
        checkpoints = self._list_checkpoints()
        
        if len(checkpoints) > self.max_checkpoints:
            to_delete = checkpoints[self.max_checkpoints:]
            for filepath in to_delete:
                os.remove(filepath)
                print(f"🗑️ Vieux checkpoint supprimé: {os.path.basename(filepath)}")


class RecoveryManager:
    """
    Gestionnaire de récupération après interruption
    """
    
    def __init__(self, checkpoint_manager: CheckpointManager):
        self.checkpoint_mgr = checkpoint_manager
    
    def analyze_interruption(self) -> Dict:
        """
        Analyser l'état après interruption
        
        Returns:
            Rapport de récupération
        """
        checkpoints = self.checkpoint_mgr.list_all_checkpoints()
        
        if not checkpoints:
            return {
                "can_resume": False,
                "message": "Aucun checkpoint trouvé - démarrage frais"
            }
        
        # Grouper par phase/segment
        by_segment = {}
        for cp in checkpoints:
            key = f"{cp['phase']}/{cp['segment']}"
            if key not in by_segment:
                by_segment[key] = []
            by_segment[key].append(cp)
        
        # Déterminer où reprendre
        resume_points = []
        for key, cps in by_segment.items():
            latest = cps[0]  # Plus récent
            resume_points.append({
                "phase": latest['phase'],
                "segment": latest['segment'],
                "player_index": latest['player_index'],
                "last_update": latest['created_at']
            })
        
        return {
            "can_resume": True,
            "checkpoints_found": len(checkpoints),
            "segments_in_progress": len(by_segment),
            "resume_points": resume_points,
            "recommendation": "Reprise possible depuis les checkpoints"
        }
    
    def resume_segment(self, phase: str, segment: str) -> tuple:
        """
        Préparer la reprise d'un segment
        
        Returns:
            tuple: (index, mappings, failed, is_resuming)
        """
        checkpoint = self.checkpoint_mgr.load_latest_checkpoint(phase, segment)
        
        if checkpoint is None:
            return 0, [], [], False
        
        print(f"🔄 Reprise du segment {phase}/{segment}")
        print(f"   Index: {checkpoint['player_index']}")
        print(f"   Mappings déjà réussis: {len(checkpoint['successful_mappings'])}")
        print(f"   Failed: {len(checkpoint['failed_players'])}")
        
        return (
            checkpoint['player_index'],
            checkpoint['successful_mappings'],
            checkpoint['failed_players'],
            True
        )
