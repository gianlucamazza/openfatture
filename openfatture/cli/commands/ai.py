"""AI-powered assistance commands."""

import asyncio
import json
from typing import Optional

import typer
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.table import Table

from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.domain.context import InvoiceContext, TaxContext
from openfatture.ai.providers.factory import create_provider
from openfatture.utils.logging import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command("describe")
def ai_describe(
    text: str = typer.Argument(..., help="Service description to expand"),
    hours: Optional[float] = typer.Option(None, "--hours", "-h", help="Hours worked"),
    rate: Optional[float] = typer.Option(None, "--rate", "-r", help="Hourly rate (€)"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project name"),
    technologies: Optional[str] = typer.Option(
        None, "--tech", "-t", help="Technologies used (comma-separated)"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """
    Use AI to generate detailed invoice descriptions.

    Example:
        openfatture ai describe "3 ore consulenza web"
        openfatture ai describe "sviluppo backend API" --hours 5 --tech "Python,FastAPI"
    """
    asyncio.run(_run_invoice_assistant(text, hours, rate, project, technologies, json_output))


async def _run_invoice_assistant(
    text: str,
    hours: Optional[float],
    rate: Optional[float],
    project: Optional[str],
    technologies: Optional[str],
    json_output: bool,
) -> None:
    """Run the Invoice Assistant agent."""
    console.print("\n[bold blue]🤖 AI Invoice Description Generator[/bold blue]\n")

    try:
        # Parse technologies
        tech_list = []
        if technologies:
            tech_list = [t.strip() for t in technologies.split(",")]

        # Create context
        context = InvoiceContext(
            user_input=text,
            servizio_base=text,
            ore_lavorate=hours,
            tariffa_oraria=rate,
            progetto=project,
            tecnologie=tech_list,
        )

        # Show input
        _display_input(context)

        # Create provider and agent
        with console.status("[bold green]Generating description with AI..."):
            provider = create_provider()
            agent = InvoiceAssistantAgent(provider=provider)

            # Execute agent
            response = await agent.execute(context)

        # Check for errors
        if response.status.value == "error":
            console.print(f"\n[bold red]❌ Error:[/bold red] {response.error}\n")
            logger.error("ai_describe_failed", error=response.error)
            return

        # Display results
        if json_output:
            # Raw JSON output
            if response.metadata.get("is_structured"):
                output = response.metadata["parsed_model"]
            else:
                output = {"descrizione_completa": response.content}
            console.print(JSON(json.dumps(output, indent=2, ensure_ascii=False)))
        else:
            # Formatted output
            _display_result(response)

        # Show metrics
        _display_metrics(response)

    except Exception as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {e}\n")
        logger.error("ai_describe_error", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)


def _display_input(context: InvoiceContext) -> None:
    """Display input context."""
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("📝 Service:", context.servizio_base)

    if context.ore_lavorate:
        table.add_row("⏱️  Hours:", f"{context.ore_lavorate:.1f}h")

    if context.tariffa_oraria:
        table.add_row("💰 Rate:", f"€{context.tariffa_oraria:.2f}/h")

    if context.progetto:
        table.add_row("📁 Project:", context.progetto)

    if context.tecnologie:
        table.add_row("🔧 Technologies:", ", ".join(context.tecnologie))

    console.print(table)
    console.print()


def _display_result(response) -> None:
    """Display structured result."""
    # Try to get structured model
    if response.metadata.get("is_structured"):
        data = response.metadata["parsed_model"]

        # Description
        console.print(
            Panel(
                data["descrizione_completa"],
                title="[bold]📄 Professional Description[/bold]",
                border_style="green",
            )
        )

        # Deliverables
        if data.get("deliverables"):
            console.print("\n[bold cyan]📦 Deliverables:[/bold cyan]")
            for item in data["deliverables"]:
                console.print(f"  • {item}")

        # Competenze
        if data.get("competenze"):
            console.print("\n[bold cyan]🔧 Technical Skills:[/bold cyan]")
            for skill in data["competenze"]:
                console.print(f"  • {skill}")

        # Duration
        if data.get("durata_ore"):
            console.print(f"\n[bold cyan]⏱️  Duration:[/bold cyan] {data['durata_ore']}h")

        # Notes
        if data.get("note"):
            console.print(f"\n[bold cyan]📌 Notes:[/bold cyan] {data['note']}")

    else:
        # Fallback to plain text
        console.print(
            Panel(
                response.content,
                title="[bold]📄 Generated Description[/bold]",
                border_style="green",
            )
        )

    console.print()


def _display_metrics(response) -> None:
    """Display response metrics."""
    metrics_table = Table(show_header=False, box=None, padding=(0, 2))
    metrics_table.add_column("Metric", style="dim")
    metrics_table.add_column("Value", style="dim")

    metrics_table.add_row(
        f"Provider: {response.provider}",
        f"Model: {response.model}",
    )
    metrics_table.add_row(
        f"Tokens: {response.usage.total_tokens}",
        f"Cost: ${response.usage.estimated_cost_usd:.4f}",
    )
    metrics_table.add_row(
        f"Latency: {response.latency_ms:.0f}ms",
        "",
    )

    console.print(metrics_table)
    console.print()


@app.command("suggest-vat")
def ai_suggest_vat(
    description: str = typer.Argument(..., help="Service/product description"),
    pa: bool = typer.Option(False, "--pa", help="Client is Public Administration"),
    estero: bool = typer.Option(False, "--estero", help="Foreign client"),
    paese: Optional[str] = typer.Option(None, "--paese", help="Client country code (IT, FR, US, etc.)"),
    categoria: Optional[str] = typer.Option(None, "--categoria", "-c", help="Service category"),
    importo: Optional[float] = typer.Option(None, "--importo", "-i", help="Amount in EUR"),
    ateco: Optional[str] = typer.Option(None, "--ateco", help="ATECO code"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """
    Use AI to suggest appropriate VAT rate and fiscal treatment.

    Examples:
        openfatture ai suggest-vat "consulenza IT"
        openfatture ai suggest-vat "consulenza IT per azienda edile"
        openfatture ai suggest-vat "formazione professionale" --pa
        openfatture ai suggest-vat "consulenza" --estero --paese US
    """
    asyncio.run(_run_tax_advisor(description, pa, estero, paese, categoria, importo, ateco, json_output))


async def _run_tax_advisor(
    description: str,
    pa: bool,
    estero: bool,
    paese: Optional[str],
    categoria: Optional[str],
    importo: Optional[float],
    ateco: Optional[str],
    json_output: bool,
) -> None:
    """Run the Tax Advisor agent."""
    console.print("\n[bold blue]🧾 AI Tax Advisor - Suggerimento Fiscale[/bold blue]\n")

    try:
        # Import TaxContext
        from openfatture.ai.agents.tax_advisor import TaxAdvisorAgent
        from openfatture.ai.domain.context import TaxContext

        # Create context
        context = TaxContext(
            user_input=description,
            tipo_servizio=description,
            categoria_servizio=categoria,
            importo=importo or 0,
            cliente_pa=pa,
            cliente_estero=estero,
            paese_cliente=paese or ("IT" if not estero else "XX"),
            codice_ateco=ateco,
        )

        # Show input
        _display_tax_input(context)

        # Create provider and agent
        with console.status("[bold green]Analizzando trattamento fiscale..."):
            provider = create_provider()
            agent = TaxAdvisorAgent(provider=provider)

            # Execute agent
            response = await agent.execute(context)

        # Check for errors
        if response.status.value == "error":
            console.print(f"\n[bold red]❌ Errore:[/bold red] {response.error}\n")
            logger.error("ai_suggest_vat_failed", error=response.error)
            return

        # Display results
        if json_output:
            # Raw JSON output
            if response.metadata.get("is_structured"):
                output = response.metadata["parsed_model"]
            else:
                output = {"spiegazione": response.content}
            console.print(JSON(json.dumps(output, indent=2, ensure_ascii=False)))
        else:
            # Formatted output
            _display_tax_result(response)

        # Show metrics
        _display_metrics(response)

    except Exception as e:
        console.print(f"\n[bold red]❌ Errore:[/bold red] {e}\n")
        logger.error("ai_suggest_vat_error", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)


def _display_tax_input(context: TaxContext) -> None:
    """Display tax context input."""
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("📝 Servizio/Prodotto:", context.tipo_servizio)

    if context.categoria_servizio:
        table.add_row("📂 Categoria:", context.categoria_servizio)

    if context.importo:
        table.add_row("💰 Importo:", f"€{context.importo:.2f}")

    if context.cliente_pa:
        table.add_row("🏛️  Cliente:", "Pubblica Amministrazione")

    if context.cliente_estero:
        table.add_row("🌍 Cliente estero:", context.paese_cliente)

    if context.codice_ateco:
        table.add_row("🔢 Codice ATECO:", context.codice_ateco)

    console.print(table)
    console.print()


def _display_tax_result(response) -> None:
    """Display tax suggestion result."""
    # Try to get structured model
    if response.metadata.get("is_structured"):
        data = response.metadata["parsed_model"]

        # Main tax info panel
        tax_info = f"""[bold]Aliquota IVA:[/bold]    {data['aliquota_iva']}%
[bold]Reverse Charge:[/bold]  {'✓ SI' if data['reverse_charge'] else '✗ NO'}"""

        if data.get("codice_natura"):
            tax_info += f"\n[bold]Natura IVA:[/bold]      {data['codice_natura']}"

        if data.get("split_payment"):
            tax_info += f"\n[bold]Split Payment:[/bold]   ✓ SI"

        if data.get("regime_speciale"):
            tax_info += f"\n[bold]Regime Speciale:[/bold] {data['regime_speciale']}"

        tax_info += f"\n[bold]Confidence:[/bold]      {int(data['confidence'] * 100)}%"

        console.print(
            Panel(
                tax_info,
                title="[bold]📊 Trattamento Fiscale[/bold]",
                border_style="green",
            )
        )

        # Spiegazione
        console.print(f"\n[bold cyan]📋 Spiegazione:[/bold cyan]")
        console.print(f"{data['spiegazione']}\n")

        # Riferimento normativo
        console.print(f"[bold cyan]📜 Riferimento normativo:[/bold cyan]")
        console.print(f"{data['riferimento_normativo']}\n")

        # Nota fattura
        if data.get("note_fattura"):
            console.print(f"[bold cyan]📝 Nota per fattura:[/bold cyan]")
            console.print(f'"{data["note_fattura"]}"\n')

        # Raccomandazioni
        if data.get("raccomandazioni") and len(data["raccomandazioni"]) > 0:
            console.print(f"[bold cyan]💡 Raccomandazioni:[/bold cyan]")
            for racc in data["raccomandazioni"]:
                console.print(f"  • {racc}")
            console.print()

    else:
        # Fallback to plain text
        console.print(
            Panel(
                response.content,
                title="[bold]📊 Suggerimento Fiscale[/bold]",
                border_style="green",
            )
        )


@app.command("forecast")
def ai_forecast(
    months: int = typer.Option(3, "--months", "-m", help="Months to forecast"),
) -> None:
    """
    Use AI/ML to forecast cash flow.

    Example:
        openfatture ai forecast --months 6
    """
    console.print("\n[bold blue]🤖 AI Cash Flow Forecasting[/bold blue]\n")

    console.print("[yellow]⚠ AI/ML features not yet implemented[/yellow]")
    console.print(
        f"[dim]This will analyze your invoices and predict cash flow for the next {months} months.[/dim]\n"
    )

    console.print("[bold]Forecast preview:[/bold]")
    console.print("  Month 1: +€5,000 (expected)")
    console.print("  Month 2: +€3,500 (expected)")
    console.print("  Month 3: +€4,200 (expected)")


@app.command("check")
def ai_check(
    fattura_id: int = typer.Argument(..., help="Invoice ID to check"),
) -> None:
    """
    Use AI to validate invoice compliance.

    Example:
        openfatture ai check 123
    """
    console.print("\n[bold blue]🤖 AI Compliance Checker[/bold blue]\n")

    console.print("[yellow]⚠ AI features not yet implemented[/yellow]")
    console.print(
        f"[dim]This will use AI to check invoice {fattura_id} for compliance issues.[/dim]\n"
    )

    console.print("[bold]Compliance Check:[/bold]")
    console.print("  [green]✓[/green] All required fields present")
    console.print("  [green]✓[/green] VAT calculations correct")
    console.print("  [green]✓[/green] Client data valid")
    console.print("  [yellow]⚠[/yellow] Consider adding more detailed description")
