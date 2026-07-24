"""Read-only application status command."""

import json

import typer
from rich.console import Console
from rich.table import Table

from openfatture import __version__
from openfatture.utils.config import get_settings

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def status(json_output: bool = typer.Option(False, "--json", help="Emit status as JSON.")) -> None:
    """Show local configuration and storage readiness without changing state."""
    settings = get_settings()
    data = {
        "version": __version__,
        "database": str(settings.database_url),
        "data_dir": str(settings.data_dir),
        "archive_dir": str(settings.archivio_dir),
        "ai_provider": settings.ai_provider,
        "ai_model": settings.ai_model,
        "ai_api_key_configured": bool(settings.ai_api_key),
    }
    if json_output:
        console.print(json.dumps(data, indent=2, default=str))
        return
    table = Table(title="OpenFatture status")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")
    for key, value in data.items():
        table.add_row(key.replace("_", " ").title(), str(value))
    console.print(table)
