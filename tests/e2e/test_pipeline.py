"""
Tests End-to-End - Pipeline complet NBA-29
Test le workflow complet: Catalog → Export → API
"""

import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nba.reporting.catalog import DataCatalog
from nba.reporting.exporters import get_exporter


class TestFullExportWorkflow:
    """Tests workflow export complet"""
    
    def test_full_export_workflow(self):
        """Test workflow complet: création → catalog → export"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            # 1. Crée données de test
            gold_path = Path(tmpdir) / "gold"
            gold_path.mkdir(parents=True, exist_ok=True)
            
            df = pd.DataFrame({
                "id": range(100),
                "name": [f"Player_{i}" for i in range(100)],
                "team": ["Lakers", "Warriors", "Celtics"] * 33 + ["Heat"],
                "points": [20.5] * 100,
                "season": ["2023-24"] * 100
            })
            df.to_parquet(gold_path / "players.parquet")
            
            # 2. Scan dans catalog
            catalog = DataCatalog(str(Path(tmpdir) / "catalog.db"))
            count = catalog.scan_datasets(str(gold_path))
            assert count == 1
            
            # 3. Export en Parquet
            exporter = get_exporter("parquet", gold_path=gold_path)
            export_dir = Path(tmpdir) / "exports"
            result = exporter.export("players", export_dir)
            
            assert Path(result).exists()
            
            # 4. Vérifie le fichier exporté
            df_exported = pd.read_parquet(result)
            assert len(df_exported) == 100
            
            # 5. Met à jour le catalog
            catalog.register_export(
                dataset="players",
                format="parquet",
                path=result,
                metadata={"record_count": 100}
            )
            
            # 6. Vérifie historique
            history = catalog.get_export_history("players")
            assert len(history) == 1
    
    def test_multi_format_export(self):
        """Test export dans plusieurs formats"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            # Crée dataset
            gold_path = Path(tmpdir) / "gold"
            gold_path.mkdir(parents=True, exist_ok=True)
            
            df = pd.DataFrame({
                "id": [1, 2, 3],
                "name": ["LeBron", "Curry", "Durant"]
            })
            df.to_parquet(gold_path / "stars.parquet")
            
            catalog = DataCatalog(str(Path(tmpdir) / "catalog.db"))
            catalog.scan_datasets(str(gold_path))
            
            export_dir = Path(tmpdir) / "exports"
            
            # Exporte dans tous les formats
            for fmt in ["parquet", "csv", "json"]:
                exporter = get_exporter(fmt, gold_path=gold_path)
                result = exporter.export("stars", export_dir / fmt)
                
                assert Path(result).exists()
                
                catalog.register_export(
                    dataset="stars",
                    format=fmt,
                    path=result
                )
            
            # Vérifie historique
            history = catalog.get_export_history("stars")
            assert len(history) == 3
    
    def test_partitioned_export_e2e(self):
        """Test export partitionné end-to-end"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            # Crée dataset avec partitionnement
            gold_path = Path(tmpdir) / "gold"
            gold_path.mkdir(parents=True, exist_ok=True)
            
            df = pd.DataFrame({
                "id": range(100),
                "season": ["2022-23"] * 50 + ["2023-24"] * 50
            })
            df.to_parquet(gold_path / "season_data.parquet")
            
            # Export partitionné
            exporter = get_exporter("parquet", gold_path=gold_path)
            result = exporter.export(
                dataset="season_data",
                output_dir=Path(tmpdir) / "exports",
                partition_by="season"
            )
            
            # Vérifie partitions
            partition_base = Path(result)
            assert (partition_base / "season=2022-23").exists()
            assert (partition_base / "season=2023-24").exists()
            
            # Vérifie données
            df_2022 = pd.read_parquet(partition_base / "season=2022-23" / "part-0.parquet")
            assert len(df_2022) == 50


class TestCatalogToExportFlow:
    """Tests flux catalog vers export"""
    
    def test_catalog_to_export_flow(self):
        """Test flux complet catalog → export"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            # Setup
            gold_path = Path(tmpdir) / "gold"
            gold_path.mkdir(parents=True, exist_ok=True)
            
            # Crée plusieurs datasets
            for name in ["players", "teams"]:
                df = pd.DataFrame({
                    "id": range(10),
                    "name": [f"{name}_{i}" for i in range(10)]
                })
                df.to_parquet(gold_path / f"{name}.parquet")
            
            # Scan
            catalog = DataCatalog(str(Path(tmpdir) / "catalog.db"))
            catalog.scan_datasets(str(gold_path))
            
            datasets = catalog.list_datasets()
            assert len(datasets) == 2
            
            # Exporte tous
            for dataset_info in datasets:
                exporter = get_exporter("csv", gold_path=gold_path)
                result = exporter.export(
                    dataset_info.name,
                    Path(tmpdir) / "exports"
                )
                
                assert Path(result).exists()
                
                catalog.register_export(
                    dataset=dataset_info.name,
                    format="csv",
                    path=result
                )
    
    def test_incremental_export(self):
        """Test export incrémental"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            gold_path = Path(tmpdir) / "gold"
            gold_path.mkdir(parents=True, exist_ok=True)
            
            # Dataset initial
            df = pd.DataFrame({"id": [1, 2]})
            df.to_parquet(gold_path / "incremental.parquet")
            
            catalog = DataCatalog(str(Path(tmpdir) / "catalog.db"))
            catalog.scan_datasets(str(gold_path))
            
            # Premier export
            exporter = get_exporter("parquet", gold_path=gold_path)
            result1 = exporter.export("incremental", Path(tmpdir) / "exports")
            catalog.register_export("incremental", "parquet", result1)
            
            # Mise à jour dataset
            df = pd.DataFrame({"id": [1, 2, 3, 4]})
            df.to_parquet(gold_path / "incremental.parquet")
            catalog.scan_datasets(str(gold_path))
            
            # Nouvel export
            result2 = exporter.export("incremental", Path(tmpdir) / "exports_v2")
            catalog.register_export("incremental", "parquet", result2)
            
            # Vérifie historique
            history = catalog.get_export_history("incremental")
            assert len(history) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
