"""Batch operations commands."""

from pathlib import Path
from typing import cast

import typer
from rich.console import Console
from rich.table import Table

from openfatture.cli.lifespan import get_event_bus
from openfatture.core.batch.invoice_processor import InvoiceBatchProcessor
from openfatture.core.events import BatchImportCompletedEvent, BatchImportStartedEvent
from openfatture.i18n import _
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
    csv_file: str = typer.Argument(..., help=_("cli-batch-help-csv-file")),
    dry_run: bool = typer.Option(False, "--dry-run", help=_("cli-batch-help-dry-run")),
    send_summary: bool = typer.Option(
        True, "--summary/--no-summary", help=_("cli-batch-help-send-summary")
    ),
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

    console.print(f"\n{_('cli-batch-import-title')}\n")

    file = Path(csv_file)

    if not file.exists():
        console.print(_("cli-batch-file-not-found", file=csv_file))
        raise typer.Exit(1)

    console.print(_("cli-batch-file-info-name", name=file.name))
    console.print(_("cli-batch-file-info-size", size=file.stat().st_size))
    console.print(_("cli-batch-mode-dry-run" if dry_run else "cli-batch-mode-import"))

    if dry_run:
        console.print(f"{_('cli-batch-warning-dry-run')}\n")

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
        console.print(f"\n{_('cli-batch-results-title')}\n")

        table = Table(show_header=False, box=None)
        table.add_column(_("cli-batch-metric-label"), style="cyan", width=25)
        table.add_column(_("cli-batch-metric-value"), style="white", justify="right")

        table.add_row(_("cli-batch-metric-total"), str(result.total))
        table.add_row(_("cli-batch-metric-processed"), str(result.processed))
        table.add_row(_("cli-batch-metric-succeeded"), f"[green]{result.succeeded}[/green]")
        table.add_row(
            _("cli-batch-metric-failed"),
            f"[red]{result.failed}[/red]" if result.failed > 0 else "0",
        )
        table.add_row(_("cli-batch-metric-success-rate"), f"{result.success_rate:.1f}%")

        if result.duration:
            table.add_row(_("cli-batch-metric-duration"), f"{result.duration:.2f}s")

        console.print(table)

        # Show errors
        if result.errors:
            console.print(f"\n{_('cli-batch-errors-title')}")
            for error in result.errors[:10]:
                console.print(f"  • {error}")

            if len(result.errors) > 10:
                console.print(_("cli-batch-errors-more", count=len(result.errors) - 10))

        # Summary message
        if result.succeeded == result.total:
            console.print(f"\n{_('cli-batch-success-all')}")
        elif result.failed > 0:
            console.print(_("cli-batch-warning-failed", count=result.failed))

        # Send email summary
        if send_summary and not dry_run and settings.notification_enabled:
            email_option = settings.notification_email
            if not email_option:
                console.print(_("cli-batch-email-not-configured"))
            else:
                email = cast(str, email_option)
                console.print(f"\n{_('cli-batch-email-sending')}")

                sender = TemplatePECSender(settings=settings, locale=settings.locale)
                success, summary_error = sender.send_batch_summary(
                    result=result,
                    operation_type="import",
                    recipients=[email],
                )

                if success:
                    console.print(_("cli-batch-email-sent", email=email))
                else:
                    console.print(_("cli-batch-email-failed", error=summary_error))

        console.print()

    except Exception as e:
        db.rollback()
        if not errors:
            errors = [str(e)]
        console.print(_("cli-batch-error-general", error=str(e)))
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
    output_file: str = typer.Argument(..., help=_("cli-batch-help-output-file")),
    anno: int | None = typer.Option(None, "--anno", help=_("cli-batch-help-anno")),
    stato: str | None = typer.Option(None, "--stato", help=_("cli-batch-help-stato")),
) -> None:
    """
    Export invoices to CSV file.

    Examples:
        openfatture batch export fatture.csv
        openfatture batch export fatture_2025.csv --anno 2025
        openfatture batch export inviati.csv --stato inviata
    """
    ensure_db()

    console.print(f"\n{_('cli-batch-export-title')}\n")

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
            console.print(_("cli-batch-filter-year", year=anno))

        if stato:
            try:
                stato_enum = StatoFattura(stato.lower())
                query = query.filter(Fattura.stato == stato_enum)
                console.print(_("cli-batch-filter-status", status=stato_enum.value))
            except ValueError:
                console.print(_("cli-batch-invalid-status", status=stato))
                return

        fatture = query.all()

        if not fatture:
            console.print(f"\n{_('cli-batch-no-invoices')}")
            return

        console.print(_("cli-batch-invoices-count", count=len(fatture)))

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
            console.print(_("cli-batch-export-success", count=result.succeeded))
            console.print(_("cli-batch-export-file", path=str(output_path.absolute())))
            console.print(_("cli-batch-export-size", size=output_path.stat().st_size))
        else:
            console.print(_("cli-batch-export-failed"))
            for error in result.errors:
                console.print(f"  • {error}")

    except Exception as e:
        if not errors:
            errors = [str(e)]
        console.print(_("cli-batch-error-general", error=str(e)))
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
    limit: int = typer.Option(10, "--limit", "-l", help=_("cli-batch-help-limit")),
) -> None:
    """
    Show history of batch operations.

    This shows previous import/export operations with their results.

    Example:
        openfatture batch history
        openfatture batch history --limit 20
    """
    console.print(f"\n{_('cli-batch-history-title')}\n")

    console.print(_("cli-batch-history-not-implemented"))
    console.print(_("cli-batch-history-will-show"))
    console.print(_("cli-batch-history-feature-datetime"))
    console.print(_("cli-batch-history-feature-type"))
    console.print(_("cli-batch-history-feature-records"))
    console.print(_("cli-batch-history-feature-counts"))
    console.print(_("cli-batch-history-feature-errors"))

    # Placeholder example
    console.print(f"\n{_('cli-batch-history-example')}\n")

    table = Table(show_lines=False)
    table.add_column(_("cli-batch-history-col-date"), style="cyan", width=20)
    table.add_column(_("cli-batch-history-col-type"), style="white", width=10)
    table.add_column(_("cli-batch-history-col-records"), justify="right", width=10)
    table.add_column(_("cli-batch-history-col-success"), style="green", justify="right", width=10)
    table.add_column(_("cli-batch-history-col-failed"), style="red", justify="right", width=10)

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

    console.print(f"\n{_('cli-batch-history-todo')}")
    console.print()
