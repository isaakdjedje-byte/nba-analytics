"""
Tests pour la couche Silver (processing/silver/)
"""

import pytest
from src.processing.silver import PlayersSilver, SilverValidator
from src.processing.silver.cleaning_functions import clean_player_record


class TestSilverValidator:
    """Tests pour SilverValidator."""
    
    def test_validate_no_duplicates(self):
        """Pas de doublons = succès."""
        validator = SilverValidator()
        
        players = [
            {'id': 1, 'full_name': 'Player 1', 'height_cm': 200, 'weight_kg': 100, 'position': 'F'},
            {'id': 2, 'full_name': 'Player 2', 'height_cm': 190, 'weight_kg': 90, 'position': 'G'},
        ]
        
        result = validator.validate(players)
        assert result
    
    def test_validate_critical_fields_present(self):
        """Champs critiques présents = succès."""
        validator = SilverValidator()
        
        players = [
            {'id': 1, 'full_name': 'Test', 'height_cm': 200, 'weight_kg': 100, 'position': 'F'},
        ]
        
        result = validator.validate(players)
        assert result
    
    def test_validate_missing_critical_field_fails(self):
        """Champ critique manquant = échec."""
        validator = SilverValidator()
        
        players = [
            {'id': 1, 'full_name': 'Test', 'height_cm': 200},  # Pas de weight_kg
        ]
        
        result = validator.validate(players)
        assert not result
    
    def test_validate_value_ranges(self):
        """Valeurs dans les plages = succès."""
        validator = SilverValidator()
        
        players = [
            {'id': 1, 'full_name': 'Test', 'height_cm': 200, 'weight_kg': 100, 'position': 'F'},
        ]
        
        result = validator.validate(players)
        assert result  # Warnings mais pas échec
    
    def test_validate_null_rate(self):
        """Taux de nulls acceptable = succès."""
        validator = SilverValidator()
        
        players = [
            {'id': 1, 'full_name': 'Test', 'height_cm': 200, 'weight_kg': 100, 'position': 'F', 'birth_date': None},
        ]
        
        result = validator.validate(players)
        assert result


class TestCleaningFunctions:
    """Tests pour cleaning_functions."""
    
    def test_clean_player_record_conversion(self):
        """Test conversion complète."""
        player = {
            'id': 2544,
            'full_name': 'LeBron James',
            'first_name': 'LeBron',
            'last_name': 'James',
            'height': '6-9',
            'weight': '250',
            'position': 'Forward',
            'birth_date': '1984-12-30',
            'data_source': 'api'
        }
        
        cleaned = clean_player_record(player)
        
        assert cleaned['height_cm'] == 206  # 6-9 en cm
        assert cleaned['weight_kg'] == 113  # 250 lbs en kg
        assert cleaned['position'] == 'F'   # Standardisé
        assert cleaned['age'] is not None   # Calculé
        assert 'height' not in cleaned      # Supprimé
        assert 'weight' not in cleaned      # Supprimé
    
    def test_clean_player_partial_data(self):
        """Test avec données partielles."""
        player = {
            'id': 999,
            'full_name': 'Unknown Player',
            'data_source': 'base'
        }
        
        cleaned = clean_player_record(player)
        
        assert cleaned['id'] == 999
        assert cleaned['full_name'] == 'Unknown Player'
        assert cleaned.get('height_cm') is None


class TestPlayersSilver:
    """Tests pour PlayersSilver."""
    
    def test_initialization(self):
        """Test initialisation Spark."""
        silver = PlayersSilver()
        
        assert silver is not None
        assert silver.spark is not None
    
    def test_clean_players(self):
        """Test nettoyage liste joueurs."""
        silver = PlayersSilver()
        
        bronze_players = [
            {
                'id': 1,
                'full_name': 'Test Player',
                'height': '6-8',
                'weight': '225',
                'position': 'Guard',
                'data_source': 'api'
            }
        ]
        
        cleaned = silver.clean_players(bronze_players)
        
        assert len(cleaned) == 1
        assert cleaned[0]['height_cm'] == 203


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
