"""RAG auto-update service commands."""

import typer
from rich.table import Table

from openfatture.utils.async_bridge import run_async

from ._app import auto_update_app, console


@auto_update_app.command("status")
def auto_update_status() -> None:
    """Show RAG auto-update service status.

    Displays:
    - Service enabled/running status
    - Queue statistics (pending changes, processed count)
    - Configuration settings
    - Tracker statistics

    Example:
        openfatture ai auto-update status
    """
    from openfatture.ai.rag.auto_update import get_auto_indexing_service

    service = get_auto_indexing_service()
    status = service.get_status()

    console.print("\n[bold blue]🔄 RAG Auto-Update Service Status[/bold blue]\n")

    # Main status
    status_table = Table(show_header=False, box=None)
    status_table.add_column("Setting", style="cyan bold")
    status_table.add_column("Value")

    # Enabled/Running
    enabled_icon = "✅" if status["enabled"] else "❌"
    running_icon = "🟢" if status["running"] else "⚫"

    status_table.add_row("Enabled:", f"{enabled_icon} {status['enabled']}")
    status_table.add_row("Running:", f"{running_icon} {status['running']}")

    console.print(status_table)
    console.print()

    # Configuration
    config = status.get("config", {})
    console.print("[bold]Configuration:[/bold]")
    console.print(f"  Batch Size: {config.get('batch_size', 0)}")
    console.print(f"  Debounce: {config.get('debounce_seconds', 0)}s")
    console.print(f"  Incremental Updates: {config.get('incremental_updates', False)}")
    tracked = config.get("tracked_entities", [])
    if tracked:
        console.print(f"  Tracked Entities: {', '.join(tracked)}")
    console.print()

    # Queue statistics
    queue_stats = status.get("queue_stats", {})
    console.print("[bold]Queue Statistics:[/bold]")
    console.print(f"  Running: {queue_stats.get('running', False)}")
    console.print(f"  Total Processed: {queue_stats.get('total_processed', 0)}")
    console.print(f"  Total Batches: {queue_stats.get('total_batches', 0)}")
    if queue_stats.get("last_process_time_ms"):
        console.print(f"  Last Process Time: {queue_stats['last_process_time_ms']:.0f}ms")
    console.print()

    # Tracker statistics
    tracker_stats = status.get("tracker_stats", {})
    if tracker_stats:
        console.print("[bold]Tracker Statistics:[/bold]")
        for entity_type, count in tracker_stats.items():
            console.print(f"  {entity_type}: {count} pending")
        console.print()


@auto_update_app.command("start")
def auto_update_start() -> None:
    """Start the RAG auto-indexing service.

    Starts background processing of data changes for automatic
    reindexing of the vector store.

    Example:
        openfatture ai auto-update start
    """

    from openfatture.ai.rag.auto_update import get_auto_indexing_service

    service = get_auto_indexing_service()

    console.print("\n[bold blue]🔄 Starting RAG Auto-Update Service[/bold blue]\n")

    with console.status("[bold green]Starting service..."):
        run_async(service.start())

    console.print("[bold green]✅ Service started successfully[/bold green]\n")


@auto_update_app.command("stop")
def auto_update_stop() -> None:
    """Stop the RAG auto-indexing service.

    Stops background processing and optionally persists pending
    changes to disk based on configuration.

    Example:
        openfatture ai auto-update stop
    """

    from openfatture.ai.rag.auto_update import get_auto_indexing_service

    service = get_auto_indexing_service()

    console.print("\n[bold blue]🔄 Stopping RAG Auto-Update Service[/bold blue]\n")

    with console.status("[bold yellow]Stopping service..."):
        run_async(service.stop())

    console.print("[bold yellow]⏸️  Service stopped[/bold yellow]\n")


@auto_update_app.command("queue")
def auto_update_queue() -> None:
    """Show detailed queue statistics.

    Displays pending changes by entity type and processing metrics.

    Example:
        openfatture ai auto-update queue
    """
    from openfatture.ai.rag.auto_update import get_change_tracker, get_reindex_queue

    tracker = get_change_tracker()
    queue = get_reindex_queue()

    console.print("\n[bold blue]📊 RAG Auto-Update Queue Statistics[/bold blue]\n")

    # Queue stats
    queue_stats = queue.get_stats()
    stats_table = Table(show_header=False, box=None)
    stats_table.add_column("Metric", style="cyan bold")
    stats_table.add_column("Value")

    stats_table.add_row("Running:", "🟢 Yes" if queue_stats["running"] else "⚫ No")
    stats_table.add_row("Total Processed:", str(queue_stats["total_processed"]))
    stats_table.add_row("Total Batches:", str(queue_stats["total_batches"]))
    if queue_stats.get("last_process_time_ms"):
        stats_table.add_row("Last Process Time:", f"{queue_stats['last_process_time_ms']:.0f}ms")

    console.print(stats_table)
    console.print()

    # Tracker stats (pending changes)
    tracker_stats = tracker.get_queue_stats()
    console.print("[bold]Pending Changes:[/bold]")
    if tracker_stats:
        pending_table = Table(box=None)
        pending_table.add_column("Entity Type", style="cyan")
        pending_table.add_column("Count", justify="right", style="yellow")

        total_pending = 0
        for entity_type, count in tracker_stats.items():
            pending_table.add_row(entity_type, str(count))
            total_pending += count

        console.print(pending_table)
        console.print(f"\n[bold]Total Pending:[/bold] {total_pending}")
    else:
        console.print("[dim]No pending changes[/dim]")
    console.print()


@auto_update_app.command("manual")
def auto_update_manual(
    entity_type: str = typer.Argument(..., help="Entity type to reindex (invoice, client)"),
    entity_ids: list[int] = typer.Argument(..., help="Entity IDs to reindex (space-separated)"),
) -> None:
    """Manually trigger reindexing for specific entities.

    Forces immediate reindexing of specified invoices or clients,
    bypassing the normal queue processing.

    Examples:
        openfatture ai auto-update manual invoice 1 2 3
        openfatture ai auto-update manual client 123
    """

    from openfatture.ai.rag.auto_update import get_auto_indexing_service

    service = get_auto_indexing_service()

    console.print("\n[bold blue]🔄 Manual Reindexing[/bold blue]\n")
    console.print(f"[bold]Entity Type:[/bold] {entity_type}")
    console.print(f"[bold]Entity IDs:[/bold] {', '.join(map(str, entity_ids))}\n")

    with console.status("[bold green]Reindexing..."):
        result = run_async(service.manual_reindex(entity_type, entity_ids))

    # Display results
    console.print("[bold green]✅ Reindexing completed[/bold green]\n")
    console.print(f"[cyan]Requested:[/cyan] {result['requested_count']}")
    console.print(f"[green]Successful:[/green] {len(result['successful'])}")
    console.print(f"[red]Failed:[/red] {len(result['failed'])}")

    if result["successful"]:
        console.print("\n[bold green]Successfully reindexed:[/bold green]")
        for entity_id in result["successful"][:10]:  # Show first 10
            console.print(f"  • {entity_type} {entity_id}")
        if len(result["successful"]) > 10:
            console.print(f"  ... and {len(result['successful']) - 10} more")

    if result["failed"]:
        console.print("\n[bold red]Failed to reindex:[/bold red]")
        for failure in result["failed"][:5]:  # Show first 5 errors
            console.print(f"  • {entity_type} {failure['entity_id']}: {failure['error']}")
        if len(result["failed"]) > 5:
            console.print(f"  ... and {len(result['failed']) - 5} more")

    console.print()
