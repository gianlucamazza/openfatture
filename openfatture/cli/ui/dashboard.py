"""Interactive dashboard with real-time statistics."""

from datetime import datetime, timedelta
from decimal import Decimal

from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from sqlalchemy import extract, func

from openfatture.storage.database.base import SessionLocal
from openfatture.storage.database.models import Cliente, Fattura, StatoFattura

console = Console()


class DashboardData:
    """Fetch and process dashboard statistics."""

    def __init__(self):
        """Initialize with database session."""
        self.db = SessionLocal()

    def close(self):
        """Close database session."""
        self.db.close()

    def get_total_invoices(self) -> int:
        """Get total number of invoices."""
        return self.db.query(Fattura).count()

    def get_total_clients(self) -> int:
        """Get total number of clients."""
        return self.db.query(Cliente).count()

    def get_total_revenue(self) -> Decimal:
        """Get total revenue from all invoices."""
        total = self.db.query(func.sum(Fattura.totale)).scalar()
        return total or Decimal("0")

    def get_revenue_this_month(self) -> Decimal:
        """Get revenue for current month."""
        now = datetime.now()
        total = (
            self.db.query(func.sum(Fattura.totale))
            .filter(
                extract("year", Fattura.data_emissione) == now.year,
                extract("month", Fattura.data_emissione) == now.month,
            )
            .scalar()
        )
        return total or Decimal("0")

    def get_revenue_this_year(self) -> Decimal:
        """Get revenue for current year."""
        now = datetime.now()
        total = (
            self.db.query(func.sum(Fattura.totale))
            .filter(extract("year", Fattura.data) == now.year)
            .scalar()
        )
        return total or Decimal("0")

    def get_invoices_by_status(self) -> list[tuple[str, int]]:
        """Get invoice count grouped by status."""
        results = self.db.query(Fattura.stato, func.count(Fattura.id)).group_by(Fattura.stato).all()
        return [(stato.value, count) for stato, count in results]

    def get_pending_amount(self) -> Decimal:
        """Get total amount from pending invoices."""
        total = (
            self.db.query(func.sum(Fattura.totale))
            .filter(Fattura.stato.in_([StatoFattura.BOZZA, StatoFattura.DA_INVIARE]))
            .scalar()
        )
        return total or Decimal("0")

    def get_sent_not_accepted(self) -> int:
        """Get count of invoices sent but not yet accepted."""
        return self.db.query(Fattura).filter(Fattura.stato == StatoFattura.INVIATA).count()

    def get_monthly_revenue(self, months: int = 6) -> list[tuple[str, Decimal]]:
        """
        Get revenue for last N months.

        Args:
            months: Number of months to retrieve

        Returns:
            List of (month_name, revenue) tuples
        """
        now = datetime.now()
        results = []

        for i in range(months - 1, -1, -1):
            # Calculate month/year
            target_date = now - timedelta(days=30 * i)
            month = target_date.month
            year = target_date.year

            # Query revenue for that month
            revenue = (
                self.db.query(func.sum(Fattura.totale))
                .filter(
                    extract("year", Fattura.data_emissione) == year,
                    extract("month", Fattura.data_emissione) == month,
                )
                .scalar()
            ) or Decimal("0")

            month_name = target_date.strftime("%b %Y")
            results.append((month_name, revenue))

        return results

    def get_top_clients(self, limit: int = 5) -> list[tuple[str, int, Decimal]]:
        """
        Get top clients by revenue.

        Args:
            limit: Number of clients to return

        Returns:
            List of (client_name, invoice_count, total_revenue) tuples
        """
        results = (
            self.db.query(
                Cliente.denominazione,
                func.count(Fattura.id),
                func.sum(Fattura.totale),
            )
            .join(Fattura)
            .group_by(Cliente.id, Cliente.denominazione)
            .order_by(func.sum(Fattura.totale).desc())
            .limit(limit)
            .all()
        )

        return [(name, count, total or Decimal("0")) for name, count, total in results]

    def get_recent_invoices(self, limit: int = 5) -> list[Fattura]:
        """
        Get most recent invoices.

        Args:
            limit: Number of invoices to return

        Returns:
            List of Invoice objects
        """
        return self.db.query(Fattura).order_by(Fattura.data_emissione.desc()).limit(limit).all()


def create_overview_panel(data: DashboardData) -> Panel:
    """
    Create overview panel with key metrics.

    Args:
        data: DashboardData instance

    Returns:
        Rich Panel with overview
    """
    total_invoices = data.get_total_invoices()
    total_clients = data.get_total_clients()
    total_revenue = data.get_total_revenue()
    revenue_month = data.get_revenue_this_month()
    revenue_year = data.get_revenue_this_year()
    pending = data.get_pending_amount()
    sent_not_accepted = data.get_sent_not_accepted()

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


def create_status_table(data: DashboardData) -> Table:
    """
    Create table with invoice status distribution.

    Args:
        data: DashboardData instance

    Returns:
        Rich Table
    """
    table = Table(title="📊 Distribuzione per Stato", show_header=True, header_style="bold magenta")
    table.add_column("Stato", style="cyan", no_wrap=True)
    table.add_column("Numero", justify="right", style="green")

    status_data = data.get_invoices_by_status()
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


def create_monthly_revenue_table(data: DashboardData, months: int = 6) -> Table:
    """
    Create table with monthly revenue.

    Args:
        data: DashboardData instance
        months: Number of months to display

    Returns:
        Rich Table
    """
    table = Table(
        title=f"📈 Fatturato Ultimi {months} Mesi", show_header=True, header_style="bold magenta"
    )
    table.add_column("Mese", style="cyan", no_wrap=True)
    table.add_column("Fatturato", justify="right", style="green")

    monthly_data = data.get_monthly_revenue(months)

    for month_name, revenue in monthly_data:
        table.add_row(month_name, f"€{revenue:,.2f}")

    # Add total row
    total = sum(revenue for _, revenue in monthly_data)
    table.add_section()
    table.add_row("[bold]TOTALE[/bold]", f"[bold]€{total:,.2f}[/bold]")

    return table


def create_top_clients_table(data: DashboardData, limit: int = 5) -> Table:
    """
    Create table with top clients.

    Args:
        data: DashboardData instance
        limit: Number of clients to display

    Returns:
        Rich Table
    """
    table = Table(title=f"👑 Top {limit} Clienti", show_header=True, header_style="bold magenta")
    table.add_column("Cliente", style="cyan")
    table.add_column("Fatture", justify="right", style="yellow")
    table.add_column("Fatturato", justify="right", style="green")

    top_clients = data.get_top_clients(limit)

    for name, count, revenue in top_clients:
        # Truncate long names
        display_name = name[:40] + "..." if len(name) > 40 else name
        table.add_row(display_name, str(count), f"€{revenue:,.2f}")

    return table


def create_recent_invoices_table(data: DashboardData, limit: int = 5) -> Table:
    """
    Create table with recent invoices.

    Args:
        data: DashboardData instance
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

    recent = data.get_recent_invoices(limit)

    status_emoji = {
        StatoFattura.BOZZA: "📝",
        StatoFattura.DA_INVIARE: "📤",
        StatoFattura.INVIATA: "✉️",
        StatoFattura.ACCETTATA: "✅",
        StatoFattura.RIFIUTATA: "❌",
    }

    for fattura in recent:
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


def show_dashboard(refresh: bool = False) -> None:
    """
    Display interactive dashboard.

    Args:
        refresh: If True, will refresh continuously
    """
    data = DashboardData()

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
        layout["left"].update(create_overview_panel(data))

        # Right side: Split into top and bottom
        layout["right"].split_column(
            Layout(name="top"),
            Layout(name="bottom"),
        )

        # Top right: Status and Monthly Revenue
        layout["top"].split_row(
            Layout(create_status_table(data)),
            Layout(create_monthly_revenue_table(data)),
        )

        # Bottom right: Top Clients and Recent Invoices
        layout["bottom"].split_row(
            Layout(create_top_clients_table(data)),
            Layout(create_recent_invoices_table(data)),
        )

        # Print the layout
        console.print(layout)

        # Footer instructions
        console.print("\n[dim]Premi INVIO per tornare al menu...[/dim]", justify="center")
        input()

    finally:
        data.close()
