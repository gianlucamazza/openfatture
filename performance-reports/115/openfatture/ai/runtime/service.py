"""Unified assistant runtime used by the public CLI.

This is the only product-supported orchestration path for natural-language
business operations. Interactive sessions optionally persist via the
file-backed session store.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.message import ConversationHistory, Message, Role
from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.streaming.events import StreamEvent
from openfatture.platform.config import DebugConfig, Settings, get_settings
from openfatture.platform.extras import require_extra
from openfatture.platform.logging import get_logger

logger = get_logger(__name__)


def _history_from_dicts(items: list[dict[str, str]] | None) -> ConversationHistory | None:
    if not items:
        return None
    history = ConversationHistory()
    for item in items:
        try:
            role = Role(item.get("role", "user"))
        except ValueError:
            role = Role.USER
        history.add_message(Message(role=role, content=item.get("content", "")))
    return history


class AssistantRuntime:
    """Single assistant entry used by ``openfatture assistant`` / interactive."""

    def __init__(
        self,
        *,
        provider: Any | None = None,
        settings: Settings | None = None,
        enable_streaming: bool = True,
        enable_tools: bool = True,
        debug_config: DebugConfig | None = None,
        session_id: str | None = None,
        persist_session: bool = False,
    ) -> None:
        require_extra("ai", feature="the business assistant")
        from openfatture.ai.agents.chat_agent import ChatAgent
        from openfatture.ai.providers.factory import create_provider

        self.settings = settings or get_settings()
        self._provider = provider or create_provider()
        self._agent = ChatAgent(
            provider=self._provider,
            enable_streaming=enable_streaming,
            enable_tools=enable_tools,
            debug_config=debug_config or self.settings.debug_config,
        )
        self.persist_session = persist_session
        self._session = None
        self._session_store = None
        if persist_session:
            from openfatture.ai.session import ChatSession, get_session_store

            self._session_store = get_session_store()
            if session_id:
                self._session = self._session_store.load(session_id)
            if self._session is None:
                self._session = ChatSession()
            logger.info("assistant_session_attached", session_id=self._session.id)

        logger.info(
            "assistant_runtime_ready",
            provider=self._provider.provider_name,
            model=getattr(self._provider, "model", None),
            backend="chat_agent_tool_loop",
            persist_session=persist_session,
        )

    @property
    def backend(self) -> str:
        """Orchestration backend identifier (stable for status/metrics)."""
        return "chat_agent_tool_loop"

    @property
    def session_id(self) -> str | None:
        return self._session.id if self._session is not None else None

    def _context(
        self,
        user_input: str,
        history: list[dict[str, str]] | ConversationHistory | None = None,
    ) -> ChatContext:
        conv: ConversationHistory | None
        if isinstance(history, ConversationHistory):
            conv = history
        elif history is not None:
            conv = _history_from_dicts(history)
        elif self._session is not None:
            # Rebuild history from persisted session messages
            conv = ConversationHistory()
            for msg in self._session.messages:
                conv.add_message(Message(role=msg.role, content=msg.content))
        else:
            conv = ConversationHistory()
        return ChatContext(user_input=user_input, conversation_history=conv)

    def _persist_turn(
        self, user_input: str, assistant_content: str, response: AgentResponse | None = None
    ) -> None:
        if not self.persist_session or self._session is None or self._session_store is None:
            return
        self._session.add_user_message(user_input)
        tokens = 0
        cost = 0.0
        if response is not None and response.usage is not None:
            tokens = response.usage.total_tokens
            cost = response.usage.estimated_cost_usd
        self._session.add_assistant_message(
            assistant_content,
            provider=getattr(self._provider, "provider_name", None),
            model=getattr(self._provider, "model", None),
            tokens=tokens,
            cost=cost,
        )
        self._session_store.save(self._session)
        logger.debug("assistant_session_saved", session_id=self._session.id)

    async def run(
        self,
        user_input: str,
        *,
        history: list[dict[str, str]] | ConversationHistory | None = None,
    ) -> AgentResponse:
        """Run one assistant turn and return a full response."""
        context = self._context(user_input, history)
        response = await self._agent.execute(context)
        self._persist_turn(user_input, response.content or "", response)
        return response

    async def stream(
        self,
        user_input: str,
        *,
        history: list[dict[str, str]] | ConversationHistory | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """Stream one assistant turn as typed stream events."""
        context = self._context(user_input, history)
        answer_parts: list[str] = []
        async for item in self._agent.execute_stream(context):
            if hasattr(item, "is_content") and item.is_content():
                answer_parts.append(item.get_text())
            yield item
        self._persist_turn(user_input, "".join(answer_parts), None)


def create_assistant_runtime(**kwargs: Any) -> AssistantRuntime:
    """Factory for :class:`AssistantRuntime`."""
    return AssistantRuntime(**kwargs)


async def run_assistant(
    user_input: str,
    *,
    history: list[dict[str, str]] | ConversationHistory | None = None,
    **kwargs: Any,
) -> AgentResponse:
    """Convenience one-shot run via the unified runtime."""
    runtime = create_assistant_runtime(**kwargs)
    return await runtime.run(user_input, history=history)


async def stream_assistant(
    user_input: str,
    *,
    history: list[dict[str, str]] | ConversationHistory | None = None,
    **kwargs: Any,
) -> AsyncIterator[StreamEvent]:
    """Convenience streaming run via the unified runtime."""
    runtime = create_assistant_runtime(**kwargs)
    async for item in runtime.stream(user_input, history=history):
        yield item
