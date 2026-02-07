"""
Gestion du cache pour les appels API NBA.

Permet de persister les réponses API et de les réutiliser
pour éviter les appels redondants (rate limiting, performances).
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)


class APICacheManager:
    """
    Gestionnaire de cache pour les données API NBA.
    
    Features:
    - Chargement/sauvegarde automatique
    - Sauvegardes incrémentales (checkpointing)
    - Statistiques d'utilisation
    """
    
    def __init__(self, cache_path: str = "data/raw/players_api_cache.json"):
        """
        Initialise le gestionnaire de cache.
        
        Args:
            cache_path: Chemin vers le fichier de cache
        """
        self.cache_path = Path(cache_path)
        self.cache_data: Dict[str, dict] = {}
        self.metadata: Dict = {}
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Charge le cache depuis le disque."""
        if not self.cache_path.exists():
            logger.info(f"Cache non existant: {self.cache_path}")
            return
        
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cache_data = data.get('data', {})
                self.metadata = data.get('metadata', {})
            
            logger.info(f"Cache chargé: {len(self.cache_data)} joueurs")
        except Exception as e:
            logger.warning(f"Erreur chargement cache: {e}")
            self.cache_data = {}
            self.metadata = {}
    
    def save_cache(self, force: bool = False) -> None:
        """
        Sauvegarde le cache sur le disque.
        
        Args:
            force: Si True, sauvegarde même si rien n'a changé
        """
        if not self.cache_data and not force:
            return
        
        # S'assurer que le dossier existe
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        cache_content = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "total_cached": len(self.cache_data),
                "version": "1.0"
            },
            "data": self.cache_data
        }
        
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_content, f, indent=2, default=str)
            logger.info(f"Cache sauvegardé: {len(self.cache_data)} joueurs")
        except Exception as e:
            logger.error(f"Erreur sauvegarde cache: {e}")
    
    def checkpoint(self, iteration: int, checkpoint_every: int = 100) -> None:
        """
        Sauvegarde incrémentale tous les N itérations.
        
        Args:
            iteration: Numéro d'itération actuel
            checkpoint_every: Fréquence de sauvegarde
        """
        if iteration > 0 and iteration % checkpoint_every == 0:
            self.save_cache()
            logger.info(f"Checkpoint {iteration}: {len(self.cache_data)} joueurs en cache")
    
    def get(self, player_id: int) -> Optional[dict]:
        """
        Récupère les données d'un joueur depuis le cache.
        
        Args:
            player_id: ID du joueur
            
        Returns:
            Données du joueur ou None si pas en cache
        """
        return self.cache_data.get(str(player_id))
    
    def set(self, player_id: int, player_data: dict) -> None:
        """
        Stocke les données d'un joueur dans le cache.
        
        Args:
            player_id: ID du joueur
            player_data: Données à stocker
        """
        self.cache_data[str(player_id)] = player_data
    
    def exists(self, player_id: int) -> bool:
        """
        Vérifie si un joueur est dans le cache.
        
        Args:
            player_id: ID du joueur
            
        Returns:
            True si le joueur est en cache
        """
        return str(player_id) in self.cache_data
    
    def filter_missing(self, player_ids: list) -> list:
        """
        Filtre les IDs pour ne garder que ceux qui ne sont pas en cache.
        
        Args:
            player_ids: Liste d'IDs à filtrer
            
        Returns:
            Liste des IDs manquants du cache
        """
        missing = [pid for pid in player_ids if not self.exists(pid)]
        cached_count = len(player_ids) - len(missing)
        
        if cached_count > 0:
            logger.info(f"{cached_count} joueurs déjà en cache (pas d'appel API)")
        
        return missing
    
    def get_cached_ids(self) -> Set[int]:
        """
        Retourne l'ensemble des IDs présents dans le cache.
        
        Returns:
            Set d'IDs (int)
        """
        return {int(pid) for pid in self.cache_data.keys()}
    
    def get_stats(self) -> dict:
        """
        Retourne les statistiques du cache.
        
        Returns:
            Dict avec métriques du cache
        """
        return {
            "total_cached": len(self.cache_data),
            "cache_file": str(self.cache_path),
            "metadata": self.metadata
        }
    
    def clear(self) -> None:
        """Vide le cache (attention: irréversible)."""
        self.cache_data = {}
        self.metadata = {}
        logger.warning("Cache vidé")
    
    def backup(self, backup_path: str) -> None:
        """
        Crée une copie de sauvegarde du cache.
        
        Args:
            backup_path: Chemin pour la sauvegarde
        """
        backup_file = Path(backup_path)
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        
        backup_content = {
            "metadata": {
                **self.metadata,
                "backup_created": datetime.now().isoformat()
            },
            "data": self.cache_data
        }
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_content, f, indent=2, default=str)
        
        logger.info(f"Backup créé: {backup_path} ({len(self.cache_data)} joueurs)")


if __name__ == "__main__":
    # Test rapide
    print("Test APICacheManager:")
    cache = APICacheManager("data/test_cache.json")
    
    # Simuler des données
    cache.set(2544, {"name": "LeBron James", "height": "6-9"})
    cache.set(201939, {"name": "Stephen Curry", "height": "6-2"})
    
    print(f"Stats: {cache.get_stats()}")
    print(f"LeBron en cache: {cache.exists(2544)}")
    print(f"ID manquants: {cache.filter_missing([2544, 201939, 999999])}")
    
    # Sauvegarder
    cache.save_cache()
    print("Cache sauvegardé")
