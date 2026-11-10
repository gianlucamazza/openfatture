"""The bulkhead reports the callers really waiting for a slot."""

import asyncio

import pytest

from openfatture.ai.orchestration.resilience import BulkheadConfig
from openfatture.ai.tools.models import Tool, ToolRisk
from openfatture.ai.tools.registry import ToolRegistry
from openfatture.ai.tools.registry.resilience import Bulkhead, bulkhead_config_for


async def _settle() -> None:
    for _ in range(5):
        await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_bulkhead_counts_waiting_and_active_callers():
    bulkhead = Bulkhead(BulkheadConfig(max_concurrent_executions=1))
    assert await bulkhead.acquire()
    waiters = [asyncio.create_task(bulkhead.acquire()) for _ in range(2)]
    await _settle()
    assert (bulkhead.active, bulkhead.queued) == (1, 2)

    bulkhead.release()
    await _settle()
    assert (bulkhead.active, bulkhead.queued) == (1, 1)

    bulkhead.release()
    await _settle()
    assert (bulkhead.active, bulkhead.queued) == (1, 0)
    assert all(await asyncio.gather(*waiters))
    bulkhead.release()
    assert (bulkhead.active, bulkhead.queued) == (0, 0)


@pytest.mark.asyncio
async def test_bulkhead_timeout_leaves_the_queue():
    bulkhead = Bulkhead(
        BulkheadConfig(max_concurrent_executions=1, acquisition_timeout_seconds=0.01)
    )
    assert await bulkhead.acquire()
    assert not await bulkhead.acquire()
    assert (bulkhead.active, bulkhead.queued) == (1, 0)


@pytest.mark.asyncio
async def test_tool_results_report_real_queue_depth(monkeypatch):
    monkeypatch.setattr(
        "openfatture.ai.tools.registry.core.bulkhead_config_for",
        lambda _name: BulkheadConfig(max_concurrent_executions=1, acquisition_timeout_seconds=5),
    )
    gate = asyncio.Event()

    async def slow() -> str:
        await gate.wait()
        return "ok"

    registry = ToolRegistry()
    registry.register(Tool(name="slow_tool", description="test", func=slow))
    monkeypatch.setattr(registry, "_get_cache", lambda: None)
    monkeypatch.setattr(registry, "_get_metrics", lambda: None)

    calls = [asyncio.create_task(registry.execute_tool("slow_tool", {})) for _ in range(3)]
    await _settle()
    bulkhead = registry.get_bulkhead("slow_tool")
    assert (bulkhead.active, bulkhead.queued) == (1, 2)

    gate.set()
    results = await asyncio.gather(*calls)
    assert all(result.success for result in results)
    # Each finishing call sees the callers still waiting behind it.
    assert sorted(result.bulkhead_queue_length or 0 for result in results) == [0, 1, 2]
    assert (bulkhead.active, bulkhead.queued) == (0, 0)


@pytest.mark.asyncio
async def test_rejected_call_reports_waiters(monkeypatch):
    monkeypatch.setattr(
        "openfatture.ai.tools.registry.core.bulkhead_config_for",
        lambda _name: BulkheadConfig(max_concurrent_executions=1, acquisition_timeout_seconds=0.05),
    )
    gate = asyncio.Event()

    async def slow() -> str:
        await gate.wait()
        return "ok"

    registry = ToolRegistry()
    registry.register(Tool(name="slow_tool", description="test", func=slow))
    monkeypatch.setattr(registry, "_get_cache", lambda: None)
    monkeypatch.setattr(registry, "_get_metrics", lambda: None)

    holder = asyncio.create_task(registry.execute_tool("slow_tool", {}))
    await _settle()
    rejected = await registry.execute_tool("slow_tool", {})
    assert rejected.error_type == "bulkhead_limit_exceeded"
    assert rejected.bulkhead_queue_length == 0
    gate.set()
    assert (await holder).success


def test_bulkhead_config_by_tool_kind():
    assert bulkhead_config_for(ToolRisk.READ).max_concurrent_executions == 10
    assert bulkhead_config_for(ToolRisk.MUTATE).max_concurrent_executions == 2
    assert bulkhead_config_for(ToolRisk.LOCAL_ARTIFACT).max_concurrent_executions == 2
    assert bulkhead_config_for(None) == BulkheadConfig()
