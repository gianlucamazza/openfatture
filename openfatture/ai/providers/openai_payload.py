"""Mapping between OpenFatture messages and the OpenAI Chat Completions payload.

Outgoing: messages and tool-call history to API messages, filtered extra
parameters. Incoming: tool calls from a completion and from streamed deltas.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from typing import Any

from openfatture.ai.domain.message import Message, Role
from openfatture.ai.domain.response import ToolCall
from openfatture.platform.logging import get_logger

logger = get_logger(__name__)

ALLOWED_EXTRA_PARAMS = frozenset(
    {
        "tools",
        "tool_choice",
        "parallel_tool_calls",
        "metadata",
        "top_p",
        "top_logprobs",
        "logprobs",
        "max_tokens",
        "store",
        "user",
        "stream_options",
        "response_format",
        "reasoning_effort",  # GPT-5 reasoning control: "low", "medium", "high", or "none"
    }
)


def filter_extra_params(params: dict[str, Any]) -> dict[str, Any]:
    """Keep only the keyword arguments the Chat Completions API accepts."""
    return {key: value for key, value in params.items() if key in ALLOWED_EXTRA_PARAMS}


def _history_tool_call(tool_call: ToolCall | dict[str, Any]) -> dict[str, Any]:
    """An assistant tool call as API history; arguments are always a JSON string."""
    if isinstance(tool_call, ToolCall):
        return {
            "id": tool_call.id,
            "type": "function",
            "function": {
                "name": tool_call.name,
                "arguments": (
                    json.dumps(tool_call.arguments)
                    if isinstance(tool_call.arguments, dict)
                    else tool_call.arguments
                ),
            },
        }
    function = tool_call.get("function", {})
    arguments = function.get("arguments")
    if arguments is None:
        arguments = tool_call.get("arguments", {})
    if not isinstance(arguments, str):
        arguments = json.dumps(arguments, ensure_ascii=False)
    return {
        "id": tool_call.get("id") or tool_call.get("call_id"),
        "type": "function",
        "function": {
            "name": function.get("name") or tool_call.get("name"),
            "arguments": arguments,
        },
    }


def build_chat_messages(messages: list[Message], system_prompt: str | None) -> list[dict[str, Any]]:
    """Convert internal messages into Chat Completions API messages."""
    chat_messages: list[dict[str, Any]] = []

    if system_prompt:
        chat_messages.append({"role": "system", "content": system_prompt})

    for message in messages:
        if message.role == Role.SYSTEM:
            # System messages are handled via system_prompt, skip duplicates
            continue

        if message.role == Role.USER:
            chat_messages.append({"role": "user", "content": message.content})
            continue

        if message.role == Role.ASSISTANT:
            assistant_msg: dict[str, Any] = {"role": "assistant"}
            if message.content:
                assistant_msg["content"] = message.content
            tool_calls = [
                _history_tool_call(tool_call)
                for tool_call in message.tool_calls or []
                if isinstance(tool_call, ToolCall | dict)
            ]
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            chat_messages.append(assistant_msg)
            continue

        if message.role == Role.TOOL:
            if not message.tool_call_id:
                logger.warning(
                    "tool_message_missing_id",
                    message="Skipping tool message without tool_call_id",
                )
                continue
            chat_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": message.tool_call_id,
                    "content": message.content,
                }
            )

    return chat_messages


def parse_tool_calls(api_tool_calls: Iterable[Any] | None) -> list[ToolCall]:
    """Tool calls of a completion message; invalid JSON arguments raise ValueError."""
    tool_calls: list[ToolCall] = []
    for tool_call in api_tool_calls or []:
        try:
            arguments = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            logger.warning(
                "tool_call_arguments_parse_failed",
                tool_name=tool_call.function.name,
                arguments=tool_call.function.arguments,
            )
            raise ValueError("Invalid tool arguments") from None
        tool_calls.append(
            ToolCall(id=tool_call.id, name=tool_call.function.name, arguments=arguments)
        )
    return tool_calls


class StreamedToolCalls:
    """Accumulates tool-call deltas of a streamed completion by index."""

    def __init__(self) -> None:
        self._buffer: list[dict[str, Any]] = []

    def add(self, deltas: Iterable[Any]) -> None:
        """Merge the tool-call deltas of one stream chunk."""
        for delta in deltas:
            while len(self._buffer) <= delta.index:
                self._buffer.append(
                    {"id": "", "type": "function", "function": {"name": "", "arguments": ""}}
                )
            tool_call = self._buffer[delta.index]
            if delta.id:
                tool_call["id"] = delta.id
            if delta.function:
                if delta.function.name:
                    tool_call["function"]["name"] += delta.function.name
                if delta.function.arguments:
                    tool_call["function"]["arguments"] += delta.function.arguments

    def complete(self) -> Iterator[ToolCall]:
        """Yield the accumulated tool calls; invalid JSON arguments raise ValueError."""
        for data in self._buffer:
            try:
                arguments = json.loads(data["function"]["arguments"])
            except json.JSONDecodeError:
                logger.warning(
                    "tool_call_arguments_stream_parse_failed",
                    tool_name=data["function"]["name"],
                    arguments=data["function"]["arguments"],
                )
                raise ValueError("Invalid streamed tool arguments") from None
            yield ToolCall(
                id=data["id"],
                name=data["function"]["name"] or "unknown_tool",
                arguments=arguments,
            )
