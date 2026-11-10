"""LangGraph product backend for the assistant runtime.

Implements the same turn contract as ChatAgent (AgentResponse + StreamEvent)
without re-entering :class:`AssistantRuntime` from graph nodes.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.message import Role
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.ai.runtime.constants import DEFAULT_TOOL_MAX_ITERATIONS
from openfatture.ai.runtime.model_calls import generate
from openfatture.ai.runtime.prompt import build_chat_messages, build_chat_system_prompt
from openfatture.ai.streaming.events import StreamEvent
from openfatture.ai.tools.registry import ToolRegistry
from openfatture.platform.config import DebugConfig
from openfatture.platform.extras import require_extra
from openfatture.platform.logging import get_logger

logger = get_logger(__name__)


class GraphAssistantBackend:
    """Product orchestration path backed by a model↔tools StateGraph."""

    def __init__(
        self,
        *,
        provider: BaseLLMProvider,
        tool_registry: ToolRegistry,
        enable_tools: bool = True,
        max_iterations: int = DEFAULT_TOOL_MAX_ITERATIONS,
        debug_config: DebugConfig | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        model_timeout_seconds: float = 120,
    ) -> None:
        require_extra("ai", feature="LangGraph assistant backend")
        self.provider = provider
        self.tool_registry = tool_registry
        self.enable_tools = enable_tools
        self.max_iterations = max_iterations
        self.debug_config = debug_config
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model_timeout_seconds = model_timeout_seconds
        self._compiled_tool_graph: Any | None = None

    def prepare_context(self, context: ChatContext) -> ChatContext:
        """Ensure ``available_tools`` is populated when tools are enabled."""
        if self.enable_tools and not context.available_tools:
            context.available_tools = [t.name for t in self.tool_registry.list_tools()]
        return context

    def _use_native_tools(self, context: ChatContext) -> bool:
        return self.enable_tools and self.provider.supports_tools and bool(context.available_tools)

    def _use_react(self, context: ChatContext) -> bool:
        return (
            self.enable_tools and not self.provider.supports_tools and bool(context.available_tools)
        )

    def _get_tool_graph(self) -> Any:
        if self._compiled_tool_graph is None:
            from openfatture.ai.runtime.graph import build_tool_loop_graph

            self._compiled_tool_graph = build_tool_loop_graph(
                provider=self.provider,
                tool_registry=self.tool_registry,
                max_iterations=self.max_iterations,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                model_timeout_seconds=self.model_timeout_seconds,
            )
        return self._compiled_tool_graph

    def _initial_tool_state(self, context: ChatContext) -> dict[str, Any]:
        system_prompt = build_chat_system_prompt(context, enable_tools=self.enable_tools)
        # Graph keeps system prompt out-of-band; seed with user (+ history sans system).
        history_messages = build_chat_messages(
            context, enable_tools=self.enable_tools, include_system=False
        )
        if self._use_react(context):
            from openfatture.ai.orchestration.react import build_react_messages

            history_messages = build_react_messages(
                context, self.tool_registry.list_tools(enabled_only=True)
            )
            system_prompt = history_messages[0].content
            history_messages = history_messages[1:]
        messages: list[dict[str, Any]] = []
        for msg in history_messages:
            entry: dict[str, Any] = {
                "role": msg.role.value,
                "content": msg.content or "",
            }
            if msg.tool_calls:
                entry["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id
            if msg.name:
                entry["name"] = msg.name
            messages.append(entry)
        return {
            "tools_enabled": self._use_native_tools(context),
            "react": self._use_react(context),
            "streaming": bool(context.metadata.get("streaming")),
            "user_input": context.user_input,
            "system_prompt": system_prompt,
            "messages": messages,
            "iteration": 0,
            "max_iterations": self.max_iterations,
            "tool_results": [],
            "content": "",
            "status": "",
            "error": None,
            "tokens": 0,
        }

    def _state_to_response(self, state: dict[str, Any]) -> AgentResponse:
        status_raw = state.get("status") or "final"
        if state.get("interrupted"):
            status = ResponseStatus.PARTIAL
        elif state.get("error") == "max_iterations_reached":
            status = ResponseStatus.PARTIAL
        elif state.get("error") or status_raw == "error":
            status = ResponseStatus.ERROR
        elif status_raw == "final":
            status = ResponseStatus.SUCCESS
        else:
            status = ResponseStatus.PARTIAL
        tokens = int(state.get("tokens") or 0)
        tool_results = list(state.get("tool_results") or [])
        error = state.get("error")
        blocked = [
            entry
            for entry in tool_results
            if not entry.get("success") and str(entry.get("result", "")).startswith("confirmation_")
        ]
        if blocked:
            status = ResponseStatus.PARTIAL
            error = str(blocked[-1].get("result"))
        return AgentResponse(
            content=str(state.get("content") or ""),
            status=status,
            agent_name="chat_assistant",
            model=self.provider.model,
            provider=self.provider.provider_name,
            usage=UsageMetrics(**state["usage"])
            if state.get("usage")
            else UsageMetrics(total_tokens=tokens, cost_known=False),
            error=str(error) if error is not None else None,
            metadata={
                "interrupted": bool(state.get("interrupted")),
                "pending_approval": state.get("pending_approval"),
                "orchestrator": "langgraph_tool_loop",
                "tool_results": tool_results,
                "iterations": state.get("iteration"),
            },
        )

    async def _run_plain(self, context: ChatContext) -> AgentResponse:
        messages = build_chat_messages(context, enable_tools=self.enable_tools)
        system: str | None = None
        chat_messages = messages
        if messages and messages[0].role == Role.SYSTEM:
            system = messages[0].content
            chat_messages = messages[1:]
        response: AgentResponse = await generate(
            self.provider,
            timeout=self.model_timeout_seconds,
            messages=chat_messages,
            system_prompt=system,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        response.agent_name = "chat_assistant"
        response.metadata["orchestrator"] = "langgraph_plain"
        return response

    async def _run_react(self, context: ChatContext) -> AgentResponse:
        response = await self._run_tool_graph(context)
        response.metadata["orchestrator"] = "langgraph_react"
        return response

    async def _run_tool_graph(self, context: ChatContext, on_event: Any = None) -> AgentResponse:
        if context.metadata.get("checkpoint_directory"):
            from pathlib import Path

            from openfatture.ai.runtime.durability import DurableToolExecutor

            state = await DurableToolExecutor(Path(context.metadata["checkpoint_directory"])).run(
                session_id=context.session_id or "",
                turn_id=context.metadata["turn_id"],
                provider=self.provider,
                registry=self.tool_registry,
                initial=self._initial_tool_state(context),
                on_event=on_event,
                max_iterations=self.max_iterations,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                model_timeout_seconds=self.model_timeout_seconds,
            )
        else:
            graph = self._get_tool_graph()
            state = await graph.ainvoke(
                self._initial_tool_state(context),
                config={"recursion_limit": 2 * self.max_iterations + 2},
            )
        if not isinstance(state, dict):
            return AgentResponse(
                content="",
                status=ResponseStatus.ERROR,
                agent_name="chat_assistant",
                error="LangGraph returned a non-dict state",
            )
        return self._state_to_response(state)

    async def run(self, context: ChatContext) -> AgentResponse:
        """Execute one assistant turn via the LangGraph product path."""
        context = self.prepare_context(context)
        if not context.user_input or not str(context.user_input).strip():
            return AgentResponse(
                content="",
                status=ResponseStatus.ERROR,
                agent_name="chat_assistant",
                error="Input utente richiesto",
            )
        if len(context.user_input) > 5000:
            return AgentResponse(
                content="",
                status=ResponseStatus.ERROR,
                agent_name="chat_assistant",
                error="Input troppo lungo (max 5000 caratteri)",
            )

        if self._use_native_tools(context):
            logger.info(
                "langgraph_native_tools",
                provider=self.provider.provider_name,
                tools=len(context.available_tools),
            )
            return await self._run_tool_graph(context)
        if self._use_react(context):
            logger.info(
                "langgraph_react_fallback",
                provider=self.provider.provider_name,
                tools=len(context.available_tools),
            )
            return await self._run_react(context)
        logger.info("langgraph_plain", provider=self.provider.provider_name)
        if context.metadata.get("checkpoint_directory"):
            return await self._run_tool_graph(context)
        return await self._run_plain(context)

    async def stream(self, context: ChatContext) -> AsyncIterator[StreamEvent]:
        """Stream one turn as typed events (node-granularity for the tool graph).

        Token-level model streaming is not required for parity v1; the CLI
        receives progressive tool lifecycle events and final content.
        """
        context = self.prepare_context(context)
        context.metadata["streaming"] = True

        if not context.user_input.strip() or len(context.user_input) > 5000:
            response = await self.run(context)
            yield StreamEvent.done(status=response.status.value, error=response.error)
            return
        if context.metadata.get("checkpoint_directory"):
            import asyncio
            from contextlib import suppress

            queue: asyncio.Queue[Any] = asyncio.Queue()
            streamed_content = False
            task = asyncio.create_task(self._run_tool_graph(context, queue.put_nowait))
            task.add_done_callback(lambda _: queue.put_nowait(None))
            try:
                while True:
                    update = await queue.get()
                    if update is None:
                        break
                    if update.get("event") == "content":
                        streamed_content = True
                        yield StreamEvent.content(str(update["content"]))
                        continue
                    name = str(update.get("tool") or "unknown")
                    if update.get("event") == "tool_start":
                        event = StreamEvent.tool_start(
                            name, parameters=update.get("parameters") or {}
                        )
                    elif update.get("event") == "tool_finished":
                        event = (
                            StreamEvent.tool_result(name, result=update.get("result"))
                            if update.get("success")
                            else StreamEvent.tool_error(name, error=str(update.get("result")))
                        )
                    else:
                        continue
                    event.metadata["tool_call_id"] = update.get("tool_call_id")
                    yield event
                response = await task
            finally:
                if not task.done():
                    task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            yield StreamEvent.metrics(**response.usage.model_dump())
            if response.content and not streamed_content:
                yield StreamEvent.content(response.content)
            done = StreamEvent.done(status=response.status.value, error=response.error)
            done.metadata["interrupted"] = response.metadata.get("interrupted", False)
            yield done
            return

        graph = self._get_tool_graph()
        initial = self._initial_tool_state(context)
        emitted_final_content = False
        merged: dict[str, Any] = dict(initial)

        async for part in graph.astream(
            initial,
            config={"recursion_limit": 2 * self.max_iterations + 2},
            stream_mode=["updates", "custom"],
            version="v2",
        ):
            mode, update = part["type"], part["data"]
            if not isinstance(update, dict):
                continue
            if mode == "custom":
                if update.get("event") == "content":
                    emitted_final_content = True
                    yield StreamEvent.content(str(update["content"]))
                    continue
                name = str(update.get("tool") or "unknown")
                if update.get("event") == "tool_start":
                    event = StreamEvent.tool_start(name, parameters=update.get("parameters") or {})
                elif update.get("event") == "tool_finished":
                    event = (
                        StreamEvent.tool_result(name, result=update.get("result"))
                        if update.get("success")
                        else StreamEvent.tool_error(name, error=str(update.get("result")))
                    )
                else:
                    continue
                event.metadata["tool_call_id"] = update.get("tool_call_id")
                yield event
                continue
            for node_name, delta in update.items():
                if not isinstance(delta, dict):
                    continue
                merged = {**merged, **delta}
                if node_name == "call_model":
                    content = str(delta.get("content") or "")
                    status = delta.get("status")
                    if status == "final" and content and not delta.get("streamed"):
                        emitted_final_content = True
                        yield StreamEvent.content(content)
                    elif status == "tool_calls":
                        yield StreamEvent.status("Calling tools…")

        from openfatture.ai.streaming.events import StreamEventType

        yield StreamEvent(type=StreamEventType.METRICS, data=dict(merged.get("usage") or {}))
        final_response = self._state_to_response(merged)
        if not emitted_final_content:
            content = str(merged.get("content") or "")
            if content:
                yield StreamEvent.content(content)

        yield StreamEvent.done(status=final_response.status.value, error=final_response.error)
