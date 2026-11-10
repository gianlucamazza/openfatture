"""Application refusals ({"error": ...}) are failed tool calls, not faults."""

import pytest
from sqlalchemy.exc import OperationalError

from openfatture.ai.tools.models import Tool
from openfatture.ai.tools.registry.core import ToolRegistry


def _refuse(fattura_id: int) -> dict[str, object]:
    return {"error": f"Invoice {fattura_id} not found", "error_code": "not_found"}


def _crash() -> None:
    raise OperationalError("SELECT * FROM fatture", {}, Exception("no such table: fatture"))


@pytest.mark.asyncio
async def test_error_dict_is_a_failed_result():
    result = await Tool(name="get_invoice", description="t", func=_refuse).execute(fattura_id=7)
    assert result.success is False
    assert result.error == "Invoice 7 not found"
    assert result.error_type == "not_found"
    assert result.data == {"error": "Invoice 7 not found", "error_code": "not_found"}


@pytest.mark.asyncio
async def test_refusals_are_not_cached_and_do_not_open_the_circuit(monkeypatch):
    registry = ToolRegistry()
    registry.register(Tool(name="get_invoice_details", description="t", func=_refuse))
    monkeypatch.setattr(registry, "_get_metrics", lambda: None)
    cache = registry._get_cache()
    for _ in range(10):
        result = await registry.execute_tool("get_invoice_details", {"fattura_id": 7})
        assert result.success is False and result.cache_hit is False
    assert result.circuit_breaker_state == "closed"
    if cache is not None:
        assert await cache.get_cached_result("get_invoice_details", {"fattura_id": 7}) is None


@pytest.mark.asyncio
async def test_exception_text_does_not_leak_sql():
    result = await Tool(name="crash", description="t", func=_crash).execute()
    assert result.success is False
    assert result.error is not None and "SQL" not in result.error
