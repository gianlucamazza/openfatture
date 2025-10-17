"""HTML benchmark report generator.

Generates comprehensive HTML reports from performance test results.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from tests.performance.utils import PerformanceMetrics


class HTMLBenchmarkReporter:
    """Generate HTML benchmark reports with charts and tables.

    Example:
        >>> reporter = HTMLBenchmarkReporter()
        >>> reporter.add_metrics(my_metrics)
        >>> reporter.save("benchmark_report.html")
    """

    def __init__(self):
        """Initialize reporter."""
        self.metrics_list: list[PerformanceMetrics] = []
        self.test_info: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {},
        }

    def add_metrics(self, metrics: PerformanceMetrics) -> None:
        """Add performance metrics to report.

        Args:
            metrics: PerformanceMetrics object
        """
        self.metrics_list.append(metrics)

    def save(self, output_path: str | Path) -> None:
        """Generate and save HTML report.

        Args:
            output_path: Path to save HTML file
        """
        output_path = Path(output_path)
        html_content = self._generate_html()

        output_path.write_text(html_content, encoding="utf-8")
        print(f"Benchmark report saved to: {output_path}")

    def _generate_html(self) -> str:
        """Generate complete HTML report content."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenFatture Performance Benchmark Report</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>OpenFatture Performance Benchmark Report</h1>
            <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>

        <section class="summary">
            <h2>Summary</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Total Tests</h3>
                    <p class="stat-value">{len(self.metrics_list)}</p>
                </div>
                <div class="stat-card">
                    <h3>Total Iterations</h3>
                    <p class="stat-value">{sum(m.iterations for m in self.metrics_list)}</p>
                </div>
                <div class="stat-card">
                    <h3>Avg Latency</h3>
                    <p class="stat-value">{self._avg_latency():.2f} ms</p>
                </div>
                <div class="stat-card">
                    <h3>Peak Memory</h3>
                    <p class="stat-value">{self._peak_memory():.2f} MB</p>
                </div>
            </div>
        </section>

        <section class="details">
            <h2>Test Details</h2>
            {self._generate_metrics_tables()}
        </section>

        <section class="charts">
            <h2>Performance Charts</h2>
            <div class="chart-container">
                <canvas id="latencyChart"></canvas>
            </div>
            <div class="chart-container">
                <canvas id="throughputChart"></canvas>
            </div>
        </section>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
    <script>
        {self._generate_charts_script()}
    </script>
</body>
</html>
"""

    def _get_css(self) -> str:
        """Get CSS styles for HTML report."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .timestamp {
            opacity: 0.9;
            font-size: 0.9em;
        }

        section {
            background: white;
            padding: 30px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .stat-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }

        .stat-card h3 {
            color: #555;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }

        .metrics-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            overflow-x: auto;
            display: block;
        }

        .metrics-table table {
            width: 100%;
            min-width: 600px;
        }

        .metrics-table th,
        .metrics-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }

        .metrics-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }

        .metrics-table tr:hover {
            background: #f8f9fa;
        }

        .metrics-table .metric-name {
            font-weight: 600;
            color: #667eea;
        }

        .chart-container {
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }

        canvas {
            max-height: 400px;
        }

        .status-pass {
            color: #28a745;
            font-weight: bold;
        }

        .status-warning {
            color: #ffc107;
            font-weight: bold;
        }

        .status-fail {
            color: #dc3545;
            font-weight: bold;
        }
        """

    def _generate_metrics_tables(self) -> str:
        """Generate HTML tables for metrics."""
        if not self.metrics_list:
            return "<p>No metrics available</p>"

        table_html = """
        <div class="metrics-table">
            <table>
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Iterations</th>
                        <th>Mean (ms)</th>
                        <th>Median (ms)</th>
                        <th>P95 (ms)</th>
                        <th>P99 (ms)</th>
                        <th>Std Dev (ms)</th>
                        <th>Throughput (ops/s)</th>
                        <th>Memory (MB)</th>
                    </tr>
                </thead>
                <tbody>
        """

        for metrics in self.metrics_list:
            table_html += f"""
                <tr>
                    <td class="metric-name">{metrics.name}</td>
                    <td>{metrics.iterations}</td>
                    <td>{metrics.mean_latency_ms:.3f}</td>
                    <td>{metrics.median_latency_ms:.3f}</td>
                    <td>{metrics.p95_latency_ms:.3f}</td>
                    <td>{metrics.p99_latency_ms:.3f}</td>
                    <td>{metrics.std_latency_ms:.3f}</td>
                    <td>{metrics.throughput:.2f}</td>
                    <td>{metrics.memory_peak_mb:.2f}</td>
                </tr>
            """

        table_html += """
                </tbody>
            </table>
        </div>
        """

        return table_html

    def _generate_charts_script(self) -> str:
        """Generate Chart.js script for visualizations."""
        if not self.metrics_list:
            return ""

        # Prepare data for charts
        labels = [m.name for m in self.metrics_list]
        mean_latencies = [m.mean_latency_ms for m in self.metrics_list]
        p95_latencies = [m.p95_latency_ms for m in self.metrics_list]
        throughputs = [m.throughput for m in self.metrics_list]

        return f"""
        // Latency Chart
        const latencyCtx = document.getElementById('latencyChart').getContext('2d');
        new Chart(latencyCtx, {{
            type: 'bar',
            data: {{
                labels: {labels},
                datasets: [
                    {{
                        label: 'Mean Latency (ms)',
                        data: {mean_latencies},
                        backgroundColor: 'rgba(102, 126, 234, 0.6)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: 'P95 Latency (ms)',
                        data: {p95_latencies},
                        backgroundColor: 'rgba(118, 75, 162, 0.6)',
                        borderColor: 'rgba(118, 75, 162, 1)',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Latency (ms)'
                        }}
                    }}
                }},
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Latency Comparison'
                    }},
                    legend: {{
                        display: true,
                        position: 'top'
                    }}
                }}
            }}
        }});

        // Throughput Chart
        const throughputCtx = document.getElementById('throughputChart').getContext('2d');
        new Chart(throughputCtx, {{
            type: 'line',
            data: {{
                labels: {labels},
                datasets: [
                    {{
                        label: 'Throughput (ops/sec)',
                        data: {throughputs},
                        backgroundColor: 'rgba(40, 167, 69, 0.2)',
                        borderColor: 'rgba(40, 167, 69, 1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Operations per Second'
                        }}
                    }}
                }},
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Throughput Comparison'
                    }},
                    legend: {{
                        display: true,
                        position: 'top'
                    }}
                }}
            }}
        }});
        """

    def _avg_latency(self) -> float:
        """Calculate average latency across all tests."""
        if not self.metrics_list:
            return 0.0
        return sum(m.mean_latency_ms for m in self.metrics_list) / len(self.metrics_list)

    def _peak_memory(self) -> float:
        """Get peak memory usage across all tests."""
        if not self.metrics_list:
            return 0.0
        return max(m.memory_peak_mb for m in self.metrics_list)


def generate_report(metrics_list: list[PerformanceMetrics], output_path: str | Path) -> None:
    """Generate HTML benchmark report from metrics.

    Args:
        metrics_list: List of PerformanceMetrics objects
        output_path: Path to save HTML file

    Example:
        >>> from tests.performance.utils import PerformanceMetrics
        >>> metrics = [PerformanceMetrics(name="test1", iterations=10)]
        >>> generate_report(metrics, "report.html")
    """
    reporter = HTMLBenchmarkReporter()
    for metrics in metrics_list:
        reporter.add_metrics(metrics)
    reporter.save(output_path)
