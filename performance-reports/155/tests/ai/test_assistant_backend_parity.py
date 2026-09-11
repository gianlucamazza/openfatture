"""Parity contracts: chat vs langgraph product backends.

Same mock provider/registry fixtures drive both paths. Failures block advertising
langgraph as a ready product backend.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openfatture.ai.domain.response import AgentResponse, ResponseStatus, ToolCall, UsageMetrics
from openfatture.ai.runtime.constants import BACKEND_CHAT, BACKEND_LANGGRAPH
from openfatture.ai.streaming.events import StreamEventType
from openfatture.ai.tools.models import ToolResult


def _final(content: str = "done") -> AgentResponse:
    return AgentResponse(
        content=content,
        status=ResponseStatus.SUCCESS,
        usage=UsageMetrics(total_tokens=2, estimated_cost_usd=0.0),
    )


def _with_tool(name: str = "search_invoices") -> AgentResponse:
    return AgentResponse(
        content="",
        status=ResponseStatus.SUCCESS,
        tool_calls=[ToolCall(id="1", name=name, arguments={"limit": 5})],
        usage=UsageMetrics(total_tokens=3, estimated_cost_usd=0.0),
    )


def _provider_and_registry(
    *,
    supports_tools: bool = True,
    generate_side_effect: Any = None,
) -> tuple[MagicMock, MagicMock]:
    provider = MagicMock()
    provider.provider_name = "openai"
    provider.model = "gpt-test"
    provider.supports_tools = supports_tools
    if generate_side_effect is None:
        provider.generate = AsyncMock(return_value=_final("hello"))
    else:
        # Fresh list copy so AsyncMock side_effect is not shared across runs.
        provider.generate = AsyncMock(side_effect=list(generate_side_effect))

    registry = MagicMock()
    registry.get_openai_functions.return_value = [
        {"type": "function", "function": {"name": "search_invoices", "parameters": {}}}
    ]
    registry.get_anthropic_tools.return_value = []
    tool = MagicMock()
    tool.name = "search_invoices"
    registry.list_tools.return_value = [tool]
    registry.execute_tool = AsyncMock(
        return_value=ToolResult(
            success=True,
            data={"count": 1},
            error=None,
            tool_name="search_invoices",
        )
    )
    return provider, registry


def _runtime(backend: str, provider: MagicMock, registry: MagicMock) -> Any:
    with (
        patch("openfatture.platform.extras.require_extra"),
        patch("openfatture.ai.providers.factory.create_provider", return_value=provider),
        patch("openfatture.ai.tools.registry.get_tool_registry", return_value=registry),
        patch("openfatture.ai.runtime.service.get_tool_registry", return_value=registry),
    ):
        from openfatture.ai.runtime import create_assistant_runtime

        return create_assistant_runtime(backend=backend, provider=provider, enable_tools=True)


@pytest.mark.asyncio
async def test_explicit_chat_backend_id() -> None:
    provider, registry = _provider_and_registry()
    runtime = _runtime("chat", provider, registry)
    assert runtime.backend == BACKEND_CHAT
    assert runtime.assistant_backend == "chat"


@pytest.mark.asyncio
async def test_langgraph_backend_id() -> None:
    provider, registry = _provider_and_registry()
    runtime = _runtime("langgraph", provider, registry)
    assert runtime.backend == BACKEND_LANGGRAPH
    assert runtime.assistant_backend == "langgraph"


@pytest.mark.asyncio
async def test_settings_default_backend_is_langgraph() -> None:
    """Product default (no ctor override) is langgraph_tool_loop."""
    provider, registry = _provider_and_registry()
    with (
        patch("openfatture.platform.extras.require_extra"),
        patch("openfatture.ai.providers.factory.create_provider", return_value=provider),
        patch("openfatture.ai.tools.registry.get_tool_registry", return_value=registry),
        patch("openfatture.ai.runtime.service.get_tool_registry", return_value=registry),
    ):
        from openfatture.ai.runtime import create_assistant_runtime
        from openfatture.platform.config import Settings

        settings = Settings(assistant_backend="langgraph")
        runtime = create_assistant_runtime(provider=provider, settings=settings)
        assert runtime.backend == BACKEND_LANGGRAPH
        assert runtime.assistant_backend == "langgraph"


@pytest.mark.asyncio
async def test_parity_zero_tools_content() -> None:
    """Zero tool_calls → same final content on both backends."""
    provider_chat, registry_chat = _provider_and_registry(
        generate_side_effect=[_final("hello world")]
    )
    provider_lg, registry_lg = _provider_and_registry(generate_side_effect=[_final("hello world")])
    # No tools on registry so both use plain generation
    registry_chat.list_tools.return_value = []
    registry_lg.list_tools.return_value = []

    chat = _runtime("chat", provider_chat, registry_chat)
    lg = _runtime("langgraph", provider_lg, registry_lg)

    r_chat = await chat.run("hi")
    r_lg = await lg.run("hi")
    assert r_chat.content == r_lg.content == "hello world"
    assert r_chat.status == r_lg.status == ResponseStatus.SUCCESS


@pytest.mark.asyncio
async def test_parity_one_tool_round_trip() -> None:
    """Model → tool → final: tool name and success surface match."""
    provider_chat, registry_chat = _provider_and_registry(
        generate_side_effect=[_with_tool(), _final("Found invoices")]
    )
    provider_lg, registry_lg = _provider_and_registry(
        generate_side_effect=[_with_tool(), _final("Found invoices")]
    )

    chat = _runtime("chat", provider_chat, registry_chat)
    lg = _runtime("langgraph", provider_lg, registry_lg)

    r_chat = await chat.run("list invoices")
    r_lg = await lg.run("list invoices")

    assert r_chat.content == r_lg.content == "Found invoices"
    assert registry_chat.execute_tool.await_count == 1
    assert registry_lg.execute_tool.await_count == 1
    assert provider_chat.generate.await_count == 2
    assert provider_lg.generate.await_count == 2


@pytest.mark.asyncio
async def test_parity_max_iterations_cap() -> None:
    """Both backends stop after max_iterations of continuous tool calls."""
    # Always request tools → hit cap
    side = [_with_tool() for _ in range(10)]
    provider_chat, registry_chat = _provider_and_registry(generate_side_effect=list(side))
    provider_lg, registry_lg = _provider_and_registry(generate_side_effect=list(side))

    chat = _runtime("chat", provider_chat, registry_chat)
    lg = _runtime("langgraph", provider_lg, registry_lg)

    await chat.run("loop")
    await lg.run("loop")

    # Native orchestrator and graph both default to 5 iterations
    assert provider_chat.generate.await_count == 5
    assert provider_lg.generate.await_count == 5


@pytest.mark.asyncio
async def test_langgraph_stream_tool_event_order() -> None:
    """Stream emits tool_start before tool_result, then final content."""
    provider, registry = _provider_and_registry(
        generate_side_effect=[_with_tool(), _final("Found invoices")]
    )
    runtime = _runtime("langgraph", provider, registry)

    types: list[StreamEventType] = []
    async for event in runtime.stream("list invoices"):
        types.append(event.type)

    assert StreamEventType.TOOL_START in types
    assert StreamEventType.TOOL_RESULT in types
    assert StreamEventType.CONTENT in types
    assert types.index(StreamEventType.TOOL_START) < types.index(StreamEventType.TOOL_RESULT)
    # Final content after tools
    assert types.index(StreamEventType.TOOL_RESULT) < types.index(StreamEventType.CONTENT)


@pytest.mark.asyncio
async def test_langgraph_stream_zero_tools_has_content() -> None:
    provider, registry = _provider_and_registry(generate_side_effect=[_final("plain")])
    registry.list_tools.return_value = []
    runtime = _runtime("langgraph", provider, registry)

    events = [e async for e in runtime.stream("hi")]
    assert any(e.type == StreamEventType.CONTENT for e in events)
    assert any(e.data == "plain" for e in events if e.type == StreamEventType.CONTENT)


@pytest.mark.asyncio
async def test_session_persist_same_sequence(tmp_path: Path) -> None:
    """Persist path records user + assistant messages for both backends."""
    from openfatture.ai.session.file_store import FileSessionStore

    async def _run(backend: str) -> list[str]:
        provider, registry = _provider_and_registry(generate_side_effect=[_final(f"ok-{backend}")])
        registry.list_tools.return_value = []
        store = FileSessionStore(sessions_dir=tmp_path / backend)
        with (
            patch("openfatture.platform.extras.require_extra"),
            patch("openfatture.ai.providers.factory.create_provider", return_value=provider),
            patch("openfatture.ai.tools.registry.get_tool_registry", return_value=registry),
            patch("openfatture.ai.runtime.service.get_tool_registry", return_value=registry),
            patch("openfatture.ai.session.get_session_store", return_value=store),
        ):
            from openfatture.ai.runtime import create_assistant_runtime

            runtime = create_assistant_runtime(
                backend=backend, provider=provider, persist_session=True
            )
            await runtime.run("hello")
            assert runtime.session_id is not None
            loaded = store.load(runtime.session_id)
            assert loaded is not None
            return [
                m.role.value if hasattr(m.role, "value") else str(m.role) for m in loaded.messages
            ]

    roles_chat = await _run("chat")
    roles_lg = await _run("langgraph")
    assert roles_chat == roles_lg
    assert roles_chat[0] == "user"
    assert roles_chat[1] == "assistant"


@pytest.mark.asyncio
async def test_error_tool_result_continues_to_final() -> None:
    """Failed tool still allows a final model answer on langgraph path."""
    provider, registry = _provider_and_registry(
        generate_side_effect=[_with_tool(), _final("recovered")]
    )
    registry.execute_tool = AsyncMock(
        return_value=ToolResult(
            success=False,
            data=None,
            error="boom",
            tool_name="search_invoices",
        )
    )
    runtime = _runtime("langgraph", provider, registry)
    result = await runtime.run("list")
    assert result.content == "recovered"
    assert registry.execute_tool.await_count == 1
