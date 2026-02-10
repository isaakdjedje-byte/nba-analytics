"""
Tests d'intégration du Data Catalog avec données réelles
"""

import tempfile
from pathlib import Path
import pandas as pd
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nba.reporting.catalog import DataCatalog


class TestCatalogWithRealData:
    """Tests catalog avec données réelles"""
    
    def test_scan_real_datasets(self):
        """Test scan de vrais datasets"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            # Crée structure data/gold
            gold_path = Path(tmpdir) / "gold"
            gold_path.mkdir(parents=True, exist_ok=True)
            
            # Crée plusieurs datasets
            for dataset_name in ["players", "teams", "games"]:
                df = pd.DataFrame({
                    "id": range(100),
                    "name": [f"Item_{i}" for i in range(100)],
                    "season": ["2023-24"] * 100
                })
                df.to_parquet(gold_path / f"{dataset_name}.parquet")
            
            # Scan
            catalog = DataCatalog(str(Path(tmpdir) / "catalog.db"))
            count = catalog.scan_datasets(str(gold_path))
            
            assert count == 3
            
            # Vérifie registration
            datasets = catalog.list_datasets()
            assert len(datasets) == 3
            
            dataset_names = [ds.name for ds in datasets]
            assert "players" in dataset_names
            assert "teams" in dataset_names
            assert "games" in dataset_names
    
    def test_register_real_export(self):
        """Test registration d'export réel"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            catalog = DataCatalog(str(Path(tmpdir) / "catalog.db"))
            
            # Enregistre dataset
            catalog.register_dataset(
                name="real_players",
                format="parquet",
                path=str(Path(tmpdir) / "gold" / "players.parquet"),
                record_count=5000,
                size_bytes=1024000,
                schema={"id": "int64", "name": "object", "points": "float64"}
            )
            
            # Enregistre export
            catalog.register_export(
                dataset="real_players",
                format="csv",
                path=str(Path(tmpdir) / "exports" / "players.csv"),
                metadata={"compression": None, "partition": None}
            )
            
            # Vérifie historique
            history = catalog.get_export_history("real_players")
            assert len(history) == 1
            assert history[0]["format"] == "csv"
    
    def test_export_history_persistence(self):
        """Test persistance historique exports"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            db_path = Path(tmpdir) / "catalog.db"
            
            # Première instance
            catalog1 = DataCatalog(str(db_path))
            catalog1.register_dataset("test", "parquet", "/data/test.parquet")
            catalog1.register_export("test", "csv", "/exports/test.csv")
            
            # Deuxième instance (nouvelle connexion)
            catalog2 = DataCatalog(str(db_path))
            history = catalog2.get_export_history("test")
            
            assert len(history) == 1
            assert history[0]["path"] == "/exports/test.csv"
    
    def test_catalog_with_existing_data(self):
        """Test catalog avec données existantes"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            gold_path = Path(tmpdir) / "gold"
            gold_path.mkdir(parents=True, exist_ok=True)
            
            # Crée datasets existants
            df1 = pd.DataFrame({"id": [1, 2], "value": [10, 20]})
            df1.to_parquet(gold_path / "dataset1.parquet")
            
            # Premier scan
            catalog = DataCatalog(str(Path(tmpdir) / "catalog.db"))
            catalog.scan_datasets(str(gold_path))
            
            info1 = catalog.get_dataset_info("dataset1")
            assert info1.record_count == 2
            
            # Ajoute nouveau dataset
            df2 = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
            df2.to_parquet(gold_path / "dataset2.parquet")
            
            # Rescan
            catalog.scan_datasets(str(gold_path))
            
            datasets = catalog.list_datasets()
            assert len(datasets) == 2
    
    def test_dataset_schema_extraction(self):
        """Test extraction des schémas"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            gold_path = Path(tmpdir) / "gold"
            gold_path.mkdir(parents=True, exist_ok=True)
            
            # Dataset avec différents types
            df = pd.DataFrame({
                "id": [1, 2, 3],
                "name": ["A", "B", "C"],
                "points": [10.5, 20.3, 15.0],
                "active": [True, False, True],
                "birth_date": pd.to_datetime(["1990-01-01", "1995-01-01", "2000-01-01"])
            })
            
            df.to_parquet(gold_path / "complex.parquet")
            
            catalog = DataCatalog(str(Path(tmpdir) / "catalog.db"))
            catalog.scan_datasets(str(gold_path))
            
            info = catalog.get_dataset_info("complex")
            assert info is not None
            assert info.schema is not None
            assert "id" in info.schema
            assert "name" in info.schema
            assert "points" in info.schema
            assert "active" in info.schema
    
    def test_multiple_exports_same_dataset(self):
        """Test multiples exports du même dataset"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            catalog = DataCatalog(str(Path(tmpdir) / "catalog.db"))
            
            catalog.register_dataset("players", "parquet", "/data/players.parquet")
            
            # Multiple exports
            formats = ["csv", "parquet", "json"]
            for fmt in formats:
                catalog.register_export(
                    dataset="players",
                    format=fmt,
                    path=f"/exports/players.{fmt}"
                )
            
            history = catalog.get_export_history("players")
            assert len(history) == 3
            
            formats_in_history = [h["format"] for h in history]
            assert "csv" in formats_in_history
            assert "parquet" in formats_in_history
            assert "json" in formats_in_history


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
