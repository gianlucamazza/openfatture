#!/usr/bin/env python3
"""
Media Metrics Collection for OpenFatture

Collects and stores metrics from media automation runs including costs,
performance data, and success rates.
"""

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass
class MediaRunMetrics:
    """Metrics for a single media automation run."""

    run_id: str
    scenario: str
    timestamp: str
    duration_seconds: float
    cost_usd: float
    tokens_used: int
    video_size_mb: float
    success: bool
    error_message: str | None = None
    provider: str = "unknown"  # 'anthropic' or 'ollama'
    workflow_type: str = "unknown"  # 'generation', 'optimization', 'validation'
    git_commit: str = ""
    vhs_version: str = ""
    collected_at: str | None = None

    def __post_init__(self):
        if not self.collected_at:
            self.collected_at = datetime.now().isoformat()


class MediaMetricsCollector:
    """Collects and manages media automation metrics."""

    def __init__(
        self, metrics_dir: str = "media/metrics", alerts_config: str = "media/alerts_config.json"
    ):
        self.metrics_dir = Path(metrics_dir)
        self.alerts_config_path = Path(alerts_config)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        # Metrics files
        self.runs_file = self.metrics_dir / "runs.json"
        self.costs_file = self.metrics_dir / "costs.json"
        self.performance_file = self.metrics_dir / "performance.json"
        self.alerts_file = self.metrics_dir / "alerts.json"

        # Load alert configuration
        self.alert_config = self._load_alert_config()

    def _load_alert_config(self) -> dict[str, Any]:
        """Load alert configuration from JSON file."""
        if not self.alerts_config_path.exists():
            # Return default configuration if file doesn't exist
            return {
                "thresholds": {
                    "cost": {
                        "daily_budget_usd": 1.0,
                        "monthly_budget_usd": 30.0,
                        "monthly_warning_pct": 83,
                        "enable_daily_alerts": True,
                        "enable_monthly_alerts": True,
                    },
                    "performance": {
                        "max_duration_seconds": 600,
                        "enable_duration_alerts": True,
                        "min_success_rate_pct": 80,
                        "enable_success_rate_alerts": True,
                    },
                    "failure": {
                        "enable_failure_alerts": True,
                        "max_consecutive_failures": 3,
                        "alert_on_first_failure": True,
                    },
                },
                "notifications": {"console": {"enabled": True, "verbose": False}},
            }

        try:
            with open(self.alerts_config_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print(
                f"Warning: Could not load alert config from {self.alerts_config_path}, using defaults"
            )
            return self._load_alert_config()  # Recursive call to get defaults

    def collect_run_metrics(self, run_data: dict[str, Any]) -> None:
        """Collect metrics from a single run."""
        # Validate required fields
        required_fields = ["run_id", "scenario", "timestamp", "duration_seconds"]
        for field in required_fields:
            if field not in run_data:
                raise ValueError(f"Missing required field: {field}")

        # Create metrics object
        metrics = MediaRunMetrics(**run_data)

        # Save to runs.json
        runs = self._load_json_list(self.runs_file)
        runs.append(asdict(metrics))

        # Keep only last 1000 runs to prevent file bloat
        if len(runs) > 1000:
            runs = runs[-1000:]

        self._save_json(self.runs_file, runs)

        # Update aggregated metrics
        self._update_cost_aggregates(metrics)
        self._update_performance_aggregates(metrics)
        self._check_alerts(metrics)

    def _update_cost_aggregates(self, metrics: MediaRunMetrics) -> None:
        """Update cost aggregation data."""
        costs = self._load_json_dict(self.costs_file)

        # Daily aggregation
        date_key = metrics.timestamp[:10]  # YYYY-MM-DD
        if date_key not in costs:
            costs[date_key] = {"total_usd": 0.0, "runs": 0, "scenarios": {}, "providers": {}}

        day_data = costs[date_key]
        day_data["total_usd"] += metrics.cost_usd
        day_data["runs"] += 1

        # Scenario breakdown
        if metrics.scenario not in day_data["scenarios"]:
            day_data["scenarios"][metrics.scenario] = {"cost_usd": 0.0, "runs": 0}
        day_data["scenarios"][metrics.scenario]["cost_usd"] += metrics.cost_usd
        day_data["scenarios"][metrics.scenario]["runs"] += 1

        # Provider breakdown
        if metrics.provider not in day_data["providers"]:
            day_data["providers"][metrics.provider] = {"cost_usd": 0.0, "runs": 0}
        day_data["providers"][metrics.provider]["cost_usd"] += metrics.cost_usd
        day_data["providers"][metrics.provider]["runs"] += 1

        self._save_json(self.costs_file, costs)

    def _update_performance_aggregates(self, metrics: MediaRunMetrics) -> None:
        """Update performance aggregation data."""
        performance = self._load_json_dict(self.performance_file)

        date_key = metrics.timestamp[:10]  # YYYY-MM-DD
        if date_key not in performance:
            performance[date_key] = {
                "scenarios": {},
                "avg_duration_seconds": 0.0,
                "total_runs": 0,
                "success_rate": 0.0,
            }

        day_data = performance[date_key]

        # Scenario performance
        if metrics.scenario not in day_data["scenarios"]:
            day_data["scenarios"][metrics.scenario] = {
                "durations": [],
                "successes": 0,
                "failures": 0,
                "avg_duration": 0.0,
            }

        scenario_data = day_data["scenarios"][metrics.scenario]
        scenario_data["durations"].append(metrics.duration_seconds)

        if metrics.success:
            scenario_data["successes"] += 1
        else:
            scenario_data["failures"] += 1

        # Recalculate averages
        scenario_data["avg_duration"] = sum(scenario_data["durations"]) / len(
            scenario_data["durations"]
        )

        # Overall daily stats
        all_durations = []
        total_successes = 0
        total_runs = 0

        for scenario_stats in day_data["scenarios"].values():
            all_durations.extend(scenario_stats["durations"])
            total_successes += scenario_stats["successes"]
            total_runs += scenario_stats["successes"] + scenario_stats["failures"]

        if all_durations:
            day_data["avg_duration_seconds"] = sum(all_durations) / len(all_durations)
        day_data["total_runs"] = total_runs
        if total_runs > 0:
            day_data["success_rate"] = (total_successes / total_runs) * 100

        self._save_json(self.performance_file, performance)

    def _check_alerts(self, metrics: MediaRunMetrics) -> None:
        """Check for alerts based on configurable thresholds."""
        alerts = self._load_json_list(self.alerts_file)
        new_alerts = []

        # Cost alerts
        if self.alert_config["thresholds"]["cost"]["enable_daily_alerts"]:
            daily_cost = self._get_daily_cost(metrics.timestamp[:10])
            daily_budget = self.alert_config["thresholds"]["cost"]["daily_budget_usd"]

            if daily_cost > daily_budget:
                new_alerts.append(
                    {
                        "type": "cost",
                        "level": "warning",
                        "title": "Daily Cost Budget Exceeded",
                        "message": f"Daily cost exceeded: ${daily_cost:.2f} (budget: ${daily_budget:.2f})",
                        "timestamp": datetime.now().isoformat(),
                        "run_id": metrics.run_id,
                        "threshold": daily_budget,
                        "actual": daily_cost,
                        "scenario": metrics.scenario,
                    }
                )

        if self.alert_config["thresholds"]["cost"]["enable_monthly_alerts"]:
            monthly_cost = self._get_monthly_cost(metrics.timestamp[:7])
            monthly_budget = self.alert_config["thresholds"]["cost"]["monthly_budget_usd"]
            warning_threshold = monthly_budget * (
                self.alert_config["thresholds"]["cost"]["monthly_warning_pct"] / 100
            )

            if monthly_cost > warning_threshold:
                level = "error" if monthly_cost > monthly_budget else "warning"
                new_alerts.append(
                    {
                        "type": "cost",
                        "level": level,
                        "title": f"Monthly Cost {'Over Budget' if level == 'error' else 'Warning'}",
                        "message": f"Monthly cost: ${monthly_cost:.2f} (budget: ${monthly_budget:.2f})",
                        "timestamp": datetime.now().isoformat(),
                        "run_id": metrics.run_id,
                        "threshold": monthly_budget,
                        "actual": monthly_cost,
                        "scenario": metrics.scenario,
                    }
                )

        # Performance alerts
        if self.alert_config["thresholds"]["performance"]["enable_duration_alerts"]:
            max_duration = self.alert_config["thresholds"]["performance"]["max_duration_seconds"]

            if metrics.duration_seconds > max_duration:
                new_alerts.append(
                    {
                        "type": "performance",
                        "level": "warning",
                        "title": "Long Generation Time",
                        "message": f"Generation time exceeded: {metrics.duration_seconds:.1f}s (max: {max_duration}s) for {metrics.scenario}",
                        "timestamp": datetime.now().isoformat(),
                        "run_id": metrics.run_id,
                        "threshold": max_duration,
                        "actual": metrics.duration_seconds,
                        "scenario": metrics.scenario,
                    }
                )

        # Success rate alerts (check daily success rate)
        if self.alert_config["thresholds"]["performance"]["enable_success_rate_alerts"]:
            min_success_rate = self.alert_config["thresholds"]["performance"][
                "min_success_rate_pct"
            ]
            daily_success_rate = self._get_daily_success_rate(metrics.timestamp[:10])

            if daily_success_rate < min_success_rate:
                new_alerts.append(
                    {
                        "type": "performance",
                        "level": "error",
                        "title": "Low Success Rate",
                        "message": f"Daily success rate: {daily_success_rate:.1f}% (minimum: {min_success_rate}%)",
                        "timestamp": datetime.now().isoformat(),
                        "run_id": metrics.run_id,
                        "threshold": min_success_rate,
                        "actual": daily_success_rate,
                        "scenario": metrics.scenario,
                    }
                )

        # Failure alerts
        if (
            not metrics.success
            and self.alert_config["thresholds"]["failure"]["enable_failure_alerts"]
        ):
            level = "error"
            title = "Scenario Execution Failed"
            message = (
                f"Scenario {metrics.scenario} failed: {metrics.error_message or 'Unknown error'}"
            )

            # Check for consecutive failures if configured
            consecutive_failures = self._get_consecutive_failures(metrics.scenario)
            if (
                consecutive_failures
                >= self.alert_config["thresholds"]["failure"]["max_consecutive_failures"]
            ):
                level = "critical"
                title = "Multiple Consecutive Failures"
                message = (
                    f"Scenario {metrics.scenario} failed {consecutive_failures} times consecutively"
                )

            new_alerts.append(
                {
                    "type": "failure",
                    "level": level,
                    "title": title,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                    "run_id": metrics.run_id,
                    "scenario": metrics.scenario,
                    "error_message": metrics.error_message,
                    "consecutive_failures": consecutive_failures,
                }
            )

        # Save new alerts
        if new_alerts:
            alerts.extend(new_alerts)

            # Apply retention policy based on alert levels
            max_alerts = self.alert_config.get("maintenance", {}).get("max_alerts_retained", 1000)
            if len(alerts) > max_alerts:
                alerts = alerts[-max_alerts:]

            self._save_json(self.alerts_file, alerts)

            # Send notifications if configured
            self._send_notifications(new_alerts)

    def _get_daily_cost(self, date: str) -> float:
        """Get total cost for a specific date."""
        costs = self._load_json_dict(self.costs_file)
        return costs.get(date, {}).get("total_usd", 0.0)

    def _get_monthly_cost(self, year_month: str) -> float:
        """Get total cost for a specific month."""
        costs = self._load_json_dict(self.costs_file)
        monthly_total = 0.0

        for date_key, data in costs.items():
            if date_key.startswith(year_month):
                monthly_total += data.get("total_usd", 0.0)

        return monthly_total

    def _get_daily_success_rate(self, date: str) -> float:
        """Get success rate for a specific date."""
        performance = self._load_json_dict(self.performance_file)
        day_data = performance.get(date, {})
        return day_data.get("success_rate", 0.0)

    def _get_consecutive_failures(self, scenario: str) -> int:
        """Get number of consecutive failures for a scenario."""
        runs = self._load_json_list(self.runs_file)

        # Get recent runs for this scenario, sorted by timestamp descending
        scenario_runs = [run for run in runs if run.get("scenario") == scenario]
        scenario_runs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        consecutive_failures = 0
        for run in scenario_runs:
            if run.get("success", False):
                break
            consecutive_failures += 1

        return consecutive_failures

    def _send_notifications(self, alerts: list[dict[str, Any]]) -> None:
        """Send notifications for alerts based on configuration."""
        try:
            # Try to import from current directory first
            import os
            import sys

            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)

            from notifications import NotificationManager

            manager = NotificationManager(self.alert_config)
            manager.send_alerts(alerts)
        except ImportError:
            # Fallback to simple console notifications if notifications module not available
            print("Warning: notifications module not available, using console output only")
            notifications_config = self.alert_config.get("notifications", {})
            for alert in alerts:
                # Console notifications (always enabled for debugging)
                if notifications_config.get("console", {}).get("enabled", True):
                    level_icon = (
                        self.alert_config.get("alert_levels", {})
                        .get(alert.get("level", "info"), {})
                        .get("icon", "ℹ️")
                    )
                    print(
                        f"{level_icon} [{alert.get('level', 'info').upper()}] {alert.get('title', 'Alert')}: {alert.get('message', '')}"
                    )

                # Email notifications (placeholder for future implementation)
                if notifications_config.get("email", {}).get("enabled", False):
                    print(f"📧 Email notification would be sent for: {alert.get('title', 'Alert')}")

                # Slack notifications (placeholder for future implementation)
                if notifications_config.get("slack", {}).get("enabled", False):
                    print(f"💬 Slack notification would be sent for: {alert.get('title', 'Alert')}")

    def get_summary_stats(self, days: int = 7) -> dict[str, Any]:
        """Get summary statistics for recent days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        runs = self._load_json_list(self.runs_file)

        # Filter recent runs
        recent_runs = [
            run for run in runs if datetime.fromisoformat(run["timestamp"]) > cutoff_date
        ]

        if not recent_runs:
            return {"error": "No recent data available"}

        # Calculate stats
        total_cost = sum(run.get("cost_usd", 0) for run in recent_runs)
        total_duration = sum(run.get("duration_seconds", 0) for run in recent_runs)
        successful_runs = sum(1 for run in recent_runs if run.get("success", False))
        total_runs = len(recent_runs)

        return {
            "period_days": days,
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate_pct": (successful_runs / total_runs * 100) if total_runs > 0 else 0,
            "total_cost_usd": total_cost,
            "avg_cost_per_run_usd": total_cost / total_runs if total_runs > 0 else 0,
            "total_duration_seconds": total_duration,
            "avg_duration_seconds": total_duration / total_runs if total_runs > 0 else 0,
            "scenarios_covered": len({run.get("scenario", "") for run in recent_runs}),
        }

    def _load_json_list(self, file_path: Path) -> list[dict]:
        """Load JSON file as list, return empty list if not exists."""
        if not file_path.exists():
            return []
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _load_json_dict(self, file_path: Path) -> dict:
        """Load JSON file as dict, return empty dict if not exists."""
        if not file_path.exists():
            return {}
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_json(self, file_path: Path, data: Any) -> None:
        """Save data to JSON file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def main():
    """CLI interface for metrics collection."""
    parser = argparse.ArgumentParser(description="Collect media automation metrics")
    parser.add_argument("--run-id", required=True, help="GitHub Actions run ID")
    parser.add_argument("--scenario", required=True, help="Scenario identifier (A, B, C, D, E)")
    parser.add_argument(
        "--duration-seconds", type=float, required=True, help="Run duration in seconds"
    )
    parser.add_argument("--cost-usd", type=float, default=0.0, help="Cost in USD")
    parser.add_argument("--tokens-used", type=int, default=0, help="Tokens used")
    parser.add_argument("--video-size-mb", type=float, default=0.0, help="Video file size in MB")
    parser.add_argument("--success", action="store_true", help="Run was successful")
    parser.add_argument("--error-message", help="Error message if failed")
    parser.add_argument("--provider", default="unknown", help="AI provider used")
    parser.add_argument("--workflow-type", default="unknown", help="Workflow type")
    parser.add_argument("--git-commit", help="Git commit hash")
    parser.add_argument("--vhs-version", help="VHS version used")
    parser.add_argument("--timestamp", help="Run timestamp (ISO format)")
    parser.add_argument("--metrics-dir", default="media/metrics", help="Metrics directory")

    args = parser.parse_args()

    # Prepare metrics data
    metrics_data = {
        "run_id": args.run_id,
        "scenario": args.scenario,
        "timestamp": args.timestamp or datetime.now().isoformat(),
        "duration_seconds": args.duration_seconds,
        "cost_usd": args.cost_usd,
        "tokens_used": args.tokens_used,
        "video_size_mb": args.video_size_mb,
        "success": args.success,
        "error_message": args.error_message,
        "provider": args.provider,
        "workflow_type": args.workflow_type,
        "git_commit": args.git_commit or "",
        "vhs_version": args.vhs_version or "",
    }

    # Collect metrics
    collector = MediaMetricsCollector(args.metrics_dir)
    collector.collect_run_metrics(metrics_data)

    print(f"✓ Metrics collected for run {args.run_id}")


if __name__ == "__main__":
    main()
