"""Client management commands."""

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from sqlalchemy.exc import SQLAlchemyError

from openfatture.cli.lifespan import get_event_bus
from openfatture.core.events import ClientCreatedEvent, ClientDeletedEvent
from openfatture.i18n import _
from openfatture.storage.database.base import init_db
from openfatture.storage.database.models import Cliente
from openfatture.storage.session import db_session
from openfatture.utils.config import get_settings
from openfatture.utils.validators import (
    validate_codice_destinatario,
    validate_codice_fiscale,
    validate_partita_iva,
    validate_pec_email,
)

app = typer.Typer(no_args_is_help=True)
console = Console()


def ensure_db() -> None:
    """Ensure database is initialized."""
    settings = get_settings()
    init_db(str(settings.database_url))


@app.command("add")
def add_cliente(
    denominazione: str | None = typer.Argument(None, help=_("cli-cliente-help-name")),
    partita_iva: str | None = typer.Option(None, "--piva", help=_("cli-cliente-help-piva")),
    codice_fiscale: str | None = typer.Option(None, "--cf", help=_("cli-cliente-help-cf")),
    codice_destinatario: str | None = typer.Option(None, "--sdi", help=_("cli-cliente-help-sdi")),
    pec: str | None = typer.Option(None, "--pec", help=_("cli-cliente-help-pec")),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help=_("cli-cliente-help-interactive")
    ),
) -> None:
    """
    Add a new client to the database.

    Creates a new client record with tax information required for Italian invoicing.
    Use --interactive mode for guided setup with validation.

    Examples:
        openfatture cliente add "ACME Corp" --piva IT12345678901 --sdi ABCDEFG
        openfatture cliente add "John Doe" --cf RSSGNN80A01H501U --interactive
    """
    ensure_db()

    indirizzo: str | None = None
    numero_civico: str | None = None
    cap: str | None = None
    comune: str | None = None
    provincia: str | None = None
    email: str | None = None
    telefono: str | None = None
    note: str | None = None

    # Interactive mode collects all data
    if interactive:
        denominazione = (
            Prompt.ask(_("cli-cliente-prompt-company-name"), default=denominazione or "").strip()
            or None
        )

        partita_iva_input = Prompt.ask(_("cli-cliente-prompt-piva"), default=partita_iva or "")
        if partita_iva_input and validate_partita_iva(partita_iva_input):
            partita_iva = partita_iva_input
        elif partita_iva_input:
            console.print(_("cli-cliente-invalid-piva"))

        cf_input = Prompt.ask(_("cli-cliente-prompt-cf"), default=codice_fiscale or "")
        if cf_input and validate_codice_fiscale(cf_input):
            codice_fiscale = cf_input.upper()
        elif cf_input:
            console.print(_("cli-cliente-invalid-cf"))

        # Address
        indirizzo = Prompt.ask(_("cli-cliente-prompt-address"), default="").strip() or None
        numero_civico = Prompt.ask(_("cli-cliente-prompt-civic-number"), default="").strip() or None
        cap = Prompt.ask(_("cli-cliente-prompt-cap"), default="").strip() or None
        comune = Prompt.ask(_("cli-cliente-prompt-city"), default="").strip() or None
        provincia = Prompt.ask(_("cli-cliente-prompt-province"), default="").strip().upper() or None

        # SDI/PEC
        sdi_input = Prompt.ask(_("cli-cliente-prompt-sdi"), default="")
        if sdi_input and validate_codice_destinatario(sdi_input):
            codice_destinatario = sdi_input.upper()

        pec_input = Prompt.ask(_("cli-cliente-prompt-pec-address"), default="")
        if pec_input and validate_pec_email(pec_input):
            pec = pec_input

        email = Prompt.ask(_("cli-cliente-prompt-email"), default="").strip() or None
        telefono = Prompt.ask(_("cli-cliente-prompt-phone"), default="").strip() or None
        note = Prompt.ask(_("cli-cliente-prompt-notes"), default="").strip() or None

    # Validate required fields
    if denominazione:
        denominazione = denominazione.strip()

    if not denominazione:
        console.print(_("cli-cliente-name-required"))
        raise typer.Exit(1)

    # Create client
    try:
        with db_session() as db:
            # Parse name into first and last name if possible
            nome = None
            cognome = None
            if denominazione and " " in denominazione:
                # Try to split the name into first and last name
                parts = denominazione.split(" ", 1)
                if len(parts) == 2:
                    nome = parts[0]
                    cognome = parts[1]

            cliente = Cliente(
                denominazione=denominazione,
                nome=nome,
                cognome=cognome,
                partita_iva=partita_iva,
                codice_fiscale=codice_fiscale,
                codice_destinatario=codice_destinatario,
                pec=pec,
                indirizzo=indirizzo if interactive else None,
                numero_civico=numero_civico if interactive else None,
                cap=cap if interactive else None,
                comune=comune if interactive else None,
                provincia=provincia if interactive else None,
                nazione="IT",  # Default to Italy
                email=email if interactive else None,
                telefono=telefono if interactive else None,
                note=note if interactive else None,
            )

            db.add(cliente)
            db.commit()
            db.refresh(cliente)

            # Publish ClientCreatedEvent
            event_bus = get_event_bus()
            if event_bus:
                event_bus.publish(
                    ClientCreatedEvent(
                        client_id=cliente.id,
                        client_name=cliente.denominazione,
                        partita_iva=cliente.partita_iva,
                        codice_fiscale=cliente.codice_fiscale,
                        codice_destinatario=cliente.codice_destinatario,
                        pec=cliente.pec,
                    )
                )

            console.print(_("cli-cliente-added-success", id=cliente.id))

            # Show summary
            table = Table(title=_("cli-cliente-table-title", name=denominazione))
            table.add_column(_("cli-cliente-table-field"), style="cyan")
            table.add_column(_("cli-cliente-table-value"), style="white")

            if partita_iva:
                table.add_row(_("cli-cliente-label-piva"), partita_iva)
            if codice_fiscale:
                table.add_row(_("cli-cliente-label-cf"), codice_fiscale)
            if codice_destinatario:
                table.add_row(_("cli-cliente-label-sdi"), codice_destinatario)
            if pec:
                table.add_row(_("cli-cliente-label-pec"), pec)

            console.print(table)
    except (SQLAlchemyError, ValueError) as exc:
        # db_session() has already rolled back; convert the failure into a
        # clean error message and non-zero exit instead of a raw traceback.
        console.print(_("cli-cliente-add-error", error=str(exc)))
        raise typer.Exit(1) from exc


@app.command("list")
def list_clienti(
    limit: int = typer.Option(50, "--limit", "-l", help=_("cli-cliente-help-limit")),
) -> None:
    """List all clients."""
    ensure_db()

    with db_session() as db:
        clienti = db.query(Cliente).order_by(Cliente.denominazione).limit(limit).all()

        if not clienti:
            console.print(_("cli-cliente-no-clients"))
            return

        table = Table(title=_("cli-cliente-list-title", count=len(clienti)), show_lines=False)
        table.add_column(_("cli-cliente-column-id"), style="cyan", width=6)
        table.add_column(_("cli-cliente-column-name"), style="bold white")
        table.add_column(_("cli-cliente-column-piva"), style="white")
        table.add_column(_("cli-cliente-column-sdi-pec"), style="green")
        table.add_column(_("cli-cliente-column-invoices"), style="yellow", justify="right")

        for c in clienti:
            sdi_pec = c.codice_destinatario or c.pec or "-"
            num_fatture = len(c.fatture)
            table.add_row(
                str(c.id),
                c.denominazione,
                c.partita_iva or "-",
                sdi_pec[:20],
                str(num_fatture),
            )

        console.print(table)


@app.command("show")
def show_cliente(
    cliente_id: int = typer.Argument(..., help=_("cli-cliente-help-cliente-id")),
) -> None:
    """Show detailed client information."""
    ensure_db()

    with db_session() as db:
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()

        if not cliente:
            console.print(_("cli-cliente-not-found", id=cliente_id))
            raise typer.Exit(1)

        table = Table(title=_("cli-cliente-show-title", name=cliente.denominazione))
        table.add_column(_("cli-cliente-table-field"), style="cyan", width=20)
        table.add_column(_("cli-cliente-table-value"), style="white")

        table.add_row(_("cli-cliente-label-id"), str(cliente.id))
        table.add_row(_("cli-cliente-label-name"), cliente.denominazione)

        if cliente.partita_iva:
            table.add_row(_("cli-cliente-label-piva"), cliente.partita_iva)
        if cliente.codice_fiscale:
            table.add_row(_("cli-cliente-label-cf"), cliente.codice_fiscale)

        if cliente.indirizzo:
            address = f"{cliente.indirizzo}, {cliente.cap} {cliente.comune} ({cliente.provincia})"
            table.add_row(_("cli-cliente-label-address"), address)

        if cliente.codice_destinatario:
            table.add_row(_("cli-cliente-label-sdi"), cliente.codice_destinatario)
        if cliente.pec:
            table.add_row(_("cli-cliente-label-pec"), cliente.pec)
        if cliente.email:
            table.add_row(_("cli-cliente-label-email"), cliente.email)
        if cliente.telefono:
            table.add_row(_("cli-cliente-label-phone"), cliente.telefono)

        table.add_row(_("cli-cliente-label-total-invoices"), str(len(cliente.fatture)))
        table.add_row(_("cli-cliente-label-created"), cliente.created_at.strftime("%Y-%m-%d %H:%M"))

        console.print(table)


@app.command("delete")
def delete_cliente(
    cliente_id: int = typer.Argument(..., help=_("cli-cliente-help-cliente-id")),
    force: bool = typer.Option(False, "--force", "-f", help=_("cli-cliente-help-force")),
) -> None:
    """Delete a client."""
    ensure_db()

    with db_session() as db:
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()

        if not cliente:
            console.print(_("cli-cliente-not-found", id=cliente_id))
            raise typer.Exit(1)

        # Check for invoices
        if len(cliente.fatture) > 0 and not force:
            console.print(_("cli-cliente-has-invoices", count=len(cliente.fatture)))
            if not Confirm.ask(_("cli-cliente-confirm-delete")):
                console.print(_("cli-cliente-cancelled"))
                return

        if not force and not Confirm.ask(
            _("cli-cliente-confirm-delete-client", name=cliente.denominazione), default=False
        ):
            console.print(_("cli-cliente-cancelled"))
            return

        # Store info before deletion
        client_name = cliente.denominazione
        client_id = cliente.id
        invoice_count = len(cliente.fatture)

        db.delete(cliente)
        db.commit()

        # Publish ClientDeletedEvent
        event_bus = get_event_bus()
        if event_bus:
            event_bus.publish(
                ClientDeletedEvent(
                    client_id=client_id,
                    client_name=client_name,
                    invoice_count=invoice_count,
                    reason="User requested deletion",
                )
            )

        console.print(_("cli-cliente-deleted", name=client_name))
