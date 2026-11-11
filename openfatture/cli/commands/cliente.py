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
from openfatture.cli.output import format_eur, remember_result
from openfatture.i18n import _

app = typer.Typer(name="cliente", help="Manage clients (customers)")
console = Console()


@app.callback()
def prepare_database() -> None:
    from openfatture.cli.database import ensure_database

    ensure_database()


@app.command("list")
def list_clients(
    query: str = typer.Option(None, "--query", "-q", help="Search by name, VAT, or tax code"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of results"),
) -> None:
    """List and search clients."""
    result = search_clients(query=query, limit=limit)
    remember_result(result)

    if "error" in result:
        console.print(_("cli-common-error", error=result["error"]))
        raise typer.Exit(code=1)

    if result["count"] == 0:
        console.print(_("cli-cliente-none-found"))
        return

    # Display as table
    table = Table(title=_("cli-cliente-list-title", count=result["count"]))
    table.add_column("ID", style="cyan")
    table.add_column(_("cli-common-name"), style="green")
    table.add_column(_("cli-common-vat-number"))
    table.add_column(_("cli-common-tax-code"))
    table.add_column("Email")
    table.add_column(_("cli-cliente-column-invoices"), justify="right")

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
        console.print(_("cli-common-more-results"))


@app.command("show")
def show_client(
    cliente_id: int = typer.Argument(..., help="Client ID"),
) -> None:
    """Show detailed client information."""
    result = get_client_details(cliente_id=cliente_id)
    remember_result(result)

    if "error" in result:
        console.print(_("cli-common-error", error=result["error"]))
        raise typer.Exit(code=1)

    # Display client details
    console.print("\n" + _("cli-cliente-show-title", id=str(result["id"])))
    console.print(f"[bold]{_('cli-common-name')}:[/bold] {result['denominazione']}")

    if result.get("partita_iva"):
        console.print(f"[bold]{_('cli-common-vat-number')}:[/bold] {result['partita_iva']}")
    if result.get("codice_fiscale"):
        console.print(f"[bold]{_('cli-common-tax-code')}:[/bold] {result['codice_fiscale']}")

    # Address
    indirizzo = result.get("indirizzo", {})
    if any(indirizzo.values()):
        console.print(f"\n[bold]{_('cli-cliente-address')}:[/bold]")
        if indirizzo.get("via"):
            console.print(f"  {indirizzo['via']}")
        if indirizzo.get("cap") or indirizzo.get("comune"):
            console.print(f"  {indirizzo.get('cap', '')} {indirizzo.get('comune', '')}")

    # Contacts
    contatti = result.get("contatti", {})
    if any(contatti.values()):
        console.print(f"\n[bold]{_('cli-cliente-contacts')}:[/bold]")
        if contatti.get("email"):
            console.print(f"  Email: {contatti['email']}")
        if contatti.get("pec"):
            console.print(f"  PEC: {contatti['pec']}")
        if contatti.get("telefono"):
            console.print(f"  {_('cli-cliente-phone')}: {contatti['telefono']}")

    # Recent invoices
    console.print("\n" + _("cli-cliente-invoices-total", count=result["fatture_count"]))
    if result.get("fatture_recenti"):
        table = Table(title=_("cli-cliente-recent-invoices"))
        table.add_column("ID", style="cyan")
        table.add_column(_("cli-common-number"))
        table.add_column(_("cli-common-date"))
        table.add_column(_("cli-common-amount"), justify="right")
        table.add_column(_("cli-common-status"))

        for fattura in result["fatture_recenti"]:
            table.add_row(
                str(fattura["id"]),
                f"{fattura['numero']}/{fattura['anno']}",
                fattura["data"],
                format_eur(fattura["importo"]),
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
    remember_result(result)

    if "error" in result:
        console.print(_("cli-common-error", error=result["error"]))
        raise typer.Exit(code=1)

    console.print(f"[green]✓[/green] {result['message']}")
    console.print(_("cli-cliente-created-id", id=str(result["client_id"])))
