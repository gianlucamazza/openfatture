"""Email templates and testing commands."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from openfatture.storage.database.models import Cliente, Fattura
from openfatture.utils.config import get_settings
from openfatture.utils.email.models import FatturaInvioContext
from openfatture.utils.email.renderer import TemplateRenderer
from openfatture.utils.email.sender import TemplatePECSender

app = typer.Typer()
console = Console()


@app.command("test")
def test_email() -> None:
    """
    Send test email with professional template.

    This verifies:
    - PEC credentials work
    - Email templates render correctly
    - Notification email receives messages
    """
    console.print("\n[bold blue]📧 Testing Email Configuration[/bold blue]\n")

    settings = get_settings()

    # Check configuration
    if not settings.pec_address:
        console.print("[red]❌ PEC address not configured[/red]")
        console.print("Run: [cyan]openfatture init[/cyan] to configure")
        raise typer.Exit(1)

    if not settings.notification_email:
        console.print("[red]❌ Notification email not configured[/red]")
        console.print("Add NOTIFICATION_EMAIL to your .env file")
        raise typer.Exit(1)

    console.print(f"[cyan]PEC From:[/cyan] {settings.pec_address}")
    console.print(f"[cyan]Sending To:[/cyan] {settings.notification_email}")
    console.print("[cyan]Template:[/cyan] test/test_email.html + .txt")
    console.print(f"[cyan]Locale:[/cyan] {settings.locale}\n")

    console.print("Sending test email with professional template...")

    sender = TemplatePECSender(settings=settings, locale=settings.locale)
    success, error = sender.send_test_email()

    if success:
        console.print("\n[bold green]✓ Test email sent successfully![/bold green]")
        console.print(f"Check inbox: {settings.notification_email}")
        console.print("\n[dim]The email includes:[/dim]")
        console.print("  • Professional HTML + plain text")
        console.print("  • Your company branding")
        console.print(f"  • Language: {settings.locale.upper()}")
        console.print(f"  • Primary color: {settings.email_primary_color}")
    else:
        console.print(f"\n[red]❌ Test failed: {error}[/red]")
        console.print("\n[yellow]Troubleshooting:[/yellow]")
        console.print("  1. Check PEC credentials in .env")
        console.print("  2. Verify SMTP server and port")
        console.print("  3. Ensure NOTIFICATION_EMAIL is valid")
        console.print("  4. Check firewall allows port 465")
        raise typer.Exit(1)


@app.command("preview")
def preview_template(
    template: str = typer.Option(
        "sdi/invio_fattura",
        "--template",
        "-t",
        help="Template name (e.g., sdi/invio_fattura)",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path (default: /tmp/email_preview.html)",
    ),
) -> None:
    """
    Generate HTML preview of email template.

    Example:
        openfatture email preview --template sdi/invio_fattura
        openfatture email preview --template batch/riepilogo_batch -o /tmp/preview.html
    """
    console.print("\n[bold blue]🎨 Email Template Preview[/bold blue]\n")

    settings = get_settings()
    renderer = TemplateRenderer(settings=settings, locale=settings.locale)

    # Create mock context based on template type
    console.print(f"[cyan]Template:[/cyan] {template}.html")
    console.print(f"[cyan]Locale:[/cyan] {settings.locale}\n")

    console.print("Generating preview with mock data...")

    try:
        # Mock invoice for preview
        if "invio_fattura" in template or "notifica" in template:
            mock_cliente = Cliente(
                denominazione="Cliente Demo SRL",
                partita_iva="12345678901",
            )
            mock_fattura = Fattura(
                numero="001",
                anno=2025,
                data_emissione=date.today(),
                cliente=mock_cliente,
                totale=Decimal("1220.00"),
            )

            context = FatturaInvioContext(
                fattura=mock_fattura,
                cedente={
                    "denominazione": settings.cedente_denominazione or "Your Company",
                    "partita_iva": settings.cedente_partita_iva or "00000000000",
                    "indirizzo": settings.cedente_indirizzo or "Via Example 1",
                    "cap": settings.cedente_cap or "00100",
                    "comune": settings.cedente_comune or "Roma",
                },
                destinatario="sdi01@pec.fatturapa.it",
                is_signed=False,
                xml_filename="IT12345678901_00001.xml",
            )
        else:
            console.print("[yellow]⚠ Preview for this template type not yet supported[/yellow]")
            console.print("[dim]Supported: sdi/* templates[/dim]")
            return

        # Generate preview
        output_path = Path(output) if output else Path("/tmp/email_preview.html")
        preview_path = renderer.preview(
            template_name=f"{template}.html",
            context=context,
            output_path=output_path,
        )

        console.print("\n[bold green]✓ Preview generated![/bold green]")
        console.print(f"[cyan]File:[/cyan] file://{preview_path}")
        console.print(f"[cyan]Size:[/cyan] {preview_path.stat().st_size} bytes")
        console.print("\n[dim]Open in browser to view the rendered template[/dim]")

    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("info")
def email_info() -> None:
    """Show email templates configuration and available templates."""
    console.print("\n[bold blue]📧 Email Templates Configuration[/bold blue]\n")

    settings = get_settings()

    # Configuration table
    table = Table(title="Configuration", show_header=False)
    table.add_column("Setting", style="cyan", width=25)
    table.add_column("Value", style="white")

    table.add_row("Notification Email", settings.notification_email or "[red]Not set[/red]")
    table.add_row(
        "Notifications Enabled",
        "[green]Yes[/green]" if settings.notification_enabled else "[red]No[/red]",
    )
    table.add_row("Locale", settings.locale)
    table.add_row("Logo URL", settings.email_logo_url or "[dim]None[/dim]")
    table.add_row(
        "Primary Color",
        f"[{settings.email_primary_color}]●[/{settings.email_primary_color}] {settings.email_primary_color}",
    )
    table.add_row(
        "Secondary Color",
        f"[{settings.email_secondary_color}]●[/{settings.email_secondary_color}] {settings.email_secondary_color}",
    )
    table.add_row("Footer Text", settings.email_footer_text or "[dim]Auto-generated[/dim]")

    console.print(table)

    # Available templates
    console.print("\n[bold]Available Templates:[/bold]\n")

    templates_info = [
        ("📤 sdi/invio_fattura", "Invoice submission to SDI"),
        ("✅ sdi/notifica_consegna", "Delivery confirmation (RC)"),
        ("❌ sdi/notifica_scarto", "Rejection notification (NS)"),
        ("📨 sdi/notifica_attestazione", "Transmission attestation (AT)"),
        ("⚠️  sdi/notifica_mancata_consegna", "Failed delivery (MC)"),
        ("✅ sdi/notifica_esito_accettata", "Customer acceptance (NE-EC01)"),
        ("❌ sdi/notifica_esito_rifiutata", "Customer rejection (NE-EC02)"),
        ("📊 batch/riepilogo_batch", "Batch operation summary"),
        ("🧪 test/test_email", "Test email template"),
    ]

    for name, desc in templates_info:
        console.print(f"  {name:<35} [dim]{desc}[/dim]")

    console.print("\n[dim]Each template has HTML + plain text versions[/dim]")

    # Quick actions
    console.print("\n[bold]Quick Actions:[/bold]")
    console.print("  • Test email:  [cyan]openfatture email test[/cyan]")
    console.print(
        "  • Preview:     [cyan]openfatture email preview --template sdi/invio_fattura[/cyan]"
    )
    console.print("  • Customize:   Edit templates in [cyan]~/.openfatture/templates/[/cyan]")
    console.print()
