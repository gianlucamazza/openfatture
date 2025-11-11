"""Performance benchmarks for CompositeMatcher parallel execution.

PHASE 1 Enhancement: Verify 2-4x speedup from asyncio.gather() parallelization.

Run with: pytest tests/payment/matchers/test_composite_matcher_benchmark.py --benchmark-only
"""

import asyncio
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from openfatture.payment.domain.enums import MatchType
from openfatture.payment.domain.value_objects import MatchResult
from openfatture.payment.matchers.composite import CompositeMatcher

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_transaction():
    """Create mock transaction for benchmarking."""
    transaction = Mock()
    transaction.id = "bench-tx-001"
    transaction.amount = Decimal("1000.00")
    transaction.description = "Test payment for benchmarking"
    transaction.date = date.today()
    return transaction


@pytest.fixture
def mock_payments():
    """Create mock payment candidates (realistic dataset)."""
    payments = []
    for i in range(100):  # 100 candidate payments
        payment = Mock()
        payment.id = i + 1
        payment.importo_totale = Decimal("1000.00") + Decimal(i)
        payment.data_scadenza = date.today()
        payments.append(payment)
    return payments


def create_async_strategy_with_delay(
    payment_id: int, confidence: float, delay_ms: int = 10
) -> AsyncMock:
    """Create async strategy that simulates realistic I/O delay."""

    async def match_with_delay(transaction, payments):
        # Simulate database query or computation time
        await asyncio.sleep(delay_ms / 1000.0)
        return [
            MatchResult(
                payment=Mock(id=payment_id),
                confidence=Decimal(str(confidence)),
                match_type=MatchType.COMPOSITE,
                match_reason=f"Strategy {payment_id}",
            )
        ]

    strategy = AsyncMock()
    strategy.match.side_effect = match_with_delay
    return strategy


class TestCompositeMatcherPerformance:
    """Benchmarks for CompositeMatcher parallel execution."""

    @pytest.mark.benchmark(group="parallel-execution")
    def test_benchmark_parallel_4_strategies(self, benchmark, mock_transaction, mock_payments):
        """Benchmark CompositeMatcher with 4 strategies running in parallel.

        Target: Complete in <50ms with 10ms simulated I/O per strategy.
        Sequential: 4 * 10ms = 40ms
        Parallel: max(10ms, 10ms, 10ms, 10ms) = ~10-15ms
        Expected speedup: ~3-4x
        """
        # Create 4 async strategies with simulated I/O
        strategies = [
            create_async_strategy_with_delay(i + 1, 0.80 - i * 0.1, delay_ms=10) for i in range(4)
        ]

        composite = CompositeMatcher(strategies=strategies)

        # Benchmark the match operation (use asyncio.run since not async test)
        result = benchmark.pedantic(
            lambda: asyncio.run(composite.match(mock_transaction, mock_payments)),
            iterations=10,
            rounds=5,
        )

        # Verify results are correct
        assert len(result) > 0
        # Should complete much faster than sequential (40ms)
        # Parallel should be ~10-15ms
        assert benchmark.stats.stats.mean < 0.030  # 30ms threshold

    @pytest.mark.benchmark(group="parallel-execution")
    def test_benchmark_parallel_8_strategies(self, benchmark, mock_transaction, mock_payments):
        """Benchmark with 8 strategies to verify scaling.

        Sequential: 8 * 10ms = 80ms
        Parallel: max(...) = ~10-15ms
        Expected speedup: ~6-8x
        """
        strategies = [
            create_async_strategy_with_delay(i + 1, 0.90 - i * 0.05, delay_ms=10) for i in range(8)
        ]

        composite = CompositeMatcher(strategies=strategies)

        result = benchmark.pedantic(
            lambda: asyncio.run(composite.match(mock_transaction, mock_payments)),
            iterations=10,
            rounds=5,
        )

        assert len(result) > 0
        # Should still complete in similar time (parallel)
        assert benchmark.stats.stats.mean < 0.030

    @pytest.mark.benchmark(group="parallel-execution")
    def test_benchmark_parallel_vs_sequential_simulation(
        self, benchmark, mock_transaction, mock_payments
    ):
        """Compare parallel execution vs sequential simulation.

        This test simulates what the old sequential code would have done.
        """
        strategies = [create_async_strategy_with_delay(i + 1, 0.85, delay_ms=10) for i in range(4)]

        composite = CompositeMatcher(strategies=strategies)

        # Benchmark NEW parallel implementation
        result_parallel = benchmark.pedantic(
            lambda: asyncio.run(composite.match(mock_transaction, mock_payments)),
            iterations=10,
            rounds=5,
        )

        # Measure sequential for comparison (run once, not benchmarked)
        async def sequential_simulation():
            """Simulate old sequential execution."""
            results = []
            for strategy in strategies:
                result = await strategy.match(mock_transaction, mock_payments)
                results.extend(result)
            return results

        import time

        start = time.perf_counter()
        result_sequential = asyncio.run(sequential_simulation())
        sequential_time = time.perf_counter() - start

        # Print speedup for visibility
        parallel_time = benchmark.stats.stats.mean
        speedup = sequential_time / parallel_time

        print(
            f"\nSpeedup: {speedup:.2f}x "
            f"(Sequential: {sequential_time*1000:.1f}ms → "
            f"Parallel: {parallel_time*1000:.1f}ms)"
        )

        # Verify results are equivalent
        assert len(result_parallel) == len(result_sequential)

        # Assert minimum 2x speedup (conservative target)
        assert speedup >= 2.0, f"Speedup {speedup:.2f}x is below 2x target"

    @pytest.mark.benchmark(group="large-dataset")
    def test_benchmark_large_payment_dataset(self, benchmark, mock_transaction):
        """Benchmark with realistic large dataset (1000 payments)."""
        # Create 1000 candidate payments
        large_payments = []
        for i in range(1000):
            payment = Mock()
            payment.id = i + 1
            payment.importo_totale = Decimal("1000.00") + Decimal(i)
            payment.data_scadenza = date.today()
            large_payments.append(payment)

        # 4 strategies with minimal delay (pure computation)
        strategies = [create_async_strategy_with_delay(i + 1, 0.85, delay_ms=1) for i in range(4)]

        composite = CompositeMatcher(strategies=strategies)

        result = benchmark.pedantic(
            lambda: asyncio.run(composite.match(mock_transaction, large_payments)),
            iterations=5,
            rounds=3,
        )

        assert len(result) > 0
        # Should handle large dataset efficiently
        assert benchmark.stats.stats.mean < 0.100  # 100ms for 1000 payments

    @pytest.mark.benchmark(group="exception-handling")
    def test_benchmark_with_failing_strategy(self, benchmark, mock_transaction, mock_payments):
        """Benchmark performance when one strategy fails.

        Verify exception isolation doesn't significantly impact performance.
        """
        # 3 successful strategies + 1 failing
        strategies = [create_async_strategy_with_delay(i + 1, 0.85, delay_ms=10) for i in range(3)]

        # Add failing strategy
        failing_strategy = AsyncMock()
        failing_strategy.match.side_effect = ValueError("Simulated failure")
        failing_strategy.__class__.__name__ = "FailingStrategy"
        strategies.append(failing_strategy)

        composite = CompositeMatcher(strategies=strategies)

        result = benchmark.pedantic(
            lambda: asyncio.run(composite.match(mock_transaction, mock_payments)),
            iterations=10,
            rounds=5,
        )

        # Should still return results from successful strategies
        assert len(result) > 0

        # Exception handling should not significantly impact performance
        assert benchmark.stats.stats.mean < 0.030


# Configuration for pytest-benchmark
def pytest_configure(config):
    """Configure benchmark plugin."""
    config.addinivalue_line("markers", "benchmark: mark test as a performance benchmark")
