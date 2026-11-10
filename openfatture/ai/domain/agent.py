"""Base agent implementation."""

import time
from abc import abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from openfatture.ai.domain.agent_contract import AgentConfig, AgentProtocol
from openfatture.ai.domain.context import AgentContext
from openfatture.ai.domain.llm_retry import generate_with_retry, stream_with_retry
from openfatture.ai.domain.message import Message
from openfatture.ai.domain.response import AgentResponse, ResponseStatus
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.ai.streaming.events import StreamEvent
from openfatture.platform.logging import get_logger

logger = get_logger(__name__)


class BaseAgent[ContextT: AgentContext](AgentProtocol[ContextT]):
    """
    Base implementation of AgentProtocol.

    Provides common functionality for all agents:
    - Provider management
    - Structured logging
    - Metrics collection
    - Error handling
    - Cost tracking
    - Retry logic

    Generic over ContextT to support specialized contexts:
    - ChatAgent[ChatContext]
    - TaxAdvisor[TaxContext]
    - InvoiceAssistant[InvoiceContext]
    etc.

    Concrete agents should:
    1. Inherit from BaseAgent[YourContextType]
    2. Override _build_prompt() to construct agent-specific prompts
    3. Override _parse_response() to extract structured data
    4. Optionally override validate_input() for custom validation
    """

    def __init__(
        self,
        config: AgentConfig,
        provider: BaseLLMProvider,
        logger_instance: Any | None = None,
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
        context: ContextT,
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
            context: Agent execution context (specialized per agent type)
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
            response = await generate_with_retry(
                self.provider, self.config, self.logger, messages, **kwargs
            )

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
        context: ContextT,
        **kwargs: Any,
    ) -> AsyncIterator[str | StreamEvent]:
        """
        Execute the agent with streaming response.

        This method yields response chunks as they arrive from the LLM,
        enabling real-time token-by-token rendering in UIs. Specialized agents
        may yield typed :class:`StreamEvent` values instead of bare strings.

        Flow:
        1. Validate input
        2. Build prompt
        3. Stream from LLM (with retry logic)
        4. Yield chunks in real-time

        Args:
            context: Agent execution context (specialized per agent type)
            **kwargs: Additional arguments

        Yields:
            ``str`` tokens or typed :class:`StreamEvent` items

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
            collected_content = ""

            async for chunk in stream_with_retry(
                self.provider, self.config, self.logger, messages, **kwargs
            ):
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

    async def validate_input(self, context: ContextT) -> tuple[bool, str | None]:
        """
        Default validation - can be overridden by subclasses.

        Args:
            context: Agent execution context (specialized per agent type)

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
    async def _build_prompt(self, context: ContextT) -> list[Message]:
        """
        Build the prompt for this agent.

        Subclasses must implement this to construct agent-specific
        prompts based on the context.

        Args:
            context: Agent execution context (specialized per agent type)

        Returns:
            List of messages to send to LLM
        """
        pass

    async def _parse_response(
        self,
        response: AgentResponse,
        context: ContextT,
    ) -> AgentResponse:
        """
        Parse and process the LLM response.

        Subclasses can override this to extract structured data,
        validate outputs, or add metadata.

        Default implementation returns response as-is.

        Args:
            response: Raw response from LLM
            context: Agent execution context (specialized per agent type)

        Returns:
            Processed AgentResponse
        """
        return response

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
