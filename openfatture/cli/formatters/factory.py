"""Formatter factory for creating formatter instances."""

from typing import Literal

from openfatture.cli.formatters.base import BaseFormatter

# Format type literal for type checking
FormatType = Literal["json", "markdown", "stream-json", "html", "rich"]


class FormatterFactory:
    """Factory for creating formatter instances based on format type."""

    _formatters: dict[str, type[BaseFormatter]] = {}

    @classmethod
    def register(cls, format_type: str, formatter_class: type[BaseFormatter]) -> None:
        """Register a formatter class for a format type.

        Args:
            format_type: The format type identifier (e.g., "json", "markdown")
            formatter_class: The formatter class to register
        """
        cls._formatters[format_type.lower()] = formatter_class

    @classmethod
    def get_formatter(cls, format_type: str) -> BaseFormatter:
        """Get a formatter instance for the specified format type.

        Args:
            format_type: The format type identifier

        Returns:
            Formatter instance

        Raises:
            ValueError: If format type is not supported
        """
        formatter_class = cls._formatters.get(format_type.lower())
        if formatter_class is None:
            supported = ", ".join(cls._formatters.keys())
            raise ValueError(
                f"Unsupported format type: {format_type}. " f"Supported types: {supported}"
            )
        return formatter_class()

    @classmethod
    def get_supported_formats(cls) -> list[str]:
        """Get list of supported format types.

        Returns:
            List of supported format type identifiers
        """
        return list(cls._formatters.keys())


def get_formatter(format_type: str = "rich") -> BaseFormatter:
    """Convenience function to get a formatter instance.

    Args:
        format_type: The format type identifier (default: "rich")

    Returns:
        Formatter instance

    Raises:
        ValueError: If format type is not supported
    """
    return FormatterFactory.get_formatter(format_type)


# Auto-register formatters when this module is imported
def _register_default_formatters() -> None:
    """Register all default formatters."""
    from openfatture.cli.formatters.html import HTMLFormatter
    from openfatture.cli.formatters.json import JSONFormatter
    from openfatture.cli.formatters.markdown import MarkdownFormatter
    from openfatture.cli.formatters.rich_formatter import RichFormatter
    from openfatture.cli.formatters.stream_json import StreamJSONFormatter

    FormatterFactory.register("json", JSONFormatter)
    FormatterFactory.register("rich", RichFormatter)
    FormatterFactory.register("markdown", MarkdownFormatter)
    FormatterFactory.register("stream-json", StreamJSONFormatter)
    FormatterFactory.register("html", HTMLFormatter)


_register_default_formatters()
