"""Base agent implementation and protocol."""

import time
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional

from pydantic import BaseModel, Field

from openfatture.ai.domain.context import AgentContext
from openfatture.ai.domain.message import Message, Role
from openfatture.ai.domain.response import AgentResponse, ResponseStatus
from openfatture.ai.providers.base import BaseLLMProvider, ProviderError
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


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
    model: Optional[str] = Field(default=None, description="Model to use (overrides provider default)")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature (0.0-2.0)")
    max_tokens: int = Field(default=2000, ge=1, description="Max tokens to generate")

    # Prompts
    system_prompt: Optional[str] = Field(default=None, description="System prompt template")
    prompt_template: Optional[str] = Field(default=None, description="Prompt template name")

    # Features
    tools_enabled: bool = Field(default=False, description="Enable tool/function calling")
    memory_enabled: bool = Field(default=False, description="Enable conversation memory")
    rag_enabled: bool = Field(default=False, description="Enable RAG (vector search)")
    streaming_enabled: bool = Field(default=False, description="Enable streaming responses")

    # Limits
    max_retries: int = Field(default=3, ge=0, description="Max retries on failure")
    timeout_seconds: int = Field(default=30, ge=1, description="Request timeout")

    # Cost controls
    max_cost_per_request: float = Field(default=0.5, ge=0.0, description="Max cost per request (USD)")

    # Metadata
    tags: list[str] = Field(default_factory=list, description="Agent tags/categories")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentProtocol(ABC):
    """
    Protocol that all agents must implement.

    Defines the contract for agent execution with context
    management and structured responses.
    """

    @property
    @abstractmethod
    def config(self) -> AgentConfig:
        """Get agent configuration."""
        pass

    @abstractmethod
    async def execute(
        self,
        context: AgentContext,
        **kwargs: Any,
    ) -> AgentResponse:
        """
        Execute the agent with given context.

        Args:
            context: Agent execution context
            **kwargs: Additional arguments

        Returns:
            AgentResponse with structured output

        Raises:
            ProviderError: If execution fails
        """
        pass

    @abstractmethod
    async def validate_input(self, context: AgentContext) -> tuple[bool, Optional[str]]:
        """
        Validate input before execution.

        Args:
            context: Agent execution context

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources after execution."""
        pass


class BaseAgent(AgentProtocol):
    """
    Base implementation of AgentProtocol.

    Provides common functionality for all agents:
    - Provider management
    - Structured logging
    - Metrics collection
    - Error handling
    - Cost tracking
    - Retry logic

    Concrete agents should:
    1. Inherit from BaseAgent
    2. Override _build_prompt() to construct agent-specific prompts
    3. Override _parse_response() to extract structured data
    4. Optionally override validate_input() for custom validation
    """

    def __init__(
        self,
        config: AgentConfig,
        provider: BaseLLMProvider,
        logger_instance: Optional[Any] = None,
    ) -> None:
        """
        Initialize base agent.

        Args:
            config: Agent configuration
            provider: LLM provider instance
            logger_instance: Optional logger (uses module logger if None)
        """
        self._config = config
        self.provider = provider
        self.logger = logger_instance or logger

        # Metrics
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.total_errors = 0

    @property
    def config(self) -> AgentConfig:
        """Get agent configuration."""
        return self._config

    async def execute(
        self,
        context: AgentContext,
        **kwargs: Any,
    ) -> AgentResponse:
        """
        Execute the agent (template method).

        This implements the common execution flow:
        1. Validate input
        2. Build prompt
        3. Call LLM
        4. Parse response
        5. Track metrics
        6. Handle errors

        Args:
            context: Agent execution context
            **kwargs: Additional arguments

        Returns:
            AgentResponse with results
        """
        start_time = time.time()

        self.logger.info(
            "agent_execution_started",
            agent=self.config.name,
            correlation_id=context.correlation_id,
            user_input_preview=context.user_input[:100],
        )

        try:
            # 1. Validate input
            is_valid, error_msg = await self.validate_input(context)
            if not is_valid:
                self.logger.warning(
                    "agent_validation_failed",
                    agent=self.config.name,
                    error=error_msg,
                )
                return AgentResponse(
                    content="",
                    status=ResponseStatus.ERROR,
                    agent_name=self.config.name,
                    error=error_msg,
                )

            # 2. Build prompt
            messages = await self._build_prompt(context)

            # 3. Call LLM with retry logic
            response = await self._call_llm_with_retry(messages, context)

            # 4. Parse response (allow subclasses to process)
            response = await self._parse_response(response, context)

            # 5. Update metrics
            self.total_requests += 1
            self.total_tokens += response.usage.total_tokens
            self.total_cost += response.usage.estimated_cost_usd

            # Set agent name
            response.agent_name = self.config.name

            # Calculate total latency
            response.latency_ms = (time.time() - start_time) * 1000

            self.logger.info(
                "agent_execution_completed",
                agent=self.config.name,
                correlation_id=context.correlation_id,
                status=response.status.value,
                tokens=response.usage.total_tokens,
                cost_usd=response.usage.estimated_cost_usd,
                latency_ms=response.latency_ms,
            )

            return response

        except Exception as e:
            self.total_errors += 1

            self.logger.error(
                "agent_execution_failed",
                agent=self.config.name,
                correlation_id=context.correlation_id,
                error=str(e),
                error_type=type(e).__name__,
            )

            return AgentResponse(
                content="",
                status=ResponseStatus.ERROR,
                agent_name=self.config.name,
                error=str(e),
                error_details={"error_type": type(e).__name__},
            )

    async def execute_stream(
        self,
        context: AgentContext,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Execute the agent with streaming response.

        This method yields response chunks as they arrive from the LLM,
        enabling real-time token-by-token rendering in UIs.

        Flow:
        1. Validate input
        2. Build prompt
        3. Stream from LLM (with retry logic)
        4. Yield chunks in real-time

        Args:
            context: Agent execution context
            **kwargs: Additional arguments

        Yields:
            str: Response chunks as they arrive

        Raises:
            ValueError: If streaming is not enabled in config
            ProviderError: If execution fails
        """
        if not self.config.streaming_enabled:
            raise ValueError(
                f"Streaming not enabled for agent '{self.config.name}'. "
                "Set streaming_enabled=True in AgentConfig."
            )

        start_time = time.time()

        self.logger.info(
            "agent_streaming_started",
            agent=self.config.name,
            correlation_id=context.correlation_id,
            user_input_preview=context.user_input[:100],
        )

        try:
            # 1. Validate input
            is_valid, error_msg = await self.validate_input(context)
            if not is_valid:
                self.logger.warning(
                    "agent_validation_failed",
                    agent=self.config.name,
                    error=error_msg,
                )
                yield f"[Error: {error_msg}]"
                return

            # 2. Build prompt
            messages = await self._build_prompt(context)

            # 3. Stream from LLM with retry logic
            total_tokens = 0
            collected_content = ""

            async for chunk in self._call_llm_streaming_with_retry(messages, context):
                collected_content += chunk
                yield chunk

            # 4. Update metrics (estimate tokens from content)
            # Note: Exact token count not available in streaming mode
            # We'll estimate based on content length
            estimated_tokens = len(collected_content) // 4  # Rough estimate
            self.total_requests += 1
            self.total_tokens += estimated_tokens

            latency_ms = (time.time() - start_time) * 1000

            self.logger.info(
                "agent_streaming_completed",
                agent=self.config.name,
                correlation_id=context.correlation_id,
                estimated_tokens=estimated_tokens,
                latency_ms=latency_ms,
                content_length=len(collected_content),
            )

        except Exception as e:
            self.total_errors += 1

            self.logger.error(
                "agent_streaming_failed",
                agent=self.config.name,
                correlation_id=context.correlation_id,
                error=str(e),
                error_type=type(e).__name__,
            )

            yield f"\n\n[Error: {str(e)}]"

    async def validate_input(self, context: AgentContext) -> tuple[bool, Optional[str]]:
        """
        Default validation - can be overridden by subclasses.

        Args:
            context: Agent execution context

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation
        if not context.user_input or len(context.user_input.strip()) == 0:
            return False, "User input is required"

        if len(context.user_input) > 10000:
            return False, "User input too long (max 10000 characters)"

        return True, None

    async def cleanup(self) -> None:
        """Default cleanup - can be overridden by subclasses."""
        # Log metrics
        self.logger.info(
            "agent_cleanup",
            agent=self.config.name,
            total_requests=self.total_requests,
            total_tokens=self.total_tokens,
            total_cost_usd=self.total_cost,
            total_errors=self.total_errors,
        )

    # Abstract methods that subclasses must implement

    @abstractmethod
    async def _build_prompt(self, context: AgentContext) -> list[Message]:
        """
        Build the prompt for this agent.

        Subclasses must implement this to construct agent-specific
        prompts based on the context.

        Args:
            context: Agent execution context

        Returns:
            List of messages to send to LLM
        """
        pass

    async def _parse_response(
        self,
        response: AgentResponse,
        context: AgentContext,
    ) -> AgentResponse:
        """
        Parse and process the LLM response.

        Subclasses can override this to extract structured data,
        validate outputs, or add metadata.

        Default implementation returns response as-is.

        Args:
            response: Raw response from LLM
            context: Agent execution context

        Returns:
            Processed AgentResponse
        """
        return response

    # Helper methods

    async def _call_llm_with_retry(
        self,
        messages: list[Message],
        context: AgentContext,
    ) -> AgentResponse:
        """
        Call LLM with retry logic.

        Args:
            messages: Messages to send
            context: Agent execution context

        Returns:
            AgentResponse

        Raises:
            ProviderError: If all retries fail
        """
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                # Get system prompt
                system_prompt = self.config.system_prompt

                # Override model if specified in config
                temperature = self.config.temperature
                max_tokens = self.config.max_tokens

                # Check cost limit before calling
                # (simplified - would need to estimate tokens first)

                # Call provider
                response = await self.provider.generate(
                    messages=messages,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                # Check cost after calling
                if response.usage.estimated_cost_usd > self.config.max_cost_per_request:
                    self.logger.warning(
                        "agent_cost_exceeded",
                        agent=self.config.name,
                        cost=response.usage.estimated_cost_usd,
                        limit=self.config.max_cost_per_request,
                    )

                return response

            except ProviderError as e:
                last_error = e

                self.logger.warning(
                    "agent_llm_call_failed",
                    agent=self.config.name,
                    attempt=attempt + 1,
                    max_retries=self.config.max_retries,
                    error=str(e),
                )

                # If this was the last attempt, raise
                if attempt >= self.config.max_retries:
                    break

                # Wait before retrying (exponential backoff)
                import asyncio

                await asyncio.sleep(2**attempt)

        # All retries failed
        raise last_error or ProviderError(
            "LLM call failed after all retries",
            provider=self.provider.provider_name,
        )

    async def _call_llm_streaming_with_retry(
        self,
        messages: list[Message],
        context: AgentContext,
    ) -> AsyncIterator[str]:
        """
        Call LLM in streaming mode with retry logic.

        Args:
            messages: Messages to send
            context: Agent execution context

        Yields:
            str: Response chunks as they arrive

        Raises:
            ProviderError: If all retries fail
        """
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                # Get system prompt
                system_prompt = self.config.system_prompt

                # Get parameters from config
                temperature = self.config.temperature
                max_tokens = self.config.max_tokens

                # Stream from provider
                async for chunk in self.provider.stream(
                    messages=messages,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ):
                    yield chunk

                # If we got here, streaming succeeded
                return

            except ProviderError as e:
                last_error = e

                self.logger.warning(
                    "agent_llm_streaming_failed",
                    agent=self.config.name,
                    attempt=attempt + 1,
                    max_retries=self.config.max_retries,
                    error=str(e),
                )

                # If this was the last attempt, raise
                if attempt >= self.config.max_retries:
                    break

                # Wait before retrying (exponential backoff)
                import asyncio

                await asyncio.sleep(2**attempt)

        # All retries failed
        raise last_error or ProviderError(
            "LLM streaming call failed after all retries",
            provider=self.provider.provider_name,
        )

    def _create_message(self, role: Role, content: str) -> Message:
        """
        Create a message.

        Args:
            role: Message role
            content: Message content

        Returns:
            Message instance
        """
        return Message(role=role, content=content)

    def get_metrics(self) -> dict[str, Any]:
        """
        Get agent metrics.

        Returns:
            Dictionary with metrics
        """
        return {
            "agent": self.config.name,
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost,
            "total_errors": self.total_errors,
            "error_rate": self.total_errors / max(self.total_requests, 1),
            "avg_tokens_per_request": self.total_tokens / max(self.total_requests, 1),
            "avg_cost_per_request": self.total_cost / max(self.total_requests, 1),
        }
