"""Fattura (invoice) management CLI commands."""

import typer
from babel.numbers import format_currency
from rich.console import Console
from rich.table import Table

from openfatture.billing.application.invoice_commands import (
    create_invoice,
    create_riga,
    update_invoice_status,
)
from openfatture.billing.application.invoice_queries import (
    get_invoice_details,
    search_invoices,
)
from openfatture.i18n import _, get_locale
from openfatture.pdf.generator import PDFGenerator, PDFGeneratorConfig
from openfatture.platform.config import get_settings
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Fattura

app = typer.Typer(name="fattura", help="Manage invoices")
console = Console()


@app.callback()
def prepare_database() -> None:
    from openfatture.cli.database import ensure_database

    ensure_database()


@app.command("list")
def list_invoices(
    query: str = typer.Option(None, "--query", "-q", help="Search by number or notes"),
    anno: int = typer.Option(None, "--year", "-y", help="Filter by year"),
    stato: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    cliente_id: int = typer.Option(None, "--client", "-c", help="Filter by client ID"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of results"),
) -> None:
    """List and search invoices."""
    result = search_invoices(
        query=query,
        anno=anno,
        stato=stato,
        cliente_id=cliente_id,
        limit=limit,
    )

    if "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        raise typer.Exit(code=1)

    if result["count"] == 0:
        console.print("[yellow]No invoices found.[/yellow]")
        return

    if console.width < 120:
        console.print(f"Invoices ({result['count']})")
        for invoice in result["fatture"]:
            console.print(
                f"{invoice['numero']}/{invoice['anno']} · {invoice['cliente']}", markup=False
            )
            for field, key in (
                ("importo", "total"),
                ("amount_paid", "collected"),
                ("outstanding", "residual"),
            ):
                value = (
                    "—"
                    if field == "amount_paid" and invoice["payment_status"] == "no_payment_record"
                    else format_currency(invoice[field], "EUR", locale=get_locale())
                )
                console.print(f"  {_('cli-invoice-' + key)}: {value}", markup=False)
            document = (
                _("cli-invoice-historical") if invoice["issued_elsewhere"] else invoice["stato"]
            )
            if invoice.get("submission_state") in {"pending", "uncertain"}:
                document += " · PEC: da verificare"
            if invoice.get("status_origin") == "sdi_receipt":
                document += f" · SDI: {invoice['stato']}"
            console.print(
                f"  {invoice['data']} · {document} · {_('cli-invoice-' + invoice['payment_status'])}",
                markup=False,
            )
            console.print()
        if result.get("has_more"):
            console.print("… --limit")
        return

    # Display as table
    table = Table(title=f"Invoices ({result['count']})")
    table.add_column("ID", style="cyan")
    table.add_column("Number")
    table.add_column("Date")
    table.add_column("Client", style="green")
    table.add_column("Amount", justify="right")
    for key in ("collected", "residual", "collection", "document"):
        table.add_column(
            _("cli-invoice-" + key), justify="right" if key in ("collected", "residual") else "left"
        )

    for fattura in result["fatture"]:
        table.add_row(
            str(fattura["id"]),
            f"{fattura['numero']}/{fattura['anno']}",
            fattura["data"],
            fattura["cliente"],
            format_currency(fattura["importo"], "EUR", locale=get_locale()),
            "—"
            if fattura["payment_status"] == "no_payment_record"
            else format_currency(fattura["amount_paid"], "EUR", locale=get_locale()),
            format_currency(fattura["outstanding"], "EUR", locale=get_locale()),
            _("cli-invoice-" + fattura["payment_status"]),
            (
                _("cli-invoice-historical")
                + (
                    f" · SDI: {fattura['stato']}"
                    if fattura.get("status_origin") == "sdi_receipt"
                    else ""
                )
            )
            if fattura["issued_elsewhere"]
            else fattura["stato"],
        )

    console.print(table)

    if result.get("has_more"):
        console.print("[dim]... and more. Use --limit to see more results.[/dim]")


@app.command("show")
def show_invoice(
    fattura_id: int = typer.Argument(..., help="Invoice ID"),
) -> None:
    """Show detailed invoice information."""
    result = get_invoice_details(fattura_id=fattura_id)

    if "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        raise typer.Exit(code=1)

    # Display invoice details
    console.print(f"\n[bold cyan]Invoice #{result['id']}[/bold cyan]")
    console.print(f"[bold]Number:[/bold] {result['numero']}/{result['anno']}")
    console.print(f"[bold]Date:[/bold] {result['data_emissione']}")
    console.print(f"[bold]Status:[/bold] {result['stato']}")

    console.print(
        _("cli-invoice-document")
        + ": "
        + (_("cli-invoice-historical") if result["issued_elsewhere"] else result["stato"])
    )
    if result["issued_elsewhere"] and result.get("status_origin") != "sdi_receipt":
        console.print(_("cli-invoice-historical-note"))
    for attempt in result.get("submission_evidence", []):
        console.print(f"PEC #{attempt['id']} · {attempt['outcome']}", markup=False)
    if result.get("submission_state") in {"pending", "uncertain"}:
        console.print("Esito invio da verificare; non ripetere automaticamente la trasmissione.")
    for receipt in result.get("sdi_evidence", []):
        console.print(
            f"SDI #{receipt['id']} · {receipt['source']} · {receipt['outcome']}", markup=False
        )
    console.print(_("cli-invoice-collection") + ": " + _("cli-invoice-" + result["payment_status"]))
    for field, label in (("amount_paid", "collected"), ("outstanding", "residual")):
        value = (
            "—"
            if field == "amount_paid" and result["payment_status"] == "no_payment_record"
            else format_currency(result[field], "EUR", locale=get_locale())
        )
        console.print(_("cli-invoice-" + label) + ": " + value)

    # Client
    cliente = result.get("cliente", {})
    console.print("\n[bold]Client:[/bold]")
    console.print(f"  {cliente.get('denominazione', 'N/A')}")
    if cliente.get("partita_iva"):
        console.print(f"  P.IVA: {cliente['partita_iva']}")

    # Amounts
    importi = result.get("importi", {})
    console.print("\n[bold]Amounts:[/bold]")
    console.print(f"  Imponibile: € {importi.get('imponibile', 0):.2f}")
    console.print(f"  IVA:        € {importi.get('iva', 0):.2f}")
    console.print(f"  [bold]Total:      € {importi.get('totale', 0):.2f}[/bold]")

    for payment in result.get("pagamenti", []):
        console.print(
            f"  #{payment['id']} · {_('cli-invoice-collected')}: {format_currency(payment['incassato'], 'EUR', locale=get_locale())} · {_('cli-invoice-residual')}: {format_currency(payment['residuo'], 'EUR', locale=get_locale())}",
            markup=False,
        )

    # Line items
    console.print(f"\n[bold]Line Items:[/bold] {result['righe_count']} total")
    if result.get("righe"):
        table = Table()
        table.add_column("Description", style="green")
        table.add_column("Qty", justify="right")
        table.add_column("Unit Price", justify="right")
        table.add_column("IVA %", justify="right")

        for riga in result["righe"]:
            table.add_row(
                riga["descrizione"],
                f"{riga['quantita']:.2f}",
                f"€ {riga['prezzo_unitario']:.2f}",
                f"{riga['aliquota_iva']:.0f}%",
            )

        console.print(table)

    # Notes
    if result.get("note"):
        console.print("\n[bold]Notes:[/bold]")
        console.print(f"  {result['note']}")


@app.command("create")
def create_new_invoice(
    cliente_id: int = typer.Option(..., "--client", "-c", help="Client ID"),
    anno: int = typer.Option(None, "--year", "-y", help="Year (default: current year)"),
    numero: str = typer.Option(
        None, "--number", "-n", help="Invoice number (default: auto-generate)"
    ),
    note: str = typer.Option(None, "--note", help="Notes"),
) -> None:
    """Create a new draft invoice."""
    result = create_invoice(
        cliente_id=cliente_id,
        anno=anno,
        numero=numero,
        note=note,
    )

    if "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        raise typer.Exit(code=1)

    console.print(f"[green]✓[/green] {result['message']}")
    console.print(f"Invoice ID: [cyan]{result['invoice_id']}[/cyan]")
    console.print(f"Number: {result['numero']}/{result['anno']}")
    console.print(f"Client: {result['cliente']}")
    console.print(f"Status: {result['stato']}")


@app.command("add-line")
def add_line_item(
    fattura_id: int = typer.Option(..., "--invoice", "-i", help="Invoice ID"),
    descrizione: str = typer.Option(..., "--desc", "-d", help="Item description"),
    quantita: float = typer.Option(..., "--qty", "-q", help="Quantity"),
    prezzo: float = typer.Option(..., "--price", "-p", help="Unit price (€)"),
    iva: float = typer.Option(22.0, "--iva", help="VAT rate (%, default: 22)"),
    unita: str = typer.Option("ore", "--unit", "-u", help="Unit of measure (default: ore)"),
) -> None:
    """Add line item to an invoice."""
    result = create_riga(
        fattura_id=fattura_id,
        descrizione=descrizione,
        quantita=quantita,
        prezzo_unitario=prezzo,
        aliquota_iva=iva,
        unita_misura=unita,
    )

    if "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        raise typer.Exit(code=1)

    console.print(f"[green]✓[/green] {result['message']}")
    console.print(f"Line #{result['numero_riga']}: {result['descrizione']}")
    console.print(f"Total: € {result['totale']:.2f}")
    console.print(f"Invoice total: [bold]€ {result['invoice_totale']:.2f}[/bold]")


@app.command("generate-pdf")
def generate_pdf(
    fattura_id: int = typer.Argument(..., help="Invoice ID"),
    output: str = typer.Option(None, "--output", "-o", help="Output PDF file path"),
    template: str = typer.Option(
        "professional", "--template", "-t", help="Template (professional/minimalist/branded)"
    ),
    logo: str = typer.Option(None, "--logo", help="Path to company logo"),
) -> None:
    """Generate PDF for an invoice."""
    settings = get_settings()

    # Load invoice from database
    session = get_session()
    try:
        fattura = session.query(Fattura).filter(Fattura.id == fattura_id).first()
        if not fattura:
            console.print(f"[red]Error:[/red] Invoice {fattura_id} not found")
            raise typer.Exit(code=1)

        # Create PDF generator config
        config = PDFGeneratorConfig(
            template=template,
            company_name=settings.cedente_denominazione or "OpenFatture",
            company_vat=settings.cedente_partita_iva,
            company_cf=settings.cedente_codice_fiscale,
            company_address=settings.cedente_indirizzo,
            company_city=f"{settings.cedente_cap} {settings.cedente_comune}".strip(),
            regime_fiscale=settings.cedente_regime_fiscale,
            logo_path=logo,
            enable_qr_code=False,
        )

        generator = PDFGenerator(config)

        # Generate PDF
        pdf_path = generator.generate(fattura, output_path=output)

        console.print("[green]✓[/green] PDF generated successfully")
        console.print(f"Output: [cyan]{pdf_path}[/cyan]")
        console.print(f"Size: {pdf_path.stat().st_size:,} bytes")

    finally:
        session.close()


@app.command("generate-xml")
def generate_xml(
    fattura_id: int = typer.Argument(..., help="Invoice ID"),
    output: str = typer.Option(None, "--output", "-o", help="Output XML file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show XML without writing file"),
) -> None:
    """Generate FatturaPA XML for an invoice."""
    from pathlib import Path

    from openfatture.billing.fatture.service import InvoiceService
    from openfatture.exceptions import XMLValidationError

    settings = get_settings()
    session = get_session()
    try:
        service = InvoiceService(settings)

        fattura = session.query(Fattura).filter(Fattura.id == fattura_id).first()
        if not fattura:
            console.print(f"[red]Error:[/red] Invoice {fattura_id} not found")
            raise typer.Exit(code=1)

        try:
            xml_content, error = service.generate_xml(fattura, validate=False)

            if error:
                console.print(f"[red]Error:[/red] {error}")
                raise typer.Exit(code=1)

            if dry_run:
                console.print("[green]✓[/green] XML generated successfully (dry-run mode)")
                console.print("\n[bold]XML Content:[/bold]")
                console.print(xml_content)
            else:
                if output:
                    xml_path = Path(output)
                else:
                    xml_path = service.get_xml_path(fattura)

                xml_path.parent.mkdir(parents=True, exist_ok=True)
                xml_path.write_text(xml_content, encoding="utf-8")

                session.commit()

                console.print("[green]✓[/green] XML generated successfully")
                console.print(f"Output: [cyan]{xml_path}[/cyan]")
                console.print(f"Size: {xml_path.stat().st_size:,} bytes")

        except XMLValidationError as e:
            console.print(f"[red]XML Validation Error:[/red] {e}")
            raise typer.Exit(code=1) from None

    finally:
        session.close()


@app.command("set-status")
def set_status(
    fattura_id: int = typer.Argument(..., help="Invoice ID"),
    status: str = typer.Argument(..., help="New status (bozza, da_inviare)"),
) -> None:
    """Update invoice status."""
    result = update_invoice_status(fattura_id=fattura_id, new_status=status)

    if "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        raise typer.Exit(code=1)

    console.print(f"[green]✓[/green] {result['message']}")
    console.print(f"Status: {result['old_status']} → {result['new_status']}")


@app.command("create-credit-note")
def create_credit_note(
    from_invoice: int = typer.Option(..., "--from-invoice", "-i", help="Source invoice ID"),
    note: str = typer.Option(None, "--note", "-n", help="Notes for credit note"),
    full_refund: bool = typer.Option(True, "--full", help="Full refund (default: True)"),
) -> None:
    """Create nota di credito (TD04) from an existing invoice."""
    from openfatture.billing.application.nota_credito_ops import (
        create_nota_credito_from_fattura,
    )

    result = create_nota_credito_from_fattura(
        fattura_id=from_invoice,
        note=note,
        full_refund=full_refund,
    )

    if "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        raise typer.Exit(code=1)

    console.print(f"[green]✓[/green] {result['message']}")
    console.print(f"Nota di credito ID: [cyan]{result['nota_credito_id']}[/cyan]")
    console.print(f"Number: {result['numero']}/{result['anno']}")
    console.print(f"Type: {result['tipo_documento']}")
    console.print(f"Client: {result['cliente']}")
    console.print(f"Total: [bold]€ {result['totale']:.2f}[/bold]")
    console.print("\n[dim]Source invoice:[/dim]")
    console.print(f"  ID: {result['source_invoice']['id']}")
    console.print(f"  Number: {result['source_invoice']['numero']}")
    console.print(f"  Date: {result['source_invoice']['data']}")


@app.command("sdi-journal")
def sdi_journal() -> None:
    """Inspect recorded submissions and imported receipts without sending anything."""
    from openfatture.storage.database.models import SDINotificationRecord, SDISubmissionAttempt

    with get_session() as session:
        for attempt in session.query(SDISubmissionAttempt).order_by(SDISubmissionAttempt.id):
            console.print(
                f"Invio #{attempt.id} · fattura {attempt.invoice_id} · {attempt.filename} · {attempt.outcome}",
                markup=False,
            )
        for receipt in session.query(SDINotificationRecord).order_by(SDINotificationRecord.id):
            console.print(
                f"Ricevuta #{receipt.id} · fattura {receipt.invoice_id} · {receipt.outcome} · origine {receipt.source}",
                markup=False,
            )


@app.command("associate-receipt")
def associate_receipt(
    receipt_id: int, invoice_id: int, evidence: str = typer.Option(..., "--evidence")
) -> None:
    """Associate an unresolved receipt after explicit human verification."""
    import json

    from openfatture.sdi.notifiche.parser import NotificaSDI
    from openfatture.sdi.notifiche.processor import NotificationProcessor
    from openfatture.storage.database.models import SDINotificationRecord

    if not typer.confirm(
        f"Associare ricevuta {receipt_id} alla fattura {invoice_id}?", default=False
    ):
        raise typer.Abort()
    with get_session() as session:
        receipt = session.get(SDINotificationRecord, receipt_id)
        if receipt is None or receipt.outcome not in {"unassociated", "association_conflict"}:
            console.print("Ricevuta non associabile")
            raise typer.Exit(1)
        success, error, _notification = NotificationProcessor(session).process_notification(
            NotificaSDI.model_validate(json.loads(receipt.payload)),
            associated_invoice_id=invoice_id,
            association_note=evidence,
        )
        console.print(error or "Ricevuta associata")
        if not success:
            raise typer.Exit(1)


@app.command("resolve-submission")
def resolve_submission_command(
    attempt_id: int,
    sent: bool = typer.Option(..., "--sent/--not-sent"),
    evidence: str = typer.Option(..., "--evidence"),
) -> None:
    """Resolve an uncertain PEC attempt only after checking transport evidence."""
    from openfatture.sdi.application.submissions import resolve_submission

    if not typer.confirm(f"Confermare verifica invio {attempt_id}: inviato={sent}?", default=False):
        raise typer.Abort()
    with get_session() as session:
        try:
            resolve_submission(session, attempt_id, sent=sent, note=evidence)
        except ValueError as exc:
            session.rollback()
            console.print(str(exc), markup=False)
            raise typer.Exit(1) from exc
    console.print("Verifica registrata")
