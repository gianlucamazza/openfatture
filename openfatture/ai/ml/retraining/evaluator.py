"""Model Performance Evaluation and Comparison.

Evaluates ML models on validation data and determines if new models
should be deployed based on performance thresholds and improvement criteria.

Example:
    >>> from openfatture.ai.ml.retraining import ModelEvaluator
    >>> evaluator = ModelEvaluator()
    >>>
    >>> # Evaluate new model vs current
    >>> should_deploy, metrics = evaluator.evaluate_and_compare(
    ...     new_model=new_ensemble,
    ...     current_model=current_ensemble,
    ...     X_val=X_val,
    ...     y_val=y_val,
    ... )
    >>>
    >>> if should_deploy:
    ...     # Deploy new model
    ...     pass
"""

from typing import Any

import numpy as np
import pandas as pd

from openfatture.ai.ml.models import CashFlowEnsemble
from openfatture.ai.ml.retraining.config import get_retraining_config
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class ModelEvaluationResult:
    """Result from model evaluation.

    Attributes:
        metrics: Performance metrics dict
        should_deploy: Whether model should be deployed
        deployment_reason: Reason for deployment decision
        comparison: Comparison metrics vs current model
    """

    def __init__(
        self,
        metrics: dict[str, Any],
        should_deploy: bool,
        deployment_reason: str,
        comparison: dict[str, Any] | None = None,
    ):
        """Initialize evaluation result."""
        self.metrics = metrics
        self.should_deploy = should_deploy
        self.deployment_reason = deployment_reason
        self.comparison = comparison or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metrics": self.metrics,
            "should_deploy": self.should_deploy,
            "deployment_reason": self.deployment_reason,
            "comparison": self.comparison,
        }


class ModelEvaluator:
    """Evaluates and compares ML model performance.

    Determines if new models should be deployed based on:
    - Performance improvement over current model
    - Performance degradation thresholds
    - Minimum confidence requirements
    - Validation set evaluation

    Example:
        >>> evaluator = ModelEvaluator()
        >>> result = evaluator.evaluate_and_compare(
        ...     new_model, current_model, X_val, y_val
        ... )
        >>> if result.should_deploy:
        ...     print(result.deployment_reason)
    """

    def __init__(self):
        """Initialize model evaluator."""
        self.config = get_retraining_config()
        logger.info("model_evaluator_initialized")

    def evaluate_model(
        self,
        model: CashFlowEnsemble,
        X_val: pd.DataFrame,
        y_val: pd.Series,
    ) -> dict[str, Any]:
        """Evaluate a model on validation data.

        Args:
            model: Trained ensemble model
            X_val: Validation features
            y_val: Validation targets

        Returns:
            Dictionary of performance metrics
        """
        if len(X_val) == 0 or len(y_val) == 0:
            logger.warning("empty_validation_set")
            return {
                "mae": float("inf"),
                "rmse": float("inf"),
                "r2": 0.0,
                "mape": float("inf"),
                "coverage": 0.0,
                "median_interval_width": 0.0,
                "avg_confidence": 0.0,
                "samples": 0,
            }

        # Make predictions
        predictions = model.predict(X_val)
        y_true = y_val.to_numpy(dtype=float)
        y_pred = np.array([pred.yhat for pred in predictions], dtype=float)

        # Calculate residuals
        residuals = y_true - y_pred

        # Core metrics
        mae = float(np.mean(np.abs(residuals)))
        rmse = float(np.sqrt(np.mean(np.square(residuals))))
        median_abs_error = float(np.median(np.abs(residuals)))

        # R² score
        ss_res = np.sum(np.square(residuals))
        ss_tot = np.sum(np.square(y_true - np.mean(y_true)))
        r2 = float(1 - (ss_res / ss_tot)) if ss_tot != 0 else 0.0

        # MAPE (Mean Absolute Percentage Error)
        # Avoid division by zero
        non_zero_mask = y_true != 0
        if np.any(non_zero_mask):
            mape = float(np.mean(np.abs(residuals[non_zero_mask] / y_true[non_zero_mask])) * 100)
        else:
            mape = float("inf")

        # Prediction interval coverage and confidence
        coverages = []
        interval_widths = []
        confidence_scores = []

        for target, pred in zip(y_true, predictions, strict=False):
            if pred.yhat_lower is not None and pred.yhat_upper is not None:
                interval_widths.append(pred.uncertainty)
                coverages.append(pred.yhat_lower <= target <= pred.yhat_upper)

            if pred.confidence_score is not None:
                confidence_scores.append(pred.confidence_score)

        coverage = float(np.mean(coverages)) if coverages else 0.0
        median_interval_width = float(np.median(interval_widths)) if interval_widths else 0.0
        avg_confidence = float(np.mean(confidence_scores)) if confidence_scores else 0.0

        metrics = {
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
            "mape": mape,
            "median_abs_error": median_abs_error,
            "coverage": coverage,
            "median_interval_width": median_interval_width,
            "avg_confidence": avg_confidence,
            "samples": int(len(X_val)),
        }

        logger.info("model_evaluated", metrics=metrics)

        return metrics

    def compare_models(
        self,
        new_metrics: dict[str, Any],
        current_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """Compare metrics between new and current models.

        Args:
            new_metrics: Metrics from new model
            current_metrics: Metrics from current model

        Returns:
            Dictionary with comparison results and percentage changes
        """
        comparison = {}

        # Compare each metric
        for metric in ["mae", "rmse", "r2", "mape", "avg_confidence"]:
            if metric not in new_metrics or metric not in current_metrics:
                continue

            new_val = new_metrics[metric]
            current_val = current_metrics[metric]

            # For MAE, RMSE, MAPE: lower is better
            # For R², confidence: higher is better
            if metric in ["mae", "rmse", "mape"]:
                improvement_pct = (
                    ((current_val - new_val) / current_val * 100) if current_val != 0 else 0.0
                )
                is_better = new_val < current_val
            else:  # r2, confidence
                improvement_pct = (
                    ((new_val - current_val) / abs(current_val) * 100) if current_val != 0 else 0.0
                )
                is_better = new_val > current_val

            comparison[metric] = {
                "new": new_val,
                "current": current_val,
                "improvement_pct": improvement_pct,
                "is_better": is_better,
            }

        logger.info("models_compared", comparison=comparison)

        return comparison

    def should_deploy_model(
        self,
        new_metrics: dict[str, Any],
        current_metrics: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """Determine if new model should be deployed.

        Args:
            new_metrics: Metrics from new model
            current_metrics: Metrics from current model (None if first model)

        Returns:
            Tuple of (should_deploy, reason)
        """
        # If no current model, deploy if meets minimum requirements
        if current_metrics is None:
            if new_metrics["avg_confidence"] < self.config.min_confidence_for_deployment:
                return False, (
                    f"Confidence {new_metrics['avg_confidence']:.2%} below threshold "
                    f"{self.config.min_confidence_for_deployment:.2%}"
                )
            return True, "First model deployment"

        # Compare models
        comparison = self.compare_models(new_metrics, current_metrics)

        # Get primary metric
        primary_metric = self.config.primary_metric
        if primary_metric not in comparison:
            return False, f"Primary metric '{primary_metric}' not found in comparison"

        primary_comparison = comparison[primary_metric]

        # Check for performance degradation
        if not primary_comparison["is_better"]:
            degradation_pct = abs(primary_comparison["improvement_pct"])
            if degradation_pct > self.config.performance_degradation_threshold * 100:
                return False, (
                    f"Performance degraded by {degradation_pct:.1f}% "
                    f"(threshold: {self.config.performance_degradation_threshold * 100:.1f}%)"
                )

        # Check if improvement required
        if self.config.require_improvement_for_deployment:
            if not primary_comparison["is_better"]:
                return False, f"No improvement in {primary_metric}"

            improvement_pct = primary_comparison["improvement_pct"]
            min_improvement = self.config.min_improvement_percentage * 100

            if improvement_pct < min_improvement:
                return False, (
                    f"Improvement {improvement_pct:.1f}% below threshold {min_improvement:.1f}%"
                )

        # Check confidence threshold
        if new_metrics["avg_confidence"] < self.config.min_confidence_for_deployment:
            return False, (
                f"Confidence {new_metrics['avg_confidence']:.2%} below threshold "
                f"{self.config.min_confidence_for_deployment:.2%}"
            )

        # All checks passed
        improvement_pct = primary_comparison["improvement_pct"]
        return True, f"Improved {primary_metric} by {improvement_pct:.1f}%"

    def evaluate_and_compare(
        self,
        new_model: CashFlowEnsemble,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        current_model: CashFlowEnsemble | None = None,
    ) -> ModelEvaluationResult:
        """Evaluate new model and compare against current.

        Args:
            new_model: New trained model
            X_val: Validation features
            y_val: Validation targets
            current_model: Current deployed model (optional)

        Returns:
            ModelEvaluationResult with deployment decision
        """
        # Evaluate new model
        new_metrics = self.evaluate_model(new_model, X_val, y_val)

        # Evaluate current model if provided
        current_metrics = None
        if current_model is not None:
            current_metrics = self.evaluate_model(current_model, X_val, y_val)

        # Determine deployment
        should_deploy, reason = self.should_deploy_model(new_metrics, current_metrics)

        # Build comparison
        comparison = {}
        if current_metrics is not None:
            comparison = self.compare_models(new_metrics, current_metrics)

        result = ModelEvaluationResult(
            metrics=new_metrics,
            should_deploy=should_deploy,
            deployment_reason=reason,
            comparison=comparison,
        )

        logger.info(
            "evaluation_completed",
            should_deploy=should_deploy,
            reason=reason,
            new_mae=new_metrics.get("mae"),
            current_mae=current_metrics.get("mae") if current_metrics else None,
        )

        return result
