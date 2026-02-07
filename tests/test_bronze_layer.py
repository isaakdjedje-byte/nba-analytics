"""
Tests pour la couche Bronze (processing/bronze/)
"""

import pytest
from src.processing.bronze import PlayersBronze, BronzeValidator


class TestBronzeValidator:
    """Tests pour BronzeValidator."""
    
    def test_validate_empty_list_fails(self):
        """Liste vide = échec."""
        validator = BronzeValidator()
        result = validator.validate([])
        
        assert not result
        assert len(validator.errors) > 0
    
    def test_validate_unique_ids(self):
        """IDs uniques = succès."""
        validator = BronzeValidator()
        
        players = [
            {'id': 1, 'full_name': 'Player 1'},
            {'id': 2, 'full_name': 'Player 2'},
        ]
        
        result = validator.validate(players)
        assert result
    
    def test_validate_duplicate_ids_fails(self):
        """IDs dupliqués = échec."""
        validator = BronzeValidator()
        
        players = [
            {'id': 1, 'full_name': 'Player 1'},
            {'id': 1, 'full_name': 'Player 1 Duplicate'},
        ]
        
        result = validator.validate(players)
        assert not result
    
    def test_validate_required_fields(self):
        """Champs requis présents = succès."""
        validator = BronzeValidator()
        
        players = [
            {'id': 1, 'full_name': 'Test Player'},
        ]
        
        result = validator.validate(players)
        assert result
    
    def test_validate_missing_required_field_fails(self):
        """Champ requis manquant = échec."""
        validator = BronzeValidator()
        
        players = [
            {'id': 1},  # Pas de full_name
        ]
        
        result = validator.validate(players)
        assert not result
    
    def test_validate_completion_rate(self):
        """Taux de complétion suffisant = succès."""
        validator = BronzeValidator(min_completion_rate=0.3)
        
        players = [
            {'id': 1, 'full_name': 'Test', 'height': '6-8', 'weight': '200'},
        ]
        
        result = validator.validate(players)
        assert result


class TestPlayersBronze:
    """Tests pour PlayersBronze."""
    
    def test_initialization(self):
        """Test initialisation."""
        bronze = PlayersBronze()
        
        assert bronze is not None
        assert bronze.stats['total'] == 0
    
    def test_critical_player_ids_defined(self):
        """IDs critiques définis."""
        bronze = PlayersBronze()
        
        assert len(bronze.CRITICAL_PLAYER_IDS) == 18
        assert 23 in bronze.CRITICAL_PLAYER_IDS  # Jordan
        assert 977 in bronze.CRITICAL_PLAYER_IDS  # Kobe
    
    def test_is_player_modern(self):
        """Test filtre joueurs modernes."""
        bronze = PlayersBronze()
        
        # ID moderne (2016+)
        assert bronze._is_player_modern(1_620_000)
        
        # Légende critique
        assert bronze._is_player_modern(23)  # Jordan
        
        # Joueur ancien
        assert not bronze._is_player_modern(100)  # Vieux joueur


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
