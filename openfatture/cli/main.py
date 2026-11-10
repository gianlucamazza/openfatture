"""Main CLI entry point for OpenFatture."""

from uuid import uuid4

import typer
from rich.console import Console

from openfatture import __version__
from openfatture.i18n import _
from openfatture.platform.config import get_settings
from openfatture.platform.logging import configure_dynamic_logging, set_correlation_id

from .commands import assistant, cliente, config, fattura, init, pagamento, status
from .output import OutputGroup

app = typer.Typer(
    cls=OutputGroup,
    name="openfatture",
    help="Fatturazione elettronica con assistente. Avvia openfatture per conversare.",
    epilog='Esempi: openfatture · openfatture assistant "Mostra le fatture non pagate"',
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=False,
    invoke_without_command=True,
    pretty_exceptions_show_locals=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(_("cli-main-version", version=__version__))
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
    debug: bool = typer.Option(False, "--debug", help="Show diagnostic logs and tracebacks."),
    format_type: str = typer.Option(
        "rich",
        "--format",
        "-f",
        help="Output format: rich, json, markdown, stream-json, html",
    ),
) -> None:
    """Configure the CLI and start the assistant when no command is selected."""
    # One correlation ID per CLI invocation ties together every log line,
    # event and tool call of that command.
    set_correlation_id(uuid4().hex[:12])
    settings = get_settings()
    settings.debug_config.enable_debug_logging |= debug
    configure_dynamic_logging(settings.debug_config)
    ctx.ensure_object(dict)
    ctx.obj["format"] = format_type
    if ctx.invoked_subcommand is None:
        assistant.assistant(ctx, message=None, stream=True, json_output=False, session=None)


app.command(
    "assistant", help="Invia una richiesta o riprendi una sessione", rich_help_panel="Assistente"
)(assistant.assistant)
app.command("init", help="Inizializza OpenFatture", rich_help_panel="Configurazione e diagnostica")(
    init.init
)
app.add_typer(
    config.app,
    name="config",
    help="Gestisci la configurazione",
    rich_help_panel="Configurazione e diagnostica",
)
app.command(
    "status",
    help="Verifica configurazione e disponibilità",
    rich_help_panel="Configurazione e diagnostica",
)(status.status)
app.add_typer(
    cliente.app,
    name="cliente",
    help="Consulta e gestisci i clienti",
    rich_help_panel="Gestione dati",
)
app.add_typer(
    fattura.app,
    name="fattura",
    help="Consulta e gestisci le fatture",
    rich_help_panel="Gestione dati",
)


app.add_typer(
    pagamento.app,
    name="pagamento",
    help="Registra e gestisci gli incassi",
    rich_help_panel="Gestione dati",
)

if __name__ == "__main__":
    app()
