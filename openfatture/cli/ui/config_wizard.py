"""Interactive configuration wizard for OpenFatture."""

from pathlib import Path
from typing import cast

import questionary
from rich.console import Console
from rich.prompt import Confirm, Prompt

from openfatture.cli.ui.styles import openfatture_style
from openfatture.utils.config import get_settings
from openfatture.utils.validators import validate_codice_fiscale, validate_partita_iva

console = Console()


def interactive_config_wizard() -> None:
    """
    Interactive wizard to modify OpenFatture configuration.

    Allows users to modify configuration values in .env file with a guided interface.
    """
    console.print("\n[bold blue]✏️  Modifica Configurazione OpenFatture[/bold blue]\n")

    # Check if .env exists
    env_file = Path(".env")
    if not env_file.exists():
        console.print("[red]File .env non trovato![/red]")
        console.print(
            "[yellow]Esegui prima l'inizializzazione: Setup > Inizializza OpenFatture[/yellow]\n"
        )
        return

    # Load current settings
    settings = get_settings()

    while True:
        # Show configuration menu
        choice = show_config_edit_menu()

        if "Torna" in choice or choice is None:
            break

        if "Dati Azienda" in choice:
            edit_company_data(env_file, settings)
        elif "Configurazione PEC" in choice:
            edit_pec_config(env_file, settings)
        elif "Email e Notifiche" in choice:
            edit_email_config(env_file, settings)
        elif "AI" in choice:
            edit_ai_config(env_file, settings)
        elif "Salva ed Esci" in choice:
            console.print("\n[green]✓ Configurazione salvata![/green]")
            break


def show_config_edit_menu() -> str:
    """Show configuration edit menu."""
    choices: list[str | questionary.Choice] = [
        "1. 🏢 Dati Azienda (Cedente Prestatore)",
        "2. 📧 Configurazione PEC",
        "3. 📬 Email e Notifiche",
        "4. 🤖 Configurazione AI",
        questionary.Choice(title="────────────", disabled=" "),
        "5. 💾 Salva ed Esci",
        "0. ← Torna senza salvare",
    ]

    return questionary.select(
        "Cosa vuoi modificare?",
        choices=choices,
        use_shortcuts=True,
        use_arrow_keys=True,
        style=openfatture_style,
        instruction="(Premi 1-5 per selezionare, 0 per tornare, ↑↓ per navigare)",
    ).ask()


def edit_company_data(env_file: Path, settings) -> None:
    """Edit company data configuration."""
    console.print("\n[bold]🏢 Modifica Dati Azienda[/bold]\n")

    # Read current .env
    env_lines = env_file.read_text().splitlines() if env_file.exists() else []
    env_dict = parse_env_file(env_lines)

    # Show current values and ask for changes
    console.print("[dim]Lascia vuoto per mantenere il valore attuale[/dim]\n")

    # Company name
    current_name = env_dict.get("CEDENTE_DENOMINAZIONE", "")
    denominazione = Prompt.ask(
        "Denominazione/Ragione Sociale",
        default=current_name,
    )
    if denominazione:
        env_dict["CEDENTE_DENOMINAZIONE"] = f'"{denominazione}"'

    # Partita IVA
    current_piva = env_dict.get("CEDENTE_PARTITA_IVA", "")
    change_piva = Confirm.ask(
        f"Modificare Partita IVA (attuale: {current_piva})?",
        default=False,
    )
    if change_piva:
        while True:
            piva = Prompt.ask("Partita IVA (11 cifre)", default=current_piva)
            if validate_partita_iva(piva):
                env_dict["CEDENTE_PARTITA_IVA"] = piva
                break
            else:
                console.print("[red]Partita IVA non valida. Riprova.[/red]")

    # Codice Fiscale
    current_cf = env_dict.get("CEDENTE_CODICE_FISCALE", "")
    change_cf = Confirm.ask(
        f"Modificare Codice Fiscale (attuale: {current_cf})?",
        default=False,
    )
    if change_cf:
        while True:
            cf = Prompt.ask("Codice Fiscale (16 caratteri)", default=current_cf)
            if validate_codice_fiscale(cf):
                env_dict["CEDENTE_CODICE_FISCALE"] = cf.upper()
                break
            else:
                console.print("[red]Codice Fiscale non valido. Riprova.[/red]")

    # Address
    current_addr = env_dict.get("CEDENTE_INDIRIZZO", "")
    indirizzo = Prompt.ask("Indirizzo (Via/Piazza)", default=current_addr.strip('"'))
    if indirizzo:
        env_dict["CEDENTE_INDIRIZZO"] = f'"{indirizzo}"'

    # CAP
    current_cap = env_dict.get("CEDENTE_CAP", "")
    cap = Prompt.ask("CAP", default=current_cap)
    if cap:
        env_dict["CEDENTE_CAP"] = cap

    # Comune
    current_comune = env_dict.get("CEDENTE_COMUNE", "")
    comune = Prompt.ask("Comune", default=current_comune.strip('"'))
    if comune:
        env_dict["CEDENTE_COMUNE"] = f'"{comune}"'

    # Provincia
    current_prov = env_dict.get("CEDENTE_PROVINCIA", "")
    provincia = Prompt.ask("Provincia (2 lettere, es. RM)", default=current_prov).upper()
    if provincia:
        env_dict["CEDENTE_PROVINCIA"] = provincia

    # Regime Fiscale
    current_regime = env_dict.get("CEDENTE_REGIME_FISCALE", "RF19")
    regime = Prompt.ask(
        "Regime Fiscale (RF19=Forfettario, RF01=Ordinario)",
        default=current_regime,
    )
    if regime:
        env_dict["CEDENTE_REGIME_FISCALE"] = regime

    # Write back to .env
    write_env_file(env_file, env_dict, env_lines)
    console.print("\n[green]✓ Dati azienda aggiornati[/green]\n")


def edit_pec_config(env_file: Path, settings) -> None:
    """Edit PEC configuration."""
    console.print("\n[bold]📧 Modifica Configurazione PEC[/bold]\n")

    # Read current .env
    env_lines = env_file.read_text().splitlines() if env_file.exists() else []
    env_dict = parse_env_file(env_lines)

    console.print("[dim]Lascia vuoto per mantenere il valore attuale[/dim]\n")

    # PEC Address
    current_pec = env_dict.get("PEC_ADDRESS", "")
    pec_address = Prompt.ask("Indirizzo PEC", default=current_pec)
    if pec_address:
        env_dict["PEC_ADDRESS"] = pec_address

    # PEC Password
    change_pwd = Confirm.ask("Modificare password PEC?", default=False)
    if change_pwd:
        pec_password = Prompt.ask("Password PEC", password=True)
        if pec_password:
            env_dict["PEC_PASSWORD"] = f'"{pec_password}"'

    # SMTP Server
    current_smtp = env_dict.get("PEC_SMTP_SERVER", "smtp.pec.aruba.it")
    smtp_server = Prompt.ask("Server SMTP", default=current_smtp)
    if smtp_server:
        env_dict["PEC_SMTP_SERVER"] = smtp_server

    # SMTP Port
    current_port = env_dict.get("PEC_SMTP_PORT", "465")
    smtp_port = Prompt.ask("Porta SMTP", default=current_port)
    if smtp_port:
        env_dict["PEC_SMTP_PORT"] = smtp_port

    # SDI PEC Address
    current_sdi = env_dict.get("SDI_PEC_ADDRESS", "sdi01@pec.fatturapa.it")
    sdi_pec = Prompt.ask("Indirizzo PEC SDI", default=current_sdi)
    if sdi_pec:
        env_dict["SDI_PEC_ADDRESS"] = sdi_pec

    # Write back to .env
    write_env_file(env_file, env_dict, env_lines)
    console.print("\n[green]✓ Configurazione PEC aggiornata[/green]\n")


def edit_email_config(env_file: Path, settings) -> None:
    """Edit email and notification configuration."""
    console.print("\n[bold]📬 Modifica Email e Notifiche[/bold]\n")

    # Read current .env
    env_lines = env_file.read_text().splitlines() if env_file.exists() else []
    env_dict = parse_env_file(env_lines)

    console.print("[dim]Lascia vuoto per mantenere il valore attuale[/dim]\n")

    # Notification Email
    current_notif = env_dict.get("NOTIFICATION_EMAIL", "")
    notif_email = Prompt.ask("Email per notifiche", default=current_notif)
    if notif_email:
        env_dict["NOTIFICATION_EMAIL"] = notif_email

    # Notifications Enabled
    current_enabled = env_dict.get("NOTIFICATION_ENABLED", "true")
    enabled = Confirm.ask(
        "Abilitare notifiche email?",
        default=current_enabled.lower() == "true",
    )
    env_dict["NOTIFICATION_ENABLED"] = str(enabled).lower()

    # Locale
    current_locale = env_dict.get("LOCALE", "it")
    locale = Prompt.ask("Locale (it/en)", default=current_locale)
    if locale:
        env_dict["LOCALE"] = locale

    # Email Branding (optional)
    console.print("\n[bold]Personalizzazione Email (opzionale)[/bold]")

    customize = Confirm.ask("Personalizzare il branding delle email?", default=False)
    if customize:
        # Logo URL
        current_logo = env_dict.get("EMAIL_LOGO_URL", "")
        logo_url = Prompt.ask("URL Logo (lascia vuoto per default)", default=current_logo)
        if logo_url:
            env_dict["EMAIL_LOGO_URL"] = logo_url

        # Primary Color
        current_color = env_dict.get("EMAIL_PRIMARY_COLOR", "#1976D2")
        primary_color = Prompt.ask("Colore Primario (hex)", default=current_color)
        if primary_color:
            env_dict["EMAIL_PRIMARY_COLOR"] = primary_color

        # Footer Text
        current_footer = env_dict.get("EMAIL_FOOTER_TEXT", "")
        footer_text = Prompt.ask("Testo Footer", default=current_footer.strip('"'))
        if footer_text:
            env_dict["EMAIL_FOOTER_TEXT"] = f'"{footer_text}"'

    # Write back to .env
    write_env_file(env_file, env_dict, env_lines)
    console.print("\n[green]✓ Configurazione email aggiornata[/green]\n")


def edit_ai_config(env_file: Path, settings) -> None:
    """Edit AI configuration."""
    console.print("\n[bold]🤖 Modifica Configurazione AI[/bold]\n")

    # Read current .env
    env_lines = env_file.read_text().splitlines() if env_file.exists() else []
    env_dict = parse_env_file(env_lines)

    console.print("[dim]Lascia vuoto per mantenere il valore attuale[/dim]\n")

    # =========================================================================
    # 1. AI Provider & Model
    # =========================================================================
    console.print("[bold]🔌 Provider & Modello[/bold]\n")

    current_provider = env_dict.get("AI_PROVIDER", "anthropic")
    provider = questionary.select(
        "Provider AI",
        choices=["anthropic", "openai", "ollama"],
        default=(
            current_provider
            if current_provider in ["anthropic", "openai", "ollama"]
            else "anthropic"
        ),
        style=openfatture_style,
    ).ask()
    if provider:
        env_dict["AI_PROVIDER"] = provider

    # AI Model - updated 2025 models
    current_model = env_dict.get("AI_MODEL", "claude-3-5-sonnet-20241022")

    # Suggest models based on provider
    if provider == "anthropic":
        model_choices = [
            "claude-3-5-sonnet-20241022",  # Latest, best quality
            "claude-3-5-haiku-20241022",  # Fast & cheap
            "claude-3-opus-20240229",  # Most powerful
        ]
    elif provider == "openai":
        model_choices = [
            "gpt-4o",  # Latest multimodal
            "gpt-4o-mini",  # Cost-effective
            "gpt-4-turbo",  # Powerful
        ]
    else:  # ollama
        model_choices = [
            "llama3.2",  # Latest Llama
            "llama3.1",  # Stable
            "mistral",  # Good alternative
            "codellama",  # Code-focused
            "Custom...",  # Allow manual input
        ]

    model = questionary.select(
        "Modello AI",
        choices=model_choices,
        default=current_model if current_model in model_choices else model_choices[0],
        style=openfatture_style,
    ).ask()

    if model == "Custom...":
        custom_model = Prompt.ask("Nome modello personalizzato")
        if custom_model:
            env_dict["AI_MODEL"] = custom_model
    elif model:
        env_dict["AI_MODEL"] = model

    # AI Base URL (for Ollama)
    if provider == "ollama":
        current_base_url = env_dict.get("AI_BASE_URL", "http://localhost:11434")
        base_url = Prompt.ask("Ollama Base URL", default=current_base_url)
        if base_url:
            env_dict["AI_BASE_URL"] = base_url
    else:
        # Remove AI_BASE_URL if switching from ollama
        if "AI_BASE_URL" in env_dict:
            del env_dict["AI_BASE_URL"]

    # AI API Key
    if provider in ["anthropic", "openai"]:
        change_key = Confirm.ask("Modificare API Key?", default=False)
        if change_key:
            api_key = Prompt.ask("API Key", password=True)
            if api_key:
                env_dict["AI_API_KEY"] = api_key
    else:
        # Ollama doesn't need API key
        if "AI_API_KEY" in env_dict:
            console.print("[dim]Nota: Ollama non richiede API key (rimossa)[/dim]")
            del env_dict["AI_API_KEY"]

    # Show helpful info based on provider
    if provider == "anthropic":
        console.print(
            "\n[dim]💡 Anthropic API key: https://console.anthropic.com/settings/keys[/dim]"
        )
    elif provider == "openai":
        console.print("\n[dim]💡 OpenAI API key: https://platform.openai.com/api-keys[/dim]")
    else:  # ollama
        console.print("\n[dim]💡 Ollama: gratuito e locale. Avvia con 'ollama serve'[/dim]")
        console.print("[dim]   Installa modelli: 'ollama pull llama3.2'[/dim]")

    # =========================================================================
    # 2. AI Chat Assistant
    # =========================================================================
    console.print("\n[bold]💬 AI Chat Assistant[/bold]\n")

    # Chat enabled
    current_chat_enabled = env_dict.get("AI_CHAT_ENABLED", "true")
    chat_enabled = Confirm.ask(
        "Abilitare AI Chat Assistant?",
        default=current_chat_enabled.lower() == "true",
    )
    env_dict["AI_CHAT_ENABLED"] = str(chat_enabled).lower()

    if chat_enabled:
        # Auto-save
        current_auto_save = env_dict.get("AI_CHAT_AUTO_SAVE", "true")
        auto_save = Confirm.ask(
            "Auto-salvare conversazioni?",
            default=current_auto_save.lower() == "true",
        )
        env_dict["AI_CHAT_AUTO_SAVE"] = str(auto_save).lower()

        # Max messages
        current_max_msg = env_dict.get("AI_CHAT_MAX_MESSAGES", "100")
        max_messages = Prompt.ask(
            "Max messaggi per sessione",
            default=current_max_msg,
        )
        if max_messages:
            env_dict["AI_CHAT_MAX_MESSAGES"] = max_messages

        # Max tokens
        current_max_tokens = env_dict.get("AI_CHAT_MAX_TOKENS", "8000")
        max_tokens = Prompt.ask(
            "Max token per sessione",
            default=current_max_tokens,
        )
        if max_tokens:
            env_dict["AI_CHAT_MAX_TOKENS"] = max_tokens

    # =========================================================================
    # 3. AI Tools & Function Calling
    # =========================================================================
    console.print("\n[bold]🛠️  AI Tools & Function Calling[/bold]\n")

    # Tools enabled
    current_tools_enabled = env_dict.get("AI_TOOLS_ENABLED", "true")
    tools_enabled = Confirm.ask(
        "Abilitare function calling (tools)?",
        default=current_tools_enabled.lower() == "true",
    )
    env_dict["AI_TOOLS_ENABLED"] = str(tools_enabled).lower()

    if tools_enabled:
        # Which tools to enable
        all_tools = [
            "search_invoices",
            "get_invoice_details",
            "get_invoice_stats",
            "search_clients",
            "get_client_details",
            "get_client_stats",
        ]

        current_tools_str = env_dict.get("AI_ENABLED_TOOLS", ",".join(all_tools))
        current_tools = [t.strip() for t in current_tools_str.split(",")]

        selected_tools = questionary.checkbox(
            "Seleziona tools da abilitare:",
            choices=all_tools,
            default=cast("list[str]", [t for t in current_tools if t in all_tools]),  # type: ignore[arg-type]
            style=openfatture_style,
        ).ask()

        if selected_tools:
            env_dict["AI_ENABLED_TOOLS"] = ",".join(selected_tools)

        # Require confirmation
        current_confirm = env_dict.get("AI_TOOLS_REQUIRE_CONFIRMATION", "true")
        require_confirm = Confirm.ask(
            "Richiedere conferma prima di eseguire tools?",
            default=current_confirm.lower() == "true",
        )
        env_dict["AI_TOOLS_REQUIRE_CONFIRMATION"] = str(require_confirm).lower()

    # Write back to .env
    write_env_file(env_file, env_dict, env_lines)
    console.print("\n[green]✓ Configurazione AI aggiornata[/green]\n")


def parse_env_file(lines: list[str]) -> dict[str, str]:
    """
    Parse .env file lines into a dictionary.

    Args:
        lines: List of lines from .env file

    Returns:
        Dictionary of key-value pairs
    """
    env_dict = {}
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env_dict[key.strip()] = value.strip()
    return env_dict


def write_env_file(env_file: Path, env_dict: dict[str, str], original_lines: list[str]) -> None:
    """
    Write updated configuration back to .env file, preserving comments and structure.

    Args:
        env_file: Path to .env file
        env_dict: Updated environment variables dictionary
        original_lines: Original lines from .env file
    """
    new_lines = []
    updated_keys = set()

    # Update existing keys and preserve comments/structure
    for line in original_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in env_dict:
                # Update with new value
                new_lines.append(f"{key}={env_dict[key]}")
                updated_keys.add(key)
            else:
                # Keep original line
                new_lines.append(line)
        else:
            # Keep comments and empty lines
            new_lines.append(line)

    # Add new keys that weren't in the original file
    for key, value in env_dict.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}")

    # Write back to file
    env_file.write_text("\n".join(new_lines) + "\n")
