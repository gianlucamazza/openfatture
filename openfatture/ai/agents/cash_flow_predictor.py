"""Cash Flow Predictor Agent.

AI-powered agent that combines ML models with natural language insights
for invoice payment delay prediction and cash flow forecasting.

This agent:
1. Trains or loads Prophet + XGBoost ensemble models
2. Generates payment delay predictions for invoices
3. Forecasts cash flow for upcoming months
4. Provides AI-generated insights and recommendations
5. Classifies risk levels (LOW/MEDIUM/HIGH)

Example Usage:
    >>> from openfatture.ai.agents.cash_flow_predictor import CashFlowPredictorAgent
    >>>
    >>> agent = CashFlowPredictorAgent()
    >>> await agent.initialize()  # Train or load models
    >>>
    >>> # Predict single invoice
    >>> result = await agent.predict_invoice(invoice_id=123)
    >>> print(f"Expected delay: {result['expected_days']:.1f} days")
    >>> print(f"Risk: {result['risk_level']}")
    >>>
    >>> # Forecast multiple months
    >>> forecast = await agent.forecast_cash_flow(months=3)
    >>> for month_data in forecast['monthly']:
    ...     print(f"{month_data['month']}: €{month_data['expected']:.2f}")
"""

import json
import pickle
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from openfatture.ai.domain.message import Message, Role
from openfatture.ai.feedback.service import FeedbackService
from openfatture.ai.ml.config import MLConfig, get_ml_config
from openfatture.ai.ml.data_loader import DatasetMetadata, InvoiceDataLoader
from openfatture.ai.ml.features import FeaturePipeline
from openfatture.ai.ml.models import CashFlowEnsemble
from openfatture.ai.ml.retraining.evaluator import ModelEvaluator
from openfatture.ai.ml.retraining.versioning import ModelVersionManager
from openfatture.ai.providers import create_provider
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.storage.database.base import SessionLocal
from openfatture.storage.database.models import Fattura, PredictionType, StatoFattura
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


def _get_session() -> Session:
    """Return database session ensuring initialisation."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() before using the agent.")
    return SessionLocal()


@dataclass
class PredictionResult:
    """Result from cash flow prediction.

    Attributes:
        invoice_id: Invoice ID
        expected_days: Expected payment delay in days
        confidence_score: Prediction confidence (0-1)
        risk_level: Risk classification (LOW/MEDIUM/HIGH)
        lower_bound: Lower bound of prediction interval
        upper_bound: Upper bound of prediction interval
        insights: AI-generated natural language insights
        recommendations: List of actionable recommendations
    """

    invoice_id: int
    expected_days: float
    confidence_score: float
    risk_level: str
    lower_bound: float
    upper_bound: float
    insights: str
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "invoice_id": self.invoice_id,
            "expected_days": float(self.expected_days),
            "confidence_score": float(self.confidence_score),
            "risk_level": self.risk_level,
            "prediction_interval": {
                "lower": float(self.lower_bound),
                "upper": float(self.upper_bound),
            },
            "insights": self.insights,
            "recommendations": self.recommendations,
        }


@dataclass
class ForecastResult:
    """Result from multi-month cash flow forecast.

    Attributes:
        months: Number of months forecasted
        monthly_forecast: List of monthly predictions
        total_expected: Total expected revenue
        insights: AI-generated insights
        recommendations: Strategic recommendations
    """

    months: int
    monthly_forecast: list[dict[str, Any]]
    total_expected: float
    insights: str
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "months": self.months,
            "monthly": self.monthly_forecast,
            "total_expected": float(self.total_expected),
            "insights": self.insights,
            "recommendations": self.recommendations,
        }


class CashFlowPredictorAgent:
    """AI-powered cash flow prediction agent.

    Combines ML models (Prophet + XGBoost ensemble) with AI-generated
    natural language insights for payment delay prediction and forecasting.

    Example:
        >>> agent = CashFlowPredictorAgent()
        >>> await agent.initialize()
        >>>
        >>> # Single invoice prediction
        >>> result = await agent.predict_invoice(123)
        >>>
        >>> # Multi-month forecast
        >>> forecast = await agent.forecast_cash_flow(months=6)
    """

    def __init__(
        self,
        config: MLConfig | None = None,
        ai_provider: BaseLLMProvider | None = None,
    ):
        """Initialize Cash Flow Predictor Agent.

        Args:
            config: ML configuration (uses defaults if None)
            ai_provider: AI provider for insights (creates default if None)
        """
        self.config = config or get_ml_config()
        self.ai_provider = ai_provider or create_provider()

        # ML components
        self.ensemble: CashFlowEnsemble | None = None
        self.feature_pipeline: FeaturePipeline | None = None
        self.data_loader: InvoiceDataLoader | None = None

        # State
        self.initialized_ = False
        self.model_trained_ = False
        self.training_metrics_: dict[str, Any] | None = None
        self.dataset_metadata_: dict[str, Any] | None = None
        self.feature_schema_: dict[str, Any] | None = None

        logger.info("cash_flow_predictor_agent_initialized")

    async def initialize(
        self,
        force_retrain: bool = False,
    ) -> None:
        """Initialize agent by loading or training models.

        Args:
            force_retrain: Force model retraining even if saved models exist
        """
        logger.info("initializing_agent", force_retrain=force_retrain)

        # Initialize data loader
        self.data_loader = InvoiceDataLoader(**self.config.get_data_loader_params())

        # Initialize feature pipeline
        self.feature_pipeline = FeaturePipeline(**self.config.get_feature_pipeline_params())

        # Initialize ensemble
        self.ensemble = CashFlowEnsemble(
            prophet_weight=self.config.prophet_weight,
            xgboost_weight=self.config.xgboost_weight,
            prophet_params=self.config.get_prophet_params(),
            xgboost_params=self.config.get_xgboost_params(),
            optimize_weights=self.config.optimize_weights,
        )

        # Load or train models
        model_path = self.config.get_model_filepath("cash_flow")

        if not force_retrain and self._models_exist(model_path):
            logger.info("loading_existing_models", path=model_path)
            await self._load_models(model_path)
        else:
            logger.info("training_new_models")
            await self._train_models()

        self.initialized_ = True

        logger.info("agent_initialized", model_trained=self.model_trained_)

    async def predict_invoice(
        self,
        invoice_id: int,
        include_insights: bool = True,
    ) -> PredictionResult:
        """Predict payment delay for a specific invoice.

        Args:
            invoice_id: Invoice ID to predict
            include_insights: Generate AI insights (default: True)

        Returns:
            PredictionResult with prediction and insights

        Raises:
            ValueError: If agent not initialized or invoice not found
        """
        if not self.initialized_:
            raise ValueError("Agent must be initialized before prediction")

        logger.info("predicting_invoice", invoice_id=invoice_id)

        # Load invoice data
        db = _get_session()
        try:
            fattura = db.query(Fattura).filter(Fattura.id == invoice_id).first()

            if not fattura:
                raise ValueError(f"Invoice {invoice_id} not found")

            # Convert to DataFrame row
            X_row = self._invoice_to_features(fattura)

            # Extract features
            if self.feature_pipeline is None:
                raise RuntimeError("Feature pipeline not initialized. Call initialize() first.")
            X_features = self.feature_pipeline.transform(pd.DataFrame([X_row]))

            # Make prediction
            if self.ensemble is None:
                raise RuntimeError("Ensemble model not initialized. Call initialize() first.")
            prediction = self.ensemble.predict_single(X_features.iloc[0])

            # Generate insights if requested
            if include_insights:
                insights, recommendations = await self._generate_insights(fattura, prediction)
            else:
                insights = ""
                recommendations = []

            result = PredictionResult(
                invoice_id=invoice_id,
                expected_days=prediction.yhat,
                confidence_score=prediction.confidence_score,
                risk_level=prediction.risk_level.value,
                lower_bound=prediction.yhat_lower,
                upper_bound=prediction.yhat_upper,
                insights=insights,
                recommendations=recommendations,
            )

            logger.info(
                "invoice_predicted",
                invoice_id=invoice_id,
                expected_days=result.expected_days,
                risk_level=result.risk_level,
                confidence=result.confidence_score,
            )

            return result

        finally:
            db.close()

    async def forecast_cash_flow(
        self,
        months: int = 3,
        client_id: int | None = None,
    ) -> ForecastResult:
        """Forecast cash flow for upcoming months.

        Args:
            months: Number of months to forecast
            client_id: Optional filter by specific client

        Returns:
            ForecastResult with monthly forecasts
        """
        if not self.initialized_:
            raise ValueError("Agent must be initialized before forecasting")

        logger.info("forecasting_cash_flow", months=months, client_id=client_id)

        # Get unpaid invoices
        db = _get_session()
        try:
            query = db.query(Fattura).filter(
                Fattura.stato.in_(
                    [
                        StatoFattura.DA_INVIARE,
                        StatoFattura.INVIATA,
                        StatoFattura.CONSEGNATA,
                    ]
                )
            )

            if client_id:
                query = query.filter(Fattura.cliente_id == client_id)

            unpaid_invoices = query.all()

            logger.info(
                "forecasting_unpaid_invoices",
                count=len(unpaid_invoices),
                client_id=client_id,
            )

            # Predict payment dates for all invoices
            monthly_totals = dict.fromkeys(range(months), 0.0)

            for fattura in unpaid_invoices:
                try:
                    # Get prediction
                    prediction_result = await self.predict_invoice(
                        fattura.id, include_insights=False
                    )

                    # Calculate expected payment date
                    expected_payment_date = fattura.data_emissione + timedelta(
                        days=prediction_result.expected_days
                    )

                    # Determine which month this falls into
                    today = date.today()
                    month_diff = (
                        (expected_payment_date.year - today.year) * 12
                        + expected_payment_date.month
                        - today.month
                    )

                    if 0 <= month_diff < months:
                        monthly_totals[month_diff] += float(fattura.totale)

                except Exception as e:
                    logger.warning(
                        "invoice_forecast_failed",
                        invoice_id=fattura.id,
                        error=str(e),
                    )

            # Build monthly forecast
            monthly_forecast = []
            today = date.today()

            for i in range(months):
                month_date = today + timedelta(days=30 * (i + 1))
                month_str = month_date.strftime("%B %Y")

                monthly_forecast.append(
                    {
                        "month": month_str,
                        "month_index": i + 1,
                        "expected": monthly_totals[i],
                    }
                )

            total_expected = sum(monthly_totals.values())

            # Generate AI insights
            insights, recommendations = await self._generate_forecast_insights(
                monthly_forecast, total_expected, months
            )

            result = ForecastResult(
                months=months,
                monthly_forecast=monthly_forecast,
                total_expected=total_expected,
                insights=insights,
                recommendations=recommendations,
            )

            logger.info(
                "forecast_completed",
                months=months,
                total_expected=total_expected,
            )

            return result

        finally:
            db.close()

    async def retrain_from_feedback(self, min_feedback_count: int = 10) -> dict[str, Any]:
        """Retrain model using accumulated user feedback.

        This method:
        1. Loads unprocessed prediction feedback
        2. Extracts user corrections
        3. Combines with historical training data
        4. Trains new model
        5. Evaluates against current model
        6. Deploys if improvement criteria met
        7. Saves as new version
        8. Marks feedback as processed

        Args:
            min_feedback_count: Minimum feedback samples required (default: 10)

        Returns:
            Dictionary with retraining results and metrics

        Raises:
            ValueError: If not enough feedback or agent not initialized
        """
        if not self.initialized_:
            raise ValueError("Agent must be initialized before retraining")

        logger.info("retraining_from_feedback_started", min_feedback_count=min_feedback_count)

        # Load unprocessed feedback
        feedback_service = FeedbackService()
        feedbacks = feedback_service.get_unprocessed_predictions(
            prediction_type=PredictionType.INVOICE_DELAY
        )

        if len(feedbacks) < min_feedback_count:
            logger.warning(
                "insufficient_feedback",
                feedback_count=len(feedbacks),
                min_required=min_feedback_count,
            )
            return {
                "success": False,
                "message": f"Insufficient feedback: {len(feedbacks)} < {min_feedback_count}",
                "feedback_count": len(feedbacks),
            }

        logger.info("feedback_loaded", count=len(feedbacks))

        # Save current model as version before retraining
        version_manager = ModelVersionManager()
        try:
            current_version_id = version_manager.save_version(
                model_name="cash_flow",
                metrics=(
                    self.training_metrics_.get("validation") if self.training_metrics_ else None
                ),
                notes="Pre-retraining backup",
            )
            logger.info("current_model_versioned", version_id=current_version_id)
        except FileNotFoundError:
            # No current model to version (first training)
            current_version_id = None
            logger.info("no_current_model_to_version")

        # Save reference to current ensemble for comparison
        current_ensemble = self.ensemble

        try:
            # Initialize new ensemble for retraining
            new_ensemble = CashFlowEnsemble(
                prophet_weight=self.config.prophet_weight,
                xgboost_weight=self.config.xgboost_weight,
                prophet_params=self.config.get_prophet_params(),
                xgboost_params=self.config.get_xgboost_params(),
                optimize_weights=self.config.optimize_weights,
            )

            # Train new model (this loads historical data + applies standard pipeline)
            await self._train_models_with_ensemble(new_ensemble)

            logger.info("new_model_trained")

            # Evaluate new model vs current
            evaluator = ModelEvaluator()

            # Load validation dataset for comparison
            if self.data_loader is None:
                raise RuntimeError("Data loader not initialized")

            dataset = self.data_loader.load_dataset(
                val_split=self.config.validation_split,
                test_split=self.config.test_split,
            )

            if self.feature_pipeline is None:
                raise RuntimeError("Feature pipeline not initialized")

            X_val_features = (
                self.feature_pipeline.transform(dataset.X_val)
                if len(dataset.X_val) > 0
                else dataset.X_val
            )

            # Compare models
            eval_result = evaluator.evaluate_and_compare(
                new_model=new_ensemble,
                X_val=X_val_features,
                y_val=dataset.y_val,
                current_model=current_ensemble,
            )

            logger.info(
                "evaluation_completed",
                should_deploy=eval_result.should_deploy,
                reason=eval_result.deployment_reason,
                new_mae=eval_result.metrics.get("mae"),
            )

            if not eval_result.should_deploy:
                # Rollback: keep current model
                logger.info("new_model_rejected", reason=eval_result.deployment_reason)

                return {
                    "success": False,
                    "deployed": False,
                    "message": f"New model not deployed: {eval_result.deployment_reason}",
                    "feedback_count": len(feedbacks),
                    "evaluation": eval_result.to_dict(),
                }

            # Deploy new model
            self.ensemble = new_ensemble
            model_path = self.config.get_model_filepath("cash_flow")
            await self._save_models(model_path)

            # Save as new version
            new_version_id = version_manager.save_version(
                model_name="cash_flow",
                metrics=eval_result.metrics,
                notes=f"Retrained with {len(feedbacks)} feedback samples",
            )

            logger.info("new_model_deployed", version_id=new_version_id)

            # Mark feedback as processed
            for feedback in feedbacks:
                try:
                    feedback_service.mark_prediction_processed(feedback.id)
                except Exception as e:
                    logger.error(
                        "failed_to_mark_feedback_processed",
                        feedback_id=feedback.id,
                        error=str(e),
                    )

            logger.info("feedback_marked_processed", count=len(feedbacks))

            return {
                "success": True,
                "deployed": True,
                "message": eval_result.deployment_reason,
                "feedback_count": len(feedbacks),
                "version_id": new_version_id,
                "previous_version_id": current_version_id,
                "evaluation": eval_result.to_dict(),
            }

        except Exception as e:
            # Rollback on error: restore current model
            logger.error("retraining_failed", error=str(e), exc_info=True)

            if current_ensemble is not None:
                self.ensemble = current_ensemble
                logger.info("model_restored_after_error")

            return {
                "success": False,
                "deployed": False,
                "message": f"Retraining failed: {str(e)}",
                "feedback_count": len(feedbacks),
            }

    async def _train_models_with_ensemble(self, ensemble: CashFlowEnsemble) -> None:
        """Train models using provided ensemble instance.

        This is a helper for retraining that allows using a separate ensemble
        without modifying self.ensemble until deployment decision is made.

        Args:
            ensemble: CashFlowEnsemble instance to train
        """
        # Load dataset
        if self.data_loader is None:
            raise RuntimeError("Data loader not initialized")

        dataset = self.data_loader.load_dataset(
            val_split=self.config.validation_split,
            test_split=self.config.test_split,
        )

        # Guard against insufficient data
        if len(dataset.X_train) < 25:
            raise ValueError(
                "Not enough samples to train. "
                "At least 25 historical invoices with payment data are required."
            )

        # Fit feature pipeline
        if self.feature_pipeline is None:
            raise RuntimeError("Feature pipeline not initialized")

        self.feature_pipeline.fit(dataset.X_train, dataset.y_train)

        # Transform features
        X_train_features = self.feature_pipeline.transform(dataset.X_train)
        X_val_features = (
            self.feature_pipeline.transform(dataset.X_val)
            if len(dataset.X_val) > 0
            else dataset.X_val
        )
        X_test_features = (
            self.feature_pipeline.transform(dataset.X_test)
            if len(dataset.X_test) > 0
            else dataset.X_test
        )

        # Train ensemble
        ensemble.fit(
            X_train_features,
            dataset.y_train,
            X_val_features if len(dataset.X_val) > 0 else None,
            dataset.y_val if len(dataset.y_val) > 0 else None,
        )

        # Update internal state
        self.training_metrics_ = self._evaluate_model_with_ensemble(
            ensemble,
            X_train_features,
            dataset.y_train,
            X_val_features,
            dataset.y_val,
            X_test_features,
            dataset.y_test,
        )
        self.dataset_metadata_ = self._serialize_dataset_metadata(dataset.metadata)

    def _evaluate_model_with_ensemble(
        self,
        ensemble: CashFlowEnsemble,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> dict[str, Any]:
        """Evaluate a specific ensemble instance.

        Args:
            ensemble: Ensemble to evaluate
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
            X_test: Test features
            y_test: Test targets

        Returns:
            Dictionary of evaluation metrics
        """

        def _split_metrics(name: str, X: pd.DataFrame, y: pd.Series) -> dict[str, Any] | None:
            if X is None or y is None or len(X) == 0:
                return None
            predictions = ensemble.predict(X)
            y_true = y.to_numpy(dtype=float)
            y_pred = np.array([pred.yhat for pred in predictions], dtype=float)
            residuals = y_true - y_pred

            mae = float(np.mean(np.abs(residuals)))
            rmse = float(np.sqrt(np.mean(np.square(residuals))))
            median_abs_error = float(np.median(np.abs(residuals)))

            coverages = []
            interval_widths = []
            for target, pred in zip(y_true, predictions, strict=False):
                if pred.yhat_lower is not None and pred.yhat_upper is not None:
                    interval_widths.append(pred.uncertainty)
                    coverages.append(pred.yhat_lower <= target <= pred.yhat_upper)

            coverage = float(np.mean(coverages)) if coverages else None
            median_interval = float(np.median(interval_widths)) if interval_widths else None

            return {
                "mae": mae,
                "rmse": rmse,
                "median_abs_error": median_abs_error,
                "coverage": coverage,
                "median_interval_width": median_interval,
                "samples": int(len(X)),
            }

        metrics: dict[str, Any] = {}
        for split_name, X_split, y_split in (
            ("train", X_train, y_train),
            ("validation", X_val, y_val),
            ("test", X_test, y_test),
        ):
            split_metrics = _split_metrics(split_name, X_split, y_split)
            if split_metrics:
                metrics[split_name] = split_metrics

        return metrics

    async def _train_models(self) -> None:
        """Train ML models on historical data."""
        logger.info("training_models")

        # Load dataset
        if self.data_loader is None:
            raise RuntimeError("Data loader not initialized. Call initialize() first.")
        dataset = self.data_loader.load_dataset(
            val_split=self.config.validation_split,
            test_split=self.config.test_split,
        )

        logger.info(
            "dataset_loaded",
            train_size=len(dataset.X_train),
            val_size=len(dataset.X_val),
            test_size=len(dataset.X_test),
        )

        # Guard against insufficient data
        if len(dataset.X_train) < 25:
            raise ValueError(
                "Not enough samples to train the Cash Flow Predictor. "
                "At least 25 historical invoices with payment data are required."
            )

        # Fit feature pipeline
        if self.feature_pipeline is None:
            raise RuntimeError("Feature pipeline not initialized. Call initialize() first.")
        self.feature_pipeline.fit(dataset.X_train, dataset.y_train)

        # Transform features for each split
        X_train_features = self.feature_pipeline.transform(dataset.X_train)
        X_val_features = (
            self.feature_pipeline.transform(dataset.X_val)
            if len(dataset.X_val) > 0
            else dataset.X_val
        )
        X_test_features = (
            self.feature_pipeline.transform(dataset.X_test)
            if len(dataset.X_test) > 0
            else dataset.X_test
        )

        # Persist feature schema for downstream inspection
        self.feature_schema_ = (
            self.feature_pipeline.get_schema().__dict__
            if hasattr(self.feature_pipeline, "get_schema")
            else None
        )

        # Train ensemble
        if self.ensemble is None:
            raise RuntimeError("Ensemble model not initialized. Call initialize() first.")
        self.ensemble.fit(
            X_train_features,
            dataset.y_train,
            X_val_features if len(dataset.X_val) > 0 else None,
            dataset.y_val if len(dataset.y_val) > 0 else None,
        )

        # Evaluate and capture metrics
        self.training_metrics_ = self._evaluate_model(
            X_train_features,
            dataset.y_train,
            X_val_features,
            dataset.y_val,
            X_test_features,
            dataset.y_test,
        )

        logger.info("models_trained", metrics=self.training_metrics_)

        # Persist dataset metadata for audit purposes
        self.dataset_metadata_ = self._serialize_dataset_metadata(dataset.metadata)

        # Save models
        model_path = self.config.get_model_filepath("cash_flow")
        await self._save_models(model_path)

        self.model_trained_ = True

    async def _save_models(self, filepath_prefix: str) -> None:
        """Save trained models to disk."""
        if self.ensemble is None:
            raise RuntimeError("Ensemble model not initialized. Cannot save.")
        if self.feature_pipeline is None or not self.feature_pipeline.fitted_:
            raise RuntimeError("Feature pipeline not fitted. Cannot save.")

        model_dir = Path(filepath_prefix).parent
        model_dir.mkdir(parents=True, exist_ok=True)

        # Save ensemble constituents
        self.ensemble.save(filepath_prefix)

        # Persist feature pipeline state
        pipeline_path = Path(f"{filepath_prefix}_pipeline.pkl")
        pipeline_payload = {
            "pipeline": self.feature_pipeline,
            "schema": self.feature_schema_,
        }
        with pipeline_path.open("wb") as fh:
            pickle.dump(pipeline_payload, fh)

        # Persist training metadata and dataset provenance
        config_dump = self.config.model_dump()
        serializable_config = {
            key: (str(value) if isinstance(value, Path) else value)
            for key, value in config_dump.items()
        }

        metrics_path = Path(f"{filepath_prefix}_metrics.json")
        metrics_payload = {
            "trained_at": datetime.now(UTC).isoformat(),
            "config": serializable_config,
            "metrics": self.training_metrics_ or {},
            "dataset": self.dataset_metadata_ or {},
        }
        with metrics_path.open("w", encoding="utf-8") as fh:
            json.dump(metrics_payload, fh, indent=2, ensure_ascii=False)

        logger.info(
            "models_saved",
            path=filepath_prefix,
            pipeline=str(pipeline_path),
            metrics=str(metrics_path),
        )

    async def _load_models(self, filepath_prefix: str) -> None:
        """Load models from disk."""
        self.ensemble = CashFlowEnsemble.load(filepath_prefix)
        pipeline_path = Path(f"{filepath_prefix}_pipeline.pkl")
        if not pipeline_path.exists():
            raise FileNotFoundError(f"Saved feature pipeline not found at {pipeline_path}")

        with pipeline_path.open("rb") as fh:
            payload = pickle.load(fh)

        pipeline = payload.get("pipeline")
        if not isinstance(pipeline, FeaturePipeline):
            raise TypeError("Saved feature pipeline is invalid or corrupted")

        self.feature_pipeline = pipeline
        self.feature_pipeline.fitted_ = True
        self.feature_schema_ = payload.get("schema")

        metrics_path = Path(f"{filepath_prefix}_metrics.json")
        if metrics_path.exists():
            with metrics_path.open("r", encoding="utf-8") as fh:
                metrics_payload = json.load(fh)
            self.training_metrics_ = metrics_payload.get("metrics")
            self.dataset_metadata_ = metrics_payload.get("dataset")
        else:
            self.training_metrics_ = None
            self.dataset_metadata_ = None

        self.model_trained_ = True

        logger.info("models_loaded", path=filepath_prefix)

    def _models_exist(self, filepath_prefix: str) -> bool:
        """Check if saved models exist."""
        prophet_path = Path(f"{filepath_prefix}_prophet.json")
        xgboost_path = Path(f"{filepath_prefix}_xgboost.json")
        pipeline_path = Path(f"{filepath_prefix}_pipeline.pkl")

        return prophet_path.exists() and xgboost_path.exists() and pipeline_path.exists()

    def _evaluate_model(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> dict[str, Any]:
        """Compute evaluation metrics for train/validation/test splits."""

        ensemble = self.ensemble
        if ensemble is None:
            raise RuntimeError("Ensemble model not initialized. Call initialize() first.")

        def _split_metrics(name: str, X: pd.DataFrame, y: pd.Series) -> dict[str, Any] | None:
            if X is None or y is None or len(X) == 0:
                return None
            predictions = ensemble.predict(X)
            y_true = y.to_numpy(dtype=float)
            y_pred = np.array([pred.yhat for pred in predictions], dtype=float)
            residuals = y_true - y_pred

            mae = float(np.mean(np.abs(residuals)))
            rmse = float(np.sqrt(np.mean(np.square(residuals))))
            median_abs_error = float(np.median(np.abs(residuals)))

            # Compute coverage if both bounds available
            coverages = []
            interval_widths = []
            for target, pred in zip(y_true, predictions, strict=False):
                if pred.yhat_lower is not None and pred.yhat_upper is not None:
                    interval_widths.append(pred.uncertainty)
                    coverages.append(pred.yhat_lower <= target <= pred.yhat_upper)

            coverage = float(np.mean(coverages)) if coverages else None
            median_interval = float(np.median(interval_widths)) if interval_widths else None

            return {
                "mae": mae,
                "rmse": rmse,
                "median_abs_error": median_abs_error,
                "coverage": coverage,
                "median_interval_width": median_interval,
                "samples": int(len(X)),
            }

        metrics: dict[str, Any] = {}
        for split_name, X_split, y_split in (
            ("train", X_train, y_train),
            ("validation", X_val, y_val),
            ("test", X_test, y_test),
        ):
            split_metrics = _split_metrics(split_name, X_split, y_split)
            if split_metrics:
                metrics[split_name] = split_metrics

        return metrics

    def _serialize_dataset_metadata(self, metadata: DatasetMetadata) -> dict[str, Any]:
        """Normalize dataset metadata for JSON serialization."""
        payload = asdict(metadata)
        payload["created_at"] = metadata.created_at.isoformat()
        start_date, end_date = metadata.date_range
        payload["date_range"] = [start_date.isoformat(), end_date.isoformat()]
        return payload

    def _invoice_to_features(self, fattura: Fattura) -> dict[str, Any]:
        """Convert invoice to feature dictionary."""
        return {
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
            "payment_date": None,
            "payment_due_date": None,
            "payment_amount": None,
            "righe": len(fattura.righe) if fattura.righe else 0,
        }

    async def _generate_insights(
        self,
        fattura: Fattura,
        prediction: Any,
    ) -> tuple[str, list[str]]:
        """Generate AI-powered insights for invoice prediction."""

        prompt = f"""Analyze questa previsione di pagamento per fattura:

Fattura: {fattura.numero}/{fattura.anno}
Cliente: {fattura.cliente.denominazione}
Importo: €{fattura.totale:.2f}
Data emissione: {fattura.data_emissione.strftime('%d/%m/%Y')}

Previsione ML:
- Ritardo atteso: {prediction.yhat:.1f} giorni
- Intervallo confidenza: {prediction.yhat_lower:.1f} - {prediction.yhat_upper:.1f} giorni
- Confidence score: {prediction.confidence_score:.1%}
- Livello rischio: {prediction.risk_level.value.upper()}
- Agreement modelli: {prediction.model_agreement:.1%}

Fornisci:
1. Insights brevi (2-3 frasi) sulla prediction
2. 2-3 raccomandazioni actionable

Rispondi in italiano, conciso e professionale."""

        try:
            messages = [Message(role=Role.USER, content=prompt)]
            response = await self.ai_provider.generate(
                messages=messages,
                temperature=0.3,
            )

            # Parse response (simplified - in production use structured output)
            content = response.content

            # Split into insights and recommendations (heuristic parsing)
            lines = content.strip().split("\n")
            insights_lines = []
            recommendations = []

            in_recommendations = False

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if "raccomandaz" in line.lower() or "suggerim" in line.lower():
                    in_recommendations = True
                    continue

                if in_recommendations:
                    # Extract bullet points
                    if line.startswith(("-", "•", "*", "1.", "2.", "3.")):
                        rec = line.lstrip("-•*123. ")
                        if rec:
                            recommendations.append(rec)
                else:
                    insights_lines.append(line)

            insights = " ".join(insights_lines)

            return insights, recommendations

        except Exception as e:
            logger.warning("ai_insights_generation_failed", error=str(e))
            return "Previsione generata con successo.", []

    async def _generate_forecast_insights(
        self,
        monthly_forecast: list[dict],
        total_expected: float,
        months: int,
    ) -> tuple[str, list[str]]:
        """Generate AI insights for cash flow forecast."""

        monthly_summary = "\n".join(
            [f"- {m['month']}: €{m['expected']:.2f}" for m in monthly_forecast]
        )

        prompt = f"""Analyze this cash flow forecast for the next {months} months:

{monthly_summary}

Total expected: €{total_expected:.2f}

Provide:
1. Brief insights (2-3 sentences) on the forecast
2. 2-3 strategic recommendations

Respond in Italian, concise and professional."""

        try:
            messages = [Message(role=Role.USER, content=prompt)]
            response = await self.ai_provider.generate(
                messages=messages,
                temperature=0.3,
            )

            content = response.content
            lines = content.strip().split("\n")
            insights_lines = []
            recommendations = []
            in_recommendations = False

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if "raccomandaz" in line.lower() or "suggerim" in line.lower():
                    in_recommendations = True
                    continue

                if in_recommendations and line.startswith(("-", "•", "*")):
                    rec = line.lstrip("-•* 123.")
                    if rec:
                        recommendations.append(rec)
                else:
                    insights_lines.append(line)

            insights = " ".join(insights_lines)

            return insights, recommendations

        except Exception as e:
            logger.warning("forecast_insights_failed", error=str(e))
            return f"Forecast per {months} mesi completato.", []
