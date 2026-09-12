"""OpenFatture ML Module - Cash Flow Prediction.

This module provides machine learning capabilities for predicting invoice
payment timing using an ensemble of Prophet (seasonality) and XGBoost (patterns).

Components:
- Feature Engineering: Extract 24+ features from invoice and client data
- Data Loading: Chronological train/val/test splitting
- Models: Prophet, XGBoost, and weighted ensemble
- Agent: CashFlowPredictorAgent for natural language interface

Example Usage:
    >>> from openfatture.ai.ml import FeaturePipeline, InvoiceDataLoader
    >>>
    >>> # Load and preprocess data
    >>> loader = InvoiceDataLoader()
    >>> dataset = loader.load_dataset()
    >>>
    >>> # Extract features
    >>> pipeline = FeaturePipeline()
    >>> X_train_features = pipeline.fit_transform(dataset.X_train, dataset.y_train)
    >>>
    >>> # Train ensemble model
    >>> from openfatture.ai.ml.models import CashFlowEnsemble
    >>> ensemble = CashFlowEnsemble()
    >>> ensemble.fit(X_train_features, dataset.y_train)
    >>>
    >>> # Make predictions
    >>> prediction = ensemble.predict(invoice_id=123)
    >>> print(f"Expected payment delay: {prediction.expected_days:.1f} days")
"""

from openfatture.ai.ml.data_loader import (
    Dataset,
    DatasetMetadata,
    InvoiceDataLoader,
)
from openfatture.ai.ml.features import (
    ClientBehaviorFeatureExtractor,
    FeaturePipeline,
    FeatureSchema,
    InvoiceFeatureExtractor,
    TemporalFeatureExtractor,
)

__all__ = [
    # Feature Engineering
    "FeaturePipeline",
    "TemporalFeatureExtractor",
    "ClientBehaviorFeatureExtractor",
    "InvoiceFeatureExtractor",
    "FeatureSchema",
    # Data Loading
    "InvoiceDataLoader",
    "Dataset",
    "DatasetMetadata",
]
