"""Main CLI entry point for OpenFatture."""

from uuid import uuid4

import typer
from rich.console import Console

from openfatture import __version__
from openfatture.i18n import _, get_locale
from openfatture.platform.config import get_settings
from openfatture.platform.logging import configure_dynamic_logging, set_correlation_id

from . import framework_i18n
from .commands import assistant, config, fattura, init, status
from .output import OutputGroup

framework_i18n.install(get_locale())

app = typer.Typer(
    cls=OutputGroup,
    name="openfatture",
    help=_("cli-help-app"),
    epilog=_("cli-help-epilog"),
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
        help=_("cli-help-version"),
    ),
    debug: bool = typer.Option(False, "--debug", help=_("cli-help-debug")),
    format_type: str = typer.Option(
        "rich",
        "--format",
        "-f",
        help=_("cli-help-format"),
    ),
    message: str | None = typer.Option(
        None,
        "--message",
        "-m",
        help=_("cli-help-assistant-message"),
        rich_help_panel=_("cli-help-panel-assistant"),
    ),
    session: str | None = typer.Option(
        None,
        "--session",
        help=_("cli-help-assistant-session"),
        rich_help_panel=_("cli-help-panel-assistant"),
    ),
    stream: bool = typer.Option(
        True,
        "--stream/--no-stream",
        help=_("cli-help-assistant-stream"),
        rich_help_panel=_("cli-help-panel-assistant"),
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
        assistant.start(ctx, message=message, stream=stream, session=session)
    elif message is not None or session is not None:
        raise typer.BadParameter(_("cli-help-assistant-options-alone"))


app.command("init", help=_("cli-help-init"), rich_help_panel=_("cli-help-panel-setup"))(init.init)
app.add_typer(
    config.app,
    name="config",
    help=_("cli-help-config"),
    rich_help_panel=_("cli-help-panel-setup"),
)
app.command(
    "status",
    help=_("cli-help-status"),
    rich_help_panel=_("cli-help-panel-setup"),
)(status.status)
app.add_typer(
    fattura.app,
    name="fattura",
    help=_("cli-help-fattura"),
    rich_help_panel=_("cli-help-panel-sdi"),
)

if __name__ == "__main__":
    app()
