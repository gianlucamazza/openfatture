"""AI-powered assistance commands."""

import asyncio
import json
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.table import Table

from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.context import enrich_with_rag
from openfatture.ai.domain.context import InvoiceContext, TaxContext
from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.providers.factory import create_provider
from openfatture.ai.rag import KnowledgeIndexer, get_rag_config
from openfatture.utils.logging import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)

rag_app = typer.Typer(help="Gestione knowledge base RAG")


@rag_app.command("status")
def rag_status() -> None:
    """Mostra stato knowledge base e collezione vettoriale."""
    asyncio.run(_rag_status())


@rag_app.command("index")
def rag_index(
    sources: list[str] | None = typer.Option(
        None,
        "--source",
        "-s",
        help="ID sorgente definito nel manifest (opzione ripetibile)",
    )
) -> None:
    """Indicizza le sorgenti della knowledge base."""
    asyncio.run(_rag_index(sources))


@rag_app.command("search")
def rag_search(
    query: str = typer.Argument(..., help="Query semantica da eseguire sulla knowledge base"),
    top: int = typer.Option(5, "--top", "-k", help="Numero massimo di risultati da mostrare"),
    source: str | None = typer.Option(
        None, "--source", "-s", help="Limita la ricerca a una singola sorgente"
    ),
) -> None:
    """Esegue una ricerca semantica nella knowledge base."""
    asyncio.run(_rag_search(query, top, source))


async def _create_knowledge_indexer() -> KnowledgeIndexer:
    """Helper per inizializzare KnowledgeIndexer con configurazione corrente."""
    config = get_rag_config()
    api_key = os.getenv("OPENAI_API_KEY")

    if config.embedding_provider == "openai" and not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY non impostata. Impostare la chiave per generare embedding."
        )

    indexer = await KnowledgeIndexer.create(
        config=config,
        api_key=api_key,
        manifest_path=config.knowledge_manifest_path,
        base_path=Path(".").resolve(),
    )
    return indexer


async def _rag_status() -> None:
    """Mostra stato attuale della knowledge base."""
    try:
        indexer = await _create_knowledge_indexer()
    except Exception as exc:  # pragma: no cover - CLI diagnostics
        console.print(f"[bold red]Errore:[/bold red] {exc}")
        return

    stats = indexer.vector_store.get_stats()

    table = Table(title="Knowledge Base Sources", box=None)
    table.add_column("ID", style="cyan")
    table.add_column("Enabled", style="green")
    table.add_column("Percorso", style="white")
    table.add_column("Tags", style="magenta")

    for source in indexer.sources:
        tags = ", ".join(source.tags or [])
        table.add_row(
            source.id,
            "✅" if source.enabled else "❌",
            str(source.path),
            tags,
        )

    console.print(table)
    console.print()

    console.print(
        Panel.fit(
            f"[bold]Collection:[/bold] {stats['collection_name']}\n"
            f"[bold]Documenti indicizzati:[/bold] {stats['document_count']}\n"
            f"[bold]Persist directory:[/bold] {stats['persist_directory']}",
            title="Vector Store",
            border_style="blue",
        )
    )


async def _rag_index(sources: Iterable[str] | None) -> None:
    """Indicizza le sorgenti specificate (o tutte se None)."""
    try:
        indexer = await _create_knowledge_indexer()
    except Exception as exc:  # pragma: no cover - CLI diagnostics
        console.print(f"[bold red]Errore:[/bold red] {exc}")
        return

    source_ids = list(sources) if sources else None

    with console.status("[bold green]Indicizzazione conoscenza in corso..."):
        chunks = await indexer.index_sources(source_ids=source_ids)

    console.print(
        f"\n[bold green]✅ Indicizzazione completata:[/bold green] {chunks} chunk aggiornati."
    )


async def _rag_search(query: str, top: int, source: str | None) -> None:
    """Esegue ricerca semantica nella knowledge base."""
    try:
        indexer = await _create_knowledge_indexer()
    except Exception as exc:  # pragma: no cover - CLI diagnostics
        console.print(f"[bold red]Errore:[/bold red] {exc}")
        return

    filters: dict[str, Any] = {"type": "knowledge"}
    if source:
        filters["knowledge_source"] = source

    results = await indexer.vector_store.search(
        query=query,
        top_k=top,
        filters=filters,
    )

    if not results:
        console.print("[yellow]Nessun risultato trovato.[/yellow]")
        return

    results_table = Table(title=f'Risultati per "{query}"', box=None)
    results_table.add_column("Fonte", style="cyan")
    results_table.add_column("Sezione", style="white")
    results_table.add_column("Similarity", style="green")
    results_table.add_column("Estratto", style="magenta")

    for item in results:
        metadata = item.get("metadata", {})
        snippet = item.get("document", "")[:180] + (
            "…" if len(item.get("document", "")) > 180 else ""
        )
        results_table.add_row(
            metadata.get("knowledge_source", "n/a"),
            metadata.get("section_title", "n/a"),
            f"{item.get('similarity', 0):.2f}",
            snippet,
        )

    console.print(results_table)


@app.command("describe")
def ai_describe(
    text: str = typer.Argument(..., help="Service description to expand"),
    hours: float | None = typer.Option(None, "--hours", "-h", help="Hours worked"),
    rate: float | None = typer.Option(None, "--rate", "-r", help="Hourly rate (€)"),
    project: str | None = typer.Option(None, "--project", "-p", help="Project name"),
    technologies: str | None = typer.Option(
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
    hours: float | None,
    rate: float | None,
    project: str | None,
    technologies: str | None,
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

        # Optional RAG enrichment (invoice history + knowledge snippets)
        context.enable_rag = True
        try:
            context = await enrich_with_rag(context, text)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("invoice_context_rag_failed", error=str(exc))

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


app.add_typer(rag_app, name="rag")


def _display_result(response: AgentResponse) -> None:
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


def _display_metrics(response: AgentResponse) -> None:
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
    paese: str | None = typer.Option(
        None, "--paese", help="Client country code (IT, FR, US, etc.)"
    ),
    categoria: str | None = typer.Option(None, "--categoria", "-c", help="Service category"),
    importo: float | None = typer.Option(None, "--importo", "-i", help="Amount in EUR"),
    ateco: str | None = typer.Option(None, "--ateco", help="ATECO code"),
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
    asyncio.run(
        _run_tax_advisor(description, pa, estero, paese, categoria, importo, ateco, json_output)
    )


async def _run_tax_advisor(
    description: str,
    pa: bool,
    estero: bool,
    paese: str | None,
    categoria: str | None,
    importo: float | None,
    ateco: str | None,
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

        context.enable_rag = True
        try:
            context = await enrich_with_rag(context, description)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("tax_context_rag_failed", error=str(exc))

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


def _display_tax_result(response: AgentResponse) -> None:
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
            tax_info += "\n[bold]Split Payment:[/bold]   ✓ SI"

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
        console.print("\n[bold cyan]📋 Spiegazione:[/bold cyan]")
        console.print(f"{data['spiegazione']}\n")

        # Riferimento normativo
        console.print("[bold cyan]📜 Riferimento normativo:[/bold cyan]")
        console.print(f"{data['riferimento_normativo']}\n")

        # Nota fattura
        if data.get("note_fattura"):
            console.print("[bold cyan]📝 Nota per fattura:[/bold cyan]")
            console.print(f'"{data["note_fattura"]}"\n')

        # Raccomandazioni
        if data.get("raccomandazioni") and len(data["raccomandazioni"]) > 0:
            console.print("[bold cyan]💡 Raccomandazioni:[/bold cyan]")
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
    client_id: int | None = typer.Option(None, "--client", "-c", help="Filter by client ID"),
    retrain: bool = typer.Option(False, "--retrain", help="Force model retraining"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """
    Use AI/ML to forecast cash flow based on invoice payment predictions.

    The forecast analyzes unpaid invoices using an ML ensemble (Prophet + XGBoost)
    to predict when payments will arrive and provides AI-powered insights.

    Examples:
        openfatture ai forecast --months 6
        openfatture ai forecast --client 123 --months 3
        openfatture ai forecast --retrain --months 12
    """
    asyncio.run(_run_cash_flow_forecast(months, client_id, retrain, json_output))


async def _run_cash_flow_forecast(
    months: int,
    client_id: int | None,
    retrain: bool,
    json_output: bool,
) -> None:
    """Run cash flow forecasting with ML models."""
    if not json_output:
        console.print("\n[bold blue]💰 AI Cash Flow Forecasting[/bold blue]\n")

    try:
        from openfatture.ai.agents.cash_flow_predictor import CashFlowPredictorAgent

        # Create agent
        if not json_output:
            with console.status("[bold green]Initializing ML models..."):
                agent = CashFlowPredictorAgent()
                await agent.initialize(force_retrain=retrain)
        else:
            agent = CashFlowPredictorAgent()
            await agent.initialize(force_retrain=retrain)

        # Generate forecast
        if not json_output:
            status_msg = f"[bold green]Forecasting {months} months..."
            if client_id:
                status_msg += f" (client {client_id})"
            with console.status(status_msg):
                forecast = await agent.forecast_cash_flow(
                    months=months,
                    client_id=client_id,
                )
        else:
            forecast = await agent.forecast_cash_flow(
                months=months,
                client_id=client_id,
            )

        # Display results
        if json_output:
            console.print(JSON(json.dumps(forecast.to_dict(), indent=2, ensure_ascii=False)))
        else:
            _display_forecast(forecast)

    except ValueError as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {e}\n")
        logger.error("forecast_error", error=str(e))
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ Unexpected error:[/bold red] {e}\n")
        logger.error("forecast_unexpected_error", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)


def _display_forecast(forecast: Any) -> None:
    """Display cash flow forecast in rich format."""
    # Summary panel
    summary_text = f"""[bold]Forecast Period:[/bold] {forecast.months} months
[bold]Total Expected:[/bold] €{forecast.total_expected:,.2f}"""

    console.print(
        Panel(
            summary_text,
            title="[bold]📊 Cash Flow Summary[/bold]",
            border_style="blue",
        )
    )
    console.print()

    # Monthly forecast table
    table = Table(title="Monthly Forecast", box=None, show_header=True)
    table.add_column("Month", style="cyan", no_wrap=True)
    table.add_column("Expected Revenue", justify="right", style="green")

    for month_data in forecast.monthly_forecast:
        # Color based on amount
        amount = month_data["expected"]
        if amount > 0:
            amount_str = f"€{amount:,.2f}"
            amount_style = "green bold" if amount > 1000 else "green"
        else:
            amount_str = "€0.00"
            amount_style = "dim"

        table.add_row(
            month_data["month"],
            f"[{amount_style}]{amount_str}[/{amount_style}]",
        )

    console.print(table)
    console.print()

    # AI Insights
    if forecast.insights:
        console.print(
            Panel(
                forecast.insights,
                title="[bold]🤖 AI Insights[/bold]",
                border_style="magenta",
            )
        )
        console.print()

    # Recommendations
    if forecast.recommendations:
        console.print("[bold cyan]💡 Recommendations:[/bold cyan]\n")
        for rec in forecast.recommendations:
            console.print(f"  • {rec}")
        console.print()


@app.command("check")
def ai_check(
    fattura_id: int = typer.Argument(..., help="Invoice ID to check"),
    level: str = typer.Option(
        "standard",
        "--level",
        "-l",
        help="Check level: basic, standard, advanced",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all issues (including INFO)"),
) -> None:
    """
    Check invoice compliance using AI and rules engine.

    Levels:
    - basic: Only deterministic rules
    - standard: Rules + SDI rejection patterns (default)
    - advanced: Rules + SDI patterns + AI heuristics

    Examples:
        openfatture ai check 123
        openfatture ai check 123 --level advanced
        openfatture ai check 123 --json > report.json
        openfatture ai check 123 -v  # Show all issues
    """
    asyncio.run(_run_compliance_check(fattura_id, level, json_output, verbose))


async def _run_compliance_check(
    fattura_id: int,
    level_str: str,
    json_output: bool,
    verbose: bool,
) -> None:
    """Run compliance check on invoice."""
    from openfatture.ai.agents.compliance import ComplianceChecker, ComplianceLevel

    # Parse level
    level_map = {
        "basic": ComplianceLevel.BASIC,
        "standard": ComplianceLevel.STANDARD,
        "advanced": ComplianceLevel.ADVANCED,
    }

    level = level_map.get(level_str.lower())
    if not level:
        console.print(f"[bold red]❌ Invalid level: {level_str}[/bold red]")
        console.print("Valid levels: basic, standard, advanced")
        raise typer.Exit(1)

    if not json_output:
        console.print(f"\n[bold blue]🔍 Compliance Check (Level: {level.value})[/bold blue]\n")

    try:
        # Create checker
        with console.status("[bold green]Analyzing invoice...") if not json_output else None:
            checker = ComplianceChecker(level=level)
            report = await checker.check_invoice(fattura_id)

        # Output results
        if json_output:
            console.print(JSON(json.dumps(report.to_dict(), indent=2, ensure_ascii=False)))
        else:
            _display_compliance_report(report, verbose)

    except ValueError as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {e}\n")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ Unexpected error:[/bold red] {e}\n")
        logger.error("compliance_check_error", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)


def _display_compliance_report(report: Any, verbose: bool) -> None:
    """Display compliance check report in rich format."""
    # Header
    console.print(f"[bold]Invoice:[/bold] {report.invoice_number}")
    console.print(f"[bold]Check Level:[/bold] {report.level.value}")
    console.print()

    # Status panel
    if report.is_compliant:
        status_text = "[bold green]✓ COMPLIANT[/bold green]\n\nL'invoice è pronta per l'invio a SDI"
        border_style = "green"
    else:
        status_text = f"[bold red]✗ NOT COMPLIANT[/bold red]\n\nTrovati {len(report.get_errors())} errori critici"
        border_style = "red"

    console.print(
        Panel(
            status_text,
            title="[bold]Compliance Status[/bold]",
            border_style=border_style,
        )
    )
    console.print()

    # Scores
    scores_table = Table(show_header=False, box=None)
    scores_table.add_column("Metric", style="cyan bold")
    scores_table.add_column("Value")

    # Compliance score with color
    score_color = (
        "green"
        if report.compliance_score >= 80
        else "yellow" if report.compliance_score >= 60 else "red"
    )
    scores_table.add_row(
        "Compliance Score:", f"[{score_color}]{report.compliance_score:.1f}/100[/{score_color}]"
    )

    # Risk score with color (if available)
    if report.risk_score > 0:
        risk_color = (
            "red" if report.risk_score >= 70 else "yellow" if report.risk_score >= 40 else "green"
        )
        scores_table.add_row(
            "Risk Score:", f"[{risk_color}]{report.risk_score:.1f}/100[/{risk_color}]"
        )

    console.print(scores_table)
    console.print()

    # Issues summary
    errors = report.get_errors()
    warnings = report.get_warnings()
    infos = report.get_info()

    summary_table = Table(show_header=False, box=None)
    summary_table.add_column("Category", style="bold")
    summary_table.add_column("Count")

    summary_table.add_row("[red]Errors (must fix):", f"[red]{len(errors)}[/red]")
    summary_table.add_row("[yellow]Warnings:", f"[yellow]{len(warnings)}[/yellow]")
    summary_table.add_row("[blue]Info:", f"[blue]{len(infos)}[/blue]")

    if report.sdi_pattern_matches:
        summary_table.add_row(
            "[magenta]SDI Patterns Matched:",
            f"[magenta]{len(report.sdi_pattern_matches)}[/magenta]",
        )

    console.print(summary_table)
    console.print()

    # Display errors
    if errors:
        console.print("[bold red]❌ Errors (Must Fix):[/bold red]\n")
        for i, issue in enumerate(errors, 1):
            console.print(f"  {i}. [{issue.code}] {issue.message}")
            console.print(f"     Field: [cyan]{issue.field}[/cyan]")
            if issue.suggestion:
                console.print(f"     💡 {issue.suggestion}")
            if issue.reference:
                console.print(f"     [dim]Ref: {issue.reference}[/dim]")
            console.print()

    # Display warnings
    if warnings:
        console.print("[bold yellow]⚠️  Warnings:[/bold yellow]\n")
        for i, issue in enumerate(warnings, 1):
            console.print(f"  {i}. [{issue.code}] {issue.message}")
            console.print(f"     Field: [cyan]{issue.field}[/cyan]")
            if issue.suggestion:
                console.print(f"     💡 {issue.suggestion}")
            console.print()

    # Display info (only if verbose)
    if verbose and infos:
        console.print("[bold blue]ℹ️  Informational:[/bold blue]\n")
        for i, issue in enumerate(infos, 1):
            console.print(f"  {i}. [{issue.code}] {issue.message}")
            if issue.suggestion:
                console.print(f"     💡 {issue.suggestion}")
            console.print()

    # Recommendations
    if report.recommendations:
        console.print("[bold cyan]💡 Recommendations:[/bold cyan]\n")
        for rec in report.recommendations:
            console.print(f"  • {rec}")
        console.print()

    # Next steps
    if not report.is_compliant:
        console.print("[bold]Next Steps:[/bold]")
        console.print("  1. Fix all ERROR-level issues above")
        console.print("  2. Run compliance check again")
        console.print("  3. Address warnings to reduce rejection risk")
        console.print()
    else:
        console.print("[bold green]✅ Invoice is ready for SDI submission![/bold green]\n")
