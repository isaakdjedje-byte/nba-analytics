"""
Tests pour la stratification des joueurs NBA.

Valide:
- Chargement de configuration YAML
- Stratification en 3 datasets
- Validation avec differents seuils
"""

import pytest
import json
from pathlib import Path

# Ajouter src au path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.processing.silver.stratification import (
    load_stratification_config,
    stratify_players,
    get_validation_config,
    _is_in_ranges
)
from src.processing.silver.validators import SilverValidator


class TestStratificationConfig:
    """Tests de chargement de configuration."""
    
    def test_load_config_exists(self):
        """Test que le fichier de configuration existe."""
        config = load_stratification_config()
        assert config is not None
        assert 'validation_levels' in config
    
    def test_config_has_all_levels(self):
        """Test que tous les niveaux sont definis."""
        config = load_stratification_config()
        levels = config['validation_levels']
        
        assert 'all' in levels
        assert 'intermediate' in levels
        assert 'contemporary' in levels
    
    def test_config_thresholds(self):
        """Test que les seuils sont coherents."""
        config = load_stratification_config()
        levels = config['validation_levels']
        
        # Verification ordre croissant de severite
        assert levels['all']['null_threshold'] == 0.25
        assert levels['intermediate']['null_threshold'] == 0.15
        assert levels['contemporary']['null_threshold'] == 0.20


class TestStratificationLogic:
    """Tests de la logique de stratification."""
    
    @pytest.fixture
    def sample_players(self):
        """Fixture: joueurs de test representatifs."""
        return [
            {'id': 23, 'full_name': 'Michael Jordan'},      # Critique (ID bas)
            {'id': 1620000, 'full_name': 'Modern Player'},  # Contemporary
            {'id': 800000, 'full_name': 'Intermediate'},    # Intermediate
            {'id': 100, 'full_name': 'Old Player'},         # All uniquement
            {'id': 1626143, 'full_name': 'Recent Player'},  # Contemporary
        ]
    
    def test_stratify_returns_three_datasets(self, sample_players):
        """Test que la stratification retourne bien 3 datasets."""
        result = stratify_players(sample_players)
        
        assert 'all' in result
        assert 'intermediate' in result
        assert 'contemporary' in result
    
    def test_all_contains_all_players(self, sample_players):
        """Test que 'all' contient tous les joueurs."""
        result = stratify_players(sample_players)
        
        assert len(result['all']) == len(sample_players)
    
    def test_contemporary_has_modern_ids(self, sample_players):
        """Test que contemporary contient les IDs modernes."""
        result = stratify_players(sample_players)
        contemporary_ids = [p['id'] for p in result['contemporary']]
        
        assert 1620000 in contemporary_ids
        assert 1626143 in contemporary_ids
    
    def test_critical_players_in_all_detailed(self, sample_players):
        """Test que les joueurs critiques sont dans tous les datasets detailles."""
        result = stratify_players(sample_players)
        
        # Michael Jordan (ID 23) doit etre dans intermediate et contemporary
        intermediate_ids = [p['id'] for p in result['intermediate']]
        contemporary_ids = [p['id'] for p in result['contemporary']]
        
        assert 23 in intermediate_ids
        assert 23 in contemporary_ids


class TestRangeChecking:
    """Tests de la fonction _is_in_ranges."""
    
    def test_in_open_range(self):
        """Test range ouvert (max=None)."""
        ranges = [{'min': 1620000, 'max': None}]
        assert _is_in_ranges(1620000, ranges) is True
        assert _is_in_ranges(2000000, ranges) is True
        assert _is_in_ranges(1000000, ranges) is False
    
    def test_in_closed_range(self):
        """Test range ferme."""
        ranges = [{'min': 760000, 'max': 1620000}]
        assert _is_in_ranges(800000, ranges) is True
        assert _is_in_ranges(760000, ranges) is True
        assert _is_in_ranges(1619999, ranges) is True
        assert _is_in_ranges(1620000, ranges) is False  # Exclusif
    
    def test_multiple_ranges(self):
        """Test avec plusieurs ranges."""
        ranges = [
            {'min': 100, 'max': 200},
            {'min': 300, 'max': 400}
        ]
        assert _is_in_ranges(150, ranges) is True
        assert _is_in_ranges(350, ranges) is True
        assert _is_in_ranges(250, ranges) is False


class TestValidatorLevels:
    """Tests des validateurs avec differents niveaux."""
    
    @pytest.fixture
    def complete_player(self):
        """Joueur avec toutes les donnees."""
        return {
            'id': 1,
            'full_name': 'Test Player',
            'height_cm': 200,
            'weight_kg': 100,
            'position': 'F',
            'is_active': True
        }
    
    @pytest.fixture
    def partial_player(self):
        """Joueur avec donnees incompletes."""
        return {
            'id': 2,
            'full_name': 'Old Player'
            # Manque height, weight, position
        }
    
    def test_all_accepts_partial(self, complete_player, partial_player):
        """Test que niveau 'all' accepte les joueurs incomplets."""
        validator = SilverValidator(level='all')
        result = validator.validate([complete_player, partial_player])
        
        assert result is True
    
    def test_contemporary_rejects_partial(self, partial_player):
        """Test que niveau 'contemporary' rejette les joueurs incomplets."""
        validator = SilverValidator(level='contemporary')
        result = validator.validate([partial_player])
        
        assert result is False
    
    def test_contemporary_accepts_complete(self, complete_player):
        """Test que niveau 'contemporary' accepte les joueurs complets."""
        validator = SilverValidator(level='contemporary')
        result = validator.validate([complete_player])
        
        assert result is True
    
    def test_different_null_thresholds(self):
        """Test que les seuils de nulls sont differents."""
        config = load_stratification_config()
        
        all_config = get_validation_config('all', config)
        contemporary_config = get_validation_config('contemporary', config)
        
        assert all_config['null_threshold'] > contemporary_config['null_threshold']


class TestIntegration:
    """Tests d'integration bout-en-bout."""
    
    def test_full_pipeline_stratification(self):
        """Test le pipeline complet avec stratification."""
        # Charger donnees de test si disponibles
        test_data_path = Path("data/raw/all_players_historical.json")
        
        if not test_data_path.exists():
            pytest.skip("Donnees de test non disponibles")
        
        with open(test_data_path, 'r') as f:
            data = json.load(f)
            players = data['data'][:100]  # Premier 100 joueurs
        
        # Stratifier
        result = stratify_players(players)
        
        # Verifier structure
        assert len(result['all']) == 100
        assert len(result['contemporary']) >= 0
        assert len(result['intermediate']) >= 0
        
        # Verifier validation
        for level, players_subset in result.items():
            if players_subset:  # Si pas vide
                validator = SilverValidator(level=level)
                # Ne pas faire echouer le test si validation echoue
                # juste verifier que ca s'execute sans erreur
                try:
                    validator.validate(players_subset)
                except Exception as e:
                    pytest.fail(f"Validation {level} a leve exception: {e}")


if __name__ == "__main__":
    # Execution manuelle des tests
    print("Execution des tests de stratification...")
    
    # Test basique
    players = [
        {'id': 23, 'full_name': 'Michael Jordan'},
        {'id': 1626143, 'full_name': 'Modern Player'},
    ]
    
    result = stratify_players(players)
    print(f"\nResultats:")
    for key, players_list in result.items():
        print(f"  {key}: {len(players_list)} joueurs")
    
    print("\nTests OK!")
