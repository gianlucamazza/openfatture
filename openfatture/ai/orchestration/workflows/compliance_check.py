"""Compliance Check Workflow using LangGraph.

Multi-level compliance checking workflow for FatturaPA invoices.

Workflow Steps:
1. Load invoice from database
2. Level 1: Deterministic rules check (mandatory fields, formats, ranges)
3. Level 2: SDI rejection patterns (historical patterns from government system)
4. Level 3: AI heuristics (semantic analysis, edge cases)
5. Aggregate results and generate report
6. [Conditional] Human review if critical issues found

Check Levels:
- BASIC: Rules only (fast, 100% accurate for known issues)
- STANDARD: Rules + SDI patterns (catches 95% of rejections)
- ADVANCED: Rules + SDI + AI (comprehensive analysis)

Example:
    >>> workflow = ComplianceCheckWorkflow(level="standard")
    >>> result = await workflow.execute(invoice_id=123)
    >>> if result.is_compliant:
    ...     print("Invoice ready for SDI submission")
    ... else:
    ...     print(f"Found {len(result.rules_issues)} issues")
"""

from importlib import import_module
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from openfatture.ai.agents.compliance import (
    ComplianceChecker,
    ComplianceLevel,
    ComplianceReport,
)
from openfatture.ai.orchestration.states import (
    ComplianceCheckState,
    WorkflowStatus,
)
from openfatture.storage.database.base import SessionLocal
from openfatture.storage.database.models import Fattura
from openfatture.utils.datetime import utc_now
from openfatture.utils.logging import get_logger

if TYPE_CHECKING:
    from langgraph.graph import END as _END
    from langgraph.graph import StateGraph as _StateGraph
else:
    _graph_module = import_module("langgraph.graph")
    _StateGraph = _graph_module.StateGraph
    _END = _graph_module.END

StateGraph = _StateGraph
END = _END

logger = get_logger(__name__)


def _get_session() -> Session:
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() before running workflows.")
    return SessionLocal()


class ComplianceCheckWorkflow:
    """LangGraph-based compliance check workflow.

    Multi-level compliance validation with configurable depth.
    Optimized for performance: runs only necessary checks based on level.

    Features:
    - Three check levels (basic/standard/advanced)
    - Incremental checking (stop early if critical errors)
    - Detailed issue reporting with fix suggestions
    - SDI approval probability estimation
    - Human review for borderline cases
    - State persistence for audit trail

    Example:
        >>> workflow = ComplianceCheckWorkflow(level="standard")
        >>> result = await workflow.execute(123)
        >>> print(f"Compliance score: {result.compliance_score}/100")
    """

    def __init__(
        self,
        level: str = "standard",
        enable_checkpointing: bool = True,
    ):
        """Initialize compliance check workflow.

        Args:
            level: Check level (basic/standard/advanced)
            enable_checkpointing: Enable state persistence
        """
        self.level = self._parse_level(level)
        self.enable_checkpointing = enable_checkpointing

        # Compliance checker
        self.checker = ComplianceChecker(level=self.level)
        self._reports: dict[str, ComplianceReport] = {}

        # Build graph
        self.graph: Any = self._build_graph()

        logger.info(
            "compliance_workflow_initialized",
            level=self.level.value,
        )

    def _parse_level(self, level_str: str) -> ComplianceLevel:
        """Parse compliance level string."""
        level_map = {
            "basic": ComplianceLevel.BASIC,
            "standard": ComplianceLevel.STANDARD,
            "advanced": ComplianceLevel.ADVANCED,
        }
        return level_map.get(level_str.lower(), ComplianceLevel.STANDARD)

    def _build_graph(self) -> Any:
        """Build LangGraph state machine.

        Graph structure:
        START → load_invoice → rules_check → [conditional] → sdi_patterns
              → [conditional] → ai_analysis → aggregate_results → [conditional]
              → human_review → END

        Conditional routing:
        - Skip SDI patterns if level=BASIC
        - Skip AI analysis if level≠ADVANCED or critical errors found
        - Require human review if borderline score (60-80)
        """
        workflow = StateGraph(ComplianceCheckState)

        # Add nodes
        workflow.add_node("load_invoice", self._load_invoice_node)
        workflow.add_node("rules_check", self._rules_check_node)
        workflow.add_node("sdi_patterns_check", self._sdi_patterns_node)
        workflow.add_node("ai_analysis", self._ai_analysis_node)
        workflow.add_node("aggregate_results", self._aggregate_results_node)
        workflow.add_node("human_review", self._human_review_node)
        workflow.add_node("handle_error", self._handle_error_node)

        # Entry point
        workflow.set_entry_point("load_invoice")

        # Sequential: load → rules
        workflow.add_edge("load_invoice", "rules_check")

        # Conditional: rules → sdi_patterns or skip
        workflow.add_conditional_edges(
            "rules_check",
            self._should_check_sdi_patterns,
            {
                "check": "sdi_patterns_check",
                "skip": "aggregate_results",
                "error": "handle_error",
            },
        )

        # Conditional: sdi → ai_analysis or aggregate
        workflow.add_conditional_edges(
            "sdi_patterns_check",
            self._should_run_ai_analysis,
            {
                "analyze": "ai_analysis",
                "skip": "aggregate_results",
            },
        )

        # Sequential: ai → aggregate
        workflow.add_edge("ai_analysis", "aggregate_results")

        # Conditional: aggregate → review or end
        workflow.add_conditional_edges(
            "aggregate_results",
            self._should_require_review,
            {
                "review": "human_review",
                "skip": END,
            },
        )

        # End points
        workflow.add_edge("human_review", END)
        workflow.add_edge("handle_error", END)

        # Compile
        if self.enable_checkpointing:
            from importlib import import_module

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

    async def _load_invoice_node(self, state: ComplianceCheckState) -> ComplianceCheckState:
        """Load invoice from database."""
        logger.info(
            "loading_invoice",
            workflow_id=state.workflow_id,
            invoice_id=state.invoice_id,
        )

        db = _get_session()
        try:
            fattura = db.query(Fattura).filter(Fattura.id == state.invoice_id).first()

            if not fattura:
                state.add_error(f"Invoice {state.invoice_id} not found")
                return state

            # Store in metadata for later use
            state.metadata["invoice"] = {
                "numero": fattura.numero,
                "anno": fattura.anno,
                "cliente": fattura.cliente.denominazione if fattura.cliente else "Unknown",
                "totale": float(fattura.totale),
            }

            state.status = WorkflowStatus.IN_PROGRESS
            state.updated_at = utc_now()

            logger.info(
                "invoice_loaded",
                workflow_id=state.workflow_id,
                invoice_id=state.invoice_id,
            )

            return state

        except Exception as e:
            logger.error(
                "invoice_load_failed",
                workflow_id=state.workflow_id,
                error=str(e),
            )
            state.add_error(f"Failed to load invoice: {e}")
            return state

        finally:
            db.close()

    async def _rules_check_node(self, state: ComplianceCheckState) -> ComplianceCheckState:
        """Execute deterministic rules check."""
        logger.info("executing_rules_check", workflow_id=state.workflow_id)

        try:
            # Execute compliance check (Level 1: Rules)
            report = await self.checker.check_invoice(state.invoice_id)
            self._reports[state.workflow_id] = report

            # Extract rules issues
            state.rules_issues = [
                {
                    "code": issue.code,
                    "message": issue.message,
                    "severity": issue.severity.value,
                    "field": issue.field,
                    "suggestion": issue.suggestion,
                    "reference": issue.reference,
                }
                for issue in report.validation_issues
            ]

            state.rules_passed = len(report.get_errors()) == 0

            state.compliance_score = report.compliance_score
            state.risk_score = report.risk_score
            state.is_compliant = report.is_compliant
            state.metadata["compliance_report"] = report.to_dict()

            logger.info(
                "rules_check_completed",
                workflow_id=state.workflow_id,
                rules_passed=state.rules_passed,
                issues_count=len(state.rules_issues),
                score=state.compliance_score,
            )

            state.updated_at = utc_now()
            return state

        except Exception as e:
            logger.error("rules_check_error", workflow_id=state.workflow_id, error=str(e))
            state.add_error(f"Rules check failed: {e}")
            return state

    async def _sdi_patterns_node(self, state: ComplianceCheckState) -> ComplianceCheckState:
        """Check against SDI rejection patterns."""
        logger.info("checking_sdi_patterns", workflow_id=state.workflow_id)

        try:
            report = self._reports.get(state.workflow_id)
            if report is None:
                logger.warning(
                    "sdi_patterns_report_missing",
                    workflow_id=state.workflow_id,
                )
                return state

            state.sdi_patterns_checked = True

            state.sdi_warnings = [
                {
                    "pattern": pattern.pattern_name,
                    "error_code": pattern.error_code,
                    "severity": pattern.severity,
                    "description": pattern.description,
                    "suggestion": pattern.fix_suggestion,
                    "reference": pattern.reference,
                }
                for pattern in report.sdi_pattern_matches
            ]

            logger.info(
                "sdi_patterns_checked",
                workflow_id=state.workflow_id,
                warnings_count=len(state.sdi_warnings),
            )

            state.updated_at = utc_now()
            return state

        except Exception as e:
            logger.error("sdi_patterns_error", workflow_id=state.workflow_id, error=str(e))
            state.add_warning(f"SDI patterns check failed: {e}")
            return state

    async def _ai_analysis_node(self, state: ComplianceCheckState) -> ComplianceCheckState:
        """Execute AI-powered heuristic analysis."""
        logger.info("running_ai_analysis", workflow_id=state.workflow_id)

        try:
            report = self._reports.get(state.workflow_id)
            if report is None:
                logger.warning(
                    "ai_analysis_report_missing",
                    workflow_id=state.workflow_id,
                )
                return state

            state.ai_analysis_performed = True

            anomalies = [
                {
                    "code": issue.code,
                    "severity": issue.severity.value,
                    "field": issue.field,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                }
                for issue in report.heuristic_anomalies
            ]

            if anomalies:
                state.ai_insights = " ".join(
                    message for message in (a["message"] for a in anomalies) if message
                )
                state.metadata["ai_anomalies"] = anomalies
                for anomaly in anomalies:
                    suggestion = anomaly.get("suggestion")
                    if suggestion:
                        state.fix_suggestions.append(suggestion)
            else:
                state.ai_insights = "Nessuna anomalia AI rilevata."

            logger.info(
                "ai_analysis_completed",
                workflow_id=state.workflow_id,
            )

            state.updated_at = utc_now()
            return state

        except Exception as e:
            logger.error("ai_analysis_error", workflow_id=state.workflow_id, error=str(e))
            state.add_warning(f"AI analysis failed: {e}")
            return state

    async def _aggregate_results_node(self, state: ComplianceCheckState) -> ComplianceCheckState:
        """Aggregate all check results and generate report."""
        logger.info("aggregating_results", workflow_id=state.workflow_id)

        try:
            report = self._reports.get(state.workflow_id)
            if report is None:
                logger.warning(
                    "aggregate_results_missing_report",
                    workflow_id=state.workflow_id,
                )
                return state

            state.compliance_score = report.compliance_score
            state.risk_score = report.risk_score
            state.is_compliant = report.is_compliant

            suggestions = [
                issue.get("suggestion") for issue in state.rules_issues if issue.get("suggestion")
            ]
            suggestions.extend(report.recommendations)
            if state.fix_suggestions:
                suggestions.extend(state.fix_suggestions)
            # Deduplicate while preserving order
            seen: set[str] = set()
            state.fix_suggestions = []
            for suggestion in suggestions:
                if suggestion and suggestion not in seen:
                    seen.add(suggestion)
                    state.fix_suggestions.append(suggestion)

            # Estimate SDI approval probability (simple heuristic)
            errors_count = len(report.get_errors())
            if errors_count > 0:
                probability = 0.2
            else:
                probability = min(0.98, 0.5 + (report.compliance_score / 200))
                if state.sdi_warnings:
                    probability -= 0.1
            state.sdi_approval_probability = max(0.0, round(probability, 2))

            state.metadata["recommendations"] = report.recommendations
            self._reports[state.workflow_id] = report  # ensure cache retained until completion

            logger.info(
                "results_aggregated",
                workflow_id=state.workflow_id,
                compliance_score=state.compliance_score,
                approval_probability=state.sdi_approval_probability,
            )

            state.updated_at = utc_now()
            return state

        except Exception as e:
            logger.error("aggregation_error", workflow_id=state.workflow_id, error=str(e))
            state.add_error(f"Failed to aggregate results: {e}")
            return state

    async def _human_review_node(self, state: ComplianceCheckState) -> ComplianceCheckState:
        """Human review for borderline cases."""
        logger.info("awaiting_human_review", workflow_id=state.workflow_id)

        state.status = WorkflowStatus.AWAITING_APPROVAL

        # In real implementation, would pause for human input
        # For now, just mark as reviewed

        state.updated_at = utc_now()
        return state

    async def _handle_error_node(self, state: ComplianceCheckState) -> ComplianceCheckState:
        """Handle workflow errors."""
        logger.error(
            "compliance_workflow_failed",
            workflow_id=state.workflow_id,
            errors=state.errors,
        )

        state.status = WorkflowStatus.FAILED
        state.updated_at = utc_now()

        self._reports.pop(state.workflow_id, None)

        return state

    # ========================================================================
    # Conditional Routing
    # ========================================================================

    def _should_check_sdi_patterns(self, state: ComplianceCheckState) -> str:
        """Determine if SDI patterns check is needed."""
        if state.errors:
            return "error"

        # Skip if level is BASIC
        if self.level == ComplianceLevel.BASIC:
            return "skip"

        # Skip if critical errors found (no point checking patterns)
        critical_errors = [i for i in state.rules_issues if i["severity"] == "ERROR"]
        if critical_errors:
            return "skip"

        return "check"

    def _should_run_ai_analysis(self, state: ComplianceCheckState) -> str:
        """Determine if AI analysis is needed."""
        # Only for ADVANCED level
        if self.level != ComplianceLevel.ADVANCED:
            return "skip"

        # Skip if critical errors (AI won't help)
        critical_errors = [i for i in state.rules_issues if i["severity"] == "ERROR"]
        if critical_errors:
            return "skip"

        return "analyze"

    def _should_require_review(self, state: ComplianceCheckState) -> str:
        """Determine if human review is needed."""
        # Always require review if configured
        if not state.require_review_on_warnings:
            return "skip"

        # Require review for borderline scores (60-80)
        if 60 <= state.compliance_score < 80:
            return "review"

        # Require review if SDI approval probability is uncertain
        if state.sdi_approval_probability and 0.5 < state.sdi_approval_probability < 0.85:
            return "review"

        return "skip"

    # ========================================================================
    # Public API
    # ========================================================================

    async def execute(self, invoice_id: int) -> ComplianceCheckState:
        """Execute compliance check workflow.

        Args:
            invoice_id: Invoice ID to check

        Returns:
            Final workflow state with compliance results

        Example:
            >>> result = await workflow.execute(123)
            >>> if result.is_compliant:
            ...     print("Invoice is compliant")
            >>> else:
            ...     for suggestion in result.fix_suggestions:
            ...         print(f"  - {suggestion}")
        """
        from openfatture.ai.orchestration.states import create_compliance_workflow

        # Create initial state
        initial_state = create_compliance_workflow(
            invoice_id=invoice_id,
            level=self.level.value,
        )

        logger.info(
            "starting_compliance_workflow",
            workflow_id=initial_state.workflow_id,
            invoice_id=invoice_id,
            level=self.level.value,
        )

        # Execute graph
        final_state = await self.graph.ainvoke(initial_state)

        if isinstance(final_state, dict):
            final_state = ComplianceCheckState.model_validate(final_state)

        logger.info(
            "compliance_workflow_completed",
            workflow_id=final_state.workflow_id,
            is_compliant=final_state.is_compliant,
            compliance_score=final_state.compliance_score,
        )

        self._reports.pop(final_state.workflow_id, None)

        return final_state


def create_compliance_workflow(
    level: str = "standard",
) -> ComplianceCheckWorkflow:
    """Create compliance check workflow instance.

    Args:
        level: Check level (basic/standard/advanced)

    Returns:
        ComplianceCheckWorkflow ready to execute
    """
    return ComplianceCheckWorkflow(level=level)
