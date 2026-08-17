"""Base formatter interface for CLI output."""

from abc import ABC, abstractmethod
from typing import Any

from openfatture.ai.domain.response import AgentResponse


class BaseFormatter(ABC):
    """Abstract base class for output formatters.

    All formatters must implement the format_response method and declare
    whether they support streaming output.
    """

    @abstractmethod
    def format_response(self, response: AgentResponse) -> str:
        """Format a complete AgentResponse into output string.

        Args:
            response: The AgentResponse to format

        Returns:
            Formatted string representation of the response
        """
        pass

    @abstractmethod
    def format_stream_chunk(self, chunk: str) -> str:
        """Format a streaming chunk of response content.

        Args:
            chunk: A chunk of response content from streaming

        Returns:
            Formatted string representation of the chunk
        """
        pass

    @abstractmethod
    def supports_streaming(self) -> bool:
        """Check if this formatter supports streaming output.

        Returns:
            True if streaming is supported, False otherwise
        """
        pass

    def format_error(self, error: Exception | str) -> str:
        """Format an error message.

        Args:
            error: Exception or error message string

        Returns:
            Formatted error message
        """
        error_msg = str(error) if isinstance(error, Exception) else error
        return self._format_error_impl(error_msg)

    def _format_error_impl(self, error_msg: str) -> str:
        """Internal error formatting implementation.

        Subclasses can override this for custom error formatting.

        Args:
            error_msg: The error message string

        Returns:
            Formatted error message
        """
        return f"Error: {error_msg}"

    def format_metadata(self, metadata: dict[str, Any]) -> str:
        """Format metadata (usage, cost, etc.).

        Args:
            metadata: Dictionary of metadata key-value pairs

        Returns:
            Formatted metadata string
        """
        return self._format_metadata_impl(metadata)

    def _format_metadata_impl(self, metadata: dict[str, Any]) -> str:
        """Internal metadata formatting implementation.

        Subclasses can override this for custom metadata formatting.

        Args:
            metadata: Dictionary of metadata key-value pairs

        Returns:
            Formatted metadata string
        """
        lines = []
        for key, value in metadata.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
