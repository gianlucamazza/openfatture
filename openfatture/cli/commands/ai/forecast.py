"""AI cash flow forecasting command."""

from typing import Any

import typer
from rich.panel import Panel
from rich.table import Table

from openfatture.cli.lifespan import get_event_bus
from openfatture.core.events.ai_events import AICommandCompletedEvent, AICommandStartedEvent
from openfatture.utils.async_bridge import run_async

from ._app import app, console, logger


@app.command("forecast")
def ai_forecast(
    ctx: typer.Context,
    months: int = typer.Option(3, "--months", "-m", help="Months to forecast"),
    client_id: int | None = typer.Option(None, "--client", "-c", help="Filter by client ID"),
    retrain: bool = typer.Option(False, "--retrain", help="Force model retraining"),
    json_output: bool = typer.Option(
        False, "--json", help="Output as JSON (deprecated, use --format json)"
    ),
) -> None:
    """
    Use AI/ML to forecast cash flow based on invoice payment predictions.

    The forecast analyzes unpaid invoices using an ML ensemble (Prophet + XGBoost)
    to predict when payments will arrive and provides AI-powered insights.

    Examples:
        openfatture ai forecast --months 6
        openfatture ai forecast --client 123 --months 3
        openfatture ai forecast --retrain --months 12
        openfatture ai forecast --months 6 --format markdown
    """
    run_async(_run_cash_flow_forecast(ctx, months, client_id, retrain, json_output))


async def _run_cash_flow_forecast(
    ctx: typer.Context,
    months: int,
    client_id: int | None,
    retrain: bool,
    json_output: bool,
) -> None:
    """Run cash flow forecasting with ML models."""
    import time

    from openfatture.cli.formatters.utils import get_format_from_context, render_data

    format_type = get_format_from_context(ctx, json_output)

    if format_type == "rich":
        console.print("\n[bold blue]💰 AI Cash Flow Forecasting[/bold blue]\n")

    # Track execution metrics (ML model, not LLM, so no tokens)
    start_time = time.time()
    success = False

    # Publish AICommandStartedEvent
    event_bus = get_event_bus()
    if event_bus:
        event_bus.publish(
            AICommandStartedEvent(
                command="forecast",
                user_input=f"{months} months forecast",
                provider="ml_ensemble",
                model="prophet_xgboost",
                parameters={
                    "months": months,
                    "client_id": client_id,
                    "retrain": retrain,
                },
            )
        )

    try:
        from openfatture.ai.agents.cash_flow_predictor import CashFlowPredictorAgent

        # Create agent
        if format_type == "rich":
            with console.status("[bold green]Initializing ML models..."):
                agent = CashFlowPredictorAgent()
                await agent.initialize(force_retrain=retrain)
        else:
            agent = CashFlowPredictorAgent()
            await agent.initialize(force_retrain=retrain)

        # Generate forecast
        if format_type == "rich":
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
        if json_output or format_type == "json":
            render_data(forecast.to_dict(), format_type, console)
        elif format_type == "rich":
            _display_forecast(forecast)
        else:
            # For other formats, render forecast as data
            render_data(forecast.to_dict(), format_type, console)

        # Track success
        success = True

    except ValueError as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {e}\n")
        logger.error("forecast_error", error=str(e))
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ Unexpected error:[/bold red] {e}\n")
        logger.error("forecast_unexpected_error", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)
    finally:
        # Publish AICommandCompletedEvent (ML model, no tokens/cost)
        if event_bus:
            latency_ms = (time.time() - start_time) * 1000
            event_bus.publish(
                AICommandCompletedEvent(
                    command="forecast",
                    success=success,
                    tokens_used=0,  # ML model, not LLM
                    cost_usd=0.0,  # ML model, not LLM
                    latency_ms=latency_ms,
                )
            )


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
