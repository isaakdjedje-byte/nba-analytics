"""
Tests pour le gestionnaire de cache API (utils/caching.py)
"""

import json
import tempfile
from pathlib import Path
import pytest

from src.utils.caching import APICacheManager


class TestAPICacheManager:
    """Tests pour APICacheManager."""
    
    @pytest.fixture
    def temp_cache_file(self):
        """Crée un fichier temporaire pour le cache."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json.dumps({"metadata": {}, "data": {}}))
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def cache_manager(self, temp_cache_file):
        """Crée un gestionnaire de cache avec fichier temporaire."""
        return APICacheManager(cache_path=temp_cache_file)
    
    def test_initialization(self, cache_manager):
        """Test initialisation."""
        assert cache_manager is not None
        assert cache_manager.cache_data == {}
    
    def test_set_and_get(self, cache_manager):
        """Test stockage et récupération."""
        player_data = {"name": "LeBron James", "height": "6-9"}
        
        cache_manager.set(2544, player_data)
        retrieved = cache_manager.get(2544)
        
        assert retrieved == player_data
    
    def test_exists(self, cache_manager):
        """Test vérification existence."""
        assert not cache_manager.exists(2544)
        
        cache_manager.set(2544, {"name": "LeBron"})
        assert cache_manager.exists(2544)
    
    def test_filter_missing(self, cache_manager):
        """Test filtrage IDs manquants."""
        cache_manager.set(2544, {"name": "LeBron"})
        cache_manager.set(201939, {"name": "Curry"})
        
        player_ids = [2544, 201939, 999999]
        missing = cache_manager.filter_missing(player_ids)
        
        assert len(missing) == 1
        assert 999999 in missing
    
    def test_get_cached_ids(self, cache_manager):
        """Test récupération IDs en cache."""
        cache_manager.set(2544, {"name": "LeBron"})
        cache_manager.set(201939, {"name": "Curry"})
        
        cached_ids = cache_manager.get_cached_ids()
        
        assert len(cached_ids) == 2
        assert 2544 in cached_ids
        assert 201939 in cached_ids
    
    def test_get_stats(self, cache_manager):
        """Test statistiques cache."""
        cache_manager.set(2544, {"name": "LeBron"})
        
        stats = cache_manager.get_stats()
        
        assert stats['total_cached'] == 1
        assert 'cache_file' in stats
    
    def test_save_and_load(self, temp_cache_file):
        """Test sauvegarde et chargement."""
        # Créer et sauvegarder
        cache1 = APICacheManager(cache_path=temp_cache_file)
        cache1.set(2544, {"name": "LeBron"})
        cache1.save_cache()
        
        # Recharger
        cache2 = APICacheManager(cache_path=temp_cache_file)
        
        assert cache2.exists(2544)
        assert cache2.get(2544) == {"name": "LeBron"}
    
    def test_clear(self, cache_manager):
        """Test vidage cache."""
        cache_manager.set(2544, {"name": "LeBron"})
        assert cache_manager.exists(2544)
        
        cache_manager.clear()
        
        assert not cache_manager.exists(2544)
        assert len(cache_manager.cache_data) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
