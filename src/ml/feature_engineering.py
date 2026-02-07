"""
NBA-21: Feature Engineering pour Machine Learning

Crée les features finales pour l'entraînement des modèles ML.
"""

import logging
from typing import Dict, List, Optional
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, lag, avg, stddev, count, when, sum as spark_sum,
    row_number, max as spark_max, min as spark_min,
    datediff, current_date
)
from pyspark.sql.window import Window

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Crée les features pour les modèles ML.
    
    Features créées:
    - Globales: win%, classement, stats saison
    - Contexte: home/away, rest days, travel
    - Momentum: forme 5 derniers matchs
    - Matchup: historique H2H
    """
    
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("NBA-Feature-Engineering") \
            .getOrCreate()
    
    def create_features(self, games_df: DataFrame, players_df: Optional[DataFrame] = None) -> DataFrame:
        """
        Crée le dataset ML complet avec toutes les features.
        
        Args:
            games_df: DataFrame des matchs avec stats
            players_df: DataFrame des joueurs (optionnel)
            
        Returns:
            DataFrame avec features et target
        """
        logger.info("Création des features ML...")
        
        # 1. Features globales par équipe
        df = self._add_global_features(games_df)
        
        # 2. Features de contexte
        df = self._add_context_features(df)
        
        # 3. Features de momentum (forme récente)
        df = self._add_momentum_features(df)
        
        # 4. Features de matchup (H2H)
        df = self._add_matchup_features(df)
        
        # 5. Créer le target (winner)
        df = self._create_target(df)
        
        logger.info(f"Features créées: {len(df.columns)} colonnes")
        return df
    
    def _add_global_features(self, df: DataFrame) -> DataFrame:
        """Ajoute les features globales (win%, classement)."""
        logger.info("Ajout des features globales...")
        
        # Window par équipe et saison
        team_window = Window.partitionBy("team_id", "season").orderBy("game_date")
        
        # Win% cumulative
        df = df.withColumn(
            "wins_cumsum",
            spark_sum(when(col("is_winner") == 1, 1).otherwise(0)).over(team_window)
        )
        df = df.withColumn(
            "games_played",
            count("*").over(team_window)
        )
        df = df.withColumn("win_pct", col("wins_cumsum") / col("games_played"))
        
        # Points moyens par match
        df = df.withColumn(
            "avg_points_season",
            avg("points").over(Window.partitionBy("team_id", "season"))
        )
        
        return df
    
    def _add_context_features(self, df: DataFrame) -> DataFrame:
        """Ajoute les features de contexte (home/away, rest)."""
        logger.info("Ajout des features de contexte...")
        
        # Window pour calculer le dernier match
        team_window = Window.partitionBy("team_id").orderBy("game_date")
        
        # Jours depuis le dernier match (rest days)
        df = df.withColumn("last_game_date", lag("game_date").over(team_window))
        df = df.withColumn(
            "rest_days",
            when(col("last_game_date").isNotNull(),
                 datediff(col("game_date"), col("last_game_date")))
            .otherwise(7)  # Premier match de la saison = 7 jours de repos
        )
        
        # Back-to-back (0 jours de repos)
        df = df.withColumn("is_back_to_back", when(col("rest_days") <= 1, 1).otherwise(0))
        
        return df
    
    def _add_momentum_features(self, df: DataFrame) -> DataFrame:
        """Ajoute les features de momentum (forme sur 5 derniers matchs)."""
        logger.info("Ajout des features de momentum...")
        
        # Window des 5 derniers matchs
        last_5_window = Window.partitionBy("team_id").orderBy("game_date").rowsBetween(-4, 0)
        
        # Win% sur les 5 derniers matchs
        df = df.withColumn(
            "wins_last_5",
            spark_sum(when(col("is_winner") == 1, 1).otherwise(0)).over(last_5_window)
        )
        df = df.withColumn("win_pct_last_5", col("wins_last_5") / 5)
        
        # Points moyens sur les 5 derniers matchs
        df = df.withColumn("avg_points_last_5", avg("points").over(last_5_window))
        
        # Marge de victoire moyenne
        df = df.withColumn("avg_margin_last_5", avg("margin").over(last_5_window))
        
        return df
    
    def _add_matchup_features(self, df: DataFrame) -> DataFrame:
        """Ajoute les features de matchup (historique H2H)."""
        logger.info("Ajout des features de matchup...")
        
        # TODO: Implémenter l'historique H2H
        # Nécessite une jointure avec les matchs passés entre les deux équipes
        
        return df
    
    def _create_target(self, df: DataFrame) -> DataFrame:
        """Crée la variable target (winner)."""
        logger.info("Création de la target...")
        
        # Winner: 1 si l'équipe a gagné, 0 sinon
        df = df.withColumn("target", col("is_winner"))
        
        return df
    
    def save_features(self, df: DataFrame, output_path: str = "data/gold/ml_features"):
        """Sauvegarde le dataset ML."""
        logger.info(f"Sauvegarde des features: {output_path}")
        
        df.write \
            .mode("overwrite") \
            .parquet(output_path)
        
        logger.info("Features sauvegardées avec succès")


if __name__ == "__main__":
    # Exemple d'utilisation
    from pyspark.sql import SparkSession
    
    spark = SparkSession.builder.appName("Test").getOrCreate()
    
    # Créer un DataFrame de test
    test_data = [
        ("LAL", "2023-24", "2023-10-24", 1, 108, 8),
        ("LAL", "2023-24", "2023-10-26", 0, 100, -10),
        ("LAL", "2023-24", "2023-10-28", 1, 115, 15),
    ]
    
    df = spark.createDataFrame(test_data, 
        ["team_id", "season", "game_date", "is_winner", "points", "margin"])
    
    # Créer les features
    fe = FeatureEngineer()
    features_df = fe.create_features(df)
    
    features_df.show()
