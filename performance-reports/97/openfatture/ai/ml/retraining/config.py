"""Retraining Configuration for ML Models.

Pydantic-based configuration for automatic model retraining, versioning, and rollback.
Supports environment variables for production deployment.

Environment Variables:
- OPENFATTURE_RETRAIN_ENABLED: Enable auto-retraining scheduler (default: false)
- OPENFATTURE_RETRAIN_CHECK_INTERVAL_HOURS: Hours between trigger checks (default: 24)
- OPENFATTURE_RETRAIN_MIN_FEEDBACK_COUNT: Min feedback to trigger retrain (default: 25)
- OPENFATTURE_RETRAIN_MAX_DAYS_SINCE_TRAINING: Max days before retrain (default: 7)
- OPENFATTURE_RETRAIN_PERFORMANCE_DEGRADATION_THRESHOLD: Rollback threshold (default: 0.10)
- OPENFATTURE_RETRAIN_MAX_VERSIONS: Max model versions to keep (default: 10)
"""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class RetrainingConfig(BaseSettings):
    """Retraining system configuration.

    All settings can be overridden via environment variables with prefix:
    OPENFATTURE_RETRAIN_*

    Example:
        >>> config = RetrainingConfig()
        >>> print(config.enabled)
        False
        >>>
        >>> # Override via environment
        >>> os.environ['OPENFATTURE_RETRAIN_ENABLED'] = 'true'
        >>> config = RetrainingConfig()
        >>> print(config.enabled)
        True
    """

    model_config = SettingsConfigDict(
        env_prefix="OPENFATTURE_RETRAIN_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Scheduler Settings
    enabled: bool = Field(
        default=False,
        description="Enable automatic retraining scheduler (disabled by default for safety)",
    )

    check_interval_hours: int = Field(
        default=24,
        ge=1,
        le=168,  # Max 1 week
        description="Hours between retraining trigger checks",
    )

    # Trigger Thresholds
    min_feedback_count: int = Field(
        default=25,
        ge=10,
        le=1000,
        description="Minimum unprocessed feedback to trigger retraining",
    )

    max_days_since_training: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Maximum days since last training before forced retrain",
    )

    min_accuracy_drift: float = Field(
        default=0.05,
        ge=0.01,
        le=0.20,
        description="Minimum accuracy drift to trigger retraining (5% default)",
    )

    # Model Versioning
    versions_path: Path = Field(
        default=Path(".models/versions"),
        description="Directory for storing model versions",
    )

    max_versions: int = Field(
        default=10,
        ge=3,
        le=50,
        description="Maximum model versions to keep (older versions auto-deleted)",
    )

    # Performance Thresholds
    performance_degradation_threshold: float = Field(
        default=0.10,
        ge=0.01,
        le=0.50,
        description="Max performance degradation before rollback (10% default)",
    )

    min_confidence_for_deployment: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Minimum average confidence to deploy new model version",
    )

    # Validation Settings
    validation_data_months: int = Field(
        default=3,
        ge=1,
        le=12,
        description="Months of historical data for validation",
    )

    require_improvement_for_deployment: bool = Field(
        default=True,
        description="Require new model to outperform current on validation set",
    )

    min_improvement_percentage: float = Field(
        default=0.02,
        ge=0.0,
        le=0.20,
        description="Minimum improvement % required for deployment (2% default)",
    )

    # Evaluation Metrics
    primary_metric: str = Field(
        default="mae",
        description="Primary metric for model comparison (mae, rmse, r2)",
    )

    secondary_metrics: list[str] = Field(
        default=["rmse", "r2", "mape"],
        description="Secondary metrics to track",
    )

    # Safety Settings
    dry_run: bool = Field(
        default=False,
        description="Dry run mode: evaluate but don't deploy new models",
    )

    notification_email: str | None = Field(
        default=None,
        description="Email for retraining notifications (optional)",
    )

    # Logging
    log_retraining_events: bool = Field(
        default=True,
        description="Log all retraining events (triggers, evaluations, deployments)",
    )

    @field_validator("primary_metric")
    @classmethod
    def validate_primary_metric(cls, v: str) -> str:
        """Validate primary metric choice."""
        allowed = ["mae", "rmse", "r2", "mape"]
        if v.lower() not in allowed:
            raise ValueError(f"primary_metric must be one of {allowed}, got {v}")
        return v.lower()

    def __post_init__(self) -> None:
        """Post-initialization setup."""
        # Create versions directory
        self.versions_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            "retraining_config_initialized",
            enabled=self.enabled,
            check_interval_hours=self.check_interval_hours,
            min_feedback_count=self.min_feedback_count,
            max_days_since_training=self.max_days_since_training,
            dry_run=self.dry_run,
        )

    def get_trigger_params(self) -> dict:
        """Get retraining trigger parameters.

        Returns:
            Dictionary of trigger parameters
        """
        return {
            "min_feedback_count": self.min_feedback_count,
            "max_days_since_training": self.max_days_since_training,
            "min_accuracy_drift": self.min_accuracy_drift,
        }

    def get_evaluator_params(self) -> dict:
        """Get model evaluator parameters.

        Returns:
            Dictionary of evaluator parameters
        """
        return {
            "primary_metric": self.primary_metric,
            "secondary_metrics": self.secondary_metrics,
            "performance_degradation_threshold": self.performance_degradation_threshold,
            "min_confidence": self.min_confidence_for_deployment,
            "require_improvement": self.require_improvement_for_deployment,
            "min_improvement_pct": self.min_improvement_percentage,
        }

    def get_scheduler_params(self) -> dict:
        """Get scheduler parameters.

        Returns:
            Dictionary of scheduler parameters
        """
        return {
            "enabled": self.enabled,
            "interval_hours": self.check_interval_hours,
            "dry_run": self.dry_run,
        }


# Global config instance (singleton pattern)
_config: RetrainingConfig | None = None


def get_retraining_config(force_reload: bool = False) -> RetrainingConfig:
    """Get or create retraining configuration.

    Args:
        force_reload: Force reload from environment

    Returns:
        RetrainingConfig instance
    """
    global _config

    if _config is None or force_reload:
        _config = RetrainingConfig()
        _config.__post_init__()

    return _config


# Default configuration for easy access
DEFAULT_RETRAIN_CONFIG = RetrainingConfig()
DEFAULT_RETRAIN_CONFIG.__post_init__()
