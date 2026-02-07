"""
Tests pour le pipeline orchestrateur (pipeline/)
"""

import pytest
from unittest.mock import Mock, patch

from src.pipeline import PlayersPipeline


class TestPlayersPipeline:
    """Tests pour PlayersPipeline."""
    
    def test_initialization(self):
        """Test initialisation pipeline."""
        pipeline = PlayersPipeline()
        
        assert pipeline is not None
        assert pipeline.bronze is not None
        assert pipeline.silver is not None
        assert pipeline.gold is not None
    
    def test_execution_stats_initialization(self):
        """Test initialisation stats."""
        pipeline = PlayersPipeline()
        
        assert pipeline.execution_stats['start_time'] is None
        assert pipeline.execution_stats['end_time'] is None
        assert pipeline.execution_stats['steps'] == {}
    
    @patch('src.pipeline.players_pipeline.PlayersBronze')
    @patch('src.pipeline.players_pipeline.PlayersSilver')
    @patch('src.pipeline.players_pipeline.PlayersGold')
    def test_run_full_pipeline_success(self, mock_gold, mock_silver, mock_bronze):
        """Test pipeline complet succès."""
        # Configuration des mocks
        mock_bronze_instance = Mock()
        mock_bronze_instance.run_bronze_layer.return_value = [
            {'id': 1, 'full_name': 'Test'}
        ]
        mock_bronze.return_value = mock_bronze_instance
        
        mock_silver_instance = Mock()
        mock_silver_instance.run_silver_layer.return_value = [
            {'id': 1, 'full_name': 'Test', 'height_cm': 200}
        ]
        mock_silver.return_value = mock_silver_instance
        
        mock_gold_instance = Mock()
        mock_df = Mock()
        mock_df.count.return_value = 1
        mock_gold_instance.run_gold_layer.return_value = mock_df
        mock_gold.return_value = mock_gold_instance
        
        # Exécution
        pipeline = PlayersPipeline()
        
        # Patch les attributs directement
        pipeline.bronze = mock_bronze_instance
        pipeline.silver = mock_silver_instance
        pipeline.gold = mock_gold_instance
        
        result = pipeline.run_full_pipeline()
        
        assert result is True
        assert 'Bronze Layer' in pipeline.execution_stats['steps']
        assert 'Silver Layer' in pipeline.execution_stats['steps']
        assert 'Gold Layer' in pipeline.execution_stats['steps']
    
    def test_run_bronze_layer_failure(self):
        """Test échec couche Bronze."""
        pipeline = PlayersPipeline()
        
        # Mock pour simuler échec
        pipeline.bronze = Mock()
        pipeline.bronze.run_bronze_layer.side_effect = Exception("API Error")
        
        result = pipeline.run_bronze_layer()
        
        assert result is False
        assert pipeline.execution_stats['steps']['Bronze Layer']['status'] == 'failed'
    
    def test_summary_print(self, caplog):
        """Test affichage résumé."""
        pipeline = PlayersPipeline()
        
        # Simuler des stats
        pipeline.execution_stats['steps'] = {
            'Bronze Layer': {
                'status': 'success',
                'duration_seconds': 10.5,
                'players_count': 1200
            }
        }
        pipeline.execution_stats['duration_seconds'] = 10.5
        
        # Ne devrait pas planter
        pipeline._print_summary()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
