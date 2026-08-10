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
    ) -> None:
        require_extra("ai", feature="LangGraph assistant backend")
        self.provider = provider
        self.tool_registry = tool_registry
        self.enable_tools = enable_tools
        self.max_iterations = max_iterations
        self.debug_config = debug_config
        self.temperature = temperature
        self.max_tokens = max_tokens
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
            )
        return self._compiled_tool_graph

    def _initial_tool_state(self, context: ChatContext) -> dict[str, Any]:
        system_prompt = build_chat_system_prompt(context, enable_tools=self.enable_tools)
        # Graph keeps system prompt out-of-band; seed with user (+ history sans system).
        history_messages = build_chat_messages(
            context, enable_tools=self.enable_tools, include_system=False
        )
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
        if state.get("error"):
            status = ResponseStatus.ERROR
        elif status_raw == "final":
            status = ResponseStatus.SUCCESS
        else:
            status = ResponseStatus.PARTIAL
        tokens = int(state.get("tokens") or 0)
        tool_results = list(state.get("tool_results") or [])
        error = state.get("error")
        return AgentResponse(
            content=str(state.get("content") or ""),
            status=status,
            agent_name="chat_assistant",
            model=self.provider.model,
            provider=self.provider.provider_name,
            usage=UsageMetrics(total_tokens=tokens),
            error=str(error) if error is not None else None,
            metadata={
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
        response: AgentResponse = await self.provider.generate(
            messages=chat_messages,
            system_prompt=system,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        response.agent_name = "chat_assistant"
        response.metadata["orchestrator"] = "langgraph_plain"
        return response

    async def _run_react(self, context: ChatContext) -> AgentResponse:
        from openfatture.ai.orchestration.react import ReActOrchestrator

        orchestrator = ReActOrchestrator(
            provider=self.provider,
            tool_registry=self.tool_registry,
            max_iterations=self.max_iterations,
            debug_config=self.debug_config,
        )
        final_answer = await orchestrator.execute(context)
        response = AgentResponse(
            content=final_answer,
            status=ResponseStatus.SUCCESS,
            agent_name="chat_assistant",
            model=self.provider.model,
            provider=self.provider.provider_name,
        )
        response.metadata["orchestrator"] = "langgraph_react"
        response.metadata["orchestrator_metrics"] = orchestrator.get_metrics()
        return response

    async def _run_tool_graph(self, context: ChatContext) -> AgentResponse:
        graph = self._get_tool_graph()
        state = await graph.ainvoke(self._initial_tool_state(context))
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
        return await self._run_plain(context)

    async def stream(self, context: ChatContext) -> AsyncIterator[StreamEvent]:
        """Stream one turn as typed events (node-granularity for the tool graph).

        Token-level model streaming is not required for parity v1; the CLI
        receives progressive tool lifecycle events and final content.
        """
        context = self.prepare_context(context)

        if self._use_react(context):
            from openfatture.ai.orchestration.react import ReActOrchestrator

            orchestrator = ReActOrchestrator(
                provider=self.provider,
                tool_registry=self.tool_registry,
                max_iterations=self.max_iterations,
                debug_config=self.debug_config,
            )
            async for chunk in orchestrator.stream(context):
                if isinstance(chunk, str):
                    yield StreamEvent.content(chunk)
                elif isinstance(chunk, StreamEvent):
                    yield chunk
                else:
                    yield StreamEvent.content(str(chunk))
            return

        if not self._use_native_tools(context):
            response = await self._run_plain(context)
            if response.content:
                yield StreamEvent.content(response.content)
            return

        graph = self._get_tool_graph()
        initial = self._initial_tool_state(context)
        seen_tool_count = 0
        emitted_final_content = False
        merged: dict[str, Any] = dict(initial)

        async for update in graph.astream(initial, stream_mode="updates"):
            if not isinstance(update, dict):
                continue
            for node_name, delta in update.items():
                if not isinstance(delta, dict):
                    continue
                merged = {**merged, **delta}
                if node_name == "call_tools":
                    results = delta.get("tool_results") or []
                    if not isinstance(results, list):
                        continue
                    for entry in results[seen_tool_count:]:
                        if not isinstance(entry, dict):
                            continue
                        name = str(entry.get("tool") or "unknown")
                        params = entry.get("parameters") or {}
                        if not isinstance(params, dict):
                            params = {}
                        yield StreamEvent.tool_start(name, parameters=params)
                        if entry.get("success"):
                            yield StreamEvent.tool_result(name, result=entry.get("result"))
                        else:
                            yield StreamEvent.tool_error(
                                name, error=str(entry.get("result") or "tool failed")
                            )
                    seen_tool_count = len(results)
                elif node_name == "call_model":
                    content = str(delta.get("content") or "")
                    status = delta.get("status")
                    if status == "final" and content:
                        emitted_final_content = True
                        yield StreamEvent.content(content)
                    elif status == "tool_calls":
                        yield StreamEvent.status("Calling tools…")

        if not emitted_final_content:
            content = str(merged.get("content") or "")
            if content:
                yield StreamEvent.content(content)
