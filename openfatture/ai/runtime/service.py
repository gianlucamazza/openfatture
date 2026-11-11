"""Unified assistant runtime used by the public CLI.

This is the only product-supported orchestration path for natural-language
business operations. Interactive sessions optionally persist via the
file-backed session store.

Backends (settings ``assistant_backend``):
- ``langgraph`` → GraphAssistantBackend (default product path)
- ``chat`` → ChatAgent rollback (delegates tool loop to the same graph backend)
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from contextlib import ExitStack, contextmanager
from typing import TYPE_CHECKING, Any, cast

from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.message import ConversationHistory, Message, Role
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.ai.providers.factory import create_provider
from openfatture.ai.runtime.constants import (
    ASSISTANT_BACKEND_CHAT,
    ASSISTANT_BACKEND_LANGGRAPH,
    AssistantBackendName,
    resolve_backend_id,
)
from openfatture.ai.runtime.contracts import (
    AccountedProvider,
    AssistantInteraction,
    TurnAccounting,
    current_accounting,
)
from openfatture.ai.streaming.events import StreamEvent
from openfatture.ai.tools.registry import get_tool_registry
from openfatture.platform.config import DebugConfig, Settings, get_settings
from openfatture.platform.extras import require_extra
from openfatture.platform.logging import get_logger

if TYPE_CHECKING:
    from openfatture.ai.agents.chat_agent import ChatAgent
    from openfatture.ai.runtime.graph_backend import GraphAssistantBackend
    from openfatture.ai.session.models import ChatSession
    from openfatture.ai.session.store import SessionStore

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


def _resolve_backend_name(
    backend: AssistantBackendName | None, settings: Settings
) -> AssistantBackendName:
    """Map ctor override or settings to a validated backend name."""
    if backend is not None:
        if backend == ASSISTANT_BACKEND_CHAT:
            return ASSISTANT_BACKEND_CHAT
        return ASSISTANT_BACKEND_LANGGRAPH
    if settings.assistant_backend == ASSISTANT_BACKEND_CHAT:
        return ASSISTANT_BACKEND_CHAT
    return ASSISTANT_BACKEND_LANGGRAPH


class AssistantRuntime:
    """Single assistant entry used by ``openfatture`` (chat and ``-m`` requests)."""

    def __init__(
        self,
        *,
        provider: BaseLLMProvider | None = None,
        settings: Settings | None = None,
        enable_streaming: bool = True,
        enable_tools: bool = True,
        debug_config: DebugConfig | None = None,
        session_id: str | None = None,
        persist_session: bool = False,
        backend: AssistantBackendName | None = None,
        interaction: AssistantInteraction | None = None,
    ) -> None:
        require_extra("ai", feature="the business assistant")

        self.settings = settings or get_settings()
        self._provider = cast(BaseLLMProvider, AccountedProvider(provider or create_provider()))
        self.enable_tools = enable_tools
        self.enable_streaming = enable_streaming
        self.debug_config = debug_config or self.settings.debug_config
        from copy import copy

        self._tool_registry = copy(get_tool_registry())
        self._tool_registry.execution_timeout_seconds = self.settings.ai_tool_timeout_seconds
        self._tool_registry.confirmation_callback = interaction.confirm if interaction else None
        self._tool_registry.activity_callback = interaction.activity if interaction else None
        self._tool_registry.outcome_callback = interaction.finished if interaction else None
        self.last_response: AgentResponse | None = None
        self.total_usage = UsageMetrics()
        self.turn_count = 0

        self._backend_name = _resolve_backend_name(backend, self.settings)
        self._backend_id = resolve_backend_id(self._backend_name)

        self._agent: ChatAgent | None = None
        self._graph_backend: GraphAssistantBackend | None = None

        if self._backend_name == ASSISTANT_BACKEND_CHAT:
            from openfatture.ai.agents.chat_agent import ChatAgent

            self._agent = ChatAgent(
                provider=self._provider,
                tool_registry=self._tool_registry,
                enable_streaming=enable_streaming,
                enable_tools=enable_tools,
                debug_config=self.debug_config,
            )
        else:
            from openfatture.ai.runtime.graph_backend import GraphAssistantBackend

            self._graph_backend = GraphAssistantBackend(
                model_timeout_seconds=self.settings.ai_model_timeout_seconds,
                temperature=self.settings.ai_temperature,
                max_tokens=self.settings.ai_max_tokens,
                provider=self._provider,
                tool_registry=self._tool_registry,
                enable_tools=enable_tools,
                debug_config=self.debug_config,
            )

        self.persist_session = persist_session
        self._session: ChatSession | None = None
        self._session_store: SessionStore | None = None
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
            model=self._provider.model,
            backend=self._backend_id,
            assistant_backend=self._backend_name,
            persist_session=persist_session,
        )

    @property
    def backend(self) -> str:
        """Orchestration backend identifier (stable for status/metrics)."""
        return self._backend_id

    @property
    def assistant_backend(self) -> AssistantBackendName:
        """Settings-level backend name (``chat`` | ``langgraph``)."""
        return self._backend_name

    @property
    def session_id(self) -> str | None:
        return self._session.id if self._session is not None else None

    @property
    def pending_user_input(self) -> str | None:
        return self._session.pending_user_input if self._session else None

    async def resume(self) -> AgentResponse:
        if self.pending_user_input is None:
            raise ValueError("No pending turn")
        return await self.run(self.pending_user_input)

    def uncertain_tools(self) -> list[dict[str, Any]]:
        from openfatture.ai.runtime.durability import ExecutionJournal

        if self._session is None or self._session.pending_turn_id is None:
            return []
        journal = ExecutionJournal(self.settings.data_dir / "ai" / "runtime" / "executions.sqlite")
        return journal.unresolved(f"{self._session.id}:{self._session.pending_turn_id}")

    def reconcile_tool(self, call_id: str, result: dict[str, Any], evidence: str) -> None:
        from openfatture.ai.runtime.durability import ExecutionJournal

        if self._session is None:
            raise ValueError("Reconciliation requires a persistent session")
        journal = ExecutionJournal(self.settings.data_dir / "ai" / "runtime" / "executions.sqlite")
        with self._session_guard(), journal.session_lock(self._session.id):
            if call_id not in {entry["call_id"] for entry in self.uncertain_tools()}:
                raise ValueError("Receipt does not belong to this pending turn")
            journal.reconcile(call_id, result, evidence)

    @contextmanager
    def _session_guard(self) -> Iterator[None]:
        from openfatture.ai.runtime.durability import ExecutionJournal

        if self._session is None or self._session_store is None:
            yield
            return
        journal = ExecutionJournal(self.settings.data_dir / "ai" / "runtime" / "executions.sqlite")
        with journal.session_lock("runtime:" + self._session.id):
            latest = self._session_store.load(self._session.id)
            if latest is not None:
                self._session = latest
            yield

    def _context(
        self,
        user_input: str,
        history: list[dict[str, str]] | ConversationHistory | None = None,
    ) -> ChatContext:
        conv: ConversationHistory
        if isinstance(history, ConversationHistory):
            conv = history
        elif history is not None:
            conv = _history_from_dicts(history) or ConversationHistory()
        elif self._session is not None:
            from openfatture.ai.runtime.history import trim_history

            stored = [
                Message(role=msg.role, content=msg.content)
                for msg in self._session.messages
                if msg.role in (Role.USER, Role.ASSISTANT)
            ]
            # Built directly: trim_history is the only cut, so the
            # ConversationHistory message cap does not drop more.
            conv = ConversationHistory(messages=trim_history(stored), max_messages=10_000)
        else:
            conv = ConversationHistory()
        context = ChatContext(user_input=user_input, conversation_history=conv)
        if self._session is not None and self._graph_backend is not None:
            import uuid

            if self._session.pending_turn_id and self._session.pending_user_input != user_input:
                raise ValueError("A pending turn must be resumed before a new message")
            if not self._session.pending_turn_id:
                self._session.pending_turn_id = str(uuid.uuid4())
                self._session.pending_user_input = user_input
                if self._session_store and not self._session_store.save(self._session):
                    raise RuntimeError("Unable to persist pending turn")
            context.session_id = self._session.id
            context.metadata["turn_id"] = self._session.pending_turn_id
            context.metadata["checkpoint_directory"] = str(
                self.settings.data_dir / "ai" / "runtime"
            )
        from openfatture.ai.memory import get_memory_store

        context.memory_notes = [(note.id, note.text) for note in get_memory_store().entries()]
        if self.enable_tools and not context.available_tools:
            context.available_tools = [t.name for t in self._tool_registry.list_tools()]
            context.disabled_capabilities = self._tool_registry.disabled_capabilities()
        return context

    def _persist_turn(
        self, user_input: str, assistant_content: str, response: AgentResponse | None = None
    ) -> None:
        if not self.persist_session or self._session is None or self._session_store is None:
            return
        original = self._session
        self._session = original.model_copy(deep=True)
        self._session.pending_turn_id = None
        self._session.pending_user_input = None
        self._session.add_user_message(user_input)
        tokens = 0
        cost = 0.0
        if response is not None and response.usage is not None:
            tokens = response.usage.total_tokens
            cost = response.usage.estimated_cost_usd
        self._session.add_assistant_message(
            assistant_content,
            provider=self._provider.provider_name,
            model=self._provider.model,
            tokens=tokens,
            cost=cost,
            prompt_tokens=response.usage.prompt_tokens if response else 0,
            completion_tokens=response.usage.completion_tokens if response else 0,
            metadata={
                "status": response.status.value,
                "error": response.error,
                "usage": response.usage.model_dump(),
                **response.metadata,
            }
            if response
            else {},
        )
        try:
            if not self._session_store.save(self._session):
                raise RuntimeError("Unable to persist completed turn")
        except Exception:
            self._session = original
            raise
        logger.debug("assistant_session_saved", session_id=self._session.id)

    def clear_session(self) -> bool:
        with self._session_guard():
            if self._session is None:
                return False
            if self._session.pending_turn_id:
                raise ValueError("Resume or reconcile the pending turn before clearing history")
            self._session.clear_messages()
            if self._session_store and not self._session_store.save(self._session):
                raise RuntimeError("Unable to save cleared history")
            return True

    def _finish_turn(
        self, user_input: str, response: AgentResponse, accounting: TurnAccounting
    ) -> None:
        response.provider = response.provider or self._provider.provider_name
        response.model = response.model or self._provider.model
        if accounting.calls and response.usage.total_tokens <= accounting.usage.total_tokens:
            response.usage = accounting.usage.model_copy(deep=True)
        if accounting.incomplete or not accounting.calls:
            response.metadata["usage_complete"] = False
        else:
            response.metadata["usage_complete"] = True
        billed = accounting.usage
        for name in ("prompt_tokens", "completion_tokens", "total_tokens", "estimated_cost_usd"):
            setattr(
                self.total_usage,
                name,
                getattr(self.total_usage, name) + getattr(billed, name),
            )
        self.total_usage.cost_known &= billed.cost_known
        response.metadata["tool_outcomes"] = accounting.tool_outcomes
        self.last_response = response
        if response.metadata.get("interrupted") or (self._session and accounting.incomplete):
            return
        self.turn_count += 1
        from openfatture.events import get_global_event_bus
        from openfatture.events.ai_events import AITurnCompletedEvent
        from openfatture.storage.database import base as database

        if database.SessionLocal is not None:
            get_global_event_bus().publish(
                AITurnCompletedEvent(
                    status=response.status.value,
                    tokens_used=response.usage.total_tokens,
                    cost_usd=response.usage.estimated_cost_usd,
                    cost_known=response.usage.cost_known,
                    usage_complete=response.metadata["usage_complete"],
                    tool_outcomes=accounting.tool_outcomes,
                    error=response.error,
                )
            )
        if not accounting.incomplete and not response.metadata.get("interrupted"):
            self._persist_turn(user_input, response.content, response)

    async def run(
        self, user_input: str, *, history: list[dict[str, str]] | ConversationHistory | None = None
    ) -> AgentResponse:
        import asyncio

        lease = ExitStack()
        lease.enter_context(self._session_guard())
        accounting = TurnAccounting()
        token = current_accounting.set(accounting)
        response = AgentResponse(
            content="", status=ResponseStatus.PARTIAL, usage=UsageMetrics(cost_known=False)
        )
        try:
            context = self._context(user_input, history)
            if self._graph_backend is not None:
                response = await self._graph_backend.run(context)
            elif self._agent is not None:
                response = await self._agent.execute(context)
            else:
                raise RuntimeError("AssistantRuntime has no configured backend")
            return response
        except BaseException as exc:
            response.status = (
                ResponseStatus.PARTIAL
                if isinstance(exc, (asyncio.CancelledError, KeyboardInterrupt))
                else ResponseStatus.ERROR
            )
            response.error = type(exc).__name__
            accounting.incomplete = True
            raise
        finally:
            try:
                self._finish_turn(user_input, response, accounting)
            finally:
                current_accounting.reset(token)
                lease.close()

    async def stream(
        self, user_input: str, *, history: list[dict[str, str]] | ConversationHistory | None = None
    ) -> AsyncIterator[StreamEvent]:
        import asyncio

        lease = ExitStack()
        lease.enter_context(self._session_guard())
        accounting = TurnAccounting()
        token = current_accounting.set(accounting)
        response = AgentResponse(
            content="", status=ResponseStatus.PARTIAL, usage=UsageMetrics(cost_known=False)
        )
        iterator: AsyncIterator[StreamEvent] | None = None
        parts: list[str] = []
        try:
            context = self._context(user_input, history)
            if self._graph_backend is not None:
                iterator = self._graph_backend.stream(context)
            elif self._agent is not None:
                iterator = self._agent.execute_stream(context)
            else:
                raise RuntimeError("AssistantRuntime has no configured backend")
            async for item in iterator:
                if item.type.value == "done":
                    response.status = ResponseStatus(item.metadata.get("status", "partial"))
                    response.error = item.metadata.get("error")
                    response.metadata["interrupted"] = item.metadata.get("interrupted", False)
                elif item.type.value == "error":
                    response.status = ResponseStatus.ERROR
                    response.error = str(item.data)
                elif item.type.value == "metrics" and isinstance(item.data, dict):
                    response.usage = UsageMetrics(**item.data)
                elif item.is_content():
                    parts.append(item.get_text())
                yield item
        except BaseException as exc:
            response.status = (
                ResponseStatus.PARTIAL
                if isinstance(exc, (asyncio.CancelledError, KeyboardInterrupt, GeneratorExit))
                else ResponseStatus.ERROR
            )
            response.error = type(exc).__name__
            accounting.incomplete = True
            raise
        finally:
            try:
                if iterator is not None:
                    close = getattr(iterator, "aclose", None)
                    if close is not None:
                        await close()
            finally:
                response.content = "".join(parts)
                try:
                    self._finish_turn(user_input, response, accounting)
                finally:
                    current_accounting.reset(token)
                    lease.close()


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
