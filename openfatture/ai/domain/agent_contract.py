"""Agent contract: configuration and the protocol every agent implements."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from openfatture.ai.domain.context import AgentContext
from openfatture.ai.domain.response import AgentResponse


class AgentConfig(BaseModel):
    """
    Configuration for an agent.

    Defines the agent's behavior, capabilities, and limits.
    """

    # Identity
    name: str = Field(..., description="Agent name (unique identifier)")
    description: str = Field(..., description="Agent purpose and capabilities")
    version: str = Field(default="1.0.0", description="Agent version")

    # LLM Settings
    model: str | None = Field(default=None, description="Model to use (overrides provider default)")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature (0.0-2.0)")
    max_tokens: int = Field(default=2000, ge=1, description="Max tokens to generate")

    # Prompts
    system_prompt: str | None = Field(default=None, description="System prompt template")
    prompt_template: str | None = Field(default=None, description="Prompt template name")

    # Features
    tools_enabled: bool = Field(default=False, description="Enable tool/function calling")
    output_schema: dict[str, Any] | None = Field(
        default=None,
        description="JSON schema for native structured output (forced when provider supports tools)",
    )
    memory_enabled: bool = Field(default=False, description="Enable conversation memory")
    rag_enabled: bool = Field(default=False, description="Enable RAG (vector search)")
    streaming_enabled: bool = Field(default=False, description="Enable streaming responses")

    # Limits
    max_retries: int = Field(default=3, ge=0, description="Max retries on failure")
    timeout_seconds: int = Field(default=30, ge=1, description="Request timeout")

    # Cost controls
    max_cost_per_request: float = Field(
        default=0.5, ge=0.0, description="Max cost per request (USD)"
    )

    # Metadata
    tags: list[str] = Field(default_factory=list, description="Agent tags/categories")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentProtocol[ContextT: AgentContext](ABC):
    """
    Protocol that all agents must implement.

    Defines the contract for agent execution with context
    management and structured responses.

    Generic over ContextT to allow specialized contexts (ChatContext, TaxContext, etc.)
    while maintaining type safety.
    """

    @property
    @abstractmethod
    def config(self) -> AgentConfig:
        """Get agent configuration."""
        pass

    @abstractmethod
    async def execute(
        self,
        context: ContextT,
        **kwargs: Any,
    ) -> AgentResponse:
        """
        Execute the agent with given context.

        Args:
            context: Agent execution context (specialized per agent type)
            **kwargs: Additional arguments

        Returns:
            AgentResponse with structured output

        Raises:
            ProviderError: If execution fails
        """
        pass

    @abstractmethod
    async def validate_input(self, context: ContextT) -> tuple[bool, str | None]:
        """
        Validate input before execution.

        Args:
            context: Agent execution context (specialized per agent type)

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources after execution."""
        pass
