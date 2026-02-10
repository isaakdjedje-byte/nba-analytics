"""
Data Catalog léger avec SQLite
Pas besoin de DataHub complexe - zero budget pro
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd


@dataclass
class DatasetInfo:
    """Informations sur un dataset"""
    name: str
    format: str
    path: str
    record_count: int = 0
    size_bytes: int = 0
    last_updated: Optional[datetime] = None
    schema: Optional[Dict] = None
    metadata: Optional[Dict] = None


class DataCatalog:
    """
    Catalogue de données léger avec SQLite
    Remplace DataHub/Amundsen (trop lourd) pour zero budget
    """
    
    def __init__(self, db_path: str = "data/catalog.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialise le schéma SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    format TEXT NOT NULL,
                    path TEXT NOT NULL,
                    record_count INTEGER DEFAULT 0,
                    size_bytes INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    schema_json TEXT,
                    metadata_json TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS exports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_name TEXT NOT NULL,
                    format TEXT NOT NULL,
                    export_path TEXT NOT NULL,
                    exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT,
                    FOREIGN KEY (dataset_name) REFERENCES datasets(name)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_datasets_name ON datasets(name)
            """)
            conn.commit()
    
    def register_dataset(
        self,
        name: str,
        format: str,
        path: str,
        record_count: int = 0,
        size_bytes: int = 0,
        schema: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Enregistre ou met à jour un dataset"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO datasets 
                    (name, format, path, record_count, size_bytes, schema_json, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        format=excluded.format,
                        path=excluded.path,
                        record_count=excluded.record_count,
                        size_bytes=excluded.size_bytes,
                        updated_at=CURRENT_TIMESTAMP,
                        schema_json=excluded.schema_json,
                        metadata_json=excluded.metadata_json
                """, (
                    name, format, path, record_count, size_bytes,
                    json.dumps(schema) if schema else None,
                    json.dumps(metadata) if metadata else None
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Erreur registration: {e}")
            return False
    
    def register_export(
        self,
        dataset: str,
        format: str,
        path: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Enregistre un export"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO exports (dataset_name, format, export_path, metadata_json)
                    VALUES (?, ?, ?, ?)
                """, (dataset, format, path, json.dumps(metadata) if metadata else None))
                conn.commit()
                return True
        except Exception as e:
            print(f"Erreur export registration: {e}")
            return False
    
    def list_datasets(self) -> List[DatasetInfo]:
        """Liste tous les datasets"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM datasets ORDER BY updated_at DESC
            """).fetchall()
            
            return [
                DatasetInfo(
                    name=row["name"],
                    format=row["format"],
                    path=row["path"],
                    record_count=row["record_count"],
                    size_bytes=row["size_bytes"],
                    last_updated=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
                    schema=json.loads(row["schema_json"]) if row["schema_json"] else None,
                    metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else None
                )
                for row in rows
            ]
    
    def get_dataset_info(self, name: str) -> Optional[DatasetInfo]:
        """Récupère les infos d'un dataset"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM datasets WHERE name = ?", (name,)
            ).fetchone()
            
            if not row:
                return None
            
            return DatasetInfo(
                name=row["name"],
                format=row["format"],
                path=row["path"],
                record_count=row["record_count"],
                size_bytes=row["size_bytes"],
                last_updated=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
                schema=json.loads(row["schema_json"]) if row["schema_json"] else None,
                metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else None
            )
    
    def scan_datasets(self, gold_path: str) -> int:
        """
        Scan automatique des datasets dans data/gold/
        Retourne le nombre de datasets trouvés
        """
        gold_dir = Path(gold_path)
        if not gold_dir.exists():
            return 0
        
        count = 0
        
        # Scan des fichiers parquet
        for parquet_file in gold_dir.rglob("*.parquet"):
            try:
                df = pd.read_parquet(parquet_file)
                name = parquet_file.stem
                
                self.register_dataset(
                    name=name,
                    format="parquet",
                    path=str(parquet_file),
                    record_count=len(df),
                    size_bytes=parquet_file.stat().st_size,
                    schema={col: str(dtype) for col, dtype in df.dtypes.items()},
                    metadata={"columns": len(df.columns)}
                )
                count += 1
            except Exception as e:
                print(f"Erreur scan {parquet_file}: {e}")
        
        # Scan des fichiers JSON
        for json_file in gold_dir.rglob("*.json"):
            if json_file.stat().st_size > 1000000:  # Skip petits fichiers
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                        
                    name = json_file.stem
                    record_count = len(data) if isinstance(data, list) else 1
                    
                    self.register_dataset(
                        name=name,
                        format="json",
                        path=str(json_file),
                        record_count=record_count,
                        size_bytes=json_file.stat().st_size,
                        metadata={"type": "json"}
                    )
                    count += 1
                except Exception as e:
                    print(f"Erreur scan {json_file}: {e}")
        
        return count
    
    def get_export_history(self, dataset_name: str) -> List[Dict]:
        """Historique des exports d'un dataset"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM exports 
                WHERE dataset_name = ? 
                ORDER BY exported_at DESC
            """, (dataset_name,)).fetchall()
            
            return [
                {
                    "format": row["format"],
                    "path": row["export_path"],
                    "exported_at": row["exported_at"],
                    "metadata": json.loads(row["metadata_json"]) if row["metadata_json"] else None
                }
                for row in rows
            ]
