"""SDI notifications management commands."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from openfatture.i18n import _
from openfatture.sdi.notifiche.processor import NotificationProcessor
from openfatture.storage.database.base import init_db
from openfatture.storage.database.models import LogSDI
from openfatture.storage.session import db_session
from openfatture.utils.config import get_settings
from openfatture.utils.email.sender import TemplatePECSender

app = typer.Typer(no_args_is_help=True)
console = Console()


def ensure_db() -> None:
    """Ensure database is initialized."""
    settings = get_settings()
    init_db(str(settings.database_url))


@app.command("process")
def process_notification(
    file_path: str = typer.Argument(..., help=_("cli-notifiche-help-file-path")),
    no_email: bool = typer.Option(False, "--no-email", help=_("cli-notifiche-help-no-email")),
) -> None:
    """
    Process SDI notification file and update invoice status.

    Automatically sends email notification unless --no-email is specified.

    Examples:
        openfatture notifiche process RC_IT12345678901_00001.xml
        openfatture notifiche process NS_IT12345678901_00001.xml --no-email
    """
    ensure_db()

    console.print(f"\n{_('cli-notifiche-process-title')}\n")

    file = Path(file_path)

    if not file.exists():
        console.print(_("cli-notifiche-file-not-found", file_path=file_path))
        raise typer.Exit(1)

    console.print(_("cli-notifiche-file-label", name=file.name))
    console.print(_("cli-notifiche-size-label", size=file.stat().st_size))

    settings = get_settings()
    with db_session() as db:
        # Initialize processor with optional email sender
        email_sender = None
        if not no_email and settings.notification_enabled and settings.notification_email:
            email_sender = TemplatePECSender(settings=settings, locale=settings.locale)
            console.print(_("cli-notifiche-auto-email-enabled", email=settings.notification_email))

        processor = NotificationProcessor(
            db_session=db,
            email_sender=email_sender,
        )

        # Process notification
        console.print(_("cli-notifiche-processing"))

        success, error, notification = processor.process_file(file)

        if not success or notification is None:
            console.print(_("cli-notifiche-error", error=error))
            raise typer.Exit(1)

        # Success!
        console.print(f"\n{_('cli-notifiche-success')}\n")

        # Show details
        table = Table(show_header=False, box=None)
        table.add_column(_("cli-notifiche-table-field"), style="cyan", width=20)
        table.add_column(_("cli-notifiche-table-value"), style="white")

        table.add_row(_("cli-notifiche-label-type"), notification.tipo)
        table.add_row(_("cli-notifiche-label-sdi-id"), notification.identificativo_sdi)
        table.add_row(_("cli-notifiche-label-file"), notification.nome_file)
        table.add_row(
            _("cli-notifiche-label-date"), notification.data_ricezione.strftime("%Y-%m-%d %H:%M:%S")
        )

        if notification.messaggio:
            table.add_row(_("cli-notifiche-label-message"), notification.messaggio[:100])

        if notification.lista_errori:
            table.add_row(
                _("cli-notifiche-label-errors"),
                _("cli-notifiche-errors-count", count=len(notification.lista_errori)),
            )

        console.print(table)

        if email_sender and not no_email:
            console.print(_("cli-notifiche-email-sent", email=settings.notification_email))

        console.print()


@app.command("list")
def list_notifications(
    tipo: str | None = typer.Option(None, "--tipo", help=_("cli-notifiche-help-tipo")),
    limit: int = typer.Option(50, "--limit", "-l", help=_("cli-notifiche-help-limit")),
) -> None:
    """
    List all SDI notifications received.

    Examples:
        openfatture notifiche list
        openfatture notifiche list --tipo RC
        openfatture notifiche list --tipo NS --limit 10
    """
    ensure_db()

    console.print(f"\n{_('cli-notifiche-list-title')}\n")

    with db_session() as db:
        query = db.query(LogSDI).order_by(LogSDI.data_ricezione.desc())

        if tipo:
            query = query.filter(LogSDI.tipo_notifica == tipo.upper())

        notifiche = query.limit(limit).all()

        if not notifiche:
            console.print(_("cli-notifiche-no-notifications"))
            console.print(f"\n{_('cli-notifiche-process-hint')}")
            console.print(_("cli-notifiche-process-cmd"))
            return

        table = Table(
            title=_("cli-notifiche-list-table-title", count=len(notifiche)), show_lines=False
        )
        table.add_column(_("cli-notifiche-column-id"), style="cyan", width=6)
        table.add_column(_("cli-notifiche-column-type"), style="white", width=8)
        table.add_column(_("cli-notifiche-column-date"), style="white", width=12)
        table.add_column(_("cli-notifiche-column-invoice"), style="bold white", width=15)
        table.add_column(_("cli-notifiche-column-client"), style="white")
        table.add_column(_("cli-notifiche-column-sdi-id"), style="dim", width=15)

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


@app.command("show")
def show_notification(
    notification_id: int = typer.Argument(..., help=_("cli-notifiche-help-notification-id")),
) -> None:
    """
    Show detailed information about a notification.

    Example:
        openfatture notifiche show 123
    """
    ensure_db()

    with db_session() as db:
        notifica = db.query(LogSDI).filter(LogSDI.id == notification_id).first()

        if notifica is None:
            console.print(_("cli-notifiche-not-found", notification_id=notification_id))
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
            f"\n{_('cli-notifiche-show-title', emoji=type_emoji, id=notifica.id, tipo=notifica.tipo_notifica)}\n"
        )

        # Details table
        table = Table(show_header=False, box=None)
        table.add_column(_("cli-notifiche-table-field"), style="cyan", width=25)
        table.add_column(_("cli-notifiche-table-value"), style="white")

        table.add_row(_("cli-notifiche-label-type"), notifica.tipo_notifica)
        table.add_row(
            _("cli-notifiche-label-invoice"), f"{notifica.fattura.numero}/{notifica.fattura.anno}"
        )
        table.add_row(_("cli-notifiche-label-client"), notifica.fattura.cliente.denominazione)
        table.add_row(_("cli-notifiche-label-invoice-status"), notifica.fattura.stato.value)

        if notifica.data_ricezione:
            table.add_row(_("cli-notifiche-label-received"), notifica.data_ricezione.isoformat())

        if notifica.descrizione:
            table.add_row(_("cli-notifiche-label-description"), notifica.descrizione)

        if notifica.xml_path:
            table.add_row(_("cli-notifiche-label-xml-path"), notifica.xml_path)

        console.print(table)
        console.print()
