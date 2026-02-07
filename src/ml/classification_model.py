"""
NBA-22-1: Modèle de Classification (Gagnant/Perdant)

Prédit le gagnant d'un match NBA avec PySpark ML.
"""

import logging
from typing import Dict, Tuple
from pyspark.sql import DataFrame
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.classification import RandomForestClassifier, GBTClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.ml import Pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClassificationModel:
    """
    Modèle de classification pour prédire le gagnant d'un match.
    
    Algorithmes:
    - Random Forest (baseline)
    - Gradient Boosting (optimisé)
    
    Objectif: Accuracy > 65%
    """
    
    def __init__(self):
        self.model = None
        self.pipeline = None
        self.metrics = {}
    
    def train(self, train_df: DataFrame, feature_cols: list) -> 'ClassificationModel':
        """
        Entraîne le modèle de classification.
        
        Args:
            train_df: DataFrame d'entraînement
            feature_cols: Liste des colonnes features
            
        Returns:
            self
        """
        logger.info("Entraînement du modèle de classification...")
        
        # Assembler les features
        assembler = VectorAssembler(
            inputCols=feature_cols,
            outputCol="features",
            handleInvalid="skip"
        )
        
        # Scaler
        scaler = StandardScaler(
            inputCol="features",
            outputCol="scaled_features"
        )
        
        # Classifier
        rf = RandomForestClassifier(
            labelCol="target",
            featuresCol="scaled_features",
            numTrees=100,
            maxDepth=10,
            seed=42
        )
        
        # Pipeline
        self.pipeline = Pipeline(stages=[assembler, scaler, rf])
        
        # Entraînement
        self.model = self.pipeline.fit(train_df)
        
        logger.info("Modèle entraîné avec succès")
        return self
    
    def evaluate(self, test_df: DataFrame) -> Dict[str, float]:
        """
        Évalue le modèle sur le test set.
        
        Returns:
            Dict avec les métriques (accuracy, precision, recall, f1, auc)
        """
        logger.info("Évaluation du modèle...")
        
        predictions = self.model.transform(test_df)
        
        # Métriques
        evaluators = {
            'accuracy': MulticlassClassificationEvaluator(
                labelCol="target", predictionCol="prediction", metricName="accuracy"
            ),
            'precision': MulticlassClassificationEvaluator(
                labelCol="target", predictionCol="prediction", metricName="weightedPrecision"
            ),
            'recall': MulticlassClassificationEvaluator(
                labelCol="target", predictionCol="prediction", metricName="weightedRecall"
            ),
            'f1': MulticlassClassificationEvaluator(
                labelCol="target", predictionCol="prediction", metricName="f1"
            ),
            'auc': BinaryClassificationEvaluator(
                labelCol="target", rawPredictionCol="rawPrediction", metricName="areaUnderROC"
            )
        }
        
        self.metrics = {name: evaluator.evaluate(predictions) 
                       for name, evaluator in evaluators.items()}
        
        logger.info(f"Métriques: {self.metrics}")
        return self.metrics
    
    def save(self, path: str = "models/classification_model"):
        """Sauvegarde le modèle."""
        logger.info(f"Sauvegarde du modèle: {path}")
        self.model.save(path)
        logger.info("Modèle sauvegardé")
    
    def load(self, path: str = "models/classification_model"):
        """Charge un modèle sauvegardé."""
        from pyspark.ml import PipelineModel
        logger.info(f"Chargement du modèle: {path}")
        self.model = PipelineModel.load(path)
        logger.info("Modèle chargé")
        return self
    
    def predict(self, df: DataFrame) -> DataFrame:
        """Fait des prédictions sur de nouvelles données."""
        return self.model.transform(df)


if __name__ == "__main__":
    # Exemple d'utilisation
    from pyspark.sql import SparkSession
    
    spark = SparkSession.builder.appName("Classification").getOrCreate()
    
    # Données de test
    data = [
        (1.0, 0.6, 105.0, 3.0, 1),
        (0.8, 0.4, 98.0, 2.0, 0),
        (0.9, 0.7, 110.0, 4.0, 1),
    ]
    
    df = spark.createDataFrame(data, ["win_pct", "win_pct_last_5", "avg_points", "rest_days", "target"])
    
    # Entraîner
    model = ClassificationModel()
    model.train(df, ["win_pct", "win_pct_last_5", "avg_points", "rest_days"])
    
    # Évaluer
    metrics = model.evaluate(df)
    print(f"Accuracy: {metrics['accuracy']:.3f}")
