"""Initialize OpenFatture."""

import questionary
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from openfatture.i18n import _
from openfatture.platform.config import get_settings
from openfatture.platform.validators import (
    validate_codice_fiscale,
    validate_partita_iva,
    validate_regime_fiscale,
)
from openfatture.storage.database.base import init_db

app = typer.Typer()
console = Console()


@app.command()
def init(
    ctx: typer.Context,
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        "-i/-n",
        help="Run interactive setup wizard",
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

    if (
        interactive
        and ctx is not None
        and ctx.find_root().obj
        and ctx.find_root().obj.get("format", "rich") != "rich"
    ):
        raise typer.BadParameter(_("cli-init-structured-needs-no-interactive"))
    settings = get_settings()

    # Create directories
    console.print(_("cli-init-creating-dirs"))
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.archivio_dir.mkdir(parents=True, exist_ok=True)
    settings.certificates_dir.mkdir(parents=True, exist_ok=True)
    console.print(" " + _("cli-init-dirs-created") + "\n")

    # Initialize or upgrade the database schema (Alembic head)
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

    # Interactive configuration
    if interactive:
        console.print(_("cli-init-configure-company") + "\n")

        from openfatture.platform.secrets import config_file_path

        config_path = config_file_path()

        if config_path.exists():
            if not Confirm.ask(
                _("cli-init-overwrite-confirm"),
                default=False,
            ):
                console.print("\n" + _("cli-init-config-preserved") + "\n")
                _print_setup_complete()
                return
        # Never silently overwrite; only write after explicit wizard completion.

        # Gather company data
        console.print("\n" + _("cli-init-company-section"))

        denominazione = Prompt.ask(_("cli-init-prompt-name"), default="")
        partita_iva = ""
        while not partita_iva:
            piva = Prompt.ask(_("cli-init-prompt-partita-iva"), default="")
            if validate_partita_iva(piva):
                partita_iva = piva
            else:
                console.print(_("cli-init-invalid-partita-iva"))

        codice_fiscale = ""
        while not codice_fiscale:
            cf = Prompt.ask(_("cli-init-prompt-codice-fiscale"), default="")
            if validate_codice_fiscale(cf):
                codice_fiscale = cf.upper()
            else:
                console.print(_("cli-init-invalid-codice-fiscale"))

        regime_fiscale = ""
        while not validate_regime_fiscale(regime_fiscale):
            regime_fiscale = Prompt.ask(
                _("cli-init-prompt-regime"),
                default=settings.cedente_regime_fiscale or "",
            ).upper()
            if not validate_regime_fiscale(regime_fiscale):
                console.print(_("cli-init-invalid-regime"))

        indirizzo = Prompt.ask(_("cli-init-prompt-address"), default="")
        cap = Prompt.ask(_("cli-init-prompt-cap"), default="")
        comune = Prompt.ask(_("cli-init-prompt-city"), default="")
        provincia = Prompt.ask(_("cli-init-prompt-province"), default="").upper()

        console.print("\n" + _("cli-init-pec-section"))
        pec_address = Prompt.ask(_("cli-init-prompt-pec-address"), default="")
        pec_password = Prompt.ask(_("cli-init-prompt-pec-password"), password=True, default="")
        pec_smtp = Prompt.ask(_("cli-init-prompt-pec-smtp"), default="smtp.pec.aruba.it")

        console.print("\n" + _("cli-init-notifications-section"))
        notification_email = Prompt.ask(
            _("cli-init-prompt-notification-email"),
            default=pec_address,  # Default to PEC if not specified
        )
        locale = Prompt.ask(_("cli-init-prompt-locale"), default="it")

        # AI Configuration (optional)
        console.print("\n" + _("cli-init-ai-section"))
        console.print(_("cli-init-ai-description"))

        configure_ai = Confirm.ask(
            _("cli-init-ai-confirm"),
            default=False,
        )

        from openfatture.ai.config.settings import AISettings

        default_models = {
            "anthropic": str(AISettings.model_fields["anthropic_model"].default),
            "openai": str(AISettings.model_fields["openai_model"].default),
            "ollama": str(AISettings.model_fields["ollama_model"].default),
        }
        ai_values: dict[str, object] = {}
        ai_key = ""
        if configure_ai:
            ai_provider = questionary.select(
                _("cli-init-ai-provider"),
                choices=["anthropic", "openai", "ollama", _("cli-init-ai-skip")],
                default="anthropic",
            ).ask()

            if ai_provider in default_models:
                ai_model = default_models[ai_provider]
                if ai_provider == "anthropic":
                    console.print("\n" + _("cli-init-api-key-from", provider="Anthropic Claude"))
                    console.print("  https://console.anthropic.com/settings/keys")
                elif ai_provider == "openai":
                    console.print("\n" + _("cli-init-api-key-from", provider="OpenAI"))
                    console.print("  https://platform.openai.com/api-keys")
                if ai_provider == "ollama":
                    console.print("\n" + _("cli-init-ollama-selected"))
                    console.print("  " + _("cli-init-ollama-install", model=ai_model))
                    console.print("  " + _("cli-init-ollama-start"))
                else:
                    ai_key = Prompt.ask(_("cli-init-prompt-api-key"), default="", password=True)
                ai_values = {
                    "ai_provider": ai_provider,
                    "ai_model": ai_model,
                    "ai_chat_enabled": True,
                    "ai_chat_auto_save": True,
                    "ai_tools_enabled": True,
                    "ai_tools_require_confirmation": True,
                    "ai_enabled_tools": (
                        "search_invoices,get_invoice_details,get_invoice_stats,"
                        "search_clients,get_client_details,get_client_stats"
                    ),
                }
                if ai_provider == "ollama":
                    ai_values["ai_base_url"] = "http://localhost:11434"

        from openfatture.cli.config_file import store_secret, update_config

        values: dict[str, object] = {
            "database_url": str(settings.database_url),
            "cedente_denominazione": denominazione,
            "cedente_partita_iva": partita_iva,
            "cedente_codice_fiscale": codice_fiscale,
            "cedente_regime_fiscale": regime_fiscale,
            "cedente_indirizzo": indirizzo,
            "cedente_cap": cap,
            "cedente_comune": comune,
            "cedente_provincia": provincia,
            "cedente_nazione": "IT",
            "pec_smtp_server": pec_smtp,
            "pec_smtp_port": 465,
            "pec_address": pec_address,
            "sdi_pec_address": "sdi01@pec.fatturapa.it",
            "notification_email": notification_email,
            "notification_enabled": True,
            "locale": locale,
            **ai_values,
        }
        update_config(values)
        # Secrets never go to config.toml; an empty answer keeps the stored one.
        stored_in = {
            store_secret(name, secret)
            for name, secret in (("pec_password", pec_password), ("ai_api_key", ai_key))
            if secret
        }
        console.print("\n " + _("cli-init-config-saved", path=str(config_path)))
        if stored_in:
            backend = "keyring" if stored_in == {"keyring"} else "file"
            console.print(" " + _("cli-init-secrets-saved", backend=backend))
        console.print()

    _print_setup_complete()


def _print_setup_complete() -> None:
    """Show post-setup guidance without claiming the assistant is ready."""
    panel = Panel(
        _("cli-init-complete-body"),
        title=_("cli-init-complete-title"),
        border_style="green",
    )
    console.print(panel)
