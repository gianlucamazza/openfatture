"""Initialize OpenFatture."""

from collections.abc import Callable

import questionary
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from openfatture.i18n import _
from openfatture.platform.config import Settings, get_settings
from openfatture.platform.validators import (
    validate_codice_fiscale,
    validate_partita_iva,
    validate_regime_fiscale,
)
from openfatture.storage.database.base import init_db

app = typer.Typer()
console = Console()


_AI_PROVIDERS = ("anthropic", "openai", "ollama")
_AI_KEY_PAGES = {
    "anthropic": ("Anthropic Claude", "https://console.anthropic.com/settings/keys"),
    "openai": ("OpenAI", "https://platform.openai.com/api-keys"),
}


@app.command()
def init(
    ctx: typer.Context,
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        "-i/-n",
        help="Configurazione guidata interattiva",
    ),
) -> None:
    """
    Initialize OpenFatture with database and configuration.

    This command sets up:
    - Database structure
    - Configuration directories
    - Initial settings (in interactive mode)

    Examples:
        openfatture init                    # Interactive setup wizard
        openfatture init --no-interactive   # Automated setup with defaults
    """
    console.print("\n" + _("cli-init-title") + "\n")

    if interactive and _structured_output(ctx):
        raise typer.BadParameter(_("cli-init-structured-needs-no-interactive"))
    settings = get_settings()
    _create_directories(settings)
    _upgrade_schema(settings)
    if interactive:
        _run_wizard(settings)
    _print_setup_complete()


def _structured_output(ctx: typer.Context | None) -> bool:
    """Whether the root command asked for a non-rich output format."""
    if ctx is None:
        return False
    obj = ctx.find_root().obj
    return bool(obj) and obj.get("format", "rich") != "rich"


def _create_directories(settings: Settings) -> None:
    console.print(_("cli-init-creating-dirs"))
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.archivio_dir.mkdir(parents=True, exist_ok=True)
    settings.certificates_dir.mkdir(parents=True, exist_ok=True)
    console.print(" " + _("cli-init-dirs-created") + "\n")


def _upgrade_schema(settings: Settings) -> None:
    """Initialize or upgrade the database schema (Alembic head)."""
    console.print(_("cli-init-initializing-db"))
    from openfatture.storage.schema import SchemaError, upgrade_database

    try:
        previous, backup = upgrade_database(str(settings.database_url))
    except SchemaError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    init_db(str(settings.database_url))
    if backup is not None:
        console.print(" " + _("cli-init-backup", path=str(backup)))
    console.print(
        " " + _("cli-init-database", state=previous, url=str(settings.database_url)) + "\n"
    )


def _run_wizard(settings: Settings) -> None:
    """Collect the profile interactively and save it; never silently overwrite."""
    console.print(_("cli-init-configure-company") + "\n")

    from openfatture.platform.secrets import config_file_path

    config_path = config_file_path()
    if config_path.exists() and not Confirm.ask(_("cli-init-overwrite-confirm"), default=False):
        console.print("\n" + _("cli-init-config-preserved") + "\n")
        return

    values: dict[str, object] = {"database_url": str(settings.database_url)}
    values.update(_ask_company(settings))
    pec_values, pec_password = _ask_pec()
    values.update(pec_values)
    values.update(_ask_preferences(str(pec_values["pec_address"])))
    ai_values, ai_key = _ask_ai()
    values.update(ai_values)
    _save_profile(values, {"pec_password": pec_password, "ai_api_key": ai_key}, str(config_path))


def _ask_valid(label: str, invalid: str, is_valid: Callable[[str], bool]) -> str:
    """Prompt until ``is_valid`` accepts the answer."""
    while True:
        answer = Prompt.ask(_(label), default="")
        if is_valid(answer):
            return answer
        console.print(_(invalid))


def _ask_regime(default: str) -> str:
    regime_fiscale = ""
    while not validate_regime_fiscale(regime_fiscale):
        regime_fiscale = Prompt.ask(_("cli-init-prompt-regime"), default=default).upper()
        if not validate_regime_fiscale(regime_fiscale):
            console.print(_("cli-init-invalid-regime"))
    return regime_fiscale


def _ask_company(settings: Settings) -> dict[str, object]:
    console.print("\n" + _("cli-init-company-section"))
    denominazione = Prompt.ask(_("cli-init-prompt-name"), default="")
    partita_iva = _ask_valid(
        "cli-init-prompt-partita-iva", "cli-init-invalid-partita-iva", validate_partita_iva
    )
    codice_fiscale = _ask_valid(
        "cli-init-prompt-codice-fiscale", "cli-init-invalid-codice-fiscale", validate_codice_fiscale
    ).upper()
    regime_fiscale = _ask_regime(settings.cedente_regime_fiscale or "")
    return {
        "cedente_denominazione": denominazione,
        "cedente_partita_iva": partita_iva,
        "cedente_codice_fiscale": codice_fiscale,
        "cedente_regime_fiscale": regime_fiscale,
        "cedente_indirizzo": Prompt.ask(_("cli-init-prompt-address"), default=""),
        "cedente_cap": Prompt.ask(_("cli-init-prompt-cap"), default=""),
        "cedente_comune": Prompt.ask(_("cli-init-prompt-city"), default=""),
        "cedente_provincia": Prompt.ask(_("cli-init-prompt-province"), default="").upper(),
        "cedente_nazione": "IT",
    }


def _ask_pec() -> tuple[dict[str, object], str]:
    """Return the PEC settings and the PEC password (a secret, kept apart)."""
    console.print("\n" + _("cli-init-pec-section"))
    pec_address = Prompt.ask(_("cli-init-prompt-pec-address"), default="")
    pec_password = Prompt.ask(_("cli-init-prompt-pec-password"), password=True, default="")
    pec_smtp = Prompt.ask(_("cli-init-prompt-pec-smtp"), default="smtp.pec.aruba.it")
    values: dict[str, object] = {
        "pec_smtp_server": pec_smtp,
        "pec_smtp_port": 465,
        "pec_address": pec_address,
        "sdi_pec_address": "sdi01@pec.fatturapa.it",
    }
    return values, pec_password


def _ask_preferences(pec_address: str) -> dict[str, object]:
    console.print("\n" + _("cli-init-notifications-section"))
    notification_email = Prompt.ask(
        _("cli-init-prompt-notification-email"),
        default=pec_address,  # Default to PEC if not specified
    )
    locale = Prompt.ask(_("cli-init-prompt-locale"), default="it")
    return {
        "notification_email": notification_email,
        "notification_enabled": True,
        "locale": locale,
    }


def _ask_ai() -> tuple[dict[str, object], str]:
    """Optionally configure an AI provider; return its settings and API key."""
    console.print("\n" + _("cli-init-ai-section"))
    console.print(_("cli-init-ai-description"))
    configure_ai = Confirm.ask(_("cli-init-ai-confirm"), default=False)

    from openfatture.ai.config.settings import AISettings

    default_models = {
        provider: str(AISettings.model_fields[f"{provider}_model"].default)
        for provider in _AI_PROVIDERS
    }
    if not configure_ai:
        return {}, ""
    ai_provider = questionary.select(
        _("cli-init-ai-provider"),
        choices=[*_AI_PROVIDERS, _("cli-init-ai-skip")],
        default="anthropic",
    ).ask()
    if ai_provider not in default_models:
        return {}, ""
    ai_model = default_models[ai_provider]
    ai_key = _ask_ai_credentials(ai_provider, ai_model)
    ai_values: dict[str, object] = {
        "ai_provider": ai_provider,
        "ai_model": ai_model,
        "ai_chat_enabled": True,
        "ai_chat_auto_save": True,
        "ai_tools_enabled": True,
        "ai_tools_require_confirmation": True,
    }
    if ai_provider == "ollama":
        ai_values["ai_base_url"] = "http://localhost:11434"
    return ai_values, ai_key


def _ask_ai_credentials(provider: str, model: str) -> str:
    """Explain how to reach ``provider`` and ask for its API key when it needs one."""
    if provider == "ollama":
        console.print("\n" + _("cli-init-ollama-selected"))
        console.print("  " + _("cli-init-ollama-install", model=model))
        console.print("  " + _("cli-init-ollama-start"))
        return ""
    name, url = _AI_KEY_PAGES[provider]
    console.print("\n" + _("cli-init-api-key-from", provider=name))
    console.print(f"  {url}")
    return Prompt.ask(_("cli-init-prompt-api-key"), default="", password=True)


def _save_profile(values: dict[str, object], secrets: dict[str, str], config_path: str) -> None:
    from openfatture.cli.config_file import store_secret, update_config

    update_config(values)
    # Secrets never go to config.toml; an empty answer keeps the stored one.
    stored_in = {store_secret(name, secret) for name, secret in secrets.items() if secret}
    console.print("\n " + _("cli-init-config-saved", path=config_path))
    if stored_in:
        backend = "keyring" if stored_in == {"keyring"} else "file"
        console.print(" " + _("cli-init-secrets-saved", backend=backend))
    console.print()


def _print_setup_complete() -> None:
    """Show post-setup guidance without claiming the assistant is ready."""
    panel = Panel(
        _("cli-init-complete-body"),
        title=_("cli-init-complete-title"),
        border_style="green",
    )
    console.print(panel)
