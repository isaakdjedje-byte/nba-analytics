"""
Configuration centralisée avec Pydantic Settings
Gère les variables d'environnement et la configuration
"""

import re
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SeasonConfig:
    """Configuration saison dynamique"""
    CURRENT_SEASON: str = "2025-26"
    
    @classmethod
    def get_season_year_start(cls) -> int:
        """Retourne l'année de début de saison (ex: 2025)"""
        return int(cls.CURRENT_SEASON.split('-')[0])
    
    @classmethod
    def get_season_year_end(cls) -> int:
        """Retourne l'année de fin de saison (ex: 2026)"""
        year_start = cls.get_season_year_start()
        return year_start + 1
    
    @classmethod
    def is_valid_season_format(cls, season: str) -> bool:
        """Valide le format d'une saison (YYYY-YY)"""
        return bool(re.match(r'^\d{4}-\d{2}$', season))
    
    @classmethod
    def get_current_season_from_date(cls, date: Optional[datetime] = None) -> str:
        """Détermine la saison NBA en cours basée sur la date"""
        if date is None:
            date = datetime.now()
        
        # Saison NBA : Octobre -> Juin
        year = date.year
        month = date.month
        
        if month >= 10:  # Octobre à Décembre = nouvelle saison
            return f"{year}-{str(year+1)[-2:]}"
        else:  # Janvier à Septembre = saison en cours
            return f"{year-1}-{str(year)[-2:]}"
    
    @classmethod
    def get_season_file_suffix(cls, season: Optional[str] = None) -> str:
        """Convertit '2025-26' en '2025_26' pour les noms de fichiers"""
        if season is None:
            season = cls.CURRENT_SEASON
        return season.replace('-', '_')


class Settings(BaseSettings):
    """Configuration principale de l'application"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = Field(default="NBA Analytics Platform", alias="APP_NAME")
    version: str = Field(default="2.0.0", alias="VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_workers: int = Field(default=1, alias="API_WORKERS")
    
    # Database
    database_url: PostgresDsn = Field(
        default="postgresql://nba:nba@localhost:5432/nba",
        alias="DATABASE_URL"
    )
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, alias="DATABASE_MAX_OVERFLOW")
    
    # Cache
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379",
        alias="REDIS_URL"
    )
    redis_db: int = Field(default=0, alias="REDIS_DB")
    
    # MinIO / S3
    minio_endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="nbaadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="nbapassword123", alias="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")
    minio_bucket_data: str = Field(default="nba-data", alias="MINIO_BUCKET_DATA")
    
    # MLflow
    mlflow_tracking_uri: str = Field(
        default="http://localhost:5000",
        alias="MLFLOW_TRACKING_URI"
    )
    mlflow_experiment: str = Field(default="nba-predictions", alias="MLFLOW_EXPERIMENT")
    
    # Data Paths
    data_root: Path = Field(default=Path("data"), alias="DATA_ROOT")
    data_raw: Path = Field(default=Path("data/raw"), alias="DATA_RAW")
    data_silver: Path = Field(default=Path("data/silver"), alias="DATA_SILVER")
    data_gold: Path = Field(default=Path("data/gold"), alias="DATA_GOLD")
    data_exports: Path = Field(default=Path("data/exports"), alias="DATA_EXPORTS")
    
    # Catalog (SQLite pour zero budget)
    catalog_db_path: Path = Field(
        default=Path("data/catalog.db"),
        alias="CATALOG_DB_PATH"
    )
    
    # ML Paths
    model_path: Path = Field(default=Path("models"), alias="MODEL_PATH")
    predictions_path: Path = Field(default=Path("predictions"), alias="PREDICTIONS_PATH")
    default_model: str = Field(default="xgb_optimized", alias="DEFAULT_MODEL")
    features_file: str = Field(default="features_v3.parquet", alias="FEATURES_FILE")
    default_model_file: str = Field(default="model_xgb.joblib", alias="DEFAULT_MODEL_FILE")
    prediction_threshold: float = Field(default=0.5, alias="PREDICTION_THRESHOLD")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(
        default="json",
        alias="LOG_FORMAT"
    )
    
    # Feature Flags
    enable_mlflow: bool = Field(default=True, alias="ENABLE_MLFLOW")
    enable_monitoring: bool = Field(default=True, alias="ENABLE_MONITORING")
    enable_caching: bool = Field(default=True, alias="ENABLE_CACHING")
    
    # Temporal Analysis & Confidence Settings (NEW)
    temporal_analysis_enabled: bool = Field(default=True, alias="TEMPORAL_ANALYSIS_ENABLED")
    confidence_thresholds: List[float] = Field(default=[0.65, 0.70, 0.75], alias="CONFIDENCE_THRESHOLDS")
    nba23_integration_enabled: bool = Field(default=True, alias="NBA23_INTEGRATION_ENABLED")
    prediction_grade_enabled: bool = Field(default=True, alias="PREDICTION_GRADE_ENABLED")
    min_games_for_confidence: int = Field(default=50, alias="MIN_GAMES_FOR_CONFIDENCE")
    temporal_decay_factor: float = Field(default=0.95, alias="TEMPORAL_DECAY_FACTOR")
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Valide l'environnement"""
        allowed = ["development", "staging", "production"]
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v.lower()
    
    @field_validator("data_root", "data_raw", "data_silver", "data_gold", "data_exports")
    @classmethod
    def validate_paths(cls, v: Path) -> Path:
        """Crée les répertoires s'ils n'existent pas"""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @property
    def is_development(self) -> bool:
        """Vérifie si on est en développement"""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Vérifie si on est en production"""
        return self.environment == "production"
    
    @property
    def database_async_url(self) -> str:
        """URL async pour PostgreSQL"""
        return str(self.database_url).replace(
            "postgresql://", "postgresql+asyncpg://"
        )
    
    # Chemins ML calculés
    @property
    def data_ml_features(self) -> Path:
        """Répertoire des features ML"""
        return self.data_gold / "ml_features"
    
    @property
    def model_optimized_path(self) -> Path:
        """Chemin vers les modèles optimisés"""
        return self.model_path / "optimized"
    
    @property
    def features_v3_path(self) -> Path:
        """Chemin vers features_v3.parquet"""
        return self.data_ml_features / self.features_file
    
    @property
    def model_xgb_path(self) -> Path:
        """Chemin vers model_xgb.joblib"""
        return self.model_optimized_path / self.default_model_file
    
    @property
    def model_rf_path(self) -> Path:
        """Chemin vers model_rf.joblib"""
        return self.model_optimized_path / "model_rf.joblib"
    
    @property
    def calibrator_xgb_path(self) -> Path:
        """Chemin vers calibrator_xgb.joblib"""
        return self.model_optimized_path / "calibrator_xgb.joblib"
    
    @property
    def calibrator_rf_path(self) -> Path:
        """Chemin vers calibrator_rf.joblib"""
        return self.model_optimized_path / "calibrator_rf.joblib"
    
    @property
    def selected_features_path(self) -> Path:
        """Chemin vers selected_features.json"""
        return self.model_optimized_path / "selected_features.json"
    
    @property
    def training_summary_path(self) -> Path:
        """Chemin vers training_summary.json"""
        return self.model_optimized_path / "training_summary.json"
    
    @property
    def tracking_history_path(self) -> Path:
        """Chemin vers tracking_history.csv"""
        return self.predictions_path / "tracking_history.csv"
    
    @property
    def latest_predictions_path(self) -> Path:
        """Chemin vers latest_predictions_optimized.csv"""
        return self.predictions_path / "latest_predictions_optimized.csv"
    
    @property
    def team_mapping_path(self) -> Path:
        """Chemin vers team_name_to_id.json"""
        return self.data_root / "team_name_to_id.json"
    
    def validate_critical_paths(self) -> dict:
        """Vérifie que tous les chemins critiques existent
        
        Returns:
            dict: {'valid': bool, 'missing': list}
        """
        required_paths = {
            'data_gold': self.data_gold,
            'model_path': self.model_path,
            'predictions_path': self.predictions_path,
            'features_v3': self.features_v3_path,
            'model_xgb': self.model_xgb_path,
        }
        
        missing = []
        for name, path in required_paths.items():
            if not path.exists():
                missing.append(f"{name}: {path}")
        
        return {
            'valid': len(missing) == 0,
            'missing': missing
        }


@lru_cache()
def get_settings() -> Settings:
    """Retourne les settings (singleton avec cache)"""
    return Settings()


def clear_settings_cache():
    """Vide le cache des settings (utile pour les tests)"""
    get_settings.cache_clear()


# Instance globale
settings = get_settings()
