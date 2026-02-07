"""
Couche Gold - Création de features et agrégations ML-ready.

Transforme les données Silver en features exploitables pour:
- Classification (gagnant/perdant)
- Régression (score exact)
- Clustering (profils joueurs)
"""

import logging
from pathlib import Path
from typing import Dict, List

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, when, lit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlayersGold:
    """
    Gestionnaire de la couche Gold.
    """
    
    GOLD_PATH = "data/gold/players_features"
    
    def __init__(self):
        """Initialise la session Spark."""
        self.spark = SparkSession.builder \
            .appName("NBA-Players-Gold") \
            .getOrCreate()
    
    def load_silver(self, silver_path: str = "data/silver/players_cleaned") -> DataFrame:
        """
        Charge les données depuis la couche Silver.
        
        Args:
            silver_path: Chemin Delta Lake Silver
            
        Returns:
            DataFrame Spark
        """
        df = self.spark.read.format("delta").load(silver_path)
        logger.info(f"Silver chargé: {df.count()} joueurs")
        return df
    
    def create_basic_features(self, df: DataFrame) -> DataFrame:
        """
        Crée les features de base pour ML.
        
        Args:
            df: DataFrame Silver
            
        Returns:
            DataFrame avec features
        """
        logger.info("Création features de base...")
        
        # BMI (Indice de Masse Corporelle)
        df = df.withColumn(
            "bmi",
            when(col("height_cm").isNotNull() & col("weight_kg").isNotNull(),
                 col("weight_kg") / ((col("height_cm") / 100) ** 2))
            .otherwise(lit(None))
        )
        
        # Catégorie taille
        df = df.withColumn(
            "size_category",
            when(col("height_cm") < 190, "Small")
            .when(col("height_cm") < 205, "Medium")
            .otherwise("Tall")
        )
        
        # Génération (basée sur from_year)
        df = df.withColumn(
            "generation",
            when(col("from_year") < 2000, "Vintage")
            .when(col("from_year") < 2010, "2000s")
            .when(col("from_year") < 2020, "2010s")
            .otherwise("Modern")
        )
        
        return df
    
    def create_ml_features(self, df: DataFrame) -> DataFrame:
        """
        Crée features spécifiques pour ML.
        
        Pour NBA-22 (à compléter avec données de matchs)
        """
        logger.info("Création features ML...")
        
        # Placeholder - sera enrichi avec les données de matchs
        df = df.withColumn("games_played", lit(None))
        df = df.withColumn("avg_points", lit(None))
        df = df.withColumn("avg_rebounds", lit(None))
        df = df.withColumn("avg_assists", lit(None))
        
        return df
    
    def save_gold(self, df: DataFrame) -> None:
        """
        Sauvegarde les données Gold.
        
        Args:
            df: DataFrame avec features
        """
        logger.info("Sauvegarde couche Gold...")
        
        output_path = Path(self.GOLD_PATH)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Supprimer anciennes données
        import shutil
        if output_path.exists():
            shutil.rmtree(output_path)
        
        # Sauvegarder
        df.write \
            .format("delta") \
            .mode("overwrite") \
            .partitionBy("position") \
            .save(str(output_path))
        
        logger.info(f"Gold sauvegardé: {output_path} ({df.count()} joueurs)")
    
    def run_gold_layer(self, silver_path: str = "data/silver/players_cleaned") -> DataFrame:
        """
        Exécute le pipeline Gold complet.
        
        Args:
            silver_path: Chemin vers Silver
            
        Returns:
            DataFrame Gold
        """
        logger.info("=" * 60)
        logger.info("COUCHE GOLD - Features et agrégations")
        logger.info("=" * 60)
        
        # 1. Charger Silver
        df = self.load_silver(silver_path)
        
        # 2. Créer features
        df = self.create_basic_features(df)
        df = self.create_ml_features(df)
        
        # 3. Sauvegarder
        self.save_gold(df)
        
        logger.info("✅ Couche Gold terminée")
        return df


if __name__ == "__main__":
    print("Test PlayersGold:")
    gold = PlayersGold()
    print(f"Spark version: {gold.spark.version}")
    print("Module prêt")
