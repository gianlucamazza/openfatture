"""Preventivo (quote/estimate) management commands."""

from datetime import date, timedelta
from decimal import Decimal

import typer
from rich.console import Console
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table

from openfatture.core.preventivi.service import PreventivoService
from openfatture.storage.database.base import SessionLocal, get_session, init_db
from openfatture.storage.database.models import Cliente, StatoPreventivo, TipoDocumento
from openfatture.utils.config import get_settings

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


@app.command("crea")
def crea_preventivo(
    cliente_id: int | None = typer.Option(None, "--cliente", help="Client ID"),
    validita_giorni: int = typer.Option(30, "--validita", help="Validity period in days"),
) -> None:
    """
    Create a new preventivo (quote/estimate).
    """
    ensure_db()

    console.print("\n[bold blue]📋 Create New Preventivo (Quote)[/bold blue]\n")

    db = _get_session()
    try:
        # Select client
        if not cliente_id:
            clienti = db.query(Cliente).order_by(Cliente.denominazione).all()

            if not clienti:
                console.print(
                    "[red]No clients found. Add one first with 'openfatture cliente add'[/red]"
                )
                raise typer.Exit(1)

            console.print("[cyan]Available clients:[/cyan]")
            for i, c in enumerate(clienti[:10], 1):
                console.print(f"  {c.id}. {c.denominazione} ({c.partita_iva or 'N/A'})")

            cliente_id = IntPrompt.ask("\nSelect client ID", default=clienti[0].id)

        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            console.print(f"[red]Client {cliente_id} not found[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓ Client: {cliente.denominazione}[/green]\n")

        # Preventivo details
        data_emissione = date.today()
        data_scadenza = data_emissione + timedelta(days=validita_giorni)

        console.print(
            f"[dim]Validity: {validita_giorni} days (expires: {data_scadenza.isoformat()})[/dim]\n"
        )

        # Add line items
        console.print("\n[bold]Add line items[/bold]")
        console.print("[dim]Enter empty description to finish[/dim]\n")

        righe = []
        riga_num = 1
        totale_imponibile = Decimal("0")
        totale_iva = Decimal("0")

        while True:
            descrizione = Prompt.ask(f"Item {riga_num} description", default="")
            if not descrizione:
                break

            quantita = FloatPrompt.ask("Quantity", default=1.0)
            prezzo = FloatPrompt.ask("Unit price (€)", default=100.0)
            aliquota_iva = FloatPrompt.ask("VAT rate (%)", default=22.0)
            unita_misura = Prompt.ask("Unit of measure", default="ore")

            # Calculate
            imponibile = Decimal(str(quantita)) * Decimal(str(prezzo))
            iva = imponibile * Decimal(str(aliquota_iva)) / Decimal("100")
            totale = imponibile + iva

            righe.append(
                {
                    "descrizione": descrizione,
                    "quantita": quantita,
                    "prezzo_unitario": prezzo,
                    "aliquota_iva": aliquota_iva,
                    "unita_misura": unita_misura,
                }
            )

            totale_imponibile += imponibile
            totale_iva += iva

            console.print(f"  [green]✓ Added: {descrizione[:40]} - €{totale:.2f}[/green]")
            riga_num += 1

        if not righe:
            console.print("[yellow]No items added. Preventivo creation cancelled.[/yellow]")
            return

        # Optional: notes and conditions
        note = None
        condizioni = None

        if Confirm.ask("\nAdd notes?", default=False):
            note = Prompt.ask("Notes")

        if Confirm.ask("Add terms and conditions?", default=False):
            condizioni = Prompt.ask("Terms and conditions")

        # Create preventivo using service
        settings = get_settings()
        service = PreventivoService(settings)

        preventivo, error = service.create_preventivo(
            db=db,
            cliente_id=cliente_id,
            righe=righe,
            validita_giorni=validita_giorni,
            note=note,
            condizioni=condizioni,
        )

        if error:
            console.print(f"\n[red]❌ Error: {error}[/red]")
            raise typer.Exit(1)

        # Summary
        console.print("\n[bold green]✓ Preventivo created successfully![/bold green]\n")

        table = Table(title=f"Preventivo {preventivo.numero}/{preventivo.anno}")
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="white", justify="right")

        table.add_row("Client", cliente.denominazione)
        table.add_row("Issue date", preventivo.data_emissione.isoformat())
        table.add_row("Expiration date", preventivo.data_scadenza.isoformat())
        table.add_row("Line items", str(len(preventivo.righe)))
        table.add_row("Imponibile", f"€{preventivo.imponibile:.2f}")
        table.add_row("IVA", f"€{preventivo.iva:.2f}")
        table.add_row("[bold]TOTALE[/bold]", f"[bold]€{preventivo.totale:.2f}[/bold]")

        console.print(table)

        console.print(
            f"\n[dim]Next: openfatture preventivo converti {preventivo.id} (to create invoice)[/dim]"
        )

    except Exception as e:
        db.rollback()
        console.print(f"\n[red]Error creating preventivo: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("lista")
def list_preventivi(
    stato: str | None = typer.Option(None, "--stato", help="Filter by status"),
    anno: int | None = typer.Option(None, "--anno", help="Filter by year"),
    cliente_id: int | None = typer.Option(None, "--cliente", help="Filter by client ID"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
) -> None:
    """List preventivi (quotes)."""
    ensure_db()

    db = _get_session()
    try:
        settings = get_settings()
        service = PreventivoService(settings)

        stato_enum = None
        if stato:
            try:
                stato_enum = StatoPreventivo(stato.lower())
            except ValueError:
                console.print(f"[red]Invalid status: {stato}[/red]")
                console.print(f"Valid: {', '.join([s.value for s in StatoPreventivo])}")
                raise typer.Exit(1)

        preventivi = service.list_preventivi(
            db=db, stato=stato_enum, cliente_id=cliente_id, anno=anno, limit=limit
        )

        if not preventivi:
            console.print("[yellow]No preventivi found[/yellow]")
            return

        table = Table(title=f"Preventivi ({len(preventivi)})", show_lines=False)
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Number", style="white", width=12)
        table.add_column("Date", style="white", width=12)
        table.add_column("Expiration", style="white", width=12)
        table.add_column("Client", style="bold white")
        table.add_column("Total", style="green", justify="right", width=12)
        table.add_column("Status", style="yellow", width=15)

        for p in preventivi:
            status_color = {
                StatoPreventivo.BOZZA: "dim",
                StatoPreventivo.INVIATO: "yellow",
                StatoPreventivo.ACCETTATO: "green",
                StatoPreventivo.RIFIUTATO: "red",
                StatoPreventivo.SCADUTO: "red dim",
                StatoPreventivo.CONVERTITO: "blue",
            }.get(p.stato, "white")

            # Check if expired
            is_expired = p.data_scadenza < date.today() and p.stato not in [
                StatoPreventivo.CONVERTITO,
                StatoPreventivo.SCADUTO,
            ]
            expiration_style = "red" if is_expired else "white"

            table.add_row(
                str(p.id),
                f"{p.numero}/{p.anno}",
                p.data_emissione.isoformat(),
                f"[{expiration_style}]{p.data_scadenza.isoformat()}[/{expiration_style}]",
                p.cliente.denominazione[:30],
                f"€{p.totale:.2f}",
                f"[{status_color}]{p.stato.value}[/{status_color}]",
            )

        console.print(table)

    finally:
        db.close()


@app.command("show")
def show_preventivo(
    preventivo_id: int = typer.Argument(..., help="Preventivo ID"),
) -> None:
    """Show preventivo details."""
    ensure_db()

    db = _get_session()
    try:
        settings = get_settings()
        service = PreventivoService(settings)

        preventivo = service.get_preventivo(db, preventivo_id)

        if not preventivo:
            console.print(f"[red]Preventivo {preventivo_id} not found[/red]")
            raise typer.Exit(1)

        # Header
        console.print(
            f"\n[bold blue]Preventivo {preventivo.numero}/{preventivo.anno}[/bold blue]\n"
        )

        # Info table
        info = Table(show_header=False, box=None)
        info.add_column("Field", style="cyan", width=20)
        info.add_column("Value", style="white")

        info.add_row("Client", preventivo.cliente.denominazione)
        info.add_row("Issue date", preventivo.data_emissione.isoformat())
        info.add_row("Expiration date", preventivo.data_scadenza.isoformat())
        info.add_row("Validity", f"{preventivo.validita_giorni} days")
        info.add_row("Status", preventivo.stato.value)

        # Check if expired
        is_expired = preventivo.data_scadenza < date.today()
        if is_expired and preventivo.stato not in [
            StatoPreventivo.CONVERTITO,
            StatoPreventivo.SCADUTO,
        ]:
            info.add_row("[red]⚠ WARNING[/red]", "[red]Expired![/red]")

        console.print(info)

        # Line items
        console.print("\n[bold]Line Items:[/bold]")
        items_table = Table(show_lines=True)
        items_table.add_column("#", width=4, justify="right")
        items_table.add_column("Description")
        items_table.add_column("Qty", justify="right", width=8)
        items_table.add_column("Price", justify="right", width=10)
        items_table.add_column("VAT%", justify="right", width=8)
        items_table.add_column("Total", justify="right", width=12)

        for riga in preventivo.righe:
            items_table.add_row(
                str(riga.numero_riga),
                riga.descrizione,
                str(riga.quantita),
                f"€{riga.prezzo_unitario:.2f}",
                f"{riga.aliquota_iva:.0f}%",
                f"€{riga.totale:.2f}",
            )

        console.print(items_table)

        # Totals
        console.print("\n[bold]Totals:[/bold]")
        totals = Table(show_header=False, box=None)
        totals.add_column("", style="cyan", justify="right", width=30)
        totals.add_column("", style="white", justify="right", width=15)

        totals.add_row("Imponibile", f"€{preventivo.imponibile:.2f}")
        totals.add_row("IVA", f"€{preventivo.iva:.2f}")
        totals.add_row("[bold]TOTALE[/bold]", f"[bold]€{preventivo.totale:.2f}[/bold]")

        console.print(totals)

        # Notes and conditions
        if preventivo.note:
            console.print("\n[bold]Notes:[/bold]")
            console.print(f"[dim]{preventivo.note}[/dim]")

        if preventivo.condizioni:
            console.print("\n[bold]Terms and Conditions:[/bold]")
            console.print(f"[dim]{preventivo.condizioni}[/dim]")

        console.print()

    finally:
        db.close()


@app.command("delete")
def delete_preventivo(
    preventivo_id: int = typer.Argument(..., help="Preventivo ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a preventivo."""
    ensure_db()

    db = _get_session()
    try:
        settings = get_settings()
        service = PreventivoService(settings)

        preventivo = service.get_preventivo(db, preventivo_id)

        if not preventivo:
            console.print(f"[red]Preventivo {preventivo_id} not found[/red]")
            raise typer.Exit(1)

        if not force and not Confirm.ask(
            f"Delete preventivo {preventivo.numero}/{preventivo.anno}?", default=False
        ):
            console.print("Cancelled.")
            return

        success, error = service.delete_preventivo(db, preventivo_id)

        if error:
            console.print(f"[red]❌ Error: {error}[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓ Preventivo {preventivo.numero}/{preventivo.anno} deleted[/green]")

    except Exception as e:
        console.print(f"[red]Error deleting preventivo: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("converti")
def converti_preventivo(
    preventivo_id: int = typer.Argument(..., help="Preventivo ID"),
    tipo_documento: str = typer.Option(
        "TD01", "--tipo", help="Invoice document type (TD01, TD06, etc.)"
    ),
) -> None:
    """
    Convert preventivo to fattura (invoice).
    """
    ensure_db()

    console.print("\n[bold blue]🔄 Converting Preventivo to Fattura[/bold blue]\n")

    db = _get_session()
    try:
        settings = get_settings()
        service = PreventivoService(settings)

        # Get preventivo
        preventivo = service.get_preventivo(db, preventivo_id)

        if not preventivo:
            console.print(f"[red]Preventivo {preventivo_id} not found[/red]")
            raise typer.Exit(1)

        # Show preventivo summary
        console.print(f"[cyan]Preventivo: {preventivo.numero}/{preventivo.anno}[/cyan]")
        console.print(f"[cyan]Client: {preventivo.cliente.denominazione}[/cyan]")
        console.print(f"[cyan]Total: €{preventivo.totale:.2f}[/cyan]\n")

        # Parse tipo_documento
        try:
            tipo_doc_enum = TipoDocumento(tipo_documento.upper())
        except ValueError:
            console.print(f"[red]Invalid document type: {tipo_documento}[/red]")
            console.print("Valid: TD01, TD06, etc.")
            raise typer.Exit(1)

        # Confirm
        if not Confirm.ask("Convert to invoice?", default=True):
            console.print("[yellow]Cancelled.[/yellow]")
            return

        # Convert
        fattura, error = service.converti_a_fattura(db, preventivo_id, tipo_doc_enum)

        if error:
            console.print(f"\n[red]❌ Error: {error}[/red]")
            raise typer.Exit(1)

        # Success
        console.print("\n[bold green]✓ Preventivo converted successfully![/bold green]\n")

        table = Table(title=f"Invoice {fattura.numero}/{fattura.anno}")
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="white", justify="right")

        table.add_row("Client", fattura.cliente.denominazione)
        table.add_row("Date", fattura.data_emissione.isoformat())
        table.add_row("Document type", fattura.tipo_documento.value)
        table.add_row("Line items", str(len(fattura.righe)))
        table.add_row("Imponibile", f"€{fattura.imponibile:.2f}")
        table.add_row("IVA", f"€{fattura.iva:.2f}")
        table.add_row("[bold]TOTALE[/bold]", f"[bold]€{fattura.totale:.2f}[/bold]")

        console.print(table)

        console.print(f"\n[dim]Invoice ID: {fattura.id}[/dim]")
        console.print(
            f"[dim]Original preventivo: {preventivo.numero}/{preventivo.anno} (ID: {preventivo.id})[/dim]"
        )
        console.print(f"\n[dim]Next: openfatture fattura invia {fattura.id} --pec[/dim]")

    except Exception as e:
        db.rollback()
        console.print(f"\n[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("aggiorna-stato")
def aggiorna_stato(
    preventivo_id: int = typer.Argument(..., help="Preventivo ID"),
    stato: str = typer.Argument(
        ..., help="New status (bozza, inviato, accettato, rifiutato, scaduto)"
    ),
) -> None:
    """Update preventivo status."""
    ensure_db()

    db = _get_session()
    try:
        settings = get_settings()
        service = PreventivoService(settings)

        # Parse status
        try:
            stato_enum = StatoPreventivo(stato.lower())
        except ValueError:
            console.print(f"[red]Invalid status: {stato}[/red]")
            console.print(f"Valid: {', '.join([s.value for s in StatoPreventivo])}")
            raise typer.Exit(1)

        # Update
        success, error = service.update_stato(db, preventivo_id, stato_enum)

        if error:
            console.print(f"[red]❌ Error: {error}[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓ Status updated to: {stato_enum.value}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()
