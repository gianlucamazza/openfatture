"""AI VAT suggestion command."""

import json
from typing import cast

import typer
from rich.json import JSON
from rich.panel import Panel
from rich.table import Table

from openfatture.ai.context.enrichment import enrich_with_rag
from openfatture.ai.domain.context import TaxContext
from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.providers.factory import create_provider
from openfatture.cli.lifespan import get_event_bus
from openfatture.core.events.ai_events import AICommandCompletedEvent, AICommandStartedEvent
from openfatture.i18n import _
from openfatture.utils.async_bridge import run_async
from openfatture.utils.config import get_settings

from ._app import app, console, logger
from .describe import _display_metrics


@app.command("suggest-vat")
def ai_suggest_vat(
    ctx: typer.Context,
    description: str = typer.Argument(..., help=_("cli-ai-help-service-description")),
    pa: bool = typer.Option(False, "--pa", help=_("cli-ai-help-client-pa")),
    estero: bool = typer.Option(False, "--estero", help=_("cli-ai-help-client-foreign")),
    paese: str | None = typer.Option(None, "--paese", help=_("cli-ai-help-country-code")),
    categoria: str | None = typer.Option(
        None, "--categoria", "-c", help=_("cli-ai-help-service-category")
    ),
    importo: float | None = typer.Option(None, "--importo", "-i", help=_("cli-ai-help-amount-eur")),
    ateco: str | None = typer.Option(None, "--ateco", help=_("cli-ai-help-ateco-code")),
    json_output: bool = typer.Option(False, "--json", help=_("cli-ai-help-json-output")),
) -> None:
    """
    Use AI to suggest appropriate VAT rate and fiscal treatment.

    Examples:
        openfatture ai suggest-vat "consulenza IT"
        openfatture ai suggest-vat "consulenza IT per azienda edile"
        openfatture ai suggest-vat "formazione professionale" --pa
        openfatture ai suggest-vat "consulenza" --estero --paese US --format markdown
    """
    run_async(
        _run_tax_advisor(
            ctx, description, pa, estero, paese, categoria, importo, ateco, json_output
        )
    )


async def _run_tax_advisor(
    ctx: typer.Context,
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
    import time

    from openfatture.cli.formatters.utils import (
        get_format_from_context,
    )

    # Determine output format
    format_type = get_format_from_context(ctx, json_output)

    if format_type == "rich":
        console.print(f"\n{_('cli-ai-vat-title')}\n")

    # Track execution metrics
    start_time = time.time()
    success = False
    tokens_used = 0
    cost_usd = 0.0

    # Publish AICommandStartedEvent
    event_bus = get_event_bus()
    if event_bus:
        settings = get_settings()
        event_bus.publish(
            AICommandStartedEvent(
                command="suggest-vat",
                user_input=description,
                provider=settings.ai_provider,
                model=settings.ai_model,
                parameters={
                    "pa": pa,
                    "estero": estero,
                    "paese": paese,
                    "categoria": categoria,
                    "importo": importo,
                    "ateco": ateco,
                },
            )
        )

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
            context = cast(TaxContext, await enrich_with_rag(context, description))
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("tax_context_rag_failed", error=str(exc))

        # Show input
        _display_tax_input(context)

        # Create provider and agent
        with console.status(_("cli-ai-vat-processing")):
            provider = create_provider()
            agent = TaxAdvisorAgent(provider=provider)

            # Execute agent
            response = await agent.execute(context)

        # Check for errors
        if response.status.value == "error":
            console.print(f"\n{_('cli-ai-vat-error', error=response.error)}\n")
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

        # Track success and metrics
        success = True
        tokens_used = response.usage.total_tokens
        cost_usd = response.usage.estimated_cost_usd

    except Exception as e:
        console.print(f"\n{_('cli-ai-vat-error', error=str(e))}\n")
        logger.error("ai_suggest_vat_error", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)
    finally:
        # Publish AICommandCompletedEvent
        if event_bus:
            latency_ms = (time.time() - start_time) * 1000
            event_bus.publish(
                AICommandCompletedEvent(
                    command="suggest-vat",
                    success=success,
                    tokens_used=tokens_used,
                    cost_usd=cost_usd,
                    latency_ms=latency_ms,
                )
            )


def _display_tax_input(context: TaxContext) -> None:
    """Display tax context input."""
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row(_("cli-ai-vat-input-service"), context.tipo_servizio)

    if context.categoria_servizio:
        table.add_row(_("cli-ai-vat-input-category"), context.categoria_servizio)

    if context.importo:
        table.add_row(_("cli-ai-vat-input-amount"), f"€{context.importo:.2f}")

    if context.cliente_pa:
        table.add_row(_("cli-ai-vat-input-client"), _("cli-ai-vat-client-pa"))

    if context.cliente_estero:
        table.add_row(_("cli-ai-vat-input-foreign-client"), context.paese_cliente)

    if context.codice_ateco:
        table.add_row(_("cli-ai-vat-input-ateco"), context.codice_ateco)

    console.print(table)
    console.print()


def _display_tax_result(response: AgentResponse) -> None:
    """Display tax suggestion result."""
    # Try to get structured model
    if response.metadata.get("is_structured"):
        data = response.metadata["parsed_model"]

        # Main tax info panel
        yes_no = _("cli-ai-vat-yes") if data["reverse_charge"] else _("cli-ai-vat-no")
        tax_info = f"""[bold]{_("cli-ai-vat-rate-label")}[/bold]    {data["aliquota_iva"]}%
[bold]{_("cli-ai-vat-reverse-charge-label")}[/bold]  {yes_no}"""

        if data.get("codice_natura"):
            tax_info += (
                f"\n[bold]{_('cli-ai-vat-natura-label')}[/bold]      {data['codice_natura']}"
            )

        if data.get("split_payment"):
            tax_info += (
                f"\n[bold]{_('cli-ai-vat-split-payment-label')}[/bold]   {_('cli-ai-vat-yes')}"
            )

        if data.get("regime_speciale"):
            tax_info += (
                f"\n[bold]{_('cli-ai-vat-special-regime-label')}[/bold] {data['regime_speciale']}"
            )

        tax_info += f"\n[bold]{_('cli-ai-vat-confidence-label')}[/bold]      {int(data['confidence'] * 100)}%"

        console.print(
            Panel(
                tax_info,
                title=_("cli-ai-vat-result-panel-title"),
                border_style="green",
            )
        )

        # Spiegazione
        console.print(f"\n{_('cli-ai-vat-explanation-title')}")
        console.print(f"{data['spiegazione']}\n")

        # Riferimento normativo
        console.print(_("cli-ai-vat-legal-reference-title"))
        console.print(f"{data['riferimento_normativo']}\n")

        # Nota fattura
        if data.get("note_fattura"):
            console.print(_("cli-ai-vat-invoice-note-title"))
            console.print(f'"{data["note_fattura"]}"\n')

        # Raccomandazioni
        if data.get("raccomandazioni") and len(data["raccomandazioni"]) > 0:
            console.print(_("cli-ai-vat-recommendations-title"))
            for racc in data["raccomandazioni"]:
                console.print(f"  • {racc}")
            console.print()

    else:
        # Fallback to plain text
        console.print(
            Panel(
                response.content,
                title=_("cli-ai-vat-suggestion-title"),
                border_style="green",
            )
        )
