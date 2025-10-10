"""Resilience Layer for AI Agent Orchestration.

Enterprise-grade resilience patterns for AI systems:
- Circuit Breaker: Prevent cascading failures
- Exponential Backoff: Graceful retry with jitter
- Fallback Chains: Provider failover (Anthropic → OpenAI → Ollama)
- Timeout Management: Prevent hanging operations
- Health Checks: Monitor provider availability

Architecture:
- CircuitBreaker: Per-provider circuit state management
- ResiliencePolicy: Configurable retry/fallback policies
- HealthCheckMonitor: Periodic provider health checks
- ResilientProvider: Wrapper with automatic failover

Example:
    >>> policy = ResiliencePolicy(
    ...     max_retries=3,
    ...     fallback_providers=["openai", "ollama"]
    ... )
    >>> provider = ResilientProvider(
    ...     primary_provider=anthropic_provider,
    ...     policy=policy
    ... )
    >>> response = await provider.chat_with_resilience(messages)
"""

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from openfatture.ai.domain.message import Message
from openfatture.ai.domain.response import AIResponse
from openfatture.ai.providers import create_provider
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures detected, circuit is open
    HALF_OPEN = "half_open"  # Testing if service recovered


class FailureType(Enum):
    """Types of failures tracked."""

    TIMEOUT = "timeout"
    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    NETWORK_ERROR = "network_error"
    INVALID_RESPONSE = "invalid_response"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""

    failure_threshold: int = 5  # Failures to open circuit
    success_threshold: int = 2  # Successes to close from half-open
    timeout_seconds: int = 60  # Time before attempting recovery
    half_open_max_calls: int = 3  # Max calls in half-open state


@dataclass
class CircuitBreakerState:
    """Circuit breaker runtime state."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    last_state_change: datetime = field(default_factory=datetime.utcnow)
    half_open_calls: int = 0

    def reset(self) -> None:
        """Reset to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_state_change = datetime.utcnow()

    def record_failure(self, config: CircuitBreakerConfig) -> None:
        """Record a failure and update state."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        self.success_count = 0  # Reset success count

        if self.state == CircuitState.HALF_OPEN:
            # Immediately open if failure in half-open
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.utcnow()
            self.half_open_calls = 0
        elif self.failure_count >= config.failure_threshold:
            # Open circuit if threshold reached
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.utcnow()

    def record_success(self, config: CircuitBreakerConfig) -> None:
        """Record a success and update state."""
        self.failure_count = 0  # Reset failure count

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= config.success_threshold:
                # Close circuit if enough successes
                self.reset()
        elif self.state == CircuitState.CLOSED:
            # Already closed, just reset counters
            self.success_count = 0

    def can_attempt(self, config: CircuitBreakerConfig) -> bool:
        """Check if operation can be attempted."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout elapsed
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= config.timeout_seconds:
                    # Transition to half-open
                    self.state = CircuitState.HALF_OPEN
                    self.last_state_change = datetime.utcnow()
                    self.half_open_calls = 0
                    return True

            return False  # Circuit still open

        if self.state == CircuitState.HALF_OPEN:
            # Allow limited calls in half-open
            if self.half_open_calls < config.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False

        return False


class CircuitBreaker:
    """Circuit Breaker pattern implementation.

    Prevents cascading failures by stopping calls to failing services.

    States:
    - CLOSED: Normal operation
    - OPEN: Too many failures, reject calls
    - HALF_OPEN: Testing recovery, limited calls allowed

    Example:
        >>> breaker = CircuitBreaker(name="anthropic")
        >>> if breaker.can_attempt():
        ...     try:
        ...         result = await provider.generate(messages)
        ...         breaker.record_success()
        ...     except Exception as e:
        ...         breaker.record_failure()
        ...         raise
    """

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ):
        """Initialize circuit breaker.

        Args:
            name: Identifier for this circuit
            config: Circuit breaker configuration
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState()

        logger.info(
            "circuit_breaker_initialized",
            name=name,
            failure_threshold=self.config.failure_threshold,
        )

    def can_attempt(self) -> bool:
        """Check if operation can be attempted."""
        can_proceed = self.state.can_attempt(self.config)

        if not can_proceed:
            logger.warning(
                "circuit_breaker_open",
                name=self.name,
                state=self.state.state.value,
                failure_count=self.state.failure_count,
            )

        return can_proceed

    def record_success(self) -> None:
        """Record successful operation."""
        previous_state = self.state.state

        self.state.record_success(self.config)

        if previous_state != self.state.state:
            logger.info(
                "circuit_breaker_state_changed",
                name=self.name,
                from_state=previous_state.value,
                to_state=self.state.state.value,
            )

    def record_failure(self, failure_type: FailureType = FailureType.API_ERROR) -> None:
        """Record failed operation."""
        previous_state = self.state.state

        self.state.record_failure(self.config)

        logger.warning(
            "circuit_breaker_failure_recorded",
            name=self.name,
            failure_type=failure_type.value,
            failure_count=self.state.failure_count,
            state=self.state.state.value,
        )

        if previous_state != self.state.state:
            logger.error(
                "circuit_breaker_opened",
                name=self.name,
                failure_count=self.state.failure_count,
                threshold=self.config.failure_threshold,
            )

    def reset(self) -> None:
        """Manually reset circuit breaker."""
        logger.info("circuit_breaker_reset", name=self.name)
        self.state.reset()


@dataclass
class RetryConfig:
    """Retry configuration with exponential backoff."""

    max_retries: int = 3
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True  # Add randomness to prevent thundering herd

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = min(
            self.initial_delay_seconds * (self.exponential_base**attempt),
            self.max_delay_seconds,
        )

        if self.jitter:
            # Add jitter: ±25% random variation
            jitter_amount = delay * 0.25
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0.0, delay)


class ResiliencePolicy(BaseModel):
    """Resilience policy configuration.

    Defines retry, fallback, and circuit breaker behavior.
    """

    # Retry configuration
    max_retries: int = Field(default=3, ge=0, le=10)
    initial_retry_delay: float = Field(default=1.0, gt=0)
    max_retry_delay: float = Field(default=60.0, gt=0)
    enable_jitter: bool = Field(default=True)

    # Circuit breaker
    circuit_failure_threshold: int = Field(default=5, ge=1)
    circuit_timeout_seconds: int = Field(default=60, ge=10)

    # Fallback providers (in order of preference)
    fallback_providers: list[str] = Field(default_factory=list)

    # Timeout
    operation_timeout_seconds: int = Field(default=120, ge=10)

    def get_retry_config(self) -> RetryConfig:
        """Get retry configuration."""
        return RetryConfig(
            max_retries=self.max_retries,
            initial_delay_seconds=self.initial_retry_delay,
            max_delay_seconds=self.max_retry_delay,
            jitter=self.enable_jitter,
        )

    def get_circuit_config(self) -> CircuitBreakerConfig:
        """Get circuit breaker configuration."""
        return CircuitBreakerConfig(
            failure_threshold=self.circuit_failure_threshold,
            timeout_seconds=self.circuit_timeout_seconds,
        )


class ResilientProvider:
    """AI Provider wrapper with resilience patterns.

    Provides automatic retry, fallback, and circuit breaker protection.

    Example:
        >>> policy = ResiliencePolicy(
        ...     fallback_providers=["openai", "ollama"]
        ... )
        >>> provider = ResilientProvider(
        ...     primary_provider=anthropic_provider,
        ...     policy=policy
        ... )
        >>> response = await provider.generate_with_resilience(messages)
    """

    def __init__(
        self,
        primary_provider: BaseLLMProvider,
        policy: ResiliencePolicy | None = None,
    ):
        """Initialize resilient provider.

        Args:
            primary_provider: Primary AI provider to use
            policy: Resilience policy (uses defaults if None)
        """
        self.primary_provider = primary_provider
        self.policy = policy or ResiliencePolicy()

        # Circuit breaker for primary provider
        self.circuit_breaker = CircuitBreaker(
            name=f"provider_{primary_provider.provider}",
            config=self.policy.get_circuit_config(),
        )

        # Fallback providers (lazily initialized)
        self.fallback_providers: list[BaseLLMProvider] = []

        logger.info(
            "resilient_provider_initialized",
            primary=primary_provider.provider,
            fallbacks=self.policy.fallback_providers,
        )

    def _initialize_fallback_providers(self) -> None:
        """Initialize fallback providers on-demand."""
        if self.fallback_providers:
            return  # Already initialized

        for provider_name in self.policy.fallback_providers:
            try:
                provider = create_provider(provider_name=provider_name)
                self.fallback_providers.append(provider)
                logger.info("fallback_provider_initialized", provider=provider_name)
            except Exception as e:
                logger.warning(
                    "fallback_provider_init_failed",
                    provider=provider_name,
                    error=str(e),
                )

    async def generate_with_resilience(
        self,
        messages: list[Message],
        **kwargs: Any,
    ) -> AIResponse:
        """Execute chat with retry, fallback, and circuit breaker.

        Args:
            messages: Messages to send
            **kwargs: Additional provider arguments

        Returns:
            AIResponse from primary or fallback provider

        Raises:
            Exception: If all providers fail
        """
        retry_config = self.policy.get_retry_config()

        # Try primary provider with retry
        for attempt in range(retry_config.max_retries + 1):
            if not self.circuit_breaker.can_attempt():
                logger.warning(
                    "circuit_breaker_open_skipping_primary",
                    provider=self.primary_provider.provider,
                )
                break  # Skip to fallback

            try:
                # Execute with timeout
                response = await asyncio.wait_for(
                    self.primary_provider.generate(messages, **kwargs),
                    timeout=self.policy.operation_timeout_seconds,
                )

                self.circuit_breaker.record_success()

                logger.info(
                    "primary_provider_success",
                    provider=self.primary_provider.provider,
                    attempt=attempt + 1,
                )

                return response

            except TimeoutError:
                logger.warning(
                    "provider_timeout",
                    provider=self.primary_provider.provider,
                    timeout=self.policy.operation_timeout_seconds,
                    attempt=attempt + 1,
                )
                self.circuit_breaker.record_failure(FailureType.TIMEOUT)

            except Exception as e:
                logger.warning(
                    "provider_error",
                    provider=self.primary_provider.provider,
                    error=str(e),
                    attempt=attempt + 1,
                )
                self.circuit_breaker.record_failure(FailureType.API_ERROR)

            # Exponential backoff before retry
            if attempt < retry_config.max_retries:
                delay = retry_config.get_delay(attempt)
                logger.info("retrying_after_delay", delay_seconds=delay, attempt=attempt + 1)
                await asyncio.sleep(delay)

        # Primary provider failed, try fallbacks
        logger.warning(
            "primary_provider_exhausted_trying_fallbacks",
            provider=self.primary_provider.provider,
        )

        self._initialize_fallback_providers()

        for fallback_provider in self.fallback_providers:
            try:
                logger.info(
                    "attempting_fallback_provider",
                    fallback=fallback_provider.provider,
                )

                response = await asyncio.wait_for(
                    fallback_provider.generate(messages, **kwargs),
                    timeout=self.policy.operation_timeout_seconds,
                )

                logger.info(
                    "fallback_provider_success",
                    fallback=fallback_provider.provider,
                )

                return response

            except Exception as e:
                logger.warning(
                    "fallback_provider_failed",
                    fallback=fallback_provider.provider,
                    error=str(e),
                )
                continue

        # All providers failed
        error_msg = "All providers failed (primary + fallbacks)"
        logger.error(
            "all_providers_failed",
            primary=self.primary_provider.provider,
            fallbacks=[p.provider for p in self.fallback_providers],
        )

        raise RuntimeError(error_msg)


def create_resilient_provider(
    primary_provider_name: str = "anthropic",
    fallback_providers: list[str] | None = None,
) -> ResilientProvider:
    """Create resilient provider with fallback chain.

    Args:
        primary_provider_name: Primary provider to use
        fallback_providers: List of fallback providers (default: ["openai", "ollama"])

    Returns:
        ResilientProvider with configured fallbacks

    Example:
        >>> provider = create_resilient_provider(
        ...     primary_provider_name="anthropic",
        ...     fallback_providers=["openai", "ollama"]
        ... )
        >>> response = await provider.generate_with_resilience(messages)
    """
    if fallback_providers is None:
        fallback_providers = ["openai", "ollama"]

    primary = create_provider(provider_name=primary_provider_name)

    policy = ResiliencePolicy(fallback_providers=fallback_providers)

    return ResilientProvider(primary_provider=primary, policy=policy)
