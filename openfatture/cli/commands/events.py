"""Event history CLI commands."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from openfatture.core.events.analytics import EventAnalytics
from openfatture.core.events.repository import EventRepository
from openfatture.storage.database.base import init_db
from openfatture.utils.config import get_settings

app = typer.Typer(help="View and analyze event history", no_args_is_help=True)
console = Console()


def ensure_db() -> None:
    """Ensure database is initialized."""
    settings = get_settings()
    init_db(str(settings.database_url))


@app.command("list")
def list_events(
    event_type: str | None = typer.Option(None, "--type", "-t", help="Filter by event type"),
    entity_type: str | None = typer.Option(
        None, "--entity", "-e", help="Filter by entity type (fattura, cliente, pagamento, etc.)"
    ),
    entity_id: int | None = typer.Option(None, "--entity-id", help="Filter by entity ID"),
    last_hours: int | None = typer.Option(
        None, "--last-hours", "-h", help="Show events from last N hours"
    ),
    last_days: int | None = typer.Option(
        None, "--last-days", "-d", help="Show events from last N days"
    ),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of events to show"),
) -> None:
    """List recent events with optional filtering."""
    ensure_db()

    # Calculate date range
    start_date = None
    if last_hours:
        start_date = datetime.now() - timedelta(hours=last_hours)
    elif last_days:
        start_date = datetime.now() - timedelta(days=last_days)

    # Query events
    repo = EventRepository()
    try:
        events = repo.get_all(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            start_date=start_date,
            limit=limit,
        )

        if not events:
            console.print("[yellow]No events found matching the criteria[/yellow]")
            return

        # Create table
        table = Table(title=f"Event History ({len(events)} events)", show_lines=False, expand=False)
        table.add_column("Timestamp", style="cyan", width=19)
        table.add_column("Event Type", style="bold white", width=25)
        table.add_column("Entity", style="green", width=15)
        table.add_column("Summary", style="white")

        for event in events:
            # Format timestamp
            timestamp = event.occurred_at.strftime("%Y-%m-%d %H:%M:%S")

            # Format entity
            entity = f"{event.entity_type or '-'}:{event.entity_id or '-'}"

            # Create summary from event data
            try:
                event_data = json.loads(event.event_data)
                summary = repo._create_event_summary(event.event_type, event_data)
            except Exception:
                summary = event.event_type

            # Add row
            table.add_row(timestamp, event.event_type, entity, summary)

        console.print(table)

        # Show filter summary if filters applied
        if event_type or entity_type or entity_id or start_date:
            filter_info = []
            if event_type:
                filter_info.append(f"type={event_type}")
            if entity_type:
                filter_info.append(f"entity={entity_type}")
            if entity_id:
                filter_info.append(f"id={entity_id}")
            if start_date:
                filter_info.append(f"since={start_date.strftime('%Y-%m-%d %H:%M')}")

            console.print(f"\n[dim]Filters: {', '.join(filter_info)}[/dim]")

    finally:
        repo.close()


@app.command("show")
def show_event(
    event_id: str = typer.Argument(..., help="Event ID (UUID)"),
) -> None:
    """
    Show detailed information about a specific event.

    Displays complete event details including metadata, entity information,
    and structured event data in readable format.

    Examples:
        openfatture events show 123e4567-e89b-12d3-a456-426614174000
    """
    ensure_db()

    repo = EventRepository()
    try:
        event = repo.get_by_id(event_id)

        if not event:
            console.print(f"[red]Event with ID '{event_id}' not found[/red]")
            raise typer.Exit(1)

        # Parse event data
        try:
            event_data = json.loads(event.event_data)
            event_data_formatted = json.dumps(event_data, indent=2)
        except Exception:
            event_data_formatted = event.event_data

        # Parse metadata
        metadata_formatted = None
        if event.metadata_json:
            try:
                metadata = json.loads(event.metadata_json)
                metadata_formatted = json.dumps(metadata, indent=2)
            except Exception:
                metadata_formatted = event.metadata_json

        # Create detailed view
        details = f"""[bold cyan]Event ID:[/bold cyan] {event.event_id}
[bold cyan]Event Type:[/bold cyan] {event.event_type}
[bold cyan]Occurred At:[/bold cyan] {event.occurred_at.strftime("%Y-%m-%d %H:%M:%S")}
[bold cyan]Published At:[/bold cyan] {event.published_at.strftime("%Y-%m-%d %H:%M:%S")}

[bold cyan]Entity Type:[/bold cyan] {event.entity_type or "N/A"}
[bold cyan]Entity ID:[/bold cyan] {event.entity_id or "N/A"}
[bold cyan]User ID:[/bold cyan] {event.user_id or "N/A"}

[bold cyan]Event Data:[/bold cyan]
{event_data_formatted}
"""

        if metadata_formatted:
            details += f"\n[bold cyan]Metadata:[/bold cyan]\n{metadata_formatted}"

        panel = Panel(details, title=f"Event Details: {event.event_type}", border_style="blue")
        console.print(panel)

    finally:
        repo.close()


@app.command("stats")
def show_stats(
    last_hours: int | None = typer.Option(
        None, "--last-hours", "-h", help="Stats for last N hours"
    ),
    last_days: int | None = typer.Option(None, "--last-days", "-d", help="Stats for last N days"),
) -> None:
    """Show event statistics and summary."""
    ensure_db()

    # Calculate date range
    start_date = None
    date_range_label = "All Time"
    if last_hours:
        start_date = datetime.now() - timedelta(hours=last_hours)
        date_range_label = f"Last {last_hours} hours"
    elif last_days:
        start_date = datetime.now() - timedelta(days=last_days)
        date_range_label = f"Last {last_days} days"

    # Get statistics
    repo = EventRepository()
    try:
        stats = repo.get_stats(start_date=start_date)

        # Overall statistics
        console.print(Panel(f"[bold]Event Statistics - {date_range_label}[/bold]", style="cyan"))
        console.print(f"\n[bold]Total Events:[/bold] {stats['total_events']:,}\n")

        # Events by type
        if stats["events_by_type"]:
            type_table = Table(title="Events by Type", show_lines=False)
            type_table.add_column("Event Type", style="cyan")
            type_table.add_column("Count", justify="right", style="bold white")
            type_table.add_column("Percentage", justify="right", style="green")

            total = stats["total_events"]
            for event_type, count in sorted(
                stats["events_by_type"].items(), key=lambda x: x[1], reverse=True
            ):
                percentage = (count / total * 100) if total > 0 else 0
                type_table.add_row(event_type, f"{count:,}", f"{percentage:.1f}%")

            console.print(type_table)
            console.print()

        # Events by entity
        if stats["events_by_entity"]:
            entity_table = Table(title="Events by Entity Type", show_lines=False)
            entity_table.add_column("Entity Type", style="cyan")
            entity_table.add_column("Count", justify="right", style="bold white")

            for entity_type, count in sorted(
                stats["events_by_entity"].items(), key=lambda x: x[1], reverse=True
            ):
                entity_table.add_row(entity_type, f"{count:,}")

            console.print(entity_table)
            console.print()

        # Most recent and oldest events
        if stats["most_recent_event"]:
            console.print(
                f"[bold]Most Recent Event:[/bold] {stats['most_recent_event']['event_type']} "
                f"at {stats['most_recent_event']['occurred_at'].strftime('%Y-%m-%d %H:%M:%S')}"
            )

        if stats["oldest_event"]:
            console.print(
                f"[bold]Oldest Event:[/bold] {stats['oldest_event']['event_type']} "
                f"at {stats['oldest_event']['occurred_at'].strftime('%Y-%m-%d %H:%M:%S')}"
            )

    finally:
        repo.close()


@app.command("timeline")
def show_timeline(
    entity_type: str = typer.Argument(..., help="Entity type (invoice, client, etc.)"),
    entity_id: int = typer.Argument(..., help="Entity ID"),
) -> None:
    """Show event timeline for a specific entity."""
    ensure_db()

    repo = EventRepository()
    try:
        timeline = repo.get_timeline(entity_type, entity_id)

        if not timeline:
            console.print(f"[yellow]No events found for {entity_type} with ID {entity_id}[/yellow]")
            return

        # Create timeline visualization
        console.print(
            Panel(
                f"[bold]Event Timeline: {entity_type.capitalize()} #{entity_id}[/bold]",
                style="cyan",
            )
        )
        console.print()

        for i, event in enumerate(timeline):
            timestamp = event["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

            # Create timeline entry
            if i == 0:
                marker = "┌"
            elif i == len(timeline) - 1:
                marker = "└"
            else:
                marker = "├"

            event_text = Text()
            event_text.append(f"{marker}── ", style="dim")
            event_text.append(f"{timestamp}", style="cyan")
            event_text.append(" │ ", style="dim")
            event_text.append(f"{event['event_type']}", style="bold")
            event_text.append(f"\n    {event['summary']}", style="white")

            console.print(event_text)

        console.print(f"\n[dim]Total events: {len(timeline)}[/dim]")

    finally:
        repo.close()


@app.command("search")
def search_events(
    query: str = typer.Argument(..., help="Search query string"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of results"),
) -> None:
    """Search events by content in event data."""
    ensure_db()

    repo = EventRepository()
    try:
        events = repo.search(query, limit=limit)

        if not events:
            console.print(f"[yellow]No events found matching '{query}'[/yellow]")
            return

        # Create table
        table = Table(title=f"Search Results: '{query}' ({len(events)} events)", show_lines=False)
        table.add_column("Timestamp", style="cyan", width=19)
        table.add_column("Event Type", style="bold white", width=25)
        table.add_column("Match", style="yellow")

        for event in events:
            timestamp = event.occurred_at.strftime("%Y-%m-%d %H:%M:%S")

            # Find matching text snippet
            try:
                event_data = json.loads(event.event_data)
                event_str = json.dumps(event_data)

                # Find query in event data
                query_lower = query.lower()
                event_str_lower = event_str.lower()
                idx = event_str_lower.find(query_lower)

                if idx >= 0:
                    # Extract snippet around match
                    start = max(0, idx - 30)
                    end = min(len(event_str), idx + len(query) + 30)
                    snippet = event_str[start:end]
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(event_str):
                        snippet = snippet + "..."
                    match = snippet
                else:
                    match = repo._create_event_summary(event.event_type, event_data)
            except Exception:
                match = event.event_type

            table.add_row(timestamp, event.event_type, match)

        console.print(table)

    finally:
        repo.close()


@app.command("types")
def list_event_types() -> None:
    """List all event types in the system."""
    ensure_db()

    repo = EventRepository()
    try:
        stats = repo.get_stats()

        if not stats["events_by_type"]:
            console.print("[yellow]No events recorded yet[/yellow]")
            return

        table = Table(title="Available Event Types", show_lines=False)
        table.add_column("#", style="dim", width=4)
        table.add_column("Event Type", style="cyan")
        table.add_column("Count", justify="right", style="white")

        for i, (event_type, count) in enumerate(sorted(stats["events_by_type"].items()), start=1):
            table.add_row(str(i), event_type, f"{count:,}")

        console.print(table)

    finally:
        repo.close()


@app.command("dashboard")
def show_dashboard(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
) -> None:
    """Show comprehensive event analytics dashboard."""
    ensure_db()

    analytics = EventAnalytics()
    try:
        # Get dashboard summary
        summary = analytics.get_dashboard_summary(days=days)

        # Header
        console.print()
        console.print(
            Panel(
                f"[bold]Event Analytics Dashboard - Last {days} Days[/bold]",
                style="cyan",
                expand=False,
            )
        )
        console.print()

        # Key metrics
        metrics_table = Table(show_header=False, show_edge=False, padding=(0, 2))
        metrics_table.add_column(style="bold cyan")
        metrics_table.add_column(style="white")

        metrics_table.add_row("Total Events", f"{summary['total_events']:,}")
        metrics_table.add_row("Event Types", f"{summary['event_types_count']}")
        metrics_table.add_row(
            "Events/Hour (24h)", f"{summary['velocity_24h']['events_per_hour']:.1f}"
        )

        # Add trend indicator
        trends = summary["trends"]
        trend_icon = (
            "📈"
            if trends["trend"] == "increasing"
            else "📉" if trends["trend"] == "decreasing" else "➡️"
        )
        trend_color = (
            "green"
            if trends["trend"] == "increasing"
            else "red" if trends["trend"] == "decreasing" else "yellow"
        )
        metrics_table.add_row(
            "Trend",
            f"[{trend_color}]{trend_icon} {trends['change']:+,} ({trends['change_percent']:+.1f}%)[/{trend_color}]",
        )

        console.print(metrics_table)
        console.print()

        # Top Event Types with bar visualization
        if summary["top_event_types"]:
            console.print("[bold]Top Event Types[/bold]")
            console.print()

            # Find max count for scaling
            max_count = max((item["count"] for item in summary["top_event_types"]), default=1)

            for item in summary["top_event_types"]:
                event_type = item["event_type"]
                count = item["count"]
                percentage = item["percentage"]

                # Create bar
                bar_width = int((count / max_count) * 40) if max_count > 0 else 0
                bar = "█" * bar_width

                # Shorten event type name if too long
                display_name = event_type.replace("Event", "")
                if len(display_name) > 25:
                    display_name = display_name[:22] + "..."

                console.print(
                    f"  {display_name:25} [cyan]{bar:40}[/cyan] {count:>6,} ({percentage:>5.1f}%)"
                )

            console.print()

        # Entity Activity
        if summary["entity_activity"]:
            entity_table = Table(title="Entity Activity", show_lines=False)
            entity_table.add_column("Entity Type", style="cyan")
            entity_table.add_column("Events", justify="right", style="white")

            for item in summary["entity_activity"]:
                entity_table.add_row(item["entity_type"], f"{item['count']:,}")

            console.print(entity_table)
            console.print()

        # Recent Activity
        if summary["most_recent_event"]:
            recent = summary["most_recent_event"]
            console.print(
                f"[dim]Most Recent: {recent['event_type']} at "
                f"{recent['occurred_at'].strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
            )

    finally:
        analytics.close()


@app.command("trends")
def show_trends(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
    event_type: str | None = typer.Option(None, "--type", "-t", help="Filter by event type"),
) -> None:
    """Show event trends over time."""
    ensure_db()

    analytics = EventAnalytics()
    try:
        # Get daily activity
        daily = analytics.get_daily_activity(days=days, event_type=event_type)

        if not daily:
            console.print("[yellow]No events found for the specified period[/yellow]")
            return

        # Header
        title = f"Event Trends - Last {days} Days"
        if event_type:
            title += f" ({event_type})"

        console.print()
        console.print(Panel(f"[bold]{title}[/bold]", style="cyan"))
        console.print()

        # Create simple bar chart
        max_count = max((item["count"] for item in daily), default=1)

        for item in daily:
            date = item["date"]
            count = item["count"]

            # Create bar (scaled to 50 chars max)
            bar_width = int((count / max_count) * 50) if max_count > 0 else 0
            bar = "█" * bar_width

            console.print(f"  {date} [cyan]{bar:50}[/cyan] {count:>5,}")

        # Summary stats
        total = sum(item["count"] for item in daily)
        avg = total / len(daily) if daily else 0

        console.print()
        console.print(f"[dim]Total: {total:,} events | Average: {avg:.1f} events/day[/dim]")

    finally:
        analytics.close()
