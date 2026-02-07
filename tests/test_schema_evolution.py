"""
Tests for NBA-14: Schema Evolution Management

Simplified tests to avoid cloudpickle serialization issues with Python 3.14.
Tests use direct DataFrame creation within test methods.

NOTE: These tests require Python 3.11 or 3.12 due to cloudpickle compatibility issues with Python 3.14+
"""
import sys
import os
sys.path.insert(0, 'src')

# Skip all tests if Python 3.14+ (cloudpickle incompatibility)
import pytest
if sys.version_info >= (3, 14):
    pytest.skip("Schema evolution tests require Python 3.11 or 3.12 (cloudpickle incompatibility with 3.14+)", allow_module_level=True)

from src.utils.schema_manager import (
    write_with_merge,
    read_version,
    compare_versions,
    get_current_schema,
    get_schema_history,
    get_version_count,
    validate_schema,
    log_schema_version,
    get_schema_versions,
    get_latest_schema_version,
)


class TestMergeSchema:
    """Test suite for schema merging functionality"""
    
    def test_merge_schema_basic(self, spark_session, delta_path):
        """
        Test basic MergeSchema functionality with column addition.
        """
        # Create V1 data directly in test
        df_v1 = spark_session.createDataFrame([
            (1, "LAL", 120, 45),
            (2, "GSW", 115, 42)
        ], ["game_id", "team", "points", "rebounds"])
        
        # Write V1 data
        df_v1.write.format("delta").mode("overwrite").save(delta_path)
        
        # Create V2 data with additional column
        df_v2 = spark_session.createDataFrame([
            (3, "BOS", 108, 38, 25, 0.58),
            (4, "MIA", 112, 41, 22, 0.62)
        ], ["game_id", "team", "points", "rebounds", "assists", "ts_pct"])
        
        # Write V2 data with mergeSchema
        write_with_merge(df_v2, delta_path, mode="append")
        
        # Verify results
        df_all = spark_session.read.format("delta").load(delta_path)
        
        assert df_all.count() == 4, f"Expected 4 rows, got {df_all.count()}"
        assert "assists" in df_all.columns, "Column 'assists' should exist"
        
        # Verify NULLs for old data
        v1_data = df_all.filter(df_all.game_id.isin([1, 2]))
        null_count = v1_data.filter(v1_data.assists.isNull()).count()
        assert null_count == 2, f"Expected 2 NULLs for old data, got {null_count}"
    
    def test_merge_schema_multiple_columns(self, spark_session, delta_path):
        """
        Test merging multiple new columns at once.
        """
        # V1: 3 columns
        df_v1 = spark_session.createDataFrame([
            (1, "LAL", 120),
        ], ["game_id", "team", "points"])
        
        df_v1.write.format("delta").mode("overwrite").save(delta_path)
        
        # V2: 5 columns (+2 new)
        df_v2 = spark_session.createDataFrame([
            (2, "GSW", 115, 42, 0.58),
        ], ["game_id", "team", "points", "rebounds", "ts_pct"])
        
        write_with_merge(df_v2, delta_path, mode="append")
        
        df_all = spark_session.read.format("delta").load(delta_path)
        
        assert len(df_all.columns) == 5, f"Expected 5 columns, got {len(df_all.columns)}"
        assert "rebounds" in df_all.columns
        assert "ts_pct" in df_all.columns


class TestTimeTravel:
    """Test suite for Delta Lake time travel functionality"""
    
    def test_read_version_historical(self, spark_session, delta_path):
        """
        Test reading a specific historical version.
        """
        # Write V1
        df_v1 = spark_session.createDataFrame([
            (1, "LAL", 100),
            (2, "GSW", 95),
        ], ["game_id", "team", "points"])
        df_v1.write.format("delta").mode("overwrite").save(delta_path)
        
        # Write V2
        df_v2 = spark_session.createDataFrame([
            (3, "BOS", 110),
            (4, "MIA", 105),
        ], ["game_id", "team", "points"])
        df_v2.write.format("delta").mode("append").save(delta_path)
        
        # Read version 0
        df_version_0 = read_version(delta_path, 0, spark_session)
        
        assert df_version_0.count() == 2, f"Version 0 should have 2 rows, got {df_version_0.count()}"
        assert df_version_0.filter(df_version_0.team == "LAL").count() > 0, "Version 0 should contain LAL"
    
    def test_compare_versions(self, spark_session, delta_path):
        """
        Test comparing two versions and detecting differences.
        """
        # V1
        df_v1 = spark_session.createDataFrame([
            (1, "LAL", 100),
        ], ["game_id", "team", "points"])
        df_v1.write.format("delta").mode("overwrite").save(delta_path)
        
        # V2 with new columns
        df_v2 = spark_session.createDataFrame([
            (2, "GSW", 110, 45, 0.55),
        ], ["game_id", "team", "points", "rebounds", "ts_pct"])
        write_with_merge(df_v2, delta_path, mode="append")
        
        # Compare versions
        diff = compare_versions(delta_path, 0, 1, spark_session)
        
        assert "rebounds" in diff["added"], "Should detect 'rebounds' as added"
        assert "ts_pct" in diff["added"], "Should detect 'ts_pct' as added"
        assert diff["record_count_v1"] == 1
        assert diff["record_count_v2"] == 2


class TestFullSchemaEvolution:
    """Test suite for complete schema evolution scenarios"""
    
    def test_full_schema_change_scenario(self, spark_session, delta_path):
        """
        Test complete V1 to V2 evolution scenario.
        """
        # V1 data
        df_v1 = spark_session.createDataFrame([
            (1, "LAL", 120.0, 45),
            (2, "GSW", 115.0, 42)
        ], ["game_id", "team", "points", "rebounds"])
        
        df_v1.write.format("delta").mode("overwrite").save(delta_path)
        
        # V2 data with new columns
        df_v2 = spark_session.createDataFrame([
            (3, "BOS", 108.0, 38, 25, 0.58),
            (4, "MIA", 112.0, 41, 22, 0.62)
        ], ["game_id", "team", "points", "rebounds", "assists", "ts_pct"])
        
        write_with_merge(df_v2, delta_path, mode="append")
        
        # Validate final state
        df_all = spark_session.read.format("delta").load(delta_path)
        
        assert df_all.count() == 4, "Total rows should be 4"
        assert len(df_all.columns) == 6, "Total columns should be 6"
        assert "assists" in df_all.columns
        assert "ts_pct" in df_all.columns
        
        # Validate data consistency
        v1_rows = df_all.filter(df_all.game_id.isin([1, 2]))
        assert v1_rows.filter(v1_rows.assists.isNull()).count() == 2, "V1 data should have NULL assists"
        
        v2_rows = df_all.filter(df_all.game_id.isin([3, 4]))
        assert v2_rows.filter(v2_rows.assists.isNotNull()).count() == 2, "V2 data should have values"


class TestSchemaLogger:
    """Test suite for YAML schema evolution logging"""
    
    def test_log_schema_version(self, log_path):
        """
        Test logging schema versions to YAML file.
        """
        # Log version 1
        log_schema_version(
            version=1,
            columns=["game_id", "team", "points"],
            record_count=100,
            author="NBA-14",
            log_path=log_path
        )
        
        # Log version 2 with changes
        log_schema_version(
            version=2,
            columns=["game_id", "team", "points", "assists"],
            record_count=150,
            changes={
                "added": ["assists"],
                "removed": [],
                "modified": []
            },
            author="NBA-14",
            log_path=log_path
        )
        
        # Verify
        versions = get_schema_versions(log_path)
        assert len(versions) == 2, f"Should have 2 versions, got {len(versions)}"
        
        latest = get_latest_schema_version(log_path)
        assert latest is not None, "Latest version should exist"
        assert latest["version"] == 2
        assert "assists" in latest["columns"]
        assert "changes" in latest


class TestSchemaValidation:
    """Test suite for schema validation functionality"""
    
    def test_validate_schema_success(self, spark_session, delta_path):
        """
        Test successful schema validation.
        """
        df = spark_session.createDataFrame([
            (1, "LAL", 100),
            (2, "GSW", 95),
        ], ["game_id", "team", "points"])
        
        df.write.format("delta").mode("overwrite").save(delta_path)
        
        is_valid = validate_schema(delta_path, ["game_id", "team", "points"], spark_session)
        assert is_valid is True, "Should validate successfully"
    
    def test_validate_schema_failure(self, spark_session, delta_path):
        """
        Test failed schema validation.
        """
        df = spark_session.createDataFrame([
            (1, "LAL", 100),
            (2, "GSW", 95),
        ], ["game_id", "team", "points"])
        
        df.write.format("delta").mode("overwrite").save(delta_path)
        
        is_valid = validate_schema(delta_path, ["game_id", "team", "missing_col"], spark_session)
        assert is_valid is False, "Should fail validation"


class TestSchemaHistory:
    """Test suite for schema history tracking"""
    
    def test_get_schema_history(self, spark_session, delta_path):
        """
        Test retrieving schema history.
        """
        # Create 3 versions
        for i in range(3):
            df = spark_session.createDataFrame([
                (i, f"TEAM{i}", 100 + i),
            ], ["game_id", "team", "points"])
            df.write.format("delta").mode("append").save(delta_path)
        
        history = get_schema_history(delta_path, spark_session)
        
        assert history.count() >= 3, f"Should have at least 3 versions, got {history.count()}"
        
        version_count = get_version_count(delta_path, spark_session)
        assert version_count >= 3, f"Version count should be >= 3, got {version_count}"
