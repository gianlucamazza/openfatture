"""Reporting commands."""

from datetime import date
from decimal import Decimal

import typer
from rich.console import Console
from rich.table import Table

from openfatture.payment.application.services.payment_overview import (
    PaymentDueEntry,
    collect_payment_due_summary,
)
from openfatture.storage.database.base import SessionLocal, get_session, init_db
from openfatture.storage.database.models import Fattura, StatoFattura, StatoPagamento
from openfatture.utils.config import get_settings

app = typer.Typer(no_args_is_help=True)
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

    db = _get_session()
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

        by_aliquota: dict[Decimal, dict[str, Decimal]] = defaultdict(
            lambda: {"imponibile": Decimal("0"), "iva": Decimal("0")}
        )

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

    db = _get_session()
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
            if cliente is None:
                # Skip if client was deleted
                continue

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
def report_scadenze(
    finestra: int = typer.Option(
        14,
        "--finestra",
        "-f",
        min=1,
        help='Numero di giorni considerati "in scadenza" (default: 14).',
    ),
) -> None:
    """
    Show overdue and upcoming payment due dates leveraging the Pagamento ledger.

    Example:
        openfatture report scadenze --finestra 21
    """
    ensure_db()

    console.print("\n[bold blue]📅 Payment Due Dates Overview[/bold blue]\n")

    db = _get_session()
    try:
        summary = collect_payment_due_summary(db, window_days=finestra, max_upcoming=20)

        has_entries = any(summary.overdue or summary.due_soon or summary.upcoming)

        if not has_entries:
            console.print("[green]✅ No outstanding payments. All invoices are settled![/green]\n")
            return

        section_config = [
            ("overdue", "[red]🔥 Scaduti[/red]", "red"),
            (
                "due_soon",
                f"[yellow]⏰ In scadenza (<= {finestra} giorni)[/yellow]",
                "yellow",
            ),
            ("upcoming", "[cyan]📆 Prossimi pagamenti[/cyan]", "cyan"),
        ]

        def _format_money(amount: Decimal) -> str:
            return f"€{amount:,.2f}"

        def _format_days(delta: int) -> str:
            if delta < 0:
                return f"[red]{delta}[/red]"
            if delta == 0:
                return "[yellow]0[/yellow]"
            return f"[green]+{delta}[/green]"

        def _label_for(entry: PaymentDueEntry) -> str:
            mapping = {
                StatoPagamento.SCADUTO: "Scaduto",
                StatoPagamento.PAGATO_PARZIALE: "Parziale",
                StatoPagamento.DA_PAGARE: "Da pagare",
            }
            return mapping.get(entry.status, entry.status.value.replace("_", " ").title())

        for key, title, color in section_config:
            rows = getattr(summary, key)
            if not rows:
                continue

            console.print(title)
            table = Table(
                show_header=True,
                header_style="bold",
                show_lines=False,
                box=None,
            )
            table.add_column("Fattura", style="cyan", no_wrap=True, min_width=10)
            table.add_column("Cliente", style="white", no_wrap=True, min_width=18)
            table.add_column("Scadenza", justify="center")
            table.add_column("Δ giorni", justify="right")
            table.add_column("Residuo", justify="right")
            table.add_column("Pagato", justify="right")
            table.add_column("Totale", justify="right")
            table.add_column("Stato", justify="left")

            for item in rows:
                residual_display = f"[bold {color}]{_format_money(item.residual)}[/bold {color}]"
                paid_display = _format_money(item.paid)
                total_display = _format_money(item.total)
                table.add_row(
                    item.invoice_ref,
                    item.client_name,
                    item.due_date.isoformat(),
                    _format_days(item.days_delta),
                    residual_display,
                    paid_display,
                    total_display,
                    _label_for(item),
                )

            console.print(table)

            total_residual = sum(item.residual for item in rows)
            console.print(
                f"[bold {color}]Totale residuo: {_format_money(total_residual)} • Pagamenti: {len(rows)}[/]",
            )
            console.print()

        if summary.hidden_upcoming > 0:
            console.print(
                f"[dim]… {summary.hidden_upcoming} ulteriori pagamenti futuri non mostrati. Usa --finestra o esporta dati dal modulo payment per maggiori dettagli.[/dim]\n"
            )

        console.print(
            f"[bold]Totale residuo complessivo: {_format_money(summary.total_outstanding)}[/bold]\n"
        )

    finally:
        db.close()
