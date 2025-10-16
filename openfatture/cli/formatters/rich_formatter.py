"""Rich terminal output formatter (default)."""

from typing import Any

from rich.console import Console
from rich.panel import Panel

from openfatture.ai.domain.response import AgentResponse
from openfatture.cli.formatters.base import BaseFormatter


class RichFormatter(BaseFormatter):
    """Formatter that outputs responses using Rich terminal formatting.

    This is the default formatter and maintains backward compatibility
    with existing CLI output behavior. It uses Rich library for
    beautiful terminal output with colors, panels, and formatting.
    """

    def __init__(self, console: Console | None = None):
        """Initialize Rich formatter.

        Args:
            console: Rich Console instance (creates new one if None)
        """
        self.console = console or Console()

    def format_response(self, response: AgentResponse) -> str:
        """Format AgentResponse as Rich terminal output.

        This method returns the content only. For full Rich rendering,
        use the console directly or call render_response().

        Args:
            response: The AgentResponse to format

        Returns:
            Content string (Rich markup can be included)
        """
        # Return content with Rich markup
        if response.status.value == "error":
            return f"[bold red]❌ Error:[/bold red] {response.error or 'Unknown error'}"

        return response.content

    def format_stream_chunk(self, chunk: str) -> str:
        """Format streaming chunk with Rich markup.

        Args:
            chunk: A chunk of response content

        Returns:
            Chunk with Rich markup (if applicable)
        """
        return chunk

    def supports_streaming(self) -> bool:
        """Rich formatter supports streaming.

        Returns:
            True - streaming is supported
        """
        return True

    def render_response(self, response: AgentResponse, show_metrics: bool = True) -> None:
        """Render AgentResponse to console with full Rich formatting.

        This is the recommended way to display responses when using RichFormatter.

        Args:
            response: The AgentResponse to render
            show_metrics: Whether to show usage metrics (default: True)
        """
        # Handle errors
        if response.status.value == "error":
            self.console.print(
                f"\n[bold red]❌ Error:[/bold red] {response.error or 'Unknown error'}\n"
            )
            return

        # Display content in panel
        self.console.print(
            Panel(
                response.content,
                title="[bold]🤖 AI Response[/bold]",
                border_style="green",
            )
        )
        self.console.print()

        # Display metrics if enabled
        if show_metrics and response.usage:
            self._render_metrics(response)

    def _render_metrics(self, response: AgentResponse) -> None:
        """Render usage metrics.

        Args:
            response: The AgentResponse with metrics
        """
        from rich.table import Table

        metrics_table = Table(show_header=False, box=None, padding=(0, 2))
        metrics_table.add_column("Metric", style="dim")
        metrics_table.add_column("Value", style="dim")

        metrics_table.add_row(
            f"Provider: {response.provider or 'unknown'}",
            f"Model: {response.model or 'unknown'}",
        )

        if response.usage:
            metrics_table.add_row(
                f"Tokens: {response.usage.total_tokens}",
                f"Cost: ${response.usage.estimated_cost_usd:.4f}",
            )

        if response.latency_ms:
            metrics_table.add_row(
                f"Latency: {response.latency_ms:.0f}ms",
                "",
            )

        self.console.print(metrics_table)
        self.console.print()

    def _format_error_impl(self, error_msg: str) -> str:
        """Format error with Rich markup.

        Args:
            error_msg: The error message

        Returns:
            Rich formatted error message
        """
        return f"[bold red]❌ Error:[/bold red] {error_msg}"

    def _format_metadata_impl(self, metadata: dict[str, Any]) -> str:
        """Format metadata with Rich markup.

        Args:
            metadata: Metadata dictionary

        Returns:
            Rich formatted metadata
        """
        lines = []
        for key, value in metadata.items():
            lines.append(f"[cyan]{key}:[/cyan] {value}")
        return "\n".join(lines)
