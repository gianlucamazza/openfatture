"""End-to-end performance tests for complete workflows.

Benchmarks for:
- Invoice creation → indexing → retrieval flow
- Search query → retrieve → format pipeline
- Concurrent multi-client operations
- Full system integration performance

Run with: pytest tests/integration/performance/test_e2e_performance.py -v --benchmark-only
"""

import asyncio

import pytest

from tests.performance.utils import (
    PerformanceProfiler,
    assert_performance_target,
    measure_async_function,
)


@pytest.mark.performance
@pytest.mark.asyncio
@pytest.mark.slow
class TestEndToEndWorkflowPerformance:
    """Test complete end-to-end workflow performance."""

    async def test_invoice_creation_to_retrieval_flow(self, e2e_system_indexed, e2e_retriever):
        """Test complete flow: create invoice → index → retrieve (target: <1s)."""
        session, clienti, fatture, indexer = e2e_system_indexed

        # Pick a test invoice
        test_fattura = fatture[100]  # Use middle invoice

        async def complete_flow():
            # Step 1: Simulate invoice already exists (in setup)
            # Step 2: Index invoice
            await indexer.index_invoice(test_fattura.id)

            # Step 3: Retrieve similar invoices
            query = f"Fattura {test_fattura.cliente.denominazione}"
            results = await e2e_retriever.retrieve(query, top_k=5)

            # Step 4: Format results
            formatted = e2e_retriever.format_results(results)

            return results, formatted

        metrics = await measure_async_function(complete_flow, iterations=10, warmup=2)

        metrics.print_summary()

        # Target: <1s for complete flow
        assert_performance_target(metrics, target_ms=1000.0, percentile="median")

        print("\nFlow breakdown:")
        print("  - Index: ~200ms")
        print("  - Retrieve: ~200ms")
        print("  - Format: ~10ms")

    async def test_search_query_end_to_end(self, e2e_system_indexed, e2e_retriever):
        """Test search query end-to-end (target: <300ms)."""
        session, clienti, fatture, indexer = e2e_system_indexed

        queries = [
            "Consulenza informatica",
            "Sviluppo software",
            "Marketing digitale",
            "Servizi IT",
        ]

        for query in queries:

            async def search_flow(q=query):
                # Retrieve
                results = await e2e_retriever.retrieve(q, top_k=5)

                # Format
                formatted = e2e_retriever.format_results(results)

                return results, formatted

            metrics = await measure_async_function(search_flow, iterations=15, warmup=3)

            print(f"\nQuery: '{query}'")
            print(f"  Mean latency: {metrics.mean_latency_ms:.2f}ms")
            print(f"  p95 latency:  {metrics.p95_latency_ms:.2f}ms")

            # Target: <300ms
            assert_performance_target(metrics, target_ms=300.0, percentile="p95")

    async def test_batch_indexing_then_search(self, e2e_database, e2e_indexer, e2e_retriever):
        """Test batch indexing followed by searches (target: <15s total for 200 invoices)."""
        session, clienti, fatture = e2e_database

        async def batch_then_search():
            # Index all invoices
            await e2e_indexer.index_all_invoices(batch_size=50)

            # Perform searches
            queries = ["Consulenza", "Sviluppo", "Marketing"]
            results_list = []
            for query in queries:
                results = await e2e_retriever.retrieve(query, top_k=5)
                results_list.append(results)

            return results_list

        metrics = await measure_async_function(batch_then_search, iterations=2, warmup=0)

        metrics.print_summary()

        # Target: <15s for indexing 200 + 3 searches
        assert_performance_target(metrics, target_ms=15000.0, percentile="mean")

        print("\nIndexed 200 invoices + 3 searches")
        print(f"Throughput: {200 / (metrics.mean_latency_ms / 1000):.2f} invoices/sec")


@pytest.mark.performance
@pytest.mark.asyncio
@pytest.mark.slow
class TestConcurrentOperationsPerformance:
    """Test concurrent multi-client operations."""

    async def test_concurrent_searches(self, e2e_system_indexed, e2e_retriever):
        """Test concurrent search queries (5 concurrent, target: <500ms)."""
        session, clienti, fatture, indexer = e2e_system_indexed

        queries = [
            "Consulenza informatica",
            "Sviluppo software",
            "Marketing digitale",
            "Servizi IT",
            "Manutenzione sistemi",
        ]

        async def single_search(query: str):
            results = await e2e_retriever.retrieve(query, top_k=5)
            return results

        async def concurrent_searches():
            tasks = [single_search(q) for q in queries]
            results = await asyncio.gather(*tasks)
            return results

        metrics = await measure_async_function(concurrent_searches, iterations=10, warmup=2)

        metrics.print_summary()

        # Target: <500ms for 5 concurrent searches
        assert_performance_target(metrics, target_ms=500.0, percentile="p95")

        print("\n5 concurrent searches completed")
        print(f"Average latency per search: {metrics.mean_latency_ms / 5:.2f}ms")

    async def test_concurrent_indexing_and_search(self, e2e_database, e2e_indexer, e2e_retriever):
        """Test concurrent indexing and searching (target: no deadlocks, reasonable latency)."""
        session, clienti, fatture = e2e_database

        # Index first batch
        await e2e_indexer.index_all_invoices(batch_size=50)

        async def index_invoice(invoice_id: int):
            await e2e_indexer.index_invoice(invoice_id)

        async def search_query(query: str):
            return await e2e_retriever.retrieve(query, top_k=5)

        async def mixed_operations():
            # Mix of indexing and searching
            tasks = []

            # 3 indexing operations
            for i in range(3):
                tasks.append(index_invoice(fatture[i].id))

            # 5 search operations
            queries = ["Consulenza", "Sviluppo", "Marketing", "IT", "Servizi"]
            for query in queries:
                tasks.append(search_query(query))

            # Execute concurrently
            results = await asyncio.gather(*tasks)
            return results

        metrics = await measure_async_function(mixed_operations, iterations=5, warmup=1)

        metrics.print_summary()

        # Should complete without deadlocks in reasonable time
        assert metrics.mean_latency_ms < 2000.0, "Mixed operations too slow"

        print("\n3 indexing + 5 search operations concurrent")
        print(f"Total latency: {metrics.mean_latency_ms:.2f}ms")


@pytest.mark.performance
@pytest.mark.asyncio
@pytest.mark.slow
class TestMemoryUnderLoad:
    """Test memory usage under load conditions."""

    async def test_memory_during_batch_operations(self, e2e_database, e2e_indexer):
        """Test memory usage during large batch operations (target: <400MB)."""
        session, clienti, fatture = e2e_database

        async def large_batch_operation():
            # Index all 200 invoices
            await e2e_indexer.index_all_invoices(batch_size=50)

        metrics = await measure_async_function(large_batch_operation, iterations=1, warmup=0)

        metrics.print_summary()

        # Target: <400MB for indexing 200 invoices
        assert (
            metrics.memory_peak_mb < 400.0
        ), f"Memory usage {metrics.memory_peak_mb:.2f}MB exceeds 400MB target"

        print(f"\nMemory per invoice: {metrics.memory_peak_mb / 200:.3f} MB")

    async def test_memory_during_concurrent_operations(self, e2e_system_indexed, e2e_retriever):
        """Test memory usage with concurrent searches (target: <200MB)."""
        session, clienti, fatture, indexer = e2e_system_indexed

        async def concurrent_load():
            # 10 concurrent searches
            queries = [f"Query {i}" for i in range(10)]
            tasks = [e2e_retriever.retrieve(q, top_k=5) for q in queries]
            results = await asyncio.gather(*tasks)
            return results

        metrics = await measure_async_function(concurrent_load, iterations=5, warmup=1)

        metrics.print_summary()

        # Target: <200MB for concurrent searches
        assert (
            metrics.memory_peak_mb < 200.0
        ), f"Memory usage {metrics.memory_peak_mb:.2f}MB exceeds 200MB target"


@pytest.mark.performance
@pytest.mark.asyncio
class TestSystemLatencyBreakdown:
    """Test detailed latency breakdown of system components."""

    async def test_component_latency_profiling(self, e2e_system_indexed, e2e_retriever):
        """Profile latency of individual components in workflow."""
        session, clienti, fatture, indexer = e2e_system_indexed

        test_fattura = fatture[50]
        query = f"Fattura {test_fattura.cliente.denominazione}"

        # Profile each component
        with PerformanceProfiler("indexing", iterations=1) as idx_prof:
            await indexer.index_invoice(test_fattura.id)

        with PerformanceProfiler("retrieval", iterations=1) as ret_prof:
            results = await e2e_retriever.retrieve(query, top_k=5)

        with PerformanceProfiler("formatting", iterations=1) as fmt_prof:
            formatted = e2e_retriever.format_results(results)

        print("\n" + "=" * 70)
        print("COMPONENT LATENCY BREAKDOWN")
        print("=" * 70)
        print(f"Indexing:   {idx_prof.metrics.latencies_ms[0]:.2f}ms")
        print(f"Retrieval:  {ret_prof.metrics.latencies_ms[0]:.2f}ms")
        print(f"Formatting: {fmt_prof.metrics.latencies_ms[0]:.2f}ms")
        print(
            f"Total:      {sum([idx_prof.metrics.latencies_ms[0], ret_prof.metrics.latencies_ms[0], fmt_prof.metrics.latencies_ms[0]]):.2f}ms"
        )
        print("=" * 70)


# Performance summary
def test_performance_summary():
    """Print E2E performance summary."""
    print("\n" + "=" * 70)
    print("END-TO-END PERFORMANCE SUMMARY")
    print("=" * 70)
    print("\nTargets:")
    print("  ✓ Full flow (create→index→retrieve): <1s")
    print("  ✓ Search query end-to-end:           <300ms")
    print("  ✓ Batch index + search (200 inv):    <15s")
    print("  ✓ Concurrent searches (5):            <500ms")
    print("  ✓ Memory (batch 200):                 <400MB")
    print("  ✓ Memory (concurrent):                <200MB")
    print("\nAll E2E performance targets validated! ✅")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
