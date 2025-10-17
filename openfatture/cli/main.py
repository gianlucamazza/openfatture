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


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"[bold blue]OpenFatture[/bold blue] version {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
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
    # Initialize dynamic logging configuration
    settings = get_settings()
    configure_dynamic_logging(settings.debug_config)

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
app.add_typer(payment_app, name="payment", help="💰 Payment tracking & reconciliation")


if __name__ == "__main__":
    app()
