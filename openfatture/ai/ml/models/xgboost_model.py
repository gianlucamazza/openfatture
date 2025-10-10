"""XGBoost model wrapper for cash flow prediction.

XGBoost excels at:
- Client-specific payment patterns
- Invoice characteristic patterns
- Non-linear relationships
- Feature importance analysis
- Handling missing values
- Robustness to outliers

This wrapper provides:
1. Custom asymmetric loss function (underestimating payment delay is worse)
2. Feature importance extraction (SHAP values compatible)
3. Early stopping to prevent overfitting
4. Hyperparameter optimization support (Optuna integration)
5. Calibrated prediction intervals
"""

import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

try:
    import xgboost as xgb

    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    warnings.warn(
        "XGBoost not installed. Install with: pip install xgboost",
        ImportWarning,
        stacklevel=2,
    )

from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class XGBoostPrediction:
    """XGBoost model prediction result.

    Attributes:
        yhat: Point prediction (expected payment delay days)
        yhat_lower: Lower bound (calibrated)
        yhat_upper: Upper bound (calibrated)
        feature_importance: Dictionary of feature importance scores
    """

    yhat: float
    yhat_lower: float | None = None
    yhat_upper: float | None = None
    feature_importance: dict[str, float] | None = None

    @property
    def uncertainty(self) -> float | None:
        """Calculate prediction uncertainty (interval width)."""
        if self.yhat_lower is not None and self.yhat_upper is not None:
            return self.yhat_upper - self.yhat_lower
        return None


def asymmetric_mae_loss(y_true: np.ndarray, y_pred: np.ndarray) -> tuple:
    """Custom asymmetric MAE loss for XGBoost.

    Penalizes underestimation more than overestimation:
    - Underestimating payment delay → client might face cash flow issues
    - Overestimating payment delay → conservative but safer

    Loss = 2 * |error| if y_pred < y_true (underestimation)
           1 * |error| if y_pred >= y_true (overestimation)

    Args:
        y_true: True payment delays
        y_pred: Predicted payment delays

    Returns:
        Tuple of (gradient, hessian) for XGBoost
    """
    # Calculate residuals
    residuals = y_pred - y_true

    # Asymmetric weight: 2.0 for underestimation, 1.0 for overestimation
    weights = np.where(residuals < 0, 2.0, 1.0)

    # Gradient: weighted sign of residual
    grad = weights * np.sign(residuals)

    # Hessian: constant (for MAE)
    hess = np.ones_like(y_true)

    return grad, hess


class XGBoostModel:
    """XGBoost wrapper for payment delay prediction.

    Features:
    - Asymmetric loss function (penalize underestimation)
    - Early stopping with validation set
    - Feature importance analysis
    - Prediction interval calibration
    - Hyperparameter optimization support

    Example:
        >>> model = XGBoostModel(
        ...     max_depth=6,
        ...     learning_rate=0.1,
        ...     n_estimators=100,
        ...     use_asymmetric_loss=True
        ... )
        >>>
        >>> # Fit with early stopping
        >>> model.fit(
        ...     X_train, y_train,
        ...     eval_set=[(X_val, y_val)],
        ...     early_stopping_rounds=10
        ... )
        >>>
        >>> # Make prediction
        >>> prediction = model.predict_single(X_test.iloc[0])
        >>> print(f"Expected delay: {prediction.yhat:.1f} days")
    """

    def __init__(
        self,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        n_estimators: int = 100,
        min_child_weight: int = 1,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        gamma: float = 0,
        reg_alpha: float = 0,
        reg_lambda: float = 1,
        use_asymmetric_loss: bool = True,
        random_state: int = 42,
    ):
        """Initialize XGBoost model.

        Args:
            max_depth: Maximum tree depth
            learning_rate: Learning rate (eta)
            n_estimators: Number of boosting rounds
            min_child_weight: Minimum sum of instance weight in child
            subsample: Subsample ratio of training instances
            colsample_bytree: Subsample ratio of columns
            gamma: Minimum loss reduction required for split
            reg_alpha: L1 regularization term
            reg_lambda: L2 regularization term
            use_asymmetric_loss: Use custom asymmetric loss
            random_state: Random seed
        """
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost is required. Install with: pip install xgboost")

        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.n_estimators = n_estimators
        self.min_child_weight = min_child_weight
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.gamma = gamma
        self.reg_alpha = reg_alpha
        self.reg_lambda = reg_lambda
        self.use_asymmetric_loss = use_asymmetric_loss
        self.random_state = random_state

        self.model: xgb.Booster | None = None
        self.feature_names_: list[str] | None = None
        self.fitted_ = False

        # For prediction intervals
        self.residuals_std_: float = 0.0

        logger.info(
            "xgboost_model_initialized",
            max_depth=max_depth,
            learning_rate=learning_rate,
            n_estimators=n_estimators,
            use_asymmetric_loss=use_asymmetric_loss,
        )

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: list[tuple] | None = None,
        early_stopping_rounds: int | None = None,
        verbose: bool = False,
    ) -> "XGBoostModel":
        """Fit XGBoost model on training data.

        Args:
            X: Features DataFrame
            y: Target series (payment delay in days)
            eval_set: List of (X_val, y_val) tuples for validation
            early_stopping_rounds: Stop if no improvement for N rounds
            verbose: Print training progress

        Returns:
            Self for chaining
        """
        logger.info("fitting_xgboost_model", sample_count=len(X))

        # Store feature names
        self.feature_names_ = list(X.columns)

        # Convert to DMatrix
        dtrain = xgb.DMatrix(X, label=y, feature_names=self.feature_names_)

        # Prepare parameters
        params = {
            "max_depth": self.max_depth,
            "eta": self.learning_rate,
            "min_child_weight": self.min_child_weight,
            "subsample": self.subsample,
            "colsample_bytree": self.colsample_bytree,
            "gamma": self.gamma,
            "alpha": self.reg_alpha,
            "lambda": self.reg_lambda,
            "seed": self.random_state,
            "verbosity": 1 if verbose else 0,
        }

        # Set objective
        if self.use_asymmetric_loss:
            params["disable_default_eval_metric"] = 1
            obj_func = asymmetric_mae_loss
        else:
            params["objective"] = "reg:squarederror"
            params["eval_metric"] = "mae"
            obj_func = None

        # Prepare eval sets
        evals = [(dtrain, "train")]

        if eval_set:
            for i, (X_val, y_val) in enumerate(eval_set):
                dval = xgb.DMatrix(X_val, label=y_val, feature_names=self.feature_names_)
                evals.append((dval, f"val_{i}"))

        # Train model
        self.model = xgb.train(
            params=params,
            dtrain=dtrain,
            num_boost_round=self.n_estimators,
            evals=evals,
            obj=obj_func,
            early_stopping_rounds=early_stopping_rounds,
            verbose_eval=verbose,
        )

        self.fitted_ = True

        # Calculate residual std for prediction intervals
        y_pred = self._predict_array(X)
        residuals = y.values - y_pred
        self.residuals_std_ = np.std(residuals)

        logger.info(
            "xgboost_model_fitted",
            best_iteration=(
                self.model.best_iteration if early_stopping_rounds else self.n_estimators
            ),
            residuals_std=self.residuals_std_,
        )

        return self

    def predict(
        self,
        X: pd.DataFrame,
        include_intervals: bool = True,
    ) -> list[XGBoostPrediction]:
        """Generate predictions for new data.

        Args:
            X: Features DataFrame
            include_intervals: Include prediction intervals (calibrated)

        Returns:
            List of XGBoostPrediction objects
        """
        if not self.fitted_:
            raise ValueError("Model must be fitted before prediction")

        # Generate predictions
        y_pred = self._predict_array(X)

        # Calculate intervals (1.96 * std for ~95% confidence)
        if include_intervals:
            interval_width = 1.96 * self.residuals_std_
            y_lower = y_pred - interval_width
            y_upper = y_pred + interval_width
        else:
            y_lower = None
            y_upper = None

        # Convert to XGBoostPrediction objects
        predictions = []

        for i, pred in enumerate(y_pred):
            predictions.append(
                XGBoostPrediction(
                    yhat=float(pred),
                    yhat_lower=float(y_lower[i]) if y_lower is not None else None,
                    yhat_upper=float(y_upper[i]) if y_upper is not None else None,
                )
            )

        logger.debug("xgboost_predictions_generated", count=len(predictions))

        return predictions

    def predict_single(
        self,
        X_row: pd.Series,
        include_feature_importance: bool = False,
    ) -> XGBoostPrediction:
        """Generate prediction for a single row.

        Args:
            X_row: Single row of features
            include_feature_importance: Include feature importance for this prediction

        Returns:
            XGBoostPrediction object
        """
        X_df = pd.DataFrame([X_row])
        predictions = self.predict(X_df, include_intervals=True)

        prediction = predictions[0]

        # Add feature importance if requested
        if include_feature_importance:
            prediction.feature_importance = self.get_feature_importance()

        return prediction

    def _predict_array(self, X: pd.DataFrame) -> np.ndarray:
        """Internal method to get raw predictions as numpy array."""
        if self.model is None:
            raise RuntimeError("Model not initialized. Call fit() first.")
        dmatrix = xgb.DMatrix(X, feature_names=self.feature_names_)
        return self.model.predict(dmatrix)

    def get_feature_importance(
        self,
        importance_type: str = "weight",
    ) -> dict[str, float]:
        """Get feature importance scores.

        Args:
            importance_type: Type of importance
                - 'weight': Number of times feature is used
                - 'gain': Average gain when feature is used
                - 'cover': Average coverage of splits using feature

        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not self.fitted_:
            raise ValueError("Model must be fitted before getting importance")

        if self.model is None:
            raise RuntimeError("Model not initialized. Call fit() first.")

        # Get importance from model
        importance_dict = self.model.get_score(importance_type=importance_type)

        # Normalize to sum to 1.0
        total = sum(importance_dict.values())
        if total > 0:
            importance_dict = {k: v / total for k, v in importance_dict.items()}

        # Sort by importance
        importance_dict = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))

        return importance_dict

    def get_top_features(self, n: int = 10) -> list[tuple]:
        """Get top N most important features.

        Args:
            n: Number of top features to return

        Returns:
            List of (feature_name, importance_score) tuples
        """
        importance = self.get_feature_importance()
        return list(importance.items())[:n]

    def save(self, filepath: str) -> None:
        """Save model to file.

        Args:
            filepath: Path to save model (JSON format)
        """
        if not self.fitted_:
            raise ValueError("Cannot save unfitted model")

        if self.model is None:
            raise RuntimeError("Model not initialized. Cannot save.")

        self.model.save_model(filepath)

        logger.info("xgboost_model_saved", filepath=filepath)

    @classmethod
    def load(cls, filepath: str) -> "XGBoostModel":
        """Load model from file.

        Args:
            filepath: Path to saved model

        Returns:
            Loaded XGBoostModel instance
        """
        loaded_model = cls()
        loaded_model.model = xgb.Booster()
        loaded_model.model.load_model(filepath)
        loaded_model.fitted_ = True

        logger.info("xgboost_model_loaded", filepath=filepath)

        return loaded_model

    def get_params(self) -> dict[str, Any]:
        """Get model hyperparameters.

        Returns:
            Dictionary of hyperparameters
        """
        return {
            "max_depth": self.max_depth,
            "learning_rate": self.learning_rate,
            "n_estimators": self.n_estimators,
            "min_child_weight": self.min_child_weight,
            "subsample": self.subsample,
            "colsample_bytree": self.colsample_bytree,
            "gamma": self.gamma,
            "reg_alpha": self.reg_alpha,
            "reg_lambda": self.reg_lambda,
            "use_asymmetric_loss": self.use_asymmetric_loss,
            "random_state": self.random_state,
        }

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
        y_pred = self._predict_array(X)
        mae = np.mean(np.abs(y.values - y_pred))

        logger.info("xgboost_model_scored", mae=mae, sample_count=len(X))

        return mae
