"""Initialize database access for each fresh CLI process."""

from __future__ import annotations

import typer
from rich.console import Console
from sqlalchemy.engine import make_url

from openfatture.platform.config import get_settings
from openfatture.platform.logging import redact_sensitive
from openfatture.storage.database import base


def ensure_database() -> None:
    settings = get_settings()
    try:
        if (
            base.engine is None
            or base.SessionLocal is None
            or base.engine.url != make_url(settings.database_url)
        ):
            base.init_db(settings.database_url)
    except Exception as exc:
        from openfatture.cli.assistant_ui import translate

        Console(stderr=True).print(translate("cli-database-unavailable", settings.locale))
        if settings.debug_config.enable_debug_logging:
            import traceback

            Console(stderr=True).print(redact_sensitive(traceback.format_exc()), markup=False)
        raise typer.Exit(1) from exc
