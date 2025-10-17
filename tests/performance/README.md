# Performance Testing Utilities

Core utilities for performance testing in OpenFatture.

## Overview

This directory contains reusable utilities for performance benchmarking:

- **`utils.py`**: Performance profiler, metrics collector, assertions
- **`fixtures.py`**: Realistic dataset generators (invoices, clients, documents)
- **`report_generator.py`**: HTML report generator with Chart.js visualizations

## Quick Start

```python
from tests.performance.utils import (
    PerformanceProfiler,
    PerformanceMetrics,
    measure_async_function,
    assert_performance_target,
)
from tests.performance.fixtures import generate_invoices, generate_clients

# Profile a function
with PerformanceProfiler("my_operation") as profiler:
    # ... do work ...
    pass

profiler.metrics.print_summary()

# Measure over iterations
metrics = await measure_async_function(
    my_async_func,
    arg1, arg2,
    iterations=20,
    warmup=5
)

# Assert performance target
assert_performance_target(metrics, target_ms=100.0, percentile="p95")
```

## Utilities Reference

### PerformanceMetrics

Dataclass for storing performance metrics:

```python
@dataclass
class PerformanceMetrics:
    name: str
    iterations: int
    latencies_ms: list[float]
    memory_peak_mb: float
    throughput: float

    # Computed properties
    mean_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    std_latency_ms: float
```

### PerformanceProfiler

Context manager for profiling:

```python
with PerformanceProfiler("operation_name", track_memory=True) as profiler:
    # ... do work ...
    pass

# Access metrics
metrics = profiler.metrics
print(f"Latency: {metrics.mean_latency_ms:.2f}ms")
print(f"Memory: {metrics.memory_peak_mb:.2f}MB")
```

### measure_async_function / measure_sync_function

Measure function performance over multiple iterations:

```python
# Async function
metrics = await measure_async_function(
    async_func,
    arg1, arg2,
    iterations=20,
    warmup=5,
    kwarg1="value"
)

# Sync function
metrics = measure_sync_function(
    sync_func,
    arg1,
    iterations=20,
    warmup=5
)
```

### assert_performance_target

Assert performance meets target:

```python
assert_performance_target(
    metrics,
    target_ms=100.0,
    percentile="p95"  # Options: "mean", "median", "p50", "p95", "p99"
)
```

## Dataset Generators

### DataGenerator

Reproducible test data with seeded random:

```python
from tests.performance.fixtures import DataGenerator

gen = DataGenerator(seed=42)

# Generate clients
clienti = gen.generate_clients(count=100)

# Generate invoices
fatture = gen.generate_invoices(clienti, count=1000, year=2025)

# Generate payments
pagamenti = gen.generate_payments(fatture, payment_rate=0.7)

# Generate RAG documents
documents = gen.generate_documents_for_rag(count=500)
```

### Convenience Functions

```python
from tests.performance.fixtures import (
    generate_clients,
    generate_invoices,
    generate_payments,
    generate_rag_documents,
)

clienti = generate_clients(count=100, seed=42)
fatture = generate_invoices(clienti, count=1000, year=2025, seed=42)
pagamenti = generate_payments(fatture, payment_rate=0.7, seed=42)
documents = generate_rag_documents(count=500, seed=42)
```

## HTML Report Generator

Generate visual performance reports:

```python
from tests.performance.report_generator import (
    HTMLBenchmarkReporter,
    generate_report,
)

# Create reporter
reporter = HTMLBenchmarkReporter()

# Add metrics
reporter.add_metrics(metrics1)
reporter.add_metrics(metrics2)
reporter.add_metrics(metrics3)

# Save HTML report
reporter.save("benchmark_report.html")

# Or use convenience function
generate_report([metrics1, metrics2, metrics3], "report.html")
```

**Report Features:**
- Summary statistics (total tests, avg latency, peak memory)
- Detailed metrics table (mean, median, p95, p99, throughput)
- Interactive Chart.js visualizations (latency, throughput)
- Responsive design

## Best Practices

### 1. Use Fixed Seeds

Always use fixed seeds for reproducibility:

```python
# Good
clienti = generate_clients(count=100, seed=42)

# Bad - random seed
clienti = generate_clients(count=100)
```

### 2. Include Warmup Runs

Include warmup iterations to stabilize measurements:

```python
# Good
metrics = await measure_async_function(
    func,
    iterations=20,
    warmup=5  # 5 warmup runs
)

# Bad - no warmup
metrics = await measure_async_function(func, iterations=20, warmup=0)
```

### 3. Check Multiple Percentiles

Don't rely only on mean latency:

```python
# Good - check p95 and p99
assert_performance_target(metrics, target_ms=100.0, percentile="p95")
assert_performance_target(metrics, target_ms=150.0, percentile="p99")

# Less reliable - mean can hide outliers
assert_performance_target(metrics, target_ms=50.0, percentile="mean")
```

### 4. Track Memory for Large Operations

Enable memory tracking for batch operations:

```python
with PerformanceProfiler("large_batch", track_memory=True) as profiler:
    process_large_batch(data)

assert profiler.metrics.memory_peak_mb < 200.0
```

### 5. Use Realistic Data Sizes

Match dataset sizes to real-world scenarios:

```python
# Production-like sizes
clienti = generate_clients(count=100)     # ~100 clients
fatture = generate_invoices(clienti, count=1000)  # ~1000 invoices/year
documents = generate_rag_documents(count=500)  # ~500 indexed docs
```

## Examples

See test files for complete examples:
- `tests/ai/rag/performance/test_embeddings_performance.py`
- `tests/ai/rag/performance/test_vector_store_performance.py`
- `tests/storage/performance/test_database_performance.py`
- `tests/integration/performance/test_e2e_performance.py`

## Performance Targets

Recommended targets by component:

| Component | Operation | Target |
|-----------|-----------|--------|
| Embeddings | Single text (local) | <50ms |
| Embeddings | Batch 100 (local) | <5s |
| Vector Store | Search (100 docs) | <150ms |
| Vector Store | Insert batch (100) | <3s |
| Database | Simple query | <10ms |
| Database | Complex join | <100ms |
| Indexing | Single invoice | <200ms |
| Indexing | Batch 500 | <30s |
| E2E | Full workflow | <1s |

## Troubleshooting

**High variance in results:**
- Increase iteration count (20-50 iterations)
- Increase warmup runs (5-10 warmup)
- Close background applications
- Run on isolated hardware

**Memory errors:**
- Reduce dataset size
- Process in smaller batches
- Check for memory leaks

**Tests too slow:**
- Use mock embeddings for faster tests
- Reduce iteration count for quick checks
- Run specific test files instead of full suite

## Contributing

When adding new performance utilities:

1. Add docstrings with examples
2. Include type hints
3. Add unit tests (if applicable)
4. Update this README
5. Follow existing patterns
