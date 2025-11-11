"""SDI notifications management commands."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from openfatture.sdi.notifiche.processor import NotificationProcessor
from openfatture.storage.database.base import SessionLocal, get_session, init_db
from openfatture.storage.database.models import LogSDI
from openfatture.utils.config import get_settings
from openfatture.utils.email.sender import TemplatePECSender

app = typer.Typer(no_args_is_help=True)
console = Console()


def ensure_db() -> None:
    """Ensure database is initialized."""
    settings = get_settings()
    init_db(str(settings.database_url))


def _get_session():
    """Return a database session using the configured factory."""
    if SessionLocal is not None:
        return SessionLocal()
    return get_session()


@app.command("process")
def process_notification(
    file_path: str = typer.Argument(..., help="Path to SDI notification XML file"),
    no_email: bool = typer.Option(False, "--no-email", help="Skip automatic email notification"),
) -> None:
    """
    Process SDI notification file and update invoice status.

    Automatically sends email notification unless --no-email is specified.

    Examples:
        openfatture notifiche process RC_IT12345678901_00001.xml
        openfatture notifiche process NS_IT12345678901_00001.xml --no-email
    """
    ensure_db()

    console.print("\n[bold blue]📬 Processing SDI Notification[/bold blue]\n")

    file = Path(file_path)

    if not file.exists():
        console.print(f"[red]❌ File not found: {file_path}[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]File:[/cyan] {file.name}")
    console.print(f"[cyan]Size:[/cyan] {file.stat().st_size} bytes\n")

    settings = get_settings()
    db = _get_session()

    try:
        # Initialize processor with optional email sender
        email_sender = None
        if not no_email and settings.notification_enabled and settings.notification_email:
            email_sender = TemplatePECSender(settings=settings, locale=settings.locale)
            console.print(f"[dim]📧 Auto-email enabled → {settings.notification_email}[/dim]\n")

        processor = NotificationProcessor(
            db_session=db,
            email_sender=email_sender,
        )

        # Process notification
        console.print("Processing notification...")

        success, error, notification = processor.process_file(file)

        if not success or notification is None:
            console.print(f"\n[red]❌ Error: {error}[/red]")
            raise typer.Exit(1)

        # Success!
        console.print("\n[bold green]✓ Notification processed successfully![/bold green]\n")

        # Show details
        table = Table(show_header=False, box=None)
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="white")

        table.add_row("Type", notification.tipo)
        table.add_row("SDI ID", notification.identificativo_sdi)
        table.add_row("File", notification.nome_file)
        table.add_row("Date", notification.data_ricezione.strftime("%Y-%m-%d %H:%M:%S"))

        if notification.messaggio:
            table.add_row("Message", notification.messaggio[:100])

        if notification.lista_errori:
            table.add_row("Errors", f"{len(notification.lista_errori)} error(s)")

        console.print(table)

        if email_sender and not no_email:
            console.print(
                f"\n[dim]📧 Email notification sent to {settings.notification_email}[/dim]"
            )

        console.print()

    except Exception as e:
        db.rollback()
        console.print(f"\n[red]❌ Error processing notification: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("list")
def list_notifications(
    tipo: str | None = typer.Option(None, "--tipo", help="Filter by type (AT, RC, NS, MC, NE)"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
) -> None:
    """
    List all SDI notifications received.

    Examples:
        openfatture notifiche list
        openfatture notifiche list --tipo RC
        openfatture notifiche list --tipo NS --limit 10
    """
    ensure_db()

    console.print("\n[bold blue]📬 SDI Notifications[/bold blue]\n")

    db = _get_session()
    try:
        query = db.query(LogSDI).order_by(LogSDI.data_ricezione.desc())

        if tipo:
            query = query.filter(LogSDI.tipo_notifica == tipo.upper())

        notifiche = query.limit(limit).all()

        if not notifiche:
            console.print("[yellow]No notifications found[/yellow]")
            console.print("\n[dim]Process notifications with:[/dim]")
            console.print("  [cyan]openfatture notifiche process <file.xml>[/cyan]")
            return

        table = Table(title=f"Notifications ({len(notifiche)})", show_lines=False)
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Type", style="white", width=8)
        table.add_column("Date", style="white", width=12)
        table.add_column("Invoice", style="bold white", width=15)
        table.add_column("Client", style="white")
        table.add_column("SDI ID", style="dim", width=15)

        for n in notifiche:
            # Color by type
            type_color = {
                "RC": "green",
                "NS": "red",
                "AT": "cyan",
                "MC": "yellow",
                "NE": "blue",
            }.get(n.tipo_notifica, "white")

            # Skip if fattura or cliente is None
            if n.fattura is None or n.fattura.cliente is None:
                continue

            table.add_row(
                str(n.id),
                f"[{type_color}]{n.tipo_notifica}[/{type_color}]",
                n.data_ricezione.date().isoformat() if n.data_ricezione else "-",
                f"{n.fattura.numero}/{n.fattura.anno}",
                n.fattura.cliente.denominazione[:30],
                "-",  # SDI ID not stored in LogSDI yet
            )

        console.print(table)
        console.print()

    finally:
        db.close()


@app.command("show")
def show_notification(
    notification_id: int = typer.Argument(..., help="Notification ID"),
) -> None:
    """
    Show detailed information about a notification.

    Example:
        openfatture notifiche show 123
    """
    ensure_db()

    db = _get_session()
    try:
        notifica = db.query(LogSDI).filter(LogSDI.id == notification_id).first()

        if notifica is None:
            console.print(f"[red]Notification {notification_id} not found[/red]")
            raise typer.Exit(1)

        # Header
        type_emoji = {
            "RC": "✅",
            "NS": "❌",
            "AT": "📨",
            "MC": "⚠️",
            "NE": "📋",
        }.get(notifica.tipo_notifica, "📬")

        console.print(
            f"\n[bold blue]{type_emoji} Notification {notifica.id}: {notifica.tipo_notifica}[/bold blue]\n"
        )

        # Details table
        table = Table(show_header=False, box=None)
        table.add_column("Field", style="cyan", width=25)
        table.add_column("Value", style="white")

        table.add_row("Type", notifica.tipo_notifica)
        table.add_row("Invoice", f"{notifica.fattura.numero}/{notifica.fattura.anno}")
        table.add_row("Client", notifica.fattura.cliente.denominazione)
        table.add_row("Invoice Status", notifica.fattura.stato.value)

        if notifica.data_ricezione:
            table.add_row("Received", notifica.data_ricezione.isoformat())

        if notifica.descrizione:
            table.add_row("Description", notifica.descrizione)

        if notifica.xml_path:
            table.add_row("XML Path", notifica.xml_path)

        console.print(table)
        console.print()

    finally:
        db.close()
