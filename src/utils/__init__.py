"""
NBA Analytics utilities package

Expose les fonctions utilitaires principales pour faciliter l'import.

Usage:
    from src.utils import get_logger, DataQualityReporter, PipelineMetrics
    from src.utils import alert_on_drift, alert_on_quality_failure
"""

from .monitoring import (
    get_logger,
    DataQualityReporter,
    PipelineMetrics,
    log_pipeline_start,
    log_pipeline_end,
)

from .alerts import (
    AlertManager,
    alert_on_drift,
    alert_on_quality_failure,
    alert_on_pipeline_failure,
    alert_on_performance_degradation,
    send_alert,
)

__all__ = [
    # Monitoring
    'get_logger',
    'DataQualityReporter',
    'PipelineMetrics',
    'log_pipeline_start',
    'log_pipeline_end',
    # Alerts
    'AlertManager',
    'alert_on_drift',
    'alert_on_quality_failure',
    'alert_on_pipeline_failure',
    'alert_on_performance_degradation',
    'send_alert',
]
