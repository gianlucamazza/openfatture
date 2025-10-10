"""Invoice management commands."""

from datetime import date
from decimal import Decimal

import typer
from rich.console import Console
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table

from openfatture.storage.database.base import get_session, init_db
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)
from openfatture.utils.config import get_settings

app = typer.Typer()
console = Console()


def ensure_db() -> None:
    """Ensure database is initialized."""
    settings = get_settings()
    init_db(str(settings.database_url))


@app.command("crea")
def crea_fattura(
    cliente_id: int | None = typer.Option(None, "--cliente", help="Client ID"),
) -> None:
    """
    Create a new invoice (interactive wizard).
    """
    ensure_db()

    console.print("\n[bold blue]🧾 Create New Invoice[/bold blue]\n")

    db = get_session()
    try:
        # Select client
        if not cliente_id:
            clienti = db.query(Cliente).order_by(Cliente.denominazione).all()

            if not clienti:
                console.print("[red]No clients found. Add one first with 'cliente add'[/red]")
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

        # Invoice details
        anno = date.today().year
        ultimo_numero = (
            db.query(Fattura).filter(Fattura.anno == anno).order_by(Fattura.numero.desc()).first()
        )

        if ultimo_numero:
            prossimo_numero = int(ultimo_numero.numero) + 1
        else:
            prossimo_numero = 1

        numero = Prompt.ask("Invoice number", default=str(prossimo_numero))
        data_emissione = Prompt.ask("Issue date (YYYY-MM-DD)", default=date.today().isoformat())

        # Create invoice
        fattura = Fattura(
            numero=numero,
            anno=anno,
            data_emissione=date.fromisoformat(data_emissione),
            cliente_id=cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
        )

        db.add(fattura)
        db.flush()  # Get ID without committing

        console.print("\n[bold]Add line items[/bold]")
        console.print("[dim]Enter empty description to finish[/dim]\n")

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

            # Calculate
            imponibile = Decimal(str(quantita)) * Decimal(str(prezzo))
            iva = imponibile * Decimal(str(aliquota_iva)) / Decimal("100")
            totale = imponibile + iva

            # Add line
            riga = RigaFattura(
                fattura_id=fattura.id,
                numero_riga=riga_num,
                descrizione=descrizione,
                quantita=Decimal(str(quantita)),
                prezzo_unitario=Decimal(str(prezzo)),
                aliquota_iva=Decimal(str(aliquota_iva)),
                imponibile=imponibile,
                iva=iva,
                totale=totale,
            )

            db.add(riga)

            totale_imponibile += imponibile
            totale_iva += iva

            console.print(f"  [green]✓ Added: {descrizione[:40]} - €{totale:.2f}[/green]")
            riga_num += 1

        if riga_num == 1:
            console.print("[yellow]No items added. Invoice creation cancelled.[/yellow]")
            db.rollback()
            return

        # Update invoice totals
        fattura.imponibile = totale_imponibile
        fattura.iva = totale_iva
        fattura.totale = totale_imponibile + totale_iva

        # Ritenuta d'acconto (optional)
        if Confirm.ask("\nApply ritenuta d'acconto (withholding tax)?", default=False):
            aliquota_ritenuta = FloatPrompt.ask("Ritenuta rate (%)", default=20.0)
            ritenuta = totale_imponibile * Decimal(str(aliquota_ritenuta)) / Decimal("100")
            fattura.ritenuta_acconto = ritenuta
            fattura.aliquota_ritenuta = Decimal(str(aliquota_ritenuta))

        # Bollo (stamp duty for invoices without VAT >77.47€)
        if totale_iva == 0 and totale_imponibile > Decimal("77.47"):
            if Confirm.ask("Add bollo (€2.00)?", default=True):
                fattura.importo_bollo = Decimal("2.00")

        db.commit()
        db.refresh(fattura)

        # Summary
        console.print("\n[bold green]✓ Invoice created successfully![/bold green]\n")

        table = Table(title=f"Invoice {numero}/{anno}")
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="white", justify="right")

        table.add_row("Client", cliente.denominazione)
        table.add_row("Date", fattura.data_emissione.isoformat())
        table.add_row("Line items", str(len(fattura.righe)))
        table.add_row("Imponibile", f"€{fattura.imponibile:.2f}")
        table.add_row("IVA", f"€{fattura.iva:.2f}")
        if fattura.ritenuta_acconto:
            table.add_row("Ritenuta", f"-€{fattura.ritenuta_acconto:.2f}")
        if fattura.importo_bollo:
            table.add_row("Bollo", f"€{fattura.importo_bollo:.2f}")
        table.add_row("[bold]TOTALE[/bold]", f"[bold]€{fattura.totale:.2f}[/bold]")

        console.print(table)

        console.print(f"\n[dim]Next: openfatture fattura invia {fattura.id} --pec[/dim]")

    except Exception as e:
        db.rollback()
        console.print(f"\n[red]Error creating invoice: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("list")
def list_fatture(
    stato: str | None = typer.Option(None, "--stato", help="Filter by status"),
    anno: int | None = typer.Option(None, "--anno", help="Filter by year"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
) -> None:
    """List invoices."""
    ensure_db()

    db = get_session()
    try:
        query = db.query(Fattura).order_by(Fattura.anno.desc(), Fattura.numero.desc())

        if stato:
            try:
                stato_enum = StatoFattura(stato.lower())
                query = query.filter(Fattura.stato == stato_enum)
            except ValueError:
                console.print(f"[red]Invalid status: {stato}[/red]")
                return

        if anno:
            query = query.filter(Fattura.anno == anno)

        fatture = query.limit(limit).all()

        if not fatture:
            console.print("[yellow]No invoices found[/yellow]")
            return

        table = Table(title=f"Invoices ({len(fatture)})", show_lines=False)
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Number", style="white", width=12)
        table.add_column("Date", style="white", width=12)
        table.add_column("Client", style="bold white")
        table.add_column("Total", style="green", justify="right", width=12)
        table.add_column("Status", style="yellow", width=15)

        for f in fatture:
            status_color = {
                StatoFattura.BOZZA: "dim",
                StatoFattura.DA_INVIARE: "yellow",
                StatoFattura.INVIATA: "cyan",
                StatoFattura.ACCETTATA: "green",
                StatoFattura.RIFIUTATA: "red",
            }.get(f.stato, "white")

            table.add_row(
                str(f.id),
                f"{f.numero}/{f.anno}",
                f.data_emissione.isoformat(),
                f.cliente.denominazione[:30],
                f"€{f.totale:.2f}",
                f"[{status_color}]{f.stato.value}[/{status_color}]",
            )

        console.print(table)

    finally:
        db.close()


@app.command("show")
def show_fattura(
    fattura_id: int = typer.Argument(..., help="Invoice ID"),
) -> None:
    """Show invoice details."""
    ensure_db()

    db = get_session()
    try:
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()

        if not fattura:
            console.print(f"[red]Invoice {fattura_id} not found[/red]")
            raise typer.Exit(1)

        # Header
        console.print(f"\n[bold blue]Invoice {fattura.numero}/{fattura.anno}[/bold blue]\n")

        # Info table
        info = Table(show_header=False, box=None)
        info.add_column("Field", style="cyan", width=20)
        info.add_column("Value", style="white")

        info.add_row("Client", fattura.cliente.denominazione)
        info.add_row("Date", fattura.data_emissione.isoformat())
        info.add_row("Type", fattura.tipo_documento.value)
        info.add_row("Status", fattura.stato.value)

        if fattura.numero_sdi:
            info.add_row("SDI Number", fattura.numero_sdi)

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

        for riga in fattura.righe:
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

        totals.add_row("Imponibile", f"€{fattura.imponibile:.2f}")
        totals.add_row("IVA", f"€{fattura.iva:.2f}")

        if fattura.ritenuta_acconto:
            totals.add_row(
                f"Ritenuta ({fattura.aliquota_ritenuta}%)",
                f"-€{fattura.ritenuta_acconto:.2f}",
            )

        if fattura.importo_bollo:
            totals.add_row("Bollo", f"€{fattura.importo_bollo:.2f}")

        totals.add_row("[bold]TOTALE[/bold]", f"[bold]€{fattura.totale:.2f}[/bold]")

        console.print(totals)
        console.print()

    finally:
        db.close()


@app.command("delete")
def delete_fattura(
    fattura_id: int = typer.Argument(..., help="Invoice ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete an invoice."""
    ensure_db()

    db = get_session()
    try:
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()

        if not fattura:
            console.print(f"[red]Invoice {fattura_id} not found[/red]")
            raise typer.Exit(1)

        # Prevent deletion of sent invoices
        if fattura.stato in [
            StatoFattura.INVIATA,
            StatoFattura.ACCETTATA,
            StatoFattura.CONSEGNATA,
        ]:
            console.print(f"[red]Cannot delete invoice in status '{fattura.stato.value}'[/red]")
            raise typer.Exit(1)

        if not force and not Confirm.ask(
            f"Delete invoice {fattura.numero}/{fattura.anno}?", default=False
        ):
            console.print("Cancelled.")
            return

        db.delete(fattura)
        db.commit()

        console.print(f"[green]✓ Invoice {fattura.numero}/{fattura.anno} deleted[/green]")

    except Exception as e:
        db.rollback()
        console.print(f"[red]Error deleting invoice: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("xml")
def genera_xml(
    fattura_id: int = typer.Argument(..., help="Invoice ID"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output path"),
    no_validate: bool = typer.Option(False, "--no-validate", help="Skip XSD validation"),
) -> None:
    """Generate FatturaPA XML for an invoice."""
    ensure_db()

    console.print("\n[bold blue]🔧 Generating FatturaPA XML[/bold blue]\n")

    db = get_session()
    try:
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()

        if not fattura:
            console.print(f"[red]Invoice {fattura_id} not found[/red]")
            raise typer.Exit(1)

        # Import service
        from openfatture.core.fatture.service import InvoiceService

        settings = get_settings()
        service = InvoiceService(settings)

        # Generate XML
        console.print(f"Generating XML for invoice {fattura.numero}/{fattura.anno}...")

        xml_content, error = service.generate_xml(fattura, validate=not no_validate)

        if error:
            console.print(f"\n[red]❌ Error: {error}[/red]")
            if "XSD schema not found" in error:
                console.print(
                    "\n[yellow]Hint: Download the XSD schema from:[/yellow]\n"
                    "https://www.fatturapa.gov.it/export/documenti/fatturapa/v1.2.2/"
                    "Schema_del_file_xml_FatturaPA_v1.2.2.xsd\n"
                    f"And save it to: {settings.data_dir / 'schemas' / 'FatturaPA_v1.2.2.xsd'}"
                )
            raise typer.Exit(1)

        # Save to custom path if specified
        if output:
            from pathlib import Path

            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(xml_content, encoding="utf-8")
            console.print(f"\n[green]✓ XML saved to: {output_path.absolute()}[/green]")
        else:
            xml_path = service.get_xml_path(fattura)
            console.print("\n[green]✓ XML generated successfully![/green]")
            console.print(f"Path: {xml_path.absolute()}")

        # Update database
        db.commit()

        # Preview
        console.print("\n[dim]Preview (first 500 chars):[/dim]")
        console.print(f"[dim]{xml_content[:500]}...[/dim]")

    except Exception as e:
        db.rollback()
        console.print(f"\n[red]Error generating XML: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("invia")
def invia_fattura(
    fattura_id: int = typer.Argument(..., help="Invoice ID"),
    pec: bool = typer.Option(True, "--pec", help="Send via PEC"),
) -> None:
    """
    Send invoice to SDI.

    Note: This will generate XML and send via PEC in one command.
    """
    ensure_db()

    console.print("\n[bold blue]📤 Sending Invoice to SDI[/bold blue]\n")

    db = get_session()
    try:
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()

        if not fattura:
            console.print(f"[red]Invoice {fattura_id} not found[/red]")
            raise typer.Exit(1)

        # Step 1: Generate XML
        console.print("[cyan]1. Generating XML...[/cyan]")

        from openfatture.core.fatture.service import InvoiceService

        settings = get_settings()
        service = InvoiceService(settings)

        xml_content, error = service.generate_xml(fattura, validate=True)

        if error:
            console.print(f"[red]❌ XML generation failed: {error}[/red]")
            raise typer.Exit(1)

        console.print("[green]✓ XML generated[/green]")

        # Step 2: Digital signature (placeholder)
        console.print("\n[cyan]2. Digital signature...[/cyan]")
        console.print("[yellow]⚠ Digital signature not yet implemented[/yellow]")
        console.print("[dim]For now, you can sign manually with external tools.[/dim]")

        # Step 3: Send via PEC
        console.print("\n[cyan]3. Sending via PEC with professional email template...[/cyan]")

        if not Confirm.ask("Send invoice to SDI now?", default=False):
            console.print(
                "\n[yellow]Cancelled. Use 'openfatture fattura invia' later to send.[/yellow]"
            )
            db.commit()
            return

        from openfatture.utils.email.sender import TemplatePECSender

        sender = TemplatePECSender(settings=settings, locale=settings.locale)
        xml_path = service.get_xml_path(fattura)

        # Note: For production, integrate digital signature here
        # For now, send unsigned XML (acceptable for testing)
        success, error = sender.send_invoice_to_sdi(fattura, xml_path, signed=False)

        if success:
            console.print("[green]✓ Invoice sent to SDI via PEC with professional template[/green]")

            db.commit()

            console.print(
                f"\n[bold green]✓ Invoice {fattura.numero}/{fattura.anno} sent successfully![/bold green]"
            )
            console.print("\n[dim]📧 Professional email sent to SDI with:[/dim]")
            console.print("  • HTML + plain text format")
            console.print(f"  • Company branding ({settings.email_primary_color})")
            console.print(f"  • Language: {settings.locale.upper()}")
            console.print("\n[dim]📬 Automatic notifications:[/dim]")
            if settings.notification_enabled and settings.notification_email:
                console.print(
                    f"  • SDI responses will be emailed to: {settings.notification_email}"
                )
                console.print(
                    "  • Process notifications with: [cyan]openfatture notifiche process <file>[/cyan]"
                )
            else:
                console.print("  • Enable with: NOTIFICATION_EMAIL in .env")
            console.print("\n[dim]Monitor your PEC inbox for SDI notifications.[/dim]")

        else:
            console.print(f"[red]❌ Failed to send: {error}[/red]")

            # Still save the XML
            db.commit()

            console.print("\n[yellow]Manual steps:[/yellow]")
            console.print(f"  1. XML saved at: {xml_path}")
            console.print(f"  2. Sign if needed, then send to: {settings.sdi_pec_address}")
            raise typer.Exit(1)

    except Exception as e:
        db.rollback()
        console.print(f"\n[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()
