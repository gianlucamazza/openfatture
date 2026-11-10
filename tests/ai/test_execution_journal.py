from pathlib import Path

import pytest

from openfatture.ai.runtime.durability import ExecutionJournal, UncertainToolOutcome


def test_receipt_survives_restart(tmp_path: Path) -> None:
    path = tmp_path / "journal.sqlite"
    journal = ExecutionJournal(path)
    assert journal.begin("turn:call", "create", {"amount": 12}) is None
    with pytest.raises(UncertainToolOutcome):
        ExecutionJournal(path).begin("turn:call", "create", {"amount": 12})
    journal.complete("turn:call", {"success": True, "id": 9})
    assert ExecutionJournal(path).begin("turn:call", "create", {"amount": 12}) == {
        "success": True,
        "id": 9,
    }
    with pytest.raises(ValueError):
        journal.begin("turn:call", "create", {"amount": 13})


def test_session_exclusion_and_release(tmp_path: Path) -> None:
    journal = ExecutionJournal(tmp_path / "journal.sqlite")
    with journal.session_lock("one"):
        with pytest.raises(RuntimeError):
            with journal.session_lock("one"):
                pytest.fail("overlapping execution")
        with journal.session_lock("two"):
            pass
    with journal.session_lock("one"):
        pass


@pytest.mark.asyncio
async def test_checkpoint_resume_does_not_repeat_completed_tool(tmp_path: Path) -> None:
    from unittest.mock import AsyncMock, MagicMock

    from openfatture.ai.domain.response import AgentResponse, ResponseStatus, ToolCall
    from openfatture.ai.runtime.durability import DurableToolExecutor
    from openfatture.ai.tools.models import ToolResult

    provider = MagicMock(provider_name="openai", supports_tools=True)
    requested = AgentResponse(
        content="",
        status=ResponseStatus.SUCCESS,
        tool_calls=[ToolCall(id="call1", name="create", arguments={})],
    )
    provider.generate = AsyncMock(side_effect=[requested, RuntimeError("connection lost")])
    registry = MagicMock()
    registry.get_openai_functions.return_value = []
    registry.execute_tool = AsyncMock(
        return_value=ToolResult(success=True, data={"id": 1}, tool_name="create")
    )
    with pytest.raises(RuntimeError, match="connection lost"):
        await DurableToolExecutor(tmp_path).run(
            session_id="s",
            turn_id="t",
            provider=provider,
            registry=registry,
            initial={"user_input": "create", "iteration": 0},
        )
    provider.generate = AsyncMock(
        return_value=AgentResponse(content="created", status=ResponseStatus.SUCCESS)
    )
    result = await DurableToolExecutor(tmp_path).run(
        session_id="s",
        turn_id="t",
        provider=provider,
        registry=registry,
        initial=None,
    )
    assert result["content"] == "created"
    assert registry.execute_tool.await_count == 1
    provider.generate.reset_mock()
    replay = await DurableToolExecutor(tmp_path).run(
        session_id="s",
        turn_id="t",
        provider=provider,
        registry=registry,
        initial=None,
    )
    assert replay == result
    provider.generate.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("decision", [True, False])
async def test_approval_survives_executor_restart(tmp_path: Path, decision: bool) -> None:
    from unittest.mock import AsyncMock, MagicMock

    from openfatture.ai.domain.response import AgentResponse, ResponseStatus, ToolCall
    from openfatture.ai.runtime.durability import DurableToolExecutor
    from openfatture.ai.tools.models import Tool, ToolResult

    provider = MagicMock(provider_name="openai", supports_tools=True)
    provider.generate = AsyncMock(
        side_effect=[
            AgentResponse(
                content="",
                status=ResponseStatus.SUCCESS,
                tool_calls=[ToolCall(id="c1", name="write", arguments={"value": 3})],
            ),
            AgentResponse(content="finished", status=ResponseStatus.SUCCESS),
        ]
    )
    registry = MagicMock()
    registry.get_openai_functions.return_value = []
    registry.get_tool.return_value = Tool(
        name="write", description="write", func=lambda: None, requires_confirmation=True
    )
    registry.confirmation_callback = None
    registry.execute_tool = AsyncMock(
        return_value=ToolResult(success=True, data=3, tool_name="write")
    )
    state = await DurableToolExecutor(tmp_path).run(
        session_id="s",
        turn_id="t",
        provider=provider,
        registry=registry,
        initial={"user_input": "write", "iteration": 0},
    )
    assert state["interrupted"]
    registry.execute_tool.assert_not_awaited()
    registry.confirmation_callback = AsyncMock(return_value=decision)
    result = await DurableToolExecutor(tmp_path).run(
        session_id="s",
        turn_id="t",
        provider=provider,
        registry=registry,
        initial=None,
    )
    assert result["content"] == "finished"
    registry.confirmation_callback.assert_awaited_once_with("write", {"value": 3})
    assert registry.execute_tool.await_count == int(decision)
    if decision:
        assert registry.execute_tool.await_args.kwargs["source"] == "human"
        assert registry.execute_tool.await_args.kwargs["confirmed"] is True


@pytest.mark.asyncio
async def test_durable_events_precede_tool_completion_and_cancel_releases_lock(
    tmp_path: Path,
) -> None:
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    from openfatture.ai.domain.response import AgentResponse, ResponseStatus, ToolCall
    from openfatture.ai.runtime.durability import DurableToolExecutor

    started = asyncio.Event()
    blocked = asyncio.Event()
    provider = MagicMock(provider_name="openai", supports_tools=True)
    provider.generate = AsyncMock(
        return_value=AgentResponse(
            content="",
            status=ResponseStatus.SUCCESS,
            tool_calls=[ToolCall(id="c1", name="slow", arguments={})],
        )
    )
    registry = MagicMock()
    registry.get_openai_functions.return_value = []
    registry.execute_tool = AsyncMock(side_effect=lambda **kwargs: None)

    async def slow(**kwargs):
        await blocked.wait()

    registry.execute_tool.side_effect = slow
    events = []

    def observe(event):
        events.append(event)
        if event.get("event") == "tool_start":
            started.set()

    executor = DurableToolExecutor(tmp_path)
    task = asyncio.create_task(
        executor.run(
            session_id="s",
            turn_id="t",
            provider=provider,
            registry=registry,
            initial={"user_input": "slow"},
            on_event=observe,
        )
    )
    await asyncio.wait_for(started.wait(), 5)
    assert not task.done()
    assert not any(e.get("event") == "tool_finished" for e in events)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    with executor.journal.session_lock("s"):
        pass
    with pytest.raises(UncertainToolOutcome):
        await executor.run(
            session_id="s", turn_id="t", provider=provider, registry=registry, initial=None
        )
    assert registry.execute_tool.await_count == 1


def test_reconcile_requires_matching_tool_and_evidence(tmp_path: Path) -> None:
    journal = ExecutionJournal(tmp_path / "journal.sqlite")
    journal.begin("s:t:1:c1", "send", {"id": 3})
    assert journal.unresolved("s:t")[0]["tool"] == "send"
    assert journal.unresolved("another") == []
    with pytest.raises(ValueError):
        journal.reconcile("s:t:1:c1", {"tool_name": "send", "success": True}, "")
    with pytest.raises(ValueError):
        journal.reconcile("s:t:1:c1", {"tool_name": "other", "success": True}, "checked")
    journal.reconcile(
        "s:t:1:c1",
        {"tool_name": "send", "success": True, "data": {"id": 3}},
        "Verified external receipt 123",
    )
    assert journal.unresolved("s:t") == []
    assert journal.begin("s:t:1:c1", "send", {"id": 3})["success"]
    with pytest.raises(ValueError):
        journal.reconcile("s:t:1:c1", {"tool_name": "send", "success": True}, "checked twice")


@pytest.mark.asyncio
async def test_effect_completed_before_receipt_failure_requires_reconciliation(
    tmp_path: Path,
) -> None:
    from unittest.mock import AsyncMock, MagicMock, patch

    from openfatture.ai.domain.response import AgentResponse, ToolCall
    from openfatture.ai.runtime.durability import DurableToolExecutor
    from openfatture.ai.tools.models import ToolResult

    provider = MagicMock(provider_name="openai", supports_tools=True)
    provider.generate = AsyncMock(
        side_effect=[
            AgentResponse(content="", tool_calls=[ToolCall(id="c", name="write", arguments={})]),
            AgentResponse(content="done"),
        ]
    )
    registry = MagicMock()
    registry.get_openai_functions.return_value = []
    registry.execute_tool = AsyncMock(
        return_value=ToolResult(tool_name="write", success=True, data={"id": 7})
    )
    executor = DurableToolExecutor(tmp_path)
    with patch.object(executor.journal, "complete", side_effect=OSError("disk unavailable")):
        with pytest.raises(UncertainToolOutcome):
            await executor.run(
                session_id="s",
                turn_id="t",
                provider=provider,
                registry=registry,
                initial={"user_input": "write"},
            )
    restarted = DurableToolExecutor(tmp_path)
    with pytest.raises(UncertainToolOutcome):
        await restarted.run(
            session_id="s", turn_id="t", provider=provider, registry=registry, initial=None
        )
    receipt = restarted.journal.unresolved("s:t")[0]
    restarted.journal.reconcile(
        receipt["call_id"],
        {"tool_name": "write", "success": True, "data": {"id": 7}},
        "Verified local record 7",
    )
    state = await restarted.run(
        session_id="s", turn_id="t", provider=provider, registry=registry, initial=None
    )
    assert state["content"] == "done"
    assert registry.execute_tool.await_count == 1


@pytest.mark.asyncio
async def test_tool_timeout_is_not_automatically_retried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    from openfatture.ai.domain.response import AgentResponse, ToolCall
    from openfatture.ai.runtime.durability import DurableToolExecutor
    from openfatture.ai.tools.models import Tool
    from openfatture.ai.tools.registry import ToolRegistry

    calls = 0

    async def slow():
        nonlocal calls
        calls += 1
        await asyncio.Event().wait()

    registry = ToolRegistry()
    registry.execution_timeout_seconds = 0.01
    monkeypatch.setattr(registry, "_get_cache", lambda: None)
    monkeypatch.setattr(registry, "_get_metrics", lambda: None)
    registry.register(Tool(name="slow", description="slow operation", func=slow))
    provider = MagicMock(provider_name="openai", supports_tools=True)
    provider.generate = AsyncMock(
        return_value=AgentResponse(
            content="",
            tool_calls=[ToolCall(id="c", name="slow", arguments={})],
        )
    )
    executor = DurableToolExecutor(tmp_path)
    with pytest.raises(UncertainToolOutcome):
        await executor.run(
            session_id="s",
            turn_id="t",
            provider=provider,
            registry=registry,
            initial={"user_input": "slow"},
        )
    with pytest.raises(UncertainToolOutcome):
        await executor.run(
            session_id="s", turn_id="t", provider=provider, registry=registry, initial=None
        )
    assert calls == 1
