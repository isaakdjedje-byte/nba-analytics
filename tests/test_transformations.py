"""
Tests pour les fonctions de transformation (utils/transformations.py)
"""

import pytest
from src.utils.transformations import (
    convert_height_to_cm,
    convert_weight_to_kg,
    standardize_position,
    standardize_date,
    calculate_age,
    convert_to_int_safe
)


class TestHeightConversion:
    """Tests conversion taille."""
    
    def test_convert_standard_height(self):
        """Conversion standard '6-8' -> 203 cm."""
        assert convert_height_to_cm('6-8') == 203
    
    def test_convert_small_height(self):
        """Petite taille '5-9' -> 175 cm."""
        assert convert_height_to_cm('5-9') == 175
    
    def test_convert_tall_height(self):
        """Grande taille '7-0' -> 213 cm."""
        assert convert_height_to_cm('7-0') == 213
    
    def test_convert_none_returns_none(self):
        """None retourne None."""
        assert convert_height_to_cm(None) is None
    
    def test_convert_empty_returns_none(self):
        """String vide retourne None."""
        assert convert_height_to_cm('') is None
    
    def test_convert_invalid_returns_none(self):
        """Format invalide retourne None."""
        assert convert_height_to_cm('invalid') is None


class TestWeightConversion:
    """Tests conversion poids."""
    
    def test_convert_standard_weight(self):
        """Conversion standard 225 lbs -> 102 kg."""
        result = convert_weight_to_kg(225)
        assert result == 102
    
    def test_convert_with_lbs_suffix(self):
        """Conversion avec suffixe '250 lbs'."""
        result = convert_weight_to_kg('250 lbs')
        assert result == 113
    
    def test_convert_float_weight(self):
        """Conversion float 200.5 lbs."""
        result = convert_weight_to_kg(200.5)
        assert result == 91
    
    def test_convert_none_returns_none(self):
        """None retourne None."""
        assert convert_weight_to_kg(None) is None


class TestPositionStandardization:
    """Tests standardisation position."""
    
    def test_standardize_guard(self):
        """'Guard' -> 'G'."""
        assert standardize_position('Guard') == 'G'
    
    def test_standardize_forward(self):
        """'Forward' -> 'F'."""
        assert standardize_position('Forward') == 'F'
    
    def test_standardize_center(self):
        """'Center' -> 'C'."""
        assert standardize_position('Center') == 'C'
    
    def test_standardize_forward_center(self):
        """'Forward-Center' -> 'F-C'."""
        assert standardize_position('Forward-Center') == 'F-C'
    
    def test_standardize_unknown(self):
        """Position inconnue -> 'Unknown'."""
        assert standardize_position(None) == 'Unknown'


class TestDateStandardization:
    """Tests standardisation date."""
    
    def test_standardize_iso_date(self):
        """ISO déjà standard."""
        assert standardize_date('1984-12-30') == '1984-12-30'
    
    def test_standardize_verbose_date(self):
        """Format 'DEC 30, 1984'."""
        assert standardize_date('DEC 30, 1984') == '1984-12-30'
    
    def test_standardize_none(self):
        """None retourne None."""
        assert standardize_date(None) is None


class TestAgeCalculation:
    """Tests calcul âge."""
    
    def test_calculate_age_from_birth_date(self):
        """Calcul depuis date de naissance."""
        age = calculate_age('1984-12-30')
        assert isinstance(age, int)
        assert age > 30  # LeBron doit avoir plus de 30 ans
    
    def test_calculate_age_none(self):
        """None retourne None."""
        assert calculate_age(None) is None


class TestSafeIntConversion:
    """Tests conversion int sécurisée."""
    
    def test_convert_int(self):
        """Int reste int."""
        assert convert_to_int_safe(2023) == 2023
    
    def test_convert_float(self):
        """Float -> int."""
        assert convert_to_int_safe(2023.0) == 2023
    
    def test_convert_string(self):
        """String -> int."""
        assert convert_to_int_safe('2023') == 2023
    
    def test_convert_invalid_returns_default(self):
        """Valeur invalide retourne default."""
        assert convert_to_int_safe('invalid', 0) == 0
    
    def test_convert_none_returns_default(self):
        """None retourne default."""
        assert convert_to_int_safe(None, 0) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
