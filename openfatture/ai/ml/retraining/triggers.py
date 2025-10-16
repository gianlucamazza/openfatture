"""Retraining Trigger Logic.

Determines when ML models should be retrained based on:
- Feedback accumulation (number of unprocessed feedback)
- Time since last training
- Model performance drift

Example:
    >>> from openfatture.ai.ml.retraining import RetrainingTrigger
    >>> trigger = RetrainingTrigger()
    >>>
    >>> # Check if retraining should be triggered
    >>> should_retrain, reasons = trigger.should_trigger_retraining("cash_flow")
    >>>
    >>> if should_retrain:
    ...     print("Retraining triggered:", reasons)
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from openfatture.ai.feedback.service import FeedbackService
from openfatture.ai.ml.config import get_ml_config
from openfatture.ai.ml.retraining.config import get_retraining_config
from openfatture.storage.database.models import PredictionType
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class TriggerReason:
    """Reason for triggering retraining.

    Attributes:
        trigger_type: Type of trigger (feedback_count, time_elapsed, accuracy_drift)
        message: Human-readable message
        metadata: Additional metadata about the trigger
    """

    def __init__(self, trigger_type: str, message: str, metadata: dict[str, Any] | None = None):
        """Initialize trigger reason."""
        self.trigger_type = trigger_type
        self.message = message
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trigger_type": self.trigger_type,
            "message": self.message,
            "metadata": self.metadata,
        }


class RetrainingTrigger:
    """Determines when to trigger model retraining.

    Checks multiple conditions:
    1. Feedback count: Enough unprocessed feedback accumulated
    2. Time elapsed: Sufficient time since last training
    3. Accuracy drift: Performance degradation detected

    Example:
        >>> trigger = RetrainingTrigger()
        >>> should_retrain, reasons = trigger.should_trigger_retraining("cash_flow")
        >>> if should_retrain:
        ...     for reason in reasons:
        ...         print(reason.message)
    """

    def __init__(self):
        """Initialize retraining trigger."""
        self.ml_config = get_ml_config()
        self.retrain_config = get_retraining_config()
        self.feedback_service = FeedbackService()

        logger.info("retraining_trigger_initialized")

    def should_trigger_retraining(
        self, model_name: str = "cash_flow"
    ) -> tuple[bool, list[TriggerReason]]:
        """Check if retraining should be triggered.

        Args:
            model_name: Name of the model to check

        Returns:
            Tuple of (should_trigger, list_of_reasons)
        """
        reasons = []

        # Check feedback count
        feedback_reason = self._check_feedback_count()
        if feedback_reason:
            reasons.append(feedback_reason)

        # Check time since last training
        time_reason = self._check_time_elapsed(model_name)
        if time_reason:
            reasons.append(time_reason)

        # Check accuracy drift
        drift_reason = self._check_accuracy_drift(model_name)
        if drift_reason:
            reasons.append(drift_reason)

        should_trigger = len(reasons) > 0

        if should_trigger:
            logger.info(
                "retraining_triggered",
                model_name=model_name,
                reason_count=len(reasons),
                reasons=[r.trigger_type for r in reasons],
            )
        else:
            logger.debug("retraining_not_triggered", model_name=model_name)

        return should_trigger, reasons

    def _check_feedback_count(self) -> TriggerReason | None:
        """Check if enough unprocessed feedback exists.

        Returns:
            TriggerReason if threshold exceeded, None otherwise
        """
        # Get unprocessed prediction feedback for cash flow predictions
        unprocessed = self.feedback_service.get_unprocessed_predictions(
            prediction_type=PredictionType.INVOICE_DELAY
        )

        count = len(unprocessed)

        if count >= self.retrain_config.min_feedback_count:
            return TriggerReason(
                trigger_type="feedback_count",
                message=(
                    f"Accumulated {count} unprocessed feedback samples "
                    f"(threshold: {self.retrain_config.min_feedback_count})"
                ),
                metadata={
                    "feedback_count": count,
                    "threshold": self.retrain_config.min_feedback_count,
                },
            )

        return None

    def _check_time_elapsed(self, model_name: str) -> TriggerReason | None:
        """Check if enough time has passed since last training.

        Args:
            model_name: Name of the model

        Returns:
            TriggerReason if threshold exceeded, None otherwise
        """
        # Get last training time from model metrics
        model_path = self.ml_config.get_model_filepath(model_name)
        metrics_path = Path(f"{model_path}_metrics.json")

        if not metrics_path.exists():
            # No existing model, trigger training
            return TriggerReason(
                trigger_type="time_elapsed",
                message="No existing model found, initial training required",
                metadata={"is_initial_training": True},
            )

        try:
            with metrics_path.open("r", encoding="utf-8") as f:
                metrics_data = json.load(f)

            trained_at_str = metrics_data.get("trained_at")
            if not trained_at_str:
                return None

            trained_at = datetime.fromisoformat(trained_at_str)
            now = datetime.now(UTC)
            days_elapsed = (now - trained_at).days

            if days_elapsed >= self.retrain_config.max_days_since_training:
                return TriggerReason(
                    trigger_type="time_elapsed",
                    message=(
                        f"{days_elapsed} days since last training "
                        f"(threshold: {self.retrain_config.max_days_since_training} days)"
                    ),
                    metadata={
                        "days_elapsed": days_elapsed,
                        "threshold": self.retrain_config.max_days_since_training,
                        "trained_at": trained_at_str,
                    },
                )

        except Exception as e:
            logger.warning("failed_to_check_training_time", error=str(e))

        return None

    def _check_accuracy_drift(self, model_name: str) -> TriggerReason | None:
        """Check if model accuracy has drifted.

        Note: This is a placeholder for future implementation.
        Requires tracking validation metrics over time.

        Args:
            model_name: Name of the model

        Returns:
            TriggerReason if drift detected, None otherwise
        """
        # TODO: Implement accuracy drift detection
        # This would require:
        # 1. Periodic evaluation on a hold-out validation set
        # 2. Tracking metrics over time in a time series
        # 3. Detecting significant degradation (e.g., MAE increase > 5%)
        #
        # For now, return None (not implemented)
        return None

    def get_trigger_summary(self, model_name: str = "cash_flow") -> dict[str, Any]:
        """Get a summary of current trigger status.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary with trigger status and details
        """
        should_trigger, reasons = self.should_trigger_retraining(model_name)

        # Get detailed stats
        unprocessed_count = len(
            self.feedback_service.get_unprocessed_predictions(
                prediction_type=PredictionType.INVOICE_DELAY
            )
        )

        # Get last training time
        model_path = self.ml_config.get_model_filepath(model_name)
        metrics_path = Path(f"{model_path}_metrics.json")

        last_training_time = None
        days_since_training = None

        if metrics_path.exists():
            try:
                with metrics_path.open("r", encoding="utf-8") as f:
                    metrics_data = json.load(f)
                    last_training_time = metrics_data.get("trained_at")

                    if last_training_time:
                        trained_at = datetime.fromisoformat(last_training_time)
                        now = datetime.now(UTC)
                        days_since_training = (now - trained_at).days

            except Exception as e:
                logger.warning("failed_to_load_training_time", error=str(e))

        summary = {
            "should_trigger": should_trigger,
            "trigger_count": len(reasons),
            "triggers": [r.to_dict() for r in reasons],
            "feedback_stats": {
                "unprocessed_count": unprocessed_count,
                "threshold": self.retrain_config.min_feedback_count,
                "ready": unprocessed_count >= self.retrain_config.min_feedback_count,
            },
            "time_stats": {
                "last_training": last_training_time,
                "days_since_training": days_since_training,
                "threshold_days": self.retrain_config.max_days_since_training,
                "ready": (
                    days_since_training >= self.retrain_config.max_days_since_training
                    if days_since_training is not None
                    else False
                ),
            },
        }

        return summary
