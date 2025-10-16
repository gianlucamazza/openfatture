"""ML Model Retraining and Versioning System.

This package provides automatic model retraining, versioning, and rollback
capabilities for the ML prediction models (cash flow, tax suggestions, etc.).

Key Components:
- RetrainingConfig: Configuration for retraining triggers and thresholds
- ModelVersionManager: Model versioning and rollback
- ModelEvaluator: Performance evaluation and comparison
- RetrainingTrigger: Checks conditions for triggering retraining
- RetrainingScheduler: APScheduler integration for automatic retraining

Example:
    >>> from openfatture.ai.ml.retraining import get_retraining_config, RetrainingScheduler
    >>> config = get_retraining_config()
    >>> print(config.enabled)
    False
    >>>
    >>> # Start auto-retraining
    >>> scheduler = RetrainingScheduler()
    >>> scheduler.start()
"""

from openfatture.ai.ml.retraining.config import (
    DEFAULT_RETRAIN_CONFIG,
    RetrainingConfig,
    get_retraining_config,
)
from openfatture.ai.ml.retraining.evaluator import ModelEvaluationResult, ModelEvaluator
from openfatture.ai.ml.retraining.scheduler import RetrainingScheduler, get_scheduler
from openfatture.ai.ml.retraining.triggers import RetrainingTrigger, TriggerReason
from openfatture.ai.ml.retraining.versioning import ModelVersion, ModelVersionManager

__all__ = [
    # Config
    "RetrainingConfig",
    "get_retraining_config",
    "DEFAULT_RETRAIN_CONFIG",
    # Versioning
    "ModelVersionManager",
    "ModelVersion",
    # Evaluation
    "ModelEvaluator",
    "ModelEvaluationResult",
    # Triggers
    "RetrainingTrigger",
    "TriggerReason",
    # Scheduler
    "RetrainingScheduler",
    "get_scheduler",
]
