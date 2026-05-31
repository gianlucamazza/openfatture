"""ML model retraining commands."""

import typer
from rich.table import Table

from openfatture.utils.async_bridge import run_async

from ._app import console, retrain_app


@retrain_app.command("trigger")
def retrain_trigger(
    force: bool = typer.Option(
        False, "--force", "-f", help="Force retraining even if triggers not met"
    ),
) -> None:
    """Manually trigger model retraining.

    Checks retraining triggers and executes retraining if conditions are met.
    Use --force to skip trigger checks.

    Examples:
        openfatture ai retrain trigger
        openfatture ai retrain trigger --force
    """
    from openfatture.ai.ml.retraining import get_scheduler

    scheduler = get_scheduler()

    console.print("\n[bold blue]🔄 Manual Model Retraining[/bold blue]\n")

    # Run async retraining

    with console.status("[bold green]Triggering retraining..."):
        result = run_async(scheduler.trigger_manual_retraining("cash_flow", force=force))

    # Display results
    if result["success"]:
        console.print(f"[bold green]✅ {result['message']}[/bold green]\n")

        if result.get("deployed"):
            console.print(f"[cyan]Version ID:[/cyan] {result.get('version_id')}")
            console.print(f"[cyan]Feedback processed:[/cyan] {result.get('feedback_count')}")

            if result.get("evaluation"):
                eval_data = result["evaluation"]
                metrics = eval_data.get("metrics", {})

                console.print("\n[bold]New Model Metrics:[/bold]")
                console.print(f"  MAE: {metrics.get('mae', 0):.2f} days")
                console.print(f"  RMSE: {metrics.get('rmse', 0):.2f} days")
                console.print(f"  Confidence: {metrics.get('avg_confidence', 0):.1%}")

                if eval_data.get("comparison"):
                    console.print("\n[bold]Improvement:[/bold]")
                    for metric, data in eval_data["comparison"].items():
                        if data["is_better"]:
                            console.print(f"  {metric.upper()}: +{data['improvement_pct']:.1f}%")
        else:
            console.print(f"[dim]Model not deployed: {result.get('message')}[/dim]")
    else:
        console.print(f"[bold red]❌ {result['message']}[/bold red]\n")


@retrain_app.command("status")
def retrain_status() -> None:
    """Show retraining scheduler status and trigger conditions.

    Displays:
    - Scheduler running status
    - Next scheduled check
    - Trigger conditions (feedback count, time elapsed)
    - Last retraining time

    Example:
        openfatture ai retrain status
    """
    from openfatture.ai.ml.retraining import get_scheduler

    scheduler = get_scheduler()
    status = scheduler.get_status()

    console.print("\n[bold blue]🔄 Retraining Scheduler Status[/bold blue]\n")

    # Main status
    status_table = Table(show_header=False, box=None)
    status_table.add_column("Setting", style="cyan bold")
    status_table.add_column("Value")

    # Enabled/Running
    enabled_icon = "✅" if status["enabled"] else "❌"
    running_icon = "🟢" if status["running"] else "⚫"

    status_table.add_row("Enabled:", f"{enabled_icon} {status['enabled']}")
    status_table.add_row("Running:", f"{running_icon} {status['running']}")
    status_table.add_row("Dry Run:", "Yes" if status["dry_run"] else "No")
    status_table.add_row("Check Interval:", f"{status['interval_hours']}h")

    if status.get("last_check_time"):
        status_table.add_row("Last Check:", status["last_check_time"])

    if status.get("last_retrain_time"):
        status_table.add_row("Last Retrain:", status["last_retrain_time"])

    if status.get("next_run_time"):
        status_table.add_row("Next Run:", status["next_run_time"])

    status_table.add_row("Retraining Active:", "Yes" if status["retraining_in_progress"] else "No")

    console.print(status_table)
    console.print()

    # Trigger status
    trigger_status = status.get("trigger_status", {})
    should_trigger = trigger_status.get("should_trigger", False)

    if should_trigger:
        console.print("[bold yellow]⚠️  Retraining Triggers Met[/bold yellow]\n")
    else:
        console.print("[bold green]✅ No Retraining Needed[/bold green]\n")

    # Feedback stats
    feedback_stats = trigger_status.get("feedback_stats", {})
    console.print("[bold]Feedback Status:[/bold]")
    console.print(f"  Unprocessed: {feedback_stats.get('unprocessed_count', 0)}")
    console.print(f"  Threshold: {feedback_stats.get('threshold', 0)}")
    ready_icon = "✅" if feedback_stats.get("ready") else "❌"
    console.print(f"  Ready: {ready_icon}")
    console.print()

    # Time stats
    time_stats = trigger_status.get("time_stats", {})
    console.print("[bold]Time Status:[/bold]")
    if time_stats.get("last_training"):
        console.print(f"  Last Training: {time_stats['last_training']}")
    if time_stats.get("days_since_training") is not None:
        console.print(f"  Days Elapsed: {time_stats['days_since_training']}")
    console.print(f"  Threshold: {time_stats.get('threshold_days', 0)} days")
    ready_icon = "✅" if time_stats.get("ready") else "❌"
    console.print(f"  Ready: {ready_icon}")
    console.print()

    # Active triggers
    if trigger_status.get("triggers"):
        console.print("[bold yellow]Active Triggers:[/bold yellow]")
        for trigger in trigger_status["triggers"]:
            console.print(f"  • {trigger['message']}")
        console.print()


@retrain_app.command("history")
def retrain_history(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of versions to show"),
) -> None:
    """Show model version history.

    Displays all saved model versions with metrics and creation times.

    Example:
        openfatture ai retrain history
        openfatture ai retrain history --limit 5
    """
    from openfatture.ai.ml.retraining import ModelVersionManager

    version_manager = ModelVersionManager()
    versions = version_manager.list_versions("cash_flow")

    console.print("\n[bold blue]📦 Model Version History[/bold blue]\n")

    if not versions:
        console.print("[dim]No model versions found.[/dim]\n")
        return

    # Version table
    versions_table = Table(title="Cash Flow Model Versions", box=None)
    versions_table.add_column("Version ID", style="cyan")
    versions_table.add_column("Created", style="white")
    versions_table.add_column("MAE", style="green")
    versions_table.add_column("RMSE", style="green")
    versions_table.add_column("Notes", style="dim", no_wrap=False, max_width=40)

    for version in versions[:limit]:
        created = version.created_at.strftime("%Y-%m-%d %H:%M")
        mae = version.metrics.get("mae", "N/A")
        rmse = version.metrics.get("rmse", "N/A")

        mae_str = f"{mae:.2f}" if isinstance(mae, int | float) else mae
        rmse_str = f"{rmse:.2f}" if isinstance(rmse, int | float) else rmse

        notes = version.notes or ""

        versions_table.add_row(
            version.version_id,
            created,
            mae_str,
            rmse_str,
            notes,
        )

    console.print(versions_table)
    console.print()

    if len(versions) > limit:
        console.print(
            f"[dim]Showing {limit} of {len(versions)} versions. Use --limit to see more.[/dim]\n"
        )


@retrain_app.command("rollback")
def retrain_rollback(
    version_id: str = typer.Argument(..., help="Version ID to rollback to"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Rollback to a previous model version.

    Restores a previous model version to the current model location.
    This overwrites the current model.

    Example:
        openfatture ai retrain rollback 20250116_143022
        openfatture ai retrain rollback 20250116_143022 --yes
    """
    from openfatture.ai.ml.retraining import ModelVersionManager

    version_manager = ModelVersionManager()

    console.print("\n[bold blue]🔄 Model Rollback[/bold blue]\n")

    # Verify version exists
    try:
        version = version_manager.load_version("cash_flow", version_id, restore_to_current=False)
    except FileNotFoundError:
        console.print(f"[bold red]❌ Version '{version_id}' not found[/bold red]\n")
        raise typer.Exit(1)

    # Show version info
    console.print(f"[bold]Rolling back to version:[/bold] {version_id}")
    console.print(f"[bold]Created:[/bold] {version.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if version.notes:
        console.print(f"[bold]Notes:[/bold] {version.notes}")

    # Show metrics
    if version.metrics:
        console.print("\n[bold]Metrics:[/bold]")
        for key, value in version.metrics.items():
            if isinstance(value, int | float):
                console.print(f"  {key}: {value:.2f}")

    console.print()

    # Confirmation
    if not confirm:
        proceed = typer.confirm("⚠️  This will overwrite the current model. Continue?")
        if not proceed:
            console.print("[dim]Rollback cancelled.[/dim]\n")
            raise typer.Exit(0)

    # Perform rollback
    try:
        version_manager.rollback_to_version("cash_flow", version_id)
        console.print(
            f"[bold green]✅ Successfully rolled back to version {version_id}[/bold green]\n"
        )
    except Exception as e:
        console.print(f"[bold red]❌ Rollback failed: {e}[/bold red]\n")
        raise typer.Exit(1)
