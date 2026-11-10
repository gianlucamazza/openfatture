"""Configuration management commands."""

from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.table import Table

from openfatture.cli.config_file import (
    coerce_setting,
    env_override,
    is_secret,
    resolve_setting,
    store_secret,
    update_config,
)
from openfatture.i18n import _
from openfatture.platform.config import config_sources, get_settings, reload_settings
from openfatture.platform.secrets import SECRET_FIELDS, SecretStore, config_file_path

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

    Displays the effective configuration and where each value comes from
    (environment, keychain or credentials file, config.toml, default).

    Examples:
        openfatture config show
    """
    settings = get_settings()
    sources = config_sources()
    backend = SecretStore().backend
    source_labels = {
        "env": _("cli-config-source-env"),
        "secret": _(
            "cli-config-source-keyring" if backend == "keyring" else "cli-config-source-file"
        ),
        "config": _("cli-config-source-config"),
        "default": _("cli-config-source-default"),
    }

    table = Table(title=_("cli-config-show-title"), show_header=True)
    table.add_column(_("cli-config-column-setting"), style="cyan", no_wrap=True)
    table.add_column(_("cli-config-column-value"), style="white")
    table.add_column(_("cli-config-column-source"), style="dim")

    def add(label: str, value: str, field: str | None = None) -> None:
        source = source_labels.get(sources.get(field, ""), "") if field else ""
        table.add_row(label, value, source)

    # Application
    table.add_section()
    add(
        _("cli-config-label-app-version"),
        _format_value(getattr(settings, "app_version", None)),
        field="app_version",
    )
    add(_("cli-config-label-debug-mode"), str(getattr(settings, "debug", False)), field="debug")

    # Database
    table.add_section()
    add(
        _("cli-config-label-database-url"),
        _format_value(getattr(settings, "database_url", None)),
        field="database_url",
    )

    # Paths
    table.add_section()
    add(
        _("cli-config-label-data-dir"),
        _format_value(getattr(settings, "data_dir", None)),
        field="data_dir",
    )
    add(
        _("cli-config-label-archive-dir"),
        _format_value(getattr(settings, "archivio_dir", None)),
        field="archivio_dir",
    )
    add(
        _("cli-config-label-certificates-dir"),
        _format_value(getattr(settings, "certificates_dir", None)),
        field="certificates_dir",
    )

    # Company Data
    table.add_section()
    add(
        _("cli-config-label-company-name"),
        _format_value(getattr(settings, "cedente_denominazione", None)),
        field="cedente_denominazione",
    )
    add(
        _("cli-config-label-partita-iva"),
        _format_value(getattr(settings, "cedente_partita_iva", None)),
        field="cedente_partita_iva",
    )
    add(
        _("cli-config-label-codice-fiscale"),
        _format_value(getattr(settings, "cedente_codice_fiscale", None)),
        field="cedente_codice_fiscale",
    )
    add(
        _("cli-config-label-tax-regime"),
        _format_value(getattr(settings, "cedente_regime_fiscale", None)),
        field="cedente_regime_fiscale",
    )

    # PEC
    table.add_section()
    add(
        _("cli-config-label-pec-address"),
        _format_value(getattr(settings, "pec_address", None)),
        field="pec_address",
    )
    add(
        _("cli-config-label-pec-smtp-server"),
        _format_value(getattr(settings, "pec_smtp_server", None)),
        field="pec_smtp_server",
    )
    add(
        _("cli-config-label-sdi-pec-address"),
        _format_value(getattr(settings, "sdi_pec_address", None)),
        field="sdi_pec_address",
    )

    # Email Templates & Notifications
    table.add_section()
    add(
        _("cli-config-label-notification-email"),
        _format_value(
            getattr(settings, "notification_email", None), _("cli-config-not-set-optional")
        ),
        field="notification_email",
    )
    add(
        _("cli-config-label-notifications-enabled"),
        (
            _("cli-config-yes")
            if getattr(settings, "notification_enabled", False)
            else _("cli-config-no")
        ),
        field="notification_enabled",
    )
    add(
        _("cli-config-label-locale"),
        _format_value(getattr(settings, "locale", None)),
        field="locale",
    )
    add(
        _("cli-config-label-email-logo-url"),
        _format_value(getattr(settings, "email_logo_url", None), _("cli-config-not-set-optional")),
        field="email_logo_url",
    )
    add(
        _("cli-config-label-primary-color"),
        _format_value(getattr(settings, "email_primary_color", None)),
        field="email_primary_color",
    )
    add(
        _("cli-config-label-secondary-color"),
        _format_value(getattr(settings, "email_secondary_color", None)),
        field="email_secondary_color",
    )
    add(
        _("cli-config-label-email-footer"),
        _format_value(getattr(settings, "email_footer_text", None), _("cli-config-auto-generated")),
        field="email_footer_text",
    )

    # AI Configuration (expanded)
    table.add_section()
    ai_provider = getattr(settings, "ai_provider", None)
    add(_("cli-config-label-ai-provider"), _format_value(ai_provider), field="ai_provider")
    add(
        _("cli-config-label-ai-model"),
        _format_value(getattr(settings, "ai_model", None)),
        field="ai_model",
    )

    # Show base URL for ollama
    if ai_provider == "ollama":
        base_url = getattr(settings, "ai_base_url", "http://localhost:11434")
        add(_("cli-config-label-ai-base-url"), _format_value(base_url), field="ai_base_url")

    add(
        _("cli-config-label-ai-api-key"),
        (
            _("cli-config-set")
            if getattr(settings, "ai_api_key", None)
            else _("cli-config-not-set-optional")
        ),
        field="ai_api_key",
    )

    # AI Chat
    chat_enabled = getattr(settings, "ai_chat_enabled", True)
    add(
        _("cli-config-label-chat-enabled"),
        _("cli-config-yes") if chat_enabled else _("cli-config-no"),
    )
    add(
        _("cli-config-label-chat-auto-save"),
        str(getattr(settings, "ai_chat_auto_save", True)),
        field="ai_chat_auto_save",
    )
    add(
        _("cli-config-label-max-messages"),
        str(getattr(settings, "ai_chat_max_messages", 100)),
        field="ai_chat_max_messages",
    )
    add(
        _("cli-config-label-max-tokens"),
        str(getattr(settings, "ai_chat_max_tokens", 8000)),
        field="ai_chat_max_tokens",
    )

    # AI Tools
    tools_enabled = getattr(settings, "ai_tools_enabled", True)
    add(
        _("cli-config-label-tools-enabled"),
        _("cli-config-yes") if tools_enabled else _("cli-config-no"),
    )

    enabled_tools = getattr(settings, "ai_enabled_tools", "all")
    if isinstance(enabled_tools, str):
        if enabled_tools.lower() == "all":
            add(_("cli-config-label-enabled-tools"), _("cli-config-all-tools"))
        else:
            tool_names = [tool.strip() for tool in enabled_tools.split(",") if tool.strip()]
            if tool_names:
                add(
                    _("cli-config-label-enabled-tools"),
                    _("cli-config-tools-count", count=len(tool_names)),
                )
    elif isinstance(enabled_tools, list | tuple | set):
        add(
            _("cli-config-label-enabled-tools"),
            _("cli-config-tools-count", count=len(enabled_tools)),
        )

    console.print(table)
    console.print(_("cli-config-file-path", path=str(config_file_path())))
    console.print(
        _(
            "cli-config-secret-backend",
            backend=source_labels["secret"],
        )
    )


@app.command("reload")
def reload_config() -> None:
    """Reload configuration from the environment, secret store and config.toml."""
    reload_settings()
    console.print(_("cli-config-reload-success"))


@app.command("set")
def set_config(
    key: str = typer.Argument(..., help=_("cli-config-help-key")),
    value: str = typer.Argument(..., help=_("cli-config-help-value")),
) -> None:
    """
    Set a configuration value.

    Only KEY is written. Secrets (API keys, passwords) go to the OS keychain,
    or to the private credentials file when no keychain is available; other
    values go to config.toml. Nested keys use dots, e.g.
    debug_config.enable_debug_logging.
    """
    from openfatture.platform.logging import redact_sensitive

    try:
        stored = coerce_setting(key, value)
    except KeyError:
        console.print(_("cli-config-invalid-key", key=key))
        raise typer.Exit(1) from None
    except ValueError as exc:
        console.print(_("cli-config-invalid-value", key=key, error=str(exc)))
        raise typer.Exit(1) from None

    try:
        if is_secret(key):
            backend = store_secret(key, str(stored))
            # A plaintext copy left in config.toml would be misleading.
            update_config({}, remove=(key,))
        else:
            update_config({key: stored})
    except Exception as exc:
        console.print(_("cli-config-error", error=str(exc)))
        raise typer.Exit(1) from exc

    if is_secret(key):
        label = _("cli-config-source-keyring" if backend == "keyring" else "cli-config-source-file")
        console.print(_("cli-config-secret-saved", key=key, backend=label))
    else:
        display_value = redact_sensitive({key: value})[key]
        console.print(_("cli-config-set-success", key=key, value=display_value))
        console.print(_("cli-config-saved-to", path=str(config_file_path())))
    if env_override(key):
        console.print(_("cli-config-env-override", key=key))
    reload_settings()


@app.command("unset")
def unset_config(key: str = typer.Argument(..., help=_("cli-config-help-key"))) -> None:
    """Remove KEY from config.toml or the secret store, restoring its default."""
    from openfatture.platform.config import read_config_file

    try:
        resolve_setting(key)
    except KeyError:
        console.print(_("cli-config-invalid-key", key=key))
        raise typer.Exit(1) from None

    removed = False
    if is_secret(key):
        removed = SecretStore().delete(key)
    stored: object = read_config_file()
    for part in key.split("."):
        stored = stored.get(part) if isinstance(stored, dict) else None
    if stored is not None:
        update_config({}, remove=(key,))
        removed = True
    console.print(_("cli-config-unset-success" if removed else "cli-config-unset-missing", key=key))
    reload_settings()


@app.command("migrate")
def migrate_config(
    env_file: Annotated[
        Path | None,
        typer.Option(
            "--env-file",
            exists=True,
            dir_okay=False,
            help="Import settings from a dotenv file (existing values are kept).",
        ),
    ] = None,
) -> None:
    """
    Move plaintext secrets out of config.toml and optionally import a .env file.

    Secrets go to the OS keychain (or the private credentials file); other
    values from --env-file are added to config.toml only when not already set.
    The source file is never modified.
    """
    from openfatture.platform.config import Settings, read_config_file

    store = SecretStore()
    stored = read_config_file()
    moved: list[str] = []
    imported: list[str] = []
    conflicts: list[str] = []
    invalid: list[tuple[str, str]] = []

    for name in SECRET_FIELDS:
        value = stored.get(name)
        if value:
            store.set(name, str(value))
            moved.append(name)
    if moved:
        update_config({}, remove=tuple(moved))

    if env_file is not None:
        from dotenv import dotenv_values

        changes: dict[str, Any] = {}
        for raw_key, raw_value in dotenv_values(env_file).items():
            key = raw_key.lower()
            if raw_value is None or key not in Settings.model_fields:
                continue
            try:
                value = coerce_setting(key, raw_value)
            except ValueError as exc:
                invalid.append((raw_key, str(exc)))
                continue
            if is_secret(key):
                if not raw_value:
                    continue
                if store.get(key) not in (None, "", str(value)):
                    conflicts.append(key)
                    continue
                store.set(key, str(value))
                moved.append(key)
            elif key in stored and stored[key] != value:
                conflicts.append(key)
            elif key not in stored:
                changes[key] = value
                imported.append(key)
        if changes:
            update_config(changes)

    backend = _(
        "cli-config-source-keyring" if store.backend == "keyring" else "cli-config-source-file"
    )
    if moved:
        console.print(
            _("cli-config-migrate-moved", backend=backend, keys=", ".join(sorted(set(moved))))
        )
    if imported:
        console.print(_("cli-config-migrate-imported", keys=", ".join(sorted(imported))))
    if conflicts:
        console.print(_("cli-config-migrate-conflicts", keys=", ".join(sorted(conflicts))))
    for key, error in invalid:
        console.print(_("cli-config-invalid-value", key=key, error=error))
    if not (moved or imported or conflicts or invalid):
        console.print(_("cli-config-migrate-nothing"))
    if env_file is not None:
        console.print(_("cli-config-migrate-source-kept", path=str(env_file)))
    reload_settings()
