"""Reindex queue must not simulate indexing without a real callback."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from openfatture.ai.rag.auto_update.queue import ReindexQueue
from openfatture.ai.rag.auto_update.tracker import ChangeType, EntityChange


def _change(entity_id: int, change_type: ChangeType) -> EntityChange:
    return EntityChange(
        entity_type="invoice",
        entity_id=entity_id,
        change_type=change_type,
        timestamp=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_process_entity_type_requires_callback() -> None:
    queue = ReindexQueue(reindex_callback=None)
    with pytest.raises(RuntimeError, match="no reindex_callback"):
        await queue._process_entity_type("invoice", [_change(1, ChangeType.UPDATE)])


@pytest.mark.asyncio
async def test_process_entity_type_invokes_callback() -> None:
    seen: list[list[EntityChange]] = []

    async def cb(changes: list[EntityChange]) -> None:
        seen.append(list(changes))

    queue = ReindexQueue(reindex_callback=cb)
    await queue._process_entity_type("invoice", [_change(2, ChangeType.CREATE)])
    assert len(seen) == 1
    assert seen[0][0].entity_id == 2
