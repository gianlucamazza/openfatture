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

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from openfatture.ai.domain.message import Message
from openfatture.ai.ml.config import MLConfig, get_ml_config
from openfatture.ai.ml.data_loader import InvoiceDataLoader
from openfatture.ai.ml.features import FeaturePipeline
from openfatture.ai.ml.models import CashFlowEnsemble
from openfatture.ai.providers import create_provider
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.storage.database.base import SessionLocal
from openfatture.storage.database.models import Fattura, StatoFattura
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


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
        db = SessionLocal()
        try:
            fattura = db.query(Fattura).filter(Fattura.id == invoice_id).first()

            if not fattura:
                raise ValueError(f"Invoice {invoice_id} not found")

            # Convert to DataFrame row
            X_row = self._invoice_to_features(fattura)

            # Extract features
            if self.feature_pipeline is None:
                raise RuntimeError(
                    "Feature pipeline not initialized. Call initialize() first."
                )
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
        db = SessionLocal()
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
                    result = await self.predict_invoice(fattura.id, include_insights=False)

                    # Calculate expected payment date
                    expected_payment_date = fattura.data_emissione + timedelta(
                        days=result.expected_days
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

        # Fit feature pipeline
        if self.feature_pipeline is None:
            raise RuntimeError("Feature pipeline not initialized. Call initialize() first.")
        self.feature_pipeline.fit(dataset.X_train, dataset.y_train)

        # Transform features
        X_train_features = self.feature_pipeline.transform(dataset.X_train)
        X_val_features = self.feature_pipeline.transform(dataset.X_val)
        X_test_features = self.feature_pipeline.transform(dataset.X_test)

        # Train ensemble
        if self.ensemble is None:
            raise RuntimeError("Ensemble model not initialized. Call initialize() first.")
        self.ensemble.fit(
            X_train_features,
            dataset.y_train,
            X_val_features,
            dataset.y_val,
        )

        # Evaluate on test set
        if self.ensemble is None:
            raise RuntimeError("Ensemble model not initialized. Call initialize() first.")
        test_mae = self.ensemble.score(X_test_features, dataset.y_test)

        logger.info("models_trained", test_mae=test_mae)

        # Save models
        model_path = self.config.get_model_filepath("cash_flow")
        await self._save_models(model_path)

        self.model_trained_ = True

    async def _save_models(self, filepath_prefix: str) -> None:
        """Save trained models to disk."""
        if self.ensemble is None:
            raise RuntimeError("Ensemble model not initialized. Cannot save.")
        self.ensemble.save(filepath_prefix)

        logger.info("models_saved", path=filepath_prefix)

    async def _load_models(self, filepath_prefix: str) -> None:
        """Load models from disk."""
        self.ensemble = CashFlowEnsemble.load(filepath_prefix)
        self.model_trained_ = True

        logger.info("models_loaded", path=filepath_prefix)

    def _models_exist(self, filepath_prefix: str) -> bool:
        """Check if saved models exist."""
        prophet_path = Path(f"{filepath_prefix}_prophet.json")
        xgboost_path = Path(f"{filepath_prefix}_xgboost.json")

        return prophet_path.exists() and xgboost_path.exists()

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
            messages = [Message(role="user", content=prompt)]
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
            messages = [Message(role="user", content=prompt)]
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
