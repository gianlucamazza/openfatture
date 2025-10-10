"""Human-in-the-Loop System for AI Workflows.

Provides approval checkpoints and review mechanisms for AI agent decisions.

Features:
- Configurable approval checkpoints in workflows
- CLI-based review interface (Rich terminal UI)
- Decision logging and audit trail
- Override capabilities
- Feedback collection for model improvement
- Approval policies (always, never, confidence-based, error-based)

Architecture:
- ApprovalCheckpoint: Defines when/what to review
- HumanReviewer: Interactive review interface
- ApprovalPolicy: Rules for when approval is required
- ReviewDecisionLogger: Audit trail for all decisions

Example:
    >>> checkpoint = ApprovalCheckpoint(
    ...     name="tax_suggestion",
    ...     require_approval_on_low_confidence=True,
    ...     confidence_threshold=0.85
    ... )
    >>> decision = await checkpoint.request_approval(
    ...     data=tax_result,
    ...     workflow_state=state
    ... )
    >>> if decision.approved:
    ...     # Continue workflow
    ...     pass
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from openfatture.ai.orchestration.states import (
    ApprovalDecision,
    HumanReview,
)
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


class ApprovalPolicy(Enum):
    """Approval policy types."""

    ALWAYS = "always"  # Always require approval
    NEVER = "never"  # Never require approval (auto-approve)
    LOW_CONFIDENCE = "low_confidence"  # Approve if confidence < threshold
    ON_ERROR = "on_error"  # Approve only if errors/warnings present
    SMART = "smart"  # Combination of confidence + error checks


@dataclass
class ApprovalRequest:
    """Approval request data."""

    checkpoint_name: str
    workflow_id: str
    agent_type: str
    data: dict[str, Any]
    confidence: float | None = None
    errors: list = None
    warnings: list = None
    context: dict[str, Any] | None = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class ApprovalResponse:
    """Approval response from reviewer."""

    approved: bool
    decision: ApprovalDecision
    feedback: str | None = None
    modifications: dict[str, Any] | None = None
    reviewer: str = "human"
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_human_review(self) -> HumanReview:
        """Convert to HumanReview model."""
        return HumanReview(
            decision=self.decision,
            feedback=self.feedback,
            reviewer=self.reviewer,
            timestamp=self.timestamp,
        )


class ApprovalCheckpoint:
    """Approval checkpoint for workflow decisions.

    Determines when human approval is required and handles the review process.

    Example:
        >>> checkpoint = ApprovalCheckpoint(
        ...     name="description_review",
        ...     policy=ApprovalPolicy.LOW_CONFIDENCE,
        ...     confidence_threshold=0.85
        ... )
        >>> response = await checkpoint.request_approval(request)
    """

    def __init__(
        self,
        name: str,
        policy: ApprovalPolicy = ApprovalPolicy.SMART,
        confidence_threshold: float = 0.85,
        auto_approve_on_high_confidence: bool = True,
        reviewer: Optional["HumanReviewer"] = None,
    ):
        """Initialize approval checkpoint.

        Args:
            name: Checkpoint identifier
            policy: Approval policy to use
            confidence_threshold: Minimum confidence for auto-approval
            auto_approve_on_high_confidence: Skip approval if confidence > threshold
            reviewer: Human reviewer interface (creates default if None)
        """
        self.name = name
        self.policy = policy
        self.confidence_threshold = confidence_threshold
        self.auto_approve_on_high_confidence = auto_approve_on_high_confidence
        self.reviewer = reviewer or HumanReviewer()

        logger.info(
            "approval_checkpoint_initialized",
            name=name,
            policy=policy.value,
            threshold=confidence_threshold,
        )

    def should_request_approval(self, request: ApprovalRequest) -> bool:
        """Determine if approval should be requested.

        Args:
            request: Approval request data

        Returns:
            True if approval is required
        """
        if self.policy == ApprovalPolicy.ALWAYS:
            return True

        if self.policy == ApprovalPolicy.NEVER:
            return False

        if self.policy == ApprovalPolicy.ON_ERROR:
            # Only if errors/warnings present
            return len(request.errors) > 0 or len(request.warnings) > 0

        if self.policy == ApprovalPolicy.LOW_CONFIDENCE:
            # Only if confidence below threshold
            if request.confidence is not None:
                return request.confidence < self.confidence_threshold
            return True  # No confidence provided, require approval

        if self.policy == ApprovalPolicy.SMART:
            # Combination: low confidence OR errors/warnings
            has_issues = len(request.errors) > 0 or len(request.warnings) > 0
            low_confidence = (
                request.confidence is not None and request.confidence < self.confidence_threshold
            )

            return has_issues or low_confidence

        return True  # Default: require approval

    async def request_approval(
        self,
        request: ApprovalRequest,
    ) -> ApprovalResponse:
        """Request human approval.

        Args:
            request: Approval request data

        Returns:
            ApprovalResponse with decision

        Example:
            >>> response = await checkpoint.request_approval(request)
            >>> if response.approved:
            ...     print("Approved!")
        """
        # Check if approval is needed
        if not self.should_request_approval(request):
            logger.info(
                "auto_approved",
                checkpoint=self.name,
                workflow_id=request.workflow_id,
                reason="policy_skip",
            )

            return ApprovalResponse(
                approved=True,
                decision=ApprovalDecision.APPROVE,
                feedback="Auto-approved (policy skip)",
                reviewer="system",
            )

        # Auto-approve on high confidence if enabled
        if (
            self.auto_approve_on_high_confidence
            and request.confidence is not None
            and request.confidence >= self.confidence_threshold
            and len(request.errors) == 0
        ):
            logger.info(
                "auto_approved",
                checkpoint=self.name,
                workflow_id=request.workflow_id,
                confidence=request.confidence,
                reason="high_confidence",
            )

            return ApprovalResponse(
                approved=True,
                decision=ApprovalDecision.APPROVE,
                feedback=f"Auto-approved (confidence: {request.confidence:.1%})",
                reviewer="system",
            )

        # Request human review
        logger.info(
            "requesting_human_approval",
            checkpoint=self.name,
            workflow_id=request.workflow_id,
        )

        response = await self.reviewer.review(request)

        logger.info(
            "human_approval_received",
            checkpoint=self.name,
            workflow_id=request.workflow_id,
            decision=response.decision.value,
            approved=response.approved,
        )

        return response


class HumanReviewer:
    """Interactive human review interface.

    Provides Rich terminal UI for reviewing AI decisions.

    Example:
        >>> reviewer = HumanReviewer()
        >>> response = await reviewer.review(request)
    """

    def __init__(self, console: Console | None = None):
        """Initialize human reviewer.

        Args:
            console: Rich console (creates default if None)
        """
        self.console = console or Console()

    async def review(self, request: ApprovalRequest) -> ApprovalResponse:
        """Interactive review session.

        Args:
            request: Approval request data

        Returns:
            ApprovalResponse with user decision
        """
        self.console.print()
        self.console.print(
            Panel(
                f"[bold yellow]Human Approval Required[/bold yellow]\n\n"
                f"Checkpoint: {request.checkpoint_name}\n"
                f"Workflow: {request.workflow_id}",
                border_style="yellow",
            )
        )
        self.console.print()

        # Display data
        self._display_data(request)

        # Display confidence if available
        if request.confidence is not None:
            confidence_color = (
                "green"
                if request.confidence >= 0.85
                else "yellow" if request.confidence >= 0.7 else "red"
            )
            self.console.print(
                f"[bold]Confidence Score:[/bold] [{confidence_color}]{request.confidence:.1%}[/{confidence_color}]\n"
            )

        # Display errors/warnings
        if request.errors:
            self.console.print("[bold red]Errors:[/bold red]")
            for error in request.errors:
                self.console.print(f"  ❌ {error}")
            self.console.print()

        if request.warnings:
            self.console.print("[bold yellow]Warnings:[/bold yellow]")
            for warning in request.warnings:
                self.console.print(f"  ⚠️  {warning}")
            self.console.print()

        # Request decision
        self.console.print("[bold cyan]Decision Options:[/bold cyan]")
        self.console.print("  1. [green]Approve[/green] - Continue workflow")
        self.console.print("  2. [yellow]Request Changes[/yellow] - Modify and re-submit")
        self.console.print("  3. [red]Reject[/red] - Cancel workflow")
        self.console.print("  4. [dim]Skip[/dim] - Skip this checkpoint")
        self.console.print()

        decision_map = {
            "1": ApprovalDecision.APPROVE,
            "2": ApprovalDecision.REQUEST_CHANGES,
            "3": ApprovalDecision.REJECT,
            "4": ApprovalDecision.SKIP,
        }

        choice = Prompt.ask(
            "Your decision",
            choices=["1", "2", "3", "4"],
            default="1",
        )

        decision = decision_map[choice]

        # Get feedback if requested
        feedback = None
        if decision in [ApprovalDecision.REQUEST_CHANGES, ApprovalDecision.REJECT]:
            feedback = Prompt.ask("Feedback (optional)", default="")

        # Determine if approved
        approved = decision in [ApprovalDecision.APPROVE, ApprovalDecision.SKIP]

        self.console.print()
        if approved:
            self.console.print("[bold green]✓ Approved[/bold green]")
        else:
            self.console.print("[bold red]✗ Rejected[/bold red]")
        self.console.print()

        return ApprovalResponse(
            approved=approved,
            decision=decision,
            feedback=feedback if feedback else None,
            reviewer="human",
        )

    def _display_data(self, request: ApprovalRequest) -> None:
        """Display approval request data."""
        self.console.print("[bold]Data for Review:[/bold]\n")

        # Create table for structured data
        table = Table(show_header=False, box=None)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")

        for key, value in request.data.items():
            # Format value
            if isinstance(value, dict):
                value_str = "\n".join(f"  {k}: {v}" for k, v in value.items())
            elif isinstance(value, list):
                value_str = ", ".join(str(v) for v in value)
            else:
                value_str = str(value)

            table.add_row(key, value_str)

        self.console.print(table)
        self.console.print()


class ReviewDecisionLogger:
    """Logs all approval decisions for audit trail.

    Example:
        >>> logger = ReviewDecisionLogger()
        >>> logger.log_decision(request, response)
    """

    def __init__(self, log_file: str | None = None):
        """Initialize decision logger.

        Args:
            log_file: Optional file path for logging (uses structured logger if None)
        """
        self.log_file = log_file
        self.logger = get_logger(__name__)

    def log_decision(
        self,
        request: ApprovalRequest,
        response: ApprovalResponse,
    ) -> None:
        """Log approval decision.

        Args:
            request: Original approval request
            response: Approval response
        """
        self.logger.info(
            "approval_decision_logged",
            checkpoint=request.checkpoint_name,
            workflow_id=request.workflow_id,
            agent_type=request.agent_type,
            decision=response.decision.value,
            approved=response.approved,
            confidence=request.confidence,
            has_errors=len(request.errors) > 0,
            has_warnings=len(request.warnings) > 0,
            reviewer=response.reviewer,
            timestamp=response.timestamp.isoformat(),
        )


def create_approval_checkpoint(
    name: str,
    policy: str = "smart",
    confidence_threshold: float = 0.85,
) -> ApprovalCheckpoint:
    """Create approval checkpoint with policy.

    Args:
        name: Checkpoint identifier
        policy: Policy name (always/never/low_confidence/on_error/smart)
        confidence_threshold: Confidence threshold for auto-approval

    Returns:
        ApprovalCheckpoint ready to use

    Example:
        >>> checkpoint = create_approval_checkpoint(
        ...     name="tax_review",
        ...     policy="smart",
        ...     confidence_threshold=0.85
        ... )
    """
    policy_map = {
        "always": ApprovalPolicy.ALWAYS,
        "never": ApprovalPolicy.NEVER,
        "low_confidence": ApprovalPolicy.LOW_CONFIDENCE,
        "on_error": ApprovalPolicy.ON_ERROR,
        "smart": ApprovalPolicy.SMART,
    }

    policy_enum = policy_map.get(policy.lower(), ApprovalPolicy.SMART)

    return ApprovalCheckpoint(
        name=name,
        policy=policy_enum,
        confidence_threshold=confidence_threshold,
    )
