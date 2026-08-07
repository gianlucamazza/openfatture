"""Unified assistant runtime is the product entrypoint."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics


@pytest.mark.asyncio
async def test_runtime_run_delegates_to_chat_agent() -> None:
    mock_response = AgentResponse(
        content="ok",
        status=ResponseStatus.SUCCESS,
        agent_name="chat",
        usage=UsageMetrics(total_tokens=1, estimated_cost_usd=0.0),
    )
    empty_registry = MagicMock(list_tools=MagicMock(return_value=[]))
    with (
        patch("openfatture.platform.extras.require_extra"),
        patch("openfatture.ai.providers.factory.create_provider") as mock_prov,
        patch("openfatture.ai.tools.registry.get_tool_registry", return_value=empty_registry),
        patch("openfatture.ai.runtime.service.ChatAgent") as mock_agent_cls,
    ):
        mock_prov.return_value = MagicMock(provider_name="openai", model="gpt", supports_tools=True)
        agent = MagicMock()
        agent.execute = AsyncMock(return_value=mock_response)
        mock_agent_cls.return_value = agent

        from openfatture.ai.runtime import create_assistant_runtime

        runtime = create_assistant_runtime()
        result = await runtime.run("lista fatture")
        assert result.content == "ok"
        agent.execute.assert_awaited_once()
        assert runtime.session_id is None
        assert runtime.backend == "chat_agent_tool_loop"


def test_build_assistant_graph_compiles() -> None:
    empty_registry = MagicMock(list_tools=MagicMock(return_value=[]))
    with (
        patch("openfatture.platform.extras.require_extra"),
        patch("openfatture.ai.providers.factory.create_provider") as mock_prov,
        patch("openfatture.ai.tools.registry.get_tool_registry", return_value=empty_registry),
        patch("openfatture.ai.runtime.service.ChatAgent"),
    ):
        mock_prov.return_value = MagicMock(
            provider_name="openai", model="gpt", supports_tools=False
        )
        from openfatture.ai.runtime import create_assistant_runtime
        from openfatture.ai.runtime.graph import build_assistant_graph

        runtime = create_assistant_runtime()
        graph = build_assistant_graph(runtime)
        assert graph is not None
        assert hasattr(graph, "ainvoke")


@pytest.mark.asyncio
async def test_runtime_persist_session_saves_and_reloads(tmp_path: Path) -> None:
    mock_response = AgentResponse(
        content="hello back",
        status=ResponseStatus.SUCCESS,
        agent_name="chat",
        usage=UsageMetrics(total_tokens=2, estimated_cost_usd=0.0),
    )
    empty_registry = MagicMock(list_tools=MagicMock(return_value=[]))
    with (
        patch("openfatture.platform.extras.require_extra"),
        patch("openfatture.ai.providers.factory.create_provider") as mock_prov,
        patch("openfatture.ai.tools.registry.get_tool_registry", return_value=empty_registry),
        patch("openfatture.ai.runtime.service.ChatAgent") as mock_agent_cls,
        patch("openfatture.ai.session.get_session_store") as mock_store_factory,
    ):
        from openfatture.ai.session.file_store import FileSessionStore

        store = FileSessionStore(sessions_dir=tmp_path)
        mock_store_factory.return_value = store
        mock_prov.return_value = MagicMock(provider_name="openai", model="gpt")
        agent = MagicMock()
        agent.execute = AsyncMock(return_value=mock_response)
        mock_agent_cls.return_value = agent

        from openfatture.ai.runtime import create_assistant_runtime

        runtime = create_assistant_runtime(persist_session=True)
        assert runtime.session_id is not None
        sid = runtime.session_id
        await runtime.run("hi")

        loaded = store.load(sid)
        assert loaded is not None
        assert len(loaded.messages) >= 2

        runtime2 = create_assistant_runtime(persist_session=True, session_id=sid)
        assert runtime2.session_id == sid
        await runtime2.run("again")
        reloaded = store.load(sid)
        assert reloaded is not None
        assert len(reloaded.messages) >= 4
