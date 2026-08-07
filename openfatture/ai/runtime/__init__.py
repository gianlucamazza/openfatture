"""Product assistant runtime — single entry for CLI and interactive mode.

All user-facing assistant flows MUST go through this package. Multi-agent
LangGraph workflows under ``ai.orchestration.workflows`` are internal/experimental
and are not registered on the public CLI.
"""

from openfatture.ai.runtime.service import (
    AssistantRuntime,
    create_assistant_runtime,
    run_assistant,
    stream_assistant,
)

__all__ = [
    "AssistantRuntime",
    "create_assistant_runtime",
    "run_assistant",
    "stream_assistant",
]
