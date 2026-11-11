"""Utility functions for using formatters in CLI commands."""

import typer
from rich.console import Console

from openfatture.ai.domain.response import AgentResponse
from openfatture.cli.formatters.factory import get_formatter
from openfatture.cli.formatters.rich_formatter import RichFormatter


def get_format_from_context(ctx: typer.Context | None = None) -> str:
    """The output format chosen with the root ``--format`` option (default ``rich``)."""
    if ctx and ctx.obj and "format" in ctx.obj:
        return str(ctx.obj["format"])
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
