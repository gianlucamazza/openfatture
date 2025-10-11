"""Feature engineering pipeline for cash flow prediction.

This module implements comprehensive feature extraction for payment prediction ML models.
Features are designed to capture:
- Temporal patterns (seasonality, day of week, holidays)
- Client behavior (historical payment patterns)
- Invoice characteristics (amount, type, VAT)
- Historical trends (rolling statistics)

All features are engineered to be:
- Deterministic (reproducible)
- Versioned (schema tracked)
- Validated (distribution checks)
- Explained (SHAP-compatible)
"""

import statistics
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, cast

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from openfatture.storage.database.base import SessionLocal
from openfatture.storage.database.models import Fattura
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


def _get_session() -> Session:
    """Return a database session, ensuring the engine is initialised."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialised. Call init_db() before using features.")
    return SessionLocal()


# Italian public holidays (fixed dates)
ITALIAN_HOLIDAYS = [
    (1, 1),  # Capodanno
    (1, 6),  # Epifania
    (4, 25),  # Festa della Liberazione
    (5, 1),  # Festa del Lavoro
    (6, 2),  # Festa della Repubblica
    (8, 15),  # Ferragosto
    (11, 1),  # Ognissanti
    (12, 8),  # Immacolata Concezione
    (12, 25),  # Natale
    (12, 26),  # Santo Stefano
]


@dataclass
class FeatureSchema:
    """Feature schema definition for versioning and validation.

    Attributes:
        version: Schema version (semantic versioning)
        features: List of feature names in order
        dtypes: Expected data types for each feature
        nullable: Which features can be null
    """

    version: str = "1.0.0"
    features: list[str] = field(default_factory=list)
    dtypes: dict[str, str] = field(default_factory=dict)
    nullable: dict[str, bool] = field(default_factory=dict)

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate dataframe against schema."""
        # Check all features present
        missing_features = set(self.features) - set(df.columns)
        if missing_features:
            raise ValueError(f"Missing features: {missing_features}")

        # Check dtypes match
        for feature, expected_dtype in self.dtypes.items():
            actual_dtype = str(df[feature].dtype)
            if expected_dtype not in actual_dtype:
                logger.warning(
                    "feature_dtype_mismatch",
                    feature=feature,
                    expected=expected_dtype,
                    actual=actual_dtype,
                )

        # Check nullability
        for feature, can_be_null in self.nullable.items():
            has_nulls = df[feature].isnull().any()
            if has_nulls and not can_be_null:
                raise ValueError(f"Feature {feature} contains nulls but shouldn't")

        return True


class TemporalFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract temporal features from invoice emission date.

    Features extracted:
    - day_of_week (0=Monday, 6=Sunday)
    - day_of_month (1-31)
    - month (1-12)
    - quarter (1-4)
    - is_weekend (boolean)
    - is_holiday (Italian public holidays)
    - days_until_month_end
    - week_of_year (1-53)
    """

    def __init__(self) -> None:
        """Initialize temporal feature extractor."""
        self.feature_names_ = [
            "day_of_week",
            "day_of_month",
            "month",
            "quarter",
            "is_weekend",
            "is_holiday",
            "days_until_month_end",
            "week_of_year",
        ]

    def fit(self, X: Any, y: Any = None) -> "TemporalFeatureExtractor":
        """Fit transformer (no-op for temporal features)."""
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Extract temporal features from date column."""
        X = X.copy()

        # Ensure we have a date column
        if "data_emissione" not in X.columns:
            raise ValueError("Missing 'data_emissione' column")

        # Convert to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(X["data_emissione"]):
            X["data_emissione"] = pd.to_datetime(X["data_emissione"])

        # Extract temporal features
        X["day_of_week"] = X["data_emissione"].dt.dayofweek
        X["day_of_month"] = X["data_emissione"].dt.day
        X["month"] = X["data_emissione"].dt.month
        X["quarter"] = X["data_emissione"].dt.quarter
        X["week_of_year"] = X["data_emissione"].dt.isocalendar().week

        # Weekend detection
        X["is_weekend"] = X["day_of_week"].isin([5, 6]).astype(int)

        # Holiday detection
        X["is_holiday"] = (
            X["data_emissione"].apply(lambda d: (d.month, d.day) in ITALIAN_HOLIDAYS).astype(int)
        )

        # Days until month end
        X["days_until_month_end"] = X["data_emissione"].apply(
            lambda d: (
                (date(d.year, d.month + 1, 1) - timedelta(days=1)).day - d.day
                if d.month < 12
                else (date(d.year + 1, 1, 1) - timedelta(days=1)).day - d.day
            )
        )

        logger.debug(
            "temporal_features_extracted",
            feature_count=len(self.feature_names_),
            sample_count=len(X),
        )

        return X

    def get_feature_names_out(self, input_features: Any = None) -> list[str]:
        """Get output feature names."""
        return self.feature_names_


class ClientBehaviorFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract client historical behavior features.

    Features extracted:
    - avg_payment_delay_30d (average days late in last 30 days)
    - avg_payment_delay_90d (average days late in last 90 days)
    - avg_payment_delay_all (all-time average)
    - payment_velocity (invoices per month)
    - overdue_ratio (% of invoices paid late)
    - client_age_days (days since first invoice)
    - total_invoices_count
    - total_amount_paid (lifetime value)
    """

    def __init__(self) -> None:
        """Initialize client behavior extractor."""
        self.feature_names_ = [
            "avg_payment_delay_30d",
            "avg_payment_delay_90d",
            "avg_payment_delay_all",
            "payment_velocity",
            "overdue_ratio",
            "client_age_days",
            "total_invoices_count",
            "total_amount_paid",
        ]
        self.client_stats_cache_: dict[int, dict[str, float]] = {}

    def fit(self, X: Any, y: Any = None) -> "ClientBehaviorFeatureExtractor":
        """Fit transformer by computing client statistics."""
        # Compute stats for each unique client
        unique_clients = X["cliente_id"].unique()

        db = _get_session()
        try:
            for client_id in unique_clients:
                self.client_stats_cache_[client_id] = self._compute_client_stats(db, client_id)
        finally:
            db.close()

        logger.info(
            "client_behavior_features_fitted",
            unique_clients=len(unique_clients),
        )

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Extract client behavior features."""
        X = X.copy()

        # Apply cached stats to each row
        for feature in self.feature_names_:
            X[feature] = X["cliente_id"].apply(
                lambda cid, feature_name=feature: self.client_stats_cache_.get(cid, {}).get(
                    feature_name, 0.0
                )
            )

        logger.debug(
            "client_behavior_features_extracted",
            feature_count=len(self.feature_names_),
        )

        return X

    def _compute_client_stats(self, db: Session, client_id: int) -> dict[str, float]:
        """Compute historical statistics for a client."""
        # Get all invoices for client
        fatture = (
            db.query(Fattura)
            .filter(Fattura.cliente_id == client_id)
            .order_by(Fattura.data_emissione.desc())
            .all()
        )

        if not fatture:
            return dict.fromkeys(self.feature_names_, 0.0)

        # Get payment data
        payment_delays = []
        paid_late_count = 0
        total_paid = 0.0

        now = datetime.now().date()

        for fattura in fatture:
            if fattura.pagamenti:
                for pagamento in fattura.pagamenti:
                    if pagamento.data_pagamento:
                        # Calculate delay (positive = late, negative = early)
                        delay_days = (pagamento.data_pagamento - pagamento.data_scadenza).days
                        payment_delays.append(delay_days)

                        if delay_days > 0:
                            paid_late_count += 1

                        total_paid += float(pagamento.importo)

        # Calculate stats
        avg_delay_all = statistics.mean(payment_delays) if payment_delays else 0.0

        # Last 30 days
        recent_delays_30 = [
            d
            for d, f in zip(payment_delays, fatture, strict=False)
            if (now - f.data_emissione).days <= 30
        ]
        avg_delay_30 = statistics.mean(recent_delays_30) if recent_delays_30 else avg_delay_all

        # Last 90 days
        recent_delays_90 = [
            d
            for d, f in zip(payment_delays, fatture, strict=False)
            if (now - f.data_emissione).days <= 90
        ]
        avg_delay_90 = statistics.mean(recent_delays_90) if recent_delays_90 else avg_delay_all

        # Overdue ratio
        overdue_ratio = paid_late_count / len(payment_delays) if payment_delays else 0.0

        # Client age
        first_invoice_date = min(f.data_emissione for f in fatture)
        client_age_days = (now - first_invoice_date).days

        # Payment velocity (invoices per month)
        months_active = max(1, client_age_days / 30)
        payment_velocity = len(fatture) / months_active

        return {
            "avg_payment_delay_30d": avg_delay_30,
            "avg_payment_delay_90d": avg_delay_90,
            "avg_payment_delay_all": avg_delay_all,
            "payment_velocity": payment_velocity,
            "overdue_ratio": overdue_ratio,
            "client_age_days": float(client_age_days),
            "total_invoices_count": float(len(fatture)),
            "total_amount_paid": total_paid,
        }

    def get_feature_names_out(self, input_features: Any = None) -> list[str]:
        """Get output feature names."""
        return self.feature_names_


class InvoiceFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract invoice-specific features.

    Features extracted:
    - amount (invoice total)
    - amount_log (log-transformed for normality)
    - amount_zscore (standardized amount)
    - amount_percentile (within client history)
    - has_ritenuta (boolean)
    - ritenuta_percentage
    - has_bollo (boolean)
    - iva_rate (main VAT rate)
    - invoice_type (encoded)
    - line_item_count
    """

    def __init__(self) -> None:
        """Initialize invoice feature extractor."""
        self.feature_names_ = [
            "amount",
            "amount_log",
            "amount_zscore",
            "has_ritenuta",
            "ritenuta_percentage",
            "has_bollo",
            "iva_rate",
            "line_item_count",
        ]
        self.amount_mean_ = 0.0
        self.amount_std_ = 1.0

    def fit(self, X: Any, y: Any = None) -> "InvoiceFeatureExtractor":
        """Fit transformer by computing amount statistics."""
        amounts = X["totale"].astype(float)
        self.amount_mean_ = amounts.mean()
        self.amount_std_ = amounts.std()

        logger.info(
            "invoice_features_fitted",
            amount_mean=self.amount_mean_,
            amount_std=self.amount_std_,
        )

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Extract invoice-specific features."""
        X = X.copy()

        # Amount features
        X["amount"] = X["totale"].astype(float)
        X["amount_log"] = np.log1p(X["amount"])  # log(1 + x) for stability
        X["amount_zscore"] = (X["amount"] - self.amount_mean_) / self.amount_std_

        # Ritenuta features
        X["has_ritenuta"] = (X["ritenuta_acconto"] > 0).astype(int)
        X["ritenuta_percentage"] = X["aliquota_ritenuta"].fillna(0).astype(float)

        # Bollo
        X["has_bollo"] = (X["importo_bollo"] > 0).astype(int)

        # IVA rate (main rate - most common in invoice)
        X["iva_rate"] = X["iva"].astype(float) / X["imponibile"].astype(float) * 100
        X["iva_rate"] = X["iva_rate"].fillna(0)

        # Line item count (proxy for complexity)
        # Note: This requires righe relationship to be loaded
        # For now, set to 0 if not available
        if "righe" not in X.columns:
            X["line_item_count"] = 0
        else:
            X["line_item_count"] = X["righe"].apply(lambda righe: len(righe) if righe else 0)

        logger.debug(
            "invoice_features_extracted",
            feature_count=len(self.feature_names_),
        )

        return X

    def get_feature_names_out(self, input_features: Any = None) -> list[str]:
        """Get output feature names."""
        return self.feature_names_


class FeaturePipeline:
    """Complete feature engineering pipeline.

    Combines all feature extractors into a scikit-learn Pipeline
    for reproducible and maintainable feature engineering.

    Example:
        >>> pipeline = FeaturePipeline()
        >>> pipeline.fit(X_train)
        >>> X_features = pipeline.transform(X_train)
        >>> X_test_features = pipeline.transform(X_test)
    """

    def __init__(
        self,
        include_temporal: bool = True,
        include_client_behavior: bool = True,
        include_invoice: bool = True,
        scale_features: bool = True,
    ):
        """Initialize feature pipeline.

        Args:
            include_temporal: Include temporal features
            include_client_behavior: Include client behavior features
            include_invoice: Include invoice-specific features
            scale_features: Apply StandardScaler to final features
        """
        self.include_temporal = include_temporal
        self.include_client_behavior = include_client_behavior
        self.include_invoice = include_invoice
        self.scale_features = scale_features

        # Build pipeline
        steps: list[tuple[str, TransformerMixin]] = []

        if include_temporal:
            steps.append(("temporal", TemporalFeatureExtractor()))

        if include_client_behavior:
            steps.append(("client_behavior", ClientBehaviorFeatureExtractor()))

        if include_invoice:
            steps.append(("invoice", InvoiceFeatureExtractor()))

        # Note: Scaling applied separately to avoid scaling categorical features

        self.pipeline = Pipeline(steps)
        self.scaler = StandardScaler() if scale_features else None
        self.fitted_ = False

        logger.info(
            "feature_pipeline_initialized",
            steps=len(steps),
            scale_features=scale_features,
        )

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "FeaturePipeline":
        """Fit all feature extractors.

        Args:
            X: Input dataframe with invoice data
            y: Optional target variable (payment delay days)

        Returns:
            Self for chaining
        """
        logger.info("fitting_feature_pipeline", sample_count=len(X))

        # Fit pipeline
        self.pipeline.fit(X, y)

        # Fit scaler if enabled
        if self.scaler:
            X_transformed = cast(pd.DataFrame, self.pipeline.transform(X))
            numerical_features = self._get_numerical_features(X_transformed)
            self.scaler.fit(X_transformed[numerical_features])

        self.fitted_ = True

        logger.info("feature_pipeline_fitted")

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform input data to features.

        Args:
            X: Input dataframe with invoice data

        Returns:
            Dataframe with extracted and scaled features
        """
        if not self.fitted_:
            raise ValueError("Pipeline must be fitted before transform")

        # Apply feature extraction
        X_features = cast(pd.DataFrame, self.pipeline.transform(X))

        # Apply scaling if enabled
        if self.scaler:
            numerical_features = self._get_numerical_features(X_features)
            X_features[numerical_features] = self.scaler.transform(X_features[numerical_features])

        logger.debug(
            "features_transformed",
            sample_count=len(X_features),
            feature_count=len(X_features.columns),
        )

        return X_features

    def fit_transform(self, X: pd.DataFrame, y: pd.Series | None = None) -> pd.DataFrame:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)

    def _get_numerical_features(self, X: pd.DataFrame) -> list[str]:
        """Get list of numerical feature columns."""
        numerical_features = []

        for col in X.columns:
            if pd.api.types.is_numeric_dtype(X[col]):
                numerical_features.append(col)

        return numerical_features

    def get_feature_names(self) -> list[str]:
        """Get all feature names in order."""
        if not self.fitted_:
            raise ValueError("Pipeline must be fitted before getting feature names")

        feature_names = []

        for name, transformer in self.pipeline.steps:
            if hasattr(transformer, "feature_names_"):
                feature_names.extend(transformer.feature_names_)

        return feature_names

    def get_schema(self) -> FeatureSchema:
        """Get feature schema for versioning."""
        feature_names = self.get_feature_names()

        # Determine dtypes and nullability
        dtypes = {}
        nullable = {}

        for feature in feature_names:
            # Determine expected dtype
            if feature.startswith("is_") or feature.startswith("has_"):
                dtypes[feature] = "int"
                nullable[feature] = False
            elif "count" in feature:
                dtypes[feature] = "int"
                nullable[feature] = False
            else:
                dtypes[feature] = "float"
                nullable[feature] = False

        return FeatureSchema(
            version="1.0.0",
            features=feature_names,
            dtypes=dtypes,
            nullable=nullable,
        )
