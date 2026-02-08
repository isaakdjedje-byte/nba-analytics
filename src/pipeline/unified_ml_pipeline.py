"""
Pipeline ML Unifié - Orchestration NBA-20 → NBA-21 → NBA-22

Connecte les composants existants:
- NBA-20: GamesTransformer (transformation matchs)
- NBA-21: FeatureEngineer (feature engineering - existant)
- NBA-22: ClassificationModel (modèle ML - existant)

Usage:
    pipeline = NBAMLPipeline()
    pipeline.run_full_pipeline()
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Optional

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.nba20_transform_games import GamesTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NBAMLPipeline:
    """
    Pipeline ML unifié NBA-20 → NBA-21 → NBA-22.
    
    Orchestre la transformation des matchs, le feature engineering
    et l'entraînement des modèles ML.
    
    Attributes:
        games_transformer: Instance de GamesTransformer (NBA-20)
        feature_engineer: Instance de FeatureEngineer (NBA-21)
        classifier: Instance de ClassificationModel (NBA-22)
    """
    
    def __init__(self):
        self.games_transformer = GamesTransformer()
        self.feature_engineer = None
        self.classifier = None
        self.stats = {}
    
    def run_full_pipeline(self, run_nba20: bool = True, 
                         run_nba21: bool = False,
                         run_nba22: bool = False) -> Dict:
        """
        Exécute le pipeline ML complet.
        
        Args:
            run_nba20: Exécuter la transformation des matchs
            run_nba21: Exécuter le feature engineering (nécessite PySpark)
            run_nba22: Entraîner le modèle ML (nécessite PySpark)
            
        Returns:
            Dict avec les statistiques de chaque étape
        """
        logger.info("=" * 70)
        logger.info("PIPELINE ML UNIFIÉ - NBA-20/21/22")
        logger.info("=" * 70)
        
        # Étape 1: NBA-20 - Transformation des matchs
        if run_nba20:
            self.stats['nba20'] = self._run_nba20()
        
        # Étape 2: NBA-21 - Feature Engineering
        if run_nba21:
            self.stats['nba21'] = self._run_nba21()
        
        # Étape 3: NBA-22 - Classification
        if run_nba22:
            self.stats['nba22'] = self._run_nba22()
        
        logger.info("=" * 70)
        logger.info("PIPELINE TERMINÉ")
        logger.info("=" * 70)
        
        return self.stats
    
    def _run_nba20(self) -> Dict:
        """Exécute NBA-20: Transformation des matchs."""
        logger.info("\n" + "=" * 70)
        logger.info("ÉTAPE 1: NBA-20 - Transformation des matchs")
        logger.info("=" * 70)
        
        try:
            stats = self.games_transformer.transform_all()
            logger.info("✅ NBA-20 terminé avec succès")
            return {
                'status': 'success',
                'games_transformed': stats.get('unique_games', 0),
                'home_win_rate': stats.get('home_win_rate', 0),
                'avg_margin': stats.get('avg_margin', 0)
            }
        except Exception as e:
            logger.error(f"❌ Erreur NBA-20: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _run_nba21(self) -> Dict:
        """Exécute NBA-21: Feature Engineering."""
        logger.info("\n" + "=" * 70)
        logger.info("ÉTAPE 2: NBA-21 - Feature Engineering")
        logger.info("=" * 70)
        
        try:
            from ml.feature_engineering import FeatureEngineer
            
            self.feature_engineer = FeatureEngineer()
            
            # Charger les matchs transformés
            import json
            games_file = Path("data/silver/games_processed/games_structured.json")
            
            if not games_file.exists():
                logger.error("Fichier games_structured.json non trouvé")
                return {'status': 'error', 'message': 'File not found'}
            
            with open(games_file) as f:
                games_data = json.load(f)
            
            # Convertir en DataFrame PySpark
            games_df = self._convert_to_spark_df(games_data['data'])
            
            # Créer les features
            features_df = self.feature_engineer.create_features(games_df)
            
            # Sauvegarder
            self.feature_engineer.save_features(features_df)
            
            logger.info("✅ NBA-21 terminé avec succès")
            return {
                'status': 'success',
                'features_created': len(features_df.columns),
                'records': features_df.count()
            }
            
        except ImportError as e:
            logger.warning(f"⚠️ PySpark non disponible: {e}")
            return {'status': 'skipped', 'message': 'PySpark not available'}
        except Exception as e:
            logger.error(f"❌ Erreur NBA-21: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _run_nba22(self) -> Dict:
        """Exécute NBA-22: Classification."""
        logger.info("\n" + "=" * 70)
        logger.info("ÉTAPE 3: NBA-22 - Modèle de Classification")
        logger.info("=" * 70)
        
        try:
            from ml.classification_model import ClassificationModel
            
            self.classifier = ClassificationModel()
            
            # Charger les features
            from pyspark.sql import SparkSession
            spark = SparkSession.builder.appName("NBA-22").getOrCreate()
            
            features_df = spark.read.parquet("data/gold/ml_features")
            
            # Split train/test
            train_df, test_df = features_df.randomSplit([0.8, 0.2], seed=42)
            
            # Définir les features
            feature_cols = [c for c in features_df.columns if c not in ['target', 'game_id']]
            
            # Entraîner
            self.classifier.train(train_df, feature_cols)
            
            # Évaluer
            metrics = self.classifier.evaluate(test_df)
            
            # Sauvegarder
            self.classifier.save("models/nba22_classifier")
            
            logger.info("✅ NBA-22 terminé avec succès")
            return {
                'status': 'success',
                'accuracy': metrics.get('accuracy', 0),
                'precision': metrics.get('precision', 0),
                'recall': metrics.get('recall', 0),
                'f1': metrics.get('f1', 0)
            }
            
        except ImportError as e:
            logger.warning(f"⚠️ PySpark ML non disponible: {e}")
            return {'status': 'skipped', 'message': 'PySpark ML not available'}
        except Exception as e:
            logger.error(f"❌ Erreur NBA-22: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _convert_to_spark_df(self, games_list: list):
        """Convertit une liste de dicts en DataFrame PySpark."""
        from pyspark.sql import SparkSession
        from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, DateType
        from pyspark.sql.functions import to_date
        
        spark = SparkSession.builder.appName("NBA-20").getOrCreate()
        
        # Créer le schéma
        schema = StructType([
            StructField("game_id", StringType(), True),
            StructField("season", StringType(), True),
            StructField("game_date", StringType(), True),
            StructField("team_id", IntegerType(), True),
            StructField("points", IntegerType(), True),
            StructField("is_winner", IntegerType(), True),
            StructField("margin", IntegerType(), True),
        ])
        
        # Convertir les données
        rows = []
        for game in games_list:
            # Créer 2 lignes par match (une pour chaque équipe)
            # Ligne home
            rows.append({
                'game_id': game['game_id'],
                'season': game['season'],
                'game_date': game['game_date'],
                'team_id': game['home_team_id'],
                'points': game['home_score'],
                'is_winner': 1 if game['winner'] == 'home' else 0,
                'margin': game['point_diff']
            })
            # Ligne away
            rows.append({
                'game_id': game['game_id'],
                'season': game['season'],
                'game_date': game['game_date'],
                'team_id': game['away_team_id'],
                'points': game['away_score'],
                'is_winner': 1 if game['winner'] == 'away' else 0,
                'margin': -game['point_diff']
            })
        
        df = spark.createDataFrame(rows, schema)
        df = df.withColumn("game_date", to_date(col("game_date")))
        
        return df


if __name__ == "__main__":
    # Exécution du pipeline
    pipeline = NBAMLPipeline()
    
    # Par défaut: exécuter uniquement NBA-20 (ne nécessite pas PySpark)
    stats = pipeline.run_full_pipeline(run_nba20=True, run_nba21=False, run_nba22=False)
    
    print("\n" + "=" * 70)
    print("RÉSULTATS DU PIPELINE")
    print("=" * 70)
    
    for step, result in stats.items():
        print(f"\n{step.upper()}:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    
    print("=" * 70)
