"""Configuration management commands."""

import typer
from rich.console import Console
from rich.table import Table

from openfatture.utils.config import get_settings, reload_settings

app = typer.Typer()
console = Console()


@app.command("show")
def show_config() -> None:
    """Show current configuration."""
    settings = get_settings()

    table = Table(title="OpenFatture Configuration", show_header=True)
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    # Application
    table.add_section()
    table.add_row("App Version", settings.app_version)
    table.add_row("Debug Mode", str(settings.debug))

    # Database
    table.add_section()
    table.add_row("Database URL", settings.database_url)

    # Paths
    table.add_section()
    table.add_row("Data Directory", str(settings.data_dir))
    table.add_row("Archive Directory", str(settings.archivio_dir))
    table.add_row("Certificates Directory", str(settings.certificates_dir))

    # Company Data
    table.add_section()
    table.add_row("Company Name", settings.cedente_denominazione or "[red]Not set[/red]")
    table.add_row("Partita IVA", settings.cedente_partita_iva or "[red]Not set[/red]")
    table.add_row("Codice Fiscale", settings.cedente_codice_fiscale or "[red]Not set[/red]")
    table.add_row("Tax Regime", settings.cedente_regime_fiscale)

    # PEC
    table.add_section()
    table.add_row("PEC Address", settings.pec_address or "[red]Not set[/red]")
    table.add_row("PEC SMTP Server", settings.pec_smtp_server)
    table.add_row("SDI PEC Address", settings.sdi_pec_address)

    # Email Templates & Notifications
    table.add_section()
    table.add_row(
        "Notification Email",
        settings.notification_email or "[yellow]Not set[/yellow]",
    )
    table.add_row(
        "Notifications Enabled",
        "[green]Yes[/green]" if settings.notification_enabled else "[red]No[/red]",
    )
    table.add_row("Locale", settings.locale)
    table.add_row(
        "Email Logo URL",
        settings.email_logo_url or "[dim]Not set[/dim]",
    )
    table.add_row("Primary Color", settings.email_primary_color)
    table.add_row("Secondary Color", settings.email_secondary_color)
    table.add_row(
        "Email Footer",
        settings.email_footer_text or "[dim]Auto-generated[/dim]",
    )

    # AI
    table.add_section()
    table.add_row("AI Provider", settings.ai_provider)
    table.add_row("AI Model", settings.ai_model)
    table.add_row(
        "AI API Key",
        "[green]Set[/green]" if settings.ai_api_key else "[yellow]Not set[/yellow]",
    )

    console.print(table)


@app.command("reload")
def reload_config() -> None:
    """Reload configuration from .env file."""
    reload_settings()
    console.print("[green]✓ Configuration reloaded[/green]")


@app.command("set")
def set_config(
    key: str = typer.Argument(..., help="Configuration key (e.g., pec.address)"),
    value: str = typer.Argument(..., help="Configuration value"),
) -> None:
    """
    Set a configuration value.

    Note: This command updates the .env file. For complex changes,
    edit .env directly.
    """
    # Simple implementation: append to .env
    # In production, use proper .env parser like python-dotenv
    env_file = ".env"

    try:
        with open(env_file, "a") as f:
            env_key = key.upper().replace(".", "_")
            f.write(f'\n{env_key}="{value}"\n')

        console.print(f"[green]✓ Set {key} = {value}[/green]")
        console.print("[yellow]Note: Restart CLI or run 'config reload' to apply[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
