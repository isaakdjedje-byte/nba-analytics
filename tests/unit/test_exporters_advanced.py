"""
Tests avancés pour les exporteurs NBA-29
"""

import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nba.reporting.exporters import (
    ParquetExporter, CSVExporter, JSONExporter, 
    DeltaExporter, get_exporter
)


class TestParquetExporterAdvanced:
    """Tests avancés exporteur Parquet"""
    
    def test_parquet_compression_options(self):
        """Test différentes options de compression"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            df = pd.DataFrame({
                "id": range(100),
                "value": np.random.randn(100)
            })
            
            input_path = Path(tmpdir) / "input.parquet"
            df.to_parquet(input_path)
            
            exporter = ParquetExporter(gold_path=Path(tmpdir))
            output_dir = Path(tmpdir) / "exports"
            
            # Test sans compression
            result1 = exporter.export(
                dataset="input",
                output_dir=output_dir,
                compression=None
            )
            assert Path(result1).exists()
            
            # Test avec snappy
            result2 = exporter.export(
                dataset="input",
                output_dir=output_dir / "snappy",
                compression="snappy"
            )
            assert Path(result2).exists()
    
    def test_export_with_null_values(self):
        """Test export avec valeurs null"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            df = pd.DataFrame({
                "id": [1, 2, 3],
                "name": ["LeBron", None, "Curry"],
                "points": [25.0, np.nan, 30.0]
            })
            
            input_path = Path(tmpdir) / "input.parquet"
            df.to_parquet(input_path)
            
            exporter = ParquetExporter(gold_path=Path(tmpdir))
            result = exporter.export("input", Path(tmpdir) / "exports")
            
            # Vérifie lecture
            df_read = pd.read_parquet(result)
            assert len(df_read) == 3
            assert df_read["name"].isna().sum() == 1
    
    def test_export_large_dataset(self):
        """Test export dataset volumineux"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            # Crée un dataset de 10k lignes
            df = pd.DataFrame({
                "id": range(10000),
                "value": np.random.randn(10000),
                "category": np.random.choice(["A", "B", "C"], 10000)
            })
            
            input_path = Path(tmpdir) / "large.parquet"
            df.to_parquet(input_path)
            
            exporter = ParquetExporter(gold_path=Path(tmpdir))
            result = exporter.export("large", Path(tmpdir) / "exports")
            
            df_read = pd.read_parquet(result)
            assert len(df_read) == 10000


class TestCSVExporterAdvanced:
    """Tests avancés exporteur CSV"""
    
    def test_csv_encoding_utf8(self):
        """Test encodage UTF-8 avec caractères spéciaux"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            df = pd.DataFrame({
                "id": [1, 2],
                "name": ["Giannis Antetokounmpo", "Luka Dončić"],
                "team": ["Bucks", "Mavericks"]
            })
            
            input_path = Path(tmpdir) / "input.parquet"
            df.to_parquet(input_path)
            
            exporter = CSVExporter(gold_path=Path(tmpdir))
            result = exporter.export("input", Path(tmpdir) / "exports")
            
            # Vérifie encodage
            with open(result, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Giannis Antetokounmpo" in content
                assert "Luka Dončić" in content
    
    def test_csv_with_special_characters(self):
        """Test CSV avec caractères spéciaux et virgules"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            df = pd.DataFrame({
                "id": [1],
                "description": ["Player, with comma and \"quotes\""]
            })
            
            input_path = Path(tmpdir) / "input.parquet"
            df.to_parquet(input_path)
            
            exporter = CSVExporter(gold_path=Path(tmpdir))
            result = exporter.export("input", Path(tmpdir) / "exports")
            
            # Vérifie lecture correcte
            df_read = pd.read_csv(result)
            assert len(df_read) == 1


class TestJSONExporterAdvanced:
    """Tests avancés exporteur JSON"""
    
    def test_json_orient_options(self):
        """Test différentes orientations JSON"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            df = pd.DataFrame({
                "id": [1, 2],
                "name": ["LeBron", "Curry"]
            })
            
            input_path = Path(tmpdir) / "input.parquet"
            df.to_parquet(input_path)
            
            exporter = JSONExporter(gold_path=Path(tmpdir))
            
            # Test orient records (défaut)
            result1 = exporter.export(
                dataset="input",
                output_dir=Path(tmpdir) / "exports1",
                orient="records"
            )
            
            with open(result1) as f:
                data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 2
    
    def test_json_datetime_handling(self):
        """Test gestion des dates dans JSON"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            df = pd.DataFrame({
                "id": [1, 2],
                "date": pd.to_datetime(["2024-01-01", "2024-01-02"])
            })
            
            input_path = Path(tmpdir) / "input.parquet"
            df.to_parquet(input_path)
            
            exporter = JSONExporter(gold_path=Path(tmpdir))
            result = exporter.export("input", Path(tmpdir) / "exports")
            
            with open(result) as f:
                data = json.load(f)
            
            # Les dates doivent être converties en string
            assert isinstance(data[0]["date"], str)


class TestExporterErrorHandling:
    """Tests gestion des erreurs"""
    
    def test_export_nonexistent_dataset(self):
        """Test export dataset inexistant"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            exporter = ParquetExporter(gold_path=Path(tmpdir))
            
            with pytest.raises(FileNotFoundError):
                exporter.export("nonexistent", Path(tmpdir) / "exports")
    
    def test_get_exporter_invalid_format(self):
        """Test factory avec format invalide"""
        with pytest.raises(ValueError) as exc_info:
            get_exporter("invalid_format")
        
        assert "Format non supporté" in str(exc_info.value)
    
    def test_delta_exporter_without_dependency(self):
        """Test DeltaExporter sans dépendance"""
        exporter = DeltaExporter()
        
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            df = pd.DataFrame({"id": [1]})
            input_path = Path(tmpdir) / "input.parquet"
            df.to_parquet(input_path)
            
            # Si deltalake n'est pas installé, doit lever ImportError
            if not exporter.has_delta:
                with pytest.raises(ImportError):
                    exporter.export("input", Path(tmpdir) / "exports")


class TestExporterFactory:
    """Tests factory d'exporteurs"""
    
    def test_all_supported_formats(self):
        """Test que tous les formats supportés fonctionnent"""
        supported_formats = ["parquet", "csv", "json"]
        
        for fmt in supported_formats:
            exporter = get_exporter(fmt)
            assert exporter is not None
            assert exporter.format_name == fmt
    
    def test_case_insensitivity(self):
        """Test insensibilité à la casse"""
        exporter1 = get_exporter("PARQUET")
        exporter2 = get_exporter("Parquet")
        exporter3 = get_exporter("parquet")
        
        assert isinstance(exporter1, ParquetExporter)
        assert isinstance(exporter2, ParquetExporter)
        assert isinstance(exporter3, ParquetExporter)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
