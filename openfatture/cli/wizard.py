"""Configuration wizard for OpenFatture."""

from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel

from openfatture.utils.config import Settings, dirs

console = Console()


def run_setup_wizard() -> None:
    """Run the first-run setup wizard."""
    console.print(
        Panel.fit(
            "[bold blue]Welcome to OpenFatture![/bold blue]\n\n"
            "It looks like this is your first time running the application.\n"
            "Let's get you set up with some basic configuration.",
            title="🚀 Setup Wizard",
        )
    )

    # Company Information
    console.print("\n[bold]🏢 Company Information[/bold]")
    cedente_denominazione = questionary.text("Company Name / Denominazione:").ask()
    cedente_partita_iva = questionary.text("VAT Number / Partita IVA:").ask()
    cedente_codice_fiscale = questionary.text("Tax Code / Codice Fiscale:").ask()

    cedente_indirizzo = questionary.text("Address / Indirizzo:").ask()
    cedente_cap = questionary.text("ZIP Code / CAP:").ask()
    cedente_comune = questionary.text("City / Comune:").ask()
    cedente_provincia = questionary.text("Province / Provincia (2 chars):").ask()

    # PEC
    console.print("\n[bold]📧 PEC Configuration[/bold]")
    pec_address = questionary.text("Your PEC Address:").ask()
    pec_password = questionary.password("PEC Password:").ask()

    # AI Configuration
    console.print("\n[bold]🤖 AI Configuration[/bold]")
    ai_provider = questionary.select(
        "Select AI Provider:", choices=["openai", "anthropic", "ollama"], default="openai"
    ).ask()

    ai_api_key = None
    if ai_provider != "ollama":
        ai_api_key = questionary.password(f"{ai_provider.capitalize()} API Key:").ask()

    # Confirm and Save
    if questionary.confirm("Save configuration?").ask():
        config_path = dirs.user_config_dir / "config.toml"

        # Create settings object (using defaults for everything else)
        settings = Settings(
            cedente_denominazione=cedente_denominazione,
            cedente_partita_iva=cedente_partita_iva,
            cedente_codice_fiscale=cedente_codice_fiscale,
            cedente_indirizzo=cedente_indirizzo,
            cedente_cap=cedente_cap,
            cedente_comune=cedente_comune,
            cedente_provincia=cedente_provincia,
            pec_address=pec_address,
            pec_password=pec_password,
            ai_provider=ai_provider,
            ai_api_key=ai_api_key,
        )

        # Save to TOML
        save_config(settings, config_path)
        console.print(f"\n[green]Configuration saved to {config_path}![/green]")
        console.print("You can change these settings later using [bold]openfatture config[/bold].")
    else:
        console.print("[red]Setup cancelled.[/red]")
        raise SystemExit(1)


def save_config(settings: Settings, path: Path) -> None:
    """Save settings to a TOML file."""

    import toml  # type: ignore

    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert settings to dict, excluding defaults if possible or just dumping all
    # Pydantic's model_dump is useful here
    data = settings.model_dump(mode="json", exclude_none=True)

    # Filter out internal paths that are dynamically generated
    # (data_dir, archivio_dir, etc. should be left to defaults unless explicitly overridden)
    # For simplicity, we might just save the fields we asked for + explicit overrides.
    # But dumping everything is safer to ensure consistency,
    # EXCEPT for the paths which are dynamic based on platformdirs.

    # Let's clean up the dict for storage
    keys_to_exclude = {
        "data_dir",
        "archivio_dir",
        "certificates_dir",
        "vector_store_path",
        "ai_chat_sessions_dir",
        "plugins_dir",
        "debug_config",
    }

    storage_data = {k: v for k, v in data.items() if k not in keys_to_exclude}

    # Handle nested debug_config separately if needed, or just exclude it for now

    with open(path, "w") as f:
        toml.dump(storage_data, f)
