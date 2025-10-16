"""JSON output formatter."""

import json
from typing import Any

from openfatture.ai.domain.response import AgentResponse
from openfatture.cli.formatters.base import BaseFormatter


class JSONFormatter(BaseFormatter):
    """Formatter that outputs responses as pretty-printed JSON.

    This formatter leverages the AgentResponse.to_dict() method and
    produces indented JSON output suitable for both human reading
    and machine parsing.
    """

    def __init__(self, indent: int = 2, ensure_ascii: bool = False):
        """Initialize JSON formatter.

        Args:
            indent: Number of spaces for indentation (default: 2)
            ensure_ascii: If True, escape non-ASCII characters (default: False)
        """
        self.indent = indent
        self.ensure_ascii = ensure_ascii

    def format_response(self, response: AgentResponse) -> str:
        """Format AgentResponse as pretty-printed JSON.

        Args:
            response: The AgentResponse to format

        Returns:
            JSON string representation
        """
        data = response.to_dict()
        return json.dumps(data, indent=self.indent, ensure_ascii=self.ensure_ascii)

    def format_stream_chunk(self, chunk: str) -> str:
        """Format streaming chunk (not supported for standard JSON).

        For standard JSON, streaming is not supported as we need the complete
        response to generate valid JSON. Use StreamJSONFormatter for streaming.

        Args:
            chunk: A chunk of response content

        Returns:
            The chunk as-is (will be buffered)
        """
        # Return chunk as-is for buffering
        return chunk

    def supports_streaming(self) -> bool:
        """Standard JSON does not support streaming.

        Returns:
            False - streaming not supported
        """
        return False

    def _format_error_impl(self, error_msg: str) -> str:
        """Format error as JSON.

        Args:
            error_msg: The error message

        Returns:
            JSON formatted error
        """
        error_data = {"error": error_msg, "status": "error"}
        return json.dumps(error_data, indent=self.indent, ensure_ascii=self.ensure_ascii)

    def _format_metadata_impl(self, metadata: dict[str, Any]) -> str:
        """Format metadata as JSON.

        Args:
            metadata: Metadata dictionary

        Returns:
            JSON formatted metadata
        """
        return json.dumps(metadata, indent=self.indent, ensure_ascii=self.ensure_ascii)
