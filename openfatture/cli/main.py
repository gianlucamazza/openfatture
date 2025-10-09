"""Main CLI entry point for OpenFatture."""

import typer
from rich.console import Console

from openfatture import __version__

# Import command modules
from .commands import (
    ai,
    batch,
    cliente,
    config,
    email,
    fattura,
    init,
    interactive,
    notifiche,
    pec,
    report,
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
) -> None:
    """
    OpenFatture - Electronic invoicing made simple.

    A modern, CLI-first tool for Italian freelancers to create and manage
    FatturaPA electronic invoices with AI-powered workflows.
    """
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
app.add_typer(pec.app, name="pec", help="📧 PEC configuration and testing")
app.add_typer(email.app, name="email", help="📧 Email templates & testing")
app.add_typer(notifiche.app, name="notifiche", help="📬 SDI notifications")
app.add_typer(batch.app, name="batch", help="📦 Batch operations")
app.add_typer(ai.app, name="ai", help="🤖 AI-powered assistance")
app.add_typer(report.app, name="report", help="📊 Generate reports")


if __name__ == "__main__":
    app()
