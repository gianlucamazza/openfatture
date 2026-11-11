"""Configuration management commands."""

from dataclasses import dataclass, field
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
    Mostra la configurazione effettiva.

    Per ogni valore indica la provenienza: ambiente, portachiavi o file delle
    credenziali, config.toml, predefinito.
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

    add(_("cli-config-label-tool-access"), settings.ai_tool_access, "ai_tool_access")
    extra_tools = [name.strip() for name in settings.ai_enabled_tools.split(",") if name.strip()]
    if extra_tools:
        add(_("cli-config-label-extra-tools"), ", ".join(extra_tools), "ai_enabled_tools")

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
    """Ricarica la configurazione da ambiente, archivio segreti e config.toml."""
    reload_settings()
    console.print(_("cli-config-reload-success"))


@app.command("set")
def set_config(
    key: str = typer.Argument(..., help=_("cli-config-help-key")),
    value: str = typer.Argument(..., help=_("cli-config-help-value")),
) -> None:
    """
    Imposta un valore di configurazione.

    Scrive solo KEY. I segreti (chiavi API, password) vanno nel portachiavi del
    sistema, o nel file privato delle credenziali se il portachiavi non c'è; gli
    altri valori in config.toml. Le chiavi annidate usano il punto, ad esempio
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
    """Rimuove KEY da config.toml o dall'archivio segreti e ripristina il predefinito."""
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
            help="Importa le impostazioni da un file dotenv (i valori già presenti restano).",
        ),
    ] = None,
) -> None:
    """
    Sposta i segreti in chiaro fuori da config.toml e importa un file .env.

    I segreti vanno nel portachiavi (o nel file privato delle credenziali); gli
    altri valori di --env-file entrano in config.toml solo se non sono già
    impostati. Il file di origine non viene modificato.
    """
    from openfatture.platform.config import read_config_file

    store = SecretStore()
    stored = read_config_file()
    report = _MigrationReport()
    _move_plaintext_secrets(store, stored, report)
    if env_file is not None:
        _import_env_file(env_file, store, stored, report)
    _print_migration_report(report, store.backend, env_file)
    reload_settings()


@dataclass
class _MigrationReport:
    """What ``config migrate`` moved, imported, kept or rejected."""

    moved: list[str] = field(default_factory=list)
    imported: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    invalid: list[tuple[str, str]] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not (self.moved or self.imported or self.conflicts or self.invalid)


def _move_plaintext_secrets(
    store: SecretStore, stored: dict[str, Any], report: _MigrationReport
) -> None:
    for name in SECRET_FIELDS:
        value = stored.get(name)
        if value:
            store.set(name, str(value))
            report.moved.append(name)
    if report.moved:
        update_config({}, remove=tuple(report.moved))


def _import_env_file(
    env_file: Path, store: SecretStore, stored: dict[str, Any], report: _MigrationReport
) -> None:
    """Add dotenv values that are not set yet; secrets go to the secret store."""
    from dotenv import dotenv_values

    from openfatture.platform.config import Settings

    changes: dict[str, Any] = {}
    for raw_key, raw_value in dotenv_values(env_file).items():
        key = raw_key.lower()
        if raw_value is None or key not in Settings.model_fields:
            continue
        try:
            value = coerce_setting(key, raw_value)
        except ValueError as exc:
            report.invalid.append((raw_key, str(exc)))
            continue
        if is_secret(key):
            _import_env_secret(store, key, raw_value, value, report)
        elif key in stored and stored[key] != value:
            report.conflicts.append(key)
        elif key not in stored:
            changes[key] = value
            report.imported.append(key)
    if changes:
        update_config(changes)


def _import_env_secret(
    store: SecretStore, key: str, raw_value: str, value: object, report: _MigrationReport
) -> None:
    if not raw_value:
        return
    if store.get(key) not in (None, "", str(value)):
        report.conflicts.append(key)
        return
    store.set(key, str(value))
    report.moved.append(key)


def _print_migration_report(
    report: _MigrationReport, backend_name: str, env_file: Path | None
) -> None:
    backend = _(
        "cli-config-source-keyring" if backend_name == "keyring" else "cli-config-source-file"
    )
    if report.moved:
        console.print(
            _(
                "cli-config-migrate-moved",
                backend=backend,
                keys=", ".join(sorted(set(report.moved))),
            )
        )
    if report.imported:
        console.print(_("cli-config-migrate-imported", keys=", ".join(sorted(report.imported))))
    if report.conflicts:
        console.print(_("cli-config-migrate-conflicts", keys=", ".join(sorted(report.conflicts))))
    for key, error in report.invalid:
        console.print(_("cli-config-invalid-value", key=key, error=error))
    if report.is_empty():
        console.print(_("cli-config-migrate-nothing"))
    if env_file is not None:
        console.print(_("cli-config-migrate-source-kept", path=str(env_file)))
