"""Single source of truth for assistant backend names and stable backend ids.

Core CLI (status) and the AI runtime both import from here so mapping never
drifts. Does not import the AI package.
"""

from __future__ import annotations

from typing import Final, Literal

AssistantBackendName = Literal["chat", "langgraph"]

ASSISTANT_BACKEND_CHAT: Final[Literal["chat"]] = "chat"
ASSISTANT_BACKEND_LANGGRAPH: Final[Literal["langgraph"]] = "langgraph"

# Stable ids for status/metrics (do not rename lightly)
BACKEND_CHAT: Final = "chat_agent_tool_loop"
BACKEND_LANGGRAPH: Final = "langgraph_tool_loop"

DEFAULT_ASSISTANT_BACKEND: Final[AssistantBackendName] = ASSISTANT_BACKEND_LANGGRAPH

BACKEND_IDS: Final[dict[str, str]] = {
    ASSISTANT_BACKEND_CHAT: BACKEND_CHAT,
    ASSISTANT_BACKEND_LANGGRAPH: BACKEND_LANGGRAPH,
}


def resolve_backend_id(assistant_backend: str) -> str:
    """Map settings ``assistant_backend`` to the stable backend id string."""
    key = (assistant_backend or DEFAULT_ASSISTANT_BACKEND).strip().lower()
    if key == ASSISTANT_BACKEND_LANGGRAPH:
        return BACKEND_LANGGRAPH
    if key == ASSISTANT_BACKEND_CHAT:
        return BACKEND_CHAT
    raise ValueError(
        f"Unknown assistant_backend={assistant_backend!r}; expected one of {sorted(BACKEND_IDS)}"
    )
