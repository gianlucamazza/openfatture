"""Tool history must remain valid for OpenAI-compatible chat APIs."""

import json

import pytest

from openfatture.ai.domain.message import Message, Role
from openfatture.ai.providers.openai_payload import build_chat_messages


@pytest.mark.parametrize("arguments", [{}, {"anno": 2026}, '{"anno": 2026}'])
@pytest.mark.parametrize("nested", [False, True])
def test_dict_tool_arguments_are_json_strings(arguments, nested):
    tool = {"id": "call_1", "name": "search_invoices", "arguments": arguments}
    if nested:
        tool = {
            "id": "call_1",
            "type": "function",
            "function": {"name": "search_invoices", "arguments": arguments},
        }
    messages = [
        Message(role=Role.USER, content="Synthetic invoice query"),
        Message(role=Role.ASSISTANT, content="", tool_calls=[tool]),
        Message(role=Role.TOOL, content='{"count": 0}', tool_call_id="call_1"),
    ]
    payload = build_chat_messages(messages, None)
    encoded = payload[1]["tool_calls"][0]["function"]["arguments"]
    assert isinstance(encoded, str)
    assert json.loads(encoded) == (
        json.loads(arguments) if isinstance(arguments, str) else arguments
    )
    assert payload[2]["content"] == '{"count": 0}'
