"""Stable identifiers and shared constants for the assistant runtime."""

from __future__ import annotations

from typing import Final, Literal

# Product backend ids (status/metrics; stable contract)
BACKEND_CHAT: Final = "chat_agent_tool_loop"
BACKEND_LANGGRAPH: Final = "langgraph_tool_loop"

# Settings values map to backend ids (Literal keeps mypy/runtime aligned)
AssistantBackendName = Literal["chat", "langgraph"]
ASSISTANT_BACKEND_CHAT: Final[Literal["chat"]] = "chat"
ASSISTANT_BACKEND_LANGGRAPH: Final[Literal["langgraph"]] = "langgraph"

DEFAULT_TOOL_MAX_ITERATIONS: Final[int] = 5

BACKEND_IDS: Final[dict[str, str]] = {
    ASSISTANT_BACKEND_CHAT: BACKEND_CHAT,
    ASSISTANT_BACKEND_LANGGRAPH: BACKEND_LANGGRAPH,
}


def resolve_backend_id(assistant_backend: str) -> str:
    """Map settings ``assistant_backend`` to the stable backend id string."""
    key = (assistant_backend or ASSISTANT_BACKEND_CHAT).strip().lower()
    if key == ASSISTANT_BACKEND_LANGGRAPH:
        return BACKEND_LANGGRAPH
    if key == ASSISTANT_BACKEND_CHAT:
        return BACKEND_CHAT
    raise ValueError(
        f"Unknown assistant_backend={assistant_backend!r}; expected one of {sorted(BACKEND_IDS)}"
    )
