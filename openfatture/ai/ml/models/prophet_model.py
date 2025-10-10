"""Prophet model wrapper for cash flow prediction.

Prophet (Facebook's time series forecasting library) excels at:
- Trend decomposition (linear, logistic)
- Multiple seasonality patterns (daily, weekly, yearly)
- Holiday effects (Italian public holidays)
- Automatic changepoint detection
- Uncertainty intervals

This wrapper adapts Prophet for payment delay prediction by:
1. Converting invoice emission dates to time series format
2. Adding Italian holidays as special events
3. Extracting trend and seasonality components
4. Providing prediction intervals for risk assessment
"""

import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

try:
    from prophet import Prophet
    from prophet.serialize import model_from_json, model_to_json

    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    warnings.warn(
        "Prophet not installed. Install with: pip install prophet",
        ImportWarning,
        stacklevel=2,
    )

from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


# Italian public holidays for Prophet
ITALIAN_HOLIDAYS_DF = pd.DataFrame(
    {
        "holiday": [
            "Capodanno",
            "Epifania",
            "Festa della Liberazione",
            "Festa del Lavoro",
            "Festa della Repubblica",
            "Ferragosto",
            "Ognissanti",
            "Immacolata Concezione",
            "Natale",
            "Santo Stefano",
        ],
        "ds": pd.to_datetime(
            [
                "2020-01-01",
                "2020-01-06",
                "2020-04-25",
                "2020-05-01",
                "2020-06-02",
                "2020-08-15",
                "2020-11-01",
                "2020-12-08",
                "2020-12-25",
                "2020-12-26",
            ]
        ),
        "lower_window": 0,
        "upper_window": 1,  # Holiday effect lasts 1 day
    }
)


@dataclass
class ProphetPrediction:
    """Prophet model prediction result.

    Attributes:
        yhat: Point prediction (expected payment delay days)
        yhat_lower: Lower bound of prediction interval
        yhat_upper: Upper bound of prediction interval
        trend: Trend component
        seasonal: Seasonal component (weekly + yearly)
        holiday: Holiday effect component
    """

    yhat: float
    yhat_lower: float
    yhat_upper: float
    trend: float
    seasonal: float
    holiday: float

    @property
    def uncertainty(self) -> float:
        """Calculate prediction uncertainty (interval width)."""
        return self.yhat_upper - self.yhat_lower


class ProphetModel:
    """Prophet wrapper for payment delay prediction.

    Features:
    - Automatic trend detection with changepoints
    - Multiple seasonality (weekly, yearly)
    - Italian holiday effects
    - Prediction intervals for uncertainty quantification
    - Component analysis (trend, seasonality, holidays)

    Example:
        >>> model = ProphetModel(
        ...     seasonality_mode='multiplicative',
        ...     yearly_seasonality=True,
        ...     weekly_seasonality=True
        ... )
        >>>
        >>> # Fit model
        >>> model.fit(X_train, y_train)
        >>>
        >>> # Make prediction
        >>> prediction = model.predict(X_test.iloc[0])
        >>> print(f"Expected delay: {prediction.yhat:.1f} days")
        >>> print(f"Uncertainty: {prediction.uncertainty:.1f} days")
    """

    def __init__(
        self,
        seasonality_mode: str = "multiplicative",
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = True,
        daily_seasonality: bool = False,
        interval_width: float = 0.80,
        changepoint_prior_scale: float = 0.05,
        seasonality_prior_scale: float = 10.0,
        holidays: pd.DataFrame | None = None,
    ):
        """Initialize Prophet model.

        Args:
            seasonality_mode: 'additive' or 'multiplicative'
            yearly_seasonality: Include yearly seasonality
            weekly_seasonality: Include weekly seasonality
            daily_seasonality: Include daily seasonality (usually False for invoices)
            interval_width: Width of prediction intervals (0.80 = 80%)
            changepoint_prior_scale: Flexibility of trend (higher = more flexible)
            seasonality_prior_scale: Strength of seasonality (higher = stronger)
            holidays: DataFrame of holidays (defaults to Italian holidays)
        """
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet is required. Install with: pip install prophet")

        self.seasonality_mode = seasonality_mode
        self.yearly_seasonality = yearly_seasonality
        self.weekly_seasonality = weekly_seasonality
        self.daily_seasonality = daily_seasonality
        self.interval_width = interval_width
        self.changepoint_prior_scale = changepoint_prior_scale
        self.seasonality_prior_scale = seasonality_prior_scale

        # Use Italian holidays by default
        self.holidays = holidays if holidays is not None else ITALIAN_HOLIDAYS_DF

        self.model: Prophet | None = None
        self.fitted_ = False

        logger.info(
            "prophet_model_initialized",
            seasonality_mode=seasonality_mode,
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
        )

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
    ) -> "ProphetModel":
        """Fit Prophet model on training data.

        Args:
            X: Features DataFrame (must contain 'data_emissione' column)
            y: Target series (payment delay in days)

        Returns:
            Self for chaining
        """
        logger.info("fitting_prophet_model", sample_count=len(X))

        # Convert to Prophet format
        df_prophet = self._to_prophet_format(X, y)

        # Initialize Prophet model
        self.model = Prophet(
            seasonality_mode=self.seasonality_mode,
            yearly_seasonality=self.yearly_seasonality,
            weekly_seasonality=self.weekly_seasonality,
            daily_seasonality=self.daily_seasonality,
            interval_width=self.interval_width,
            changepoint_prior_scale=self.changepoint_prior_scale,
            seasonality_prior_scale=self.seasonality_prior_scale,
            holidays=self.holidays,
        )

        # Fit model
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Suppress Prophet's verbose output
            self.model.fit(df_prophet)

        self.fitted_ = True

        logger.info(
            "prophet_model_fitted",
            changepoints=len(self.model.changepoints),
            trend_changepoint_dates=self.model.changepoints.tolist()[:3],  # Log first 3
        )

        return self

    def predict(
        self,
        X: pd.DataFrame,
    ) -> list[ProphetPrediction]:
        """Generate predictions for new data.

        Args:
            X: Features DataFrame (must contain 'data_emissione' column)

        Returns:
            List of ProphetPrediction objects
        """
        if not self.fitted_:
            raise ValueError("Model must be fitted before prediction")

        # Convert to Prophet format (without target)
        df_prophet = pd.DataFrame({"ds": pd.to_datetime(X["data_emissione"])})

        # Generate forecast
        forecast = self.model.predict(df_prophet)

        # Convert to ProphetPrediction objects
        predictions = []

        for idx, row in forecast.iterrows():
            pred = ProphetPrediction(
                yhat=row["yhat"],
                yhat_lower=row["yhat_lower"],
                yhat_upper=row["yhat_upper"],
                trend=row["trend"],
                seasonal=row.get("weekly", 0) + row.get("yearly", 0),
                holiday=row.get("holidays", 0),
            )
            predictions.append(pred)

        logger.debug(
            "prophet_predictions_generated",
            count=len(predictions),
        )

        return predictions

    def predict_single(
        self,
        X_row: pd.Series,
    ) -> ProphetPrediction:
        """Generate prediction for a single row.

        Args:
            X_row: Single row of features

        Returns:
            ProphetPrediction object
        """
        X_df = pd.DataFrame([X_row])
        predictions = self.predict(X_df)
        return predictions[0]

    def _to_prophet_format(
        self,
        X: pd.DataFrame,
        y: pd.Series | None = None,
    ) -> pd.DataFrame:
        """Convert data to Prophet's required format.

        Prophet expects:
        - 'ds': datetime column
        - 'y': target column

        Args:
            X: Features DataFrame
            y: Optional target series

        Returns:
            DataFrame in Prophet format
        """
        if "data_emissione" not in X.columns:
            raise ValueError("X must contain 'data_emissione' column")

        df = pd.DataFrame({"ds": pd.to_datetime(X["data_emissione"])})

        if y is not None:
            df["y"] = y.values

        return df

    def get_components(
        self,
        X: pd.DataFrame,
    ) -> pd.DataFrame:
        """Get forecast components (trend, seasonality, holidays).

        Useful for understanding which factors drive predictions.

        Args:
            X: Features DataFrame

        Returns:
            DataFrame with components:
            - trend: Long-term trend
            - weekly: Weekly seasonality
            - yearly: Yearly seasonality
            - holidays: Holiday effects
        """
        if not self.fitted_:
            raise ValueError("Model must be fitted before getting components")

        df_prophet = self._to_prophet_format(X)
        forecast = self.model.predict(df_prophet)

        # Extract components
        components = forecast[["ds", "trend", "yhat"]].copy()

        # Add seasonality components if available
        if "weekly" in forecast.columns:
            components["weekly"] = forecast["weekly"]

        if "yearly" in forecast.columns:
            components["yearly"] = forecast["yearly"]

        if "holidays" in forecast.columns:
            components["holidays"] = forecast["holidays"]

        return components

    def get_changepoints(self) -> pd.DataFrame:
        """Get detected trend changepoints.

        Returns:
            DataFrame with changepoint dates and significance
        """
        if not self.fitted_:
            raise ValueError("Model must be fitted before getting changepoints")

        changepoints = pd.DataFrame(
            {"date": self.model.changepoints, "delta": self.model.params["delta"].flatten()}
        )

        return changepoints.sort_values("date")

    def save(self, filepath: str) -> None:
        """Save model to file.

        Args:
            filepath: Path to save model (JSON format)
        """
        if not self.fitted_:
            raise ValueError("Cannot save unfitted model")

        with open(filepath, "w") as f:
            f.write(model_to_json(self.model))

        logger.info("prophet_model_saved", filepath=filepath)

    @classmethod
    def load(cls, filepath: str) -> "ProphetModel":
        """Load model from file.

        Args:
            filepath: Path to saved model

        Returns:
            Loaded ProphetModel instance
        """
        with open(filepath) as f:
            model_json = f.read()

        loaded_model = cls()
        loaded_model.model = model_from_json(model_json)
        loaded_model.fitted_ = True

        logger.info("prophet_model_loaded", filepath=filepath)

        return loaded_model

    def get_params(self) -> dict[str, Any]:
        """Get model hyperparameters.

        Returns:
            Dictionary of hyperparameters
        """
        return {
            "seasonality_mode": self.seasonality_mode,
            "yearly_seasonality": self.yearly_seasonality,
            "weekly_seasonality": self.weekly_seasonality,
            "daily_seasonality": self.daily_seasonality,
            "interval_width": self.interval_width,
            "changepoint_prior_scale": self.changepoint_prior_scale,
            "seasonality_prior_scale": self.seasonality_prior_scale,
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
        predictions = self.predict(X)
        y_pred = np.array([p.yhat for p in predictions])

        mae = np.mean(np.abs(y.values - y_pred))

        logger.info("prophet_model_scored", mae=mae, sample_count=len(X))

        return mae
