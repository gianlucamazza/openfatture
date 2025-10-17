"""Performance testing utilities.

Provides profiling, metrics collection, and analysis tools for performance tests.
"""

import asyncio
import functools
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from structlog import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a function or operation.

    Attributes:
        name: Operation name
        iterations: Number of iterations
        latencies_ms: List of latency measurements in milliseconds
        memory_peak_mb: Peak memory usage in MB
        throughput: Operations per second
    """

    name: str
    iterations: int
    latencies_ms: list[float] = field(default_factory=list)
    memory_peak_mb: float = 0.0
    throughput: float = 0.0

    @property
    def mean_latency_ms(self) -> float:
        """Mean latency in milliseconds."""
        return float(np.mean(self.latencies_ms)) if self.latencies_ms else 0.0

    @property
    def median_latency_ms(self) -> float:
        """Median latency (p50) in milliseconds."""
        return float(np.median(self.latencies_ms)) if self.latencies_ms else 0.0

    @property
    def p95_latency_ms(self) -> float:
        """95th percentile latency in milliseconds."""
        return float(np.percentile(self.latencies_ms, 95)) if self.latencies_ms else 0.0

    @property
    def p99_latency_ms(self) -> float:
        """99th percentile latency in milliseconds."""
        return float(np.percentile(self.latencies_ms, 99)) if self.latencies_ms else 0.0

    @property
    def min_latency_ms(self) -> float:
        """Minimum latency in milliseconds."""
        return float(np.min(self.latencies_ms)) if self.latencies_ms else 0.0

    @property
    def max_latency_ms(self) -> float:
        """Maximum latency in milliseconds."""
        return float(np.max(self.latencies_ms)) if self.latencies_ms else 0.0

    @property
    def std_latency_ms(self) -> float:
        """Standard deviation of latency in milliseconds."""
        return float(np.std(self.latencies_ms)) if self.latencies_ms else 0.0

    def summary(self) -> dict[str, Any]:
        """Get metrics summary dictionary."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "mean_ms": round(self.mean_latency_ms, 3),
            "median_ms": round(self.median_latency_ms, 3),
            "p95_ms": round(self.p95_latency_ms, 3),
            "p99_ms": round(self.p99_latency_ms, 3),
            "min_ms": round(self.min_latency_ms, 3),
            "max_ms": round(self.max_latency_ms, 3),
            "std_ms": round(self.std_latency_ms, 3),
            "throughput_ops_sec": round(self.throughput, 2),
            "memory_peak_mb": round(self.memory_peak_mb, 2),
        }

    def print_summary(self) -> None:
        """Print formatted metrics summary."""
        print(f"\n{'='*70}")
        print(f"Performance Metrics: {self.name}")
        print(f"{'='*70}")
        print(f"Iterations:      {self.iterations}")
        print(f"Mean latency:    {self.mean_latency_ms:.3f} ms")
        print(f"Median (p50):    {self.median_latency_ms:.3f} ms")
        print(f"p95:             {self.p95_latency_ms:.3f} ms")
        print(f"p99:             {self.p99_latency_ms:.3f} ms")
        print(f"Min:             {self.min_latency_ms:.3f} ms")
        print(f"Max:             {self.max_latency_ms:.3f} ms")
        print(f"Std dev:         {self.std_latency_ms:.3f} ms")
        print(f"Throughput:      {self.throughput:.2f} ops/sec")
        print(f"Peak memory:     {self.memory_peak_mb:.2f} MB")
        print(f"{'='*70}\n")


class PerformanceProfiler:
    """Context manager for profiling function performance.

    Measures execution time and peak memory usage.

    Example:
        >>> with PerformanceProfiler("my_operation") as profiler:
        ...     # do work
        ...     pass
        >>> print(profiler.metrics.mean_latency_ms)
    """

    def __init__(self, name: str, iterations: int = 1, track_memory: bool = True):
        """Initialize profiler.

        Args:
            name: Operation name for metrics
            iterations: Expected number of iterations
            track_memory: Whether to track memory usage
        """
        self.name = name
        self.iterations = iterations
        self.track_memory = track_memory
        self.metrics = PerformanceMetrics(name=name, iterations=iterations)
        self._start_time = 0.0
        self._memory_start = 0
        self._memory_peak = 0

    def __enter__(self) -> "PerformanceProfiler":
        """Start profiling."""
        self._start_time = time.perf_counter()

        if self.track_memory:
            tracemalloc.start()
            self._memory_start, _ = tracemalloc.get_traced_memory()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop profiling and collect metrics."""
        end_time = time.perf_counter()
        latency_ms = (end_time - self._start_time) * 1000

        self.metrics.latencies_ms.append(latency_ms)

        # Calculate throughput
        if latency_ms > 0:
            self.metrics.throughput = (self.iterations / latency_ms) * 1000

        if self.track_memory:
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            self.metrics.memory_peak_mb = (peak - self._memory_start) / (1024 * 1024)

        logger.info(
            "performance_measurement",
            name=self.name,
            latency_ms=round(latency_ms, 3),
            memory_mb=round(self.metrics.memory_peak_mb, 2),
        )


def profile_function(func: Callable | None = None, *, name: str | None = None, iterations: int = 1):
    """Decorator for profiling function performance.

    Can be used with or without arguments:
        @profile_function
        def my_func():
            pass

        @profile_function(name="Custom Name", iterations=100)
        async def my_async_func():
            pass

    Args:
        func: Function to profile (when used without arguments)
        name: Custom name for metrics (default: function name)
        iterations: Number of iterations to run

    Returns:
        Decorated function that profiles performance
    """

    def decorator(fn: Callable) -> Callable:
        profiler_name = name or fn.__name__

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            with PerformanceProfiler(profiler_name, iterations=iterations) as profiler:
                result = await fn(*args, **kwargs)

            # Attach metrics to result if it's a dict
            if isinstance(result, dict):
                result["_performance_metrics"] = profiler.metrics.summary()

            return result

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            with PerformanceProfiler(profiler_name, iterations=iterations) as profiler:
                result = fn(*args, **kwargs)

            # Attach metrics to result if it's a dict
            if isinstance(result, dict):
                result["_performance_metrics"] = profiler.metrics.summary()

            return result

        return async_wrapper if asyncio.iscoroutinefunction(fn) else sync_wrapper

    # Handle decorator with or without arguments
    if func is None:
        return decorator
    else:
        return decorator(func)


async def measure_async_function(
    func: Callable, *args, iterations: int = 10, warmup: int = 2, **kwargs
) -> PerformanceMetrics:
    """Measure performance of an async function over multiple iterations.

    Args:
        func: Async function to measure
        *args: Positional arguments for function
        iterations: Number of measurement iterations
        warmup: Number of warmup iterations (not measured)
        **kwargs: Keyword arguments for function

    Returns:
        PerformanceMetrics with aggregated results

    Example:
        >>> async def my_func(x):
        ...     return x * 2
        >>> metrics = await measure_async_function(my_func, 42, iterations=100)
        >>> print(metrics.mean_latency_ms)
    """
    metrics = PerformanceMetrics(name=func.__name__, iterations=iterations)

    # Warmup runs
    for _ in range(warmup):
        await func(*args, **kwargs)

    # Start memory tracking
    tracemalloc.start()
    memory_start, _ = tracemalloc.get_traced_memory()

    # Measurement runs
    for _ in range(iterations):
        start = time.perf_counter()
        await func(*args, **kwargs)
        end = time.perf_counter()

        latency_ms = (end - start) * 1000
        metrics.latencies_ms.append(latency_ms)

    # Memory tracking
    _, memory_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    metrics.memory_peak_mb = (memory_peak - memory_start) / (1024 * 1024)

    # Calculate throughput
    total_time_s = sum(metrics.latencies_ms) / 1000
    metrics.throughput = iterations / total_time_s if total_time_s > 0 else 0.0

    logger.info(
        "async_function_measured",
        function=func.__name__,
        iterations=iterations,
        mean_latency_ms=round(metrics.mean_latency_ms, 3),
        p95_latency_ms=round(metrics.p95_latency_ms, 3),
        throughput=round(metrics.throughput, 2),
    )

    return metrics


def measure_sync_function(
    func: Callable, *args, iterations: int = 10, warmup: int = 2, **kwargs
) -> PerformanceMetrics:
    """Measure performance of a sync function over multiple iterations.

    Args:
        func: Sync function to measure
        *args: Positional arguments for function
        iterations: Number of measurement iterations
        warmup: Number of warmup iterations (not measured)
        **kwargs: Keyword arguments for function

    Returns:
        PerformanceMetrics with aggregated results
    """
    metrics = PerformanceMetrics(name=func.__name__, iterations=iterations)

    # Warmup runs
    for _ in range(warmup):
        func(*args, **kwargs)

    # Start memory tracking
    tracemalloc.start()
    memory_start, _ = tracemalloc.get_traced_memory()

    # Measurement runs
    for _ in range(iterations):
        start = time.perf_counter()
        func(*args, **kwargs)
        end = time.perf_counter()

        latency_ms = (end - start) * 1000
        metrics.latencies_ms.append(latency_ms)

    # Memory tracking
    _, memory_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    metrics.memory_peak_mb = (memory_peak - memory_start) / (1024 * 1024)

    # Calculate throughput
    total_time_s = sum(metrics.latencies_ms) / 1000
    metrics.throughput = iterations / total_time_s if total_time_s > 0 else 0.0

    logger.info(
        "sync_function_measured",
        function=func.__name__,
        iterations=iterations,
        mean_latency_ms=round(metrics.mean_latency_ms, 3),
        p95_latency_ms=round(metrics.p95_latency_ms, 3),
        throughput=round(metrics.throughput, 2),
    )

    return metrics


def assert_performance_target(
    metrics: PerformanceMetrics, target_ms: float, percentile: str = "mean"
) -> None:
    """Assert that performance meets target latency.

    Args:
        metrics: Performance metrics to check
        target_ms: Target latency in milliseconds
        percentile: Which percentile to check ("mean", "median", "p95", "p99")

    Raises:
        AssertionError: If performance does not meet target

    Example:
        >>> metrics = PerformanceMetrics(name="test", iterations=10)
        >>> metrics.latencies_ms = [10.0, 15.0, 12.0]
        >>> assert_performance_target(metrics, target_ms=20.0, percentile="p95")
    """
    percentile_map = {
        "mean": metrics.mean_latency_ms,
        "median": metrics.median_latency_ms,
        "p50": metrics.median_latency_ms,
        "p95": metrics.p95_latency_ms,
        "p99": metrics.p99_latency_ms,
    }

    actual_latency = percentile_map.get(percentile)
    if actual_latency is None:
        raise ValueError(f"Invalid percentile: {percentile}")

    assert (
        actual_latency <= target_ms
    ), f"{metrics.name} {percentile} latency {actual_latency:.3f}ms exceeds target {target_ms}ms"

    logger.info(
        "performance_target_met",
        name=metrics.name,
        percentile=percentile,
        actual_ms=round(actual_latency, 3),
        target_ms=target_ms,
    )
