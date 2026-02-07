#!/usr/bin/env python3
"""
NBA-17: Tests du pipeline de nettoyage des données joueurs
Tests complets et simples pour clean_players.py
"""

import pytest
import json
from datetime import datetime, date
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

from src.processing.clean_players import PlayersDataCleaner


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
        """Test conversion height '6-8' -> 203 cm."""
        assert cleaner._convert_height_to_cm('6-8') == 203
        assert cleaner._convert_height_to_cm('7-2') == 218
        assert cleaner._convert_height_to_cm('5-9') == 175
        assert cleaner._convert_height_to_cm(None) is None
        assert cleaner._convert_height_to_cm('') is None
    
    def test_convert_weight_to_kg(self, cleaner):
        """Test conversion weight 225 lbs -> 102 kg."""
        assert cleaner._convert_weight_to_kg(225) == 102
        assert cleaner._convert_weight_to_kg('225') == 102
        assert cleaner._convert_weight_to_kg('225 lbs') == 102
        assert abs(cleaner._convert_weight_to_kg(250) - 113) < 1
        assert cleaner._convert_weight_to_kg(None) is None
    
    def test_standardize_position(self, cleaner):
        """Test standardisation des positions."""
        assert cleaner._standardize_position('Guard') == 'G'
        assert cleaner._standardize_position('Forward') == 'F'
        assert cleaner._standardize_position('Center') == 'C'
        assert cleaner._standardize_position('G-F') == 'G-F'
        assert cleaner._standardize_position('F-C') == 'F-C'
        assert cleaner._standardize_position(None) == 'Unknown'
        assert cleaner._standardize_position('') == 'Unknown'
    
    def test_standardize_date(self, cleaner):
        """Test standardisation des dates."""
        assert cleaner._standardize_date('1984-12-30') == '1984-12-30'
        assert cleaner._standardize_date('DEC 30, 1984') == '1984-12-30'
        assert cleaner._standardize_date(None) is None
    
    def test_calculate_age(self, cleaner):
        """Test calcul de l'âge."""
        current_year = date.today().year
        age = cleaner._calculate_age('1984-12-30')
        assert age is not None
        assert age >= current_year - 1984 - 1  # -1 si anniversaire pas passé
    
    def test_impute_height(self, cleaner):
        """Test imputation de la taille."""
        assert cleaner._impute_height({'position': 'G'}) == 191
        assert cleaner._impute_height({'position': 'F'}) == 203
        assert cleaner._impute_height({'position': 'C'}) == 211
        assert cleaner._impute_height({'position': 'Unknown'}) == 200
    
    def test_impute_weight(self, cleaner):
        """Test imputation du poids."""
        assert cleaner._impute_weight({'position': 'G'}) == 90
        assert cleaner._impute_weight({'position': 'F'}) == 102
        assert cleaner._impute_weight({'position': 'C'}) == 115
    
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
