"""Tests for orchestration state models."""

import importlib.util
import sys
from decimal import Decimal

# Mock sklearn/scipy to avoid import issues
sys.modules["sklearn"] = type(sys)("sklearn")
sys.modules["sklearn.base"] = type(sys)("sklearn.base")
sys.modules["scipy"] = type(sys)("scipy")
sys.modules["scipy.stats"] = type(sys)("scipy.stats")
sys.modules["plotly"] = type(sys)("plotly")

# Import states module directly to avoid __init__.py workflow imports
spec = importlib.util.spec_from_file_location("states", "openfatture/ai/orchestration/states.py")
if spec is None or spec.loader is None:
    raise ImportError("Could not load states module")
states = importlib.util.module_from_spec(spec)
sys.modules["openfatture.ai.orchestration.states"] = states
spec.loader.exec_module(states)

# Import the classes
AgentResult = states.AgentResult
AgentType = states.AgentType
ApprovalDecision = states.ApprovalDecision
BaseWorkflowState = states.BaseWorkflowState
ComplianceCheckState = states.ComplianceCheckState
HumanReview = states.HumanReview
InvoiceCreationState = states.InvoiceCreationState
SharedContext = states.SharedContext
WorkflowStatus = states.WorkflowStatus


class TestAgentResult:
    """Test AgentResult model."""

    def test_agent_result_creation(self):
        """Test basic AgentResult creation."""
        result = AgentResult(
            agent_type=AgentType.DESCRIPTION,
            success=True,
            content="Test content",
            confidence=0.85,
            metadata={"key": "value"},
        )
        assert result.agent_type == "description"  # Pydantic uses enum values
        assert result.success is True
        assert result.content == "Test content"
        assert result.confidence == 0.85
        assert result.metadata == {"key": "value"}
        assert result.error is None

    def test_agent_result_with_error(self):
        """Test AgentResult with error."""
        result = AgentResult(
            agent_type=AgentType.TAX_ADVISOR,
            success=False,
            content="",
            confidence=0.0,
            error="Test error",
        )
        assert result.success is False
        assert result.error == "Test error"


class TestHumanReview:
    """Test HumanReview model."""

    def test_human_review_creation(self):
        """Test basic HumanReview creation."""
        review = HumanReview(
            decision=ApprovalDecision.APPROVE,
            feedback="Looks good",
            reviewer="test@example.com",
        )
        assert review.decision == "approve"  # Pydantic uses enum values
        assert review.feedback == "Looks good"
        assert review.reviewer == "test@example.com"


class TestSharedContext:
    """Test SharedContext model."""

    def test_shared_context_creation(self):
        """Test basic SharedContext creation."""
        context = SharedContext(
            total_invoices_ytd=10,
            total_revenue_ytd=50000.0,
            unpaid_invoices_count=2,
            unpaid_invoices_value=10000.0,
            recent_clients=[{"id": 1, "name": "Test Client"}],
            default_tax_regime="RF01",
        )
        assert context.total_invoices_ytd == 10
        assert context.total_revenue_ytd == 50000.0
        assert context.unpaid_invoices_count == 2
        assert context.unpaid_invoices_value == 10000.0
        assert context.recent_clients == [{"id": 1, "name": "Test Client"}]
        assert context.default_tax_regime == "RF01"


class TestBaseWorkflowState:
    """Test BaseWorkflowState model."""

    def test_base_workflow_state_creation(self):
        """Test basic BaseWorkflowState creation."""
        state = BaseWorkflowState(
            correlation_id="test-123",
            status=WorkflowStatus.IN_PROGRESS,
        )
        assert state.workflow_id is not None
        assert state.correlation_id == "test-123"
        assert state.status == "in_progress"  # Pydantic uses enum values
        assert state.errors == []
        assert state.warnings == []

    def test_add_error(self):
        """Test adding errors to workflow state."""
        state = BaseWorkflowState()
        state.add_error("Test error")
        assert state.errors == ["Test error"]
        assert state.status == WorkflowStatus.FAILED.value

    def test_add_warning(self):
        """Test adding warnings to workflow state."""
        state = BaseWorkflowState()
        state.add_warning("Test warning")
        assert state.warnings == ["Test warning"]

    def test_mark_completed(self):
        """Test marking workflow as completed."""
        state = BaseWorkflowState()
        state.mark_completed()
        assert state.status == WorkflowStatus.COMPLETED.value
        assert state.completed_at is not None


class TestInvoiceCreationState:
    """Test InvoiceCreationState model."""

    def test_invoice_creation_state_creation(self):
        """Test basic InvoiceCreationState creation."""
        state = InvoiceCreationState(
            user_input="Test invoice",
            client_id=123,
            imponibile_target=Decimal("1000.00"),
            vat_rate=Decimal("22.00"),
        )
        assert state.user_input == "Test invoice"
        assert state.client_id == 123
        assert state.imponibile_target == Decimal("1000.00")
        assert state.vat_rate == Decimal("22.00")
        assert state.line_items == []
        assert state.tax_details == {}

    def test_description_approval_properties(self):
        """Test description approval properties."""
        # No approval required
        state = InvoiceCreationState(
            user_input="Test",
            client_id=123,
            require_description_approval=False,
        )
        assert state.is_description_approved is True

        # Approval required but no review
        state.require_description_approval = True
        assert state.is_description_approved is False

        # Approval required with approved review
        state.description_review = HumanReview(decision=ApprovalDecision.APPROVE)
        assert state.is_description_approved is True

        # Approval required with rejected review
        state.description_review = HumanReview(decision=ApprovalDecision.REJECT)
        assert state.is_description_approved is False

    def test_tax_approval_properties(self):
        """Test tax approval properties."""
        state = InvoiceCreationState(
            user_input="Test",
            client_id=123,
            require_tax_approval=True,
        )
        assert state.is_tax_approved is False

        state.tax_review = HumanReview(decision=ApprovalDecision.APPROVE)
        assert state.is_tax_approved is True

    def test_compliance_property(self):
        """Test compliance property."""
        state = InvoiceCreationState(user_input="Test", client_id=123)

        # No compliance result
        assert state.is_compliant is False

        # Failed compliance
        state.compliance_result = AgentResult(
            agent_type=AgentType.COMPLIANCE,
            success=False,
            content="Failed",
            confidence=0.5,
        )
        assert state.is_compliant is False

        # Successful compliance with low confidence
        state.compliance_result = AgentResult(
            agent_type=AgentType.COMPLIANCE,
            success=True,
            content="Passed",
            confidence=0.7,
        )
        assert state.is_compliant is False

        # Successful compliance with high confidence
        state.compliance_result.confidence = 0.9
        assert state.is_compliant is True


class TestComplianceCheckState:
    """Test ComplianceCheckState model."""

    def test_compliance_check_state_creation(self):
        """Test basic ComplianceCheckState creation."""
        state = ComplianceCheckState(
            invoice_id=456,
            check_level="advanced",
        )
        assert state.invoice_id == 456
        assert state.check_level == "advanced"
        assert state.rules_passed is False
        assert state.rules_issues == []
        assert state.sdi_patterns_checked is False
        assert state.sdi_warnings == []
        assert state.ai_analysis_performed is False
        assert state.is_compliant is False
        assert state.compliance_score == 0.0
        assert state.risk_score == 0.0
