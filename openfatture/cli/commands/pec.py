"""PEC testing and configuration commands."""

import typer
from rich.console import Console

from openfatture.utils.config import get_settings
from openfatture.utils.email.sender import TemplatePECSender

PECSender = TemplatePECSender

app = typer.Typer()
console = Console()


@app.command("test")
def test_pec() -> None:
    """
    Test PEC configuration with professional email template.

    This verifies that:
    - PEC credentials are correct
    - SMTP server is reachable
    - Email templates render correctly
    - You can send emails via PEC

    Note: This uses the new TemplatePECSender with HTML + text templates.
    """
    console.print("\n[bold blue]🧪 Testing PEC Configuration[/bold blue]\n")

    settings = get_settings()

    # Check configuration
    if not settings.pec_address:
        console.print("[red]❌ PEC address not configured[/red]")
        console.print("Run: [cyan]openfatture init[/cyan] to configure")
        raise typer.Exit(1)

    if not settings.pec_password:
        console.print("[red]❌ PEC password not configured[/red]")
        console.print("Set it in your .env file: PEC_PASSWORD=your_password")
        raise typer.Exit(1)

    console.print(f"[cyan]PEC Address:[/cyan] {settings.pec_address}")
    console.print(f"[cyan]SMTP Server:[/cyan] {settings.pec_smtp_server}:{settings.pec_smtp_port}")
    console.print("[cyan]Template:[/cyan] test/test_email.html + .txt")
    console.print(f"[cyan]Locale:[/cyan] {settings.locale}\n")

    console.print("Sending test email with professional template...")

    sender = PECSender(settings=settings, locale=settings.locale)
    success, error = sender.send_test_email()

    if success:
        console.print("\n[bold green]✓ Test email sent successfully![/bold green]")
        console.print(f"Check your PEC inbox: {settings.pec_address}")
        console.print("\n[dim]The email includes:[/dim]")
        console.print("  • Professional HTML + plain text")
        console.print("  • Your company branding")
        console.print(f"  • Language: {settings.locale.upper()}")
        console.print("\n[dim]For more email testing:[/dim]")
        console.print("  [cyan]openfatture email test[/cyan]  - Full email test")
        console.print("  [cyan]openfatture email preview[/cyan] - Preview templates")
    else:
        console.print(f"\n[red]❌ Test failed: {error}[/red]")
        console.print("\n[yellow]Common issues:[/yellow]")
        console.print("  • Wrong PEC credentials")
        console.print("  • Incorrect SMTP server")
        console.print("  • Firewall blocking port 465")
        console.print("  • PEC mailbox full")
        raise typer.Exit(1)


@app.command("info")
def pec_info() -> None:
    """Show PEC configuration."""
    console.print("\n[bold blue]📧 PEC Configuration[/bold blue]\n")

    settings = get_settings()

    from rich.table import Table

    table = Table(show_header=False)
    table.add_column("Setting", style="cyan", width=20)
    table.add_column("Value", style="white")

    table.add_row("PEC Address", settings.pec_address or "[red]Not set[/red]")
    table.add_row(
        "Password",
        "[green]Set[/green]" if settings.pec_password else "[red]Not set[/red]",
    )
    table.add_row("SMTP Server", settings.pec_smtp_server)
    table.add_row("SMTP Port", str(settings.pec_smtp_port))
    table.add_row("SDI PEC", settings.sdi_pec_address)

    console.print(table)
    console.print()
