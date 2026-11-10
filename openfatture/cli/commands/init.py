"""Initialize OpenFatture."""

import questionary
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

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
    console.print("\n[bold blue]OpenFatture Setup[/bold blue]\n")

    if (
        interactive
        and ctx is not None
        and ctx.find_root().obj
        and ctx.find_root().obj.get("format", "rich") != "rich"
    ):
        raise typer.BadParameter("Use --no-interactive with a structured output format")
    settings = get_settings()

    # Create directories
    console.print("[cyan]Creating directories...[/cyan]")
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.archivio_dir.mkdir(parents=True, exist_ok=True)
    settings.certificates_dir.mkdir(parents=True, exist_ok=True)
    console.print(" Data directories created\n")

    # Initialize database
    console.print("[cyan]Initializing database...[/cyan]")
    init_db(str(settings.database_url))
    console.print(f" Database initialized at: {settings.database_url}\n")

    # Interactive configuration
    if interactive:
        console.print("[bold yellow]Let's configure your company data[/bold yellow]\n")

        from openfatture.platform.secrets import config_file_path

        config_path = config_file_path()

        if config_path.exists():
            if not Confirm.ask(
                "[yellow]An OpenFatture profile already exists. Overwrite company/AI settings?[/yellow]",
                default=False,
            ):
                console.print(
                    "\n[green]Existing configuration preserved.[/green] "
                    "Dirs and database were still ensured above.\n"
                )
                _print_setup_complete()
                return
        # Never silently overwrite; only write after explicit wizard completion.

        # Gather company data
        console.print("\n[bold]Company Information (Cedente Prestatore)[/bold]")

        denominazione = Prompt.ask("Company/Your name", default="")
        partita_iva = ""
        while not partita_iva:
            piva = Prompt.ask("Partita IVA (11 digits)", default="")
            if validate_partita_iva(piva):
                partita_iva = piva
            else:
                console.print("[red]Invalid Partita IVA. Please try again.[/red]")

        codice_fiscale = ""
        while not codice_fiscale:
            cf = Prompt.ask("Codice Fiscale (16 characters)", default="")
            if validate_codice_fiscale(cf):
                codice_fiscale = cf.upper()
            else:
                console.print("[red]Invalid Codice Fiscale. Please try again.[/red]")

        regime_fiscale = ""
        while not validate_regime_fiscale(regime_fiscale):
            regime_fiscale = Prompt.ask(
                "Tax regime (use your actual RF code)",
                default=settings.cedente_regime_fiscale or "",
            ).upper()
            if not validate_regime_fiscale(regime_fiscale):
                console.print("[red]Enter a tax regime supported by FatturaPA.[/red]")

        indirizzo = Prompt.ask("Address (Via/Piazza)", default="")
        cap = Prompt.ask("CAP (Postal code)", default="")
        comune = Prompt.ask("City (Comune)", default="")
        provincia = Prompt.ask("Province (2 letters, e.g., RM)", default="").upper()

        console.print("\n[bold]PEC Configuration[/bold]")
        pec_address = Prompt.ask("Your PEC address", default="")
        pec_password = Prompt.ask("PEC password", password=True, default="")
        pec_smtp = Prompt.ask("PEC SMTP server", default="smtp.pec.aruba.it")

        console.print("\n[bold]Email Notifications[/bold]")
        notification_email = Prompt.ask(
            "Email for notifications (SDI alerts, batch summaries)",
            default=pec_address,  # Default to PEC if not specified
        )
        locale = Prompt.ask("Locale (it/en)", default="it")

        # AI Configuration (optional)
        console.print("\n[bold]AI Configuration (Optional)[/bold]")
        console.print(
            "[dim]Configure AI features for smart invoice descriptions, tax suggestions, and chat assistant.[/dim]"
        )

        configure_ai = Confirm.ask(
            "Configure AI features now? (You can do this later via config wizard)",
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
                "AI Provider",
                choices=["anthropic", "openai", "ollama", "Skip for now"],
                default="anthropic",
            ).ask()

            if ai_provider in default_models:
                ai_model = default_models[ai_provider]
                if ai_provider == "anthropic":
                    console.print("\n[cyan]Anthropic Claude selected - get API key from:[/cyan]")
                    console.print("  https://console.anthropic.com/settings/keys")
                elif ai_provider == "openai":
                    console.print("\n[cyan]OpenAI selected - get API key from:[/cyan]")
                    console.print("  https://platform.openai.com/api-keys")
                if ai_provider == "ollama":
                    console.print("\n[cyan]Ollama selected - FREE local model![/cyan]")
                    console.print(f"  Install: [bold]ollama pull {ai_model}[/bold]")
                    console.print("  Start: [bold]ollama serve[/bold]")
                else:
                    ai_key = Prompt.ask(
                        "API Key (or leave empty to set later)", default="", password=True
                    )
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
        console.print(f"\n Configuration saved to: {config_path}")
        if stored_in:
            where = "system keychain" if stored_in == {"keyring"} else "private credentials file"
            console.print(f" Secrets saved to the {where}")
        console.print()

    _print_setup_complete()


def _print_setup_complete() -> None:
    """Show post-setup guidance without claiming the assistant is ready."""
    panel = Panel(
        "[bold green]Setup finished[/bold green]\n\n"
        "Next steps:\n"
        "  • Check readiness: [cyan]openfatture status[/cyan]\n"
        "  • Configure values: [cyan]openfatture config show[/cyan]\n"
        "  • Assistant (needs [cyan]uv sync --extra ai[/cyan]):\n"
        '      [cyan]openfatture assistant "Elenca le fatture aperte"[/cyan]\n'
        "  • Help: [cyan]openfatture --help[/cyan]",
        title="Setup Complete",
        border_style="green",
    )
    console.print(panel)
