"""Click and Typer messages in the configured locale.

Click and Typer translate their own text (panel titles, ``--help``, usage
errors, prompts) with the standard ``gettext`` module, whose language comes
from the ``LANGUAGE`` environment variable. OpenFatture's own messages use
Fluent and the configured locale; ``install`` points gettext at the bundled
catalogs (``openfatture/i18n/gettext``) and at the same locale, so both halves
of the CLI speak one language. English has no catalog: the source text is
English.

``LANGUAGE`` only selects message catalogs; child processes such as hooks
inherit it, which keeps their gettext output in the same language.
"""

from __future__ import annotations

import gettext
import os
from pathlib import Path

DOMAIN = "openfatture-cli"
CATALOGS = Path(__file__).resolve().parent.parent / "i18n" / "gettext"

# Typer computes these labels when it is imported, before ``install`` can run.
_TYPER_LABELS = {
    "DEPRECATED_STRING": "(deprecated) ",
    "DEFAULT_STRING": "[default: {}]",
    "ENVVAR_STRING": "[env var: {}]",
    "REQUIRED_LONG_STRING": "[required]",
    "ARGUMENTS_PANEL_TITLE": "Arguments",
    "OPTIONS_PANEL_TITLE": "Options",
    "COMMANDS_PANEL_TITLE": "Commands",
    "ERRORS_PANEL_TITLE": "Error",
    "ABORTED_TEXT": "Aborted.",
    "RICH_HELP": "Try [blue]'{command_path} {help_option}'[/] for help.",
}


def install(locale: str) -> None:
    """Translate Click and Typer messages into ``locale`` for this process."""
    from typer import rich_utils

    gettext.bindtextdomain(DOMAIN, str(CATALOGS))
    gettext.textdomain(DOMAIN)
    os.environ["LANGUAGE"] = locale
    for name, message in _TYPER_LABELS.items():
        setattr(rich_utils, name, gettext.gettext(message))
