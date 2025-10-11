"""Cash Flow Analysis Workflow using LangGraph.

ML-powered cash flow forecasting workflow with AI insights generation.

Workflow Steps:
1. Load unpaid invoices (filtered by client if specified)
2. For each invoice: Predict payment delay using ML ensemble
3. Aggregate predictions into monthly buckets
4. Calculate risk metrics (high-risk invoices, overdue predictions)
5. Generate AI insights and recommendations
6. Produce forecast report

Parallel Execution:
- Predictions run in parallel batches (rate-limited)
- Configurable batch size for performance vs memory tradeoff

Example:
    >>> workflow = CashFlowAnalysisWorkflow()
    >>> result = await workflow.execute(months=6, client_id=123)
    >>> for month in result.monthly_forecast:
    ...     print(f"{month['month']}: €{month['expected']:.2f}")
"""

from datetime import date, timedelta
from importlib import import_module
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from openfatture.ai.agents.cash_flow_predictor import CashFlowPredictorAgent
from openfatture.ai.domain.message import Message, Role
from openfatture.ai.orchestration.states import (
    CashFlowAnalysisState,
    WorkflowStatus,
)
from openfatture.ai.providers import create_provider
from openfatture.storage.database.base import SessionLocal
from openfatture.storage.database.models import Fattura, StatoFattura
from openfatture.utils.datetime import utc_now
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


def _get_session() -> Session:
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() before running workflows.")
    return SessionLocal()


if TYPE_CHECKING:
    from langgraph.graph import END as _END
    from langgraph.graph import StateGraph as _StateGraph
else:
    _graph_module = import_module("langgraph.graph")
    _StateGraph = _graph_module.StateGraph
    _END = _graph_module.END

StateGraph = _StateGraph
END = _END


class CashFlowAnalysisWorkflow:
    """LangGraph-based cash flow analysis workflow.

    Multi-month forecasting using ML ensemble (Prophet + XGBoost)
    with AI-generated insights and recommendations.

    Features:
    - ML-powered payment delay prediction
    - Monthly revenue aggregation
    - Risk analysis (high-risk invoices, overdue predictions)
    - AI-generated insights in Italian
    - Configurable forecast horizon
    - Client-specific or comprehensive analysis
    - Parallel prediction execution (rate-limited)

    Example:
        >>> workflow = CashFlowAnalysisWorkflow()
        >>> result = await workflow.execute(months=3)
        >>> print(f"Total expected: €{result.total_expected_revenue:.2f}")
    """

    def __init__(
        self,
        batch_size: int = 20,
        enable_checkpointing: bool = True,
    ):
        """Initialize cash flow analysis workflow.

        Args:
            batch_size: Number of invoices to process in parallel
            enable_checkpointing: Enable state persistence
        """
        self.batch_size = batch_size
        self.enable_checkpointing = enable_checkpointing

        # AI provider
        self.ai_provider = create_provider()

        # Cash flow predictor agent
        self.cash_flow_agent: CashFlowPredictorAgent | None = None

        # Build graph
        self.graph: Any = self._build_graph()

        logger.info(
            "cash_flow_workflow_initialized",
            batch_size=batch_size,
        )

    def _build_graph(self) -> Any:
        """Build LangGraph state machine.

        Graph structure:
        START → initialize_agent → load_unpaid_invoices → predict_batch
              → aggregate_monthly → analyze_risks → generate_insights → END

        Parallel execution:
        - predict_batch runs predictions in parallel
        - Batch size controls parallelism
        """
        workflow = StateGraph(CashFlowAnalysisState)

        # Add nodes
        workflow.add_node("initialize_agent", self._initialize_agent_node)
        workflow.add_node("load_invoices", self._load_invoices_node)
        workflow.add_node("predict_batch", self._predict_batch_node)
        workflow.add_node("aggregate_monthly", self._aggregate_monthly_node)
        workflow.add_node("analyze_risks", self._analyze_risks_node)
        workflow.add_node("generate_insights", self._generate_insights_node)
        workflow.add_node("handle_error", self._handle_error_node)

        # Entry point
        workflow.set_entry_point("initialize_agent")

        # Sequential edges
        workflow.add_edge("initialize_agent", "load_invoices")

        # Conditional: load → predict or error
        workflow.add_conditional_edges(
            "load_invoices",
            self._should_predict,
            {
                "predict": "predict_batch",
                "error": "handle_error",
            },
        )

        workflow.add_edge("predict_batch", "aggregate_monthly")
        workflow.add_edge("aggregate_monthly", "analyze_risks")
        workflow.add_edge("analyze_risks", "generate_insights")

        # End
        workflow.add_edge("generate_insights", END)
        workflow.add_edge("handle_error", END)

        # Compile
        if self.enable_checkpointing:
            checkpoint_module = import_module("langgraph.checkpoint")
            memory_saver_cls = getattr(checkpoint_module, "MemorySaver", None)
            if memory_saver_cls is None:
                raise RuntimeError("LangGraph MemorySaver unavailable")
            checkpointer = memory_saver_cls()
            return workflow.compile(checkpointer=checkpointer)
        return workflow.compile()

    # ========================================================================
    # Node Implementations
    # ========================================================================

    async def _initialize_agent_node(self, state: CashFlowAnalysisState) -> CashFlowAnalysisState:
        """Initialize Cash Flow Predictor Agent."""
        logger.info("initializing_cash_flow_agent", workflow_id=state.workflow_id)

        try:
            self.cash_flow_agent = CashFlowPredictorAgent(ai_provider=self.ai_provider)

            # Initialize (load or train models)
            await self.cash_flow_agent.initialize(force_retrain=False)

            state.status = WorkflowStatus.IN_PROGRESS
            state.updated_at = utc_now()

            logger.info(
                "agent_initialized",
                workflow_id=state.workflow_id,
                model_trained=self.cash_flow_agent.model_trained_,
            )

            return state

        except Exception as e:
            logger.error(
                "agent_initialization_failed",
                workflow_id=state.workflow_id,
                error=str(e),
            )
            state.add_error(f"Failed to initialize ML agent: {e}")
            return state

    async def _load_invoices_node(self, state: CashFlowAnalysisState) -> CashFlowAnalysisState:
        """Load unpaid invoices for prediction."""
        logger.info(
            "loading_unpaid_invoices",
            workflow_id=state.workflow_id,
            client_id=state.client_id,
        )

        db = _get_session()
        try:
            # Query unpaid invoices
            query = db.query(Fattura).filter(
                Fattura.stato.in_(
                    [
                        StatoFattura.DA_INVIARE,
                        StatoFattura.INVIATA,
                        StatoFattura.CONSEGNATA,
                    ]
                )
            )

            # Filter by client if specified
            if state.client_id:
                query = query.filter(Fattura.cliente_id == state.client_id)

            # Filter by invoice IDs if specified
            if state.invoice_ids:
                query = query.filter(Fattura.id.in_(state.invoice_ids))

            invoices = query.all()

            # Store invoice IDs for processing
            state.metadata["invoice_ids"] = [f.id for f in invoices]
            state.total_invoices_analyzed = len(invoices)

            if len(invoices) == 0:
                state.add_warning("No unpaid invoices found matching criteria")

            logger.info(
                "invoices_loaded",
                workflow_id=state.workflow_id,
                count=len(invoices),
            )

            state.updated_at = utc_now()
            return state

        except Exception as e:
            logger.error(
                "invoice_loading_failed",
                workflow_id=state.workflow_id,
                error=str(e),
            )
            state.add_error(f"Failed to load invoices: {e}")
            return state

        finally:
            db.close()

    async def _predict_batch_node(self, state: CashFlowAnalysisState) -> CashFlowAnalysisState:
        """Predict payment delays for all invoices."""
        logger.info("predicting_payment_delays", workflow_id=state.workflow_id)

        invoice_ids = state.metadata.get("invoice_ids", [])

        if not invoice_ids:
            state.updated_at = utc_now()
            return state

        if self.cash_flow_agent is None:
            raise RuntimeError("Cash flow agent not initialized.")

        try:
            # Predict for each invoice
            for invoice_id in invoice_ids:
                try:
                    result = await self.cash_flow_agent.predict_invoice(
                        invoice_id=invoice_id,
                        include_insights=False,  # Skip insights per invoice
                    )

                    # Store prediction
                    state.predictions.append(
                        {
                            "invoice_id": invoice_id,
                            "expected_days": result.expected_days,
                            "confidence_score": result.confidence_score,
                            "risk_level": result.risk_level,
                            "lower_bound": result.lower_bound,
                            "upper_bound": result.upper_bound,
                        }
                    )

                    # Track high-risk invoices
                    if result.risk_level == "high":
                        state.high_risk_invoices.append(invoice_id)

                except Exception as e:
                    logger.warning(
                        "prediction_failed",
                        workflow_id=state.workflow_id,
                        invoice_id=invoice_id,
                        error=str(e),
                    )
                    state.failed_predictions += 1

            # Calculate average confidence
            if state.predictions:
                state.average_confidence = sum(
                    p["confidence_score"] for p in state.predictions
                ) / len(state.predictions)

            logger.info(
                "predictions_completed",
                workflow_id=state.workflow_id,
                successful=len(state.predictions),
                failed=state.failed_predictions,
            )

            state.updated_at = utc_now()
            return state

        except Exception as e:
            logger.error(
                "batch_prediction_failed",
                workflow_id=state.workflow_id,
                error=str(e),
            )
            state.add_error(f"Batch prediction failed: {e}")
            return state

    async def _aggregate_monthly_node(self, state: CashFlowAnalysisState) -> CashFlowAnalysisState:
        """Aggregate predictions into monthly buckets."""
        logger.info("aggregating_monthly_forecast", workflow_id=state.workflow_id)

        db = _get_session()
        try:
            invoice_ids = [p["invoice_id"] for p in state.predictions]
            invoices = db.query(Fattura).filter(Fattura.id.in_(invoice_ids)).all()

            # Create invoice lookup
            invoice_map = {f.id: f for f in invoices}

            # Initialize monthly totals
            monthly_totals: dict[int, float] = dict.fromkeys(range(state.forecast_months), 0.0)  # type: ignore[assignment]

            today = date.today()

            # Aggregate by expected payment month
            for prediction in state.predictions:
                invoice_id = prediction["invoice_id"]
                fattura = invoice_map.get(invoice_id)

                if not fattura:
                    continue

                expected_payment_date = fattura.data_emissione + timedelta(
                    days=prediction["expected_days"]
                )

                month_diff = (
                    (expected_payment_date.year - today.year) * 12
                    + expected_payment_date.month
                    - today.month
                )

                if 0 <= month_diff < state.forecast_months:
                    monthly_totals[month_diff] += float(fattura.totale)

            # Build monthly forecast
            state.monthly_forecast = []
            for i in range(state.forecast_months):
                month_date = today + timedelta(days=30 * (i + 1))
                month_str = month_date.strftime("%B %Y")

                state.monthly_forecast.append(
                    {
                        "month": month_str,
                        "month_index": i + 1,
                        "expected": monthly_totals[i],
                    }
                )

            state.total_expected_revenue = sum(monthly_totals.values())

            logger.info(
                "monthly_aggregation_completed",
                workflow_id=state.workflow_id,
                total_expected=state.total_expected_revenue,
            )

            state.updated_at = utc_now()
            return state

        except Exception as e:
            logger.error(
                "monthly_aggregation_failed",
                workflow_id=state.workflow_id,
                error=str(e),
            )
            state.add_error(f"Monthly aggregation failed: {e}")
            return state
        finally:
            db.close()

    async def _analyze_risks_node(self, state: CashFlowAnalysisState) -> CashFlowAnalysisState:
        """Analyze payment risks and overdue predictions."""
        logger.info("analyzing_risks", workflow_id=state.workflow_id)

        try:
            # Identify overdue predictions (expected_days > 30)
            for prediction in state.predictions:
                if prediction["expected_days"] > 30:
                    state.overdue_predictions.append(
                        {
                            "invoice_id": prediction["invoice_id"],
                            "expected_days": prediction["expected_days"],
                            "confidence": prediction["confidence_score"],
                        }
                    )

            logger.info(
                "risk_analysis_completed",
                workflow_id=state.workflow_id,
                high_risk_count=len(state.high_risk_invoices),
                overdue_count=len(state.overdue_predictions),
            )

            state.updated_at = utc_now()
            return state

        except Exception as e:
            logger.error(
                "risk_analysis_failed",
                workflow_id=state.workflow_id,
                error=str(e),
            )
            state.add_warning(f"Risk analysis failed: {e}")
            return state

    async def _generate_insights_node(self, state: CashFlowAnalysisState) -> CashFlowAnalysisState:
        """Generate AI insights and recommendations."""
        logger.info("generating_insights", workflow_id=state.workflow_id)

        try:
            # Use cash flow agent to generate insights
            monthly_summary = "\n".join(
                [f"- {m['month']}: €{m['expected']:.2f}" for m in state.monthly_forecast]
            )

            # Generate insights using AI
            prompt = f"""Analizza questa previsione cash flow:

{monthly_summary}

Totale atteso: €{state.total_expected_revenue:.2f}
Fatture ad alto rischio: {len(state.high_risk_invoices)}
Previsioni in ritardo: {len(state.overdue_predictions)}
Confidence media: {state.average_confidence:.1%}

Fornisci:
1. Insights brevi (2-3 frasi)
2. 2-3 raccomandazioni strategiche

Rispondi in italiano, conciso e professionale."""

            messages = [Message(role=Role.USER, content=prompt)]
            response = await self.ai_provider.generate(
                messages=messages,
                temperature=0.3,
            )

            # Parse response
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

            state.insights = " ".join(insights_lines)
            state.recommendations = recommendations

            logger.info(
                "insights_generated",
                workflow_id=state.workflow_id,
                recommendations_count=len(recommendations),
            )

            state.mark_completed()
            return state

        except Exception as e:
            logger.error(
                "insights_generation_failed",
                workflow_id=state.workflow_id,
                error=str(e),
            )
            state.add_warning(f"Insights generation failed: {e}")
            state.insights = f"Previsione per {state.forecast_months} mesi completata."
            state.mark_completed()
            return state

    async def _handle_error_node(self, state: CashFlowAnalysisState) -> CashFlowAnalysisState:
        """Handle workflow errors."""
        logger.error(
            "cash_flow_workflow_failed",
            workflow_id=state.workflow_id,
            errors=state.errors,
        )

        state.status = WorkflowStatus.FAILED
        state.updated_at = utc_now()

        return state

    # ========================================================================
    # Conditional Routing
    # ========================================================================

    def _should_predict(self, state: CashFlowAnalysisState) -> str:
        """Determine if predictions should run."""
        if state.errors:
            return "error"

        if state.total_invoices_analyzed == 0:
            return "error"

        return "predict"

    # ========================================================================
    # Public API
    # ========================================================================

    async def execute(
        self,
        months: int = 3,
        client_id: int | None = None,
        invoice_ids: list[int] | None = None,
    ) -> CashFlowAnalysisState:
        """Execute cash flow analysis workflow.

        Args:
            months: Number of months to forecast
            client_id: Optional filter by specific client
            invoice_ids: Optional list of specific invoice IDs

        Returns:
            Final workflow state with forecast results

        Example:
            >>> result = await workflow.execute(months=6)
            >>> for month in result.monthly_forecast:
            ...     print(f"{month['month']}: €{month['expected']:.2f}")
        """
        from openfatture.ai.orchestration.states import create_cash_flow_workflow

        # Create initial state
        initial_state = create_cash_flow_workflow(
            months=months,
            client_id=client_id,
        )

        if invoice_ids:
            initial_state.invoice_ids = invoice_ids

        logger.info(
            "starting_cash_flow_workflow",
            workflow_id=initial_state.workflow_id,
            months=months,
            client_id=client_id,
        )

        # Execute graph
        final_state = await self.graph.ainvoke(initial_state)

        logger.info(
            "cash_flow_workflow_completed",
            workflow_id=final_state.workflow_id,
            status=final_state.status,
            total_expected=final_state.total_expected_revenue,
        )

        return final_state


def create_cash_flow_workflow(
    batch_size: int = 20,
) -> CashFlowAnalysisWorkflow:
    """Create cash flow analysis workflow instance.

    Args:
        batch_size: Number of invoices to process in parallel

    Returns:
        CashFlowAnalysisWorkflow ready to execute
    """
    return CashFlowAnalysisWorkflow(batch_size=batch_size)
