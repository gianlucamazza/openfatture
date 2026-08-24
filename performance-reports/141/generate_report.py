import json
from pathlib import Path
from tests.performance.report_generator import HTMLBenchmarkReporter
from tests.performance.utils import PerformanceMetrics

# Load benchmark results
results_file = Path("benchmark-results/benchmark-results.json")
if not results_file.exists() or results_file.stat().st_size == 0:
    print("No benchmark results found; skipping HTML report")
    exit(0)

try:
    with open(results_file) as f:
        data = json.load(f)
except json.JSONDecodeError:
    print("Benchmark results are empty or invalid; skipping HTML report")
    exit(0)

if not data.get("benchmarks"):
    print("No benchmark entries found; skipping HTML report")
    exit(0)

# Convert to PerformanceMetrics
reporter = HTMLBenchmarkReporter()

for bench in data.get("benchmarks", []):
    stats = bench.get("stats", {})
    metrics = PerformanceMetrics(
        name=bench.get("name", "unknown"),
        iterations=bench.get("params", {}).get("iterations", 1),
    )

    # Add latency data
    if "mean" in stats:
        metrics.latencies_ms = [stats["mean"] * 1000]
        metrics.throughput = 1000 / (stats["mean"] * 1000) if stats["mean"] > 0 else 0

    reporter.add_metrics(metrics)

# Save report
reporter.save("performance-report.html")
print("Report generated: performance-report.html")
