"""
Gestionnaire de checkpoints pour NBA-19
Permet de reprendre le fetching en cas d'interruption
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class CheckpointManager:
    """Gère les checkpoints pour le fetching des rosters"""
    
    def __init__(self, checkpoint_file: str):
        self.checkpoint_file = checkpoint_file
        self.checkpoint_dir = os.path.dirname(checkpoint_file)
        
        # Créer le répertoire si nécessaire
        if self.checkpoint_dir:
            os.makedirs(self.checkpoint_dir, exist_ok=True)
    
    def save_checkpoint(
        self, 
        season: str, 
        team_index: int, 
        completed_teams: List[int],
        stats: Dict
    ):
        """Sauvegarder l'état actuel"""
        checkpoint = {
            "last_updated": datetime.now().isoformat(),
            "current_season": season,
            "current_team_index": team_index,
            "completed_teams": completed_teams,
            "stats": stats
        }
        
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2)
        
        print(f"💾 Checkpoint sauvegardé: Saison {season}, Équipe {team_index + 1}")
    
    def load_checkpoint(self) -> Optional[Dict]:
        """Charger le dernier checkpoint"""
        if not os.path.exists(self.checkpoint_file):
            return None
        
        try:
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            
            print(f"📂 Checkpoint chargé: Saison {checkpoint.get('current_season')}, "
                  f"Équipe {checkpoint.get('current_team_index', 0) + 1}")
            return checkpoint
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Erreur chargement checkpoint: {e}")
            return None
    
    def clear_checkpoint(self):
        """Effacer le checkpoint (quand tout est terminé)"""
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
            print("🗑️ Checkpoint effacé")
    
    def get_resume_position(self, seasons: List[str]) -> tuple:
        """
        Déterminer où reprendre le fetching
        
        Returns:
            tuple: (season_index, team_index, completed_teams)
        """
        checkpoint = self.load_checkpoint()
        
        if checkpoint is None:
            return 0, 0, []
        
        current_season = checkpoint.get('current_season')
        current_team_index = checkpoint.get('current_team_index', 0)
        completed_teams = checkpoint.get('completed_teams', [])
        
        # Trouver l'index de la saison
        try:
            season_index = seasons.index(current_season)
        except ValueError:
            # Saison non trouvée, recommencer
            return 0, 0, []
        
        return season_index, current_team_index, completed_teams


class FetchingStats:
    """Statistiques de fetching"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.total_teams = 0
        self.completed_teams = 0
        self.failed_teams = 0
        self.total_players = 0
        self.errors = []
    
    def to_dict(self) -> Dict:
        """Convertir en dictionnaire"""
        elapsed = datetime.now() - self.start_time
        
        return {
            "start_time": self.start_time.isoformat(),
            "elapsed_seconds": elapsed.total_seconds(),
            "total_teams": self.total_teams,
            "completed_teams": self.completed_teams,
            "failed_teams": self.failed_teams,
            "total_players": self.total_players,
            "success_rate": self._calculate_success_rate(),
            "errors": self.errors[-10:]  # Garder les 10 dernières erreurs
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculer le taux de succès"""
        if self.total_teams == 0:
            return 0.0
        return (self.completed_teams / self.total_teams) * 100
    
    def add_error(self, season: str, team_id: int, error: str):
        """Ajouter une erreur"""
        self.errors.append({
            "timestamp": datetime.now().isoformat(),
            "season": season,
            "team_id": team_id,
            "error": error
        })
    
    def print_summary(self):
        """Afficher le résumé"""
        elapsed = datetime.now() - self.start_time
        
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DU FETCHING")
        print("=" * 60)
        print(f"⏱️  Durée: {elapsed}")
        print(f"🏀 Équipes: {self.completed_teams}/{self.total_teams} "
              f"({self._calculate_success_rate():.1f}%)")
        print(f"👥 Joueurs récupérés: {self.total_players}")
        print(f"❌ Échecs: {self.failed_teams}")
        
        if self.errors:
            print(f"⚠️  Erreurs: {len(self.errors)}")
        
        print("=" * 60)
