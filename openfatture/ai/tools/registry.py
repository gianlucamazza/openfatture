"""Central registry for AI tools and function calling."""

import asyncio
from typing import Any

from openfatture.ai.orchestration.resilience import (
    BulkheadConfig,
    CircuitBreaker,
    CircuitBreakerConfig,
)
from openfatture.ai.tools.models import Tool, ToolResult
from openfatture.utils.logging import get_logger
from openfatture.utils.rate_limiter import RateLimiter

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

    def __init__(self) -> None:
        """Initialize empty tool registry."""
        self._tools: dict[str, Tool] = {}
        self._categories: dict[str, list[str]] = {}
        # Rate limiters: 10 calls per minute per tool
        self._rate_limiters: dict[str, RateLimiter] = {}

        # Circuit breakers for resilience (Phase 3)
        self._circuit_breakers: dict[str, CircuitBreaker] = {}

        # Bulkhead semaphores for concurrency limiting (Phase 3)
        self._bulkhead_semaphores: dict[str, asyncio.Semaphore] = {}

        # Initialize cache and metrics (lazy loaded)
        self._cache = None
        self._metrics = None

        logger.info("tool_registry_initialized")

    def _get_cache(self):
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

    def _get_metrics(self):
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

    def unregister(self, tool_name: str) -> bool:
        """
        Unregister a tool.

        Args:
            tool_name: Name of tool to remove

        Returns:
            True if removed, False if not found
        """
        if tool_name in self._tools:
            tool = self._tools[tool_name]

            # Remove from category index
            if tool.category in self._categories:
                self._categories[tool.category].remove(tool_name)

            del self._tools[tool_name]
            logger.info("tool_unregistered", name=tool_name)
            return True

        return False

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
            tools = [t for t in tools if t.enabled]

        return tools

    def get_categories(self) -> list[str]:
        """Get all tool categories."""
        return list(self._categories.keys())

    def get_circuit_breaker(self, tool_name: str) -> CircuitBreaker:
        """
        Get or create circuit breaker for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            CircuitBreaker instance for the tool
        """
        if tool_name not in self._circuit_breakers:
            config = self._get_resilience_config(tool_name)
            self._circuit_breakers[tool_name] = CircuitBreaker(
                name=f"tool_{tool_name}", config=config
            )
            logger.debug("circuit_breaker_created", tool_name=tool_name)

        return self._circuit_breakers[tool_name]

    def get_bulkhead_semaphore(self, tool_name: str) -> asyncio.Semaphore:
        """
        Get or create bulkhead semaphore for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Semaphore for limiting concurrent executions
        """
        if tool_name not in self._bulkhead_semaphores:
            config = self._get_bulkhead_config(tool_name)
            self._bulkhead_semaphores[tool_name] = asyncio.Semaphore(
                config.max_concurrent_executions
            )
            logger.debug("bulkhead_semaphore_created", tool_name=tool_name)

        return self._bulkhead_semaphores[tool_name]

    def _get_bulkhead_config(self, tool_name: str) -> BulkheadConfig:
        """
        Get bulkhead configuration based on tool characteristics.

        Different concurrency limits for different tool types:
        - Read operations: higher concurrency (more parallel requests)
        - Write operations: lower concurrency (safer, less resource intensive)

        Args:
            tool_name: Name of the tool

        Returns:
            BulkheadConfig for the tool
        """
        # Read operations - higher concurrency allowed
        read_tools = {
            "search_invoices",
            "get_invoice_details",
            "get_invoice_stats",
            "search_clients",
            "get_client_details",
            "get_client_stats",
            "search_knowledge_base",
        }

        if tool_name in read_tools:
            return BulkheadConfig(
                max_concurrent_executions=10,  # Higher concurrency for reads
                acquisition_timeout_seconds=15.0,  # Longer timeout
            )

        # Write operations - lower concurrency for safety
        write_tools = {"create_invoice", "update_client", "delete_invoice"}

        if tool_name in write_tools:
            return BulkheadConfig(
                max_concurrent_executions=2,  # Lower concurrency for writes
                acquisition_timeout_seconds=5.0,  # Shorter timeout
            )

        # Default configuration for other tools
        return BulkheadConfig()

    def _get_resilience_config(self, tool_name: str) -> CircuitBreakerConfig:
        """
        Get resilience configuration based on tool characteristics.

        Different policies for different tool types:
        - Read operations: more lenient (higher failure threshold, faster recovery)
        - Write operations: stricter (lower failure threshold, longer recovery)

        Args:
            tool_name: Name of the tool

        Returns:
            CircuitBreakerConfig for the tool
        """
        # Read operations - more lenient
        read_tools = {
            "search_invoices",
            "get_invoice_details",
            "get_invoice_stats",
            "search_clients",
            "get_client_details",
            "get_client_stats",
            "search_knowledge_base",
        }

        if tool_name in read_tools:
            return CircuitBreakerConfig(
                failure_threshold=10,  # Higher tolerance for read ops
                success_threshold=3,  # Need more successes to close
                timeout_seconds=30,  # Faster recovery
                half_open_max_calls=5,  # More calls in half-open
            )

        # Write operations - stricter
        write_tools = {"create_invoice", "update_client", "delete_invoice"}

        if tool_name in write_tools:
            return CircuitBreakerConfig(
                failure_threshold=3,  # Lower tolerance for write ops
                success_threshold=1,  # Single success closes circuit
                timeout_seconds=120,  # Longer recovery time
                half_open_max_calls=2,  # Fewer calls in half-open
            )

        # Default configuration for other tools
        return CircuitBreakerConfig()

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
        """
        Get statistics for all circuit breakers.

        Returns:
            Dictionary mapping tool names to circuit breaker stats
        """
        stats = {}
        for tool_name, breaker in self._circuit_breakers.items():
            stats[tool_name] = {
                "state": breaker.state.state.value,
                "failure_count": breaker.state.failure_count,
                "success_count": breaker.state.success_count,
                "last_failure_time": (
                    breaker.state.last_failure_time.isoformat()
                    if breaker.state.last_failure_time
                    else None
                ),
                "last_state_change": breaker.state.last_state_change.isoformat(),
            }
        return stats

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
        confirm: bool = True,
    ) -> ToolResult:
        """
        Execute a tool by name with caching and metrics.

        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters
            confirm: Skip confirmation if False

        Returns:
            ToolResult with execution outcome
        """
        # Get tool
        tool = self.get_tool(tool_name)

        if not tool:
            logger.error("tool_not_found", name=tool_name)
            result = ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found",
                tool_name=tool_name,
            )
            # Record metrics even for failures
            metrics = self._get_metrics()
            if metrics:
                metrics.record_execution(result)
            return result

        if not tool.enabled:
            logger.error("tool_disabled", name=tool_name)
            result = ToolResult(
                success=False,
                error=f"Tool '{tool_name}' is disabled",
                tool_name=tool_name,
            )
            metrics = self._get_metrics()
            if metrics:
                metrics.record_execution(result)
            return result

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
            metrics = self._get_metrics()
            if metrics:
                metrics.record_execution(result)
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
            metrics = self._get_metrics()
            if metrics:
                metrics.record_execution(result)
            return result

        # Check bulkhead (concurrency limiting) (Phase 3)
        bulkhead_semaphore = self.get_bulkhead_semaphore(tool_name)
        bulkhead_config = self._get_bulkhead_config(tool_name)

        try:
            # Try to acquire semaphore with timeout
            await asyncio.wait_for(
                bulkhead_semaphore.acquire(), timeout=bulkhead_config.acquisition_timeout_seconds
            )
        except TimeoutError:
            logger.warning("tool_bulkhead_limit_exceeded", name=tool_name)
            result = ToolResult(
                success=False,
                error=f"Tool '{tool_name}' concurrency limit exceeded. Please wait for other executions to complete.",
                tool_name=tool_name,
                error_type="bulkhead_limit_exceeded",
            )
            # Record bulkhead state in result
            # TODO: Implement proper queue length tracking for bulkhead
            result.bulkhead_queue_length = 0
            metrics = self._get_metrics()
            if metrics:
                metrics.record_execution(result)
            return result

        # Check confirmation requirement
        if tool.requires_confirmation and confirm:
            # In a real implementation, this would ask the user
            # For now, we'll just log it
            logger.info(
                "tool_requires_confirmation",
                name=tool_name,
                parameters=parameters,
            )

        # Try cache first for read operations
        cache = self._get_cache()
        if cache and cache.is_cacheable(tool_name):
            cached_result = await cache.get_cached_result(tool_name, parameters)
            if cached_result:
                logger.info("tool_cache_hit", name=tool_name)
                # Record metrics for cache hit
                metrics = self._get_metrics()
                if metrics:
                    metrics.record_execution(cached_result)
                return cached_result

        try:
            # Execute tool
            logger.info(
                "tool_executing",
                name=tool_name,
                parameters=parameters,
            )

            result = await tool.execute(**parameters)

            # Record circuit breaker success/failure (Phase 3)
            if result.success:
                circuit_breaker.record_success()
            else:
                circuit_breaker.record_failure()

            # Add circuit breaker state to result
            result.circuit_breaker_state = circuit_breaker.state.state.value

            # Add bulkhead state to result
            # TODO: Implement proper queue length tracking for bulkhead
            result.bulkhead_queue_length = 0

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

            # Record metrics
            metrics = self._get_metrics()
            if metrics:
                metrics.record_execution(result)

            return result
        finally:
            # Always release the bulkhead semaphore
            bulkhead_semaphore.release()

    def get_stats(self) -> dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with stats
        """
        circuit_breaker_stats = self.get_circuit_breaker_stats()

        return {
            "total_tools": len(self._tools),
            "enabled_tools": len([t for t in self._tools.values() if t.enabled]),
            "categories": len(self._categories),
            "tools_by_category": {cat: len(tools) for cat, tools in self._categories.items()},
            "circuit_breakers": {
                "total": len(self._circuit_breakers),
                "by_state": {
                    "closed": len(
                        [
                            cb
                            for cb in self._circuit_breakers.values()
                            if cb.state.state.value == "closed"
                        ]
                    ),
                    "open": len(
                        [
                            cb
                            for cb in self._circuit_breakers.values()
                            if cb.state.state.value == "open"
                        ]
                    ),
                    "half_open": len(
                        [
                            cb
                            for cb in self._circuit_breakers.values()
                            if cb.state.state.value == "half_open"
                        ]
                    ),
                },
                "details": circuit_breaker_stats,
            },
        }


# Global registry instance
_global_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.

    Returns:
        Global ToolRegistry
    """
    global _global_registry

    if _global_registry is None:
        _global_registry = ToolRegistry()

        # Register default tools
        _register_default_tools(_global_registry)

    return _global_registry


def _register_default_tools(registry: ToolRegistry) -> None:
    """
    Register default tools on first use.

    Args:
        registry: Registry to populate
    """
    # Import and register tools
    try:
        from openfatture.ai.tools import client_tools, invoice_tools, knowledge_tools

        # Register invoice tools
        for tool in invoice_tools.get_invoice_tools():
            registry.register(tool)

        # Register client tools
        for tool in client_tools.get_client_tools():
            registry.register(tool)

        # Register knowledge tools
        for tool in knowledge_tools.get_knowledge_tools():
            registry.register(tool)

        logger.info("default_tools_registered")

    except ImportError as e:
        logger.warning(
            "could_not_register_default_tools",
            error=str(e),
            message="Tools will be registered on demand",
        )
