"""Main CLI entry point for OpenFatture."""

import typer
from rich.console import Console

from openfatture import __version__
from openfatture.utils.config import get_settings
from openfatture.utils.logging import configure_dynamic_logging

from .commands import assistant, config, init, interactive, status

app = typer.Typer(
    name="openfatture",
    help="Agentic electronic invoicing for Italian freelancers.",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"[bold blue]OpenFatture[/bold blue] version {__version__}")
        raise typer.Exit()


@app.callback()
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
    format_type: str = typer.Option(
        "rich",
        "--format",
        "-f",
        help="Output format: rich, json, markdown, stream-json, html",
    ),
) -> None:
    """Configure output and logging for the selected command."""
    settings = get_settings()
    configure_dynamic_logging(settings.debug_config)
    ctx.ensure_object(dict)
    ctx.obj["format"] = format_type


app.command("assistant", help="Ask the business assistant")(assistant.assistant)
app.add_typer(interactive.app, name="interactive", help="Start a conversational session")
app.add_typer(init.app, name="init", help="Initialize OpenFatture")
app.add_typer(config.app, name="config", help="Manage configuration")
app.command("status", help="Show local readiness and configuration")(status.status)


if __name__ == "__main__":
    app()
