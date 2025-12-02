"""Invoice management commands."""

from datetime import date
from decimal import Decimal

import typer
from rich.console import Console
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table

from openfatture.cli.lifespan import get_event_bus
from openfatture.core.events import (
    InvoiceCreatedEvent,
    InvoiceDeletedEvent,
    InvoiceSentEvent,
    InvoiceValidatedEvent,
)
from openfatture.i18n import _
from openfatture.storage.database.base import init_db
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)
from openfatture.storage.session import db_session
from openfatture.utils.config import get_settings

app = typer.Typer(no_args_is_help=True)
console = Console()


def ensure_db() -> None:
    """Ensure database is initialized."""
    settings = get_settings()
    init_db(str(settings.database_url))


@app.command("crea")
def crea_fattura(
    cliente_id: int | None = typer.Option(None, "--cliente", help=_("cli-fattura-help-cliente-id")),
) -> None:
    """
    Create a new invoice (interactive wizard).

    This command guides you through creating a complete invoice with line items,
    taxes, and client selection. If no client ID is provided, you'll be prompted
    to select from existing clients.

    Examples:
        openfatture fattura crea
        openfatture fattura crea --cliente 1
    """
    ensure_db()

    console.print(f"\n{_('cli-fattura-create-title')}\n")

    with db_session() as db:
        # Select client
        if not cliente_id:
            clienti = db.query(Cliente).order_by(Cliente.denominazione).all()

            if not clienti:
                console.print(_("cli-fattura-no-clients-error"))
                raise typer.Exit(1)

            console.print(_("cli-fattura-available-clients"))
            for i, c in enumerate(clienti[:10], 1):
                console.print(f"  {c.id}. {c.denominazione} ({c.partita_iva or 'N/A'})")

            cliente_id = IntPrompt.ask(
                f"\n{_('cli-fattura-prompt-select-client')}", default=clienti[0].id
            )

        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            console.print(_("cli-fattura-invalid-client-error"))
            raise typer.Exit(1)

        console.print(f"{_('cli-fattura-client-selected', client_name=cliente.denominazione)}\n")

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

        console.print(f"\n{_('cli-fattura-add-lines-title')}")
        console.print(f"[dim]{_('cli-fattura-line-description-prompt')} to finish[/dim]\n")

        riga_num = 1
        totale_imponibile = Decimal("0")
        totale_iva = Decimal("0")

        while True:
            descrizione = Prompt.ask(
                f"Item {riga_num} {_('cli-fattura-line-description-prompt').lower()}", default=""
            )
            if not descrizione:
                break

            quantita = FloatPrompt.ask(_("cli-fattura-line-quantity-prompt"), default=1.0)
            prezzo = FloatPrompt.ask(_("cli-fattura-line-unit-price-prompt"), default=100.0)
            aliquota_iva = FloatPrompt.ask(_("cli-fattura-line-vat-rate-prompt"), default=22.0)

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

            console.print(
                _("cli-fattura-line-added", description=descrizione[:40], amount=f"{totale:.2f}")
            )
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

        # Publish InvoiceCreatedEvent
        event_bus = get_event_bus()
        if event_bus:
            event_bus.publish(
                InvoiceCreatedEvent(
                    invoice_id=fattura.id,
                    invoice_number=f"{fattura.numero}/{fattura.anno}",
                    client_id=fattura.cliente_id,
                    client_name=cliente.denominazione,
                    total_amount=fattura.totale,
                )
            )

        # Summary
        console.print(f"\n{_('cli-fattura-created-success')}\n")
        console.print(_("cli-fattura-created-number", numero=numero, anno=anno))

        table = Table(title=_("cli-fattura-show-title", numero=numero, anno=anno))
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


@app.command("list")
def list_fatture(
    stato: str | None = typer.Option(None, "--stato", help=_("cli-fattura-help-filter-status")),
    anno: int | None = typer.Option(None, "--anno", help=_("cli-fattura-help-filter-anno")),
    limit: int = typer.Option(50, "--limit", "-l", help=_("cli-fattura-help-limit")),
) -> None:
    """List invoices."""
    ensure_db()

    with db_session() as db:
        query = db.query(Fattura).order_by(Fattura.anno.desc(), Fattura.numero.desc())

        if stato:
            try:
                stato_enum = StatoFattura(stato.lower())
                query = query.filter(Fattura.stato == stato_enum)
            except ValueError:
                console.print(_("cli-fattura-invalid-status", status=stato))
                return

        if anno:
            query = query.filter(Fattura.anno == anno)

        fatture = query.limit(limit).all()

        if not fatture:
            console.print(_("cli-fattura-list-empty"))
            return

        table = Table(title=_("cli-fattura-table-title-list", count=len(fatture)), show_lines=False)
        table.add_column(_("cli-fattura-table-id"), style="cyan", width=6)
        table.add_column(_("cli-fattura-table-number"), style="white", width=12)
        table.add_column(_("cli-fattura-table-date"), style="white", width=12)
        table.add_column(_("cli-fattura-table-client"), style="bold white")
        table.add_column(_("cli-fattura-table-total"), style="green", justify="right", width=12)
        table.add_column(_("cli-fattura-table-status"), style="yellow", width=15)

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


@app.command("show")
def show_fattura(
    fattura_id: int = typer.Argument(..., help=_("cli-fattura-help-invoice-id")),
) -> None:
    """Show invoice details."""
    ensure_db()

    with db_session() as db:
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()

        if not fattura:
            console.print(_("cli-fattura-invoice-not-found", invoice_id=fattura_id))
            raise typer.Exit(1)

        # Header
        console.print(
            f"\n{_('cli-fattura-show-title', numero=fattura.numero, anno=fattura.anno)}\n"
        )

        # Info table
        info = Table(show_header=False, box=None)
        info.add_column(_("cli-fattura-table-field"), style="cyan", width=20)
        info.add_column(_("cli-fattura-table-value"), style="white")

        info.add_row(_("cli-fattura-table-client"), fattura.cliente.denominazione)
        info.add_row(_("cli-fattura-table-date"), fattura.data_emissione.isoformat())
        info.add_row(_("cli-fattura-table-type"), fattura.tipo_documento.value)
        info.add_row(_("cli-fattura-table-status"), fattura.stato.value)

        if fattura.numero_sdi:
            info.add_row(_("cli-fattura-table-sdi-number"), fattura.numero_sdi)

        console.print(info)

        # Line items
        console.print(f"\n{_('cli-fattura-line-items-header')}")
        items_table = Table(show_lines=True)
        items_table.add_column(_("cli-fattura-table-row-number"), width=4, justify="right")
        items_table.add_column(_("cli-fattura-table-description"))
        items_table.add_column(_("cli-fattura-table-qty"), justify="right", width=8)
        items_table.add_column(_("cli-fattura-table-price"), justify="right", width=10)
        items_table.add_column(_("cli-fattura-table-vat-percent"), justify="right", width=8)
        items_table.add_column(_("cli-fattura-table-total"), justify="right", width=12)

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
        console.print(f"\n{_('cli-fattura-totals-header')}")
        totals = Table(show_header=False, box=None)
        totals.add_column("", style="cyan", justify="right", width=30)
        totals.add_column("", style="white", justify="right", width=15)

        totals.add_row(_("cli-fattura-table-imponibile"), f"€{fattura.imponibile:.2f}")
        totals.add_row(_("cli-fattura-table-iva"), f"€{fattura.iva:.2f}")

        if fattura.ritenuta_acconto:
            totals.add_row(
                f"{_('cli-fattura-table-ritenuta')} ({fattura.aliquota_ritenuta}%)",
                f"-€{fattura.ritenuta_acconto:.2f}",
            )

        if fattura.importo_bollo:
            totals.add_row(_("cli-fattura-table-bollo"), f"€{fattura.importo_bollo:.2f}")

        totals.add_row(
            f"[bold]{_('cli-fattura-table-totale')}[/bold]", f"[bold]€{fattura.totale:.2f}[/bold]"
        )

        console.print(totals)
        console.print()


@app.command("delete")
def delete_fattura(
    fattura_id: int = typer.Argument(..., help=_("cli-fattura-help-invoice-id")),
    force: bool = typer.Option(False, "--force", "-f", help=_("cli-fattura-help-force")),
) -> None:
    """Delete an invoice."""
    ensure_db()

    with db_session() as db:
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()

        if not fattura:
            console.print(_("cli-fattura-invoice-not-found", invoice_id=fattura_id))
            raise typer.Exit(1)

        # Prevent deletion of sent invoices
        if fattura.stato in [
            StatoFattura.INVIATA,
            StatoFattura.ACCETTATA,
            StatoFattura.CONSEGNATA,
        ]:
            console.print(_("cli-fattura-delete-status-restriction", status=fattura.stato.value))
            raise typer.Exit(1)

        if not force and not Confirm.ask(
            _("cli-fattura-delete-confirm", numero=fattura.numero, anno=fattura.anno), default=False
        ):
            console.print(_("cli-fattura-cancelled"))
            return

        # Store info before deletion
        invoice_number = f"{fattura.numero}/{fattura.anno}"
        invoice_id = fattura.id

        db.delete(fattura)
        db.commit()

        # Publish InvoiceDeletedEvent
        event_bus = get_event_bus()
        if event_bus:
            event_bus.publish(
                InvoiceDeletedEvent(
                    invoice_id=invoice_id,
                    invoice_number=invoice_number,
                    reason="User requested deletion",
                )
            )

        console.print(_("cli-fattura-delete-success", numero=fattura.numero, anno=fattura.anno))


@app.command("xml")
def genera_xml(
    fattura_id: int = typer.Argument(..., help=_("cli-fattura-help-invoice-id")),
    output: str | None = typer.Option(None, "--output", "-o", help=_("cli-fattura-help-output")),
    no_validate: bool = typer.Option(
        False, "--no-validate", help=_("cli-fattura-help-no-validate")
    ),
) -> None:
    """Generate FatturaPA XML for an invoice."""
    ensure_db()

    console.print(f"\n{_('cli-fattura-xml-generation-title')}\n")

    # Track validation status for event publishing
    validation_status = "failed"
    issues = []
    xml_path_str = None
    invoice_number = None
    invoice_id = None

    with db_session() as db:
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()

        if not fattura:
            console.print(_("cli-fattura-invoice-not-found", invoice_id=fattura_id))
            raise typer.Exit(1)

        # Store for event publishing
        invoice_number = f"{fattura.numero}/{fattura.anno}"
        invoice_id = fattura.id

        # Import service
        from openfatture.core.fatture.service import InvoiceService

        settings = get_settings()
        service = InvoiceService(settings)

        # Generate XML
        console.print(_("cli-fattura-generating-xml", numero=fattura.numero, anno=fattura.anno))

        xml_content, error = service.generate_xml(fattura, validate=not no_validate)

        if error:
            issues.append(error)
            console.print(_("cli-fattura-xml-generation-error", error=error))
            if "XSD schema not found" in error:
                console.print(f"\n{_('cli-fattura-xml-schema-hint')}")
                console.print(_("cli-fattura-xml-schema-url"))
                console.print(
                    _(
                        "cli-fattura-xml-schema-save-path",
                        path=str(settings.data_dir / "schemas" / "FatturaPA_v1.2.2.xsd"),
                    )
                )
            raise typer.Exit(1)

        # Save to custom path if specified
        if output:
            from pathlib import Path

            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(xml_content, encoding="utf-8")
            xml_path_str = str(output_path.absolute())
            console.print(_("cli-fattura-xml-saved", path=xml_path_str))
        else:
            xml_path = service.get_xml_path(fattura)
            xml_path_str = str(xml_path.absolute())
            console.print(f"\n{_('cli-fattura-xml-generated')}")
            console.print(_("cli-fattura-xml-path", path=xml_path_str))

        # Update database
        db.commit()

        # Mark as passed
        validation_status = "passed"

        # Preview
        console.print(f"\n{_('cli-fattura-xml-preview')}")
        console.print(f"[dim]{xml_content[:500]}...[/dim]")

    # Publish InvoiceValidatedEvent
    if invoice_id and invoice_number:
        event_bus = get_event_bus()
        if event_bus:
            event_bus.publish(
                InvoiceValidatedEvent(
                    invoice_id=invoice_id,
                    invoice_number=invoice_number,
                    validation_status=validation_status,
                    issues=issues,
                    xml_path=xml_path_str,
                )
            )


@app.command("invia")
def invia_fattura(
    fattura_id: int = typer.Argument(..., help=_("cli-fattura-help-invoice-id")),
    pec: bool = typer.Option(True, "--pec", help=_("cli-fattura-help-pec")),
) -> None:
    """
    Send invoice to SDI via PEC.

    Generates FatturaPA XML, validates it, and sends to SDI through PEC.
    The invoice status will be updated to 'inviata' upon successful sending.

    Examples:
        openfatture fattura invia 123
        openfatture fattura invia 456 --pec
    """
    ensure_db()

    console.print(f"\n{_('cli-fattura-send-title')}\n")

    with db_session() as db:
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()

        if not fattura:
            console.print(_("cli-fattura-invoice-not-found", invoice_id=fattura_id))
            raise typer.Exit(1)

        # Step 1: Generate XML
        console.print(_("cli-fattura-send-step1-xml"))

        from openfatture.core.fatture.service import InvoiceService

        settings = get_settings()
        service = InvoiceService(settings)

        xml_content, error = service.generate_xml(fattura, validate=True)

        if error:
            console.print(_("cli-fattura-send-xml-failed", error=error))
            raise typer.Exit(1)

        console.print(_("cli-fattura-send-xml-success"))

        # Step 2: Digital signature (placeholder)
        console.print(f"\n{_('cli-fattura-send-step2-signature')}")
        console.print(_("cli-fattura-send-signature-not-implemented"))
        console.print(_("cli-fattura-send-signature-manual-hint"))

        # Step 3: Send via PEC
        console.print(f"\n{_('cli-fattura-send-step3-pec')}")

        if not Confirm.ask(_("cli-fattura-send-confirm"), default=False):
            console.print(f"\n{_('cli-fattura-send-cancelled')}")
            db.commit()
            return

        from openfatture.utils.email.sender import TemplatePECSender

        sender = TemplatePECSender(settings=settings, locale=settings.locale)
        xml_path = service.get_xml_path(fattura)

        # Note: For production, integrate digital signature here
        # For now, send unsigned XML (acceptable for testing)
        success, error = sender.send_invoice_to_sdi(fattura, xml_path, signed=False)

        if success:
            console.print(_("cli-fattura-sent-successfully"))

            db.commit()

            # Publish InvoiceSentEvent
            event_bus = get_event_bus()
            if event_bus:
                event_bus.publish(
                    InvoiceSentEvent(
                        invoice_id=fattura.id,
                        invoice_number=f"{fattura.numero}/{fattura.anno}",
                        recipient=fattura.cliente.codice_destinatario or settings.sdi_pec_address,
                        pec_address=settings.sdi_pec_address,
                        xml_path=str(xml_path),
                        signed=False,
                    )
                )

            console.print(
                f"\n{_('cli-fattura-sent-success-message', numero=fattura.numero, anno=fattura.anno)}"
            )
            console.print(f"\n{_('cli-fattura-sent-email-details')}")
            console.print(f"  {_('cli-fattura-sent-email-format')}")
            console.print(
                f"  {_('cli-fattura-sent-email-branding', color=settings.email_primary_color)}"
            )
            console.print(
                f"  {_('cli-fattura-sent-email-language', language=settings.locale.upper())}"
            )
            console.print(f"\n{_('cli-fattura-sent-notifications-header')}")
            if settings.notification_enabled and settings.notification_email:
                console.print(
                    f"  {_('cli-fattura-sent-notifications-enabled', email=settings.notification_email)}"
                )
                console.print(f"  {_('cli-fattura-sent-notifications-process-cmd')}")
            else:
                console.print(f"  {_('cli-fattura-sent-notifications-disabled')}")
            console.print(f"\n{_('cli-fattura-sent-monitor-pec')}")

        else:
            console.print(_("cli-fattura-send-failed", error=error))

            # Still save the XML
            db.commit()

            console.print(f"\n{_('cli-fattura-send-manual-steps')}")
            console.print(f"  {_('cli-fattura-send-manual-step1', path=xml_path)}")
            console.print(
                f"  {_('cli-fattura-send-manual-step2', sdi_address=settings.sdi_pec_address)}"
            )
            raise typer.Exit(1)
