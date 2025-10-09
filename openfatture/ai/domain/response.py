"""Response models for AI agents."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ResponseStatus(str, Enum):
    """Status of agent response."""

    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"  # Partial success
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


class ToolCall(BaseModel):
    """Represents a tool/function call made by the agent."""

    id: str
    name: str
    arguments: dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None


class UsageMetrics(BaseModel):
    """Token usage and cost metrics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0

    @property
    def cost_display(self) -> str:
        """Format cost for display."""
        return f"${self.estimated_cost_usd:.4f}"


class AgentResponse(BaseModel):
    """
    Structured response from an AI agent.

    Contains the agent's output, metadata, usage metrics,
    and any errors that occurred.
    """

    # Core response
    content: str
    status: ResponseStatus = ResponseStatus.SUCCESS

    # Tool calls (if any)
    tool_calls: list[ToolCall] = Field(default_factory=list)

    # Metadata
    agent_name: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None

    # Usage metrics
    usage: UsageMetrics = Field(default_factory=UsageMetrics)

    # Timing
    timestamp: datetime = Field(default_factory=datetime.now)
    latency_ms: Optional[float] = None

    # Error handling
    error: Optional[str] = None
    error_details: dict[str, Any] = Field(default_factory=dict)

    # Confidence/quality
    confidence: Optional[float] = None  # 0.0 to 1.0

    # Additional data
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if response was successful."""
        return self.status == ResponseStatus.SUCCESS

    @property
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return len(self.tool_calls) > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "status": self.status.value,
            "success": self.success,
            "agent_name": self.agent_name,
            "model": self.model,
            "provider": self.provider,
            "tokens_used": self.usage.total_tokens,
            "cost_usd": self.usage.estimated_cost_usd,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "confidence": self.confidence,
            "tool_calls_count": len(self.tool_calls),
        }

    def __str__(self) -> str:
        """String representation for logging."""
        status_emoji = "✓" if self.success else "✗"
        preview = self.content[:100] + "..." if len(self.content) > 100 else self.content
        return f"{status_emoji} [{self.agent_name}] {preview}"


class StreamChunk(BaseModel):
    """
    A chunk of streamed response.

    Used when streaming responses from LLMs token by token.
    """

    content: str
    is_final: bool = False
    tool_call: Optional[ToolCall] = None
    finish_reason: Optional[str] = None

    def __str__(self) -> str:
        """String representation."""
        return self.content
