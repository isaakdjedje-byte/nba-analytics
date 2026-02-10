"""
Tests unitaires pour le module reporting (NBA-29)
"""

import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nba.reporting.catalog import DataCatalog, DatasetInfo
from nba.reporting.exporters import (
    ParquetExporter, CSVExporter, JSONExporter, get_exporter
)


class TestDataCatalog:
    """Tests pour le catalogue de données"""
    
    def test_init_creates_database(self):
        """Test que l'initialisation crée la BDD SQLite"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            db_path = Path(tmpdir) / "test_catalog.db"
            catalog = DataCatalog(str(db_path))
            
            assert db_path.exists()
            assert catalog.db_path == db_path
    
    def test_register_and_retrieve_dataset(self):
        """Test registration et récupération d'un dataset"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            catalog = DataCatalog(str(Path(tmpdir) / "catalog.db"))
            
            # Registration
            success = catalog.register_dataset(
                name="test_players",
                format="parquet",
                path="/data/test.parquet",
                record_count=100,
                size_bytes=1024,
                schema={"id": "int64", "name": "object"},
                metadata={"source": "test"}
            )
            
            assert success is True
            
            # Récupération
            info = catalog.get_dataset_info("test_players")
            assert info is not None
            assert info.name == "test_players"
            assert info.format == "parquet"
            assert info.record_count == 100
            assert info.size_bytes == 1024
    
    def test_list_datasets(self):
        """Test listage des datasets"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            catalog = DataCatalog(str(Path(tmpdir) / "catalog.db"))
            
            # Ajoute plusieurs datasets
            for i in range(3):
                catalog.register_dataset(
                    name=f"dataset_{i}",
                    format="parquet",
                    path=f"/data/{i}.parquet",
                    record_count=i * 100
                )
            
            datasets = catalog.list_datasets()
            assert len(datasets) == 3
    
    def test_export_history(self):
        """Test historique des exports"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            catalog = DataCatalog(str(Path(tmpdir) / "catalog.db"))
            
            # Enregistre dataset
            catalog.register_dataset("teams", "parquet", "/data/teams.parquet")
            
            # Enregistre exports
            catalog.register_export("teams", "csv", "/exports/teams.csv")
            catalog.register_export("teams", "parquet", "/exports/teams.parquet")
            
            history = catalog.get_export_history("teams")
            assert len(history) == 2
            assert history[0]["format"] in ["csv", "parquet"]


class TestExporters:
    """Tests pour les exporteurs"""
    
    def test_parquet_exporter(self):
        """Test exporteur Parquet"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            # Crée un dataset de test
            df = pd.DataFrame({
                "id": [1, 2, 3],
                "name": ["LeBron", "Curry", "Durant"],
                "season": ["2023-24", "2023-24", "2023-24"]
            })
            
            input_path = Path(tmpdir) / "input.parquet"
            df.to_parquet(input_path)
            
            # Exporte
            exporter = ParquetExporter(gold_path=Path(tmpdir))
            output_dir = Path(tmpdir) / "exports"
            result = exporter.export(
                dataset="input",
                output_dir=output_dir
            )
            
            assert Path(result).exists()
    
    def test_csv_exporter(self):
        """Test exporteur CSV"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            df = pd.DataFrame({
                "id": [1, 2, 3],
                "name": ["LeBron", "Curry", "Durant"]
            })
            
            input_path = Path(tmpdir) / "input.parquet"
            df.to_parquet(input_path)
            
            exporter = CSVExporter(gold_path=Path(tmpdir))
            output_dir = Path(tmpdir) / "exports"
            result = exporter.export("input", output_dir)
            
            assert Path(result).exists()
            assert Path(result).suffix == ".csv"
            
            # Vérifie le contenu
            df_read = pd.read_csv(result)
            assert len(df_read) == 3
    
    def test_json_exporter(self):
        """Test exporteur JSON"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            df = pd.DataFrame({
                "id": [1, 2],
                "name": ["LeBron", "Curry"]
            })
            
            input_path = Path(tmpdir) / "input.parquet"
            df.to_parquet(input_path)
            
            exporter = JSONExporter(gold_path=Path(tmpdir))
            output_dir = Path(tmpdir) / "exports"
            result = exporter.export("input", output_dir)
            
            assert Path(result).exists()
            
            # Vérifie le JSON
            with open(result) as f:
                data = json.load(f)
            assert len(data) == 2
    
    def test_partitioned_export(self):
        """Test export avec partitionnement"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            df = pd.DataFrame({
                "id": [1, 2, 3, 4],
                "season": ["2022-23", "2022-23", "2023-24", "2023-24"]
            })
            
            input_path = Path(tmpdir) / "input.parquet"
            df.to_parquet(input_path)
            
            exporter = ParquetExporter(gold_path=Path(tmpdir))
            output_dir = Path(tmpdir) / "exports"
            result = exporter.export(
                dataset="input",
                output_dir=output_dir,
                partition_by="season"
            )
            
            # Vérifie les partitions
            partition_base = Path(result)
            assert partition_base.exists()
            assert (partition_base / "season=2022-23").exists()
            assert (partition_base / "season=2023-24").exists()
    
    def test_get_exporter_factory(self):
        """Test factory d'exporteurs"""
        parquet_exp = get_exporter("parquet")
        assert isinstance(parquet_exp, ParquetExporter)
        
        csv_exp = get_exporter("csv")
        assert isinstance(csv_exp, CSVExporter)
        
        json_exp = get_exporter("json")
        assert isinstance(json_exp, JSONExporter)
        
        with pytest.raises(ValueError):
            get_exporter("unknown")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
