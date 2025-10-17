#!/usr/bin/env python3
"""
Media Metrics CLI Commands for OpenFatture.

Provides commands for viewing and analyzing media automation metrics.
"""

import sys
from pathlib import Path

import typer
from rich.table import Table

from openfatture.cli.commands.media import console

# Import metrics collector - handle different execution contexts
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
scripts_dir = project_root / "scripts"

# Add scripts directory to path
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(project_root))

try:
    from collect_media_metrics import MediaMetricsCollector
except ImportError as e:
    console.print(f"[red]Error: Could not import MediaMetricsCollector: {e}[/red]")
    console.print(f"[dim]Looked in: {scripts_dir}[/dim]")
    console.print(
        "[dim]Make sure scripts/collect_media_metrics.py exists and is valid Python[/dim]"
    )
    sys.exit(1)

app = typer.Typer(
    name="media-metrics", help="View and analyze media automation metrics", no_args_is_help=True
)


@app.command()
def summary():
    """Show metrics summary for recent runs."""
    try:
        collector = MediaMetricsCollector()

        # Get summary stats for different periods
        week_stats = collector.get_summary_stats(days=7)
        month_stats = collector.get_summary_stats(days=30)

        if "error" in week_stats:
            console.print(f"[yellow]{week_stats['error']}[/yellow]")
            return

        console.print("[bold]📊 Media Automation Metrics Summary[/bold]")
        console.print()

        # Weekly summary
        console.print("[bold]Last 7 Days:[/bold]")
        console.print(f"  • Total Runs: [cyan]{week_stats['total_runs']}[/cyan]")
        console.print(f"  • Success Rate: [green]{week_stats['success_rate_pct']:.1f}%[/green]")
        console.print(f"  • Total Cost: [yellow]${week_stats['total_cost_usd']:.3f}[/yellow]")
        console.print(
            f"  • Avg Cost/Run: [yellow]${week_stats['avg_cost_per_run_usd']:.3f}[/yellow]"
        )
        console.print(f"  • Avg Duration: [blue]{week_stats['avg_duration_seconds']:.1f}s[/blue]")
        console.print(f"  • Scenarios: [magenta]{week_stats['scenarios_covered']}[/magenta]")
        console.print()

        # Monthly summary
        console.print("[bold]Last 30 Days:[/bold]")
        console.print(f"  • Total Runs: [cyan]{month_stats['total_runs']}[/cyan]")
        console.print(f"  • Success Rate: [green]{month_stats['success_rate_pct']:.1f}%[/green]")
        console.print(f"  • Total Cost: [yellow]${month_stats['total_cost_usd']:.3f}[/yellow]")
        console.print(
            f"  • Avg Cost/Run: [yellow]${month_stats['avg_cost_per_run_usd']:.3f}[/yellow]"
        )
        console.print(f"  • Avg Duration: [blue]{month_stats['avg_duration_seconds']:.1f}s[/blue]")
        console.print(f"  • Scenarios: [magenta]{month_stats['scenarios_covered']}[/magenta]")

    except Exception as e:
        console.print(f"[red]Error retrieving metrics: {e}[/red]")


@app.command()
def costs():
    """Show cost analysis and trends."""
    try:
        collector = MediaMetricsCollector()

        # Load cost data
        costs = collector._load_json_dict(collector.costs_file)

        if not costs:
            console.print("[yellow]No cost data available[/yellow]")
            return

        console.print("[bold]💰 Cost Analysis[/bold]")
        console.print()

        # Calculate totals
        total_cost = sum(data.get("total_usd", 0) for data in costs.values())
        total_runs = sum(data.get("runs", 0) for data in costs.values())

        console.print(f"Total Cost (all time): [yellow]${total_cost:.3f}[/yellow]")
        console.print(f"Total Runs (all time): [cyan]{total_runs}[/cyan]")
        console.print(
            f"Average Cost/Run: [yellow]${total_cost / total_runs:.3f if total_runs > 0 else 0:.3f}[/yellow]"
        )
        console.print()

        # Recent daily costs (last 10 days)
        recent_dates = sorted(costs.keys())[-10:]

        if recent_dates:
            console.print("[bold]Recent Daily Costs:[/bold]")

            table = Table()
            table.add_column("Date", style="cyan")
            table.add_column("Cost", style="yellow", justify="right")
            table.add_column("Runs", style="magenta", justify="right")
            table.add_column("Avg/Run", style="green", justify="right")

            for date in recent_dates:
                data = costs[date]
                cost = data.get("total_usd", 0)
                runs = data.get("runs", 0)
                avg_cost = cost / runs if runs > 0 else 0

                table.add_row(date, f"${cost:.3f}", str(runs), f"${avg_cost:.3f}")

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error retrieving cost data: {e}[/red]")


@app.command()
def performance():
    """Show performance metrics and trends."""
    try:
        collector = MediaMetricsCollector()

        # Load performance data
        performance = collector._load_json_dict(collector.performance_file)

        if not performance:
            console.print("[yellow]No performance data available[/yellow]")
            return

        console.print("[bold]⚡ Performance Analysis[/bold]")
        console.print()

        # Overall stats
        total_days = len(performance)
        total_runs = sum(data.get("total_runs", 0) for data in performance.values())
        avg_success_rate = (
            sum(data.get("success_rate", 0) for data in performance.values()) / total_days
            if total_days > 0
            else 0
        )

        console.print(f"Total Days Tracked: [cyan]{total_days}[/cyan]")
        console.print(f"Total Runs: [cyan]{total_runs}[/cyan]")
        console.print(f"Average Success Rate: [green]{avg_success_rate:.1f}%[/green]")
        console.print()

        # Scenario performance (last 7 days)
        recent_dates = sorted(performance.keys())[-7:]

        if recent_dates:
            console.print("[bold]Scenario Performance (Last 7 Days):[/bold]")

            # Collect scenario stats
            scenario_stats = {}
            for date in recent_dates:
                day_data = performance[date]
                for scenario, stats in day_data.get("scenarios", {}).items():
                    if scenario not in scenario_stats:
                        scenario_stats[scenario] = {
                            "total_runs": 0,
                            "successes": 0,
                            "durations": [],
                        }

                    scenario_stats[scenario]["total_runs"] += stats["successes"] + stats["failures"]
                    scenario_stats[scenario]["successes"] += stats["successes"]
                    scenario_stats[scenario]["durations"].extend(stats["durations"])

            table = Table()
            table.add_column("Scenario", style="cyan")
            table.add_column("Runs", style="magenta", justify="right")
            table.add_column("Success Rate", style="green", justify="right")
            table.add_column("Avg Duration", style="blue", justify="right")

            for scenario, stats in sorted(scenario_stats.items()):
                runs = stats["total_runs"]
                success_rate = (stats["successes"] / runs * 100) if runs > 0 else 0
                avg_duration = (
                    sum(stats["durations"]) / len(stats["durations"]) if stats["durations"] else 0
                )

                table.add_row(
                    scenario.upper(), str(runs), f"{success_rate:.1f}%", f"{avg_duration:.1f}s"
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error retrieving performance data: {e}[/red]")


@app.command()
def alerts():
    """Show active alerts and warnings."""
    try:
        collector = MediaMetricsCollector()

        # Load alerts
        alerts = collector._load_json_list(collector.alerts_file)

        if not alerts:
            console.print("[green]✓ No active alerts[/green]")
            return

        console.print("[bold]🚨 Active Alerts[/bold]")
        console.print()

        # Group alerts by type
        alert_counts = {"cost": 0, "performance": 0, "failure": 0}

        for alert in alerts[-20:]:  # Show last 20 alerts
            alert_type = alert.get("type", "unknown")
            alert_counts[alert_type] += 1

        console.print(f"Cost Alerts: [yellow]{alert_counts['cost']}[/yellow]")
        console.print(f"Performance Alerts: [blue]{alert_counts['performance']}[/blue]")
        console.print(f"Failure Alerts: [red]{alert_counts['failure']}[/red]")
        console.print()

        # Show recent alerts
        console.print("[bold]Recent Alerts:[/bold]")

        for alert in alerts[-10:]:  # Show last 10 alerts
            level = alert.get("level", "info")
            timestamp = alert.get("timestamp", "")[:16]  # YYYY-MM-DD HH:MM

            if level == "error":
                icon = "❌"
                style = "red"
            elif level == "warning":
                icon = "⚠️"
                style = "yellow"
            else:
                icon = "ℹ️"
                style = "blue"

            console.print(
                f"[{style}]{icon} {timestamp}: {alert.get('message', 'Unknown alert')}[/{style}]"
            )

    except Exception as e:
        console.print(f"[red]Error retrieving alerts: {e}[/red]")


@app.command()
def dashboard():
    """Generate a simple dashboard summary."""
    try:
        collector = MediaMetricsCollector()

        # Get various metrics
        week_stats = collector.get_summary_stats(days=7)
        costs = collector._load_json_dict(collector.costs_file)
        alerts_list = collector._load_json_list(collector.alerts_file)

        console.print("[bold]🎬 OpenFatture Media Dashboard[/bold]")
        console.print()

        # Cost overview
        if "error" not in week_stats:
            console.print("💰 [bold]Cost Overview (7 days)[/bold]")
            console.print(f"   Total: [yellow]${week_stats['total_cost_usd']:.3f}[/yellow]")
            console.print(
                f"   Budget: [green]$7.00 remaining[/green] (${7 - week_stats['total_cost_usd']:.3f} left)"
            )
            console.print()

        # Performance overview
        if "error" not in week_stats:
            console.print("⚡ [bold]Performance (7 days)[/bold]")
            console.print(f"   Success Rate: [green]{week_stats['success_rate_pct']:.1f}%[/green]")
            console.print(
                f"   Avg Duration: [blue]{week_stats['avg_duration_seconds']:.1f}s[/blue]"
            )
            console.print(f"   Total Runs: [cyan]{week_stats['total_runs']}[/cyan]")
            console.print()

        # Recent alerts
        if alerts_list:
            recent_alerts = [a for a in alerts_list[-5:]]  # Last 5 alerts
            console.print("🚨 [bold]Recent Alerts[/bold]")
            for alert in recent_alerts:
                level = alert.get("level", "info")
                message = alert.get("message", "")[:60] + (
                    "..." if len(alert.get("message", "")) > 60 else ""
                )

                if level == "error":
                    console.print(f"   [red]❌ {message}[/red]")
                elif level == "warning":
                    console.print(f"   [yellow]⚠️  {message}[/yellow]")
                else:
                    console.print(f"   [blue]ℹ️  {message}[/blue]")
            console.print()

        # Data freshness
        runs = collector._load_json_list(collector.runs_file)
        if runs:
            latest_run = max(runs, key=lambda x: x.get("collected_at", ""))
            last_update = latest_run.get("collected_at", "")[:16]
            console.print(f"[dim]Last updated: {last_update}[/dim]")
        else:
            console.print("[dim]No data available yet[/dim]")

    except Exception as e:
        console.print(f"[red]Error generating dashboard: {e}[/red]")


if __name__ == "__main__":
    app()
