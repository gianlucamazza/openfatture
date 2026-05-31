"""AI invoice compliance check command."""

from contextlib import nullcontext
from typing import Any

import typer
from rich.panel import Panel
from rich.table import Table

from openfatture.ai.agents.compliance import ComplianceChecker
from openfatture.cli.lifespan import get_event_bus
from openfatture.core.events.ai_events import AICommandCompletedEvent, AICommandStartedEvent
from openfatture.utils.async_bridge import run_async

from ._app import app, console, logger


@app.command("check")
def ai_check(
    ctx: typer.Context,
    fattura_id: int = typer.Argument(..., help="Invoice ID to check"),
    level: str = typer.Option(
        "standard",
        "--level",
        "-l",
        help="Check level: basic, standard, advanced",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output as JSON (deprecated, use --format json)"
    ),
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
        openfatture ai check 123 --format markdown
    """
    run_async(_run_compliance_check(ctx, fattura_id, level, json_output, verbose))


async def _run_compliance_check(
    ctx: typer.Context,
    fattura_id: int,
    level_str: str,
    json_output: bool,
    verbose: bool,
) -> None:
    """Run compliance check on invoice."""
    import time

    from openfatture.ai.agents.compliance import ComplianceLevel
    from openfatture.cli.formatters.utils import get_format_from_context, render_data

    format_type = get_format_from_context(ctx, json_output)

    # Parse level
    level_map = {
        "basic": ComplianceLevel.BASIC,
        "standard": ComplianceLevel.STANDARD,
        "advanced": ComplianceLevel.ADVANCED,
    }

    level = level_map.get(level_str.lower())
    if not level:
        console.print(f"[bold red]Invalid level: {level_str}[/bold red]")
        console.print("Valid levels: basic, standard, advanced")
        raise typer.Exit(1)

    if format_type == "rich":
        console.print(f"\n[bold blue]Compliance Check (Level: {level.value})[/bold blue]\n")

    # Track execution metrics (rules-based, not LLM)
    start_time = time.time()
    success = False

    # Publish AICommandStartedEvent
    event_bus = get_event_bus()
    if event_bus:
        event_bus.publish(
            AICommandStartedEvent(
                command="check",
                user_input=f"Invoice {fattura_id}",
                provider="compliance_engine",
                model=level.value,
                parameters={"fattura_id": fattura_id, "level": level_str, "verbose": verbose},
            )
        )

    try:
        # Create checker
        status_context = (
            console.status("[bold green]Analyzing invoice...")
            if format_type == "rich"
            else nullcontext()
        )
        with status_context:
            checker = ComplianceChecker(level=level)
            report = await checker.check_invoice(fattura_id)

        # Output results
        if json_output or format_type == "json":
            render_data(report.to_dict(), format_type, console)
        elif format_type == "rich":
            _display_compliance_report(report, verbose)
        else:
            # For other formats, output as data
            render_data(report.to_dict(), format_type, console)

        # Track success
        success = True

    except ValueError as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}\n")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error:[/bold red] {e}\n")
        logger.error("compliance_check_error", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)
    finally:
        # Publish AICommandCompletedEvent (rules-based, no tokens/cost)
        if event_bus:
            latency_ms = (time.time() - start_time) * 1000
            event_bus.publish(
                AICommandCompletedEvent(
                    command="check",
                    success=success,
                    tokens_used=0,  # Rules-based, not LLM
                    cost_usd=0.0,  # Rules-based, not LLM
                    latency_ms=latency_ms,
                )
            )


def _display_compliance_report(report: Any, verbose: bool) -> None:
    """Display compliance check report in rich format."""
    # Header
    console.print(f"[bold]Invoice:[/bold] {report.invoice_number}")
    console.print(f"[bold]Check Level:[/bold] {report.level.value}")
    console.print()

    # Status panel
    if report.is_compliant:
        status_text = (
            "[bold green]COMPLIANT[/bold green]\n\nThe invoice is ready for SDI submission"
        )
        border_style = "green"
    else:
        status_text = f"[bold red]NOT COMPLIANT[/bold red]\n\nFound {len(report.get_errors())} critical errors"
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
        console.print("[bold red]Errors (Must Fix):[/bold red]\n")
        for i, issue in enumerate(errors, 1):
            console.print(f"  {i}. [{issue.code}] {issue.message}")
            console.print(f"     Field: [cyan]{issue.field}[/cyan]")
            if issue.suggestion:
                console.print(f" {issue.suggestion}")
            if issue.reference:
                console.print(f"     [dim]Ref: {issue.reference}[/dim]")
            console.print()

    # Display warnings
    if warnings:
        console.print("[bold yellow]Warnings:[/bold yellow]\n")
        for i, issue in enumerate(warnings, 1):
            console.print(f"  {i}. [{issue.code}] {issue.message}")
            console.print(f"     Field: [cyan]{issue.field}[/cyan]")
            if issue.suggestion:
                console.print(f" {issue.suggestion}")
            console.print()

    # Display info (only if verbose)
    if verbose and infos:
        console.print("[bold blue]Informational:[/bold blue]\n")
        for i, issue in enumerate(infos, 1):
            console.print(f"  {i}. [{issue.code}] {issue.message}")
            if issue.suggestion:
                console.print(f" {issue.suggestion}")
            console.print()

    # Recommendations
    if report.recommendations:
        console.print("[bold cyan]Recommendations:[/bold cyan]\n")
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
        console.print("[bold green]Invoice is ready for SDI submission![/bold green]\n")
