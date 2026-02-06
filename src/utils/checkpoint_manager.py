#!/usr/bin/env python3
"""
Gestionnaire de checkpoints pour NBA-15
Permet de reprendre l'exécution en cas d'interruption
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


class CheckpointManager:
    """Gère les checkpoints pour reprise d'exécution"""
    
    def __init__(self, checkpoint_dir: str = "data/checkpoints/nba15"):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_file = os.path.join(checkpoint_dir, "progress.json")
        self._ensure_dir()
        self.data = self._load()
    
    def _ensure_dir(self):
        """Crée le répertoire de checkpoints s'il n'existe pas"""
        if not os.path.exists(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir)
    
    def _load(self) -> Dict[str, Any]:
        """Charge le checkpoint existant ou crée un nouveau"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {
            "ticket": "NBA-15",
            "status": "not_started",
            "completed_steps": [],
            "current_step": None,
            "data": {},
            "start_time": None,
            "last_update": None
        }
    
    def save(self):
        """Sauvegarde le checkpoint"""
        self.data["last_update"] = datetime.now().isoformat()
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def start_step(self, step_name: str, step_data: Optional[Dict] = None):
        """Marque le début d'une étape"""
        if self.data["start_time"] is None:
            self.data["start_time"] = datetime.now().isoformat()
        
        self.data["current_step"] = step_name
        self.data["status"] = "in_progress"
        
        if step_data:
            self.data["data"][step_name] = step_data
        
        self.save()
    
    def complete_step(self, step_name: str, result_data: Optional[Dict] = None):
        """Marque une étape comme terminée"""
        if step_name not in self.data["completed_steps"]:
            self.data["completed_steps"].append(step_name)
        
        self.data["current_step"] = None
        
        if result_data:
            self.data["data"][step_name] = result_data
        
        self.save()
    
    def is_step_completed(self, step_name: str) -> bool:
        """Vérifie si une étape est déjà terminée"""
        return step_name in self.data["completed_steps"]
    
    def get_step_data(self, step_name: str) -> Optional[Dict]:
        """Récupère les données d'une étape"""
        return self.data["data"].get(step_name)
    
    def reset(self):
        """Réinitialise le checkpoint (recommencer à zéro)"""
        self.data = {
            "ticket": "NBA-15",
            "status": "not_started",
            "completed_steps": [],
            "current_step": None,
            "data": {},
            "start_time": None,
            "last_update": None
        }
        self.save()
    
    def get_resume_point(self) -> Optional[str]:
        """Retourne le point de reprise si interruption"""
        if self.data["current_step"]:
            return self.data["current_step"]
        
        # Détermine la prochaine étape à faire
        all_steps = ["teams", "rosters", "team_stats", "schedules", "boxscores"]
        for step in all_steps:
            if step not in self.data["completed_steps"]:
                return step
        
        return None
    
    def get_progress_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de progression"""
        all_steps = ["teams", "rosters", "team_stats", "schedules", "boxscores"]
        completed = len(self.data["completed_steps"])
        total = len(all_steps)
        
        return {
            "completed": completed,
            "total": total,
            "percentage": (completed / total * 100) if total > 0 else 0,
            "remaining": total - completed,
            "steps_done": self.data["completed_steps"],
            "current": self.data["current_step"]
        }
