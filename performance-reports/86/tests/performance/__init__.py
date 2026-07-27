"""Performance testing utilities for OpenFatture.

This module provides tools for benchmarking and profiling:
- Performance profiler decorator
- Metrics collector
- Dataset generators
- Report generation

Usage:
    from tests.performance.utils import profile_function, PerformanceMetrics
    from tests.performance.fixtures import generate_invoices

    @profile_function
    async def my_function():
        pass
"""
