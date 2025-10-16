"""Utility functions for using formatters in CLI commands."""

from typing import Any

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
    2. json_output flag (backward compatibility for --json)
    3. Context format setting (global --format flag)
    4. Default to "rich"

    Args:
        ctx: Typer context (may contain format from global flag)
        json_output: Legacy --json flag for backward compatibility
        format_override: Explicit format override

    Returns:
        Format type string
    """
    # Priority 1: Explicit override
    if format_override:
        return format_override

    # Priority 2: Legacy --json flag (backward compatibility)
    if json_output:
        return "json"

    # Priority 3: Global --format flag from context
    if ctx and ctx.obj and "format" in ctx.obj:
        return ctx.obj["format"]

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
                console.print(output)
            else:
                print(output)
    else:
        # For other formats, print formatted output
        output = formatter.format_response(response)
        if console:
            console.print(output)
        else:
            print(output)


def render_error(
    error: Exception | str,
    format_type: str = "rich",
    console: Console | None = None,
) -> None:
    """Render an error using the specified formatter.

    Args:
        error: Exception or error message string
        format_type: Format type ("rich", "json", "markdown", etc.)
        console: Rich Console instance (used for rich format)
    """
    formatter = get_formatter(format_type)
    output = formatter.format_error(error)

    if console:
        console.print(output)
    else:
        print(output)


def render_data(
    data: dict[str, Any],
    format_type: str = "rich",
    console: Console | None = None,
) -> None:
    """Render arbitrary data using the specified formatter.

    Args:
        data: Dictionary of data to render
        format_type: Format type ("rich", "json", "markdown", etc.)
        console: Rich Console instance
    """
    if format_type == "json":
        import json

        from rich.json import JSON

        output = json.dumps(data, indent=2, ensure_ascii=False)
        if console:
            console.print(JSON(output))
        else:
            print(output)
    elif format_type == "rich":
        # Use Rich's native JSON rendering
        import json

        from rich.json import JSON

        if console:
            console.print(JSON(json.dumps(data, indent=2, ensure_ascii=False)))
        else:
            print(json.dumps(data, indent=2))
    else:
        # For other formats, render as metadata
        formatter = get_formatter(format_type)
        output = formatter.format_metadata(data)
        if console:
            console.print(output)
        else:
            print(output)
