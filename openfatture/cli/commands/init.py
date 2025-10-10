"""Initialize OpenFatture."""

from pathlib import Path

import questionary
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from openfatture.storage.database.base import init_db
from openfatture.utils.config import get_settings
from openfatture.utils.validators import validate_codice_fiscale, validate_partita_iva

app = typer.Typer()
console = Console()


@app.command()
def init(
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
    """
    console.print("\n[bold blue]🚀 OpenFatture Setup[/bold blue]\n")

    settings = get_settings()

    # Create directories
    console.print("[cyan]Creating directories...[/cyan]")
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.archivio_dir.mkdir(parents=True, exist_ok=True)
    settings.certificates_dir.mkdir(parents=True, exist_ok=True)
    console.print("  ✓ Data directories created\n")

    # Initialize database
    console.print("[cyan]Initializing database...[/cyan]")
    init_db(str(settings.database_url))
    console.print(f"  ✓ Database initialized at: {settings.database_url}\n")

    # Interactive configuration
    if interactive:
        console.print("[bold yellow]📝 Let's configure your company data[/bold yellow]\n")

        env_file = Path(".env")
        env_content = []

        if env_file.exists():
            if not Confirm.ask(
                "[yellow]A .env file already exists. Overwrite?[/yellow]",
                default=False,
            ):
                console.print("\n[green]Setup complete! Existing .env preserved.[/green]")
                return
        else:
            # Copy example if starting fresh
            example = Path(".env.example")
            if example.exists():
                env_content = example.read_text().splitlines()

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
        console.print("\n[bold]🤖 AI Configuration (Optional)[/bold]")
        console.print(
            "[dim]Configure AI features for smart invoice descriptions, tax suggestions, and chat assistant.[/dim]"
        )

        configure_ai = Confirm.ask(
            "Configure AI features now? (You can do this later via config wizard)",
            default=False,
        )

        ai_lines = []
        if configure_ai:
            ai_provider = questionary.select(
                "AI Provider",
                choices=["anthropic", "openai", "ollama", "Skip for now"],
                default="anthropic",
            ).ask()

            if ai_provider != "Skip for now":
                # Add to env_lines based on provider
                if ai_provider == "anthropic":
                    ai_model = "claude-3-5-sonnet-20241022"
                    console.print("\n[cyan]Anthropic Claude selected - get API key from:[/cyan]")
                    console.print("  https://console.anthropic.com/settings/keys")
                    ai_key = Prompt.ask(
                        "API Key (or leave empty to set later)", default="", password=True
                    )

                elif ai_provider == "openai":
                    ai_model = "gpt-4o"
                    console.print("\n[cyan]OpenAI selected - get API key from:[/cyan]")
                    console.print("  https://platform.openai.com/api-keys")
                    ai_key = Prompt.ask(
                        "API Key (or leave empty to set later)", default="", password=True
                    )

                else:  # ollama
                    ai_model = "llama3.2"
                    ai_key = ""
                    console.print("\n[cyan]Ollama selected - FREE local model![/cyan]")
                    console.print("  Install: [bold]ollama pull llama3.2[/bold]")
                    console.print("  Start: [bold]ollama serve[/bold]")

                # Add AI config
                ai_lines = [
                    "",
                    "# AI Configuration",
                    f"AI_PROVIDER={ai_provider}",
                    f"AI_MODEL={ai_model}",
                ]

                if ai_key:
                    ai_lines.append(f"AI_API_KEY={ai_key}")
                else:
                    ai_lines.append("# AI_API_KEY=your-key-here  # Add your key later")

                if ai_provider == "ollama":
                    ai_lines.append("AI_BASE_URL=http://localhost:11434")

                # Add chat defaults
                ai_lines.extend(
                    [
                        "",
                        "# AI Chat Assistant",
                        "AI_CHAT_ENABLED=true",
                        "AI_CHAT_AUTO_SAVE=true",
                        "AI_CHAT_MAX_MESSAGES=100",
                        "AI_CHAT_MAX_TOKENS=8000",
                        "",
                        "# AI Tools",
                        "AI_TOOLS_ENABLED=true",
                        "AI_ENABLED_TOOLS=search_invoices,get_invoice_details,get_invoice_stats,search_clients,get_client_details,get_client_stats",
                        "AI_TOOLS_REQUIRE_CONFIRMATION=true",
                    ]
                )
            else:
                # User chose "Skip for now"
                ai_lines = [
                    "",
                    "# AI Configuration (optional - uncomment and configure to enable)",
                    "# AI_PROVIDER=anthropic",
                    "# AI_MODEL=claude-3-5-sonnet-20241022",
                    "# AI_API_KEY=sk-ant-your-key-here",
                    "# See docs for full configuration: docs/CONFIGURATION.md",
                ]
        else:
            # User chose not to configure AI now
            ai_lines = [
                "",
                "# AI Configuration (optional - uncomment and configure to enable)",
                "# AI_PROVIDER=anthropic",
                "# AI_MODEL=claude-3-5-sonnet-20241022",
                "# AI_API_KEY=sk-ant-your-key-here",
                "# See docs for full configuration: docs/CONFIGURATION.md",
            ]

        # Write .env file
        env_lines = [
            "# OpenFatture Configuration",
            "# Generated by setup wizard",
            "",
            "# Database",
            f'DATABASE_URL="{settings.database_url}"',
            "",
            "# Company Data",
            f'CEDENTE_DENOMINAZIONE="{denominazione}"',
            f"CEDENTE_PARTITA_IVA={partita_iva}",
            f"CEDENTE_CODICE_FISCALE={codice_fiscale}",
            "CEDENTE_REGIME_FISCALE=RF19",
            f'CEDENTE_INDIRIZZO="{indirizzo}"',
            f"CEDENTE_CAP={cap}",
            f'CEDENTE_COMUNE="{comune}"',
            f"CEDENTE_PROVINCIA={provincia}",
            "CEDENTE_NAZIONE=IT",
            "",
            "# PEC Configuration",
            f"PEC_SMTP_SERVER={pec_smtp}",
            "PEC_SMTP_PORT=465",
            f"PEC_ADDRESS={pec_address}",
            f'PEC_PASSWORD="{pec_password}"',
            "SDI_PEC_ADDRESS=sdi01@pec.fatturapa.it",
            "",
            "# Email Templates & Notifications",
            f"NOTIFICATION_EMAIL={notification_email}",
            "NOTIFICATION_ENABLED=true",
            f"LOCALE={locale}",
            "# Optional branding (uncomment to customize):",
            "# EMAIL_LOGO_URL=https://yourcompany.com/logo.png",
            "# EMAIL_PRIMARY_COLOR=#1976D2",
            "# EMAIL_FOOTER_TEXT=© 2025 Your Company",
        ]

        # Add AI lines
        env_lines.extend(ai_lines)

        env_file.write_text("\n".join(env_lines))
        console.print(f"\n  ✓ Configuration saved to: {env_file.absolute()}\n")

    # Success message
    panel = Panel(
        "[bold green]✓ OpenFatture is ready to use![/bold green]\n\n"
        "Next steps:\n"
        "  • Add a client: [cyan]openfatture cliente add[/cyan]\n"
        "  • Create an invoice: [cyan]openfatture fattura crea[/cyan]\n"
        "  • View help: [cyan]openfatture --help[/cyan]",
        title="🎉 Setup Complete",
        border_style="green",
    )
    console.print(panel)
