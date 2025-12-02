"""Batch operations commands."""

from pathlib import Path
from typing import cast

import typer
from rich.console import Console
from rich.table import Table

from openfatture.cli.lifespan import get_event_bus
from openfatture.core.batch.invoice_processor import InvoiceBatchProcessor
from openfatture.core.events import BatchImportCompletedEvent, BatchImportStartedEvent
from openfatture.storage.database.base import init_db
from openfatture.storage.database.models import Fattura, StatoFattura
from openfatture.storage.session import db_session
from openfatture.utils.config import get_settings
from openfatture.utils.email.sender import TemplatePECSender

app = typer.Typer(no_args_is_help=True)
console = Console()


def ensure_db() -> None:
    """Ensure database is initialized."""
    settings = get_settings()
    init_db(str(settings.database_url))


@app.command("import")
def import_invoices(
    csv_file: str = typer.Argument(..., help="Path to CSV file with invoices"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate without importing"),
    send_summary: bool = typer.Option(True, "--summary/--no-summary", help="Send email summary"),
) -> None:
    """
    Import invoices from CSV file.

    CSV format: numero, anno, cliente_id, descrizione, quantita, prezzo, aliquota_iva
    See docs/BATCH_OPERATIONS.md for details.

    Examples:
        openfatture batch import fatture.csv
        openfatture batch import fatture.csv --dry-run
        openfatture batch import fatture.csv --no-summary
    """
    ensure_db()

    console.print("\n[bold blue]📦 Batch Import Invoices[/bold blue]\n")

    file = Path(csv_file)

    if not file.exists():
        console.print(f"[red]❌ File not found: {csv_file}[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]File:[/cyan] {file.name}")
    console.print(f"[cyan]Size:[/cyan] {file.stat().st_size} bytes")
    console.print(f"[cyan]Mode:[/cyan] {'Dry run (validation only)' if dry_run else 'Import'}\n")

    if dry_run:
        console.print("[yellow]⚠ Dry run mode - no data will be saved[/yellow]\n")

    ctx = db_session()
    db = ctx.__enter__()
    settings = get_settings()

    # Publish BatchImportStartedEvent
    event_bus = get_event_bus()
    if event_bus:
        event_bus.publish(
            BatchImportStartedEvent(
                file_path=str(file.absolute()),
                operation_type="import",
                dry_run=dry_run,
            )
        )

    # Track for completion event
    success = False
    records_processed = 0
    records_succeeded = 0
    records_failed = 0
    errors = []

    try:
        processor = InvoiceBatchProcessor(db_session=db)

        # Start import
        result = processor.import_from_csv(file, dry_run=dry_run)

        # Store results for event
        success = result.failed == 0
        records_processed = result.processed
        records_succeeded = result.succeeded
        records_failed = result.failed
        errors = result.errors or []

        # Show results
        console.print("\n[bold]Import Results:[/bold]\n")

        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan", width=25)
        table.add_column("Value", style="white", justify="right")

        table.add_row("Total rows", str(result.total))
        table.add_row("Processed", str(result.processed))
        table.add_row("Succeeded", f"[green]{result.succeeded}[/green]")
        table.add_row("Failed", f"[red]{result.failed}[/red]" if result.failed > 0 else "0")
        table.add_row("Success rate", f"{result.success_rate:.1f}%")

        if result.duration:
            table.add_row("Duration", f"{result.duration:.2f}s")

        console.print(table)

        # Show errors
        if result.errors:
            console.print("\n[bold red]Errors:[/bold red]")
            for error in result.errors[:10]:
                console.print(f"  • {error}")

            if len(result.errors) > 10:
                console.print(f"  [dim]... and {len(result.errors) - 10} more errors[/dim]")

        # Summary message
        if result.succeeded == result.total:
            console.print("\n[bold green]✓ All invoices imported successfully![/bold green]")
        elif result.failed > 0:
            console.print(f"\n[yellow]⚠ {result.failed} invoices failed to import[/yellow]")

        # Send email summary
        if send_summary and not dry_run and settings.notification_enabled:
            email_option = settings.notification_email
            if not email_option:
                console.print("[yellow]Notification email not configured.[/yellow]")
            else:
                email = cast(str, email_option)
                console.print("\n[dim]Sending email summary...[/dim]")

                sender = TemplatePECSender(settings=settings, locale=settings.locale)
                success, summary_error = sender.send_batch_summary(
                    result=result,
                    operation_type="import",
                    recipients=[email],
                )

                if success:
                    console.print(f"[dim]📧 Summary sent to {email}[/dim]")
                else:
                    console.print(f"[yellow]⚠ Failed to send summary: {summary_error}[/yellow]")

        console.print()

    except Exception as e:
        db.rollback()
        if not errors:
            errors = [str(e)]
        console.print(f"\n[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        # Publish BatchImportCompletedEvent
        if event_bus:
            event_bus.publish(
                BatchImportCompletedEvent(
                    file_path=str(file.absolute()),
                    operation_type="import",
                    success=success,
                    records_processed=records_processed,
                    records_succeeded=records_succeeded,
                    records_failed=records_failed,
                    errors=errors if errors else None,
                )
            )

        ctx.__exit__(None, None, None)


@app.command("export")
def export_invoices(
    output_file: str = typer.Argument(..., help="Output CSV file path"),
    anno: int | None = typer.Option(None, "--anno", help="Filter by year"),
    stato: str | None = typer.Option(None, "--stato", help="Filter by status"),
) -> None:
    """
    Export invoices to CSV file.

    Examples:
        openfatture batch export fatture.csv
        openfatture batch export fatture_2025.csv --anno 2025
        openfatture batch export inviati.csv --stato inviata
    """
    ensure_db()

    console.print("\n[bold blue]📦 Batch Export Invoices[/bold blue]\n")

    ctx = db_session()
    db = ctx.__enter__()

    # Publish BatchImportStartedEvent
    event_bus = get_event_bus()
    output_path = Path(output_file)
    if event_bus:
        event_bus.publish(
            BatchImportStartedEvent(
                file_path=str(output_path.absolute()),
                operation_type="export",
                dry_run=False,
            )
        )

    # Track for completion event
    success = False
    records_processed = 0
    records_succeeded = 0
    records_failed = 0
    errors = []

    try:
        # Build query
        query = db.query(Fattura)

        if anno:
            query = query.filter(Fattura.anno == anno)
            console.print(f"[cyan]Filter:[/cyan] Year = {anno}")

        if stato:
            try:
                stato_enum = StatoFattura(stato.lower())
                query = query.filter(Fattura.stato == stato_enum)
                console.print(f"[cyan]Filter:[/cyan] Status = {stato_enum.value}")
            except ValueError:
                console.print(f"[red]Invalid status: {stato}[/red]")
                return

        fatture = query.all()

        if not fatture:
            console.print("\n[yellow]No invoices found matching criteria[/yellow]")
            return

        console.print(f"[cyan]Invoices:[/cyan] {len(fatture)}\n")

        # Export
        processor = InvoiceBatchProcessor(db_session=db)

        result = processor.export_to_csv(fatture, output_path)

        # Store results for event
        success = result.succeeded > 0
        records_processed = len(fatture)
        records_succeeded = result.succeeded
        records_failed = result.failed
        errors = result.errors or []

        if result.succeeded > 0:
            console.print(f"[bold green]✓ Exported {result.succeeded} invoices![/bold green]")
            console.print(f"[cyan]File:[/cyan] {output_path.absolute()}")
            console.print(f"[cyan]Size:[/cyan] {output_path.stat().st_size} bytes\n")
        else:
            console.print("[red]❌ Export failed[/red]")
            for error in result.errors:
                console.print(f"  • {error}")

    except Exception as e:
        if not errors:
            errors = [str(e)]
        console.print(f"\n[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        # Publish BatchImportCompletedEvent
        if event_bus:
            event_bus.publish(
                BatchImportCompletedEvent(
                    file_path=str(output_path.absolute()),
                    operation_type="export",
                    success=success,
                    records_processed=records_processed,
                    records_succeeded=records_succeeded,
                    records_failed=records_failed,
                    errors=errors if errors else None,
                )
            )

        ctx.__exit__(None, None, None)


@app.command("history")
def batch_history(
    limit: int = typer.Option(10, "--limit", "-l", help="Max results"),
) -> None:
    """
    Show history of batch operations.

    This shows previous import/export operations with their results.

    Example:
        openfatture batch history
        openfatture batch history --limit 20
    """
    console.print("\n[bold blue]📦 Batch Operations History[/bold blue]\n")

    console.print("[yellow]⚠ History tracking not yet fully implemented[/yellow]")
    console.print("[dim]In production, this will show:[/dim]")
    console.print("  • Date/time of operation")
    console.print("  • Type (import/export)")
    console.print("  • Records processed")
    console.print("  • Success/failure counts")
    console.print("  • Error summaries\n")

    # Placeholder example
    console.print("[bold]Example history:[/bold]\n")

    table = Table(show_lines=False)
    table.add_column("Date", style="cyan", width=20)
    table.add_column("Type", style="white", width=10)
    table.add_column("Records", justify="right", width=10)
    table.add_column("Success", style="green", justify="right", width=10)
    table.add_column("Failed", style="red", justify="right", width=10)

    table.add_row(
        "2025-10-09 14:30:22",
        "import",
        "100",
        "95",
        "5",
    )
    table.add_row(
        "2025-10-08 09:15:43",
        "export",
        "250",
        "250",
        "0",
    )
    table.add_row(
        "2025-10-05 16:45:12",
        "import",
        "50",
        "48",
        "2",
    )

    console.print(table)

    console.print("\n[dim]To implement: Add BatchOperation model to database[/dim]")
    console.print()
