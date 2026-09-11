"""Tests for CashFlowPredictorAgent training and persistence logic."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import openfatture.ai.agents.cash_flow_predictor as predictor_module
from openfatture.ai.agents.cash_flow_predictor import CashFlowPredictorAgent
from openfatture.ai.ml.config import MLConfig
from openfatture.ai.ml.data_loader import Dataset, DatasetMetadata
from openfatture.ai.ml.features import FeatureSchema
from openfatture.ai.ml.models.ensemble import (
    EnsemblePrediction,
    RiskLevel,
)
from openfatture.ai.ml.models.prophet_model import ProphetPrediction
from openfatture.ai.ml.models.xgboost_model import XGBoostPrediction


class FakeFeaturePipeline:
    """Minimal pipeline stub that records fit/transform calls."""

    def __init__(self, **_: object) -> None:
        self.fitted_ = False
        self._schema = FeatureSchema(
            version="test-1.0.0",
            features=["f1", "f2"],
            dtypes={"f1": "float", "f2": "float"},
            nullable={"f1": False, "f2": False},
        )

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> FakeFeaturePipeline:
        self.fitted_ = True
        # Store index to reuse during transform to satisfy downstream matching
        self._last_index = X.index
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self.fitted_:
            raise ValueError("Pipeline must be fitted before transform.")
        data = {
            "f1": np.ones(len(X), dtype=float),
            "f2": np.linspace(0.0, 1.0, num=len(X), dtype=float) if len(X) else np.array([]),
        }
        return pd.DataFrame(data, index=X.index)

    def get_schema(self) -> FeatureSchema:
        return self._schema


class FakeEnsemble:
    """Stub ensemble model that produces deterministic predictions."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.fitted_ = False

    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame | None = None,
        y_val: pd.Series | None = None,
    ) -> FakeEnsemble:
        self.fitted_ = True
        return self

    def predict(self, X: pd.DataFrame) -> list[EnsemblePrediction]:
        if not self.fitted_:
            raise ValueError("Model must be fitted before prediction.")

        predictions: list[EnsemblePrediction] = []
        for index in X.index:
            base_value = float(index)
            predictions.append(
                EnsemblePrediction(
                    yhat=base_value,
                    yhat_lower=base_value - 0.5,
                    yhat_upper=base_value + 0.5,
                    confidence_score=0.85,
                    risk_level=RiskLevel.LOW,
                    prophet_prediction=ProphetPrediction(
                        yhat=base_value,
                        yhat_lower=base_value - 0.5,
                        yhat_upper=base_value + 0.5,
                        trend=base_value,
                        seasonal=0.0,
                        holiday=0.0,
                    ),
                    xgboost_prediction=XGBoostPrediction(
                        yhat=base_value,
                        yhat_lower=base_value - 0.25,
                        yhat_upper=base_value + 0.25,
                        feature_importance=None,
                    ),
                    model_agreement=0.95,
                )
            )
        return predictions

    def save(self, filepath_prefix: str) -> None:
        Path(f"{filepath_prefix}_prophet.json").write_text("{}", encoding="utf-8")
        Path(f"{filepath_prefix}_xgboost.json").write_text("{}", encoding="utf-8")

    @classmethod
    def load(cls, filepath_prefix: str) -> FakeEnsemble:
        # Touch files to simulate presence
        Path(f"{filepath_prefix}_prophet.json").touch()
        Path(f"{filepath_prefix}_xgboost.json").touch()
        instance = cls()
        instance.fitted_ = True
        return instance


class FakeDataLoader:
    """Stub data loader that returns deterministic splits."""

    def __init__(self, **_: object) -> None:
        self.now = datetime.now(tz=UTC)

    def load_dataset(self, val_split: float, test_split: float) -> Dataset:
        total_samples = 36  # >= 25 to satisfy guard condition
        indices = pd.RangeIndex(start=0, stop=total_samples, step=1)
        X = pd.DataFrame({"dummy": np.arange(total_samples, dtype=float)}, index=indices)
        y = pd.Series(np.arange(total_samples, dtype=float), index=indices)

        train_end = int(total_samples * (1 - val_split - test_split))
        val_end = train_end + int(total_samples * val_split)

        X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
        X_val, y_val = X.iloc[train_end:val_end], y.iloc[train_end:val_end]
        X_test, y_test = X.iloc[val_end:], y.iloc[val_end:]

        metadata = DatasetMetadata(
            version="test-dataset",
            created_at=self.now,
            train_size=len(X_train),
            val_size=len(X_val),
            test_size=len(X_test),
            date_range=(self.now.date() - timedelta(days=365), self.now.date()),
            target_mean=float(y.mean()),
            target_std=float(y.std()),
            missing_payment_ratio=0.0,
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


class FewSamplesDataLoader(FakeDataLoader):
    """Stub loader returning too few samples to trigger guard."""

    def load_dataset(self, val_split: float, test_split: float) -> Dataset:
        total_samples = 10  # Below threshold
        indices = pd.RangeIndex(start=0, stop=total_samples, step=1)
        X = pd.DataFrame({"dummy": np.arange(total_samples, dtype=float)}, index=indices)
        y = pd.Series(np.arange(total_samples, dtype=float), index=indices)

        metadata = DatasetMetadata(
            version="tiny-dataset",
            created_at=self.now,
            train_size=len(X),
            val_size=0,
            test_size=0,
            date_range=(self.now.date() - timedelta(days=90), self.now.date()),
            target_mean=float(y.mean()),
            target_std=float(y.std()),
            missing_payment_ratio=0.0,
        )

        return Dataset(
            X_train=X,
            y_train=y,
            X_val=pd.DataFrame(columns=["dummy"]),
            y_val=pd.Series(dtype=float),
            X_test=pd.DataFrame(columns=["dummy"]),
            y_test=pd.Series(dtype=float),
            metadata=metadata,
        )


@pytest.fixture
def ml_config(tmp_path: Path) -> MLConfig:
    """Return ML configuration pointing to temporary directories."""
    config = MLConfig(
        model_path=tmp_path / "models",
        cache_path=tmp_path / "cache",
        prophet_weight=0.4,
        xgboost_weight=0.6,
    )
    config.__post_init__()
    return config


def _patch_components(monkeypatch: pytest.MonkeyPatch, loader: type) -> None:
    """Helper to patch ML components with stubs."""
    monkeypatch.setattr(predictor_module, "InvoiceDataLoader", loader)
    monkeypatch.setattr(predictor_module, "FeaturePipeline", FakeFeaturePipeline)
    monkeypatch.setattr(predictor_module, "CashFlowEnsemble", FakeEnsemble)
    monkeypatch.setattr(
        predictor_module,
        "create_provider",
        lambda: DummyProvider(),
    )


class DummyProvider:
    """Minimal LLM provider stub used to satisfy constructor dependencies."""

    provider_name = "dummy"
    model = "dummy-0"

    async def generate(self, *args: object, **kwargs: object):
        from openfatture.ai.domain.response import AgentResponse, UsageMetrics

        return AgentResponse(content="stub", usage=UsageMetrics())


@pytest.mark.asyncio
async def test_training_persists_models_and_metrics(
    monkeypatch: pytest.MonkeyPatch, ml_config: MLConfig
) -> None:
    """Training should persist ensemble artifacts, pipeline, and metrics."""
    _patch_components(monkeypatch, FakeDataLoader)

    agent = CashFlowPredictorAgent(config=ml_config)
    await agent.initialize(force_retrain=True)

    model_prefix = ml_config.get_model_filepath("cash_flow")

    assert Path(f"{model_prefix}_prophet.json").exists()
    assert Path(f"{model_prefix}_xgboost.json").exists()
    assert Path(f"{model_prefix}_pipeline.pkl").exists()
    assert Path(f"{model_prefix}_metrics.json").exists()

    assert agent.training_metrics_ is not None
    assert "train" in agent.training_metrics_
    assert agent.training_metrics_["train"]["samples"] > 0
    assert agent.dataset_metadata_ is not None
    assert agent.feature_schema_ is not None

    # Ensure loading uses persisted artifacts and keeps pipeline fitted
    reloaded_agent = CashFlowPredictorAgent(config=ml_config)
    _patch_components(monkeypatch, FakeDataLoader)
    await reloaded_agent.initialize(force_retrain=False)

    assert reloaded_agent.model_trained_
    assert reloaded_agent.feature_pipeline is not None
    assert reloaded_agent.feature_pipeline.fitted_
    assert reloaded_agent.training_metrics_ == agent.training_metrics_


@pytest.mark.asyncio
async def test_training_requires_minimum_samples(
    monkeypatch: pytest.MonkeyPatch, ml_config: MLConfig
) -> None:
    """Training should fail fast when there are insufficient samples."""
    _patch_components(monkeypatch, FewSamplesDataLoader)

    agent = CashFlowPredictorAgent(config=ml_config)

    with pytest.raises(ValueError, match="Not enough samples"):
        await agent.initialize(force_retrain=True)
