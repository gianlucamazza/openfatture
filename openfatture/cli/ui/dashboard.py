"""Interactive dashboard with real-time statistics."""

from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from openfatture.payment.application.services.payment_overview import PaymentDueEntry
from openfatture.services.dashboard import DashboardService
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Fattura, StatoFattura

console = Console()


def create_overview_panel(service: DashboardService) -> Panel:
    """
    Create overview panel with key metrics.

    Args:
        service: DashboardService instance

    Returns:
        Rich Panel with overview
    """
    total_invoices = service.get_total_invoices()
    total_clients = service.get_total_clients()
    total_revenue = service.get_total_revenue()
    revenue_month = service.get_revenue_this_month()
    revenue_year = service.get_revenue_this_year()
    pending = service.get_pending_amount()
    sent_not_accepted = service.get_sent_not_accepted()

    # Create metrics text
    content = Text()
    content.append("📊 Totale Fatture: ", style="bold")
    content.append(f"{total_invoices}\n", style="cyan")

    content.append("👥 Totale Clienti: ", style="bold")
    content.append(f"{total_clients}\n\n", style="cyan")

    content.append("💰 Fatturato Totale: ", style="bold")
    content.append(f"€{total_revenue:,.2f}\n", style="green bold")

    content.append("📅 Fatturato Mese: ", style="bold")
    content.append(f"€{revenue_month:,.2f}\n", style="green")

    content.append("📈 Fatturato Anno: ", style="bold")
    content.append(f"€{revenue_year:,.2f}\n\n", style="green")

    content.append("⏳ In Sospeso: ", style="bold")
    content.append(f"€{pending:,.2f}\n", style="yellow")

    content.append("📤 Inviate (da accettare): ", style="bold")
    content.append(f"{sent_not_accepted}", style="yellow")

    return Panel(
        Align.center(content),
        title="[bold blue]📋 Panoramica[/bold blue]",
        border_style="blue",
    )


def create_status_table(service: DashboardService) -> Table:
    """
    Create table with invoice status distribution.

    Args:
        service: DashboardService instance

    Returns:
        Rich Table
    """
    table = Table(title="📊 Distribuzione per Stato", show_header=True, header_style="bold magenta")
    table.add_column("Stato", style="cyan", no_wrap=True)
    table.add_column("Numero", justify="right", style="green")

    status_data = service.get_invoices_by_status()
    status_emoji = {
        "bozza": "📝",
        "da_inviare": "📤",
        "inviata": "✉️",
        "accettata": "✅",
        "rifiutata": "❌",
    }

    for stato, count in status_data:
        emoji = status_emoji.get(stato, "📄")
        table.add_row(f"{emoji} {stato.replace('_', ' ').title()}", str(count))

    # Add total row
    total = sum(count for _, count in status_data)
    table.add_section()
    table.add_row("[bold]TOTALE[/bold]", f"[bold]{total}[/bold]")

    return table


def create_monthly_revenue_table(service: DashboardService, months: int = 6) -> Table:
    """
    Create table with monthly revenue.

    Args:
        service: DashboardService instance
        months: Number of months to display

    Returns:
        Rich Table
    """
    table = Table(
        title=f"📈 Fatturato Ultimi {months} Mesi", show_header=True, header_style="bold magenta"
    )
    table.add_column("Mese", style="cyan", no_wrap=True)
    table.add_column("Fatturato", justify="right", style="green")

    monthly_data = service.get_monthly_revenue(months)

    for month_name, revenue in monthly_data:
        table.add_row(month_name, f"€{revenue:,.2f}")

    # Add total row
    total = sum(revenue for _, revenue in monthly_data)
    table.add_section()
    table.add_row("[bold]TOTALE[/bold]", f"[bold]€{total:,.2f}[/bold]")

    return table


def create_top_clients_table(service: DashboardService, limit: int = 5) -> Table:
    """
    Create table with top clients.

    Args:
        service: DashboardService instance
        limit: Number of clients to display

    Returns:
        Rich Table
    """
    table = Table(title=f"👑 Top {limit} Clienti", show_header=True, header_style="bold magenta")
    table.add_column("Cliente", style="cyan")
    table.add_column("Fatture", justify="right", style="yellow")
    table.add_column("Fatturato", justify="right", style="green")

    top_clients = service.get_top_clients(limit)

    for name, count, revenue in top_clients:
        # Truncate long names
        display_name = name[:40] + "..." if len(name) > 40 else name
        table.add_row(display_name, str(count), f"€{revenue:,.2f}")

    return table


def create_recent_invoices_table(service: DashboardService, limit: int = 5) -> Table:
    """
    Create table with recent invoices.

    Args:
        service: DashboardService instance
        limit: Number of invoices to display

    Returns:
        Rich Table
    """
    table = Table(title=f"🕐 Ultime {limit} Fatture", show_header=True, header_style="bold magenta")
    table.add_column("Numero", style="cyan", no_wrap=True)
    table.add_column("Data", style="yellow", no_wrap=True)
    table.add_column("Cliente", style="white")
    table.add_column("Importo", justify="right", style="green")
    table.add_column("Stato", style="magenta")

    recent = service.get_recent_invoices(limit)

    status_emoji = {
        StatoFattura.BOZZA: "📝",
        StatoFattura.DA_INVIARE: "📤",
        StatoFattura.INVIATA: "✉️",
        StatoFattura.ACCETTATA: "✅",
        StatoFattura.RIFIUTATA: "❌",
    }

    for fattura in recent:
        # Skip if cliente is None
        if fattura.cliente is None:
            continue

        emoji = status_emoji.get(fattura.stato, "📄")
        client_name = (
            fattura.cliente.denominazione[:30] + "..."
            if len(fattura.cliente.denominazione) > 30
            else fattura.cliente.denominazione
        )

        table.add_row(
            f"{fattura.numero}/{fattura.anno}",
            fattura.data_emissione.strftime("%d/%m/%Y"),
            client_name,
            f"€{fattura.totale:,.2f}",
            f"{emoji} {fattura.stato.value}",
        )

    return table


def create_payment_stats_panel(service: DashboardService) -> Panel:
    """Create panel with payment tracking statistics."""
    stats = service.get_payment_stats()

    total = stats["unmatched"] + stats["matched"] + stats["ignored"]

    content = Text()
    content.append("🔍 Non Abbinati: ", style="bold")
    content.append(f"{stats['unmatched']}\n", style="yellow")

    content.append("✅ Abbinati: ", style="bold")
    content.append(f"{stats['matched']}\n", style="green")

    content.append("⏭️  Ignorati: ", style="bold")
    content.append(f"{stats['ignored']}\n\n", style="dim")

    content.append("📊 Totale Transazioni: ", style="bold")
    content.append(f"{total}", style="cyan")

    return Panel(
        Align.center(content),
        title="[bold magenta]💰 Tracking Pagamenti[/bold magenta]",
        border_style="magenta",
    )


def create_payment_due_panel(
    service: DashboardService, window_days: int = 30, max_upcoming: int = 10
) -> Panel:
    """Create panel summarizing outstanding payments."""

    summary = service.get_payment_due_summary(window_days, max_upcoming)

    if not (summary.overdue or summary.due_soon or summary.upcoming):
        message = Align.center(Text("✅ Nessun pagamento pendente", style="green bold"))
        return Panel(
            message,
            title=f"[bold blue]💳 Scadenze Pagamenti (<= {window_days} gg)[/bold blue]",
            border_style="green",
        )

    table = Table(
        title=None,
        show_header=True,
        header_style="bold magenta",
        expand=True,
    )
    table.add_column("Categoria", style="cyan")
    table.add_column("Fattura", style="white")
    table.add_column("Cliente", style="white")
    table.add_column("Scadenza", style="yellow", justify="center")
    table.add_column("Δ", justify="right")
    table.add_column("Residuo", justify="right", style="red")
    table.add_column("Pagato", justify="right")
    table.add_column("Totale", justify="right")
    table.add_column("Stato", style="magenta")

    def _fmt_money(value) -> str:
        return f"€{value:,.2f}"

    def _fmt_days(delta: int) -> str:
        if delta < 0:
            return f"[red]{delta}[/red]"
        if delta == 0:
            return "[yellow]0[/yellow]"
        return f"[green]+{delta}[/green]"

    def _status(entry: PaymentDueEntry) -> str:
        mapping = {
            "scaduto": "[red]Scaduto[/red]",
            "pagato_parziale": "[yellow]Parziale[/yellow]",
            "da_pagare": "Da pagare",
        }
        return mapping.get(entry.status.value, entry.status.value.replace("_", " ").title())

    def _add_rows(category: str, entries: list[PaymentDueEntry]) -> None:
        color = {
            "Scaduto": "red",
            "In scadenza": "yellow",
            "Prossimo": "cyan",
        }[category]

        for entry in entries:
            table.add_row(
                category,
                entry.invoice_ref,
                entry.client_name,
                entry.due_date.strftime("%d/%m/%Y"),
                _fmt_days(entry.days_delta),
                f"[bold {color}]{_fmt_money(entry.residual)}[/bold {color}]",
                _fmt_money(entry.paid),
                _fmt_money(entry.total),
                _status(entry),
            )

    if summary.overdue:
        _add_rows("Scaduto", summary.overdue)
    if summary.due_soon:
        _add_rows("In scadenza", summary.due_soon)
    if summary.upcoming:
        _add_rows("Prossimo", summary.upcoming)

    footer = Text.assemble(
        ("Totale residuo: ", "bold"),
        (f"{_fmt_money(summary.total_outstanding)}", "bold red"),
    )
    if summary.hidden_upcoming:
        footer.append(
            f"  (+{summary.hidden_upcoming} ulteriori pagamenti futuri)",
            style="dim",
        )

    return Panel(
        table,
        title=f"[bold blue]💳 Scadenze Pagamenti (<= {window_days} gg)[/bold blue]",
        subtitle=footer,
        border_style="blue",
    )


def show_dashboard(refresh: bool = False) -> None:
    """
    Display interactive dashboard.

    Args:
        refresh: If True, will refresh continuously
    """
    db = get_session()
    service = DashboardService(db)

    try:
        # Clear console
        console.clear()

        # Create layout
        layout = Layout()

        # Split into header and body
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
        )

        # Header
        header_text = Text("OpenFatture Dashboard", style="bold white on blue", justify="center")
        layout["header"].update(Panel(header_text, style="blue"))

        # Split body into left and right
        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=2),
        )

        # Left side: Overview panel
        layout["left"].update(create_overview_panel(service))

        # Right side: Split into top, mid, and bottom
        layout["right"].split_column(
            Layout(name="top"),
            Layout(name="mid"),
            Layout(name="payment_stats"),
            Layout(name="bottom"),
        )

        # Top right: Status and Monthly Revenue
        layout["top"].split_row(
            Layout(create_status_table(service)),
            Layout(create_monthly_revenue_table(service)),
        )

        layout["mid"].update(create_payment_due_panel(service))

        # Payment stats
        layout["payment_stats"].update(create_payment_stats_panel(service))

        # Bottom right: Top Clients and Recent Invoices
        layout["bottom"].split_row(
            Layout(create_top_clients_table(service)),
            Layout(create_recent_invoices_table(service)),
        )

        # Print the layout
        console.print(layout)

        # Footer instructions
        console.print("\n[dim]Premi INVIO per tornare al menu...[/dim]", justify="center")
        input()

    finally:
        db.close()
