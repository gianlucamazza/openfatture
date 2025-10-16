"""Output formatters for AI command responses.

This module provides various output formatters for CLI responses:
- JSON: Pretty-printed JSON format
- Markdown: Rich markdown with formatting
- StreamJSON: JSON Lines format for streaming
- HTML: Styled HTML output
"""

from openfatture.cli.formatters.base import BaseFormatter
from openfatture.cli.formatters.factory import FormatterFactory, get_formatter

__all__ = ["BaseFormatter", "FormatterFactory", "get_formatter"]
