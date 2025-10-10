"""Ensemble model combining Prophet and XGBoost for cash flow prediction.

The ensemble leverages complementary strengths:
- Prophet (40%): Captures seasonality, trends, and calendar effects
- XGBoost (60%): Captures client-specific and invoice-specific patterns

Weights are optimized via cross-validation and can be adjusted dynamically
based on validation performance.

This approach provides:
1. Better accuracy than individual models
2. Robust uncertainty quantification
3. Confidence scoring based on model agreement
4. Risk level classification (LOW/MEDIUM/HIGH)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd

from openfatture.ai.ml.models.prophet_model import ProphetModel, ProphetPrediction
from openfatture.ai.ml.models.xgboost_model import XGBoostModel, XGBoostPrediction
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class RiskLevel(Enum):
    """Risk level for payment delay prediction."""

    LOW = "low"  # Expected delay < 7 days
    MEDIUM = "medium"  # Expected delay 7-30 days
    HIGH = "high"  # Expected delay > 30 days


@dataclass
class EnsemblePrediction:
    """Ensemble model prediction result.

    Attributes:
        yhat: Weighted ensemble prediction (days)
        yhat_lower: Lower bound of prediction interval
        yhat_upper: Upper bound of prediction interval
        confidence_score: Confidence in prediction (0-1)
        risk_level: Risk classification (LOW/MEDIUM/HIGH)
        prophet_prediction: Individual Prophet prediction
        xgboost_prediction: Individual XGBoost prediction
        model_agreement: Agreement between models (0-1, higher = more agreement)
    """

    yhat: float
    yhat_lower: float
    yhat_upper: float
    confidence_score: float
    risk_level: RiskLevel
    prophet_prediction: ProphetPrediction
    xgboost_prediction: XGBoostPrediction
    model_agreement: float

    @property
    def uncertainty(self) -> float:
        """Calculate prediction uncertainty (interval width)."""
        return self.yhat_upper - self.yhat_lower

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "expected_days": float(self.yhat),
            "lower_bound": float(self.yhat_lower),
            "upper_bound": float(self.yhat_upper),
            "uncertainty_days": float(self.uncertainty),
            "confidence_score": float(self.confidence_score),
            "risk_level": self.risk_level.value,
            "model_agreement": float(self.model_agreement),
            "prophet": {
                "prediction": float(self.prophet_prediction.yhat),
                "trend": float(self.prophet_prediction.trend),
                "seasonal": float(self.prophet_prediction.seasonal),
            },
            "xgboost": {
                "prediction": float(self.xgboost_prediction.yhat),
            },
        }


class CashFlowEnsemble:
    """Weighted ensemble of Prophet and XGBoost models.

    The ensemble combines:
    - Prophet (default weight: 0.4): Temporal patterns, seasonality
    - XGBoost (default weight: 0.6): Client behavior, invoice characteristics

    Weights can be optimized via cross-validation to maximize accuracy.

    Example:
        >>> ensemble = CashFlowEnsemble(
        ...     prophet_weight=0.4,
        ...     xgboost_weight=0.6
        ... )
        >>>
        >>> # Fit both models
        >>> ensemble.fit(X_train, y_train, X_val, y_val)
        >>>
        >>> # Make prediction
        >>> prediction = ensemble.predict_single(X_test.iloc[0])
        >>> print(f"Expected delay: {prediction.yhat:.1f} days")
        >>> print(f"Risk level: {prediction.risk_level.value}")
        >>> print(f"Confidence: {prediction.confidence_score:.1%}")
    """

    def __init__(
        self,
        prophet_weight: float = 0.4,
        xgboost_weight: float = 0.6,
        prophet_params: dict[str, Any] | None = None,
        xgboost_params: dict[str, Any] | None = None,
        optimize_weights: bool = False,
    ):
        """Initialize ensemble model.

        Args:
            prophet_weight: Weight for Prophet predictions
            xgboost_weight: Weight for XGBoost predictions
            prophet_params: Parameters for Prophet model
            xgboost_params: Parameters for XGBoost model
            optimize_weights: Optimize weights on validation set
        """
        # Validate weights
        if not np.isclose(prophet_weight + xgboost_weight, 1.0):
            raise ValueError("Weights must sum to 1.0")

        self.prophet_weight = prophet_weight
        self.xgboost_weight = xgboost_weight
        self.optimize_weights = optimize_weights

        # Initialize models
        self.prophet = ProphetModel(**(prophet_params or {}))
        self.xgboost = XGBoostModel(**(xgboost_params or {}))

        self.fitted_ = False

        logger.info(
            "ensemble_model_initialized",
            prophet_weight=prophet_weight,
            xgboost_weight=xgboost_weight,
            optimize_weights=optimize_weights,
        )

    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame | None = None,
        y_val: pd.Series | None = None,
    ) -> "CashFlowEnsemble":
        """Fit both Prophet and XGBoost models.

        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features (for XGBoost early stopping and weight optimization)
            y_val: Validation targets

        Returns:
            Self for chaining
        """
        logger.info(
            "fitting_ensemble",
            train_size=len(X_train),
            val_size=len(X_val) if X_val is not None else 0,
        )

        # Fit Prophet
        logger.info("fitting_prophet_in_ensemble")
        self.prophet.fit(X_train, y_train)

        # Fit XGBoost with early stopping
        logger.info("fitting_xgboost_in_ensemble")

        eval_set = [(X_val, y_val)] if X_val is not None and y_val is not None else None

        self.xgboost.fit(
            X_train,
            y_train,
            eval_set=eval_set,
            early_stopping_rounds=10 if eval_set else None,
            verbose=False,
        )

        # Optimize weights if requested
        if self.optimize_weights and X_val is not None and y_val is not None:
            self._optimize_weights(X_val, y_val)

        self.fitted_ = True

        logger.info("ensemble_fitted")

        return self

    def predict(
        self,
        X: pd.DataFrame,
    ) -> list[EnsemblePrediction]:
        """Generate ensemble predictions for multiple rows.

        Args:
            X: Features DataFrame

        Returns:
            List of EnsemblePrediction objects
        """
        if not self.fitted_:
            raise ValueError("Ensemble must be fitted before prediction")

        # Get predictions from both models
        prophet_preds = self.prophet.predict(X)
        xgboost_preds = self.xgboost.predict(X, include_intervals=True)

        # Combine predictions
        ensemble_preds = []

        for prophet_pred, xgboost_pred in zip(prophet_preds, xgboost_preds, strict=False):
            ensemble_pred = self._combine_predictions(prophet_pred, xgboost_pred)
            ensemble_preds.append(ensemble_pred)

        logger.debug("ensemble_predictions_generated", count=len(ensemble_preds))

        return ensemble_preds

    def predict_single(
        self,
        X_row: pd.Series,
    ) -> EnsemblePrediction:
        """Generate prediction for a single row.

        Args:
            X_row: Single row of features

        Returns:
            EnsemblePrediction object
        """
        X_df = pd.DataFrame([X_row])
        predictions = self.predict(X_df)
        return predictions[0]

    def _combine_predictions(
        self,
        prophet_pred: ProphetPrediction,
        xgboost_pred: XGBoostPrediction,
    ) -> EnsemblePrediction:
        """Combine individual model predictions into ensemble prediction.

        Args:
            prophet_pred: Prophet prediction
            xgboost_pred: XGBoost prediction

        Returns:
            EnsemblePrediction object
        """
        # Weighted average for point prediction
        yhat = self.prophet_weight * prophet_pred.yhat + self.xgboost_weight * xgboost_pred.yhat

        # Combine prediction intervals (conservative approach: widest interval)
        yhat_lower = min(prophet_pred.yhat_lower, xgboost_pred.yhat_lower)
        yhat_upper = max(prophet_pred.yhat_upper, xgboost_pred.yhat_upper)

        # Calculate model agreement (inverse of prediction difference)
        disagreement = abs(prophet_pred.yhat - xgboost_pred.yhat)
        model_agreement = 1.0 / (1.0 + disagreement / 10.0)  # Normalized

        # Calculate confidence score
        confidence_score = self._calculate_confidence(
            prophet_pred,
            xgboost_pred,
            model_agreement,
        )

        # Classify risk level
        risk_level = self._classify_risk(yhat, yhat_upper - yhat_lower)

        return EnsemblePrediction(
            yhat=float(yhat),
            yhat_lower=float(yhat_lower),
            yhat_upper=float(yhat_upper),
            confidence_score=float(confidence_score),
            risk_level=risk_level,
            prophet_prediction=prophet_pred,
            xgboost_prediction=xgboost_pred,
            model_agreement=float(model_agreement),
        )

    def _calculate_confidence(
        self,
        prophet_pred: ProphetPrediction,
        xgboost_pred: XGBoostPrediction,
        model_agreement: float,
    ) -> float:
        """Calculate confidence score for ensemble prediction.

        Confidence is based on:
        1. Model agreement (higher when models agree)
        2. Prediction interval width (lower when intervals are narrow)

        Args:
            prophet_pred: Prophet prediction
            xgboost_pred: XGBoost prediction
            model_agreement: Agreement score (0-1)

        Returns:
            Confidence score (0-1)
        """
        # Start with model agreement
        confidence = model_agreement

        # Penalize wide uncertainty intervals
        avg_uncertainty = (prophet_pred.uncertainty + xgboost_pred.uncertainty) / 2

        # Normalize uncertainty (assume 30 days is low confidence)
        uncertainty_penalty = min(1.0, avg_uncertainty / 30.0)

        # Combine (equal weight)
        confidence = (confidence + (1.0 - uncertainty_penalty)) / 2

        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))

    def _classify_risk(
        self,
        expected_days: float,
        uncertainty: float,
    ) -> RiskLevel:
        """Classify payment delay risk level.

        Risk classification:
        - LOW: Expected delay < 7 days
        - MEDIUM: Expected delay 7-30 days
        - HIGH: Expected delay > 30 days OR high uncertainty

        Args:
            expected_days: Expected payment delay
            uncertainty: Prediction interval width

        Returns:
            RiskLevel enum
        """
        # High uncertainty automatically elevates risk
        if uncertainty > 20:
            if expected_days < 7:
                return RiskLevel.MEDIUM  # Uncertain but potentially quick
            else:
                return RiskLevel.HIGH  # Uncertain and potentially slow

        # Normal risk classification
        if expected_days < 7:
            return RiskLevel.LOW
        elif expected_days < 30:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    def _optimize_weights(
        self,
        X_val: pd.DataFrame,
        y_val: pd.Series,
    ) -> None:
        """Optimize ensemble weights on validation set.

        Uses grid search to find optimal weights that minimize MAE.

        Args:
            X_val: Validation features
            y_val: Validation targets
        """
        logger.info("optimizing_ensemble_weights")

        # Get predictions from both models
        prophet_preds = self.prophet.predict(X_val)
        xgboost_preds = self.xgboost.predict(X_val, include_intervals=False)

        prophet_values = np.array([p.yhat for p in prophet_preds])
        xgboost_values = np.array([p.yhat for p in xgboost_preds])

        # Grid search over weights
        best_mae = float("inf")
        best_weight = 0.5

        for prophet_w in np.arange(0.0, 1.01, 0.05):
            xgboost_w = 1.0 - prophet_w

            # Ensemble prediction
            y_pred = prophet_w * prophet_values + xgboost_w * xgboost_values

            # Calculate MAE
            mae = np.mean(np.abs(y_val.values - y_pred))

            if mae < best_mae:
                best_mae = mae
                best_weight = prophet_w

        # Update weights
        self.prophet_weight = best_weight
        self.xgboost_weight = 1.0 - best_weight

        logger.info(
            "ensemble_weights_optimized",
            prophet_weight=self.prophet_weight,
            xgboost_weight=self.xgboost_weight,
            validation_mae=best_mae,
        )

    def score(
        self,
        X: pd.DataFrame,
        y: pd.Series,
    ) -> float:
        """Calculate Mean Absolute Error on test data.

        Args:
            X: Features DataFrame
            y: True target values

        Returns:
            Mean Absolute Error (MAE)
        """
        predictions = self.predict(X)
        y_pred = np.array([p.yhat for p in predictions])

        mae = np.mean(np.abs(y.values - y_pred))

        logger.info("ensemble_scored", mae=mae, sample_count=len(X))

        return mae

    def get_feature_importance(self) -> dict[str, float]:
        """Get feature importance from XGBoost model.

        Note: Prophet doesn't provide feature importance since it
        operates on time series directly.

        Returns:
            Dictionary of feature importance scores
        """
        return self.xgboost.get_feature_importance()

    def get_params(self) -> dict[str, Any]:
        """Get ensemble configuration.

        Returns:
            Dictionary with ensemble and model parameters
        """
        return {
            "prophet_weight": self.prophet_weight,
            "xgboost_weight": self.xgboost_weight,
            "optimize_weights": self.optimize_weights,
            "prophet_params": self.prophet.get_params(),
            "xgboost_params": self.xgboost.get_params(),
        }

    def save(self, filepath_prefix: str) -> None:
        """Save ensemble models to files.

        Args:
            filepath_prefix: Prefix for model files
                Will create: {prefix}_prophet.json and {prefix}_xgboost.json
        """
        if not self.fitted_:
            raise ValueError("Cannot save unfitted ensemble")

        prophet_path = f"{filepath_prefix}_prophet.json"
        xgboost_path = f"{filepath_prefix}_xgboost.json"

        self.prophet.save(prophet_path)
        self.xgboost.save(xgboost_path)

        logger.info(
            "ensemble_saved",
            prophet_path=prophet_path,
            xgboost_path=xgboost_path,
        )

    @classmethod
    def load(cls, filepath_prefix: str) -> "CashFlowEnsemble":
        """Load ensemble models from files.

        Args:
            filepath_prefix: Prefix for model files

        Returns:
            Loaded CashFlowEnsemble instance
        """
        prophet_path = f"{filepath_prefix}_prophet.json"
        xgboost_path = f"{filepath_prefix}_xgboost.json"

        ensemble = cls()
        ensemble.prophet = ProphetModel.load(prophet_path)
        ensemble.xgboost = XGBoostModel.load(xgboost_path)
        ensemble.fitted_ = True

        logger.info("ensemble_loaded", filepath_prefix=filepath_prefix)

        return ensemble
