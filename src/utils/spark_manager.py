"""
Gestionnaire centralisé de sessions Spark.

Évite la duplication et garantit une seule session Spark.
"""

import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_spark_session(app_name: str = "NBA-Analytics", 
                      master: str = "local[*]") -> 'SparkSession':
    """
    Retourne une session Spark singleton avec Delta Lake.
    
    Usage:
        spark = get_spark_session("MonApp")
        df = spark.read.json("data.json")
    
    Args:
        app_name: Nom application Spark
        master: URL master (défaut: local[*])
        
    Returns:
        SparkSession configurée
    """
    try:
        from pyspark.sql import SparkSession
        
        spark = (SparkSession.builder
            .appName(app_name)
            .master(master)
            # Config Delta Lake
            .config("spark.sql.extensions", 
                   "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", 
                   "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            # Optimisations mémoire
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
            # Logs
            .config("spark.ui.showConsoleProgress", "false")
            .getOrCreate())
        
        logger.info(f"✅ Spark session créée: {app_name}")
        return spark
        
    except ImportError:
        logger.error("PySpark non installé")
        raise


def stop_spark_session():
    """Arrête la session Spark active."""
    try:
        from pyspark.sql import SparkSession
        
        spark = SparkSession.getActiveSession()
        if spark:
            spark.stop()
            get_spark_session.cache_clear()
            logger.info("✅ Spark session arrêtée")
    except Exception as e:
        logger.warning(f"Erreur arrêt Spark: {e}")


def get_or_create_spark(app_name: str = "NBA-Analytics") -> 'SparkSession':
    """Alias pour get_spark_session."""
    return get_spark_session(app_name)


class SparkSessionManager:
    """Gestionnaire contextuel de sessions Spark."""
    
    def __init__(self, app_name: str = "NBA-Analytics"):
        self.app_name = app_name
        self.spark = None
    
    def __enter__(self):
        self.spark = get_spark_session(self.app_name)
        return self.spark
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Ne pas arrêter la session (singleton)
        pass


if __name__ == "__main__":
    print("Test Spark Manager")
    
    # Test singleton
    spark1 = get_spark_session("Test1")
    spark2 = get_spark_session("Test2")
    
    print(f"Même session: {spark1 is spark2}")
    print(f"App name: {spark1.sparkContext.appName}")
    
    # Test context manager
    with SparkSessionManager("Test3") as spark:
        print(f"Context: {spark.sparkContext.appName}")
