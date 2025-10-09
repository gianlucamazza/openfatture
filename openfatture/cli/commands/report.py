"""Reporting commands."""

from datetime import date

import typer
from rich.console import Console
from rich.table import Table

from openfatture.storage.database.base import SessionLocal, init_db
from openfatture.storage.database.models import Fattura, StatoFattura
from openfatture.utils.config import get_settings

app = typer.Typer()
console = Console()


def ensure_db() -> None:
    """Ensure database is initialized."""
    settings = get_settings()
    init_db(str(settings.database_url))


@app.command("iva")
def report_iva(
    anno: int = typer.Option(date.today().year, "--anno", help="Year"),
    trimestre: str | None = typer.Option(None, "--trimestre", help="Quarter (Q1-Q4)"),
) -> None:
    """
    Generate VAT report.

    Example:
        openfatture report iva --anno 2025 --trimestre Q1
    """
    ensure_db()

    console.print(f"\n[bold blue]📊 VAT Report - {anno}[/bold blue]")

    if trimestre:
        quarter_months = {
            "Q1": (1, 3),
            "Q2": (4, 6),
            "Q3": (7, 9),
            "Q4": (10, 12),
        }

        if trimestre.upper() not in quarter_months:
            console.print("[red]Invalid quarter. Use Q1, Q2, Q3, or Q4[/red]")
            return

        mese_inizio, mese_fine = quarter_months[trimestre.upper()]
        console.print(f"[cyan]Quarter: {trimestre.upper()} ({mese_inizio}-{mese_fine})[/cyan]\n")
    else:
        mese_inizio, mese_fine = 1, 12
        console.print("[cyan]Full year[/cyan]\n")

    db = SessionLocal()
    try:
        # Query invoices
        query = (
            db.query(Fattura)
            .filter(Fattura.anno == anno)
            .filter(Fattura.stato != StatoFattura.BOZZA)
        )

        # Filter by quarter if specified
        if trimestre:
            from sqlalchemy import extract

            query = query.filter(
                extract("month", Fattura.data_emissione) >= mese_inizio,
                extract("month", Fattura.data_emissione) <= mese_fine,
            )

        fatture = query.all()

        if not fatture:
            console.print("[yellow]No invoices found for the selected period[/yellow]")
            return

        # Calculate totals
        totale_imponibile = sum(f.imponibile for f in fatture)
        totale_iva = sum(f.iva for f in fatture)
        totale_fatturato = sum(f.totale for f in fatture)

        # Summary table
        table = Table(title="VAT Summary", show_lines=True)
        table.add_column("Metric", style="cyan", width=25)
        table.add_column("Amount", style="white", justify="right", width=15)

        table.add_row("Number of invoices", str(len(fatture)))
        table.add_row("Total imponibile", f"€{totale_imponibile:,.2f}")
        table.add_row("Total VAT", f"€{totale_iva:,.2f}")
        table.add_row("[bold]Total revenue[/bold]", f"[bold]€{totale_fatturato:,.2f}[/bold]")

        console.print(table)

        # By VAT rate
        console.print("\n[bold]Breakdown by VAT rate:[/bold]")

        from collections import defaultdict
        from decimal import Decimal

        by_aliquota = defaultdict(lambda: {"imponibile": Decimal("0"), "iva": Decimal("0")})

        for f in fatture:
            for riga in f.righe:
                aliquota = riga.aliquota_iva
                by_aliquota[aliquota]["imponibile"] += riga.imponibile
                by_aliquota[aliquota]["iva"] += riga.iva

        aliquote_table = Table()
        aliquote_table.add_column("VAT Rate", style="cyan", width=15)
        aliquote_table.add_column("Imponibile", justify="right", width=15)
        aliquote_table.add_column("VAT", justify="right", width=15)

        for aliquota in sorted(by_aliquota.keys()):
            data = by_aliquota[aliquota]
            aliquote_table.add_row(
                f"{aliquota}%",
                f"€{data['imponibile']:,.2f}",
                f"€{data['iva']:,.2f}",
            )

        console.print(aliquote_table)
        console.print()

    finally:
        db.close()


@app.command("clienti")
def report_clienti(
    anno: int = typer.Option(date.today().year, "--anno", help="Year"),
) -> None:
    """
    Generate client revenue report.

    Example:
        openfatture report clienti --anno 2025
    """
    ensure_db()

    console.print(f"\n[bold blue]📊 Client Revenue Report - {anno}[/bold blue]\n")

    db = SessionLocal()
    try:
        from sqlalchemy import func

        # Query with aggregation
        results = (
            db.query(
                Fattura.cliente_id,
                func.count(Fattura.id).label("num_fatture"),
                func.sum(Fattura.totale).label("totale_fatturato"),
            )
            .filter(Fattura.anno == anno)
            .filter(Fattura.stato != StatoFattura.BOZZA)
            .group_by(Fattura.cliente_id)
            .order_by(func.sum(Fattura.totale).desc())
            .all()
        )

        if not results:
            console.print("[yellow]No invoices found for the selected year[/yellow]")
            return

        table = Table(title=f"Top Clients - {anno}", show_lines=False)
        table.add_column("Rank", style="dim", width=6, justify="right")
        table.add_column("Client", style="cyan")
        table.add_column("Invoices", justify="right", width=10)
        table.add_column("Revenue", style="green", justify="right", width=15)

        for i, (cliente_id, num_fatture, totale) in enumerate(results, 1):
            from openfatture.storage.database.models import Cliente

            cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()

            table.add_row(
                str(i),
                cliente.denominazione,
                str(num_fatture),
                f"€{totale:,.2f}",
            )

        console.print(table)

        # Total
        totale_generale = sum(r[2] for r in results)
        console.print(f"\n[bold]Total revenue: €{totale_generale:,.2f}[/bold]\n")

    finally:
        db.close()


@app.command("scadenze")
def report_scadenze() -> None:
    """
    Show upcoming payment due dates.

    Example:
        openfatture report scadenze
    """
    ensure_db()

    console.print("\n[bold blue]📅 Upcoming Payment Due Dates[/bold blue]\n")

    console.print("[yellow]⚠ Payment tracking not yet fully implemented[/yellow]")
    console.print(
        "[dim]This will show all overdue and upcoming payments from the Pagamento table.[/dim]\n"
    )

    # Placeholder
    console.print("Example output:")
    console.print("  [red]OVERDUE:[/red] Invoice 001/2025 - Client ABC - €1,500 (due 2025-01-15)")
    console.print(
        "  [yellow]DUE SOON:[/yellow] Invoice 003/2025 - Client XYZ - €2,300 (due 2025-02-28)"
    )
