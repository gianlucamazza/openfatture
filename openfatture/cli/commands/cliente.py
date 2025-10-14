"""Client management commands."""

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from openfatture.storage.database.base import SessionLocal, get_session, init_db
from openfatture.storage.database.models import Cliente
from openfatture.utils.config import get_settings
from openfatture.utils.validators import (
    validate_codice_destinatario,
    validate_codice_fiscale,
    validate_partita_iva,
    validate_pec_email,
)

app = typer.Typer()
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


@app.command("add")
def add_cliente(
    denominazione: str = typer.Argument(..., help="Client name/company name"),
    partita_iva: str | None = typer.Option(None, "--piva", help="Partita IVA"),
    codice_fiscale: str | None = typer.Option(None, "--cf", help="Codice Fiscale"),
    codice_destinatario: str | None = typer.Option(None, "--sdi", help="SDI code"),
    pec: str | None = typer.Option(None, "--pec", help="PEC address"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode"),
) -> None:
    """Add a new client."""
    ensure_db()

    indirizzo: str | None = None
    cap: str | None = None
    comune: str | None = None
    provincia: str | None = None
    email: str | None = None
    telefono: str | None = None

    # Interactive mode collects all data
    if interactive:
        denominazione = Prompt.ask("Client name/Company", default=denominazione)

        partita_iva_input = Prompt.ask("Partita IVA (optional)", default=partita_iva or "")
        if partita_iva_input and validate_partita_iva(partita_iva_input):
            partita_iva = partita_iva_input
        elif partita_iva_input:
            console.print("[yellow]Warning: Invalid Partita IVA, skipping[/yellow]")

        cf_input = Prompt.ask("Codice Fiscale (optional)", default=codice_fiscale or "")
        if cf_input and validate_codice_fiscale(cf_input):
            codice_fiscale = cf_input.upper()
        elif cf_input:
            console.print("[yellow]Warning: Invalid Codice Fiscale, skipping[/yellow]")

        # Address
        indirizzo = Prompt.ask("Address (Via/Piazza)", default="")
        cap = Prompt.ask("CAP", default="")
        comune = Prompt.ask("City", default="")
        provincia = Prompt.ask("Province (2 letters)", default="").upper()

        # SDI/PEC
        sdi_input = Prompt.ask("SDI Code (7 chars, or 0000000 for PEC)", default="")
        if sdi_input and validate_codice_destinatario(sdi_input):
            codice_destinatario = sdi_input.upper()

        pec_input = Prompt.ask("PEC address (if SDI is 0000000)", default="")
        if pec_input and validate_pec_email(pec_input):
            pec = pec_input

        email = Prompt.ask("Regular email (optional)", default="")
        telefono = Prompt.ask("Phone (optional)", default="")

    # Validate required fields
    if not denominazione:
        console.print("[red]Error: Client name is required[/red]")
        raise typer.Exit(1)

    # Create client
    db = _get_session()
    try:
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
            numero_civico=None,  # Set to None if not provided in interactive mode
            cap=cap if interactive else None,
            comune=comune if interactive else None,
            provincia=provincia if interactive else None,
            nazione="IT",  # Default to Italy
            email=email if interactive else None,
            telefono=telefono if interactive else None,
            note=None,  # Set to None if not provided
        )

        db.add(cliente)
        db.commit()
        db.refresh(cliente)

        console.print(f"\n[green]✓ Client added successfully (ID: {cliente.id})[/green]")

        # Show summary
        table = Table(title=f"Client: {denominazione}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")

        if partita_iva:
            table.add_row("Partita IVA", partita_iva)
        if codice_fiscale:
            table.add_row("Codice Fiscale", codice_fiscale)
        if codice_destinatario:
            table.add_row("SDI Code", codice_destinatario)
        if pec:
            table.add_row("PEC", pec)

        console.print(table)

    except Exception as e:
        db.rollback()
        console.print(f"[red]Error adding client: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("list")
def list_clienti(
    limit: int = typer.Option(50, "--limit", "-l", help="Max number of results"),
) -> None:
    """List all clients."""
    ensure_db()

    db = _get_session()
    try:
        clienti = db.query(Cliente).order_by(Cliente.denominazione).limit(limit).all()

        if not clienti:
            console.print("[yellow]No clients found. Add one with 'cliente add'[/yellow]")
            return

        table = Table(title=f"Clients ({len(clienti)})", show_lines=False)
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Name", style="bold white")
        table.add_column("P.IVA", style="white")
        table.add_column("SDI/PEC", style="green")
        table.add_column("Invoices", style="yellow", justify="right")

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

    finally:
        db.close()


@app.command("show")
def show_cliente(
    cliente_id: int = typer.Argument(..., help="Client ID"),
) -> None:
    """Show detailed client information."""
    ensure_db()

    db = _get_session()
    try:
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()

        if not cliente:
            console.print(f"[red]Client with ID {cliente_id} not found[/red]")
            raise typer.Exit(1)

        table = Table(title=f"Client Details: {cliente.denominazione}")
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="white")

        table.add_row("ID", str(cliente.id))
        table.add_row("Name", cliente.denominazione)

        if cliente.partita_iva:
            table.add_row("Partita IVA", cliente.partita_iva)
        if cliente.codice_fiscale:
            table.add_row("Codice Fiscale", cliente.codice_fiscale)

        if cliente.indirizzo:
            address = f"{cliente.indirizzo}, {cliente.cap} {cliente.comune} ({cliente.provincia})"
            table.add_row("Address", address)

        if cliente.codice_destinatario:
            table.add_row("SDI Code", cliente.codice_destinatario)
        if cliente.pec:
            table.add_row("PEC", cliente.pec)
        if cliente.email:
            table.add_row("Email", cliente.email)
        if cliente.telefono:
            table.add_row("Phone", cliente.telefono)

        table.add_row("Total Invoices", str(len(cliente.fatture)))
        table.add_row("Created", cliente.created_at.strftime("%Y-%m-%d %H:%M"))

        console.print(table)

    finally:
        db.close()


@app.command("delete")
def delete_cliente(
    cliente_id: int = typer.Argument(..., help="Client ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a client."""
    ensure_db()

    db = _get_session()
    try:
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()

        if not cliente:
            console.print(f"[red]Client with ID {cliente_id} not found[/red]")
            raise typer.Exit(1)

        # Check for invoices
        if len(cliente.fatture) > 0 and not force:
            console.print(
                f"[yellow]Warning: This client has {len(cliente.fatture)} invoices[/yellow]"
            )
            if not Confirm.ask("Are you sure you want to delete?"):
                console.print("Cancelled.")
                return

        if not force and not Confirm.ask(
            f"Delete client '{cliente.denominazione}'?", default=False
        ):
            console.print("Cancelled.")
            return

        db.delete(cliente)
        db.commit()

        console.print(f"[green]✓ Client '{cliente.denominazione}' deleted[/green]")

    except Exception as e:
        db.rollback()
        console.print(f"[red]Error deleting client: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()
