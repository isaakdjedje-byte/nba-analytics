"""
Pytest configuration and fixtures for NBA Analytics tests
Professional pytest setup with proper Spark session management
"""
import pytest
import shutil
import os
import sys
import subprocess
from pathlib import Path
from pyspark.sql import SparkSession

# Setup Windows Hadoop compatibility before anything else
if sys.platform == 'win32':
    setup_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'setup_windows_hadoop_complete.py')
    if os.path.exists(setup_script):
        subprocess.run([sys.executable, setup_script], capture_output=True)
    
    # Set environment variables explicitly
    hadoop_home = os.path.join(os.getcwd(), 'tmp', 'hadoop')
    bin_dir = os.path.join(hadoop_home, 'bin')
    os.environ['HADOOP_HOME'] = hadoop_home
    os.environ['PATH'] = bin_dir + os.pathsep + os.environ.get('PATH', '')
    os.environ['SPARK_LOCAL_DIRS'] = os.path.join(os.getcwd(), 'tmp', 'spark')
    os.environ['HADOOP_OPTS'] = '-Djava.library.path=' + bin_dir
    
    os.makedirs(os.environ['SPARK_LOCAL_DIRS'], exist_ok=True)


@pytest.fixture(scope="session")
def spark_session():
    """
    Creates a SparkSession for all tests in the session.
    
    This fixture creates a single SparkSession that is shared across all tests,
    improving performance. The session is properly cleaned up after all tests complete.
    
    Yields:
        SparkSession: Configured SparkSession with Delta Lake support
    """
    builder = (SparkSession.builder
        .appName("NBA-Analytics-Tests")
        .master("local[1]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.adaptive.enabled", "false")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "false")
        .config("spark.serializer", "org.apache.spark.serializer.JavaSerializer")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.default.parallelism", "1")
    )
    
    # Configurations specifiques Windows
    if sys.platform == 'win32':
        builder = (builder
            .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.LocalFileSystem")
            .config("spark.hadoop.fs.hdfs.impl", "org.apache.hadoop.hdfs.DistributedFileSystem")
            .config("spark.sql.warehouse.dir", os.path.join(os.getcwd(), 'tmp', 'spark-warehouse'))
        )
    
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    
    yield spark
    
    # Cleanup: Stop SparkSession after all tests
    spark.stop()


@pytest.fixture(scope="function")
def test_dir(tmp_path):
    """
    Provides a temporary directory for each test function.
    
    Uses pytest's built-in tmp_path fixture which automatically cleans up.
    
    Args:
        tmp_path: pytest fixture providing a temporary path
        
    Returns:
        Path: Temporary directory path for the test
    """
    return tmp_path


@pytest.fixture(scope="function")
def delta_path(test_dir):
    """
    Provides a path for Delta Lake storage in tests.
    
    Args:
        test_dir: Temporary directory fixture
        
    Returns:
        str: Path to Delta Lake directory
    """
    path = test_dir / "delta"
    return str(path)


@pytest.fixture(scope="function")
def log_path(test_dir):
    """
    Provides a path for schema evolution log files.
    
    Args:
        test_dir: Temporary directory fixture
        
    Returns:
        str: Path to log file
    """
    return str(test_dir / "schema_evolution.log")


@pytest.fixture(scope="function", autouse=True)
def cleanup_delta(delta_path):
    """
    Automatically cleans up Delta Lake directory before each test.
    
    This ensures test isolation by removing any leftover data from previous tests.
    
    Args:
        delta_path: Delta Lake path fixture
    """
    path = Path(delta_path)
    if path.exists():
        shutil.rmtree(path)
    yield
    # Cleanup after test as well
    if path.exists():
        shutil.rmtree(path)


@pytest.fixture
def sample_data_v1(spark_session):
    """
    Provides sample DataFrame with schema V1.
    
    Args:
        spark_session: SparkSession fixture
        
    Returns:
        DataFrame: Sample data with 4 columns
    """
    return spark_session.createDataFrame([
        (1, "LAL", 120, 45),
        (2, "GSW", 115, 42)
    ], ["game_id", "team", "points", "rebounds"])


@pytest.fixture
def sample_data_v2(spark_session):
    """
    Provides sample DataFrame with schema V2 (additional columns).
    
    Args:
        spark_session: SparkSession fixture
        
    Returns:
        DataFrame: Sample data with 6 columns
    """
    return spark_session.createDataFrame([
        (3, "BOS", 108, 38, 25, 0.58),
        (4, "MIA", 112, 41, 22, 0.62)
    ], ["game_id", "team", "points", "rebounds", "assists", "ts_pct"])


# Fixtures pour NBA-29
import tempfile
import pandas as pd


@pytest.fixture
def reset_settings_cache():
    """Reset le cache des settings avant chaque test"""
    from nba.config import clear_settings_cache
    clear_settings_cache()
    yield


@pytest.fixture
def temp_gold_dir(tmp_path):
    """Crée un répertoire gold temporaire pour les tests"""
    gold_dir = tmp_path / "gold"
    gold_dir.mkdir(parents=True, exist_ok=True)
    return gold_dir


@pytest.fixture
def sample_parquet_dataset(temp_gold_dir):
    """Crée un dataset parquet de test"""
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["LeBron", "Curry", "Durant"],
        "season": ["2023-24", "2023-24", "2023-24"]
    })
    
    dataset_path = temp_gold_dir / "test_players.parquet"
    df.to_parquet(dataset_path)
    
    return "test_players", temp_gold_dir
