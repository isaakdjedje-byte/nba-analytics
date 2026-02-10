"""
Exporters NBA-29 pour BI
Supporte Parquet, CSV, JSON, Delta
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Any
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


class BaseExporter(ABC):
    """Interface abstraite pour les exporters"""
    
    def __init__(self, format_name: str, gold_path: Optional[Path] = None):
        self.format_name = format_name
        self.gold_path = gold_path or Path("data/gold")
    
    @abstractmethod
    def export(
        self,
        dataset: str,
        output_dir: Path,
        partition_by: Optional[str] = None,
        compression: Optional[str] = None,
        **kwargs
    ) -> str:
        """Exporte un dataset et retourne le chemin"""
        pass
    
    def _load_dataset(self, dataset: str) -> pd.DataFrame:
        """Charge un dataset depuis gold_path"""
        gold_path = self.gold_path
        
        # Cherche le fichier
        possible_paths = [
            gold_path / f"{dataset}.parquet",
            gold_path / f"{dataset}.json",
            gold_path / dataset / f"{dataset}.parquet",
            gold_path / "ml_features" / f"{dataset}.parquet",
            gold_path / "player_team_season" / f"{dataset}.parquet",
        ]
        
        for path in possible_paths:
            if path.exists():
                if path.suffix == ".parquet":
                    return pd.read_parquet(path)
                elif path.suffix == ".json":
                    return pd.read_json(path)
        
        # Fallback: chercher dans les sous-répertoires
        for json_file in gold_path.rglob(f"{dataset}.json"):
            return pd.read_json(json_file)
        
        raise FileNotFoundError(f"Dataset {dataset} non trouvé dans {gold_path}")


class ParquetExporter(BaseExporter):
    """Exporteur Parquet professionnel"""
    
    def __init__(self, gold_path=None):
        super().__init__("parquet", gold_path)
    
    def export(
        self,
        dataset: str,
        output_dir: Path,
        partition_by: Optional[str] = None,
        compression: str = "snappy",
        **kwargs
    ) -> str:
        """Exporte en Parquet avec partitionnement optionnel"""
        df = self._load_dataset(dataset)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{dataset}.parquet"
        
        if partition_by and partition_by in df.columns:
            # Partitionné
            base_path = output_dir / dataset
            base_path.mkdir(parents=True, exist_ok=True)
            
            for partition_value, group_df in df.groupby(partition_by):
                partition_dir = base_path / f"{partition_by}={partition_value}"
                partition_dir.mkdir(parents=True, exist_ok=True)
                
                partition_file = partition_dir / f"part-0.parquet"
                group_df.to_parquet(
                    partition_file,
                    compression=compression,
                    index=False
                )
            
            return str(base_path)
        else:
            # Non partitionné
            df.to_parquet(
                output_path,
                compression=compression,
                index=False
            )
            return str(output_path)


class CSVExporter(BaseExporter):
    """Exporteur CSV pour compatibilite"""
    
    def __init__(self, gold_path=None):
        super().__init__("csv", gold_path)
    
    def export(
        self,
        dataset: str,
        output_dir: Path,
        partition_by: Optional[str] = None,
        compression: Optional[str] = None,
        **kwargs
    ) -> str:
        """Exporte en CSV avec headers"""
        df = self._load_dataset(dataset)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{dataset}.csv"
        
        if partition_by and partition_by in df.columns:
            # Partitionné
            base_path = output_dir / dataset
            base_path.mkdir(parents=True, exist_ok=True)
            
            for partition_value, group_df in df.groupby(partition_by):
                partition_file = base_path / f"{dataset}_{partition_by}_{partition_value}.csv"
                group_df.to_csv(partition_file, index=False, encoding="utf-8")
            
            return str(base_path)
        else:
            # Non partitionné
            df.to_csv(output_path, index=False, encoding="utf-8")
            return str(output_path)


class JSONExporter(BaseExporter):
    """Exporteur JSON pour APIs"""
    
    def __init__(self, gold_path=None):
        super().__init__("json", gold_path)
    
    def export(
        self,
        dataset: str,
        output_dir: Path,
        partition_by: Optional[str] = None,
        compression: Optional[str] = None,
        orient: str = "records",
        **kwargs
    ) -> str:
        """Exporte en JSON"""
        df = self._load_dataset(dataset)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{dataset}.json"
        
        # Conversion types pour JSON
        df_export = df.copy()
        for col in df_export.columns:
            if pd.api.types.is_datetime64_any_dtype(df_export[col]):
                df_export[col] = df_export[col].astype(str)
        
        df_export.to_json(output_path, orient=orient, indent=2, force_ascii=False)
        return str(output_path)


class DeltaExporter(BaseExporter):
    """Exporteur Delta Lake (si disponible)"""
    
    def __init__(self, gold_path=None):
        super().__init__("delta", gold_path)
        self.has_delta = self._check_delta()
    
    def _check_delta(self) -> bool:
        """Vérifie si delta-spark est disponible"""
        try:
            import deltalake
            return True
        except ImportError:
            return False
    
    def export(
        self,
        dataset: str,
        output_dir: Path,
        partition_by: Optional[str] = None,
        compression: Optional[str] = None,
        **kwargs
    ) -> str:
        """Exporte en Delta Lake"""
        if not self.has_delta:
            raise ImportError("delta-spark non installé. Utilisez Parquet à la place.")
        
        from deltalake import write_deltalake
        
        df = self._load_dataset(dataset)
        output_path = output_dir / f"{dataset}_delta"
        output_path.mkdir(parents=True, exist_ok=True)
        
        partition_cols = [partition_by] if partition_by else None
        
        write_deltalake(
            str(output_path),
            df,
            partition_by=partition_cols,
            mode="overwrite"
        )
        
        return str(output_path)


def get_exporter(format: str, gold_path: Optional[Path] = None) -> BaseExporter:
    """Factory pour créer le bon exporteur"""
    exporters = {
        "parquet": ParquetExporter,
        "csv": CSVExporter,
        "json": JSONExporter,
        "delta": DeltaExporter,
    }
    
    format = format.lower()
    if format not in exporters:
        raise ValueError(f"Format non supporté: {format}. Disponibles: {list(exporters.keys())}")
    
    return exporters[format](gold_path=gold_path)


def export_dataset(
    dataset: str,
    format: str = "parquet",
    output_dir: Optional[Path] = None,
    partition_by: Optional[str] = None,
    compression: Optional[str] = None,
    validate: bool = True
) -> Dict[str, Any]:
    """
    Fonction utilitaire pour exporter un dataset
    
    Returns:
        Dict avec path, format, record_count, etc.
    """
    output_dir = output_dir or Path("data/exports")
    
    exporter = get_exporter(format)
    path = exporter.export(
        dataset=dataset,
        output_dir=output_dir,
        partition_by=partition_by,
        compression=compression
    )
    
    # Validation basique
    record_count = 0
    if validate:
        try:
            if format == "parquet":
                df_check = pd.read_parquet(path)
                record_count = len(df_check)
            elif format == "csv":
                df_check = pd.read_csv(path)
                record_count = len(df_check)
        except:
            pass
    
    return {
        "dataset": dataset,
        "format": format,
        "path": path,
        "partition_by": partition_by,
    }

