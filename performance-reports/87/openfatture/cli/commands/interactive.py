"""Conversational interactive mode for OpenFatture."""

import typer

from openfatture.cli.commands.assistant import run_assistant_session
from openfatture.cli.lifespan import run_sync_with_lifespan

app = typer.Typer()


@app.command("start")
def interactive_mode() -> None:
    """Start a conversational assistant session."""
    run_sync_with_lifespan(run_assistant_session())
