"""Runtime constants — re-exports platform SSOT for assistant backends.

Prefer importing from ``openfatture.platform.assistant_backends`` in core code.
AI modules may keep using this path for convenience.
"""

from __future__ import annotations

from typing import Final

from openfatture.platform.assistant_backends import (
    ASSISTANT_BACKEND_CHAT,
    ASSISTANT_BACKEND_LANGGRAPH,
    BACKEND_CHAT,
    BACKEND_IDS,
    BACKEND_LANGGRAPH,
    DEFAULT_ASSISTANT_BACKEND,
    AssistantBackendName,
    resolve_backend_id,
)

DEFAULT_TOOL_MAX_ITERATIONS: Final[int] = 5

__all__ = [
    "ASSISTANT_BACKEND_CHAT",
    "ASSISTANT_BACKEND_LANGGRAPH",
    "AssistantBackendName",
    "BACKEND_CHAT",
    "BACKEND_IDS",
    "BACKEND_LANGGRAPH",
    "DEFAULT_ASSISTANT_BACKEND",
    "DEFAULT_TOOL_MAX_ITERATIONS",
    "resolve_backend_id",
]
