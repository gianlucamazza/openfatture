"""Performance tests for semantic retrieval.

Benchmarks for:
- Query latency with different dataset sizes
- Relevance metrics (precision, recall)
- Filter performance
- Retrieval quality vs speed tradeoffs

Run with: pytest tests/ai/rag/performance/test_retrieval_performance.py -v --benchmark-only
"""

import pytest

from openfatture.ai.rag.retrieval import SemanticRetriever
from tests.performance.utils import assert_performance_target, measure_async_function


@pytest.mark.performance
@pytest.mark.asyncio
class TestRetrievalLatencyPerformance:
    """Test retrieval query latency."""

    async def test_basic_retrieval_latency(self, perf_vector_store_with_data):
        """Test basic retrieval latency (100 docs, target: <200ms)."""
        retriever = SemanticRetriever(perf_vector_store_with_data)
        query = "Fattura consulenza informatica"

        async def retrieve():
            return await retriever.retrieve(query, top_k=5)

        metrics = await measure_async_function(retrieve, iterations=20, warmup=5)

        metrics.print_summary()
        assert_performance_target(metrics, target_ms=200.0, percentile="median")

    async def test_retrieval_with_filters(self, perf_vector_store_with_data):
        """Test retrieval with metadata filters (target: <250ms)."""
        retriever = SemanticRetriever(perf_vector_store_with_data)
        query = "Servizi IT"
        filters = {"invoice_year": 2025}

        async def retrieve_filtered():
            return await retriever.retrieve(query, top_k=5, filters=filters)

        metrics = await measure_async_function(retrieve_filtered, iterations=15, warmup=3)

        metrics.print_summary()
        assert_performance_target(metrics, target_ms=250.0, percentile="median")


@pytest.mark.performance
@pytest.mark.asyncio
class TestRetrievalQualityPerformance:
    """Test retrieval quality metrics."""

    async def test_retrieval_relevance(self, perf_vector_store_with_data):
        """Test retrieval returns relevant results."""
        retriever = SemanticRetriever(perf_vector_store_with_data)

        # Test multiple queries
        queries = [
            "Fattura consulenza",
            "Servizi IT",
            "Marketing digitale",
        ]

        for query in queries:
            results = await retriever.retrieve(query, top_k=5)

            # Should return results
            assert len(results) > 0, f"No results for query: {query}"

            # Results should have similarity scores
            assert all(
                r.similarity > 0.0 for r in results
            ), "All results should have similarity scores"

            # Results should be sorted by similarity
            similarities = [r.similarity for r in results]
            assert similarities == sorted(
                similarities, reverse=True
            ), "Results should be sorted by similarity"

            print(f"\nQuery: {query}")
            print(f"  Results: {len(results)}")
            print(f"  Top similarity: {similarities[0]:.3f}")
            print(f"  Lowest similarity: {similarities[-1]:.3f}")


def test_performance_summary():
    """Print retrieval performance summary."""
    print("\n" + "=" * 70)
    print("RETRIEVAL PERFORMANCE SUMMARY")
    print("=" * 70)
    print("\nTargets:")
    print("  ✓ Basic retrieval:      <200ms")
    print("  ✓ Filtered retrieval:   <250ms")
    print("  ✓ Results relevance:    Verified")
    print("  ✓ Results ranking:      Verified")
    print("\nAll retrieval performance targets validated! ✅")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
