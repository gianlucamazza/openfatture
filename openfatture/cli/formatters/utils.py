"""Utility functions for using formatters in CLI commands."""

import typer
from rich.console import Console

from openfatture.ai.domain.response import AgentResponse
from openfatture.cli.formatters.factory import get_formatter
from openfatture.cli.formatters.rich_formatter import RichFormatter


def get_format_from_context(
    ctx: typer.Context | None = None,
    json_output: bool = False,
    format_override: str | None = None,
) -> str:
    """Determine output format from context and options.

    Priority order:
    1. format_override parameter (explicit format)
    2. json_output flag
    3. Context format setting (global --format flag)
    4. Default to "rich"

    Args:
        ctx: Typer context (may contain format from global flag)
        json_output: Request JSON output
        format_override: Explicit format override

    Returns:
        Format type string
    """
    # Priority 1: Explicit override
    if format_override:
        return format_override

    # Priority 2: Explicit JSON output
    if json_output:
        return "json"

    # Priority 3: Global --format flag from context
    if ctx and ctx.obj and "format" in ctx.obj:
        return str(ctx.obj["format"])

    # Default: rich
    return "rich"


def render_response(
    response: AgentResponse,
    format_type: str = "rich",
    console: Console | None = None,
    show_metrics: bool = True,
) -> None:
    """Render an AgentResponse using the specified formatter.

    Args:
        response: The AgentResponse to render
        format_type: Format type ("rich", "json", "markdown", etc.)
        console: Rich Console instance (used for rich format)
        show_metrics: Whether to show usage metrics (for rich format)
    """
    formatter = get_formatter(format_type)

    if format_type == "rich":
        # Use RichFormatter's render_response method for full rendering
        if isinstance(formatter, RichFormatter):
            if console:
                formatter.console = console
            formatter.render_response(response, show_metrics=show_metrics)
        else:
            # Fallback if not RichFormatter
            output = formatter.format_response(response)
            if console:
                console.print(output, markup=False, highlight=False, soft_wrap=True)
            else:
                print(output)
    else:
        # For other formats, print formatted output
        output = formatter.format_response(response)
        if console:
            console.print(output, markup=False, highlight=False, soft_wrap=True)
        else:
            print(output)
