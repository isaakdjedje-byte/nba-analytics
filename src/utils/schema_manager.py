#!/usr/bin/env python3
"""
Gestionnaire de schémas évolutifs pour Delta Lake - Fonctions pures
NBA-14: Schema Evolution Management

Pattern: Fonctions pures comme dans batch_ingestion_v2.py
Aucun objet JVM n'est stocké, tout passe par paramètres.
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
import yaml
from pyspark.sql import SparkSession, DataFrame
from delta.tables import DeltaTable

logger = logging.getLogger(__name__)


def get_active_spark() -> SparkSession:
    """Récupère la session Spark active ou lève une erreur"""
    spark = SparkSession.getActiveSession()
    if spark is None:
        raise RuntimeError("Aucune session Spark active. Créez-en une avant d'appeler ces fonctions.")
    return spark


def enable_auto_merge(spark: SparkSession = None):
    """Active le merge automatique des schémas au niveau Spark"""
    if spark is None:
        spark = get_active_spark()
    spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")
    logger.info("✅ Auto-merge activé")


def get_delta_table(delta_path: str, spark: SparkSession = None) -> DeltaTable:
    """Crée un objet DeltaTable à la volée (pas de stockage)"""
    if spark is None:
        spark = get_active_spark()
    return DeltaTable.forPath(spark, delta_path)


def get_current_schema(delta_path: str, spark: SparkSession = None) -> List[str]:
    """Récupère le schéma actuel du Delta Lake"""
    if spark is None:
        spark = get_active_spark()
    df = spark.read.format("delta").load(delta_path)
    return df.columns


def get_schema_history(delta_path: str, spark: SparkSession = None) -> DataFrame:
    """Récupère l'historique des versions du Delta Lake"""
    dt = get_delta_table(delta_path, spark)
    return dt.history()


def write_with_merge(df: DataFrame, delta_path: str, mode: str = "append"):
    """Écrit un DataFrame avec mergeSchema activé"""
    logger.info(f"💾 Écriture avec mergeSchema (mode={mode})")
    logger.info(f"   Colonnes: {df.columns}")
    
    # Vérifier si les colonnes de partitionnement existent
    has_season = "season" in df.columns
    has_game_year = "game_year" in df.columns
    
    writer = (df.write
        .format("delta")
        .option("mergeSchema", "true")
        .mode(mode)
    )
    
    # Partitionner seulement si les colonnes existent
    if has_season and has_game_year:
        writer = writer.partitionBy("season", "game_year")
        logger.info("   Partitionnement par season + game_year")
    elif has_season:
        writer = writer.partitionBy("season")
        logger.info("   Partitionnement par season")
    
    writer.save(delta_path)
    logger.info("✅ Écriture terminée")


def read_version(delta_path: str, version: int, spark: SparkSession = None) -> DataFrame:
    """Lit une version spécifique du Delta Lake (Time Travel)"""
    if spark is None:
        spark = get_active_spark()
    logger.info(f"📖 Lecture version {version}")
    return (spark.read
        .format("delta")
        .option("versionAsOf", version)
        .load(delta_path)
    )


def read_timestamp(delta_path: str, timestamp: str, spark: SparkSession = None) -> DataFrame:
    """Lit le Delta Lake à un timestamp spécifique"""
    if spark is None:
        spark = get_active_spark()
    return (spark.read
        .format("delta")
        .option("timestampAsOf", timestamp)
        .load(delta_path)
    )


def compare_versions(delta_path: str, v1: int, v2: int, spark: SparkSession = None) -> Dict:
    """Compare deux versions et retourne les différences"""
    df1 = read_version(delta_path, v1, spark)
    df2 = read_version(delta_path, v2, spark)
    
    cols1 = set(df1.columns)
    cols2 = set(df2.columns)
    
    return {
        "version_1": v1,
        "version_2": v2,
        "columns_v1": list(cols1),
        "columns_v2": list(cols2),
        "added": list(cols2 - cols1),
        "removed": list(cols1 - cols2),
        "common": list(cols1 & cols2),
        "record_count_v1": df1.count(),
        "record_count_v2": df2.count()
    }


def rollback_to_version(delta_path: str, version: int, spark: SparkSession = None) -> bool:
    """Rollback le Delta Lake à une version précédente"""
    try:
        logger.warning(f"⚠️  ROLLBACK vers version {version}")
        dt = get_delta_table(delta_path, spark)
        dt.restoreToVersion(version)
        logger.info(f"✅ Rollback vers version {version} réussi")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur rollback: {e}")
        return False


def get_version_count(delta_path: str, spark: SparkSession = None) -> int:
    """Retourne le nombre de versions dans l'historique"""
    history = get_schema_history(delta_path, spark)
    return history.count()


def validate_schema(delta_path: str, expected_columns: List[str], spark: SparkSession = None) -> bool:
    """Valide que le schéma actuel contient les colonnes attendues"""
    current = set(get_current_schema(delta_path, spark))
    expected = set(expected_columns)
    missing = expected - current
    
    if missing:
        logger.error(f"❌ Colonnes manquantes: {missing}")
        return False
    
    logger.info(f"✅ Schéma valide: {len(current)} colonnes")
    return True


# ============================================================
# SCHEMA EVOLUTION LOGGER (YAML)
# ============================================================

def load_schema_history(log_path: str = "docs/schema_evolution.log") -> Dict:
    """Charge l'historique des schémas depuis YAML"""
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            return yaml.safe_load(f) or {"schema_versions": []}
    return {"schema_versions": []}


def save_schema_history(history: Dict, log_path: str = "docs/schema_evolution.log"):
    """Sauvegarde l'historique dans YAML"""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as f:
        yaml.dump(history, f, default_flow_style=False, sort_keys=False)


def log_schema_version(version: int, columns: List[str], record_count: int,
                       changes: Dict = None, author: str = "NBA-14",
                       log_path: str = "docs/schema_evolution.log"):
    """Log une nouvelle version de schéma"""
    history = load_schema_history(log_path)
    
    entry = {
        "version": version,
        "date": datetime.now().isoformat(),
        "columns": columns,
        "nb_records": record_count,
        "author": author
    }
    
    if changes:
        entry["changes"] = changes
    
    history["schema_versions"].append(entry)
    save_schema_history(history, log_path)
    logger.info(f"📝 Version {version} loggée")


def get_schema_versions(log_path: str = "docs/schema_evolution.log") -> List[Dict]:
    """Retourne toutes les versions loggées"""
    history = load_schema_history(log_path)
    return history.get("schema_versions", [])


def get_latest_schema_version(log_path: str = "docs/schema_evolution.log") -> Optional[Dict]:
    """Retourne la dernière version loggée"""
    versions = get_schema_versions(log_path)
    return versions[-1] if versions else None
