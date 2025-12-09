"""Reporting commands."""

from datetime import date
from decimal import Decimal

import typer
from rich.console import Console
from rich.table import Table

from openfatture.i18n import _
from openfatture.payment.application.services.payment_overview import (
    PaymentDueEntry,
    collect_payment_due_summary,
)
from openfatture.storage.database.base import init_db
from openfatture.storage.database.models import Fattura, StatoFattura, StatoPagamento
from openfatture.storage.session import db_session
from openfatture.utils.config import get_settings

app = typer.Typer(no_args_is_help=True)
console = Console()


def ensure_db() -> None:
    """Ensure database is initialized."""
    settings = get_settings()
    init_db(str(settings.database_url))


@app.command("iva")
def report_iva(
    anno: int = typer.Option(date.today().year, "--anno", help=_("cli-report-iva-help-anno")),
    trimestre: str | None = typer.Option(
        None, "--trimestre", help=_("cli-report-iva-help-trimestre")
    ),
) -> None:
    """
    Generate VAT report.

    Example:
        openfatture report iva --anno 2025 --trimestre Q1
    """
    ensure_db()

    console.print(_("cli-report-iva-title", anno=anno))

    if trimestre:
        quarter_months = {
            "Q1": (1, 3),
            "Q2": (4, 6),
            "Q3": (7, 9),
            "Q4": (10, 12),
        }

        if trimestre.upper() not in quarter_months:
            console.print(_("cli-report-iva-error-invalid-quarter"))
            return

        mese_inizio, mese_fine = quarter_months[trimestre.upper()]
        console.print(
            _(
                "cli-report-iva-quarter",
                trimestre=trimestre.upper(),
                mese_inizio=mese_inizio,
                mese_fine=mese_fine,
            )
        )
    else:
        mese_inizio, mese_fine = 1, 12
        console.print(_("cli-report-iva-full-year"))

    with db_session() as db:
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
            console.print(_("cli-report-no-invoices"))
            return

        # Calculate totals
        totale_imponibile = sum(f.imponibile for f in fatture)
        totale_iva = sum(f.iva for f in fatture)
        totale_fatturato = sum(f.totale for f in fatture)

        # Summary table
        table = Table(title=_("cli-report-iva-summary-title"), show_lines=True)
        table.add_column(_("cli-report-iva-column-metric"), style="cyan", width=25)
        table.add_column(
            _("cli-report-iva-column-amount"), style="white", justify="right", width=15
        )

        table.add_row(_("cli-report-iva-label-num-invoices"), str(len(fatture)))
        table.add_row(_("cli-report-iva-label-imponibile"), f"€{totale_imponibile:,.2f}")
        table.add_row(_("cli-report-iva-label-total-vat"), f"€{totale_iva:,.2f}")
        table.add_row(
            _("cli-report-iva-label-total-revenue-bold"), f"[bold]€{totale_fatturato:,.2f}[/bold]"
        )

        console.print(table)

        # By VAT rate
        console.print(_("cli-report-iva-breakdown-title"))

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
        aliquote_table.add_column(_("cli-report-iva-column-vat-rate"), style="cyan", width=15)
        aliquote_table.add_column(_("cli-report-iva-column-imponibile"), justify="right", width=15)
        aliquote_table.add_column(_("cli-report-iva-column-vat"), justify="right", width=15)

        for aliquota in sorted(by_aliquota.keys()):
            data = by_aliquota[aliquota]
            aliquote_table.add_row(
                f"{aliquota}%",
                f"€{data['imponibile']:,.2f}",
                f"€{data['iva']:,.2f}",
            )

        console.print(aliquote_table)
        console.print()


@app.command("clienti")
def report_clienti(
    anno: int = typer.Option(date.today().year, "--anno", help=_("cli-report-clienti-help-anno")),
) -> None:
    """
    Generate client revenue report.

    Example:
        openfatture report clienti --anno 2025
    """
    ensure_db()

    console.print(_("cli-report-clienti-title", anno=anno))

    with db_session() as db:
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
            console.print(_("cli-report-no-invoices-year"))
            return

        table = Table(title=_("cli-report-clienti-table-title", anno=anno), show_lines=False)
        table.add_column(_("cli-report-clienti-column-rank"), style="dim", width=6, justify="right")
        table.add_column(_("cli-report-clienti-column-client"), style="cyan")
        table.add_column(_("cli-report-clienti-column-invoices"), justify="right", width=10)
        table.add_column(
            _("cli-report-clienti-column-revenue"), style="green", justify="right", width=15
        )

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
        console.print(_("cli-report-clienti-total-revenue", totale=f"€{totale_generale:,.2f}"))


@app.command("scadenze")
def report_scadenze(
    finestra: int = typer.Option(
        14,
        "--finestra",
        "-f",
        min=1,
        help=_("cli-report-scadenze-help-finestra"),
    ),
) -> None:
    """
    Show overdue and upcoming payment due dates leveraging the Pagamento ledger.

    Example:
        openfatture report scadenze --finestra 21
    """
    ensure_db()

    console.print(_("cli-report-scadenze-title"))

    with db_session() as db:
        summary = collect_payment_due_summary(db, window_days=finestra, max_upcoming=20)

        has_entries = any(summary.overdue or summary.due_soon or summary.upcoming)

        if not has_entries:
            console.print(_("cli-report-scadenze-no-outstanding"))
            return

        section_config = [
            ("overdue", _("cli-report-scadenze-section-overdue"), "red"),
            (
                "due_soon",
                _("cli-report-scadenze-section-due-soon", finestra=finestra),
                "yellow",
            ),
            ("upcoming", _("cli-report-scadenze-section-upcoming"), "cyan"),
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
                StatoPagamento.SCADUTO: _("cli-report-scadenze-status-overdue"),
                StatoPagamento.PAGATO_PARZIALE: _("cli-report-scadenze-status-partial"),
                StatoPagamento.DA_PAGARE: _("cli-report-scadenze-status-due"),
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
            table.add_column(
                _("cli-report-scadenze-column-invoice"), style="cyan", no_wrap=True, min_width=10
            )
            table.add_column(
                _("cli-report-scadenze-column-client"), style="white", no_wrap=True, min_width=18
            )
            table.add_column(_("cli-report-scadenze-column-due-date"), justify="center")
            table.add_column(_("cli-report-scadenze-column-days-delta"), justify="right")
            table.add_column(_("cli-report-scadenze-column-residual"), justify="right")
            table.add_column(_("cli-report-scadenze-column-paid"), justify="right")
            table.add_column(_("cli-report-scadenze-column-total"), justify="right")
            table.add_column(_("cli-report-scadenze-column-status"), justify="left")

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
                _(
                    "cli-report-scadenze-section-total",
                    color=color,
                    totale=_format_money(total_residual),
                    count=len(rows),
                ),
            )
            console.print()

        if summary.hidden_upcoming > 0:
            console.print(_("cli-report-scadenze-hidden-upcoming", count=summary.hidden_upcoming))

        console.print(
            _(
                "cli-report-scadenze-total-outstanding",
                totale=_format_money(summary.total_outstanding),
            )
        )
