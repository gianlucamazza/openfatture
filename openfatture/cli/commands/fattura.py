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
from openfatture.cli.output import remember_result
from openfatture.i18n import _, get_locale

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
    remember_result(result)

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
            if invoice.get("collection_statement"):
                console.print(
                    f"  Dichiarazione: {invoice['collection_statement']['value']} · fonte: {invoice['collection_statement']['source']}",
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
    for invoice in result["fatture"]:
        if invoice.get("collection_statement"):
            statement = invoice["collection_statement"]
            console.print(
                f"{invoice['numero']}/{invoice['anno']} · dichiarazione: {statement['value']} · fonte: {statement['source']}",
                markup=False,
            )

    if result.get("has_more"):
        console.print("[dim]... and more. Use --limit to see more results.[/dim]")


@app.command("show")
def show_invoice(
    fattura_id: int = typer.Argument(..., help="Invoice ID"),
) -> None:
    """Show detailed invoice information."""
    result = get_invoice_details(fattura_id=fattura_id)
    remember_result(result)

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

    if result.get("collection_statement"):
        console.print(
            f"Dichiarazione: {result['collection_statement']['value']} · fonte: {result['collection_statement']['source']}",
            markup=False,
        )

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
    remember_result(result)

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
    iva: float = typer.Option(
        None, "--iva", help="VAT rate (%; default 0 with N2.2 for forfettario, else 22)"
    ),
    unita: str = typer.Option("ore", "--unit", "-u", help="Unit of measure (default: ore)"),
    natura: str = typer.Option(
        None, "--natura", help="VAT natura for a 0% rate (e.g. N2.2, N1 for the stamp duty)"
    ),
) -> None:
    """Add line item to an invoice."""
    result = create_riga(
        fattura_id=fattura_id,
        descrizione=descrizione,
        quantita=quantita,
        prezzo_unitario=prezzo,
        aliquota_iva=iva,
        unita_misura=unita,
        natura=natura,
    )
    remember_result(result)

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
    from openfatture.pdf.tool_ops import generate_invoice_pdf

    result = generate_invoice_pdf(
        fattura_id=fattura_id, output_path=output, template=template, logo_path=logo
    )
    remember_result(result)
    if not result.get("success"):
        console.print(f"[red]Error:[/red] {result['error']}")
        raise typer.Exit(code=1)

    console.print("[green]✓[/green] PDF generated successfully")
    console.print(f"Output: [cyan]{result['pdf_path']}[/cyan]")
    console.print(f"Size: {result['file_size']:,} bytes")


@app.command("generate-xml")
def generate_xml(
    fattura_id: int = typer.Argument(..., help="Invoice ID"),
    output: str = typer.Option(None, "--output", "-o", help="Output XML file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show XML without writing file"),
) -> None:
    """Generate FatturaPA XML for an invoice."""
    from openfatture.sdi.application.invoice_sdi_ops import generate_invoice_xml

    result = generate_invoice_xml(fattura_id, output_path=output, dry_run=dry_run)
    remember_result(result)
    if "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        raise typer.Exit(code=1)

    if dry_run:
        console.print("[green]✓[/green] XML generated successfully (dry-run mode)")
        console.print("\n[bold]XML Content:[/bold]")
        console.print(result["xml_content"])
        return
    console.print("[green]✓[/green] XML generated successfully")
    console.print(f"Output: [cyan]{result['xml_path']}[/cyan]")
    console.print(f"Size: {result['file_size']:,} bytes")


@app.command("set-status")
def set_status(
    fattura_id: int = typer.Argument(..., help="Invoice ID"),
    status: str = typer.Argument(..., help="New status (bozza, da_inviare)"),
) -> None:
    """Update invoice status."""
    result = update_invoice_status(fattura_id=fattura_id, new_status=status)
    remember_result(result)

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
    remember_result(result)

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
    from openfatture.sdi.application.journal_ops import list_sdi_journal

    journal = list_sdi_journal()
    remember_result(journal)
    for attempt in journal["submissions"]:
        console.print(
            f"Invio #{attempt['id']} · fattura {attempt['invoice_id']} · "
            f"{attempt['filename']} · {attempt['outcome']}",
            markup=False,
        )
    for receipt in journal["receipts"]:
        console.print(
            f"Ricevuta #{receipt['id']} · fattura {receipt['invoice_id']} · "
            f"{receipt['outcome']} · origine {receipt['source']}",
            markup=False,
        )


@app.command("associate-receipt")
def associate_receipt(
    receipt_id: int, invoice_id: int, evidence: str = typer.Option(..., "--evidence")
) -> None:
    """Associate an unresolved receipt after explicit human verification."""
    from openfatture.sdi.application import journal_ops

    if not typer.confirm(
        f"Associare ricevuta {receipt_id} alla fattura {invoice_id}?", default=False
    ):
        raise typer.Abort()
    result = journal_ops.associate_receipt(receipt_id, invoice_id, evidence)
    remember_result(result)
    if "error" in result:
        console.print(result["error"], markup=False)
        raise typer.Exit(1)
    console.print("Ricevuta associata")


@app.command("resolve-submission")
def resolve_submission_command(
    attempt_id: int,
    sent: bool = typer.Option(..., "--sent/--not-sent"),
    evidence: str = typer.Option(..., "--evidence"),
) -> None:
    """Resolve an uncertain PEC attempt only after checking transport evidence."""
    from openfatture.sdi.application.journal_ops import resolve_submission_attempt

    if not typer.confirm(f"Confermare verifica invio {attempt_id}: inviato={sent}?", default=False):
        raise typer.Abort()
    result = resolve_submission_attempt(attempt_id, sent=sent, evidence=evidence)
    remember_result(result)
    if "error" in result:
        console.print(result["error"], markup=False)
        raise typer.Exit(1)
    console.print("Verifica registrata")
