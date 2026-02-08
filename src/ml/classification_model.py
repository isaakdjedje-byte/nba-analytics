"""
NBA-22: Modèle de Classification (Gagnant/Perdant)

Prédit le gagnant d'un match NBA avec PySpark ML.
"""

import logging
from typing import Dict, List, Tuple, Optional
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
    
    Objectif: Accuracy > 60%
    """
    
    def __init__(self, algorithm: str = 'rf'):
        """
        Initialise le modèle.
        
        Args:
            algorithm: 'rf' pour Random Forest, 'gbt' pour Gradient Boosting
        """
        self.algorithm = algorithm.lower()
        self.model = None
        self.pipeline = None
        self.metrics = {}
        self.feature_cols = []
        self.feature_importance = {}
        
    def train(self, train_df: DataFrame, feature_cols: List[str]) -> 'ClassificationModel':
        """
        Entraîne le modèle de classification.
        
        Args:
            train_df: DataFrame d'entraînement
            feature_cols: Liste des colonnes features
            
        Returns:
            self
        """
        self.feature_cols = feature_cols
        logger.info(f"Entraînement du modèle de classification ({self.algorithm.upper()})...")
        logger.info(f"Features utilisées: {len(feature_cols)}")
        
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
        
        # Classifier selon l'algorithme choisi
        if self.algorithm == 'rf':
            classifier = RandomForestClassifier(
                labelCol="target",
                featuresCol="scaled_features",
                numTrees=100,
                maxDepth=10,
                seed=42
            )
        elif self.algorithm == 'gbt':
            classifier = GBTClassifier(
                labelCol="target",
                featuresCol="scaled_features",
                maxIter=50,
                maxDepth=5,
                seed=42
            )
        else:
            raise ValueError(f"Algorithme inconnu: {self.algorithm}. Utiliser 'rf' ou 'gbt'")
        
        # Pipeline
        self.pipeline = Pipeline(stages=[assembler, scaler, classifier])
        
        # Entraînement
        self.model = self.pipeline.fit(train_df)
        
        # Extraire feature importance
        self._extract_feature_importance()
        
        logger.info(f"Modèle {self.algorithm.upper()} entraîné avec succès")
        return self
    
    def _extract_feature_importance(self):
        """Extrait l'importance des features du modèle entraîné."""
        try:
            # Récupérer le classifier depuis le pipeline
            classifier = self.model.stages[-1]
            
            if hasattr(classifier, 'featureImportances'):
                importances = classifier.featureImportances.toArray()
                self.feature_importance = {
                    feature: float(importance)
                    for feature, importance in zip(self.feature_cols, importances)
                }
                # Trier par importance
                self.feature_importance = dict(
                    sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)
                )
                logger.info(f"Top 5 features: {list(self.feature_importance.keys())[:5]}")
        except Exception as e:
            logger.warning(f"Impossible d'extraire feature importance: {e}")
    
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
