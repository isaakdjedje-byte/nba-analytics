#!/usr/bin/env python3
"""
NBA-17: Tests du pipeline de nettoyage des données joueurs
Tests complets et simples pour clean_players.py - Version refactorisée v2.0

Mise à jour: Utilise les fonctions importées depuis transformations.py et cleaning_functions.py
"""

import pytest
import json
from datetime import datetime, date
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

from src.processing.clean_players import PlayersDataCleaner

# Import des fonctions utilitaires (refactoring v2.0)
from src.utils.transformations import (
    convert_height_to_cm,
    convert_weight_to_kg,
    standardize_position,
    standardize_date,
    calculate_age,
)

from src.processing.silver.cleaning_functions import (
    impute_missing_data,
)


class TestPlayersDataCleaner:
    """Tests complets pour le nettoyeur de données joueurs."""
    
    @pytest.fixture(scope="class")
    def cleaner(self):
        """Fixture pour le nettoyeur."""
        return PlayersDataCleaner()
    
    @pytest.fixture(scope="class")
    def spark_session(self):
        """Fixture pour la session Spark."""
        spark = SparkSession.builder \
            .appName("NBA-Tests") \
            .master("local[*]") \
            .getOrCreate()
        yield spark
        spark.stop()
    
    def test_initialization(self, cleaner):
        """Test que le nettoyeur s'initialise correctement."""
        assert cleaner is not None
        assert cleaner.config is not None
        assert cleaner.spark is not None
        assert cleaner.stats['total'] == 0
    
    def test_convert_height_to_cm(self, cleaner):
        """Test conversion height '6-8' -> 203 cm via transformations.py."""
        # Utilise la fonction importée depuis transformations.py
        assert convert_height_to_cm('6-8') == 203
        assert convert_height_to_cm('7-2') == 218
        assert convert_height_to_cm('5-9') == 175
        assert convert_height_to_cm(None) is None
        assert convert_height_to_cm('') is None
    
    def test_convert_weight_to_kg(self, cleaner):
        """Test conversion weight 225 lbs -> 102 kg via transformations.py."""
        # Utilise la fonction importée depuis transformations.py
        assert convert_weight_to_kg(225) == 102
        assert convert_weight_to_kg('225') == 102
        assert convert_weight_to_kg('225 lbs') == 102
        assert abs(convert_weight_to_kg(250) - 113) < 1
        assert convert_weight_to_kg(None) is None
    
    def test_standardize_position(self, cleaner):
        """Test standardisation des positions via transformations.py."""
        # Utilise la fonction importée depuis transformations.py
        assert standardize_position('Guard') == 'G'
        assert standardize_position('Forward') == 'F'
        assert standardize_position('Center') == 'C'
        assert standardize_position('G-F') == 'G-F'
        assert standardize_position('F-C') == 'F-C'
        assert standardize_position(None) == 'Unknown'
        assert standardize_position('') == 'Unknown'
    
    def test_standardize_date(self, cleaner):
        """Test standardisation des dates via transformations.py."""
        # Utilise la fonction importée depuis transformations.py
        assert standardize_date('1984-12-30') == '1984-12-30'
        assert standardize_date('DEC 30, 1984') == '1984-12-30'
        assert standardize_date(None) is None
    
    def test_calculate_age(self, cleaner):
        """Test calcul de l'âge via transformations.py."""
        # Utilise la fonction importée depuis transformations.py
        current_year = date.today().year
        age = calculate_age('1984-12-30')
        assert age is not None
        assert age >= current_year - 1984 - 1  # -1 si anniversaire pas passé
    
    def test_impute_height(self, cleaner):
        """Test imputation de la taille via cleaning_functions.py."""
        # Utilise la fonction importée depuis cleaning_functions.py
        player_g = impute_missing_data({'position': 'G'})
        assert player_g['height_cm'] == 191
        
        player_f = impute_missing_data({'position': 'F'})
        assert player_f['height_cm'] == 203
        
        player_c = impute_missing_data({'position': 'C'})
        assert player_c['height_cm'] == 211
    
    def test_impute_weight(self, cleaner):
        """Test imputation du poids via cleaning_functions.py."""
        # Utilise la fonction importée depuis cleaning_functions.py
        player_g = impute_missing_data({'position': 'G'})
        assert player_g['weight_kg'] == 90
        
        player_f = impute_missing_data({'position': 'F'})
        assert player_f['weight_kg'] == 102
        
        player_c = impute_missing_data({'position': 'C'})
        assert player_c['weight_kg'] == 115
    
    def test_clean_and_convert(self, cleaner):
        """Test nettoyage complet."""
        test_players = {
            1: {
                'id': 1,
                'full_name': 'Test Player',
                'is_active': True,
                'height': '6-8',
                'weight': 225,
                'position': 'Forward',
                'birth_date': '1990-01-01',
                'age': 34,
                'data_source': 'test'
            }
        }
        
        result = cleaner.clean_and_convert(test_players)
        
        assert len(result) == 1
        player = result[0]
        assert player['height_cm'] == 203
        assert player['weight_kg'] == 102
        assert player['position'] == 'F'
        assert 'height' not in player  # Colonne originale supprimée
        assert 'weight' not in player
    
    def test_validate_data_no_duplicates(self, cleaner):
        """Test validation sans doublons."""
        players = [
            {'id': 1, 'full_name': 'Player 1'},
            {'id': 2, 'full_name': 'Player 2'},
            {'id': 3, 'full_name': 'Player 3'}
        ]
        assert cleaner.validate_data(players) is True
    
    def test_validate_data_critical_columns(self, cleaner):
        """Test validation colonnes critiques."""
        # Joueur avec id manquant
        players_invalid = [
            {'id': None, 'full_name': 'Invalid'},
            {'id': 2, 'full_name': 'Valid'}
        ]
        assert cleaner.validate_data(players_invalid) is False
    
    def test_stats_tracking(self, cleaner):
        """Test suivi des statistiques."""
        assert 'total' in cleaner.stats
        assert 'from_roster' in cleaner.stats
        assert 'from_api' in cleaner.stats
        assert 'from_csv' in cleaner.stats
        assert 'imputed' in cleaner.stats


class TestIntegration:
    """Tests d'intégration simples."""
    
    def test_import_clean_players(self):
        """Test que le module s'importe correctement."""
        try:
            from src.processing.clean_players import PlayersDataCleaner
            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
    
    def test_class_instantiation(self):
        """Test instanciation de la classe."""
        from src.processing.clean_players import PlayersDataCleaner
        cleaner = PlayersDataCleaner()
        assert cleaner is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
