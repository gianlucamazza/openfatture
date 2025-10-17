# Performance Testing Guide

Comprehensive guide to performance testing and benchmarking in OpenFatture.

## Overview

OpenFatture includes a complete performance testing suite to measure and optimize:
- **RAG System**: Embedding generation, vector search, semantic retrieval
- **Database**: Query latency, aggregations, complex joins
- **End-to-End**: Complete workflows from invoice creation to retrieval

## Quick Start

```bash
# Run all performance tests
make test-performance

# Run specific test suites
make test-performance-rag      # RAG system tests
make test-performance-db       # Database tests

# Generate HTML report
make test-performance-report

# Compare with previous run
make test-performance-compare
```

## Test Architecture

### Directory Structure

```
tests/
├── performance/
│   ├── __init__.py
│   ├── utils.py                 # Profiler, metrics collector
│   ├── fixtures.py              # Dataset generators
│   └── report_generator.py      # HTML benchmark reports
├── ai/rag/performance/
│   ├── conftest.py              # RAG fixtures
│   ├── test_embeddings_performance.py
│   ├── test_vector_store_performance.py
│   └── test_retrieval_performance.py
└── storage/performance/
    ├── conftest.py              # Database fixtures
    └── test_database_performance.py
```

### Key Components

**1. Performance Utilities** (`tests/performance/utils.py`)

```python
from tests.performance.utils import (
    PerformanceMetrics,
    PerformanceProfiler,
    measure_async_function,
    assert_performance_target,
)

# Profile a function
async def my_function():
    with PerformanceProfiler("operation_name") as profiler:
        # ... do work ...
        pass
    profiler.metrics.print_summary()

# Measure over multiple iterations
metrics = await measure_async_function(
    my_async_func,
    arg1, arg2,
    iterations=20,
    warmup=5
)

# Assert performance target
assert_performance_target(metrics, target_ms=100.0, percentile="p95")
```

**2. Dataset Generators** (`tests/performance/fixtures.py`)

```python
from tests.performance.fixtures import (
    generate_clients,
    generate_invoices,
    generate_rag_documents,
)

# Generate test data
clienti = generate_clients(count=100, seed=42)
fatture = generate_invoices(clienti, count=1000, year=2025)
documents = generate_rag_documents(count=500)
```

**3. HTML Reports** (`tests/performance/report_generator.py`)

```python
from tests.performance.report_generator import generate_report

# Generate HTML benchmark report
metrics_list = [metrics1, metrics2, metrics3]
generate_report(metrics_list, "benchmark_report.html")
```

## Performance Targets

### Embedding Generation

| Operation | Target | Dataset |
|-----------|--------|---------|
| Single text (local) | <50ms | 1 document |
| Batch 10 docs | <500ms | 10 documents |
| Batch 100 docs | <5000ms | 100 documents |
| Memory usage | <100MB | 100 documents |

### Vector Store

| Operation | Target | Dataset |
|-----------|--------|---------|
| Single insert | <100ms | 1 document |
| Batch insert (10) | <500ms | 10 documents |
| Batch insert (100) | <3000ms | 100 documents |
| Search (100 docs) | <150ms | 100 documents |
| Search with filters | <200ms | 100 documents |
| Update document | <150ms | 1 document |
| Memory (1000 docs) | <200MB | 1000 documents |

### Retrieval

| Operation | Target | Dataset |
|-----------|--------|---------|
| Basic retrieval | <200ms | 100 documents |
| Filtered retrieval | <250ms | 100 documents |

### Database

| Operation | Target | Dataset |
|-----------|--------|---------|
| Simple query by ID | <10ms | 500 invoices |
| Query with relationships | <50ms | 500 invoices |
| Paginated list (50) | <100ms | 500 invoices |
| Count query | <20ms | 500 invoices |
| Aggregations (SUM) | <50ms | 500 invoices |
| Complex joins | <100ms | 500 invoices |

## Writing Performance Tests

### Test Structure

```python
import pytest
from tests.performance.utils import (
    measure_async_function,
    assert_performance_target,
)

@pytest.mark.performance
@pytest.mark.asyncio
class TestMyFeaturePerformance:
    """Performance tests for MyFeature."""

    async def test_operation_latency(self, my_fixture):
        """Test operation latency (target: <100ms)."""

        async def my_operation():
            # ... perform operation ...
            pass

        metrics = await measure_async_function(
            my_operation,
            iterations=20,
            warmup=5
        )

        metrics.print_summary()
        assert_performance_target(metrics, target_ms=100.0, percentile="median")
```

### Best Practices

1. **Use Markers**: Always use `@pytest.mark.performance`
2. **Warmup Runs**: Include 2-5 warmup iterations
3. **Multiple Iterations**: Run 10-50 iterations for statistical significance
4. **Check Multiple Percentiles**: Verify p50, p95, p99
5. **Memory Profiling**: Track memory usage for large operations
6. **Deterministic Seeds**: Use fixed seeds for reproducible datasets

### Common Patterns

**Scaling Tests:**

```python
async def test_operation_scaling(self):
    """Test performance scaling with different dataset sizes."""
    sizes = [100, 500, 1000]
    results = {}

    for size in sizes:
        dataset = generate_test_data(size)
        metrics = await measure_async_function(
            process_dataset,
            dataset,
            iterations=5,
            warmup=1
        )
        results[size] = metrics.mean_latency_ms
        print(f"\nSize {size}: {metrics.mean_latency_ms:.2f}ms")

    # Verify sub-linear scaling
    scaling_factor = results[1000] / results[100]
    assert scaling_factor < 3.0, "Poor scaling detected"
```

**Memory Tests:**

```python
async def test_memory_usage(self):
    """Test peak memory usage (target: <200MB)."""
    metrics = await measure_async_function(
        large_operation,
        iterations=3,
        warmup=1
    )

    assert metrics.memory_peak_mb < 200.0
```

## Running Tests

### Command Line

```bash
# Run all performance tests
pytest -v -m performance

# Run specific test file
pytest tests/ai/rag/performance/test_embeddings_performance.py -v

# Run with benchmarking
pytest -v -m performance --benchmark-only

# Generate comparison report
pytest -v -m performance --benchmark-compare --benchmark-autosave
```

### Makefile Commands

```bash
make test-performance              # All performance tests
make test-performance-rag          # RAG tests only
make test-performance-db           # Database tests only
make test-performance-report       # Generate HTML report
make test-performance-compare      # Compare with baseline
make tperf                         # Shortcut
```

### Filtering Tests

```bash
# Skip performance tests (in regular test runs)
pytest -v -m "not performance"

# Run only slow tests
pytest -v -m "slow"

# Run performance tests for a specific module
pytest -v -k "embedding" -m performance
```

## Interpreting Results

### Performance Metrics

```
Performance Metrics: embedding_generation
====================================================================
Iterations:      20
Mean latency:    45.234 ms
Median (p50):    44.123 ms
p95:             48.567 ms
p99:             52.891 ms
Min:             42.001 ms
Max:             55.234 ms
Std dev:         3.456 ms
Throughput:      22.11 ops/sec
Peak memory:     12.34 MB
====================================================================
```

**Key Indicators:**

- **Mean**: Average performance
- **Median (p50)**: Typical case (50% of requests are faster)
- **p95**: 95% of requests are faster than this
- **p99**: Worst-case excluding outliers
- **Std dev**: Consistency (lower is better)
- **Throughput**: Operations per second
- **Memory**: Peak memory usage

### Performance Regressions

A performance regression is detected when:

1. **Mean latency increases by >20%** from baseline
2. **p95 latency increases by >30%** from baseline
3. **Throughput decreases by >20%** from baseline
4. **Memory usage increases by >50%** from baseline

### Optimization Strategies

**For Slow Embeddings:**
- Use batch processing (`embed_batch` vs multiple `embed_text`)
- Enable caching for repeated texts
- Consider local models (SentenceTransformers) vs API calls

**For Slow Vector Search:**
- Reduce `top_k` if possible
- Optimize metadata filters (use indexed fields)
- Consider collection size (reindex if too large)

**For Slow Database Queries:**
- Add indexes on frequently queried fields
- Use `joinedload`/`subqueryload` for relationships
- Implement pagination for large result sets
- Use aggregations instead of loading all records

## Continuous Monitoring

### CI/CD Integration

OpenFatture includes a complete GitHub Actions workflow for automated performance testing:

**Workflow: `.github/workflows/performance.yml`**

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Weekly schedule (Monday 2 AM UTC)
- Manual workflow dispatch

**Jobs:**

1. **performance-tests**: Runs all performance benchmarks
   - Collects metrics (latency, throughput, memory)
   - Stores results as artifacts (30 days retention)
   - Generates JSON benchmark data

2. **performance-report**: Generates HTML report (main/develop only)
   - Creates visual performance report
   - Uploads to artifacts (90 days retention)
   - Deploys to GitHub Pages for historical tracking

3. **performance-regression-check**: Detects regressions (PRs only)
   - Compares with baseline from main branch
   - Fails if >20% latency increase or >50% memory increase
   - Comments on PR with performance summary

**Setup GitHub Pages** (optional):
1. Go to repository Settings → Pages
2. Source: Deploy from branch `gh-pages`
3. Access reports at: `https://[username].github.io/[repo]/performance-reports/`

### Baseline Management

**Create Baseline:**

```bash
# Run script to save baseline
./scripts/save_performance_baseline.sh main

# Or manually with specific name
./scripts/save_performance_baseline.sh v1.2.0

# Baseline saved to: .performance-baselines/
```

**Baseline Files:**

```
.performance-baselines/
├── main_20251016_143022.json       # Timestamped baseline
├── v1.2.0_20251016_150000.json     # Version baseline
└── latest.json -> main_20251016_143022.json  # Symlink to latest
```

**Compare with Baseline:**

```bash
# Compare current performance with baseline
export PERFORMANCE_BASELINE=main
make test-performance

# View baseline metadata
cat .performance-baselines/latest.json
```

**Baseline File Format:**

```json
{
  "name": "main",
  "timestamp": "20251016_143022",
  "git_commit": "abc123def456",
  "git_branch": "main",
  "python_version": "Python 3.12.11",
  "system": "Darwin",
  "arch": "arm64"
}
```

### Automated Alerts

The CI/CD workflow automatically:

1. **Fails PR builds** if performance degrades >20% (latency) or >50% (memory)
2. **Comments on PRs** with performance summary and top 5 slowest tests
3. **Tracks trends** via GitHub Pages reports (historical data)

**Example PR Comment:**

```
## 📊 Performance Test Results

### Summary

| Metric | Value |
|--------|-------|
| Total Tests | 48 |

### Top 5 Slowest Tests

| Test | Mean | p95 |
|------|------|-----|
| test_batch_indexing_medium | 4523.45ms | 4789.12ms |
| test_search_scalability | 2341.67ms | 2567.89ms |
| test_concurrent_searches | 456.78ms | 489.12ms |
| test_batch_insertion_medium | 401.23ms | 432.56ms |
| test_retrieval_latency | 189.45ms | 201.34ms |

---
💡 View detailed results in the workflow artifacts
```

**Slack/Email Notifications** (optional):

Add to workflow:

```yaml
- name: Notify on regression
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: '⚠️ Performance regression detected in PR #${{ github.event.pull_request.number }}'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## Troubleshooting

### Common Issues

**1. Slow Test Execution**

```bash
# Use mock embeddings for faster tests
pytest -v -m performance --no-real-embeddings

# Reduce iteration count
pytest -v -m performance -k "quick"
```

**2. Inconsistent Results**

```bash
# Increase warmup runs
# Increase iteration count
# Check for background processes
# Run on isolated hardware
```

**3. Memory Errors**

```bash
# Reduce dataset size in fixtures
# Run tests sequentially
# Monitor with: htop or Activity Monitor
```

**4. Pytest-Benchmark Not Found**

```bash
# Install dev dependencies
uv sync --all-extras
```

## Examples

See example tests in:
- `tests/ai/rag/performance/test_embeddings_performance.py`
- `tests/ai/rag/performance/test_vector_store_performance.py`
- `tests/storage/performance/test_database_performance.py`

## Resources

- [pytest-benchmark documentation](https://pytest-benchmark.readthedocs.io/)
- [Performance testing best practices](https://docs.python-guide.org/writing/tests/)
- [Profiling Python code](https://docs.python.org/3/library/profile.html)

---

## Quick Reference

### Common Commands

```bash
# Run all performance tests
make test-performance

# Run specific suite
make test-performance-rag      # RAG only
make test-performance-db       # Database only

# Generate report
make test-performance-report

# Compare with baseline
make test-performance-compare

# Save baseline
./scripts/save_performance_baseline.sh main
```

### Performance Test Results Example

```
Performance Metrics: embed_text
======================================================================
Iterations:      20
Mean latency:    12.190 ms
Median (p50):    12.045 ms
p95:             12.910 ms
p99:             12.955 ms
Min:             11.414 ms
Max:             12.967 ms
Std dev:         0.426 ms
Throughput:      82.04 ops/sec
Peak memory:     0.04 MB
======================================================================
```

### CI/CD Status Badges

Add to README.md:

```markdown
![Performance Tests](https://github.com/[username]/[repo]/workflows/Performance%20Tests/badge.svg)
```

---

**Next Steps:**
1. ✅ Run initial baseline: `./scripts/save_performance_baseline.sh main`
2. ✅ Push workflow to enable CI/CD
3. ✅ Configure GitHub Pages (optional)
4. ✅ Review and adjust targets based on your hardware
5. ✅ Monitor performance trends over time
