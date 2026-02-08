"""
Processing module - NBA Data Processing Pipeline

Ce module expose les fonctions de nettoyage et traitement des données NBA.
Architecture refactorisée pour NBA-17 (zéro duplication).
"""

from src.processing.silver.cleaning_functions import (
    clean_player_record,
    impute_missing_data,
    filter_complete_players,
)

from src.utils.transformations import (
    convert_height_to_cm,
    convert_weight_to_kg,
    standardize_position,
    standardize_date,
    calculate_age,
    convert_to_int_safe,
)

__all__ = [
    # Nettoyage
    'clean_player_record',
    'impute_missing_data', 
    'filter_complete_players',
    # Transformations
    'convert_height_to_cm',
    'convert_weight_to_kg',
    'standardize_position',
    'standardize_date',
    'calculate_age',
    'convert_to_int_safe',
]

__version__ = "2.0.0-refactored"
