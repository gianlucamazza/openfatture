"""Execution gates of the tool registry: lookup, enablement, rate limit, cache, activity."""

from typing import Any

import pytest

from openfatture.ai.tools.models import Tool, ToolResult
from openfatture.ai.tools.registry import ToolRegistry
from openfatture.platform.rate_limiter import RateLimiter


class _Metrics:
    def __init__(self) -> None:
        self.recorded: list[ToolResult] = []

    def record_execution(self, result: ToolResult) -> None:
        self.recorded.append(result)


class _Cache:
    def __init__(self) -> None:
        self.stored: dict[str, ToolResult] = {}

    def is_cacheable(self, tool_name: str) -> bool:
        return True

    async def get_cached_result(
        self, tool_name: str, parameters: dict[str, Any]
    ) -> ToolResult | None:
        return self.stored.get(tool_name)

    async def cache_result(
        self, tool_name: str, parameters: dict[str, Any], result: ToolResult
    ) -> None:
        self.stored[tool_name] = result


def _echo(value: str = "ok") -> str:
    return value


def _registry(
    monkeypatch: pytest.MonkeyPatch, *tools: Tool, cache: _Cache | None = None
) -> tuple[ToolRegistry, _Metrics]:
    registry = ToolRegistry()
    for tool in tools:
        registry.register(tool)
    metrics = _Metrics()
    monkeypatch.setattr(registry, "_get_cache", lambda: cache)
    monkeypatch.setattr(registry, "_get_metrics", lambda: metrics)
    return registry, metrics


@pytest.mark.asyncio
async def test_unknown_tool_is_reported_and_recorded(monkeypatch):
    registry, metrics = _registry(monkeypatch)
    result = await registry.execute_tool("missing_tool", {})
    assert (result.success, result.error) == (False, "Tool 'missing_tool' not found")
    assert metrics.recorded == [result]


@pytest.mark.asyncio
async def test_disabled_tool_is_refused(monkeypatch):
    tool = Tool(name="echo_tool", description="echo", func=_echo, enabled=False)
    registry, metrics = _registry(monkeypatch, tool)
    result = await registry.execute_tool("echo_tool", {})
    assert (result.error, result.error_type) == ("Tool 'echo_tool' is disabled", "tool_disabled")
    assert metrics.recorded == [result]


@pytest.mark.asyncio
async def test_rate_limit_refuses_extra_calls(monkeypatch):
    registry, metrics = _registry(
        monkeypatch, Tool(name="echo_tool", description="echo", func=_echo)
    )
    registry._rate_limiters["echo_tool"] = RateLimiter(max_calls=1, period=60)
    assert (await registry.execute_tool("echo_tool", {})).success
    limited = await registry.execute_tool("echo_tool", {})
    assert limited.success is False
    assert "rate limit" in (limited.error or "")
    assert metrics.recorded[-1] is limited


@pytest.mark.asyncio
async def test_activity_is_announced_and_results_are_cached(monkeypatch):
    cache = _Cache()
    registry, metrics = _registry(
        monkeypatch, Tool(name="echo_tool", description="echo", func=_echo), cache=cache
    )
    announced: list[str] = []

    async def activity(name: str) -> None:
        announced.append(name)

    registry.activity_callback = activity
    first = await registry.execute_tool("echo_tool", {"value": "hi"})
    assert first.success and first.data == "hi"
    assert cache.stored["echo_tool"] is first
    second = await registry.execute_tool("echo_tool", {"value": "hi"})
    assert second is first
    assert announced == ["echo_tool"]
    assert metrics.recorded == [first, first]
