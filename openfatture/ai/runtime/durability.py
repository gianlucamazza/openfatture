"""Local execution leases and durable receipts for tool side effects.

An unfinished receipt is deliberately not retryable: a lost response does not
prove that the business operation failed.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class UncertainToolOutcome(RuntimeError):
    """An operation started but its completion has not been reconciled."""


class ExecutionJournal:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        from contextlib import closing

        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS receipts "
                "(call_id TEXT PRIMARY KEY, payload TEXT NOT NULL, result TEXT)"
            )
            yield conn

    @contextmanager
    def session_lock(self, session_id: str) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        name = hashlib.sha256(session_id.encode()).hexdigest()
        with (self.path.parent / f"{name}.lock").open("a") as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RuntimeError("Session already executing") from exc
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def begin(self, call_id: str, tool: str, parameters: dict[str, Any]) -> Any:
        """Return a completed result or reserve a new call before execution."""
        payload = json.dumps([tool, parameters], sort_keys=True, ensure_ascii=False)
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT payload, result FROM receipts WHERE call_id = ?", (call_id,)
            ).fetchone()
            if row is not None:
                if row[0] != payload:
                    raise ValueError("Call identity reused with different parameters")
                if row[1] is None:
                    raise UncertainToolOutcome(call_id)
                return json.loads(row[1])
            conn.execute("INSERT INTO receipts VALUES (?, ?, NULL)", (call_id, payload))
        return None

    def complete(self, call_id: str, result: dict[str, Any]) -> None:
        encoded = json.dumps(result, ensure_ascii=False)
        with self.connection() as conn:
            changed = conn.execute(
                "UPDATE receipts SET result = ? WHERE call_id = ? AND result IS NULL",
                (encoded, call_id),
            ).rowcount
            if changed != 1:
                raise ValueError("Receipt missing or already completed")

    def unresolved(self, thread_id: str) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT call_id, payload FROM receipts WHERE result IS NULL"
            ).fetchall()
        return [
            {
                "call_id": call_id,
                "tool": json.loads(payload)[0],
                "parameters": json.loads(payload)[1],
            }
            for call_id, payload in rows
            if call_id.startswith(thread_id + ":")
        ]

    def reconcile(self, call_id: str, result: dict[str, Any], evidence: str) -> None:
        """Store a human-verified outcome and its evidence atomically."""
        from openfatture.ai.tools.models import ToolResult

        if not evidence.strip():
            raise ValueError("Reconciliation requires evidence")
        verified = ToolResult.model_validate(result)
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT payload, result FROM receipts WHERE call_id = ?", (call_id,)
            ).fetchone()
            if row is None or row[1] is not None:
                raise ValueError("No unresolved receipt")
            if json.loads(row[0])[0] != verified.tool_name:
                raise ValueError("Reconciled tool does not match receipt")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS reconciliations "
                "(call_id TEXT PRIMARY KEY, evidence TEXT NOT NULL, "
                "recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )
            conn.execute(
                "INSERT INTO reconciliations (call_id, evidence) VALUES (?, ?)", (call_id, evidence)
            )
            conn.execute(
                "UPDATE receipts SET result = ? WHERE call_id = ?",
                (verified.model_dump_json(), call_id),
            )


class DurableToolExecutor:
    """Own the SQLite connection for one graph invocation, including failures."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.journal = ExecutionJournal(directory / "executions.sqlite")

    async def run(
        self,
        *,
        session_id: str,
        turn_id: str,
        provider: Any,
        registry: Any,
        initial: Any,
        on_event: Any = None,
        **options: Any,
    ) -> dict[str, Any]:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

        from openfatture.ai.runtime.graph import build_tool_loop_graph

        with self.journal.session_lock(session_id):
            async with AsyncSqliteSaver.from_conn_string(
                str(self.directory / "checkpoints.sqlite")
            ) as saver:
                graph = build_tool_loop_graph(
                    provider=provider,
                    tool_registry=registry,
                    checkpointer=saver,
                    journal=self.journal,
                    **options,
                )
                config = {
                    "configurable": {"thread_id": f"{session_id}:{turn_id}"},
                    "recursion_limit": 2 * options.get("max_iterations", 5) + 2,
                }
                snapshot = await graph.aget_state(config)
                # Existing checkpoints always take precedence over caller input.
                # Checkpoints are written synchronously (durability="sync") so an
                # abrupt exit never loses a completed step.
                if snapshot.values:
                    if not snapshot.next:
                        return dict(snapshot.values)
                    initial = None
                from langgraph.types import Command

                while True:
                    if snapshot.interrupts:
                        payload = snapshot.interrupts[0].value
                        callback = registry.confirmation_callback
                        if callback is None:
                            state = dict(snapshot.values)
                            state["interrupted"] = True
                            state["pending_approval"] = payload
                            return state
                        decision = await callback(payload["tool"], payload["parameters"])
                        initial = Command(resume=decision is True)
                    if on_event is None:
                        result = dict(
                            await graph.ainvoke(initial, config=config, durability="sync")
                        )
                    else:
                        async for event in graph.astream(
                            initial,
                            config=config,
                            stream_mode="custom",
                            version="v2",
                            durability="sync",
                        ):
                            on_event(event["data"])
                        result = dict((await graph.aget_state(config)).values)
                    snapshot = await graph.aget_state(config)
                    if not snapshot.interrupts:
                        return result
                    initial = None
