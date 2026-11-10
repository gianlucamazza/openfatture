"""Fattura (invoice) management CLI commands."""

from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from openfatture.billing.application.invoice_commands import (
    create_invoice,
    update_invoice_status,
)
from openfatture.billing.application.invoice_queries import (
    get_invoice_details,
    search_invoices,
)
from openfatture.billing.application.line_commands import create_riga
from openfatture.cli.output import format_eur, remember_result
from openfatture.i18n import _

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
        console.print(_("cli-common-error", error=result["error"]))
        raise typer.Exit(code=1)

    if result["count"] == 0:
        console.print(_("cli-fattura-none-found"))
        return

    if console.width < 120:
        _print_invoice_cards(result)
    else:
        _print_invoice_table(result)


_PAYMENT_STATUS = {
    "no_payment_record": "cli-invoice-no-payment-record",
    "unpaid": "cli-invoice-unpaid",
    "partially_paid": "cli-invoice-partially-paid",
    "fully_paid": "cli-invoice-fully-paid",
}
_COLUMNS = {
    "collected": "cli-invoice-collected",
    "residual": "cli-invoice-residual",
    "collection": "cli-invoice-collection",
    "document": "cli-invoice-document",
    "total": "cli-invoice-total",
}


def _payment_status(status: str) -> str:
    return _(_PAYMENT_STATUS[status])


def _paid_amount(invoice: dict[str, Any], field: str) -> str:
    """Format an amount; collected cash is unknown without any payment record."""
    if field == "amount_paid" and invoice["payment_status"] == "no_payment_record":
        return "—"
    return format_eur(invoice[field])


def _statement_text(invoice: dict[str, Any]) -> str:
    statement = invoice["collection_statement"]
    return _("cli-fattura-statement", value=statement["value"], source=statement["source"])


def _print_invoice_cards(result: dict[str, Any]) -> None:
    """Narrow terminals: one block of lines per invoice."""
    console.print(_("cli-fattura-list-title", count=result["count"]))
    for invoice in result["fatture"]:
        _print_invoice_card(invoice)
    if result.get("has_more"):
        console.print("… --limit")


def _print_invoice_card(invoice: dict[str, Any]) -> None:
    console.print(f"{invoice['numero']}/{invoice['anno']} · {invoice['cliente']}", markup=False)
    for field, key in (
        ("importo", "total"),
        ("amount_paid", "collected"),
        ("outstanding", "residual"),
    ):
        value = _paid_amount(invoice, field)
        console.print(f"  {_(_COLUMNS[key])}: {value}", markup=False)
    document = _("cli-invoice-historical") if invoice["issued_elsewhere"] else invoice["stato"]
    if invoice.get("submission_state") in {"pending", "uncertain"}:
        document += " · " + _("cli-fattura-pec-to-verify")
    if invoice.get("status_origin") == "sdi_receipt":
        document += f" · SDI: {invoice['stato']}"
    console.print(
        f"  {invoice['data']} · {document} · {_payment_status(invoice['payment_status'])}",
        markup=False,
    )
    if invoice.get("collection_statement"):
        console.print("  " + _statement_text(invoice), markup=False)
    console.print()


def _table_document(fattura: dict[str, Any]) -> Any:
    if not fattura["issued_elsewhere"]:
        return fattura["stato"]
    sdi = f" · SDI: {fattura['stato']}" if fattura.get("status_origin") == "sdi_receipt" else ""
    return _("cli-invoice-historical") + sdi


def _print_invoice_table(result: dict[str, Any]) -> None:
    """Wide terminals: one table row per invoice, then the owner statements."""
    table = Table(title=_("cli-fattura-list-title", count=result["count"]))
    table.add_column("ID", style="cyan")
    table.add_column(_("cli-common-number"))
    table.add_column(_("cli-common-date"))
    table.add_column(_("cli-common-client"), style="green")
    table.add_column(_("cli-common-amount"), justify="right")
    for key in ("collected", "residual", "collection", "document"):
        table.add_column(
            _(_COLUMNS[key]), justify="right" if key in ("collected", "residual") else "left"
        )

    for fattura in result["fatture"]:
        table.add_row(
            str(fattura["id"]),
            f"{fattura['numero']}/{fattura['anno']}",
            fattura["data"],
            fattura["cliente"],
            format_eur(fattura["importo"]),
            _paid_amount(fattura, "amount_paid"),
            format_eur(fattura["outstanding"]),
            _payment_status(fattura["payment_status"]),
            _table_document(fattura),
        )

    console.print(table)
    for invoice in result["fatture"]:
        if invoice.get("collection_statement"):
            console.print(
                f"{invoice['numero']}/{invoice['anno']} · " + _statement_text(invoice),
                markup=False,
            )

    if result.get("has_more"):
        console.print(_("cli-common-more-results"))


@app.command("show")
def show_invoice(
    fattura_id: int = typer.Argument(..., help="Invoice ID"),
) -> None:
    """Show detailed invoice information."""
    result = get_invoice_details(fattura_id=fattura_id)
    remember_result(result)

    if "error" in result:
        console.print(_("cli-common-error", error=result["error"]))
        raise typer.Exit(code=1)

    # Display invoice details
    console.print("\n" + _("cli-fattura-show-title", id=str(result["id"])))
    console.print(f"[bold]{_('cli-common-number')}:[/bold] {result['numero']}/{result['anno']}")
    console.print(f"[bold]{_('cli-common-date')}:[/bold] {result['data_emissione']}")
    console.print(f"[bold]{_('cli-common-status')}:[/bold] {result['stato']}")

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
        console.print(_("cli-fattura-submission-unverified"))
    for receipt in result.get("sdi_evidence", []):
        console.print(
            f"SDI #{receipt['id']} · {receipt['source']} · {receipt['outcome']}", markup=False
        )
    console.print(_("cli-invoice-collection") + ": " + _payment_status(result["payment_status"]))
    for field, label in (("amount_paid", "collected"), ("outstanding", "residual")):
        value = (
            "—"
            if field == "amount_paid" and result["payment_status"] == "no_payment_record"
            else format_eur(result[field])
        )
        console.print(_(_COLUMNS[label]) + ": " + value)

    if result.get("collection_statement"):
        statement = result["collection_statement"]
        console.print(
            _("cli-fattura-statement", value=statement["value"], source=statement["source"]),
            markup=False,
        )

    # Client
    cliente = result.get("cliente", {})
    console.print(f"\n[bold]{_('cli-common-client')}:[/bold]")
    console.print(f"  {cliente.get('denominazione') or _('cli-common-not-available')}")
    if cliente.get("partita_iva"):
        console.print(f"  {_('cli-common-vat-number')}: {cliente['partita_iva']}")

    # Amounts
    importi = result.get("importi", {})
    console.print(f"\n[bold]{_('cli-fattura-amounts')}:[/bold]")
    console.print(f"  {_('cli-fattura-taxable')}: {format_eur(importi.get('imponibile', 0))}")
    console.print(f"  {_('cli-fattura-vat')}: {format_eur(importi.get('iva', 0))}")
    console.print(
        f"  [bold]{_('cli-invoice-total')}: {format_eur(importi.get('totale', 0))}[/bold]"
    )

    for payment in result.get("pagamenti", []):
        console.print(
            f"  #{payment['id']} · {_('cli-invoice-collected')}: {format_eur(payment['incassato'])} · {_('cli-invoice-residual')}: {format_eur(payment['residuo'])}",
            markup=False,
        )

    # Line items
    console.print("\n" + _("cli-fattura-line-items", count=result["righe_count"]))
    if result.get("righe"):
        table = Table()
        table.add_column(_("cli-fattura-column-description"), style="green")
        table.add_column(_("cli-fattura-column-quantity"), justify="right")
        table.add_column(_("cli-fattura-column-unit-price"), justify="right")
        table.add_column(_("cli-fattura-column-vat-rate"), justify="right")

        for riga in result["righe"]:
            table.add_row(
                riga["descrizione"],
                f"{riga['quantita']:.2f}",
                format_eur(riga["prezzo_unitario"]),
                f"{riga['aliquota_iva']:.0f}%",
            )

        console.print(table)

    # Notes
    if result.get("note"):
        console.print(f"\n[bold]{_('cli-common-notes')}:[/bold]")
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
        console.print(_("cli-common-error", error=result["error"]))
        raise typer.Exit(code=1)

    console.print(f"[green]✓[/green] {result['message']}")
    console.print(_("cli-fattura-created-id", id=str(result["invoice_id"])))
    console.print(f"{_('cli-common-number')}: {result['numero']}/{result['anno']}")
    console.print(f"{_('cli-common-client')}: {result['cliente']}")
    console.print(f"{_('cli-common-status')}: {result['stato']}")


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
        console.print(_("cli-common-error", error=result["error"]))
        raise typer.Exit(code=1)

    console.print(f"[green]✓[/green] {result['message']}")
    console.print(
        _("cli-fattura-line", numero=str(result["numero_riga"]), descrizione=result["descrizione"])
    )
    console.print(f"{_('cli-invoice-total')}: {format_eur(result['totale'])}")
    console.print(
        f"{_('cli-fattura-invoice-total')}: [bold]{format_eur(result['invoice_totale'])}[/bold]"
    )


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
        console.print(_("cli-common-error", error=result["error"]))
        raise typer.Exit(code=1)

    console.print(_("cli-fattura-pdf-generated"))
    console.print(_("cli-fattura-output", path=str(result["pdf_path"])))
    console.print(_("cli-fattura-size", size=result["file_size"]))


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
        console.print(_("cli-common-error", error=result["error"]))
        raise typer.Exit(code=1)

    if dry_run:
        console.print(_("cli-fattura-xml-generated-dry-run"))
        console.print("\n" + _("cli-fattura-xml-content"))
        console.print(result["xml_content"])
        return
    console.print(_("cli-fattura-xml-generated"))
    console.print(_("cli-fattura-output", path=str(result["xml_path"])))
    console.print(_("cli-fattura-size", size=result["file_size"]))


@app.command("set-status")
def set_status(
    fattura_id: int = typer.Argument(..., help="Invoice ID"),
    status: str = typer.Argument(..., help="New status (bozza, da_inviare)"),
) -> None:
    """Update invoice status."""
    result = update_invoice_status(fattura_id=fattura_id, new_status=status)
    remember_result(result)

    if "error" in result:
        console.print(_("cli-common-error", error=result["error"]))
        raise typer.Exit(code=1)

    console.print(f"[green]✓[/green] {result['message']}")
    console.print(
        _("cli-fattura-status-change", old=result["old_status"], new=result["new_status"])
    )


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
        console.print(_("cli-common-error", error=result["error"]))
        raise typer.Exit(code=1)

    console.print(f"[green]✓[/green] {result['message']}")
    source = result["source_invoice"]
    console.print(_("cli-fattura-credit-note-id", id=str(result["nota_credito_id"])))
    console.print(f"{_('cli-common-number')}: {result['numero']}/{result['anno']}")
    console.print(f"{_('cli-fattura-document-type')}: {result['tipo_documento']}")
    console.print(f"{_('cli-common-client')}: {result['cliente']}")
    console.print(f"{_('cli-invoice-total')}: [bold]{format_eur(result['totale'])}[/bold]")
    console.print("\n" + _("cli-fattura-source-invoice"))
    console.print(f"  ID: {source['id']}")
    console.print(f"  {_('cli-common-number')}: {source['numero']}")
    console.print(f"  {_('cli-common-date')}: {source['data']}")


@app.command("sdi-journal")
def sdi_journal() -> None:
    """Inspect recorded submissions and imported receipts without sending anything."""
    from openfatture.sdi.application.journal_ops import list_sdi_journal

    journal = list_sdi_journal()
    remember_result(journal)
    for attempt in journal["submissions"]:
        console.print(
            _(
                "cli-fattura-journal-submission",
                id=str(attempt["id"]),
                invoice=str(attempt["invoice_id"]),
                filename=attempt["filename"],
                outcome=attempt["outcome"],
            ),
            markup=False,
        )
    for receipt in journal["receipts"]:
        console.print(
            _(
                "cli-fattura-journal-receipt",
                id=str(receipt["id"]),
                invoice=str(receipt["invoice_id"]),
                outcome=receipt["outcome"],
                source=receipt["source"],
            ),
            markup=False,
        )


@app.command("associate-receipt")
def associate_receipt(
    receipt_id: int, invoice_id: int, evidence: str = typer.Option(..., "--evidence")
) -> None:
    """Associate an unresolved receipt after explicit human verification."""
    from openfatture.sdi.application import journal_ops

    if not typer.confirm(
        _("cli-fattura-associate-confirm", receipt=str(receipt_id), invoice=str(invoice_id)),
        default=False,
    ):
        raise typer.Abort()
    result = journal_ops.associate_receipt(receipt_id, invoice_id, evidence)
    remember_result(result)
    if "error" in result:
        console.print(result["error"], markup=False)
        raise typer.Exit(1)
    console.print(_("cli-fattura-receipt-associated"))


@app.command("resolve-submission")
def resolve_submission_command(
    attempt_id: int,
    sent: bool = typer.Option(..., "--sent/--not-sent"),
    evidence: str = typer.Option(..., "--evidence"),
) -> None:
    """Resolve an uncertain PEC attempt only after checking transport evidence."""
    from openfatture.sdi.application.journal_ops import resolve_submission_attempt

    if not typer.confirm(
        _(
            "cli-fattura-resolve-confirm",
            attempt=str(attempt_id),
            sent="yes" if sent else "no",
        ),
        default=False,
    ):
        raise typer.Abort()
    result = resolve_submission_attempt(attempt_id, sent=sent, evidence=evidence)
    remember_result(result)
    if "error" in result:
        console.print(result["error"], markup=False)
        raise typer.Exit(1)
    console.print(_("cli-fattura-submission-resolved"))
