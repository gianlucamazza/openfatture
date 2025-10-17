"""Workflow State Models for LangGraph Orchestration.

Pydantic-based state management for multi-agent workflows.
Each state model represents the complete state at each workflow step,
enabling:
- Type-safe state transitions
- Validation at each step
- Persistent checkpointing
- Human-in-the-loop decision points
- Conditional routing based on state

Architecture:
- BaseWorkflowState: Common fields (correlation_id, timestamps, metadata)
- Specific states: InvoiceCreationState, ComplianceCheckState, etc.
- SharedContext: Business data shared across agents
- AgentResult: Standardized agent output format

Example:
    >>> state = InvoiceCreationState(
    ...     user_input="consulenza Python 5h",
    ...     correlation_id="req-123"
    ... )
    >>> # Agent updates state
    >>> state.description_result = DescriptionResult(
    ...     content="Consulenza tecnica Python...",
    ...     confidence=0.92
    ... )
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from openfatture.utils.datetime import utc_now


class WorkflowStatus(Enum):
    """Workflow execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ApprovalDecision(Enum):
    """Human approval decision."""

    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    SKIP = "skip"


class AgentType(Enum):
    """Available agent types."""

    DESCRIPTION = "description"
    TAX_ADVISOR = "tax_advisor"
    COMPLIANCE = "compliance"
    CASH_FLOW = "cash_flow"
    CHAT = "chat"


# ============================================================================
# Base Models
# ============================================================================


class AgentResult(BaseModel):
    """Standardized agent execution result.

    All agents return this format for consistency across workflows.
    """

    agent_type: AgentType
    success: bool
    content: str
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score (0-1)")
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    timestamp: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True)


class HumanReview(BaseModel):
    """Human review decision."""

    decision: ApprovalDecision
    feedback: str | None = None
    reviewer: str | None = None
    timestamp: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True)


class SharedContext(BaseModel):
    """Business context shared across all agents in workflow.

    Populated once at workflow start to avoid repeated DB queries.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        # Allow dict input for LangGraph compatibility
        extra="ignore",
        # Ensure proper serialization for LangGraph
        json_encoders={
            datetime: lambda v: v.isoformat(),
        },
    )

    # Current year statistics
    total_invoices_ytd: int = 0
    total_revenue_ytd: float = 0.0
    unpaid_invoices_count: int = 0
    unpaid_invoices_value: float = 0.0

    # Recent data summaries
    recent_clients: list[dict[str, Any]] = Field(default_factory=list)
    recent_invoices: list[dict[str, Any]] = Field(default_factory=list)

    # User preferences
    default_tax_regime: str | None = None
    default_payment_terms: int = 30  # days

    # Metadata
    loaded_at: datetime = Field(default_factory=utc_now)


class BaseWorkflowState(BaseModel):
    """Base state for all workflows.

    Contains common fields required by all workflow types.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        # Allow arbitrary types for LangGraph compatibility
        arbitrary_types_allowed=True,
    )

    # Workflow tracking
    workflow_id: str = Field(default_factory=lambda: str(uuid4()))
    correlation_id: str | None = None
    # Use string type directly for LangGraph compatibility
    status: str = "pending"

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None

    # Shared context (stored as dict for LangGraph compatibility)
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("context", mode="before")
    @classmethod
    def validate_context(cls, v: Any) -> dict[str, Any]:
        """Convert SharedContext to dict if needed."""
        if isinstance(v, SharedContext):
            return v.model_dump()
        return v

    # Error handling
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Metadata for extensibility
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_error(self, error: str) -> None:
        """Add error and update status."""
        self.errors.append(error)
        self.status = "failed"
        self.updated_at = utc_now()

    def add_warning(self, warning: str) -> None:
        """Add warning."""
        self.warnings.append(warning)
        self.updated_at = utc_now()

    def mark_completed(self) -> None:
        """Mark workflow as completed."""
        self.status = "completed"
        now = utc_now()
        self.completed_at = now
        self.updated_at = now


# ============================================================================
# Invoice Creation Workflow State
# ============================================================================


class InvoiceCreationState(BaseWorkflowState):
    """State for Invoice Creation workflow.

    Workflow: User Input → Description Agent → Tax Advisor → Compliance → Create

    Human approval checkpoints:
    1. After Description (optional)
    2. After Tax Suggestion (optional)
    3. After Compliance Check (if warnings/errors)

    Example:
        >>> state = InvoiceCreationState(
        ...     user_input="consulenza DevOps 3 giorni",
        ...     client_id=123
        ... )
    """

    # User inputs
    user_input: str
    client_id: int
    invoice_date: date | None = None
    payment_due_date: date | None = None

    # Financial inputs
    imponibile_target: Decimal = Field(default_factory=lambda: Decimal("0.00"))
    vat_rate: Decimal = Field(default_factory=lambda: Decimal("22.00"))
    hours: float | None = None
    hourly_rate: Decimal | None = None
    payment_terms_days: int = 30

    # Generated data
    line_items: list[dict[str, Any]] = Field(default_factory=list)
    tax_details: dict[str, Any] = Field(default_factory=dict)
    invoice_number: str | None = None

    # Agent results (populated by workflow)
    description_result: AgentResult | None = None
    tax_result: AgentResult | None = None
    compliance_result: AgentResult | None = None

    # Human reviews (if checkpoints enabled)
    description_review: HumanReview | None = None
    tax_review: HumanReview | None = None
    compliance_review: HumanReview | None = None

    # Final output
    invoice_id: int | None = None
    invoice_xml_path: str | None = None

    # Configuration
    require_description_approval: bool = False
    require_tax_approval: bool = False
    require_compliance_approval: bool = True  # Always for errors

    @property
    def is_description_approved(self) -> bool:
        """Check if description was approved (or no review required)."""
        if not self.require_description_approval:
            return True
        if not self.description_review:
            return False
        return self.description_review.decision == "approve"

    @property
    def is_tax_approved(self) -> bool:
        """Check if tax suggestion was approved."""
        if not self.require_tax_approval:
            return True
        if not self.tax_review:
            return False
        return self.tax_review.decision == "approve"

    @property
    def is_compliant(self) -> bool:
        """Check if compliance check passed."""
        if not self.compliance_result:
            return False
        return self.compliance_result.success and self.compliance_result.confidence > 0.8


# ============================================================================
# Compliance Check Workflow State
# ============================================================================


class ComplianceCheckState(BaseWorkflowState):
    """State for Compliance Check workflow.

    Workflow: Load Invoice → Rules Check → Heuristics → SDI Patterns → AI Analysis

    Multi-level compliance checking:
    - Level 1 (BASIC): Deterministic rules only
    - Level 2 (STANDARD): Rules + SDI rejection patterns
    - Level 3 (ADVANCED): Rules + SDI + AI heuristics
    """

    # Input
    invoice_id: int
    check_level: str = "standard"  # basic, standard, advanced

    # Check results
    rules_passed: bool = False
    rules_issues: list[dict[str, Any]] = Field(default_factory=list)

    sdi_patterns_checked: bool = False
    sdi_warnings: list[dict[str, Any]] = Field(default_factory=list)

    ai_analysis_performed: bool = False
    ai_insights: str | None = None

    # Final assessment
    is_compliant: bool = False
    compliance_score: float = Field(default=0.0, ge=0.0, le=100.0)
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)

    # Recommendations
    fix_suggestions: list[str] = Field(default_factory=list)
    sdi_approval_probability: float | None = None

    # Human review (if critical issues found)
    review: HumanReview | None = None
    require_review_on_warnings: bool = True


# ============================================================================
# Cash Flow Analysis Workflow State
# ============================================================================


class CashFlowAnalysisState(BaseWorkflowState):
    """State for Cash Flow Analysis workflow.

    Workflow: Load Unpaid → Predict Each → Aggregate → Generate Insights

    Can run for:
    - All clients (comprehensive forecast)
    - Single client (client-specific forecast)
    - Filtered invoices (custom query)
    """

    # Input filters
    client_id: int | None = None
    invoice_ids: list[int] | None = None
    forecast_months: int = 3

    # ML model results
    predictions: list[dict[str, Any]] = Field(default_factory=list)
    total_invoices_analyzed: int = 0
    failed_predictions: int = 0

    # Aggregated forecast
    monthly_forecast: list[dict[str, Any]] = Field(default_factory=list)
    total_expected_revenue: float = 0.0

    # Risk analysis
    high_risk_invoices: list[int] = Field(default_factory=list)
    overdue_predictions: list[dict[str, Any]] = Field(default_factory=list)

    # AI insights
    insights: str | None = None
    recommendations: list[str] = Field(default_factory=list)

    # Model performance
    average_confidence: float = 0.0
    model_agreement_avg: float = 0.0


# ============================================================================
# Batch Processing Workflow State
# ============================================================================


class BatchProcessingState(BaseWorkflowState):
    """State for Batch Processing workflow.

    Workflow: Load Batch → Parallel Process → Aggregate Results → Report

    Supports:
    - Parallel agent execution (rate-limited)
    - Progress tracking
    - Partial failures handling
    - Resume on interruption
    """

    # Batch configuration
    operation_type: str  # "validate", "generate_xml", "compliance_check", etc.
    item_ids: list[int]  # Invoice IDs or Client IDs
    batch_size: int = 10
    max_parallel: int = 5

    # Progress tracking
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0

    # Results
    results: list[dict[str, Any]] = Field(default_factory=list)
    errors_detail: list[dict[str, Any]] = Field(default_factory=list)

    # Performance
    started_at: datetime | None = None
    items_per_second: float = 0.0
    estimated_completion: datetime | None = None

    # Resume support
    checkpoint_ids: list[int] = Field(default_factory=list)  # Completed IDs
    can_resume: bool = True

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.processed_items == 0:
            return 0.0
        return (self.successful_items / self.processed_items) * 100


# ============================================================================
# Helper Functions
# ============================================================================


def create_invoice_workflow(
    user_input: str,
    client_id: int,
    *,
    require_approvals: bool = False,
    imponibile: Decimal | None = None,
    vat_rate: Decimal | float | None = None,
    hours: float | None = None,
    hourly_rate: Decimal | float | None = None,
    payment_terms_days: int = 30,
    invoice_date: date | None = None,
    payment_due_date: date | None = None,
) -> InvoiceCreationState:
    """Create a new invoice creation workflow state.

    Args:
        user_input: User's invoice description input
        client_id: Client ID for the invoice
        require_approvals: Enable human approval checkpoints

    Returns:
        InvoiceCreationState ready for workflow execution
    """
    imponibile_value = Decimal("0.00")
    if imponibile is not None:
        imponibile_value = Decimal(str(imponibile))

    vat_value = Decimal("22.00")
    if vat_rate is not None:
        vat_value = Decimal(str(vat_rate))

    hourly_rate_value: Decimal | None = None
    if hourly_rate is not None:
        hourly_rate_value = Decimal(str(hourly_rate))

    return InvoiceCreationState(
        user_input=user_input,
        client_id=client_id,
        invoice_date=invoice_date,
        payment_due_date=payment_due_date,
        imponibile_target=imponibile_value,
        vat_rate=vat_value,
        hours=hours,
        hourly_rate=hourly_rate_value,
        payment_terms_days=payment_terms_days,
        require_description_approval=require_approvals,
        require_tax_approval=require_approvals,
        require_compliance_approval=True,  # Always for errors
    )


def create_compliance_workflow(
    invoice_id: int,
    level: str = "standard",
) -> ComplianceCheckState:
    """Create a new compliance check workflow state.

    Args:
        invoice_id: Invoice ID to check
        level: Check level (basic/standard/advanced)

    Returns:
        ComplianceCheckState ready for workflow execution
    """
    return ComplianceCheckState(
        invoice_id=invoice_id,
        check_level=level,
    )


def create_cash_flow_workflow(
    months: int = 3,
    client_id: int | None = None,
) -> CashFlowAnalysisState:
    """Create a new cash flow analysis workflow state.

    Args:
        months: Number of months to forecast
        client_id: Optional client filter

    Returns:
        CashFlowAnalysisState ready for workflow execution
    """
    return CashFlowAnalysisState(
        forecast_months=months,
        client_id=client_id,
    )


def create_batch_workflow(
    operation_type: str,
    item_ids: list[int],
    batch_size: int = 10,
) -> BatchProcessingState:
    """Create a new batch processing workflow state.

    Args:
        operation_type: Type of operation to perform
        item_ids: List of item IDs to process
        batch_size: Number of items per batch

    Returns:
        BatchProcessingState ready for workflow execution
    """
    return BatchProcessingState(
        operation_type=operation_type,
        item_ids=item_ids,
        total_items=len(item_ids),
        batch_size=batch_size,
    )
