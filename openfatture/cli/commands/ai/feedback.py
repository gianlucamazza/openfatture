"""User feedback and ML prediction feedback commands."""

from pathlib import Path

import typer
from rich.table import Table

from ._app import console, feedback_app


@feedback_app.command("stats")
def feedback_stats(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
) -> None:
    """Show user feedback and prediction feedback statistics."""
    from openfatture.ai.feedback import FeedbackAnalytics

    analytics = FeedbackAnalytics()

    # User feedback stats
    console.print("\n[bold blue]User Feedback Statistics[/bold blue]\n")
    user_stats = analytics.get_user_feedback_stats(days=days)

    stats_table = Table(title=f"Last {days} Days", show_header=False)
    stats_table.add_column("Metric", style="cyan bold")
    stats_table.add_column("Value", style="white")

    stats_table.add_row("Total Feedback", str(user_stats.total_feedback))
    if user_stats.average_rating:
        stars = "" * int(user_stats.average_rating)
        stats_table.add_row("Average Rating", f"{stars} ({user_stats.average_rating:.1f}/5)")
    stats_table.add_row("Total Corrections", str(user_stats.total_corrections))
    stats_table.add_row("Recent (7 days)", str(user_stats.recent_feedback_count))

    console.print(stats_table)
    console.print()

    # By type
    if user_stats.by_type:
        console.print("[bold cyan]By Type:[/bold cyan]")
        for feedback_type, count in user_stats.by_type.items():
            console.print(f"  • {feedback_type}: {count}")
        console.print()

    # By agent
    if user_stats.by_agent:
        console.print("[bold cyan]By Agent:[/bold cyan]")
        for agent, count in user_stats.by_agent.items():
            console.print(f"  • {agent}: {count}")
        console.print()

    # Prediction feedback stats
    console.print("[bold blue]ML Prediction Feedback Statistics[/bold blue]\n")
    pred_stats = analytics.get_prediction_feedback_stats(days=days)

    pred_table = Table(title=f"Last {days} Days", show_header=False)
    pred_table.add_column("Metric", style="cyan bold")
    pred_table.add_column("Value", style="white")

    pred_table.add_row("Total Predictions", str(pred_stats.total_predictions))
    pred_table.add_row("Acceptance Rate", f"{pred_stats.acceptance_rate:.1f}%")
    if pred_stats.average_confidence:
        pred_table.add_row("Avg Confidence", f"{pred_stats.average_confidence:.1%}")
    pred_table.add_row("Total Corrections", str(pred_stats.total_corrections))
    pred_table.add_row("Unprocessed (for retraining)", str(pred_stats.unprocessed_count))

    console.print(pred_table)
    console.print()

    # By prediction type
    if pred_stats.by_type:
        console.print("[bold cyan]By Prediction Type:[/bold cyan]")
        for pred_type, count in pred_stats.by_type.items():
            console.print(f"  • {pred_type}: {count}")
        console.print()

    # By model version
    if pred_stats.by_model_version:
        console.print("[bold cyan]By Model Version:[/bold cyan]")
        version_table = Table(box=None)
        version_table.add_column("Version", style="cyan")
        version_table.add_column("Total", style="white")
        version_table.add_column("Acceptance", style="green")
        version_table.add_column("Avg Confidence", style="yellow")

        for version, data in pred_stats.by_model_version.items():
            version_table.add_row(
                version,
                str(data["total"]),
                f"{data['acceptance_rate']:.1f}%",
                f"{data['avg_confidence']:.1%}" if data["avg_confidence"] else "N/A",
            )

        console.print(version_table)
        console.print()


@feedback_app.command("export")
def feedback_export(
    output: Path = typer.Option("feedback_export.json", "--output", "-o", help="Output file path"),
    days: int = typer.Option(30, "--days", "-d", help="Number of days to export"),
) -> None:
    """Export feedback data to JSON file."""
    from datetime import datetime, timedelta

    from openfatture.ai.feedback import FeedbackService

    service = FeedbackService()
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # This is a simplified export - in production, you'd query with date filters
    console.print(f"\n[bold blue]Exporting feedback data (last {days} days)[/bold blue]\n")

    # Export user feedback (simplified - would need proper date filtering in service)
    console.print("[dim]Note: Full export functionality requires additional service methods[/dim]")
    console.print(f"[green]Export location: {output}[/green]\n")


@feedback_app.command("analyze")
def feedback_analyze(
    limit: int = typer.Option(20, "--limit", "-l", help="Number of patterns to show"),
    threshold: float = typer.Option(
        0.6, "--threshold", "-t", help="Confidence threshold for low-confidence predictions"
    ),
) -> None:
    """Analyze feedback patterns and low-confidence predictions."""
    from openfatture.ai.feedback import FeedbackAnalytics

    analytics = FeedbackAnalytics()

    # Correction patterns
    console.print("\n[bold blue]Correction Patterns Analysis[/bold blue]\n")
    patterns = analytics.get_correction_patterns(limit=limit)

    if patterns:
        patterns_table = Table(title="Recent Corrections", box=None)
        patterns_table.add_column("Agent", style="cyan")
        patterns_table.add_column("Feature", style="yellow")
        patterns_table.add_column("Original", style="white", no_wrap=False, max_width=40)
        patterns_table.add_column("Corrected", style="green", no_wrap=False, max_width=40)

        for pattern in patterns[:10]:  # Show first 10
            patterns_table.add_row(
                pattern.get("agent_type", "N/A"),
                pattern.get("feature_name", "N/A"),
                pattern.get("original", "")[:50] + "..." if pattern.get("original") else "",
                pattern.get("corrected", "")[:50] + "..." if pattern.get("corrected") else "",
            )

        console.print(patterns_table)
        console.print()
    else:
        console.print("[dim]No correction patterns found.[/dim]\n")

    # Low confidence predictions
    console.print("[bold blue]Low Confidence Predictions (Requires Review)[/bold blue]\n")
    low_conf = analytics.get_low_confidence_predictions(threshold=threshold, limit=limit)

    if low_conf:
        low_conf_table = Table(title=f"Confidence < {threshold:.0%}", box=None)
        low_conf_table.add_column("ID", style="dim")
        low_conf_table.add_column("Type", style="cyan")
        low_conf_table.add_column("Entity", style="yellow")
        low_conf_table.add_column("Confidence", style="red")
        low_conf_table.add_column("Accepted", style="green")

        for pred in low_conf:
            low_conf_table.add_row(
                str(pred["id"]),
                pred["prediction_type"],
                pred["entity"],
                f"{pred['confidence']:.1%}" if pred["confidence"] else "N/A",
                "" if pred["user_accepted"] else "",
            )

        console.print(low_conf_table)
        console.print()

        console.print(
            f"[bold yellow]Tip:[/bold yellow] These {len(low_conf)} predictions need human review "
            "for model improvement.\n"
        )
    else:
        console.print(
            f"[dim]No low-confidence predictions found (threshold: {threshold:.0%}).[/dim]\n"
        )
