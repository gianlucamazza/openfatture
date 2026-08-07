"""AI command events.

Events emitted during AI agent execution (describe, suggest-vat, forecast, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import BaseEvent


@dataclass(frozen=True)
class AICommandStartedEvent(BaseEvent):
    """Event emitted when an AI command execution begins.

    Triggered before LLM provider invocation.

    Hook point: pre-ai-command
    """

    command: str  # describe, suggest-vat, forecast, check, create-invoice, chat
    user_input: str
    provider: str  # openai, anthropic, ollama
    model: str
    parameters: dict[str, Any] | None = None


@dataclass(frozen=True)
class AICommandCompletedEvent(BaseEvent):
    """Event emitted when an AI command execution completes.

    Triggered after LLM response received and processed.

    Hook point: post-ai-command
    """

    command: str
    success: bool
    tokens_used: int
    cost_usd: float
    latency_ms: float
    error: str | None = None
    response_length: int | None = None
