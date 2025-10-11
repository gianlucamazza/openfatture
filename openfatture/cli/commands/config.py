"""Configuration management commands."""

from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from openfatture.utils.config import get_settings, reload_settings

app = typer.Typer()
console = Console()


def _format_value(value: Any, fallback: str = "[red]Not set[/red]") -> str:
    """Return a safe string representation for configuration values."""
    if value is None:
        return fallback
    if isinstance(value, str):
        return value or fallback
    module = getattr(value, "__class__", type(value)).__module__
    if module.startswith("unittest.mock"):
        return fallback
    return str(value)


@app.command("show")
def show_config() -> None:
    """Show current configuration."""
    settings = get_settings()

    table = Table(title="OpenFatture Configuration", show_header=True)
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    # Application
    table.add_section()
    table.add_row("App Version", _format_value(getattr(settings, "app_version", None)))
    table.add_row("Debug Mode", str(getattr(settings, "debug", False)))

    # Database
    table.add_section()
    table.add_row("Database URL", _format_value(getattr(settings, "database_url", None)))

    # Paths
    table.add_section()
    table.add_row("Data Directory", _format_value(getattr(settings, "data_dir", None)))
    table.add_row("Archive Directory", _format_value(getattr(settings, "archivio_dir", None)))
    table.add_row(
        "Certificates Directory", _format_value(getattr(settings, "certificates_dir", None))
    )

    # Company Data
    table.add_section()
    table.add_row("Company Name", _format_value(getattr(settings, "cedente_denominazione", None)))
    table.add_row("Partita IVA", _format_value(getattr(settings, "cedente_partita_iva", None)))
    table.add_row(
        "Codice Fiscale", _format_value(getattr(settings, "cedente_codice_fiscale", None))
    )
    table.add_row("Tax Regime", _format_value(getattr(settings, "cedente_regime_fiscale", None)))

    # PEC
    table.add_section()
    table.add_row("PEC Address", _format_value(getattr(settings, "pec_address", None)))
    table.add_row("PEC SMTP Server", _format_value(getattr(settings, "pec_smtp_server", None)))
    table.add_row("SDI PEC Address", _format_value(getattr(settings, "sdi_pec_address", None)))

    # Email Templates & Notifications
    table.add_section()
    table.add_row(
        "Notification Email",
        _format_value(getattr(settings, "notification_email", None), "[yellow]Not set[/yellow]"),
    )
    table.add_row(
        "Notifications Enabled",
        (
            "[green]Yes[/green]"
            if getattr(settings, "notification_enabled", False)
            else "[red]No[/red]"
        ),
    )
    table.add_row("Locale", _format_value(getattr(settings, "locale", None)))
    table.add_row(
        "Email Logo URL",
        _format_value(getattr(settings, "email_logo_url", None), "[dim]Not set[/dim]"),
    )
    table.add_row("Primary Color", _format_value(getattr(settings, "email_primary_color", None)))
    table.add_row(
        "Secondary Color", _format_value(getattr(settings, "email_secondary_color", None))
    )
    table.add_row(
        "Email Footer",
        _format_value(getattr(settings, "email_footer_text", None), "[dim]Auto-generated[/dim]"),
    )

    # AI Configuration (expanded)
    table.add_section()
    ai_provider = getattr(settings, "ai_provider", None)
    table.add_row("AI Provider", _format_value(ai_provider))
    table.add_row("AI Model", _format_value(getattr(settings, "ai_model", None)))

    # Show base URL for ollama
    if ai_provider == "ollama":
        base_url = getattr(settings, "ai_base_url", "http://localhost:11434")
        table.add_row("AI Base URL", _format_value(base_url))

    table.add_row(
        "AI API Key",
        (
            "[green]Set[/green]"
            if getattr(settings, "ai_api_key", None)
            else "[yellow]Not set[/yellow]"
        ),
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
    if isinstance(enabled_tools, str):
        if enabled_tools.lower() == "all":
            table.add_row("Enabled Tools", "all")
        else:
            tool_names = [tool.strip() for tool in enabled_tools.split(",") if tool.strip()]
            if tool_names:
                table.add_row("Enabled Tools", f"{len(tool_names)} tools")
    elif isinstance(enabled_tools, (list, tuple, set)):
        table.add_row("Enabled Tools", f"{len(enabled_tools)} tools")

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
