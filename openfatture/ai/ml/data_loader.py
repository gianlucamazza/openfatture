"""Data loading and preprocessing for cash flow prediction models.

This module handles:
- Historical invoice and payment data extraction from database
- Target variable creation (payment delay in days)
- Train/validation/test split (chronological for time series)
- Missing value imputation
- Data quality validation
- Dataset versioning and caching

All data splits are chronological to prevent data leakage and ensure
realistic evaluation of time series models.
"""

import pickle
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import and_

from openfatture.storage.database.base import SessionLocal
from openfatture.storage.database.models import Fattura, StatoFattura
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DatasetMetadata:
    """Metadata for a loaded dataset.

    Attributes:
        version: Dataset version
        created_at: When dataset was created
        train_size: Number of training samples
        val_size: Number of validation samples
        test_size: Number of test samples
        date_range: (start_date, end_date)
        target_mean: Mean target value
        target_std: Standard deviation of target
        missing_payment_ratio: Ratio of invoices without payment data
    """

    version: str
    created_at: datetime
    train_size: int
    val_size: int
    test_size: int
    date_range: tuple[date, date]
    target_mean: float
    target_std: float
    missing_payment_ratio: float


@dataclass
class Dataset:
    """Container for train/val/test splits.

    Attributes:
        X_train: Training features
        y_train: Training targets
        X_val: Validation features
        y_val: Validation targets
        X_test: Test features
        y_test: Test targets
        metadata: Dataset metadata
    """

    X_train: pd.DataFrame
    y_train: pd.Series
    X_val: pd.DataFrame
    y_val: pd.Series
    X_test: pd.DataFrame
    y_test: pd.Series
    metadata: DatasetMetadata


class InvoiceDataLoader:
    """Load and preprocess invoice data for ML models.

    Features:
    - Chronological train/val/test split
    - Automatic target variable creation
    - Missing value handling
    - Data quality validation
    - Caching for performance

    Example:
        >>> loader = InvoiceDataLoader()
        >>> dataset = loader.load_dataset(
        ...     min_date=date(2023, 1, 1),
        ...     max_date=date(2024, 12, 31)
        ... )
        >>> print(f"Train: {len(dataset.X_train)}, Val: {len(dataset.X_val)}")
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        min_payment_data_ratio: float = 0.3,
    ):
        """Initialize data loader.

        Args:
            cache_dir: Directory for caching preprocessed datasets
            min_payment_data_ratio: Minimum ratio of invoices with payment data
        """
        self.cache_dir = cache_dir or Path(".cache/ml_data")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.min_payment_data_ratio = min_payment_data_ratio

        logger.info(
            "invoice_data_loader_initialized",
            cache_dir=str(self.cache_dir),
        )

    def load_dataset(
        self,
        min_date: date | None = None,
        max_date: date | None = None,
        val_split: float = 0.15,
        test_split: float = 0.15,
        force_reload: bool = False,
    ) -> Dataset:
        """Load and split dataset chronologically.

        Args:
            min_date: Minimum invoice emission date (default: 2 years ago)
            max_date: Maximum invoice emission date (default: today)
            val_split: Validation set ratio
            test_split: Test set ratio
            force_reload: Force reload from database (ignore cache)

        Returns:
            Dataset with train/val/test splits

        Raises:
            ValueError: If insufficient payment data available
        """
        # Set date defaults
        if max_date is None:
            max_date = datetime.now().date()

        if min_date is None:
            min_date = max_date - timedelta(days=730)  # 2 years

        logger.info(
            "loading_dataset",
            min_date=str(min_date),
            max_date=str(max_date),
            val_split=val_split,
            test_split=test_split,
        )

        # Check cache
        cache_key = self._get_cache_key(min_date, max_date, val_split, test_split)
        cache_path = self.cache_dir / f"{cache_key}.pkl"

        if cache_path.exists() and not force_reload:
            logger.info("loading_from_cache", cache_path=str(cache_path))
            with open(cache_path, "rb") as f:
                return pickle.load(f)

        # Load from database
        df = self._load_invoices_from_db(min_date, max_date)

        # Validate data quality
        self._validate_data_quality(df)

        # Create target variable (payment delay)
        df = self._create_target_variable(df)

        # Remove rows without target (no payment data)
        df_with_target = df[df["target"].notna()].copy()

        logger.info(
            "dataset_loaded",
            total_invoices=len(df),
            with_payment_data=len(df_with_target),
            payment_data_ratio=len(df_with_target) / len(df),
        )

        # Check minimum payment data ratio
        payment_ratio = len(df_with_target) / len(df)
        if payment_ratio < self.min_payment_data_ratio:
            raise ValueError(
                f"Insufficient payment data: {payment_ratio:.1%} "
                f"(minimum: {self.min_payment_data_ratio:.1%})"
            )

        # Chronological split
        dataset = self._chronological_split(
            df_with_target,
            val_split=val_split,
            test_split=test_split,
        )

        # Cache dataset
        with open(cache_path, "wb") as f:
            pickle.dump(dataset, f)

        logger.info("dataset_cached", cache_path=str(cache_path))

        return dataset

    def _load_invoices_from_db(
        self,
        min_date: date,
        max_date: date,
    ) -> pd.DataFrame:
        """Load invoice data from database.

        Args:
            min_date: Minimum emission date
            max_date: Maximum emission date

        Returns:
            DataFrame with invoice data
        """
        db = SessionLocal()

        try:
            # Query invoices with payments and client data
            fatture = (
                db.query(Fattura)
                .filter(
                    and_(
                        Fattura.data_emissione >= min_date,
                        Fattura.data_emissione <= max_date,
                        Fattura.stato != StatoFattura.BOZZA,  # Exclude drafts
                    )
                )
                .order_by(Fattura.data_emissione.asc())
                .all()
            )

            logger.info("invoices_loaded_from_db", count=len(fatture))

            # Convert to DataFrame
            records = []

            for fattura in fatture:
                # Get payment information
                payment_date = None
                payment_due_date = None
                payment_amount = None

                if fattura.pagamenti:
                    # Use first payment for simplicity
                    # In production, handle multiple payments
                    first_payment = fattura.pagamenti[0]
                    payment_date = first_payment.data_pagamento
                    payment_due_date = first_payment.data_scadenza
                    payment_amount = float(first_payment.importo)

                records.append(
                    {
                        # Invoice data
                        "invoice_id": fattura.id,
                        "cliente_id": fattura.cliente_id,
                        "data_emissione": fattura.data_emissione,
                        "totale": float(fattura.totale),
                        "imponibile": float(fattura.imponibile),
                        "iva": float(fattura.iva),
                        "ritenuta_acconto": float(fattura.ritenuta_acconto or 0),
                        "aliquota_ritenuta": float(fattura.aliquota_ritenuta or 0),
                        "importo_bollo": float(fattura.importo_bollo),
                        "tipo_documento": fattura.tipo_documento.value,
                        "stato": fattura.stato.value,
                        # Payment data
                        "payment_date": payment_date,
                        "payment_due_date": payment_due_date,
                        "payment_amount": payment_amount,
                        # Will be populated by feature engineering
                        "righe": len(fattura.righe) if fattura.righe else 0,
                    }
                )

            df = pd.DataFrame(records)

            # Convert dates to datetime
            df["data_emissione"] = pd.to_datetime(df["data_emissione"])
            if "payment_date" in df.columns:
                df["payment_date"] = pd.to_datetime(df["payment_date"])
            if "payment_due_date" in df.columns:
                df["payment_due_date"] = pd.to_datetime(df["payment_due_date"])

            return df

        finally:
            db.close()

    def _create_target_variable(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create target variable (payment delay in days).

        Target = payment_date - payment_due_date (in days)
        - Positive values = paid late
        - Negative values = paid early
        - NaN = not yet paid or no payment data

        Args:
            df: DataFrame with invoice and payment data

        Returns:
            DataFrame with 'target' column added
        """
        df = df.copy()

        # Calculate payment delay
        df["target"] = np.nan

        # Only calculate for invoices with both payment_date and payment_due_date
        mask = df["payment_date"].notna() & df["payment_due_date"].notna()

        if mask.any():
            df.loc[mask, "target"] = (
                df.loc[mask, "payment_date"] - df.loc[mask, "payment_due_date"]
            ).dt.days.astype(float)

        logger.info(
            "target_variable_created",
            total_invoices=len(df),
            with_target=mask.sum(),
            target_mean=df["target"].mean(),
            target_std=df["target"].std(),
        )

        return df

    def _chronological_split(
        self,
        df: pd.DataFrame,
        val_split: float,
        test_split: float,
    ) -> Dataset:
        """Split dataset chronologically (time series split).

        Important: We use chronological split to prevent data leakage.
        The model is trained on older data and evaluated on newer data,
        which mimics real-world usage.

        Args:
            df: DataFrame with features and target
            val_split: Validation set ratio
            test_split: Test set ratio

        Returns:
            Dataset with train/val/test splits
        """
        # Sort by date to ensure chronological order
        df = df.sort_values("data_emissione").reset_index(drop=True)

        # Calculate split indices
        n = len(df)
        test_size = int(n * test_split)
        val_size = int(n * val_split)
        train_size = n - val_size - test_size

        # Split chronologically
        train_df = df.iloc[:train_size].copy()
        val_df = df.iloc[train_size : train_size + val_size].copy()
        test_df = df.iloc[train_size + val_size :].copy()

        # Separate features and target
        feature_cols = [
            col for col in df.columns if col not in ["target", "invoice_id", "payment_date"]
        ]

        X_train = train_df[feature_cols]
        y_train = train_df["target"]

        X_val = val_df[feature_cols]
        y_val = val_df["target"]

        X_test = test_df[feature_cols]
        y_test = test_df["target"]

        # Create metadata
        metadata = DatasetMetadata(
            version="1.0.0",
            created_at=datetime.now(),
            train_size=len(X_train),
            val_size=len(X_val),
            test_size=len(X_test),
            date_range=(df["data_emissione"].min().date(), df["data_emissione"].max().date()),
            target_mean=float(df["target"].mean()),
            target_std=float(df["target"].std()),
            missing_payment_ratio=float(df["target"].isna().mean()),
        )

        logger.info(
            "dataset_split_completed",
            train_size=len(X_train),
            val_size=len(X_val),
            test_size=len(X_test),
            train_date_range=(
                train_df["data_emissione"].min().date(),
                train_df["data_emissione"].max().date(),
            ),
            test_date_range=(
                test_df["data_emissione"].min().date(),
                test_df["data_emissione"].max().date(),
            ),
        )

        return Dataset(
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            X_test=X_test,
            y_test=y_test,
            metadata=metadata,
        )

    def _validate_data_quality(self, df: pd.DataFrame) -> None:
        """Validate data quality and log warnings.

        Args:
            df: DataFrame to validate

        Raises:
            ValueError: If data quality is insufficient
        """
        if len(df) == 0:
            raise ValueError("No invoices found in date range")

        # Check for required columns
        required_cols = [
            "cliente_id",
            "data_emissione",
            "totale",
            "imponibile",
        ]

        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Log data quality metrics
        logger.info(
            "data_quality_metrics",
            total_invoices=len(df),
            unique_clients=df["cliente_id"].nunique(),
            date_range=(df["data_emissione"].min().date(), df["data_emissione"].max().date()),
            missing_payment_ratio=df["payment_date"].isna().mean(),
            avg_invoice_amount=df["totale"].mean(),
        )

        # Warnings for potential issues
        if df["payment_date"].isna().mean() > 0.7:
            logger.warning(
                "high_missing_payment_ratio",
                ratio=df["payment_date"].isna().mean(),
                message="Many invoices lack payment data - model may be less accurate",
            )

        if len(df) < 100:
            logger.warning(
                "low_sample_count",
                count=len(df),
                message="Low sample count may affect model performance",
            )

    def _get_cache_key(
        self,
        min_date: date,
        max_date: date,
        val_split: float,
        test_split: float,
    ) -> str:
        """Generate cache key for dataset configuration."""
        return (
            f"dataset_{min_date.isoformat()}_{max_date.isoformat()}_"
            f"val{val_split:.2f}_test{test_split:.2f}"
        )

    def clear_cache(self) -> int:
        """Clear all cached datasets.

        Returns:
            Number of cache files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("dataset_*.pkl"):
            cache_file.unlink()
            count += 1

        logger.info("cache_cleared", files_deleted=count)

        return count
