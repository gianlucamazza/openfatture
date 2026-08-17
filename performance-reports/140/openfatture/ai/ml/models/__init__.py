"""ML Models for Cash Flow Prediction.

This module contains the ML model implementations:
- ProphetModel: Captures seasonality and long-term trends
- XGBoostModel: Captures client-specific and invoice-specific patterns
- CashFlowEnsemble: Weighted ensemble combining both models

The ensemble approach provides:
- Prophet (40%): Temporal patterns, seasonality, holidays
- XGBoost (60%): Client behavior, invoice characteristics
"""

from openfatture.ai.ml.models.ensemble import (
    CashFlowEnsemble,
    EnsemblePrediction,
    RiskLevel,
)
from openfatture.ai.ml.models.prophet_model import (
    ProphetModel,
    ProphetPrediction,
)
from openfatture.ai.ml.models.xgboost_model import (
    XGBoostModel,
    XGBoostPrediction,
    asymmetric_mae_loss,
)

__all__ = [
    # Prophet
    "ProphetModel",
    "ProphetPrediction",
    # XGBoost
    "XGBoostModel",
    "XGBoostPrediction",
    "asymmetric_mae_loss",
    # Ensemble
    "CashFlowEnsemble",
    "EnsemblePrediction",
    "RiskLevel",
]
