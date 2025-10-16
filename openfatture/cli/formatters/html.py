"""HTML output formatter with embedded styling."""

import html
from typing import Any

from openfatture.ai.domain.response import AgentResponse
from openfatture.cli.formatters.base import BaseFormatter


class HTMLFormatter(BaseFormatter):
    """Formatter that outputs responses as styled HTML.

    This formatter generates complete HTML documents with:
    - Embedded CSS for styling
    - Semantic HTML structure
    - Responsive design
    - Professional appearance
    """

    def __init__(self, include_metadata: bool = True, dark_mode: bool = False):
        """Initialize HTML formatter.

        Args:
            include_metadata: Whether to include metadata section (default: True)
            dark_mode: Use dark theme colors (default: False)
        """
        self.include_metadata = include_metadata
        self.dark_mode = dark_mode

    def format_response(self, response: AgentResponse) -> str:
        """Format AgentResponse as HTML document.

        Args:
            response: The AgentResponse to format

        Returns:
            Complete HTML document string
        """
        parts = []

        # HTML header with CSS
        parts.append(self._get_html_header())

        # Body start
        parts.append("<body>")
        parts.append('<div class="container">')

        # Title
        parts.append("<h1>🤖 AI Response</h1>")

        # Handle errors
        if response.status.value == "error":
            parts.append('<div class="error">')
            parts.append(
                f"<p>❌ <strong>Error:</strong> {html.escape(response.error or 'Unknown error')}</p>"
            )
            parts.append("</div>")
        else:
            # Content section
            parts.append('<div class="content">')
            parts.append("<h2>Response</h2>")
            parts.append(
                f"<div class='response-content'>{self._format_content_html(response.content)}</div>"
            )
            parts.append("</div>")

            # Metadata section
            if self.include_metadata:
                parts.append(self._format_metadata_html(response))

        # Body end
        parts.append("</div>")
        parts.append("</body>")
        parts.append("</html>")

        return "\n".join(parts)

    def _get_html_header(self) -> str:
        """Generate HTML header with embedded CSS.

        Returns:
            HTML header string
        """
        # Color scheme
        if self.dark_mode:
            bg_color = "#1e1e1e"
            text_color = "#e0e0e0"
            border_color = "#444"
            card_bg = "#2d2d2d"
            accent_color = "#4a9eff"
            error_bg = "#4a1f1f"
            error_border = "#d32f2f"
        else:
            bg_color = "#f5f5f5"
            text_color = "#333"
            border_color = "#ddd"
            card_bg = "#fff"
            accent_color = "#2196f3"
            error_bg = "#ffebee"
            error_border = "#f44336"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Response</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: {bg_color};
            color: {text_color};
            line-height: 1.6;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background-color: {card_bg};
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        h1 {{
            color: {accent_color};
            border-bottom: 2px solid {border_color};
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        h2 {{
            color: {accent_color};
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 1.5em;
        }}
        .content {{
            margin-bottom: 30px;
        }}
        .response-content {{
            padding: 20px;
            background-color: {bg_color};
            border-left: 4px solid {accent_color};
            border-radius: 4px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .metadata {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 4px;
            padding: 20px;
        }}
        .metadata-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .metadata-item {{
            padding: 10px;
            background-color: {card_bg};
            border-radius: 4px;
        }}
        .metadata-label {{
            font-weight: bold;
            color: {accent_color};
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .metadata-value {{
            margin-top: 5px;
            font-size: 1.1em;
        }}
        .error {{
            background-color: {error_bg};
            border: 2px solid {error_border};
            border-radius: 4px;
            padding: 20px;
            margin: 20px 0;
        }}
        .error p {{
            color: {error_border};
        }}
        @media (max-width: 600px) {{
            body {{
                padding: 10px;
            }}
            .container {{
                padding: 15px;
            }}
            .metadata-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>"""

    def _format_content_html(self, content: str) -> str:
        """Format content text with proper HTML escaping and line breaks.

        Args:
            content: The content text

        Returns:
            HTML formatted content
        """
        # Escape HTML and convert newlines to <br>
        escaped = html.escape(content)
        return escaped

    def _format_metadata_html(self, response: AgentResponse) -> str:
        """Format metadata section as HTML.

        Args:
            response: The AgentResponse with metadata

        Returns:
            HTML formatted metadata section
        """
        parts = []
        parts.append('<div class="metadata">')
        parts.append("<h2>Metadata</h2>")
        parts.append('<div class="metadata-grid">')

        # Provider
        if response.provider:
            parts.append(self._metadata_item("Provider", response.provider))

        # Model
        if response.model:
            parts.append(self._metadata_item("Model", response.model))

        # Tokens
        if response.usage:
            parts.append(
                self._metadata_item(
                    "Tokens Used",
                    f"{response.usage.total_tokens:,} "
                    f"(prompt: {response.usage.prompt_tokens:,}, "
                    f"completion: {response.usage.completion_tokens:,})",
                )
            )

            # Cost
            parts.append(self._metadata_item("Cost", f"${response.usage.estimated_cost_usd:.4f}"))

        # Latency
        if response.latency_ms:
            parts.append(self._metadata_item("Latency", f"{response.latency_ms:.0f}ms"))

        # Status
        parts.append(self._metadata_item("Status", response.status.value.upper()))

        # Tool calls
        if response.tool_calls:
            parts.append(self._metadata_item("Tool Calls", str(len(response.tool_calls))))

        parts.append("</div>")
        parts.append("</div>")

        return "\n".join(parts)

    def _metadata_item(self, label: str, value: str) -> str:
        """Create a metadata item HTML.

        Args:
            label: The metadata label
            value: The metadata value

        Returns:
            HTML string for metadata item
        """
        return f"""<div class="metadata-item">
    <div class="metadata-label">{html.escape(label)}</div>
    <div class="metadata-value">{html.escape(value)}</div>
</div>"""

    def format_stream_chunk(self, chunk: str) -> str:
        """Format streaming chunk (not fully supported for HTML).

        HTML needs complete document structure, so chunks are
        returned as escaped text for buffering.

        Args:
            chunk: A chunk of response content

        Returns:
            HTML escaped chunk
        """
        return html.escape(chunk)

    def supports_streaming(self) -> bool:
        """HTML formatter does not support true streaming.

        Returns:
            False - streaming not supported (will buffer)
        """
        return False

    def _format_error_impl(self, error_msg: str) -> str:
        """Format error as HTML.

        Args:
            error_msg: The error message

        Returns:
            HTML formatted error (complete document)
        """
        parts = []
        parts.append(self._get_html_header())
        parts.append("<body>")
        parts.append('<div class="container">')
        parts.append("<h1>Error</h1>")
        parts.append('<div class="error">')
        parts.append(f"<p>❌ <strong>Error:</strong> {html.escape(error_msg)}</p>")
        parts.append("</div>")
        parts.append("</div>")
        parts.append("</body>")
        parts.append("</html>")
        return "\n".join(parts)

    def _format_metadata_impl(self, metadata: dict[str, Any]) -> str:
        """Format metadata as HTML.

        Args:
            metadata: Metadata dictionary

        Returns:
            HTML formatted metadata
        """
        parts = []
        parts.append('<div class="metadata">')
        parts.append('<div class="metadata-grid">')

        for key, value in metadata.items():
            formatted_key = key.replace("_", " ").title()
            parts.append(self._metadata_item(formatted_key, str(value)))

        parts.append("</div>")
        parts.append("</div>")
        return "\n".join(parts)
