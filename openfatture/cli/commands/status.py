"""Read-only application status command."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from openfatture import __version__
from openfatture.cli.output import remember_result
from openfatture.platform.config import Settings, get_settings
from openfatture.platform.extras import available_extras

app = typer.Typer(no_args_is_help=True)
console = Console()


def _hooks_dir() -> Path:
    """Default hooks directory used by the hooks engine."""
    return Path.home() / ".openfatture" / "hooks"


_REQUIRED_FISCAL_FIELDS = (
    "cedente_codice_fiscale",
    "cedente_regime_fiscale",
    "cedente_indirizzo",
    "cedente_cap",
    "cedente_comune",
    "cedente_provincia",
    "cedente_nazione",
)


def _missing_fiscal_fields(settings: Settings) -> list[str]:
    return [
        field
        for field in _REQUIRED_FISCAL_FIELDS
        if not str(getattr(settings, field, "") or "").strip()
    ]


def _invalid_fiscal_fields(settings: Settings) -> list[str]:
    from openfatture.platform.validators import (
        validate_codice_fiscale,
        validate_partita_iva,
        validate_regime_fiscale,
    )

    invalid_fields = []
    if settings.cedente_partita_iva and not validate_partita_iva(settings.cedente_partita_iva):
        invalid_fields.append("cedente_partita_iva")
    fiscal_code = getattr(settings, "cedente_codice_fiscale", "")
    if fiscal_code and not (
        validate_codice_fiscale(fiscal_code) or validate_partita_iva(fiscal_code)
    ):
        invalid_fields.append("cedente_codice_fiscale")
    regime = getattr(settings, "cedente_regime_fiscale", "")
    if regime and not validate_regime_fiscale(regime):
        invalid_fields.append("cedente_regime_fiscale")
    return invalid_fields


def _core_next_steps(core_ready: bool, blocking_fields: list[str]) -> list[str]:
    if core_ready:
        return []
    return ["Run: openfatture init"] + [
        f"openfatture config set {field} '<value>'" for field in blocking_fields
    ]


def _assistant_next_steps(core_ready: bool, ai_extra: bool, ai_credentials_ok: bool) -> list[str]:
    next_steps: list[str] = []
    if not ai_extra:
        next_steps.append("For the assistant: uv sync --extra ai")
    elif not ai_credentials_ok:
        next_steps.append("openfatture config set ai_api_key '<key>' (or ai_provider ollama)")
    if core_ready and ai_extra and ai_credentials_ok:
        next_steps.append('Try: openfatture assistant "Elenca le fatture aperte"')
    elif core_ready and not ai_extra:
        # Only when the ai extra itself is missing — not when credentials alone fail.
        next_steps.append("Core is ready; enable the ai extra to use the assistant")
    return next_steps


def _readiness(settings: Settings, extras: dict[str, bool]) -> dict[str, Any]:
    """Compute honest setup readiness (core invoicing vs assistant)."""
    company_ok = bool(
        (settings.cedente_partita_iva or "").strip()
        and (settings.cedente_denominazione or "").strip()
    )
    data_dir_ok = settings.data_dir.exists()
    archive_ok = settings.archivio_dir.exists()
    ai_extra = bool(extras.get("ai"))
    provider = (settings.ai_provider or "").lower()
    # Ollama needs no cloud key; cloud providers need a key for real calls.
    ai_credentials_ok = provider == "ollama" or bool(settings.ai_api_key)
    assistant_ready = ai_extra and ai_credentials_ok
    missing_fields = _missing_fiscal_fields(settings)
    invalid_fields = _invalid_fiscal_fields(settings)
    core_ready = (
        company_ok and data_dir_ok and archive_ok and not missing_fields and not invalid_fields
    )

    next_steps = _core_next_steps(core_ready, missing_fields + invalid_fields)
    next_steps += _assistant_next_steps(core_ready, ai_extra, ai_credentials_ok)
    if not next_steps:
        next_steps.append("openfatture --help")

    return {
        "core_ready": core_ready,
        "missing_fields": missing_fields,
        "invalid_fields": invalid_fields,
        "invoice_ready": core_ready,
        "delivery_configured": core_ready and bool(settings.pec_address and settings.pec_password),
        "assistant_ready": assistant_ready,
        "assistant_authenticated": None,
        "checks": {
            "company_profile": company_ok,
            "fiscal_profile": not missing_fields and not invalid_fields,
            "data_dir": data_dir_ok,
            "archive_dir": archive_ok,
            "ai_extra": ai_extra,
            "ai_credentials": ai_credentials_ok,
        },
        "next_steps": next_steps,
    }


def _configuration() -> dict[str, Any]:
    """Where configuration lives and whether it needs attention (read-only)."""
    from pathlib import Path

    from openfatture.platform.config import plaintext_secrets
    from openfatture.platform.secrets import backend_name as secret_backend
    from openfatture.platform.secrets import config_file_path, credentials_file_path

    config_file = config_file_path()
    backend = secret_backend()
    return {
        "config_file": str(config_file),
        "config_file_exists": config_file.exists(),
        "secret_backend": backend,
        "credentials_file": str(credentials_file_path()) if backend == "file" else None,
        "plaintext_secrets": plaintext_secrets(),
        "ignored_dotenv": (Path.cwd() / ".env").is_file(),
    }


def _build_status() -> dict[str, Any]:
    settings = get_settings()
    extras = available_extras()
    hooks_dir = _hooks_dir()
    hook_scripts = []
    if hooks_dir.is_dir():
        hook_scripts = sorted(
            p.name for p in hooks_dir.iterdir() if p.is_file() and not p.name.startswith(".")
        )
    readiness = _readiness(settings, extras)
    from openfatture.storage.schema import database_schema_state

    database_schema = database_schema_state(str(settings.database_url))
    readiness["checks"]["database_schema"] = database_schema in ("current", "unversioned")
    if database_schema in ("outdated", "ahead"):
        readiness["core_ready"] = readiness["invoice_ready"] = False
    if database_schema in ("outdated", "unversioned"):
        readiness["next_steps"].insert(0, "Upgrade the database schema: openfatture init")
    elif database_schema == "ahead":
        readiness["next_steps"].insert(
            0, "The database is newer than this release: upgrade OpenFatture"
        )
    configuration = _configuration()
    if configuration["plaintext_secrets"]:
        readiness["next_steps"].insert(
            0, "Move plaintext secrets to the keychain: openfatture config migrate"
        )
    if configuration["ignored_dotenv"]:
        readiness["next_steps"].insert(
            0,
            "./.env is not read: use `uv run --env-file .env ...` "
            "or import it with `openfatture config migrate --env-file .env`",
        )
    # Backend ids SSOT: platform.assistant_backends (no AI package import).
    from openfatture.platform.assistant_backends import (
        DEFAULT_ASSISTANT_BACKEND,
        resolve_backend_id,
    )

    assistant_backend = str(
        getattr(settings, "assistant_backend", DEFAULT_ASSISTANT_BACKEND)
        or DEFAULT_ASSISTANT_BACKEND
    )
    try:
        assistant_backend_id = resolve_backend_id(assistant_backend)
    except ValueError:
        assistant_backend_id = resolve_backend_id(DEFAULT_ASSISTANT_BACKEND)

    return {
        "version": __version__,
        "database": str(settings.database_url),
        "database_schema": database_schema,
        "data_dir": str(settings.data_dir),
        "archive_dir": str(settings.archivio_dir),
        "ai_provider": settings.ai_provider,
        "ai_model": settings.ai_model,
        "ai_api_key_configured": bool(settings.ai_api_key),
        "assistant_backend": assistant_backend,
        "assistant_backend_id": assistant_backend_id,
        "readiness": readiness,
        "configuration": configuration,
        "extras": extras,
        "extensions": {
            # Supported extension mechanism: user hook scripts (see docs/CORE_VS_EXTENSIONS.md)
            "hooks_dir": str(hooks_dir),
            "hooks_present": hooks_dir.is_dir(),
            "hooks_scripts": hook_scripts,
            # In-process plugins are not a product API (package removed / unsupported)
            "in_process_plugins": "unsupported",
        },
        "feature_flags": {
            "assistant_available": bool(extras.get("ai")),
            "assistant_backend": assistant_backend,
            "rag_auto_update_default": False,  # OPENFATTURE_RAG_AUTO_UPDATE_ENABLED default
        },
        "limitations": {
            "rag_auto_update": (
                "requires reindex_callback (AutoIndexingService); no silent simulation"
            ),
        },
    }


@app.command()
def status(json_output: bool = typer.Option(False, "--json", help="Emit status as JSON.")) -> None:
    """Show local configuration and storage readiness without changing state."""
    data = _build_status()
    remember_result(data)
    if json_output:
        # Pure stdout for machine consumers; diagnostics use stderr via logging.
        print(json.dumps(data, indent=2, default=str))
        return

    from openfatture.i18n import _

    locale = get_settings().locale
    ready = data["readiness"]
    console.print(
        _(
            "cli-status-readiness",
            locale=locale,
            core="yes" if ready["core_ready"] else "no",
            assistant="yes" if ready["assistant_ready"] else "no",
        )
        + "\n"
    )

    table = Table(title=_("cli-status-title", locale=locale))
    table.add_column(_("cli-config-column-setting", locale=locale), style="cyan")
    table.add_column(_("cli-config-column-value", locale=locale))
    for key, label in (
        ("version", "cli-config-label-app-version"),
        ("database", "cli-config-label-database-url"),
        ("data_dir", "cli-config-label-data-dir"),
        ("archive_dir", "cli-config-label-archive-dir"),
        ("ai_provider", "cli-config-label-ai-provider"),
        ("ai_model", "cli-config-label-ai-model"),
        ("ai_api_key_configured", "cli-status-label-ai-api-key-configured"),
        ("assistant_backend", "cli-status-label-assistant-backend"),
        ("assistant_backend_id", "cli-status-label-assistant-backend-id"),
    ):
        table.add_row(_(label, locale=locale), str(data[key]))
    configuration = data["configuration"]
    table.add_row(_("cli-status-label-config-file", locale=locale), configuration["config_file"])
    table.add_row(
        _("cli-status-label-secret-backend", locale=locale), configuration["secret_backend"]
    )
    console.print(table)

    yes, no = _("cli-status-yes", locale=locale), _("cli-status-no", locale=locale)
    checks = Table(title=_("cli-status-checks-title", locale=locale))
    checks.add_column(_("cli-status-column-check", locale=locale), style="cyan")
    checks.add_column("OK")
    for name, ok in ready["checks"].items():
        checks.add_row(name.replace("_", " "), yes if ok else no)
    console.print(checks)

    if ready["missing_fields"] or ready["invalid_fields"]:
        fields = Table(title=_("status-blocking-fields", locale=locale))
        fields.add_column(_("status-field", locale=locale))
        fields.add_column(_("status-problem", locale=locale))
        for field in ready["missing_fields"]:
            fields.add_row(field, _("status-missing", locale=locale))
        for field in ready["invalid_fields"]:
            fields.add_row(field, _("status-invalid", locale=locale))
        console.print(fields)
    console.print(_("status-local-only", locale=locale), markup=False)

    if ready["next_steps"]:
        console.print("\n" + _("cli-status-next-steps", locale=locale))
        for step in ready["next_steps"]:
            console.print(f"  • {step}")
        console.print()

    extras_table = Table(title=_("cli-status-extras-title", locale=locale))
    extras_table.add_column(_("cli-status-column-extra", locale=locale), style="cyan")
    extras_table.add_column(_("cli-status-column-installed", locale=locale))
    for name, installed in sorted(data["extras"].items()):
        extras_table.add_row(name, yes if installed else no)
    console.print(extras_table)

    ext = data["extensions"]
    ext_table = Table(title=_("cli-status-extensions-title", locale=locale))
    ext_table.add_column(_("cli-status-column-mechanism", locale=locale), style="cyan")
    ext_table.add_column(_("cli-status-column-detail", locale=locale))
    ext_table.add_row(
        _("cli-status-hooks", locale=locale),
        _(
            "cli-status-hooks-detail",
            locale=locale,
            path=str(ext["hooks_dir"]),
            count=len(ext["hooks_scripts"]),
        ),
    )
    ext_table.add_row(_("cli-status-plugins", locale=locale), str(ext["in_process_plugins"]))
    console.print(ext_table)
