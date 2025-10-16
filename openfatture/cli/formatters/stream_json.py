"""Streaming JSON Lines formatter."""

import json
from typing import Any

from openfatture.ai.domain.response import AgentResponse
from openfatture.cli.formatters.base import BaseFormatter


class StreamJSONFormatter(BaseFormatter):
    """Formatter that outputs responses as JSON Lines (JSONL) format.

    This formatter is designed for streaming scenarios where each chunk
    is output as a separate JSON object on its own line. This format
    is ideal for real-time processing and log analysis.

    Format:
        {"type": "chunk", "content": "chunk text", "index": 0}
        {"type": "chunk", "content": "more text", "index": 1}
        {"type": "complete", "status": "success", "total_chunks": 2}
    """

    def __init__(self, ensure_ascii: bool = False):
        """Initialize StreamJSON formatter.

        Args:
            ensure_ascii: If True, escape non-ASCII characters (default: False)
        """
        self.ensure_ascii = ensure_ascii
        self.chunk_index = 0

    def format_response(self, response: AgentResponse) -> str:
        """Format complete AgentResponse as JSON Lines.

        When formatting a complete response (non-streaming), outputs:
        1. Content as a single chunk
        2. Metadata as separate line
        3. Complete marker

        Args:
            response: The AgentResponse to format

        Returns:
            JSONL string representation
        """
        lines = []

        # Error case
        if response.status.value == "error":
            error_obj = {
                "type": "error",
                "error": response.error or "Unknown error",
                "status": response.status.value,
            }
            return json.dumps(error_obj, ensure_ascii=self.ensure_ascii)

        # Content line
        content_obj = {
            "type": "chunk",
            "content": response.content,
            "index": 0,
        }
        lines.append(json.dumps(content_obj, ensure_ascii=self.ensure_ascii))

        # Metadata line
        metadata_obj = {
            "type": "metadata",
            "provider": response.provider,
            "model": response.model,
            "tokens": response.usage.total_tokens if response.usage else 0,
            "cost_usd": response.usage.estimated_cost_usd if response.usage else 0.0,
            "latency_ms": response.latency_ms,
            "status": response.status.value,
        }
        lines.append(json.dumps(metadata_obj, ensure_ascii=self.ensure_ascii))

        # Complete marker
        complete_obj = {
            "type": "complete",
            "status": response.status.value,
            "total_chunks": 1,
        }
        lines.append(json.dumps(complete_obj, ensure_ascii=self.ensure_ascii))

        return "\n".join(lines)

    def format_stream_chunk(self, chunk: str) -> str:
        """Format a streaming chunk as JSON Line.

        Each chunk is formatted as a separate JSON object with:
        - type: "chunk"
        - content: the chunk text
        - index: sequential chunk number

        Args:
            chunk: A chunk of response content

        Returns:
            JSONL formatted chunk with newline
        """
        chunk_obj = {
            "type": "chunk",
            "content": chunk,
            "index": self.chunk_index,
        }
        self.chunk_index += 1
        return json.dumps(chunk_obj, ensure_ascii=self.ensure_ascii) + "\n"

    def format_stream_complete(
        self,
        status: str = "success",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Format stream completion marker.

        Call this after all chunks have been streamed to indicate
        completion and provide metadata.

        Args:
            status: Completion status (default: "success")
            metadata: Optional metadata dictionary

        Returns:
            JSONL formatted completion marker
        """
        complete_obj = {
            "type": "complete",
            "status": status,
            "total_chunks": self.chunk_index,
        }
        if metadata:
            complete_obj["metadata"] = metadata

        # Reset chunk index for next stream
        self.chunk_index = 0

        return json.dumps(complete_obj, ensure_ascii=self.ensure_ascii) + "\n"

    def supports_streaming(self) -> bool:
        """StreamJSON formatter supports streaming.

        Returns:
            True - streaming is fully supported
        """
        return True

    def _format_error_impl(self, error_msg: str) -> str:
        """Format error as JSON Line.

        Args:
            error_msg: The error message

        Returns:
            JSONL formatted error
        """
        error_obj = {
            "type": "error",
            "error": error_msg,
            "status": "error",
        }
        return json.dumps(error_obj, ensure_ascii=self.ensure_ascii)

    def _format_metadata_impl(self, metadata: dict[str, Any]) -> str:
        """Format metadata as JSON Line.

        Args:
            metadata: Metadata dictionary

        Returns:
            JSONL formatted metadata
        """
        metadata_obj = {
            "type": "metadata",
            **metadata,
        }
        return json.dumps(metadata_obj, ensure_ascii=self.ensure_ascii)
