"""Fattura (invoice) management CLI commands."""

import typer
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
from openfatture.pdf.generator import PDFGenerator, PDFGeneratorConfig
from openfatture.platform.config import get_settings
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Fattura

app = typer.Typer(name="fattura", help="Manage invoices")
console = Console()


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

    # Display as table
    table = Table(title=f"Invoices ({result['count']})")
    table.add_column("ID", style="cyan")
    table.add_column("Number")
    table.add_column("Date")
    table.add_column("Client", style="green")
    table.add_column("Amount", justify="right")
    table.add_column("Status")

    for fattura in result["fatture"]:
        table.add_row(
            str(fattura["id"]),
            f"{fattura['numero']}/{fattura['anno']}",
            fattura["data"],
            fattura["cliente"],
            f"€ {fattura['importo']:.2f}",
            fattura["stato"],
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
    """Generate FatturaPA XML for an invoice (dry-run mode)."""
    from openfatture.billing.fatture.service import InvoiceService

    settings = get_settings()
    session = get_session()
    try:
        service = InvoiceService(settings)

        fattura = session.query(Fattura).filter(Fattura.id == fattura_id).first()
        if not fattura:
            console.print(f"[red]Error:[/red] Invoice {fattura_id} not found")
            raise typer.Exit(code=1)

        # Get XML path (or generate)
        xml_path = service.get_xml_path(fattura)

        if xml_path.exists():
            console.print(f"[green]✓[/green] XML already exists: [cyan]{xml_path}[/cyan]")

            if dry_run:
                console.print("\n[bold]XML Content:[/bold]")
                console.print(xml_path.read_text())
        else:
            console.print("[yellow]XML generation not yet implemented in CLI[/yellow]")
            console.print(
                f"Use the assistant: [cyan]openfatture assistant 'genera XML per fattura {fattura_id}'[/cyan]"
            )

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
