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

    # AI Configuration (expanded)
    table.add_section()
    table.add_row("AI Provider", settings.ai_provider)
    table.add_row("AI Model", settings.ai_model)

    # Show base URL for ollama
    if settings.ai_provider == "ollama":
        base_url = getattr(settings, "ai_base_url", "http://localhost:11434")
        table.add_row("AI Base URL", base_url)

    table.add_row(
        "AI API Key",
        "[green]Set[/green]" if settings.ai_api_key else "[yellow]Not set[/yellow]",
    )

    # AI Chat
    chat_enabled = getattr(settings, "ai_chat_enabled", True)
    table.add_row(
        "Chat Enabled",
        "[green]Yes[/green]" if chat_enabled else "[red]No[/red]",
    )
    table.add_row("Chat Auto-Save", str(getattr(settings, "ai_chat_auto_save", True)))
    table.add_row("Max Messages/Session", str(getattr(settings, "ai_chat_max_messages", 100)))
    table.add_row("Max Tokens/Session", str(getattr(settings, "ai_chat_max_tokens", 8000)))

    # AI Tools
    tools_enabled = getattr(settings, "ai_tools_enabled", True)
    table.add_row(
        "Tools Enabled",
        "[green]Yes[/green]" if tools_enabled else "[red]No[/red]",
    )

    enabled_tools = getattr(settings, "ai_enabled_tools", "all")
    if enabled_tools:
        tools_list = enabled_tools.split(",") if isinstance(enabled_tools, str) else enabled_tools
        table.add_row("Enabled Tools", f"{len(tools_list)} tools")

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
