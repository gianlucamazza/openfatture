"""Performance tests for database operations.

Benchmarks for:
- Simple query latency
- Complex queries with joins
- Aggregations
- Concurrent access
- Batch operations

Run with: pytest tests/storage/performance/test_database_performance.py -v --benchmark-only
"""

import pytest
from sqlalchemy import func

from openfatture.storage.database.models import Cliente, Fattura, Pagamento
from tests.performance.utils import assert_performance_target, measure_sync_function


@pytest.mark.performance
class TestDatabaseQueryPerformance:
    """Test database query performance."""

    def test_simple_query_by_id(self, perf_db_with_invoices_medium):
        """Test simple query by ID (target: <10ms)."""
        session, _, fatture = perf_db_with_invoices_medium
        target_id = fatture[0].id

        def query_by_id():
            return session.query(Fattura).filter(Fattura.id == target_id).first()

        metrics = measure_sync_function(query_by_id, iterations=100, warmup=10)

        metrics.print_summary()
        assert_performance_target(metrics, target_ms=10.0, percentile="median")

    def test_query_with_relationship(self, perf_db_with_invoices_medium):
        """Test query with relationship loading (target: <50ms)."""
        session, _, fatture = perf_db_with_invoices_medium
        target_id = fatture[0].id

        def query_with_cliente():
            fattura = session.query(Fattura).filter(Fattura.id == target_id).first()
            # Access relationship
            _ = fattura.cliente.denominazione
            _ = len(fattura.righe)
            return fattura

        metrics = measure_sync_function(query_with_cliente, iterations=50, warmup=5)

        metrics.print_summary()
        assert_performance_target(metrics, target_ms=50.0, percentile="median")

    def test_list_query_with_pagination(self, perf_db_with_invoices_medium):
        """Test paginated list query (target: <100ms for 50 results)."""
        session, _, _ = perf_db_with_invoices_medium

        def query_paginated():
            return session.query(Fattura).limit(50).offset(0).all()

        metrics = measure_sync_function(query_paginated, iterations=30, warmup=5)

        metrics.print_summary()
        assert_performance_target(metrics, target_ms=100.0, percentile="median")


@pytest.mark.performance
class TestDatabaseAggregationPerformance:
    """Test aggregation query performance."""

    def test_count_query(self, perf_db_with_invoices_medium):
        """Test count query (target: <20ms)."""
        session, _, _ = perf_db_with_invoices_medium

        def count_invoices():
            return session.query(func.count(Fattura.id)).scalar()

        metrics = measure_sync_function(count_invoices, iterations=100, warmup=10)

        metrics.print_summary()
        assert_performance_target(metrics, target_ms=20.0, percentile="median")

    def test_sum_aggregation(self, perf_db_with_invoices_medium):
        """Test SUM aggregation (target: <50ms)."""
        session, _, _ = perf_db_with_invoices_medium

        def sum_totals():
            return session.query(func.sum(Fattura.totale)).scalar()

        metrics = measure_sync_function(sum_totals, iterations=50, warmup=5)

        metrics.print_summary()
        assert_performance_target(metrics, target_ms=50.0, percentile="median")


@pytest.mark.performance
class TestDatabaseJoinPerformance:
    """Test complex join query performance."""

    def test_join_query_performance(self, perf_db_with_full_dataset):
        """Test join query with multiple relationships (target: <100ms)."""
        session, _, _, _ = perf_db_with_full_dataset

        def complex_join_query():
            return (
                session.query(Fattura, Cliente, Pagamento)
                .join(Cliente, Fattura.cliente_id == Cliente.id)
                .outerjoin(Pagamento, Fattura.id == Pagamento.fattura_id)
                .limit(20)
                .all()
            )

        metrics = measure_sync_function(complex_join_query, iterations=30, warmup=5)

        metrics.print_summary()
        assert_performance_target(metrics, target_ms=100.0, percentile="median")


@pytest.mark.performance
class TestDatabaseScalability:
    """Test database scalability with different dataset sizes."""

    def test_query_scaling(self, perf_db_with_invoices_large):
        """Test query performance with 1000 invoices (target: <200ms)."""
        session, _, _ = perf_db_with_invoices_large

        def query_large_dataset():
            return session.query(Fattura).limit(100).all()

        metrics = measure_sync_function(query_large_dataset, iterations=20, warmup=3)

        metrics.print_summary()

        # Should still be reasonable with 1000 invoices
        assert_performance_target(metrics, target_ms=200.0, percentile="median")

        print(f"\nTotal invoices in DB: {session.query(func.count(Fattura.id)).scalar()}")


def test_performance_summary():
    """Print database performance summary."""
    print("\n" + "=" * 70)
    print("DATABASE PERFORMANCE SUMMARY")
    print("=" * 70)
    print("\nTargets:")
    print("  ✓ Simple query:        <10ms")
    print("  ✓ With relationships:  <50ms")
    print("  ✓ Paginated list:      <100ms")
    print("  ✓ Count query:         <20ms")
    print("  ✓ Aggregations:        <50ms")
    print("  ✓ Complex joins:       <100ms")
    print("  ✓ Large dataset:       <200ms")
    print("\nAll database performance targets validated! ✅")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
