"""
Couche Silver - Transformation et nettoyage des données joueurs.

Cette classe orchestre le pipeline de cleaning complet:
1. Chargement données Bronze
2. Nettoyage et conversion
3. Imputation si nécessaire
4. Validation qualité
5. Sauvegarde Delta Lake
"""

import logging
from pathlib import Path
from typing import Dict, List

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, BooleanType

from .cleaning_functions import clean_player_record, filter_complete_players, impute_missing_data
from .validators import SilverValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlayersSilver:
    """
    Gestionnaire de la couche Silver pour les données joueurs.
    """
    
    SILVER_PATH = "data/silver/players_cleaned"
    
    def __init__(self):
        """Initialise la session Spark et le validateur."""
        self.spark = self._init_spark()
        self.validator = SilverValidator()
    
    def _init_spark(self) -> SparkSession:
        """Initialise la session Spark avec Delta Lake."""
        try:
            from delta import configure_spark_with_delta_pip
            builder = SparkSession.builder \
                .appName("NBA-Players-Silver") \
                .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
                .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            return configure_spark_with_delta_pip(builder).getOrCreate()
        except ImportError:
            logger.warning("Delta Lake non installé, utilisation Spark standard")
            return SparkSession.builder.appName("NBA-Players-Silver").getOrCreate()
    
    def load_bronze(self, bronze_path: str = "data/bronze/players_bronze.json") -> List[Dict]:
        """
        Charge les données depuis la couche Bronze.
        
        Args:
            bronze_path: Chemin vers le fichier Bronze
            
        Returns:
            Liste des joueurs Bronze
        """
        import json
        
        with open(bronze_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        players = data['data']
        logger.info(f"Bronze chargé: {len(players)} joueurs")
        return players
    
    def clean_players(self, bronze_players: List[Dict]) -> List[Dict]:
        """
        Pipeline de nettoyage complet.
        
        Args:
            bronze_players: Liste des joueurs Bronze
            
        Returns:
            Liste des joueurs nettoyés (Silver)
        """
        logger.info("Nettoyage des données...")
        
        # Étape 1: Nettoyer chaque joueur
        cleaned = []
        for player in bronze_players:
            try:
                # Conversion des unités
                cleaned_player = clean_player_record(player)
                
                # Étape 2: Imputation des données manquantes
                cleaned_player = impute_missing_data(cleaned_player)
                
                cleaned.append(cleaned_player)
            except Exception as e:
                logger.warning(f"Erreur nettoyage joueur {player.get('id')}: {e}")
                continue
        
        logger.info(f"{len(cleaned)} joueurs nettoyés (avec imputation)")
        return cleaned
    
    def validate_silver(self, players: List[Dict]) -> bool:
        """
        Valide les données Silver.
        
        Args:
            players: Liste des joueurs à valider
            
        Returns:
            True si validation OK
        """
        return self.validator.validate(players)
    
    def save_silver(self, players: List[Dict]) -> None:
        """
        Sauvegarde les données en Delta Lake.
        
        Args:
            players: Liste des joueurs à sauvegarder
        """
        logger.info("Sauvegarde couche Silver...")
        
        # Définir le schéma explicite
        schema = StructType([
            StructField("id", IntegerType(), True),
            StructField("full_name", StringType(), True),
            StructField("first_name", StringType(), True),
            StructField("last_name", StringType(), True),
            StructField("is_active", BooleanType(), True),
            StructField("height_cm", IntegerType(), True),
            StructField("weight_kg", IntegerType(), True),
            StructField("position", StringType(), True),
            StructField("birth_date", StringType(), True),
            StructField("age", IntegerType(), True),
            StructField("from_year", IntegerType(), True),
            StructField("to_year", IntegerType(), True),
            StructField("data_source", StringType(), True),
        ])
        
        # Créer DataFrame
        df = self.spark.createDataFrame(players, schema)
        
        # Créer répertoire
        output_path = Path(self.SILVER_PATH)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Supprimer anciennes données
        import shutil
        if output_path.exists():
            shutil.rmtree(output_path)
        
        # Sauvegarder partitionné
        df.write \
            .format("delta") \
            .mode("overwrite") \
            .partitionBy("is_active", "position") \
            .save(str(output_path))
        
        logger.info(f"Silver sauvegardé: {output_path} ({len(players)} joueurs)")
    
    def generate_report(self, players: List[Dict]) -> Dict:
        """
        Génère un rapport de qualité.
        
        Args:
            players: Liste des joueurs
            
        Returns:
            Dict avec statistiques
        """
        from datetime import datetime
        
        # Compter par source
        sources = {}
        for p in players:
            source = p.get('data_source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_players': len(players),
            'validation_stats': self.validator.get_stats(),
            'sources': sources,
            'output_path': self.SILVER_PATH
        }
        
        # Sauvegarder rapport
        import json
        report_path = Path(self.SILVER_PATH).parent / "players_cleaned_stats.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Rapport généré: {report_path}")
        return report
    
    def run_silver_layer(self, bronze_path: str = "data/bronze/players_bronze.json") -> List[Dict]:
        """
        Exécute le pipeline Silver complet.
        
        Args:
            bronze_path: Chemin vers les données Bronze
            
        Returns:
            Liste des joueurs Silver
        """
        logger.info("=" * 60)
        logger.info("COUCHE SILVER - Transformation et nettoyage")
        logger.info("=" * 60)
        
        # 1. Charger Bronze
        bronze_players = self.load_bronze(bronze_path)
        
        # 2. Nettoyer
        silver_players = self.clean_players(bronze_players)
        
        # 3. Filtrer joueurs complets
        silver_players = filter_complete_players(silver_players, min_fields=8)
        
        # 4. Valider
        if not self.validate_silver(silver_players):
            raise ValueError("Validation Silver échouée")
        
        # 5. Sauvegarder
        self.save_silver(silver_players)
        
        # 6. Rapport
        self.generate_report(silver_players)
        
        logger.info("✅ Couche Silver terminée")
        return silver_players


if __name__ == "__main__":
    print("Test PlayersSilver:")
    silver = PlayersSilver()
    print(f"Spark version: {silver.spark.version}")
    print("Module prêt")
