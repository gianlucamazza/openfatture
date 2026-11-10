"""Central registry for AI tools and function calling."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from openfatture.ai.orchestration.resilience import CircuitBreaker
from openfatture.ai.tools.models import Tool, ToolResult
from openfatture.ai.tools.registry.metrics import circuit_breaker_stats, circuit_breaker_summary
from openfatture.ai.tools.registry.policy import (
    ToolSource,
    confirmation_required,
    has_human_confirmation,
    is_tool_enabled_for_agent,
    is_transmit_tool,
    strip_reserved_parameters,
)
from openfatture.ai.tools.registry.resilience import (
    Bulkhead,
    bulkhead_config_for,
    circuit_breaker_config_for,
)
from openfatture.platform.config import get_settings
from openfatture.platform.logging import get_logger
from openfatture.platform.rate_limiter import RateLimiter

if TYPE_CHECKING:
    from openfatture.ai.cache.tool_cache import ToolResultCache
    from openfatture.ai.tools.metrics import ToolMetricsCollector

logger = get_logger(__name__)


class ToolRegistry:
    """
    Central registry for managing AI tools.

    Provides:
    - Tool registration and discovery
    - Schema generation for LLM providers
    - Safe tool execution with validation
    - Category-based filtering
    """

    def __init__(self, *, apply_ai_settings: bool = False) -> None:
        """Initialize registry, optionally honoring the configured AI allowlist."""
        from collections.abc import Awaitable, Callable

        from openfatture.ai.runtime.contracts import ActivityCallback, ConfirmCallback

        self.execution_timeout_seconds: float = 60
        self.confirmation_callback: ConfirmCallback | None = None
        self.activity_callback: ActivityCallback | None = None
        self.outcome_callback: Callable[[str, bool], Awaitable[None]] | None = None

        self._tools: dict[str, Tool] = {}
        self._categories: dict[str, list[str]] = {}
        self._apply_ai_settings = apply_ai_settings
        # Rate limiters: 10 calls per minute per tool
        self._rate_limiters: dict[str, RateLimiter] = {}

        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._bulkheads: dict[str, Bulkhead] = {}

        # Initialize cache and metrics (lazy loaded)
        self._cache: ToolResultCache | None = None
        self._metrics: ToolMetricsCollector | None = None

        logger.info("tool_registry_initialized")

    def _get_cache(self) -> ToolResultCache | None:
        """Lazy load tool cache."""
        if self._cache is None:
            try:
                import importlib

                tool_cache_module = importlib.import_module("openfatture.ai.cache.tool_cache")
                self._cache = tool_cache_module.get_tool_cache()
            except (ImportError, AttributeError):
                logger.warning("tool_cache_not_available")
                self._cache = None
        return self._cache

    def _get_metrics(self) -> ToolMetricsCollector | None:
        """Lazy load metrics collector."""
        if self._metrics is None:
            try:
                import importlib

                metrics_module = importlib.import_module("openfatture.ai.tools.metrics")
                self._metrics = metrics_module.get_tool_metrics_collector()
            except (ImportError, AttributeError):
                logger.warning("tool_metrics_not_available")
                self._metrics = None
        return self._metrics

    def _record(self, result: ToolResult) -> None:
        """Record an execution outcome in the metrics collector, when available."""
        metrics = self._get_metrics()
        if metrics:
            metrics.record_execution(result)

    def register(self, tool: Tool) -> None:
        """
        Register a tool.

        Args:
            tool: Tool to register
        """
        if tool.name in self._tools:
            logger.warning("tool_already_registered", name=tool.name)

        self._tools[tool.name] = tool

        # Add to category index
        if tool.category not in self._categories:
            self._categories[tool.category] = []
        if tool.name not in self._categories[tool.category]:
            self._categories[tool.category].append(tool.name)

        logger.info(
            "tool_registered",
            name=tool.name,
            category=tool.category,
            parameters_count=len(tool.parameters),
        )

    def get_tool(self, name: str) -> Tool | None:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool if found, None otherwise
        """
        return self._tools.get(name)

    def list_tools(
        self,
        category: str | None = None,
        enabled_only: bool = True,
    ) -> list[Tool]:
        """
        List all tools.

        Args:
            category: Filter by category
            enabled_only: Only return enabled tools

        Returns:
            List of tools
        """
        tools = list(self._tools.values())

        if category:
            tools = [t for t in tools if t.category == category]

        if enabled_only:
            settings = get_settings()
            tools = [
                tool
                for tool in tools
                if is_tool_enabled_for_agent(
                    tool.name,
                    settings.ai_enabled_tools,
                    apply_allowlist=self._apply_ai_settings,
                    tool_enabled=tool.enabled,
                )
            ]

        return tools

    def get_circuit_breaker(self, tool_name: str) -> CircuitBreaker:
        """Get or create the circuit breaker for a tool."""
        if tool_name not in self._circuit_breakers:
            self._circuit_breakers[tool_name] = CircuitBreaker(
                name=f"tool_{tool_name}", config=circuit_breaker_config_for(tool_name)
            )
            logger.debug("circuit_breaker_created", tool_name=tool_name)

        return self._circuit_breakers[tool_name]

    def get_bulkhead(self, tool_name: str) -> Bulkhead:
        """Get or create the bulkhead limiting concurrent executions of a tool."""
        if tool_name not in self._bulkheads:
            self._bulkheads[tool_name] = Bulkhead(bulkhead_config_for(tool_name))
            logger.debug("bulkhead_created", tool_name=tool_name)

        return self._bulkheads[tool_name]

    def reset_circuit_breaker(self, tool_name: str) -> bool:
        """
        Manually reset circuit breaker for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            True if reset was successful, False if tool not found
        """
        if tool_name in self._circuit_breakers:
            self._circuit_breakers[tool_name].reset()
            logger.info("circuit_breaker_reset", tool_name=tool_name)
            return True

        logger.warning("circuit_breaker_not_found", tool_name=tool_name)
        return False

    def get_circuit_breaker_stats(self) -> dict[str, dict[str, Any]]:
        """Statistics for all circuit breakers, keyed by tool name."""
        return circuit_breaker_stats(self._circuit_breakers)

    def get_openai_functions(
        self,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get tools in OpenAI function calling format.

        For Chat Completions API, tools should be in the format:
        {"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}

        NOT the old Responses API format:
        {"type": "function", "name": ..., "description": ..., "parameters": ...}

        Args:
            category: Filter by category

        Returns:
            List of function schemas for OpenAI Chat Completions API
        """
        tools = self.list_tools(category=category, enabled_only=True)
        return [{"type": "function", "function": tool.to_openai_function()} for tool in tools]

    def get_anthropic_tools(
        self,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get tools in Anthropic tool calling format.

        Args:
            category: Filter by category

        Returns:
            List of tool schemas for Anthropic API
        """
        tools = self.list_tools(category=category, enabled_only=True)
        return [tool.to_anthropic_tool() for tool in tools]

    async def execute_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        confirm: bool | None = None,
        *,
        confirmed: bool = False,
        source: ToolSource = "ai",
    ) -> ToolResult:
        from copy import deepcopy

        from openfatture.ai.runtime.contracts import current_accounting
        from openfatture.platform.logging import redact_sensitive

        snapshot = deepcopy(strip_reserved_parameters(parameters))
        outcome = {
            "tool": tool_name,
            "parameters": redact_sensitive(snapshot),
            "success": False,
            "result": "interrupted_outcome_unknown",
        }
        try:
            result = await self._execute_tool(
                tool_name, snapshot, confirmed=confirmed, source=source
            )
            outcome.update(
                success=result.success, result=result.error_type or result.error or "completed"
            )
            return result
        finally:
            accounting = current_accounting.get()
            if accounting is not None:
                accounting.tool_outcomes.append(outcome)
            if self.outcome_callback:
                await self.outcome_callback(tool_name, bool(outcome["success"]))

    async def _execute_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        *,
        confirmed: bool = False,
        source: ToolSource = "ai",
    ) -> ToolResult:
        """
        Execute a tool by name with caching and metrics.

        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters. Confirm-like keys are ignored
                (case-insensitive). Shown on the interactive confirmation
                prompt when a human yes is required.
            confirmed: Set True only after a human-facing path received yes.
                Ignored unless ``source="human"``. No built-in UI uses this
                path yet.
            source: ``"ai"`` (default, cannot self-confirm) or ``"human"``.

        Returns:
            ToolResult with execution outcome
        """
        # Get tool
        tool = self.get_tool(tool_name)
        parameters = strip_reserved_parameters(parameters)

        if not tool:
            logger.error("tool_not_found", name=tool_name)
            result = ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found",
                tool_name=tool_name,
            )
            self._record(result)
            return result

        settings = get_settings()
        if not is_tool_enabled_for_agent(
            tool.name,
            settings.ai_enabled_tools,
            apply_allowlist=self._apply_ai_settings,
            tool_enabled=tool.enabled,
        ):
            logger.error("tool_disabled", name=tool_name)
            if is_transmit_tool(tool_name):
                error = (
                    f"Tool '{tool_name}' is disabled. Transmit tools (SDI/PEC send) "
                    "stay off unless explicitly listed in ai_enabled_tools."
                )
            else:
                error = f"Tool '{tool_name}' is disabled"
            result = ToolResult(
                success=False,
                error=error,
                error_type="tool_disabled",
                tool_name=tool_name,
            )
            self._record(result)
            return result

        if confirmation_required(
            tool_name,
            tool_requires_confirmation=tool.requires_confirmation,
            require_confirmation=settings.ai_tools_require_confirmation,
        ):
            from copy import deepcopy

            if source == "human" and confirmed:
                approved = True
                error_type = "confirmation_denied"
            elif self.confirmation_callback is not None:
                approved = await self.confirmation_callback(tool_name, deepcopy(parameters))
                error_type = "confirmation_denied"
            else:
                approved = await has_human_confirmation(
                    source=source, confirmed=confirmed, tool_name=tool_name, parameters=parameters
                )
                error_type = "confirmation_required"
            if not approved:
                result = ToolResult(
                    success=False,
                    error=f"Tool '{tool_name}' requires an explicit human confirmation before execution.",
                    error_type=error_type,
                    tool_name=tool_name,
                )
                self._record(result)
                return result

        # Try cache first for read operations
        cache = self._get_cache()
        if cache and cache.is_cacheable(tool_name):
            cached_result = await cache.get_cached_result(tool_name, parameters)
            if cached_result:
                logger.info("tool_cache_hit", name=tool_name)
                self._record(cached_result)
                return cached_result

        # Check rate limiting (per tool)
        if tool_name not in self._rate_limiters:
            self._rate_limiters[tool_name] = RateLimiter(max_calls=10, period=60)

        if not self._rate_limiters[tool_name].acquire(blocking=False):
            logger.warning("tool_rate_limited", name=tool_name)
            result = ToolResult(
                success=False,
                error="Tool rate limit exceeded. Please wait before making another request.",
                tool_name=tool_name,
            )
            self._record(result)
            return result

        # Check circuit breaker (Phase 3)
        circuit_breaker = self.get_circuit_breaker(tool_name)
        if not circuit_breaker.can_attempt():
            logger.warning("tool_circuit_breaker_open", name=tool_name)
            result = ToolResult(
                success=False,
                error="Tool circuit breaker is open. Tool temporarily unavailable due to repeated failures.",
                tool_name=tool_name,
                error_type="circuit_breaker_open",
            )
            # Record circuit breaker state in result
            result.circuit_breaker_state = circuit_breaker.state.state.value
            self._record(result)
            return result

        bulkhead = self.get_bulkhead(tool_name)
        if not await bulkhead.acquire():
            logger.warning("tool_bulkhead_limit_exceeded", name=tool_name)
            result = ToolResult(
                success=False,
                error=f"Tool '{tool_name}' concurrency limit exceeded. Please wait for other executions to complete.",
                tool_name=tool_name,
                error_type="bulkhead_limit_exceeded",
            )
            result.bulkhead_queue_length = bulkhead.queued
            self._record(result)
            return result

        try:
            # Execute tool
            logger.info(
                "tool_executing",
                name=tool_name,
                parameters=parameters,
            )

            activity = getattr(self, "activity_callback", None)
            if activity:
                await activity(tool_name)
            result = await asyncio.wait_for(
                tool.execute(**parameters), timeout=self.execution_timeout_seconds
            )

            # Refusals by the application ("not found", validation) are not
            # faults of the tool and must not open the circuit.
            if result.success or result.metadata.get("application_error"):
                circuit_breaker.record_success()
            else:
                circuit_breaker.record_failure()

            # Add circuit breaker state to result
            result.circuit_breaker_state = circuit_breaker.state.state.value

            result.bulkhead_queue_length = bulkhead.queued

            # Cache successful results for read operations
            if cache and cache.is_cacheable(tool_name) and result.success:
                await cache.cache_result(tool_name, parameters, result)

            logger.info(
                "tool_executed",
                name=tool_name,
                success=result.success,
                error=result.error if not result.success else None,
                execution_time=result.execution_time,
                retries=result.retries,
                cache_hit=result.cache_hit,
                circuit_breaker_state=result.circuit_breaker_state,
                bulkhead_queue_length=result.bulkhead_queue_length,
            )

            self._record(result)

            return result
        finally:
            bulkhead.release()

    def get_stats(self) -> dict[str, Any]:
        """
        Get registry statistics.

        ``enabled_tools`` follows the same allowlist / transmit policy as
        ``list_tools(enabled_only=True)``. ``enabled_by_tool_flag`` is the
        older count of tools whose own ``enabled`` flag is True.

        Returns:
            Dictionary with stats
        """
        policy_enabled = self.list_tools(enabled_only=True)
        flag_enabled = [tool for tool in self._tools.values() if tool.enabled]

        return {
            "total_tools": len(self._tools),
            "enabled_tools": len(policy_enabled),
            "enabled_by_tool_flag": len(flag_enabled),
            "enabled_tool_names": [tool.name for tool in policy_enabled],
            "categories": len(self._categories),
            "tools_by_category": {cat: len(tools) for cat, tools in self._categories.items()},
            "circuit_breakers": circuit_breaker_summary(self._circuit_breakers),
        }
