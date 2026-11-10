"""Tool execution metrics collection and monitoring.

This module provides comprehensive metrics collection for tool execution,
including performance monitoring, error tracking, and usage statistics.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from openfatture.ai.tools.models import ToolResult
from openfatture.platform.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ToolExecutionMetrics:
    """Metrics for a single tool execution."""

    tool_name: str
    execution_time: float
    success: bool
    error_type: str | None = None
    retries: int = 0
    cache_hit: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ToolStats:
    """Aggregated statistics for a tool."""

    calls: int = 0
    successes: int = 0
    failures: int = 0
    total_execution_time: float = 0.0
    total_retries: int = 0
    cache_hits: int = 0
    error_counts: dict[str, int] = field(default_factory=dict)
    last_execution: datetime | None = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        return self.successes / self.calls if self.calls > 0 else 0.0

    @property
    def average_execution_time(self) -> float:
        """Calculate average execution time."""
        return self.total_execution_time / self.calls if self.calls > 0 else 0.0

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        return self.cache_hits / self.calls if self.calls > 0 else 0.0


class ToolMetricsCollector:
    """
    Collects and aggregates metrics for tool execution.

    Provides comprehensive monitoring of tool performance, reliability,
    and usage patterns. Integrates with structured logging for observability.

    Features:
    - Execution time tracking
    - Success/failure rates
    - Error classification
    - Cache hit monitoring
    - Retry attempt tracking
    - Real-time statistics
    """

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self._stats: dict[str, ToolStats] = defaultdict(ToolStats)
        self._execution_history: list[ToolExecutionMetrics] = []
        self._max_history_size = 10000  # Keep last 10k executions

        logger.info("tool_metrics_collector_initialized")

    def record_execution(self, result: ToolResult) -> None:
        """
        Record a tool execution result.

        Args:
            result: ToolResult from tool execution
        """
        # Create execution metrics
        metrics = ToolExecutionMetrics(
            tool_name=result.tool_name,
            execution_time=result.execution_time or 0.0,
            success=result.success,
            error_type=result.error_type,
            retries=result.retries,
            cache_hit=result.cache_hit,
        )

        # Update aggregated stats
        stats = self._stats[result.tool_name]
        stats.calls += 1
        stats.last_execution = metrics.timestamp

        if result.success:
            stats.successes += 1
        else:
            stats.failures += 1
            if result.error_type:
                stats.error_counts[result.error_type] = (
                    stats.error_counts.get(result.error_type, 0) + 1
                )

        stats.total_execution_time += metrics.execution_time
        stats.total_retries += metrics.retries

        if result.cache_hit:
            stats.cache_hits += 1

        # Add to execution history
        self._execution_history.append(metrics)
        if len(self._execution_history) > self._max_history_size:
            self._execution_history.pop(0)

        # Log execution
        logger.info(
            "tool_execution_recorded",
            tool_name=result.tool_name,
            success=result.success,
            execution_time=result.execution_time,
            retries=result.retries,
            cache_hit=result.cache_hit,
            error_type=result.error_type,
        )

    def get_all_stats(self) -> dict[str, ToolStats]:
        """
        Get statistics for all tools.

        Returns:
            Dictionary mapping tool names to their stats
        """
        return dict(self._stats)


# Global metrics collector instance
_metrics_collector: ToolMetricsCollector | None = None


def get_tool_metrics_collector() -> ToolMetricsCollector:
    """
    Get the global tool metrics collector instance.

    Returns:
        Global ToolMetricsCollector instance
    """
    global _metrics_collector

    if _metrics_collector is None:
        _metrics_collector = ToolMetricsCollector()

    return _metrics_collector
