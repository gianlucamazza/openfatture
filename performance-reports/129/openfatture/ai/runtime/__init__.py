"""Product assistant runtime — single entry for CLI and interactive mode.

All user-facing assistant flows MUST go through this package. Multi-agent
LangGraph workflows under ``ai.orchestration.workflows`` are internal/experimental
and are not registered on the public CLI.

Import ``constants`` for backend ids without constructing a runtime.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from openfatture.ai.runtime.constants import (
    ASSISTANT_BACKEND_CHAT,
    ASSISTANT_BACKEND_LANGGRAPH,
    BACKEND_CHAT,
    BACKEND_LANGGRAPH,
    AssistantBackendName,
    resolve_backend_id,
)

if TYPE_CHECKING:
    from openfatture.ai.runtime.service import AssistantRuntime

__all__ = [
    "ASSISTANT_BACKEND_CHAT",
    "ASSISTANT_BACKEND_LANGGRAPH",
    "BACKEND_CHAT",
    "BACKEND_LANGGRAPH",
    "AssistantBackendName",
    "AssistantRuntime",
    "create_assistant_runtime",
    "resolve_backend_id",
    "run_assistant",
    "stream_assistant",
]


def __getattr__(name: str) -> Any:
    """Lazy-load heavy runtime symbols so ``constants`` imports stay light."""
    if name in {
        "AssistantRuntime",
        "create_assistant_runtime",
        "run_assistant",
        "stream_assistant",
    }:
        from openfatture.ai.runtime import service as _service

        return getattr(_service, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
