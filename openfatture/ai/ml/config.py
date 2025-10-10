"""ML Configuration for Cash Flow Prediction.

Pydantic-based configuration system for ML models, feature engineering,
and prediction settings. Supports environment variables for production deployment.

Environment Variables:
- OPENFATTURE_ML_MODEL_PATH: Path to saved models (default: .models/)
- OPENFATTURE_ML_PROPHET_WEIGHT: Prophet weight in ensemble (default: 0.4)
- OPENFATTURE_ML_XGBOOST_WEIGHT: XGBoost weight in ensemble (default: 0.6)
- OPENFATTURE_ML_OPTIMIZE_WEIGHTS: Optimize weights on validation (default: false)
- OPENFATTURE_ML_CACHE_PREDICTIONS: Cache predictions (default: true)
- OPENFATTURE_ML_MIN_CONFIDENCE: Minimum confidence for predictions (default: 0.5)
"""

from pathlib import Path
from typing import Optional, Literal
import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class MLConfig(BaseSettings):
    """ML system configuration.

    All settings can be overridden via environment variables with prefix:
    OPENFATTURE_ML_*

    Example:
        >>> config = MLConfig()
        >>> print(config.model_path)
        PosixPath('.models')
        >>>
        >>> # Override via environment
        >>> os.environ['OPENFATTURE_ML_MODEL_PATH'] = '/app/models'
        >>> config = MLConfig()
        >>> print(config.model_path)
        PosixPath('/app/models')
    """

    model_config = SettingsConfigDict(
        env_prefix='OPENFATTURE_ML_',
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
    )

    # Model Storage
    model_path: Path = Field(
        default=Path('.models'),
        description="Directory for storing trained models",
    )

    cache_path: Path = Field(
        default=Path('.cache/ml_data'),
        description="Directory for caching preprocessed datasets",
    )

    # Ensemble Weights
    prophet_weight: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Weight for Prophet model in ensemble (0.0-1.0)",
    )

    xgboost_weight: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Weight for XGBoost model in ensemble (0.0-1.0)",
    )

    optimize_weights: bool = Field(
        default=False,
        description="Optimize ensemble weights on validation set",
    )

    # Prophet Hyperparameters
    prophet_seasonality_mode: Literal['additive', 'multiplicative'] = Field(
        default='multiplicative',
        description="Prophet seasonality mode",
    )

    prophet_changepoint_prior_scale: float = Field(
        default=0.05,
        ge=0.001,
        le=0.5,
        description="Prophet trend flexibility (higher = more flexible)",
    )

    prophet_seasonality_prior_scale: float = Field(
        default=10.0,
        ge=0.01,
        le=20.0,
        description="Prophet seasonality strength",
    )

    prophet_interval_width: float = Field(
        default=0.80,
        ge=0.5,
        le=0.99,
        description="Prophet prediction interval width",
    )

    # XGBoost Hyperparameters
    xgboost_max_depth: int = Field(
        default=6,
        ge=1,
        le=20,
        description="XGBoost maximum tree depth",
    )

    xgboost_learning_rate: float = Field(
        default=0.1,
        ge=0.001,
        le=0.3,
        description="XGBoost learning rate (eta)",
    )

    xgboost_n_estimators: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="XGBoost number of boosting rounds",
    )

    xgboost_subsample: float = Field(
        default=0.8,
        ge=0.5,
        le=1.0,
        description="XGBoost subsample ratio",
    )

    xgboost_colsample_bytree: float = Field(
        default=0.8,
        ge=0.5,
        le=1.0,
        description="XGBoost column subsample ratio",
    )

    xgboost_use_asymmetric_loss: bool = Field(
        default=True,
        description="Use asymmetric loss function (penalize underestimation)",
    )

    # Feature Engineering
    include_temporal_features: bool = Field(
        default=True,
        description="Include temporal features (day_of_week, seasonality, etc.)",
    )

    include_client_behavior_features: bool = Field(
        default=True,
        description="Include client behavior features (payment history, etc.)",
    )

    include_invoice_features: bool = Field(
        default=True,
        description="Include invoice-specific features (amount, VAT, etc.)",
    )

    scale_features: bool = Field(
        default=True,
        description="Apply StandardScaler to numerical features",
    )

    # Data Loading
    min_payment_data_ratio: float = Field(
        default=0.3,
        ge=0.1,
        le=1.0,
        description="Minimum ratio of invoices with payment data",
    )

    validation_split: float = Field(
        default=0.15,
        ge=0.05,
        le=0.3,
        description="Validation set size (chronological split)",
    )

    test_split: float = Field(
        default=0.15,
        ge=0.05,
        le=0.3,
        description="Test set size (chronological split)",
    )

    # Prediction Settings
    cache_predictions: bool = Field(
        default=True,
        description="Cache predictions for identical inputs",
    )

    min_confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score to return prediction",
    )

    default_forecast_months: int = Field(
        default=3,
        ge=1,
        le=12,
        description="Default number of months to forecast",
    )

    # Performance
    enable_early_stopping: bool = Field(
        default=True,
        description="Enable early stopping for XGBoost",
    )

    early_stopping_rounds: int = Field(
        default=10,
        ge=5,
        le=50,
        description="Number of rounds for early stopping",
    )

    # Logging
    log_predictions: bool = Field(
        default=True,
        description="Log all predictions for monitoring",
    )

    log_model_metrics: bool = Field(
        default=True,
        description="Log model performance metrics",
    )

    @field_validator('prophet_weight', 'xgboost_weight')
    @classmethod
    def validate_weights_sum(cls, v, info):
        """Ensure ensemble weights sum to 1.0."""
        # Note: This validator runs for each field individually
        # Full validation happens in __post_init__
        return v

    def __post_init__(self):
        """Post-initialization validation."""
        # Validate ensemble weights sum to 1.0
        total_weight = self.prophet_weight + self.xgboost_weight
        if not (0.99 <= total_weight <= 1.01):  # Allow small floating point error
            raise ValueError(
                f"Ensemble weights must sum to 1.0, got {total_weight:.3f} "
                f"(prophet={self.prophet_weight}, xgboost={self.xgboost_weight})"
            )

        # Create directories if they don't exist
        self.model_path.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            "ml_config_initialized",
            model_path=str(self.model_path),
            prophet_weight=self.prophet_weight,
            xgboost_weight=self.xgboost_weight,
            optimize_weights=self.optimize_weights,
        )

    def get_prophet_params(self) -> dict:
        """Get Prophet model parameters.

        Returns:
            Dictionary of Prophet parameters
        """
        return {
            'seasonality_mode': self.prophet_seasonality_mode,
            'changepoint_prior_scale': self.prophet_changepoint_prior_scale,
            'seasonality_prior_scale': self.prophet_seasonality_prior_scale,
            'interval_width': self.prophet_interval_width,
            'yearly_seasonality': True,
            'weekly_seasonality': True,
            'daily_seasonality': False,
        }

    def get_xgboost_params(self) -> dict:
        """Get XGBoost model parameters.

        Returns:
            Dictionary of XGBoost parameters
        """
        return {
            'max_depth': self.xgboost_max_depth,
            'learning_rate': self.xgboost_learning_rate,
            'n_estimators': self.xgboost_n_estimators,
            'subsample': self.xgboost_subsample,
            'colsample_bytree': self.xgboost_colsample_bytree,
            'use_asymmetric_loss': self.xgboost_use_asymmetric_loss,
        }

    def get_feature_pipeline_params(self) -> dict:
        """Get feature pipeline parameters.

        Returns:
            Dictionary of feature pipeline parameters
        """
        return {
            'include_temporal': self.include_temporal_features,
            'include_client_behavior': self.include_client_behavior_features,
            'include_invoice': self.include_invoice_features,
            'scale_features': self.scale_features,
        }

    def get_data_loader_params(self) -> dict:
        """Get data loader parameters.

        Returns:
            Dictionary of data loader parameters
        """
        return {
            'cache_dir': self.cache_path,
            'min_payment_data_ratio': self.min_payment_data_ratio,
        }

    def get_model_filepath(self, model_name: str = 'cash_flow') -> str:
        """Get filepath for saving/loading models.

        Args:
            model_name: Name prefix for model files

        Returns:
            Filepath prefix (without extension)
        """
        return str(self.model_path / model_name)


# Global config instance (singleton pattern)
_config: Optional[MLConfig] = None


def get_ml_config(force_reload: bool = False) -> MLConfig:
    """Get or create ML configuration.

    Args:
        force_reload: Force reload from environment

    Returns:
        MLConfig instance
    """
    global _config

    if _config is None or force_reload:
        _config = MLConfig()
        _config.__post_init__()

    return _config


# Default configuration for easy access
DEFAULT_ML_CONFIG = MLConfig()
DEFAULT_ML_CONFIG.__post_init__()
