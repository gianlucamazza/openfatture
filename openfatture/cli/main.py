"""Main CLI entry point for OpenFatture."""

import typer
from rich.console import Console

from openfatture import __version__
from openfatture.utils.config import get_settings
from openfatture.utils.logging import configure_dynamic_logging

# Payment CLI lives in the payment package to keep the top-level commands lean.
from ..payment.cli import app as payment_app

# Import command modules
from .commands import (
    ai,
    batch,
    cliente,
    config,
    email,
    events,
    fattura,
    hooks,
    init,
    interactive,
    lightning,
    media,
    notifiche,
    pec,
    plugin,
    preventivo,
    report,
    web_scraper,
)

# Create main app and console
app = typer.Typer(
    name="openfatture",
    help="🧾 Open-source electronic invoicing for Italian freelancers",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,  # Show help when no command is provided
)
console = Console()


def _initialize_plugin_system(settings) -> None:
    """Initialize the plugin system."""
    try:
        from openfatture.plugins import PluginDiscovery, get_plugin_registry

        registry = get_plugin_registry()

        # Auto-discover plugins if enabled
        if settings.plugins_auto_discover:
            discovery = PluginDiscovery([settings.plugins_dir])
            discovery.auto_register_plugins()

        # Enable plugins from configuration
        if settings.plugins_enabled_list:
            enabled_plugins = [p.strip() for p in settings.plugins_enabled_list.split(",")]
            for plugin_name in enabled_plugins:
                registry.enable_plugin(plugin_name)
        else:
            # Enable all discovered plugins by default
            for plugin in registry.list_plugins():
                registry.enable_plugin(plugin.metadata.name)

        # Initialize enabled plugins with empty config for now
        # TODO: Load plugin-specific configuration
        registry.initialize_enabled_plugins({})

    except Exception as e:
        # Don't fail startup if plugin system fails
        console.print(f"[yellow]Warning: Plugin system initialization failed: {e}[/yellow]")


def _register_plugin_commands() -> None:
    """Register plugin CLI commands with the main app."""
    try:
        from openfatture.plugins import get_plugin_registry
        from openfatture.utils.config import get_settings

        settings = get_settings()
        if not settings.plugins_enabled:
            return

        registry = get_plugin_registry()

        # Register CLI commands for enabled plugins
        for plugin in registry.list_enabled_plugins():
            cli_app = plugin.get_cli_app()
            if cli_app:
                app.add_typer(cli_app, name=plugin.metadata.name)

    except Exception as e:
        # Don't fail if plugin command registration fails
        pass


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"[bold blue]OpenFatture[/bold blue] version {__version__}")
        raise typer.Exit()


def is_interactive() -> bool:
    """Check if the session is interactive."""
    import sys

    return sys.stdin.isatty()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
    interactive_mode: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Launch interactive mode with menus",
    ),
    format_type: str = typer.Option(
        "rich",
        "--format",
        "-f",
        help="Output format: rich, json, markdown, stream-json, html",
    ),
) -> None:
    """
    OpenFatture - Electronic invoicing made simple.

    A modern, CLI-first tool for Italian freelancers to create and manage
    FatturaPA electronic invoices with AI-powered workflows.
    """
    # Check for configuration existence (First Run)
    from openfatture.utils.config import dirs

    config_path = dirs.user_config_dir / "config.toml"

    if not config_path.exists() and not ctx.invoked_subcommand == "init":
        # Only run wizard if not explicitly running 'init' (which might be used for manual setup)
        # and if we are in an interactive terminal
        if is_interactive():
            from .wizard import run_setup_wizard

            run_setup_wizard()
            # Reload settings after wizard
            from openfatture.utils.config import reload_settings

            reload_settings()

    # Initialize dynamic logging configuration
    settings = get_settings()
    configure_dynamic_logging(settings.debug_config)

    # Initialize plugin system
    if settings.plugins_enabled:
        _initialize_plugin_system(settings)
        # Register plugin CLI commands after initialization
        _register_plugin_commands()

    # Store format option in context for subcommands to access
    ctx.ensure_object(dict)
    ctx.obj["format"] = format_type

    # If --interactive flag is set and no subcommand, launch interactive mode
    if ctx.invoked_subcommand is None and interactive_mode:
        from .commands.interactive import interactive_mode as start_interactive

        start_interactive()
        raise typer.Exit()


# Register command groups
app.add_typer(interactive.app, name="interactive", help="🎯 Interactive mode with menus")
app.add_typer(init.app, name="init", help="🚀 Initialize OpenFatture")
app.add_typer(config.app, name="config", help="⚙️  Manage configuration")
app.add_typer(cliente.app, name="cliente", help="👤 Manage clients")
app.add_typer(fattura.app, name="fattura", help="🧾 Manage invoices")
app.add_typer(preventivo.app, name="preventivo", help="📋 Manage quotes/estimates")
app.add_typer(pec.app, name="pec", help="📧 PEC configuration and testing")
app.add_typer(email.app, name="email", help="📧 Email templates & testing")
app.add_typer(notifiche.app, name="notifiche", help="📬 SDI notifications")
app.add_typer(batch.app, name="batch", help="📦 Batch operations")
app.add_typer(ai.app, name="ai", help="🤖 AI-powered assistance")
app.add_typer(lightning.app, name="lightning", help="⚡ Lightning Network payments")
app.add_typer(media.app, name="media", help="🎬 Media automation & VHS generation")
app.add_typer(hooks.app, name="hooks", help="🪝 Manage lifecycle hooks")
app.add_typer(events.app, name="events", help="📜 View event history & audit log")
app.add_typer(report.app, name="report", help="📊 Generate reports")
app.add_typer(web_scraper.app, name="web-scraper", help="🕷️ Regulatory web scraping")
app.add_typer(plugin.app, name="plugin", help="🔌 Manage plugins")
app.add_typer(payment_app, name="payment", help="💰 Payment tracking & reconciliation")

# Pre-load plugins and register their CLI commands
try:
    from openfatture.utils.config import get_settings

    settings = get_settings()
    if settings.plugins_enabled:
        # Initialize plugin system
        _initialize_plugin_system(settings)
        # Register plugin CLI commands
        _register_plugin_commands()
except Exception as e:
    # Don't fail startup if plugin system fails during import
    pass


if __name__ == "__main__":
    app()
