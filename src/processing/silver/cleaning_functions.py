"""
Fonctions pures de nettoyage des données joueurs.

Toutes les fonctions sont idempotents et sans effet de bord.
"""

import logging
from typing import Dict, Optional

# Import des transformations de base
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.transformations import (
    convert_height_to_cm,
    convert_weight_to_kg,
    standardize_position,
    standardize_date,
    calculate_age,
    convert_to_int_safe
)

logger = logging.getLogger(__name__)


def clean_player_record(player: Dict) -> Dict:
    """
    Nettoie un enregistrement joueur complet.
    
    Args:
        player: Dict avec données brutes du joueur
        
    Returns:
        Dict avec données nettoyées
    """
    cleaned = player.copy()
    
    # Conversions physiques
    if cleaned.get('height'):
        cleaned['height_cm'] = convert_height_to_cm(cleaned['height'])
    
    if cleaned.get('weight'):
        cleaned['weight_kg'] = convert_weight_to_kg(cleaned['weight'])
    
    # Standardisations
    if cleaned.get('position'):
        cleaned['position'] = standardize_position(cleaned['position'])
    
    if cleaned.get('birth_date'):
        cleaned['birth_date'] = standardize_date(cleaned['birth_date'])
    
    # Calcul âge
    if cleaned.get('birth_date'):
        cleaned['age'] = calculate_age(cleaned['birth_date'])
    
    # Conversion années en int
    cleaned['from_year'] = convert_to_int_safe(cleaned.get('from_year'))
    cleaned['to_year'] = convert_to_int_safe(cleaned.get('to_year'))
    cleaned['id'] = convert_to_int_safe(cleaned.get('id'), 0)
    
    # Nettoyage des champs temporaires
    cleaned.pop('height', None)
    cleaned.pop('weight', None)
    
    return cleaned


def impute_missing_data(player: Dict) -> Dict:
    """
    Impute les données manquantes basées sur la position.
    
    Args:
        player: Dict joueur avec potentiellement des données manquantes
        
    Returns:
        Dict avec données imputées si nécessaire
    """
    position = player.get('position', 'F')
    
    # Valeurs par défaut par position
    defaults = {
        'G': {'height_cm': 191, 'weight_kg': 90},
        'F': {'height_cm': 203, 'weight_kg': 102},
        'C': {'height_cm': 211, 'weight_kg': 115},
        'G-F': {'height_cm': 197, 'weight_kg': 96},
        'F-G': {'height_cm': 197, 'weight_kg': 96},
        'F-C': {'height_cm': 207, 'weight_kg': 109},
        'C-F': {'height_cm': 207, 'weight_kg': 109},
    }
    
    defaults_for_pos = defaults.get(position, defaults['F'])
    
    # Imputer si manquant
    if not player.get('height_cm'):
        player['height_cm'] = defaults_for_pos['height_cm']
        player['data_source'] = 'imputed'
    
    if not player.get('weight_kg'):
        player['weight_kg'] = defaults_for_pos['weight_kg']
        if player.get('data_source') != 'imputed':
            player['data_source'] = 'imputed'
    
    return player


def filter_complete_players(players: list, min_fields: int = 5) -> list:
    """
    Filtre les joueurs avec suffisamment de données.
    
    Args:
        players: Liste des joueurs
        min_fields: Nombre minimum de champs requis
        
    Returns:
        Liste filtrée
    """
    complete = []
    
    for player in players:
        # Compter les champs non vides
        filled = sum(1 for v in player.values() if v is not None and v != '')
        
        if filled >= min_fields:
            complete.append(player)
    
    logger.info(f"Filtrage: {len(complete)}/{len(players)} joueurs avec {min_fields}+ champs")
    return complete


if __name__ == "__main__":
    print("Test cleaning_functions:")
    
    # Test player
    test_player = {
        'id': 2544,
        'full_name': 'LeBron James',
        'height': '6-9',
        'weight': '250',
        'position': 'Forward',
        'birth_date': '1984-12-30',
        'data_source': 'api'
    }
    
    cleaned = clean_player_record(test_player)
    print(f"Height: {cleaned.get('height_cm')} cm")
    print(f"Weight: {cleaned.get('weight_kg')} kg")
    print(f"Position: {cleaned.get('position')}")
    print(f"Age: {cleaned.get('age')}")
