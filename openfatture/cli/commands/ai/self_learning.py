"""Self-learning system status command."""

from rich.table import Table

from ._app import app, console


@app.command("status")
def self_learning_status() -> None:
    """Show comprehensive self-learning system status.

    Displays unified dashboard of all self-learning components:
    - RAG Auto-Update service
    - ML Model Retraining scheduler
    - Feedback Collection statistics

    This provides a quick overview of the entire self-learning system health.

    Example:
        openfatture ai status
    """
    from openfatture.ai.feedback import FeedbackAnalytics
    from openfatture.ai.ml.retraining import get_scheduler
    from openfatture.ai.rag.auto_update import get_auto_indexing_service

    console.print("\n[bold blue]🤖 Self-Learning System Dashboard[/bold blue]\n")

    # RAG Auto-Update Status
    console.print("[bold cyan]═══ RAG Auto-Update ═══[/bold cyan]\n")
    try:
        service = get_auto_indexing_service()
        status = service.get_status()

        # Status indicators
        enabled_icon = "✅" if status["enabled"] else "❌"
        running_icon = "🟢" if status["running"] else "⚫"

        rag_table = Table(show_header=False, box=None)
        rag_table.add_column("Metric", style="dim")
        rag_table.add_column("Value")

        rag_table.add_row("Enabled:", f"{enabled_icon} {status['enabled']}")
        rag_table.add_row("Running:", f"{running_icon} {status['running']}")

        config = status.get("config", {})
        tracked = config.get("tracked_entities", [])
        if tracked:
            rag_table.add_row("Tracking:", ", ".join(tracked))

        queue_stats = status.get("queue_stats", {})
        rag_table.add_row("Processed:", str(queue_stats.get("total_processed", 0)))

        tracker_stats = status.get("tracker_stats", {})
        pending_total = sum(tracker_stats.values()) if tracker_stats else 0
        rag_table.add_row("Pending:", str(pending_total))

        console.print(rag_table)
        console.print()

        # Show pending by type if any
        if tracker_stats:
            console.print("[dim]Pending by type:[/dim]")
            for entity_type, count in tracker_stats.items():
                console.print(f"  • {entity_type}: {count}")
            console.print()

    except Exception as e:
        console.print(f"[yellow]⚠️  Could not fetch RAG auto-update status: {e}[/yellow]\n")

    # ML Retraining Status
    console.print("[bold cyan]═══ ML Model Retraining ═══[/bold cyan]\n")
    try:
        scheduler = get_scheduler()
        status = scheduler.get_status()

        # Status indicators
        enabled_icon = "✅" if status["enabled"] else "❌"
        running_icon = "🟢" if status["running"] else "⚫"

        retrain_table = Table(show_header=False, box=None)
        retrain_table.add_column("Metric", style="dim")
        retrain_table.add_column("Value")

        retrain_table.add_row("Enabled:", f"{enabled_icon} {status['enabled']}")
        retrain_table.add_row("Running:", f"{running_icon} {status['running']}")

        if status.get("last_retrain_time"):
            retrain_table.add_row("Last Retrain:", status["last_retrain_time"])

        if status.get("next_run_time"):
            retrain_table.add_row("Next Check:", status["next_run_time"])

        # Trigger status
        trigger_status = status.get("trigger_status", {})
        should_trigger = trigger_status.get("should_trigger", False)
        trigger_icon = "⚠️" if should_trigger else "✅"
        retrain_table.add_row("Ready to Train:", f"{trigger_icon} {should_trigger}")

        # Feedback count
        feedback_stats = trigger_status.get("feedback_stats", {})
        unprocessed = feedback_stats.get("unprocessed_count", 0)
        threshold = feedback_stats.get("threshold", 0)
        retrain_table.add_row("Feedback:", f"{unprocessed}/{threshold}")

        console.print(retrain_table)
        console.print()

        # Show active triggers if any
        if trigger_status.get("triggers"):
            console.print("[yellow]Active triggers:[/yellow]")
            for trigger in trigger_status["triggers"][:3]:  # Show first 3
                console.print(f"  • {trigger['message']}")
            console.print()

    except Exception as e:
        console.print(f"[yellow]⚠️  Could not fetch retraining status: {e}[/yellow]\n")

    # Feedback Collection Stats
    console.print("[bold cyan]═══ Feedback Collection ═══[/bold cyan]\n")
    try:
        analytics = FeedbackAnalytics()

        # Last 7 days stats
        user_stats = analytics.get_user_feedback_stats(days=7)
        pred_stats = analytics.get_prediction_feedback_stats(days=7)

        feedback_table = Table(show_header=False, box=None)
        feedback_table.add_column("Metric", style="dim")
        feedback_table.add_column("Value")

        # User feedback
        feedback_table.add_row("User Feedback (7d):", str(user_stats.total_feedback))
        if user_stats.average_rating:
            stars = "⭐" * min(5, int(user_stats.average_rating))
            feedback_table.add_row("Avg Rating:", f"{stars} ({user_stats.average_rating:.1f}/5)")

        # Prediction feedback
        feedback_table.add_row("Predictions (7d):", str(pred_stats.total_predictions))
        feedback_table.add_row("Acceptance Rate:", f"{pred_stats.acceptance_rate:.1f}%")
        feedback_table.add_row("Unprocessed:", str(pred_stats.unprocessed_count))

        console.print(feedback_table)
        console.print()

        # Top agent types if available
        if user_stats.by_agent:
            console.print("[dim]Top agents:[/dim]")
            for agent, count in list(user_stats.by_agent.items())[:3]:
                console.print(f"  • {agent}: {count}")
            console.print()

    except Exception as e:
        console.print(f"[yellow]⚠️  Could not fetch feedback stats: {e}[/yellow]\n")

    # Footer with helpful commands
    console.print("[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]")
    console.print("\n[bold]Detailed Commands:[/bold]")
    console.print("  • RAG Auto-Update:    [cyan]openfatture ai auto-update status[/cyan]")
    console.print("  • ML Retraining:      [cyan]openfatture ai retrain status[/cyan]")
    console.print("  • Feedback Analysis:  [cyan]openfatture ai feedback stats[/cyan]")
    console.print("\n[dim]See docs/SELF_LEARNING.md for complete documentation[/dim]\n")
