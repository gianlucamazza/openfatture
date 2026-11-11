"""Protected tools must never run before approval."""

from unittest.mock import AsyncMock

import pytest

from openfatture.ai.tools.models import Tool
from openfatture.ai.tools.registry import ToolRegistry


@pytest.mark.asyncio
@pytest.mark.parametrize("approval", [None, False, True])
async def test_protected_tool_requires_approval(approval):
    called = []

    def action():
        called.append(True)
        return "ok"

    registry = ToolRegistry()
    registry.register(
        Tool(name="protected_test", description="test", func=action, requires_confirmation=True)
    )
    if approval is not None:
        registry.confirmation_callback = AsyncMock(return_value=approval)
    result = await registry.execute_tool("protected_test", {}, confirm=False)
    assert bool(called) == (approval is True)
    assert result.success == (approval is True)


@pytest.mark.asyncio
async def test_denials_do_not_consume_concurrency_slots():
    registry = ToolRegistry()
    registry.register(
        Tool(
            name="protected_test", description="test", func=lambda: None, requires_confirmation=True
        )
    )
    registry.confirmation_callback = AsyncMock(return_value=False)
    bulkhead = registry.get_bulkhead("protected_test")
    for _ in range(bulkhead.config.max_concurrent_executions + 2):
        result = await registry.execute_tool("protected_test", {})
        assert result.error_type == "confirmation_denied"
        assert (bulkhead.active, bulkhead.queued) == (0, 0)


@pytest.mark.asyncio
async def test_cache_hits_do_not_consume_concurrency_slots():
    from unittest.mock import Mock

    from openfatture.ai.tools.models import ToolResult

    registry = ToolRegistry()
    registry.register(Tool(name="get_test", description="test", func=lambda: None))
    registry._cache = Mock()
    registry._cache.is_cacheable.return_value = True
    registry._cache.get_cached_result = AsyncMock(
        return_value=ToolResult(success=True, tool_name="get_test")
    )
    bulkhead = registry.get_bulkhead("get_test")
    for _ in range(3):
        assert (await registry.execute_tool("get_test", {})).success
        assert (bulkhead.active, bulkhead.queued) == (0, 0)


@pytest.mark.asyncio
async def test_callback_cannot_change_approved_execution_parameters():
    actual = []
    registry = ToolRegistry()
    registry.register(
        Tool(
            name="protected_test",
            description="test",
            func=lambda payload: actual.append(payload["amount"]),
            requires_confirmation=True,
        )
    )

    async def approve(name, parameters):
        parameters["payload"]["amount"] = 999
        return True

    registry.confirmation_callback = approve
    parameters = {"payload": {"amount": 10}}
    assert (await registry.execute_tool("protected_test", parameters)).success
    assert actual == [10]
    assert parameters == {"payload": {"amount": 10}}
