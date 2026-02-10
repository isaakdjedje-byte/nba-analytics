"""Service layer for catalog and export endpoints."""

from pathlib import Path
from typing import Any, Optional

from nba.config import settings
from nba.reporting.catalog import DataCatalog
from nba.reporting.exporters import get_exporter


def list_datasets() -> list[Any]:
    catalog = DataCatalog()
    return catalog.list_datasets()


def get_dataset_info(dataset_name: str) -> Optional[Any]:
    catalog = DataCatalog()
    return catalog.get_dataset_info(dataset_name)


def export_dataset(dataset: str, fmt: str, partition_by: Optional[str] = None) -> dict[str, Any]:
    exporter = get_exporter(fmt)
    output_dir = Path(settings.data_exports)
    result_path = exporter.export(dataset=dataset, output_dir=output_dir, partition_by=partition_by)

    catalog = DataCatalog()
    catalog.register_export(
        dataset=dataset,
        format=fmt,
        path=result_path,
        metadata={"partition": partition_by},
    )

    return {
        "status": "success",
        "path": result_path,
        "dataset": dataset,
    }


def scan_catalog() -> dict[str, Any]:
    catalog = DataCatalog()
    count = catalog.scan_datasets(str(settings.data_gold))
    return {"status": "success", "datasets_found": count}
