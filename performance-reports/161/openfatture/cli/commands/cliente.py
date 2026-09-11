"""Cliente (client) management CLI commands."""

import typer
from rich.console import Console
from rich.table import Table

from openfatture.billing.application.client_commands import (
    create_client,
)
from openfatture.billing.application.client_queries import (
    get_client_details,
    search_clients,
)

app = typer.Typer(name="cliente", help="Manage clients (customers)")
console = Console()


@app.command("list")
def list_clients(
    query: str = typer.Option(None, "--query", "-q", help="Search by name, VAT, or tax code"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of results"),
) -> None:
    """List and search clients."""
    result = search_clients(query=query, limit=limit)

    if "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        raise typer.Exit(code=1)

    if result["count"] == 0:
        console.print("[yellow]No clients found.[/yellow]")
        return

    # Display as table
    table = Table(title=f"Clients ({result['count']})")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("P.IVA")
    table.add_column("CF")
    table.add_column("Email")
    table.add_column("Invoices", justify="right")

    for cliente in result["clienti"]:
        table.add_row(
            str(cliente["id"]),
            cliente["denominazione"],
            cliente["partita_iva"] or "-",
            cliente["codice_fiscale"] or "-",
            cliente["email"] or "-",
            str(cliente["fatture_count"]),
        )

    console.print(table)

    if result.get("has_more"):
        console.print("[dim]... and more. Use --limit to see more results.[/dim]")


@app.command("show")
def show_client(
    cliente_id: int = typer.Argument(..., help="Client ID"),
) -> None:
    """Show detailed client information."""
    result = get_client_details(cliente_id=cliente_id)

    if "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        raise typer.Exit(code=1)

    # Display client details
    console.print(f"\n[bold cyan]Client #{result['id']}[/bold cyan]")
    console.print(f"[bold]Name:[/bold] {result['denominazione']}")

    if result.get("partita_iva"):
        console.print(f"[bold]P.IVA:[/bold] {result['partita_iva']}")
    if result.get("codice_fiscale"):
        console.print(f"[bold]Codice Fiscale:[/bold] {result['codice_fiscale']}")

    # Address
    indirizzo = result.get("indirizzo", {})
    if any(indirizzo.values()):
        console.print("\n[bold]Address:[/bold]")
        if indirizzo.get("via"):
            console.print(f"  {indirizzo['via']}")
        if indirizzo.get("cap") or indirizzo.get("comune"):
            console.print(f"  {indirizzo.get('cap', '')} {indirizzo.get('comune', '')}")

    # Contacts
    contatti = result.get("contatti", {})
    if any(contatti.values()):
        console.print("\n[bold]Contacts:[/bold]")
        if contatti.get("email"):
            console.print(f"  Email: {contatti['email']}")
        if contatti.get("pec"):
            console.print(f"  PEC: {contatti['pec']}")
        if contatti.get("telefono"):
            console.print(f"  Tel: {contatti['telefono']}")

    # Recent invoices
    console.print(f"\n[bold]Invoices:[/bold] {result['fatture_count']} total")
    if result.get("fatture_recenti"):
        table = Table(title="Recent Invoices")
        table.add_column("ID", style="cyan")
        table.add_column("Number")
        table.add_column("Date")
        table.add_column("Amount", justify="right")
        table.add_column("Status")

        for fattura in result["fatture_recenti"]:
            table.add_row(
                str(fattura["id"]),
                f"{fattura['numero']}/{fattura['anno']}",
                fattura["data"],
                f"€ {fattura['importo']:.2f}",
                fattura["stato"],
            )

        console.print(table)


@app.command("create")
def create_new_client(
    denominazione: str = typer.Option(..., "--name", "-n", help="Client name (company or person)"),
    partita_iva: str = typer.Option(None, "--piva", help="Partita IVA (VAT number)"),
    codice_fiscale: str = typer.Option(None, "--cf", help="Codice Fiscale (tax code)"),
    email: str = typer.Option(None, "--email", "-e", help="Email address"),
    pec: str = typer.Option(None, "--pec", help="PEC email address"),
    indirizzo: str = typer.Option(None, "--address", help="Street address"),
    cap: str = typer.Option(None, "--cap", help="Postal code"),
    comune: str = typer.Option(None, "--city", help="City/Municipality"),
    provincia: str = typer.Option(None, "--province", help="Province (2 letters)"),
    telefono: str = typer.Option(None, "--phone", help="Phone number"),
    note: str = typer.Option(None, "--note", help="Notes"),
) -> None:
    """Create a new client."""
    result = create_client(
        denominazione=denominazione,
        partita_iva=partita_iva,
        codice_fiscale=codice_fiscale,
        email=email,
        pec=pec,
        indirizzo=indirizzo,
        cap=cap,
        comune=comune,
        provincia=provincia,
        telefono=telefono,
        note=note,
    )

    if "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        raise typer.Exit(code=1)

    console.print(f"[green]✓[/green] {result['message']}")
    console.print(f"Client ID: [cyan]{result['client_id']}[/cyan]")
