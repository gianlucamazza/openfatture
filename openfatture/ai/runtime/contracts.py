"""Session-scoped interaction and accounting contracts; independent of any UI."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Protocol

from openfatture.ai.domain.response import AgentResponse, UsageMetrics


class AssistantInteraction(Protocol):
    async def confirm(self, name: str, parameters: dict[str, Any]) -> bool: ...
    async def activity(self, name: str) -> None: ...
    async def finished(self, name: str, success: bool) -> None: ...


@dataclass
class TurnAccounting:
    usage: UsageMetrics = field(default_factory=UsageMetrics)
    calls: int = 0
    incomplete: bool = False
    tool_outcomes: list[dict[str, Any]] = field(default_factory=list)

    def record(self, response: AgentResponse) -> None:
        self.calls += 1
        if not response.success and response.usage.total_tokens == 0:
            self.incomplete = True
        for name in ("prompt_tokens", "completion_tokens", "total_tokens", "estimated_cost_usd"):
            setattr(self.usage, name, getattr(self.usage, name) + getattr(response.usage, name))
        self.usage.cost_known = self.usage.cost_known and response.usage.cost_known


current_accounting: ContextVar[TurnAccounting | None] = ContextVar(
    "assistant_accounting", default=None
)
ConfirmCallback = Callable[[str, dict[str, Any]], Awaitable[bool]]
ActivityCallback = Callable[[str], Awaitable[None]]


class AccountedProvider:
    """Delegate provider capabilities, recording each completed request exactly once."""

    def __init__(self, provider: Any):
        self.provider = provider
        from openfatture.platform.logging import register_sensitive_values

        credential = getattr(provider, "api_key", None)
        if isinstance(credential, str):
            register_sensitive_values(credential)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.provider, name)

    async def generate(self, *args: Any, **kwargs: Any) -> AgentResponse:
        accounting = current_accounting.get()
        try:
            response = await self.provider.generate(*args, **kwargs)
        except BaseException:
            if accounting is not None:
                accounting.incomplete = True
            raise
        if accounting is not None:
            accounting.record(response)
        return response
