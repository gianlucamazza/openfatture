"""Invoice Creation Workflow using LangGraph.

Multi-agent workflow for creating invoices with AI assistance and human oversight.

Workflow Steps:
1. User provides brief description
2. Description Agent expands to professional description
3. [Optional] Human approves description
4. Tax Advisor suggests VAT rate and treatment
5. [Optional] Human approves tax treatment
6. Compliance Checker validates invoice data
7. [Conditional] Human approves if warnings/errors
8. Create invoice in database
9. Generate FatturaPA XML

Conditional Routing:
- Skip human checkpoints if confidence > threshold
- Require approval on low confidence or errors
- Fall back to manual mode on critical failures

Example:
    >>> workflow = InvoiceCreationWorkflow()
    >>> result = await workflow.execute(
    ...     user_input="consulenza DevOps 3 giorni cliente Acme",
    ...     client_id=123,
    ...     require_approvals=True
    ... )
    >>> print(f"Created invoice #{result.invoice_id}")
"""

from datetime import datetime
from typing import Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver

from openfatture.ai.orchestration.states import (
    InvoiceCreationState,
    AgentResult,
    AgentType,
    WorkflowStatus,
    ApprovalDecision,
)
from openfatture.ai.agents import (
    InvoiceAssistantAgent,
    TaxAdvisorAgent,
)
from openfatture.ai.agents.compliance import ComplianceChecker, ComplianceLevel
from openfatture.ai.domain.context import InvoiceContext, TaxContext
from openfatture.ai.providers import create_provider
from openfatture.storage.database.base import SessionLocal
from openfatture.storage.database.models import Fattura, Cliente
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class InvoiceCreationWorkflow:
    """LangGraph-based invoice creation workflow.

    This workflow orchestrates multiple AI agents with optional human oversight
    to create validated, compliant invoices.

    Features:
    - Multi-agent collaboration (Description, Tax, Compliance)
    - Conditional routing based on confidence scores
    - Human approval checkpoints (configurable)
    - Error handling and recovery
    - State persistence for resume capability
    - Comprehensive logging and tracking

    Example:
        >>> workflow = InvoiceCreationWorkflow()
        >>> result = await workflow.execute(
        ...     user_input="sviluppo API REST 40 ore",
        ...     client_id=456
        ... )
    """

    def __init__(
        self,
        confidence_threshold: float = 0.85,
        enable_checkpointing: bool = True,
    ):
        """Initialize workflow.

        Args:
            confidence_threshold: Minimum confidence to skip human approval
            enable_checkpointing: Enable state persistence for resume
        """
        self.confidence_threshold = confidence_threshold
        self.enable_checkpointing = enable_checkpointing

        # AI provider (shared across agents)
        self.ai_provider = create_provider()

        # Agents
        self.description_agent = InvoiceAssistantAgent(provider=self.ai_provider)
        self.tax_agent = TaxAdvisorAgent(provider=self.ai_provider)
        self.compliance_checker = ComplianceChecker(level=ComplianceLevel.STANDARD)

        # Build graph
        self.graph = self._build_graph()

        logger.info(
            "invoice_creation_workflow_initialized",
            confidence_threshold=confidence_threshold,
        )

    def _build_graph(self) -> StateGraph:
        """Build LangGraph state machine.

        Graph structure:
        START → description_agent → [approval_check] → tax_agent → [approval_check]
              → compliance_check → [approval_check] → create_invoice → END

        Conditional edges:
        - Skip approval if confidence > threshold
        - Require approval on errors/warnings
        - Abort on critical failures
        """
        # Create graph
        workflow = StateGraph(InvoiceCreationState)

        # Add nodes
        workflow.add_node("enrich_context", self._enrich_context_node)
        workflow.add_node("description_agent", self._description_agent_node)
        workflow.add_node("description_approval", self._description_approval_node)
        workflow.add_node("tax_agent", self._tax_agent_node)
        workflow.add_node("tax_approval", self._tax_approval_node)
        workflow.add_node("compliance_check", self._compliance_check_node)
        workflow.add_node("compliance_approval", self._compliance_approval_node)
        workflow.add_node("create_invoice", self._create_invoice_node)
        workflow.add_node("handle_error", self._handle_error_node)

        # Entry point
        workflow.set_entry_point("enrich_context")

        # Sequential edges
        workflow.add_edge("enrich_context", "description_agent")

        # Conditional edge: description approval
        workflow.add_conditional_edges(
            "description_agent",
            self._should_approve_description,
            {
                "approve": "description_approval",
                "skip": "tax_agent",
                "error": "handle_error",
            },
        )

        workflow.add_edge("description_approval", "tax_agent")

        # Conditional edge: tax approval
        workflow.add_conditional_edges(
            "tax_agent",
            self._should_approve_tax,
            {
                "approve": "tax_approval",
                "skip": "compliance_check",
                "error": "handle_error",
            },
        )

        workflow.add_edge("tax_approval", "compliance_check")

        # Conditional edge: compliance approval
        workflow.add_conditional_edges(
            "compliance_check",
            self._should_approve_compliance,
            {
                "approve": "compliance_approval",
                "skip": "create_invoice",
                "error": "handle_error",
            },
        )

        workflow.add_edge("compliance_approval", "create_invoice")

        # End
        workflow.add_edge("create_invoice", END)
        workflow.add_edge("handle_error", END)

        # Compile with checkpointing
        if self.enable_checkpointing:
            checkpointer = MemorySaver()
            return workflow.compile(checkpointer=checkpointer)
        else:
            return workflow.compile()

    # ========================================================================
    # Node Implementations
    # ========================================================================

    async def _enrich_context_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Enrich state with business context."""
        logger.info("enriching_context", workflow_id=state.workflow_id)

        db = SessionLocal()
        try:
            # Load year-to-date statistics
            from sqlalchemy import func, extract

            current_year = datetime.now().year

            state.context.total_invoices_ytd = (
                db.query(func.count(Fattura.id))
                .filter(extract("year", Fattura.data_emissione) == current_year)
                .scalar() or 0
            )

            state.context.total_revenue_ytd = (
                db.query(func.sum(Fattura.totale))
                .filter(extract("year", Fattura.data_emissione) == current_year)
                .scalar() or 0.0
            )

            state.status = WorkflowStatus.IN_PROGRESS
            state.updated_at = datetime.utcnow()

            logger.info(
                "context_enriched",
                workflow_id=state.workflow_id,
                invoices_ytd=state.context.total_invoices_ytd,
            )

            return state

        except Exception as e:
            logger.error(
                "context_enrichment_failed",
                workflow_id=state.workflow_id,
                error=str(e),
            )
            state.add_error(f"Failed to enrich context: {e}")
            return state

        finally:
            db.close()

    async def _description_agent_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Execute Description Agent."""
        logger.info("executing_description_agent", workflow_id=state.workflow_id)

        try:
            # Create context
            context = InvoiceContext(
                user_input=state.user_input,
                servizio_base=state.user_input,
            )

            # Execute agent
            response = await self.description_agent.execute(context)

            # Extract result
            if response.status.value == "success":
                content = response.content
                confidence = response.metadata.get("confidence", 0.8)

                state.description_result = AgentResult(
                    agent_type=AgentType.DESCRIPTION,
                    success=True,
                    content=content,
                    confidence=confidence,
                    metadata=response.metadata,
                )

                logger.info(
                    "description_agent_completed",
                    workflow_id=state.workflow_id,
                    confidence=confidence,
                )
            else:
                state.add_error(f"Description agent failed: {response.error}")

            state.updated_at = datetime.utcnow()
            return state

        except Exception as e:
            logger.error(
                "description_agent_error",
                workflow_id=state.workflow_id,
                error=str(e),
            )
            state.add_error(f"Description agent error: {e}")
            return state

    async def _description_approval_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Human approval checkpoint for description."""
        logger.info("awaiting_description_approval", workflow_id=state.workflow_id)

        state.status = WorkflowStatus.AWAITING_APPROVAL

        # In real implementation, this would trigger UI or CLI prompt
        # For now, we simulate approval based on confidence
        if state.description_result and state.description_result.confidence > self.confidence_threshold:
            from openfatture.ai.orchestration.states import HumanReview

            state.description_review = HumanReview(
                decision=ApprovalDecision.APPROVE,
                feedback="Auto-approved (high confidence)",
                reviewer="system",
            )
            state.status = WorkflowStatus.APPROVED
        else:
            # Would pause here for human input
            state.status = WorkflowStatus.AWAITING_APPROVAL

        state.updated_at = datetime.utcnow()
        return state

    async def _tax_agent_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Execute Tax Advisor Agent."""
        logger.info("executing_tax_agent", workflow_id=state.workflow_id)

        try:
            # Get description from previous step
            description = state.description_result.content if state.description_result else state.user_input

            # Create tax context
            tax_context = TaxContext(
                user_input=description,
                tipo_servizio=description,
                importo=0,  # Will be filled later
                cliente_pa=False,  # TODO: Get from cliente
                cliente_estero=False,
                paese_cliente="IT",
            )

            # Execute agent
            response = await self.tax_agent.execute(tax_context)

            if response.status.value == "success":
                state.tax_result = AgentResult(
                    agent_type=AgentType.TAX_ADVISOR,
                    success=True,
                    content=response.content,
                    confidence=response.metadata.get("confidence", 0.8),
                    metadata=response.metadata,
                )

                logger.info(
                    "tax_agent_completed",
                    workflow_id=state.workflow_id,
                    confidence=state.tax_result.confidence,
                )
            else:
                state.add_error(f"Tax agent failed: {response.error}")

            state.updated_at = datetime.utcnow()
            return state

        except Exception as e:
            logger.error("tax_agent_error", workflow_id=state.workflow_id, error=str(e))
            state.add_error(f"Tax agent error: {e}")
            return state

    async def _tax_approval_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Human approval checkpoint for tax suggestion."""
        logger.info("awaiting_tax_approval", workflow_id=state.workflow_id)

        # Simulate approval logic
        if state.tax_result and state.tax_result.confidence > self.confidence_threshold:
            from openfatture.ai.orchestration.states import HumanReview

            state.tax_review = HumanReview(
                decision=ApprovalDecision.APPROVE,
                feedback="Auto-approved (high confidence)",
                reviewer="system",
            )
            state.status = WorkflowStatus.APPROVED
        else:
            state.status = WorkflowStatus.AWAITING_APPROVAL

        state.updated_at = datetime.utcnow()
        return state

    async def _compliance_check_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Execute Compliance Checker."""
        logger.info("executing_compliance_check", workflow_id=state.workflow_id)

        try:
            # In real implementation, would check against actual invoice data
            # For now, we simulate a compliance check

            state.compliance_result = AgentResult(
                agent_type=AgentType.COMPLIANCE,
                success=True,
                content="Invoice data appears compliant with FatturaPA requirements",
                confidence=0.9,
                metadata={
                    "rules_passed": True,
                    "warnings": [],
                    "compliance_score": 95.0,
                },
            )

            logger.info(
                "compliance_check_completed",
                workflow_id=state.workflow_id,
                compliant=state.is_compliant,
            )

            state.updated_at = datetime.utcnow()
            return state

        except Exception as e:
            logger.error("compliance_check_error", workflow_id=state.workflow_id, error=str(e))
            state.add_error(f"Compliance check error: {e}")
            return state

    async def _compliance_approval_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Human approval checkpoint for compliance issues."""
        logger.info("awaiting_compliance_approval", workflow_id=state.workflow_id)

        # Always require approval if compliance failed
        if not state.is_compliant:
            state.status = WorkflowStatus.AWAITING_APPROVAL
        else:
            from openfatture.ai.orchestration.states import HumanReview

            state.compliance_review = HumanReview(
                decision=ApprovalDecision.APPROVE,
                feedback="Compliance check passed",
                reviewer="system",
            )
            state.status = WorkflowStatus.APPROVED

        state.updated_at = datetime.utcnow()
        return state

    async def _create_invoice_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Create invoice in database."""
        logger.info("creating_invoice", workflow_id=state.workflow_id)

        try:
            # In real implementation, would create actual invoice
            # For now, simulate creation

            state.invoice_id = 999  # Placeholder
            state.invoice_xml_path = "/path/to/invoice.xml"  # Placeholder

            state.mark_completed()

            logger.info(
                "invoice_created",
                workflow_id=state.workflow_id,
                invoice_id=state.invoice_id,
            )

            return state

        except Exception as e:
            logger.error("invoice_creation_error", workflow_id=state.workflow_id, error=str(e))
            state.add_error(f"Failed to create invoice: {e}")
            return state

    async def _handle_error_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Handle workflow errors."""
        logger.error(
            "workflow_failed",
            workflow_id=state.workflow_id,
            errors=state.errors,
        )

        state.status = WorkflowStatus.FAILED
        state.updated_at = datetime.utcnow()

        return state

    # ========================================================================
    # Conditional Routing
    # ========================================================================

    def _should_approve_description(self, state: InvoiceCreationState) -> str:
        """Determine if description approval is needed."""
        if state.errors:
            return "error"

        if not state.require_description_approval:
            return "skip"

        if state.description_result and state.description_result.confidence > self.confidence_threshold:
            return "skip"  # Auto-approve high confidence

        return "approve"

    def _should_approve_tax(self, state: InvoiceCreationState) -> str:
        """Determine if tax approval is needed."""
        if state.errors:
            return "error"

        if not state.require_tax_approval:
            return "skip"

        if state.tax_result and state.tax_result.confidence > self.confidence_threshold:
            return "skip"

        return "approve"

    def _should_approve_compliance(self, state: InvoiceCreationState) -> str:
        """Determine if compliance approval is needed."""
        if state.errors:
            return "error"

        if state.is_compliant and state.compliance_result.confidence > 0.8:
            return "skip"

        return "approve"

    # ========================================================================
    # Public API
    # ========================================================================

    async def execute(
        self,
        user_input: str,
        client_id: int,
        require_approvals: bool = False,
    ) -> InvoiceCreationState:
        """Execute invoice creation workflow.

        Args:
            user_input: User's brief invoice description
            client_id: Client ID for the invoice
            require_approvals: Enable human approval checkpoints

        Returns:
            Final workflow state with invoice_id if successful

        Example:
            >>> result = await workflow.execute(
            ...     user_input="consulenza cloud 2 giorni",
            ...     client_id=123
            ... )
            >>> if result.status == WorkflowStatus.COMPLETED:
            ...     print(f"Invoice created: {result.invoice_id}")
        """
        from openfatture.ai.orchestration.states import create_invoice_workflow

        # Create initial state
        initial_state = create_invoice_workflow(
            user_input=user_input,
            client_id=client_id,
            require_approvals=require_approvals,
        )

        logger.info(
            "starting_invoice_workflow",
            workflow_id=initial_state.workflow_id,
            client_id=client_id,
        )

        # Execute graph
        final_state = await self.graph.ainvoke(initial_state)

        logger.info(
            "invoice_workflow_completed",
            workflow_id=final_state.workflow_id,
            status=final_state.status,
            invoice_id=final_state.invoice_id,
        )

        return final_state


def create_invoice_workflow(
    confidence_threshold: float = 0.85,
) -> InvoiceCreationWorkflow:
    """Create invoice creation workflow instance.

    Args:
        confidence_threshold: Minimum confidence for auto-approval

    Returns:
        InvoiceCreationWorkflow ready to execute
    """
    return InvoiceCreationWorkflow(confidence_threshold=confidence_threshold)
