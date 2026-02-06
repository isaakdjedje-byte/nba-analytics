#!/usr/bin/env python3
"""
Pipeline Spark avec les 20 transformations et formules officielles NBA
"""
import os
import sys
import logging
import yaml
from datetime import datetime
from typing import Dict, Optional
from pyspark.sql import SparkSession, DataFrame, Window
from pyspark.sql.functions import (
    col, when, lit, current_timestamp, to_date, year, month, dayofmonth,
    datediff, lag, lead, row_number, monotonically_increasing_id,
    sum as spark_sum, avg, max as spark_max, min as spark_min, count,
    coalesce, round as spark_round, concat, length, upper, lower, trim,
    regexp_replace, expr, abs as spark_abs
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    BooleanType, DoubleType, DateType, TimestampType
)
from delta.tables import DeltaTable
# Import formules NBA
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# UDFs définis inline dans apply_advanced_stats pour éviter sérialisation

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Config
with open('src/config/seasons_config.yaml', 'r') as f:
    CONFIG = yaml.safe_load(f)
APP_NAME = CONFIG['spark']['app_name']
RAW_BASE = CONFIG['paths']['raw_base']
PROCESSED_BASE = CONFIG['paths']['processed_base']
EXPORTS_BASE = CONFIG['paths']['exports_base']
SAISONS = CONFIG['saisons']
def create_spark_session() -> SparkSession:
    """Crée session Spark avec Delta Lake"""
    logger.info("🔧 Initialisation Spark...")
    
    spark = (SparkSession.builder
        .appName(APP_NAME)
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .getOrCreate()
    )
    
    spark.sparkContext.setLogLevel("WARN")
    
    
    logger.info(f"✅ Spark {spark.version} initialisé")
    return spark
def read_season_games(spark: SparkSession, season: str, season_type: str = "regular_season") -> Optional[DataFrame]:
    """Lit les matchs d'une saison"""
    season_dir = f"{RAW_BASE}/{season.replace('-', '_')}"
    filename = f"games_{season_type}.json"
    filepath = f"{season_dir}/{filename}"
    
    if not os.path.exists(filepath):
        logger.warning(f"⚠️  Fichier non trouvé: {filepath}")
        return None
    
    try:
        logger.info(f"📖 Lecture {season} {season_type}")
        # Lecture avec multiLine=True pour JSON structuré
        df = spark.read.option("multiLine", True).json(filepath)
        
        # Debug: voir les colonnes disponibles
        logger.info(f"   📋 Colonnes brutes: {df.columns}")
        
        # Extraction data depuis la structure {"data": [...]}
        if "data" in df.columns:
            df = df.selectExpr("explode(data) as record").select("record.*")
            logger.info(f"   📋 Colonnes après explode: {df.columns[:10]}...")
        else:
            logger.warning(f"   ⚠️  Colonne 'data' non trouvée, utilisation directe")
        
        # Vérification que les données sont bien présentes
        if len(df.columns) <= 2:
            logger.error(f"   ❌ Données vides ou mal extraites!")
            return None
        
        # Ajoute colonnes saison
        df = (df
            .withColumn("season", lit(season))
            .withColumn("season_type", lit(season_type))
        )
        
        count = df.count()
        logger.info(f"   ✅ {count:,} matchs lus avec {len(df.columns)} colonnes")
        return df
        
    except Exception as e:
        logger.error(f"❌ Erreur lecture: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def apply_foundation_transforms(df: DataFrame) -> DataFrame:
    """1-5: Fondations essentielles"""
    logger.info("   🔨 Fondations...")
    
    return (df
        # 1. Typage strict
        .withColumn("game_id", col("GAME_ID").cast("string"))
        .withColumn("team_id", col("TEAM_ID").cast("int"))
        .withColumn("points", col("PTS").cast("int"))
        .withColumn("fgm", col("FGM").cast("int"))
        .withColumn("fga", col("FGA").cast("int"))
        .withColumn("fg3m", col("FG3M").cast("int"))
        .withColumn("fg3a", col("FG3A").cast("int"))
        .withColumn("ftm", col("FTM").cast("int"))
        .withColumn("fta", col("FTA").cast("int"))
        .withColumn("oreb", col("OREB").cast("int"))
        .withColumn("dreb", col("DREB").cast("int"))
        .withColumn("reb", col("REB").cast("int"))
        .withColumn("ast", col("AST").cast("int"))
        .withColumn("stl", col("STL").cast("int"))
        .withColumn("blk", col("BLK").cast("int"))
        .withColumn("tov", col("TOV").cast("int"))
        .withColumn("pf", col("PF").cast("int"))
        
        # 2. Gestion nulls
        .fillna({
            "points": 0, "fgm": 0, "fga": 0, "fg3m": 0, "fg3a": 0,
            "ftm": 0, "fta": 0, "oreb": 0, "dreb": 0, "reb": 0,
            "ast": 0, "stl": 0, "blk": 0, "tov": 0, "pf": 0
        })
        
        # 3. Timestamps
        .withColumn("ingestion_timestamp", current_timestamp())
        .withColumn("game_date", to_date(col("GAME_DATE"), "yyyy-MM-dd"))
        .withColumn("game_year", year(col("game_date")))
        .withColumn("game_month", month(col("game_date")))
        
        # 4. Déduplication (game_id + team_id)
        .dropDuplicates(["game_id", "team_id"])
    )

def apply_form_transforms(df: DataFrame) -> DataFrame:
    """6-10: Forme et contexte"""
    logger.info("   🔨 Forme & Contexte...")

    # Window pour calculs par équipe
    window_team = Window.partitionBy("team_id").orderBy("game_date")
    window_team_5 = Window.partitionBy("team_id").orderBy("game_date").rowsBetween(-4, 0)
    window_team_10 = Window.partitionBy("team_id").orderBy("game_date").rowsBetween(-9, 0)

    return (df
        # 6. Moyenne mobile 5 matchs
        .withColumn("avg_points_last_5", spark_round(avg("points").over(window_team_5), 2))
        .withColumn("avg_reb_last_5", spark_round(avg("reb").over(window_team_5), 2))
        .withColumn("avg_ast_last_5", spark_round(avg("ast").over(window_team_5), 2))

        # Moyenne saison (tous les matchs avant)
        .withColumn("avg_points_season", spark_round(avg("points").over(window_team), 2))

        # 7. Tendance vs saison
        .withColumn("trend_vs_season", spark_round(col("avg_points_last_5") - col("avg_points_season"), 2))

        # 8. Jours de repos (diff avec match précédent)
        .withColumn("last_game_date", lag("game_date", 1).over(window_team))
        .withColumn("days_rest", datediff(col("game_date"), col("last_game_date")))
        .withColumn("days_rest", coalesce(col("days_rest"), lit(7)))  # Premier match = 7 jours

        # 9. Back-to-back flag
        .withColumn("is_back_to_back", when(col("days_rest") == 0, True).otherwise(False))

        # 10. Forme W-L sur 10 derniers
        .withColumn("result_win", when(col("WL") == "W", 1).otherwise(0))
        .withColumn("wins_last_10", spark_sum("result_win").over(window_team_10))
    )
def apply_advanced_stats(df: DataFrame, spark: SparkSession) -> DataFrame:
    """11-16: Stats avancées avec formules officielles"""
    logger.info("   🔨 Stats Avancées...")
    
    # Crée UDFs inline (évite problème sérialisation)
    from pyspark.sql.functions import udf
    from pyspark.sql.types import DoubleType
    
    # UDF True Shooting %
    @udf(DoubleType())
    def calc_ts(points, fga, fta):
        try:
            tsa = float(fga) + 0.44 * float(fta)
            if tsa == 0:
                return 0.0
            return float(points) / (2 * tsa)
        except:
            return 0.0
    
    # UDF Game Score
    @udf(DoubleType())
    def calc_gs(points, fgm, fga, fta, ftm, oreb, dreb, stl, ast, blk, pf, tov):
        try:
            gs = (float(points) + 0.4 * float(fgm) - 0.7 * float(fga) - 
                  0.4 * (float(fta) - float(ftm)) + 0.7 * float(oreb) + 
                  0.3 * float(dreb) + float(stl) + 0.7 * float(ast) + 
                  0.7 * float(blk) - 0.4 * float(pf) - float(tov))
            return gs
        except:
            return 0.0

    return (df
        # 11. True Shooting %
        .withColumn("ts_pct", spark_round(calc_ts(col("points"), col("fga"), col("fta")) * 100, 3))

        # 12. Effective FG%
        .withColumn("efg_pct", spark_round(((col("fgm") + 0.5 * col("fg3m")) / col("fga")) * 100, 3))

        # 13. Game Score (forme récente)
        .withColumn("game_score", spark_round(calc_gs(
            col("points"), col("fgm"), col("fga"), col("fta"), col("ftm"),
            col("oreb"), col("dreb"), col("stl"), col("ast"), col("blk"), col("pf"), col("tov")
        ), 2))

        # 14. Efficacité fatigue (simplifiée)
        .withColumn("fatigue_efficiency",
            when(col("is_back_to_back"), col("points") * 0.9)  # -10% si back-to-back
            .when(col("days_rest") >= 3, col("points") * 1.05)  # +5% si repos 3+ jours
            .otherwise(col("points"))
        )

        # 15-16. PER et Usage Rate (nécessitent stats équipe - placeholder pour l'instant)
        .withColumn("per_estimate", lit(15.0))  # Sera calculé avec données équipe complètes
        .withColumn("usage_rate_estimate", lit(20.0))  # Idem

        # 13bis. Pace estimate (simplifié)
        .withColumn("pace_estimate", (col("fga") + col("tov") + 0.44 * col("fta")))
    )

def apply_context_transforms(df: DataFrame) -> DataFrame:
    """17-20: Contexte et enrichissement"""
    logger.info("   🔨 Contexte...")
    
    return (df
        # 17. Record W-L saison (cumulatif)
        .withColumn("games_played", row_number().over(Window.partitionBy("team_id", "season").orderBy("game_date")))
        .withColumn("wins_cumul", spark_sum(when(col("WL") == "W", 1).otherwise(0)).over(
            Window.partitionBy("team_id", "season").orderBy("game_date")
        ))
        .withColumn("win_pct", spark_round(col("wins_cumul") / col("games_played") * 100, 2))
        
        # 18. Domicile/Extérieur (basé sur MATCHUP)
        .withColumn("is_home", when(col("MATCHUP").contains("vs."), True).otherwise(False))
        .withColumn("location", when(col("is_home"), "Home").otherwise("Away"))
        
        # Record H/A séparé (simplifié)
        .withColumn("home_wins", spark_sum(when((col("is_home") & (col("WL") == "W")), 1).otherwise(0)).over(
            Window.partitionBy("team_id", "season").orderBy("game_date")
        ))
        
        # 19. Marge de victoire/défaite (PLUS_MINUS ou calculé)
        .withColumn("point_diff", 
            when(col("PLUS_MINUS").isNotNull(), col("PLUS_MINUS").cast("double"))
            .otherwise(lit(0.0))
        )
        .withColumn("abs_point_diff", spark_abs(col("point_diff")))
        
        # 20. Importance match (algo simple basé sur date)
        .withColumn("games_remaining", 
            when(col("season_type") == "regular_season", 82 - col("games_played")).otherwise(0)
        )
        .withColumn("match_importance",
            when((col("win_pct").between(40, 60)) & (col("games_remaining") <= 20), "Critical")
            .when(col("games_remaining") <= 30, "High")
            .when(col("games_remaining") <= 50, "Medium")
            .otherwise("Low")
        )
    )
def process_season(spark: SparkSession, season: str):
    """Traite une saison complète"""
    logger.info(f"\n📅 Traitement saison: {season}")
    
    # Lecture Regular Season
    df_rs = read_season_games(spark, season, "regular_season")
    
    # Lecture Playoffs (si existe)
    df_po = read_season_games(spark, season, "playoffs")
    
    # Union si les deux existent
    if df_rs is None and df_po is None:
        logger.warning(f"⚠️  Aucune donnée pour {season}")
        return
    
    df = df_rs if df_po is None else df_rs.unionByName(df_po, allowMissingColumns=True) if df_rs else df_po
    
    if df is None:
        logger.warning(f"⚠️  DataFrame vide après union pour {season}")
        return
    
    # Vérification des colonnes requises
    required_cols = ["GAME_ID", "TEAM_ID", "GAME_DATE", "PTS"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"   ❌ Colonnes manquantes: {missing_cols}")
        return
    
    # Application des 20 transformations en chaîne
    df_transformed = (df
        .transform(apply_foundation_transforms)
        .transform(apply_form_transforms)
        .transform(lambda df: apply_advanced_stats(df, spark))
        .transform(apply_context_transforms)
        
        # Sélection finale des colonnes utiles
        .select(
            "game_id", "team_id", "season", "season_type",
            "game_date", "game_year", "game_month",
            "points", "fgm", "fga", "fg3m", "fg3a", "ftm", "fta",
            "oreb", "dreb", "reb", "ast", "stl", "blk", "tov", "pf",
            "avg_points_last_5", "avg_reb_last_5", "avg_ast_last_5",
            "trend_vs_season", "days_rest", "is_back_to_back", "wins_last_10",
            "ts_pct", "efg_pct", "game_score", "fatigue_efficiency",
            "per_estimate", "usage_rate_estimate", "pace_estimate",
            "win_pct", "is_home", "location", "point_diff",
            "match_importance", "ingestion_timestamp"
        )
    )
    
    # Écriture Delta Lake partitionné
    output_path = f"{PROCESSED_BASE}/games_enriched"
    
    logger.info(f"💾 Écriture Delta: {output_path}")
    (df_transformed.write
        .format("delta")
        .mode("append")  # Append car multi-saisons
        .partitionBy("season", "game_year")
        .option("mergeSchema", "true")
        .save(output_path)
    )
    
    # Export Parquet pour analyse externe
    parquet_path = f"{EXPORTS_BASE}/games_{season.replace('-', '_')}.parquet"
    logger.info(f"💾 Export Parquet: {parquet_path}")
    df_transformed.write.mode("overwrite").parquet(parquet_path)
    
    count = df_transformed.count()
    logger.info(f"   ✅ {count:,} matchs traités et sauvegardés")
def main():
    """Orchestration complète"""
    logger.info("="*70)
    logger.info("🚀 PIPELINE NBA-12: 20 Transformations Multi-Saisons")
    logger.info("="*70)
    
    start_time = datetime.now()
    spark = None
    
    try:
        # Initialisation
        spark = create_spark_session()
        os.makedirs(PROCESSED_BASE, exist_ok=True)
        os.makedirs(EXPORTS_BASE, exist_ok=True)
        
        # Traitement par saison
        for season in SAISONS:
            process_season(spark, season)
        
        # Optimisation finale
        logger.info("\n🚀 Optimisation Delta...")
        try:
            delta_table = DeltaTable.forPath(spark, f"{PROCESSED_BASE}/games_enriched")
            delta_table.optimize().executeCompaction()
            logger.info("✅ Optimisation Delta terminée")
        except Exception as e:
            logger.warning(f"⚠️ Optimisation ignorée: {e}")
        
        # Résumé
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("\n" + "="*70)
        logger.info("✅ PIPELINE TERMINÉ")
        logger.info("="*70)
        logger.info(f"⏱️  Durée: {duration:.1f}s")
        logger.info(f"📁 Delta: {PROCESSED_BASE}/games_enriched/")
        logger.info(f"📁 Exports: {EXPORTS_BASE}/")
        logger.info("="*70)
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        raise
    finally:
        if spark is not None:
            spark.stop()
if __name__ == "__main__":
    main()


