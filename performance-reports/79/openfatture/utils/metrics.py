"""
Structured metrics collection for monitoring and observability.

Provides comprehensive metrics collection with support for:
- Performance monitoring
- Error tracking
- Usage statistics
- Custom metrics
- Export capabilities for dashboards
"""

import json
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MetricPoint:
    """A single metric measurement point."""

    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricSeries:
    """Time series data for a metric."""

    name: str
    points: list[MetricPoint] = field(default_factory=list)
    retention_hours: int = 24

    def add_point(
        self,
        value: float,
        tags: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a new measurement point."""
        point = MetricPoint(name=self.name, value=value, tags=tags or {}, metadata=metadata or {})
        self.points.append(point)

        # Cleanup old points
        cutoff = datetime.now() - timedelta(hours=self.retention_hours)
        self.points = [p for p in self.points if p.timestamp > cutoff]

    def get_stats(self, hours: int = 1) -> dict[str, Any]:
        """Get statistics for the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_points = [p for p in self.points if p.timestamp > cutoff]

        if not recent_points:
            return {"count": 0, "avg": 0, "min": 0, "max": 0}

        values = [p.value for p in recent_points]
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "latest": values[-1] if values else 0,
        }


class MetricsCollector:
    """
    Thread-safe metrics collector for application monitoring.

    Features:
    - Time-series data collection
    - Automatic cleanup of old data
    - Thread-safe operations
    - Export capabilities (JSON, Prometheus format)
    - Performance monitoring helpers
    """

    def __init__(self) -> None:
        self._series: dict[str, MetricSeries] = defaultdict(lambda: MetricSeries("default"))
        self._lock = threading.RLock()
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}

        logger.info("metrics_collector_initialized")

    def record_metric(
        self,
        name: str,
        value: float,
        tags: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record a metric measurement."""
        with self._lock:
            if name not in self._series:
                self._series[name] = MetricSeries(name)
            self._series[name].add_point(value, tags, metadata)

    def increment_counter(
        self, name: str, amount: int = 1, tags: dict[str, str] | None = None
    ) -> None:
        """Increment a counter metric."""
        with self._lock:
            self._counters[name] += amount
            self.record_metric(f"{name}_total", self._counters[name], tags)

    def set_gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Set a gauge metric value."""
        with self._lock:
            self._gauges[name] = value
            self.record_metric(name, value, tags)

    def record_timing(
        self, name: str, duration_ms: float, tags: dict[str, str] | None = None
    ) -> None:
        """Record a timing measurement."""
        self.record_metric(f"{name}_duration_ms", duration_ms, tags)

    def record_error(
        self, error_type: str, error_message: str, context: dict[str, Any] | None = None
    ) -> None:
        """Record an error occurrence."""
        self.increment_counter(f"errors_{error_type}")
        logger.warning(
            "error_recorded",
            error_type=error_type,
            error_message=error_message[:200],
            context=context,
        )

    def get_metric_stats(self, name: str, hours: int = 1) -> dict[str, Any]:
        """Get statistics for a metric."""
        with self._lock:
            if name in self._series:
                return self._series[name].get_stats(hours)
            return {"count": 0, "avg": 0, "min": 0, "max": 0}

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all current metrics data."""
        with self._lock:
            result: dict[str, Any] = {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "series_stats": {},
            }

            for name, series in self._series.items():
                result["series_stats"][name] = series.get_stats()

            return result

    def export_json(self) -> str:
        """Export all metrics as JSON."""
        data = self.get_all_metrics()
        data["export_timestamp"] = datetime.now().isoformat()
        return json.dumps(data, indent=2, default=str)

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        timestamp_ms = int(time.time() * 1000)

        with self._lock:
            # Counters
            for name, value in self._counters.items():
                lines.append(f"# HELP {name} Counter metric")
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name}_total {value} {timestamp_ms}")

            # Gauges
            for name, gauge_value in self._gauges.items():
                lines.append(f"# HELP {name} Gauge metric")
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {gauge_value} {timestamp_ms}")

            # Series (latest values)
            for name, series in self._series.items():
                if series.points:
                    latest = series.points[-1]
                    lines.append(f"# HELP {name} Time series metric")
                    lines.append(f"# TYPE {name} gauge")
                    lines.append(f"{name} {latest.value} {timestamp_ms}")

        return "\n".join(lines)

    def cleanup_old_data(self, max_age_hours: int = 48) -> int:
        """Clean up old metric data. Returns number of points removed."""
        with self._lock:
            removed_count = 0
            cutoff = datetime.now() - timedelta(hours=max_age_hours)

            for series in self._series.values():
                old_count = len(series.points)
                series.points = [p for p in series.points if p.timestamp > cutoff]
                removed_count += old_count - len(series.points)

            logger.info("metrics_cleanup_completed", removed_points=removed_count)
            return removed_count


# Global metrics collector instance
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


class MetricsTimer:
    """Context manager for timing operations."""

    def __init__(self, operation_name: str, tags: dict[str, str] | None = None):
        self.operation_name = operation_name
        self.tags = tags or {}
        self.start_time: float | None = None
        self.collector = get_metrics_collector()

    def __enter__(self) -> "MetricsTimer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.start_time is not None:
            duration_ms = (time.perf_counter() - self.start_time) * 1000
            self.collector.record_timing(self.operation_name, duration_ms, self.tags)

            if exc_type is not None:
                # Record error
                self.collector.record_error(
                    "operation_failed",
                    f"{self.operation_name} failed: {str(exc_val)}",
                    {"operation": self.operation_name, "error_type": exc_type.__name__},
                )


# Convenience functions for common metrics
def record_ai_request(
    provider: str, model: str, tokens: int, duration_ms: float, success: bool
) -> None:
    """Record AI API request metrics."""
    collector = get_metrics_collector()
    collector.record_metric(
        "ai_requests_total", 1, {"provider": provider, "model": model, "success": str(success)}
    )
    collector.record_timing(
        "ai_request_duration", duration_ms, {"provider": provider, "model": model}
    )
    collector.record_metric("ai_tokens_used", tokens, {"provider": provider, "model": model})


def record_invoice_operation(operation: str, duration_ms: float, success: bool) -> None:
    """Record invoice operation metrics."""
    collector = get_metrics_collector()
    collector.record_metric(
        "invoice_operations_total", 1, {"operation": operation, "success": str(success)}
    )
    collector.record_timing("invoice_operation_duration", duration_ms, {"operation": operation})


def record_payment_reconciliation(
    duration_ms: float, transactions_processed: int, matches_found: int
) -> None:
    """Record payment reconciliation metrics."""
    collector = get_metrics_collector()
    collector.record_timing("payment_reconciliation_duration", duration_ms)
    collector.record_metric("payment_transactions_processed", transactions_processed)
    collector.record_metric("payment_matches_found", matches_found)
