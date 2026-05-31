"""AI invoice creation workflow command."""

import typer

from openfatture.ai.orchestration.workflows.invoice_creation import InvoiceCreationWorkflow
from openfatture.cli.lifespan import get_event_bus
from openfatture.core.events.ai_events import AICommandCompletedEvent, AICommandStartedEvent
from openfatture.utils.async_bridge import run_async
from openfatture.utils.config import get_settings

from ._app import app, console, logger


@app.command("create-invoice")
def ai_create_invoice(
    ctx: typer.Context,
    description: str = typer.Argument(..., help="Service description"),
    client_id: int = typer.Option(..., "--client", "-c", help="Client ID"),
    imponibile: float = typer.Option(..., "--amount", "-a", help="Invoice amount (€)"),
    hours: float | None = typer.Option(None, "--hours", "-h", help="Hours worked"),
    rate: float | None = typer.Option(None, "--rate", "-r", help="Hourly rate (€)"),
    project: str | None = typer.Option(None, "--project", "-p", help="Project name"),
    technologies: str | None = typer.Option(
        None, "--tech", "-t", help="Technologies used (comma-separated)"
    ),
    require_approvals: bool = typer.Option(
        False, "--require-approvals", help="Require human approval at each step"
    ),
    confidence_threshold: float = typer.Option(
        0.85, "--confidence", help="Confidence threshold for auto-approval (0.0-1.0)"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output as JSON (deprecated, use --format json)"
    ),
) -> None:
    """
    Create a complete invoice using AI workflow orchestration.

    This command uses a multi-agent LangGraph workflow to:
    1. Generate detailed description
    2. Suggest VAT treatment
    3. Check compliance
    4. Create the invoice

    Example:
        openfatture ai create-invoice "consulenza web 3 ore" --client 123 --amount 300
        openfatture ai create-invoice "sviluppo app mobile" --hours 20 --rate 50 --require-approvals
        openfatture ai create-invoice "development" --client 1 --amount 500 --format json
    """
    run_async(
        _run_invoice_workflow(
            ctx=ctx,
            description=description,
            client_id=client_id,
            imponibile=imponibile,
            hours=hours,
            rate=rate,
            project=project,
            technologies=technologies,
            require_approvals=require_approvals,
            confidence_threshold=confidence_threshold,
            json_output=json_output,
        )
    )


async def _run_invoice_workflow(
    ctx: typer.Context,
    description: str,
    client_id: int,
    imponibile: float,
    hours: float | None,
    rate: float | None,
    project: str | None,
    technologies: str | None,
    require_approvals: bool,
    confidence_threshold: float,
    json_output: bool,
) -> None:
    """Execute invoice creation workflow."""
    import time

    from openfatture.cli.formatters.utils import get_format_from_context, render_data

    format_type = get_format_from_context(ctx, json_output)

    # Track execution metrics
    start_time = time.time()
    success = False

    # Publish AICommandStartedEvent
    event_bus = get_event_bus()
    if event_bus:
        settings = get_settings()
        event_bus.publish(
            AICommandStartedEvent(
                command="create-invoice",
                user_input=description,
                provider=settings.ai_provider,
                model=settings.ai_model,
                parameters={
                    "client_id": client_id,
                    "imponibile": imponibile,
                    "hours": hours,
                    "rate": rate,
                    "project": project,
                    "technologies": technologies,
                    "require_approvals": require_approvals,
                    "confidence_threshold": confidence_threshold,
                },
            )
        )

    try:
        # Parse technologies
        tech_list = [t.strip() for t in technologies.split(",")] if technologies else None

        # Create workflow
        workflow = InvoiceCreationWorkflow(confidence_threshold=confidence_threshold)

        # Execute workflow
        result = await workflow.execute(
            user_input=description,
            client_id=client_id,
            imponibile=imponibile,
            hours=hours,
            hourly_rate=rate,
            require_approvals=require_approvals,
        )

        if json_output or format_type == "json":
            render_data(result.model_dump(), format_type, console)
        elif format_type == "rich":
            # Display results in rich format
            if result.invoice_id:
                console.print("[bold green]Invoice created successfully![/bold green]")
                console.print(f"Invoice ID: {result.invoice_id}")
            else:
                console.print(f"[yellow]Workflow completed with status: {result.status}[/yellow]")

            console.print(f"Status: {result.status}")

            if result.warnings:
                console.print("\n[yellow]Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  • {warning}")

            if result.errors:
                console.print("\n[red]Errors:[/red]")
                for error in result.errors:
                    console.print(f"  • {error}")
        else:
            # For other formats, render as data
            render_data(result.model_dump(), format_type, console)

        # Track success (workflow may have succeeded even with warnings)
        success = result.invoice_id is not None

    except Exception as e:
        logger.error("Workflow execution failed", error=str(e))
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
    finally:
        # Publish AICommandCompletedEvent (workflow uses LLMs, but we don't track tokens here)
        if event_bus:
            latency_ms = (time.time() - start_time) * 1000
            event_bus.publish(
                AICommandCompletedEvent(
                    command="create-invoice",
                    success=success,
                    tokens_used=0,  # Workflow aggregates multiple steps
                    cost_usd=0.0,  # Workflow aggregates multiple steps
                    latency_ms=latency_ms,
                )
            )
