"""Multi-Agent Orchestration Layer using LangGraph.

Enterprise-grade orchestration for AI agents with:
- State management (Pydantic models)
- Workflow definitions (LangGraph StateGraph)
- Resilience patterns (Circuit Breaker, Retry, Fallback)
- Human-in-the-loop (Approval checkpoints)
- Comprehensive logging and monitoring

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                       │
├─────────────────────────────────────────────────────────────┤
│  States          │ Workflows        │ Resilience │ Human    │
│  ─────────────── │ ──────────────── │ ────────── │ ───────  │
│  • Invoice       │ • Invoice Create │ • Circuit  │ • Review │
│  • Compliance    │ • Compliance     │ • Retry    │ • Approve│
│  • CashFlow      │ • CashFlow       │ • Fallback │ • Audit  │
│  • Batch         │                  │ • Timeout  │          │
└─────────────────────────────────────────────────────────────┘

Example Usage:
    >>> from openfatture.ai.orchestration import (
    ...     InvoiceCreationWorkflow,
    ...     create_resilient_provider,
    ...     create_approval_checkpoint,
    ... )
    >>>
    >>> # Create workflow
    >>> workflow = InvoiceCreationWorkflow()
    >>>
    >>> # Execute with resilience
    >>> result = await workflow.execute(
    ...     user_input="consulenza Python 5h",
    ...     client_id=123
    ... )
    >>>
    >>> print(f"Invoice created: {result.invoice_id}")

Key Features:
- **State Management**: Type-safe workflow states with Pydantic
- **Conditional Routing**: LangGraph edges based on confidence/errors
- **Resilience**: Circuit breaker, exponential backoff, fallback chains
- **Human Oversight**: Configurable approval checkpoints
- **Observability**: Structured logging, metrics, audit trails
"""

# State Management
from openfatture.ai.orchestration.states import (
    # Enums
    WorkflowStatus,
    ApprovalDecision,
    AgentType,
    # Base Models
    AgentResult,
    HumanReview,
    SharedContext,
    BaseWorkflowState,
    # Workflow States
    InvoiceCreationState,
    ComplianceCheckState,
    CashFlowAnalysisState,
    BatchProcessingState,
    # Factory Functions
    create_invoice_workflow as create_invoice_state,
    create_compliance_workflow as create_compliance_state,
    create_cash_flow_workflow as create_cash_flow_state,
    create_batch_workflow as create_batch_state,
)

# Workflows
from openfatture.ai.orchestration.workflows import (
    InvoiceCreationWorkflow,
    create_invoice_workflow,
    ComplianceCheckWorkflow,
    create_compliance_workflow,
    CashFlowAnalysisWorkflow,
    create_cash_flow_workflow,
)

# Resilience
from openfatture.ai.orchestration.resilience import (
    # Circuit Breaker
    CircuitState,
    CircuitBreaker,
    CircuitBreakerConfig,
    # Retry
    RetryConfig,
    FailureType,
    # Policy & Provider
    ResiliencePolicy,
    ResilientProvider,
    create_resilient_provider,
)

# Human-in-the-Loop
from openfatture.ai.orchestration.human_loop import (
    ApprovalPolicy,
    ApprovalCheckpoint,
    ApprovalRequest,
    ApprovalResponse,
    HumanReviewer,
    ReviewDecisionLogger,
    create_approval_checkpoint,
)

__all__ = [
    # ========================================================================
    # State Management
    # ========================================================================
    # Enums
    "WorkflowStatus",
    "ApprovalDecision",
    "AgentType",
    # Base Models
    "AgentResult",
    "HumanReview",
    "SharedContext",
    "BaseWorkflowState",
    # Workflow States
    "InvoiceCreationState",
    "ComplianceCheckState",
    "CashFlowAnalysisState",
    "BatchProcessingState",
    # State Factory Functions
    "create_invoice_state",
    "create_compliance_state",
    "create_cash_flow_state",
    "create_batch_state",
    # ========================================================================
    # Workflows
    # ========================================================================
    "InvoiceCreationWorkflow",
    "create_invoice_workflow",
    "ComplianceCheckWorkflow",
    "create_compliance_workflow",
    "CashFlowAnalysisWorkflow",
    "create_cash_flow_workflow",
    # ========================================================================
    # Resilience
    # ========================================================================
    # Circuit Breaker
    "CircuitState",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    # Retry
    "RetryConfig",
    "FailureType",
    # Policy & Provider
    "ResiliencePolicy",
    "ResilientProvider",
    "create_resilient_provider",
    # ========================================================================
    # Human-in-the-Loop
    # ========================================================================
    "ApprovalPolicy",
    "ApprovalCheckpoint",
    "ApprovalRequest",
    "ApprovalResponse",
    "HumanReviewer",
    "ReviewDecisionLogger",
    "create_approval_checkpoint",
]

# Version
__version__ = "0.1.0"
