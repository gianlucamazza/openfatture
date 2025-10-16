"""Markdown output formatter."""

from typing import Any

from openfatture.ai.domain.response import AgentResponse
from openfatture.cli.formatters.base import BaseFormatter


class MarkdownFormatter(BaseFormatter):
    """Formatter that outputs responses as Markdown.

    This formatter generates well-structured Markdown with:
    - Headers for sections
    - Code blocks for technical content
    - Lists for structured data
    - Emphasis and formatting
    """

    def __init__(self, include_metadata: bool = True):
        """Initialize Markdown formatter.

        Args:
            include_metadata: Whether to include metadata section (default: True)
        """
        self.include_metadata = include_metadata

    def format_response(self, response: AgentResponse) -> str:
        """Format AgentResponse as Markdown.

        Args:
            response: The AgentResponse to format

        Returns:
            Markdown string representation
        """
        lines = []

        # Title
        lines.append("# AI Response")
        lines.append("")

        # Handle errors
        if response.status.value == "error":
            lines.append("## Error")
            lines.append("")
            lines.append(f"> ❌ {response.error or 'Unknown error'}")
            lines.append("")
            return "\n".join(lines)

        # Content section
        lines.append("## Response")
        lines.append("")
        lines.append(response.content)
        lines.append("")

        # Metadata section
        if self.include_metadata:
            lines.append("---")
            lines.append("")
            lines.append("## Metadata")
            lines.append("")

            # Provider and model
            if response.provider or response.model:
                lines.append(f"- **Provider:** {response.provider or 'unknown'}")
                lines.append(f"- **Model:** {response.model or 'unknown'}")

            # Usage metrics
            if response.usage:
                lines.append(f"- **Tokens Used:** {response.usage.total_tokens}")
                lines.append(f"  - Prompt: {response.usage.prompt_tokens}")
                lines.append(f"  - Completion: {response.usage.completion_tokens}")
                lines.append(f"- **Cost:** ${response.usage.estimated_cost_usd:.4f}")

            # Latency
            if response.latency_ms:
                lines.append(f"- **Latency:** {response.latency_ms:.0f}ms")

            # Status
            lines.append(f"- **Status:** {response.status.value}")

            # Tool calls (if any)
            if response.tool_calls:
                lines.append(f"- **Tool Calls:** {len(response.tool_calls)}")

            lines.append("")

        return "\n".join(lines)

    def format_stream_chunk(self, chunk: str) -> str:
        """Format streaming chunk (not supported for Markdown).

        Markdown needs complete response structure, so chunks are
        returned as-is for buffering.

        Args:
            chunk: A chunk of response content

        Returns:
            The chunk as-is
        """
        return chunk

    def supports_streaming(self) -> bool:
        """Markdown formatter does not support true streaming.

        Returns:
            False - streaming not supported (will buffer)
        """
        return False

    def _format_error_impl(self, error_msg: str) -> str:
        """Format error as Markdown.

        Args:
            error_msg: The error message

        Returns:
            Markdown formatted error
        """
        return f"# Error\n\n> ❌ {error_msg}\n"

    def _format_metadata_impl(self, metadata: dict[str, Any]) -> str:
        """Format metadata as Markdown list.

        Args:
            metadata: Metadata dictionary

        Returns:
            Markdown formatted metadata
        """
        lines = ["## Metadata", ""]
        for key, value in metadata.items():
            # Format key as title case
            formatted_key = key.replace("_", " ").title()
            lines.append(f"- **{formatted_key}:** {value}")
        lines.append("")
        return "\n".join(lines)
