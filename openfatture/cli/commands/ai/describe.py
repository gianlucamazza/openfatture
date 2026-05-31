"""AI invoice description generation command."""

from typing import cast

import typer
from rich.panel import Panel
from rich.table import Table

from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.context.enrichment import enrich_with_rag
from openfatture.ai.domain.context import InvoiceContext
from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.providers.factory import create_provider
from openfatture.cli.lifespan import get_event_bus
from openfatture.core.events.ai_events import AICommandCompletedEvent, AICommandStartedEvent
from openfatture.i18n import _
from openfatture.utils.async_bridge import run_async
from openfatture.utils.config import get_settings

from ._app import app, console, logger


@app.command("describe")
def ai_describe(
    ctx: typer.Context,
    text: str = typer.Argument(..., help=_("cli-ai-help-service-description")),
    hours: float | None = typer.Option(None, "--hours", "-h", help=_("cli-ai-help-hours-worked")),
    rate: float | None = typer.Option(None, "--rate", "-r", help=_("cli-ai-help-hourly-rate")),
    project: str | None = typer.Option(None, "--project", "-p", help=_("cli-ai-help-project-name")),
    technologies: str | None = typer.Option(
        None, "--tech", "-t", help=_("cli-ai-help-technologies")
    ),
    json_output: bool = typer.Option(False, "--json", help=_("cli-ai-help-json-output")),
) -> None:
    """
    Use AI to generate detailed invoice descriptions.

    Example:
        openfatture ai describe "3 ore consulenza web"
        openfatture ai describe "sviluppo backend API" --hours 5 --tech "Python,FastAPI"
        openfatture ai describe "consulenza" --format markdown
    """
    run_async(_run_invoice_assistant(ctx, text, hours, rate, project, technologies, json_output))


async def _run_invoice_assistant(
    ctx: typer.Context,
    text: str,
    hours: float | None,
    rate: float | None,
    project: str | None,
    technologies: str | None,
    json_output: bool,
) -> None:
    """Run the Invoice Assistant agent."""
    import time

    from openfatture.cli.formatters.utils import (
        get_format_from_context,
        render_data,
        render_response,
    )

    # Determine output format
    format_type = get_format_from_context(ctx, json_output)

    if format_type == "rich":
        console.print(f"\n{_('cli-ai-describe-title')}\n")

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
                command="describe",
                user_input=text,
                provider=settings.ai_provider,
                model=settings.ai_model,
                parameters={
                    "hours": hours,
                    "rate": rate,
                    "project": project,
                    "technologies": technologies,
                },
            )
        )

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
            context = cast(InvoiceContext, await enrich_with_rag(context, text))
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("invoice_context_rag_failed", error=str(exc))

        # Show input (only for rich format)
        if format_type == "rich":
            _display_input(context)

        # Create provider and agent
        if format_type == "rich":
            with console.status(_("cli-ai-describe-processing")):
                provider = create_provider()
                agent = InvoiceAssistantAgent(provider=provider)
                response = await agent.execute(context)
        else:
            provider = create_provider()
            agent = InvoiceAssistantAgent(provider=provider)
            response = await agent.execute(context)

        # Check for errors
        if response.status.value == "error":
            if format_type == "rich":
                console.print(f"\n{_('cli-ai-describe-error', error=response.error)}\n")
            else:
                from openfatture.cli.formatters.utils import render_error

                render_error(response.error or _("cli-ai-error-unknown"), format_type, console)
            logger.error("ai_describe_failed", error=response.error)
            return

        # Display results using formatter
        if json_output or format_type == "json":
            # Raw JSON output (backward compatibility)
            if response.metadata.get("is_structured"):
                output = response.metadata["parsed_model"]
            else:
                output = {"descrizione_completa": response.content}
            render_data(output, format_type, console)
        elif format_type == "rich":
            # Use existing rich display
            _display_result(response)
            _display_metrics(response)
        else:
            # Use formatter for other formats
            render_response(response, format_type, console, show_metrics=True)

        # Track success and metrics
        success = True
        tokens_used = response.usage.total_tokens
        cost_usd = response.usage.estimated_cost_usd

    except Exception as e:
        if format_type == "rich":
            console.print(f"\n{_('cli-ai-describe-error', error=str(e))}\n")
        else:
            from openfatture.cli.formatters.utils import render_error

            render_error(e, format_type, console)
        logger.error("ai_describe_error", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)
    finally:
        # Publish AICommandCompletedEvent
        if event_bus:
            latency_ms = (time.time() - start_time) * 1000
            event_bus.publish(
                AICommandCompletedEvent(
                    command="describe",
                    success=success,
                    tokens_used=tokens_used,
                    cost_usd=cost_usd,
                    latency_ms=latency_ms,
                )
            )


def _display_input(context: InvoiceContext) -> None:
    """Display input context."""
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row(_("cli-ai-describe-input-service"), context.servizio_base)

    if context.ore_lavorate:
        table.add_row(_("cli-ai-describe-input-hours"), f"{context.ore_lavorate:.1f}h")

    if context.tariffa_oraria:
        table.add_row(_("cli-ai-describe-input-rate"), f"€{context.tariffa_oraria:.2f}/h")

    if context.progetto:
        table.add_row(_("cli-ai-describe-input-project"), context.progetto)

    if context.tecnologie:
        table.add_row(_("cli-ai-describe-input-technologies"), ", ".join(context.tecnologie))

    console.print(table)
    console.print()


def _display_result(response: AgentResponse) -> None:
    """Display structured result."""
    # Try to get structured model
    if response.metadata.get("is_structured"):
        data = response.metadata["parsed_model"]

        # Description
        console.print(
            Panel(
                data["descrizione_completa"],
                title=_("cli-ai-describe-result-panel-title"),
                border_style="green",
            )
        )

        # Deliverables
        if data.get("deliverables"):
            console.print(f"\n{_('cli-ai-describe-deliverables-title')}")
            for item in data["deliverables"]:
                console.print(f"  • {item}")

        # Competenze
        if data.get("competenze"):
            console.print(f"\n{_('cli-ai-describe-skills-title')}")
            for skill in data["competenze"]:
                console.print(f"  • {skill}")

        # Duration
        if data.get("durata_ore"):
            console.print(f"\n{_('cli-ai-describe-duration-label')} {data['durata_ore']}h")

        # Notes
        if data.get("note"):
            console.print(f"\n{_('cli-ai-describe-notes-label')} {data['note']}")

    else:
        # Fallback to plain text
        console.print(
            Panel(
                response.content,
                title=_("cli-ai-describe-generated-title"),
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
        _("cli-ai-metrics-provider", provider=response.provider),
        _("cli-ai-metrics-model", model=response.model),
    )
    metrics_table.add_row(
        _("cli-ai-metrics-tokens", tokens=response.usage.total_tokens),
        _("cli-ai-metrics-cost", cost=f"{response.usage.estimated_cost_usd:.4f}"),
    )
    metrics_table.add_row(
        _("cli-ai-metrics-latency", latency=f"{response.latency_ms:.0f}"),
        "",
    )

    console.print(metrics_table)
    console.print()
