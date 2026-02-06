#!/usr/bin/env python3
"""
Pipeline Spark Streaming pour Box Score NBA
Consomme le stream du simulateur et stocke dans Delta Lake
"""
import os
import sys
import time
import logging
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, current_timestamp, window, avg, max, min,
    when, abs as spark_abs, lit, struct, to_json, expr
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    DoubleType, BooleanType, TimestampType
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CHECKPOINT_BASE = "data/checkpoints"
OUTPUT_PATH = "data/silver/live_games"
INPUT_PATH = "data/streaming/input"
BATCH_INTERVAL = "30 seconds"

# Schéma des données Box Score
BOX_SCORE_SCHEMA = StructType([
    StructField("game_id", StringType(), True),
    StructField("team_id", IntegerType(), True),
    StructField("team_abbr", StringType(), True),
    StructField("matchup", StringType(), True),
    StructField("game_date", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("period", IntegerType(), True),
    StructField("time_remaining", StringType(), True),
    StructField("progress_pct", DoubleType(), True),
    StructField("is_final", BooleanType(), True),
    StructField("stats", StructType([
        StructField("score", IntegerType(), True),
        StructField("fgm", IntegerType(), True),
        StructField("fga", IntegerType(), True),
        StructField("fg_pct", DoubleType(), True),
        StructField("fg3m", IntegerType(), True),
        StructField("fg3a", IntegerType(), True),
        StructField("fg3_pct", DoubleType(), True),
        StructField("ftm", IntegerType(), True),
        StructField("fta", IntegerType(), True),
        StructField("ft_pct", DoubleType(), True),
        StructField("reb", IntegerType(), True),
        StructField("ast", IntegerType(), True),
        StructField("stl", IntegerType(), True),
        StructField("blk", IntegerType(), True)
    ]), True)
])


def create_spark_session(checkpoint_location: str) -> SparkSession:
    """Crée une session Spark configurée pour le streaming avec Delta Lake"""
    logger.info("🔧 Initialisation Spark Streaming...")
    
    spark = (SparkSession.builder
        .appName("NBA-13-Streaming-BoxScore")
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.streaming.checkpointLocation", checkpoint_location)
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.streaming.metricsEnabled", "true")
        .getOrCreate()
    )
    
    spark.sparkContext.setLogLevel("WARN")
    logger.info(f"✅ Spark {spark.version} initialisé")
    return spark


def wait_for_simulator(timeout: int = 900):
    """Attend que le simulateur crée un dossier et écrive tous les fichiers"""
    logger.info(f"⏳ Attente du simulateur (timeout: {timeout}s = {timeout//60} minutes)...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Chercher les dossiers run_*
        if os.path.exists(INPUT_PATH):
            run_dirs = [d for d in os.listdir(INPUT_PATH) if d.startswith('run_')]
            
            if run_dirs:
                # Prendre le dernier dossier créé
                run_dirs.sort()
                latest_dir = os.path.join(INPUT_PATH, run_dirs[-1])
                complete_file = os.path.join(latest_dir, 'COMPLETE')
                
                # Vérifier si le fichier COMPLETE existe
                if os.path.exists(complete_file):
                    logger.info(f"✅ Simulateur prêt dans: {latest_dir}")
                    return latest_dir
                else:
                    # Compter les fichiers JSON présents
                    json_files = [f for f in os.listdir(latest_dir) if f.endswith('.json')]
                    logger.info(f"⏳ {len(json_files)} fichiers détectés, attente complétion...")
        
        time.sleep(5)
    
    logger.error(f"❌ Timeout après {timeout}s - simulateur non détecté")
    return None


def create_streaming_query(spark: SparkSession, input_path: str):
    """Crée la requête de streaming"""
    logger.info(f"📡 Lecture des fichiers depuis {input_path}")
    
    # Lire le stream depuis les fichiers JSON du dossier spécifique
    parsed = (spark
        .readStream
        .schema(BOX_SCORE_SCHEMA)
        .json(input_path)
    )
    
    # Transformations temps réel
    transformed = (parsed
        # Timestamp de traitement
        .withColumn("processing_time", current_timestamp())
        
        # Extraire les stats dans des colonnes plates
        .withColumn("score", col("stats.score"))
        .withColumn("fgm", col("stats.fgm"))
        .withColumn("fga", col("stats.fga"))
        .withColumn("fg_pct", col("stats.fg_pct"))
        .withColumn("fg3m", col("stats.fg3m"))
        .withColumn("fg3a", col("stats.fg3a"))
        .withColumn("fg3_pct", col("stats.fg3_pct"))
        .withColumn("ftm", col("stats.ftm"))
        .withColumn("fta", col("stats.fta"))
        .withColumn("ft_pct", col("stats.ft_pct"))
        .withColumn("reb", col("stats.reb"))
        .withColumn("ast", col("stats.ast"))
        .withColumn("stl", col("stats.stl"))
        .withColumn("blk", col("stats.blk"))
        
        # Calculs dérivés
        .withColumn("total_shots", col("fga") + col("fg3a"))
        .withColumn("efficiency", 
            when(col("fga") > 0, col("score") / col("fga")).otherwise(0)
        )
        .withColumn("shooting_quality",
            when(col("fg_pct") >= 50, "Excellent")
            .when(col("fg_pct") >= 45, "Good")
            .when(col("fg_pct") >= 40, "Average")
            .otherwise("Poor")
        )
        
        # Sélection finale
        .select(
            "game_id",
            "team_id",
            "team_abbr",
            "matchup",
            "game_date",
            "period",
            "time_remaining",
            "progress_pct",
            "is_final",
            "score",
            "fgm", "fga", "fg_pct",
            "fg3m", "fg3a", "fg3_pct",
            "ftm", "fta", "ft_pct",
            "reb", "ast", "stl", "blk",
            "total_shots",
            "efficiency",
            "shooting_quality",
            "processing_time"
        )
    )
    
    return transformed


def start_streaming(spark: SparkSession, df_transformed, input_path: str, checkpoint_location: str):
    """Démarre le stream vers Delta Lake"""
    logger.info(f"💾 Configuration stockage Delta: {OUTPUT_PATH}")
    logger.info(f"📁 Input: {input_path}")
    logger.info(f"📝 Checkpoint: {checkpoint_location}")
    
    # S'assurer que les répertoires existent
    os.makedirs(input_path, exist_ok=True)
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    os.makedirs(checkpoint_location, exist_ok=True)
    
    # Écrire dans Delta Lake en mode append
    query = (df_transformed
        .writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", checkpoint_location)
        .option("mergeSchema", "true")
        .trigger(processingTime=BATCH_INTERVAL)
        .start(OUTPUT_PATH)
    )
    
    logger.info(f"🚀 Stream démarré (ID: {query.id})")
    logger.info(f"⏱️  Intervalle: {BATCH_INTERVAL}")
    logger.info("📊 En attente de données...")
    
    return query


def monitor_stream(query, duration_seconds: int = 120):
    """Monitor le stream pendant une durée donnée"""
    logger.info(f"⏱️  Monitoring pendant {duration_seconds}s minimum...")
    logger.info("⏹️  Appuyez sur Ctrl+C pour arrêter")
    
    start_time = datetime.now()
    
    try:
        # Attendre la durée minimale
        while (datetime.now() - start_time).total_seconds() < duration_seconds:
            time.sleep(5)
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"⏱️  {elapsed:.0f}s écoulés... (status: {query.status['message']})")
            
        logger.info(f"✅ Durée minimale de {duration_seconds}s atteinte!")
        logger.info("🛑 Arrêt du stream...")
        
    except KeyboardInterrupt:
        logger.info("⏹️  Interrompu par l'utilisateur")
    finally:
        query.stop()
        logger.info("✅ Stream arrêté")


def verify_results(spark: SparkSession):
    """Vérifie les résultats du streaming"""
    logger.info("🔍 Vérification des données...")
    
    try:
        df = spark.read.format("delta").load(OUTPUT_PATH)
        count = df.count()
        
        logger.info(f"📊 Total événements reçus: {count}")
        
        if count > 0:
            logger.info("📋 Aperçu des données:")
            df.select(
                "game_id", "team_abbr", "period", 
                "time_remaining", "score", "processing_time"
            ).show(10, truncate=False)
            
            logger.info("📈 Statistiques globales:")
            df.groupBy("game_id").count().show()
            
            return True
        else:
            logger.warning("⚠️  Aucune donnée reçue!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur vérification: {e}")
        return False


def main():
    """Orchestration complète du streaming"""
    logger.info("="*70)
    logger.info("🏀 NBA-13: Spark Streaming Box Score")
    logger.info("="*70)
    
    spark = None
    
    try:
        # Attendre que le simulateur soit prêt (15 minutes max)
        input_path = wait_for_simulator(timeout=900)
        if not input_path:
            logger.error("❌ Impossible de détecter le simulateur")
            sys.exit(1)
        
        # Créer un checkpoint unique basé sur le dossier d'input
        run_id = os.path.basename(input_path)
        checkpoint_location = f"{CHECKPOINT_BASE}/live_games_{run_id}"
        
        # Créer la session Spark avec le checkpoint unique
        spark = create_spark_session(checkpoint_location)
        
        # Créer la requête de streaming avec le bon dossier
        df_transformed = create_streaming_query(spark, input_path)
        
        # Démarrer le stream avec le checkpoint unique
        query = start_streaming(spark, df_transformed, input_path, checkpoint_location)
        
        # Monitorer pendant 780 secondes (13 minutes) pour traiter tout le match
        monitor_stream(query, duration_seconds=780)
        
        # Vérifier les résultats
        success = verify_results(spark)
        
        # Résumé final
        logger.info("\n" + "="*70)
        if success:
            logger.info("✅ NBA-13 STREAMING TERMINÉ AVEC SUCCÈS")
        else:
            logger.info("⚠️  NBA-13 STREAMING TERMINÉ AVEC AVERTISSEMENTS")
        logger.info("="*70)
        logger.info(f"📁 Données: {OUTPUT_PATH}")
        logger.info(f"📁 Checkpoints: {checkpoint_location}")
        logger.info("="*70)
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if spark is not None:
            spark.stop()
            logger.info("🔌 Spark arrêté")


if __name__ == "__main__":
    main()
