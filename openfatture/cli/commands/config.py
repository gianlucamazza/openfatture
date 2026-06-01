"""Configuration management commands."""

from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from openfatture.i18n import _
from openfatture.utils.config import get_settings, reload_settings

app = typer.Typer(no_args_is_help=True)
console = Console()


def _format_value(value: Any, fallback: str | None = None) -> str:
    """Return a safe string representation for configuration values."""
    if fallback is None:
        fallback = _("cli-config-not-set")
    if value is None:
        return fallback
    if isinstance(value, str):
        return value or fallback
    module = getattr(value, "__class__", type(value)).__module__
    if module.startswith("unittest.mock"):
        return fallback
    return str(value)


@app.command("show")
def show_config() -> None:
    """
    Show current configuration settings.

    Displays all configuration values from environment variables and .env file,
    organized by category (company data, AI settings, database, etc.).

    Examples:
        openfatture config show
    """
    settings = get_settings()

    table = Table(title=_("cli-config-show-title"), show_header=True)
    table.add_column(_("cli-config-column-setting"), style="cyan", no_wrap=True)
    table.add_column(_("cli-config-column-value"), style="white")

    # Application
    table.add_section()
    table.add_row(
        _("cli-config-label-app-version"), _format_value(getattr(settings, "app_version", None))
    )
    table.add_row(_("cli-config-label-debug-mode"), str(getattr(settings, "debug", False)))

    # Database
    table.add_section()
    table.add_row(
        _("cli-config-label-database-url"), _format_value(getattr(settings, "database_url", None))
    )

    # Paths
    table.add_section()
    table.add_row(
        _("cli-config-label-data-dir"), _format_value(getattr(settings, "data_dir", None))
    )
    table.add_row(
        _("cli-config-label-archive-dir"), _format_value(getattr(settings, "archivio_dir", None))
    )
    table.add_row(
        _("cli-config-label-certificates-dir"),
        _format_value(getattr(settings, "certificates_dir", None)),
    )

    # Company Data
    table.add_section()
    table.add_row(
        _("cli-config-label-company-name"),
        _format_value(getattr(settings, "cedente_denominazione", None)),
    )
    table.add_row(
        _("cli-config-label-partita-iva"),
        _format_value(getattr(settings, "cedente_partita_iva", None)),
    )
    table.add_row(
        _("cli-config-label-codice-fiscale"),
        _format_value(getattr(settings, "cedente_codice_fiscale", None)),
    )
    table.add_row(
        _("cli-config-label-tax-regime"),
        _format_value(getattr(settings, "cedente_regime_fiscale", None)),
    )

    # PEC
    table.add_section()
    table.add_row(
        _("cli-config-label-pec-address"), _format_value(getattr(settings, "pec_address", None))
    )
    table.add_row(
        _("cli-config-label-pec-smtp-server"),
        _format_value(getattr(settings, "pec_smtp_server", None)),
    )
    table.add_row(
        _("cli-config-label-sdi-pec-address"),
        _format_value(getattr(settings, "sdi_pec_address", None)),
    )

    # Email Templates & Notifications
    table.add_section()
    table.add_row(
        _("cli-config-label-notification-email"),
        _format_value(
            getattr(settings, "notification_email", None), _("cli-config-not-set-optional")
        ),
    )
    table.add_row(
        _("cli-config-label-notifications-enabled"),
        (
            _("cli-config-yes")
            if getattr(settings, "notification_enabled", False)
            else _("cli-config-no")
        ),
    )
    table.add_row(_("cli-config-label-locale"), _format_value(getattr(settings, "locale", None)))
    table.add_row(
        _("cli-config-label-email-logo-url"),
        _format_value(getattr(settings, "email_logo_url", None), _("cli-config-not-set-optional")),
    )
    table.add_row(
        _("cli-config-label-primary-color"),
        _format_value(getattr(settings, "email_primary_color", None)),
    )
    table.add_row(
        _("cli-config-label-secondary-color"),
        _format_value(getattr(settings, "email_secondary_color", None)),
    )
    table.add_row(
        _("cli-config-label-email-footer"),
        _format_value(getattr(settings, "email_footer_text", None), _("cli-config-auto-generated")),
    )

    # AI Configuration (expanded)
    table.add_section()
    ai_provider = getattr(settings, "ai_provider", None)
    table.add_row(_("cli-config-label-ai-provider"), _format_value(ai_provider))
    table.add_row(
        _("cli-config-label-ai-model"), _format_value(getattr(settings, "ai_model", None))
    )

    # Show base URL for ollama
    if ai_provider == "ollama":
        base_url = getattr(settings, "ai_base_url", "http://localhost:11434")
        table.add_row(_("cli-config-label-ai-base-url"), _format_value(base_url))

    table.add_row(
        _("cli-config-label-ai-api-key"),
        (
            _("cli-config-set")
            if getattr(settings, "ai_api_key", None)
            else _("cli-config-not-set-optional")
        ),
    )

    # AI Chat
    chat_enabled = getattr(settings, "ai_chat_enabled", True)
    table.add_row(
        _("cli-config-label-chat-enabled"),
        _("cli-config-yes") if chat_enabled else _("cli-config-no"),
    )
    table.add_row(
        _("cli-config-label-chat-auto-save"), str(getattr(settings, "ai_chat_auto_save", True))
    )
    table.add_row(
        _("cli-config-label-max-messages"), str(getattr(settings, "ai_chat_max_messages", 100))
    )
    table.add_row(
        _("cli-config-label-max-tokens"), str(getattr(settings, "ai_chat_max_tokens", 8000))
    )

    # AI Tools
    tools_enabled = getattr(settings, "ai_tools_enabled", True)
    table.add_row(
        _("cli-config-label-tools-enabled"),
        _("cli-config-yes") if tools_enabled else _("cli-config-no"),
    )

    enabled_tools = getattr(settings, "ai_enabled_tools", "all")
    if isinstance(enabled_tools, str):
        if enabled_tools.lower() == "all":
            table.add_row(_("cli-config-label-enabled-tools"), _("cli-config-all-tools"))
        else:
            tool_names = [tool.strip() for tool in enabled_tools.split(",") if tool.strip()]
            if tool_names:
                table.add_row(
                    _("cli-config-label-enabled-tools"),
                    _("cli-config-tools-count", count=len(tool_names)),
                )
    elif isinstance(enabled_tools, list | tuple | set):
        table.add_row(
            _("cli-config-label-enabled-tools"),
            _("cli-config-tools-count", count=len(enabled_tools)),
        )

    console.print(table)


@app.command("reload")
def reload_config() -> None:
    """Reload configuration from .env file."""
    reload_settings()
    console.print(_("cli-config-reload-success"))


@app.command("set")
def set_config(
    key: str = typer.Argument(..., help=_("cli-config-help-key")),
    value: str = typer.Argument(..., help=_("cli-config-help-value")),
) -> None:
    """
    Set a configuration value.

    Updates the config.toml file.
    """

    from openfatture.cli.wizard import save_config
    from openfatture.utils.config import dirs

    try:
        settings = get_settings()

        # Handle nested keys (e.g., debug_config.enable_debug_logging)
        if "." in key:
            parts = key.split(".")
            target = settings
            for part in parts[:-1]:
                if not hasattr(target, part):
                    console.print(_("cli-config-invalid-key", key=key))
                    raise typer.Exit(1)
                target = getattr(target, part)

            last_key = parts[-1]
            if not hasattr(target, last_key):
                console.print(_("cli-config-invalid-key", key=key))
                raise typer.Exit(1)

            # Basic type conversion
            current_value = getattr(target, last_key)
            new_value: Any
            if isinstance(current_value, bool):
                new_value = value.lower() == "true"
            elif isinstance(current_value, int):
                new_value = int(value)
            elif isinstance(current_value, float):
                new_value = float(value)
            else:
                new_value = value

            setattr(target, last_key, new_value)
        else:
            if not hasattr(settings, key):
                console.print(_("cli-config-invalid-key", key=key))
                raise typer.Exit(1)

            # Basic type conversion
            current_value = getattr(settings, key)
            new_val: Any
            if isinstance(current_value, bool):
                new_val = value.lower() == "true"
            elif isinstance(current_value, int):
                new_val = int(value)
            elif isinstance(current_value, float):
                new_val = float(value)
            else:
                new_val = value

            setattr(settings, key, new_val)

        # Save to TOML. dirs.user_config_dir is a str (platformdirs), so wrap it
        # in Path before joining.
        config_path = Path(dirs.user_config_dir) / "config.toml"
        save_config(settings, config_path)

        console.print(_("cli-config-set-success", key=key, value=value))
        console.print(_("cli-config-saved-to", path=config_path))

    except Exception as e:
        console.print(_("cli-config-error", error=str(e)))
        raise typer.Exit(1)
