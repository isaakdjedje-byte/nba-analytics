"""
Stratification des joueurs NBA en 3 datasets Silver.

Separe les 5103 joueurs selon leur periode et disponibilite des donnees:
- all: Tous les joueurs (validation legere)
- intermediate: Joueurs 2000-2016 avec donnees physiques (validation medium)
- contemporary: Joueurs 2016+ pour ML (validation stricte)
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("configs/silver_stratification.yaml")


def load_stratification_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Charge la configuration de stratification depuis YAML.
    
    Args:
        config_path: Chemin vers le fichier YAML (defaut: configs/silver_stratification.yaml)
        
    Returns:
        Dictionnaire de configuration
    """
    path = config_path or DEFAULT_CONFIG_PATH
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration chargee: {path}")
        return config
    except FileNotFoundError:
        logger.error(f"Fichier de configuration non trouve: {path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Erreur parsing YAML: {e}")
        raise


def stratify_players(
    players: List[Dict[str, Any]], 
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Stratifie les joueurs en 3 datasets selon leur periode.
    
    Args:
        players: Liste des joueurs depuis la couche Bronze
        config: Configuration de stratification (chargee si None)
        
    Returns:
        Dict avec cles 'all', 'intermediate', 'contemporary'
    """
    if config is None:
        config = load_stratification_config()
    
    # Initialisation des datasets
    result = {
        'all': players.copy(),
        'intermediate': [],
        'contemporary': []
    }
    
    # IDs des joueurs critiques a inclure partout
    critical_ids = set(config.get('critical_player_ids', []))
    
    # Configuration des niveaux
    levels_config = config.get('validation_levels', {})
    intermediate_config = levels_config.get('intermediate', {})
    contemporary_config = levels_config.get('contemporary', {})
    
    # Ranges pour intermediate (2000-2016)
    intermediate_ranges = intermediate_config.get('id_ranges', [])
    
    # Ranges pour contemporary (2016+)
    contemporary_ranges = contemporary_config.get('id_ranges', [])
    
    logger.info(f"Stratification de {len(players)} joueurs...")
    
    for player in players:
        player_id = player.get('id', 0)
        
        # Contemporary: ID >= 1,620,000
        if _is_in_ranges(player_id, contemporary_ranges):
            result['contemporary'].append(player)
        
        # Intermediate: ID entre 760,000 et 1,620,000
        elif _is_in_ranges(player_id, intermediate_ranges):
            result['intermediate'].append(player)
    
    # Ajouter les joueurs critiques aux datasets detailles si necessaire
    for player in players:
        player_id = player.get('id', 0)
        if player_id in critical_ids:
            for key in ['intermediate', 'contemporary']:
                if player not in result[key]:
                    result[key].append(player)
    
    # Log des statistiques
    logger.info(f"Stratification terminee:")
    logger.info(f"  - all: {len(result['all'])} joueurs")
    logger.info(f"  - intermediate: {len(result['intermediate'])} joueurs")
    logger.info(f"  - contemporary: {len(result['contemporary'])} joueurs")
    
    return result


def _is_in_ranges(player_id: int, ranges: List[Dict[str, Any]]) -> bool:
    """
    Verifie si un ID de joueur est dans les ranges definis.
    
    Args:
        player_id: ID du joueur
        ranges: Liste de ranges avec 'min' et 'max' (max=None pour infini)
        
    Returns:
        True si l'ID est dans l'un des ranges
    """
    for range_def in ranges:
        min_id = range_def.get('min', 0)
        max_id = range_def.get('max')
        
        if max_id is None:
            # Range ouvert (ex: >= 1620000)
            if player_id >= min_id:
                return True
        else:
            # Range ferme
            if min_id <= player_id < max_id:
                return True
    
    return False


def get_validation_config(level: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Recupere la configuration de validation pour un niveau specifique.
    
    Args:
        level: Niveau de validation ('all', 'intermediate', 'contemporary')
        config: Configuration complete (chargee si None)
        
    Returns:
        Configuration du niveau demande
    """
    if config is None:
        config = load_stratification_config()
    
    levels = config.get('validation_levels', {})
    
    if level not in levels:
        raise ValueError(f"Niveau invalide: {level}. Choix: {list(levels.keys())}")
    
    return levels[level]


if __name__ == "__main__":
    # Test simple
    import json
    
    print("Test de stratification:")
    
    # Charger quelques joueurs de test
    try:
        with open('data/raw/all_players_historical.json', 'r') as f:
            data = json.load(f)
            test_players = data['data'][:100]  # Premier 100 joueurs
        
        result = stratify_players(test_players)
        
        print(f"\nResultats sur {len(test_players)} joueurs:")
        for key, players in result.items():
            print(f"  {key}: {len(players)} joueurs")
            
    except FileNotFoundError:
        print("Donnees de test non disponibles")
    except Exception as e:
        print(f"Erreur: {e}")
