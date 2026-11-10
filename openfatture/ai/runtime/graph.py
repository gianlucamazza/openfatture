"""LangGraph multi-node assistant graph (model ↔ tools loop).

Public CLI still uses :class:`~openfatture.ai.runtime.service.AssistantRuntime`.
This module provides a first-class StateGraph with:

- ``call_model`` — LLM generation with tool schemas
- ``call_tools`` — ToolRegistry execution
- conditional edges until a final answer or max iterations

Experimental multi-agent workflows remain under ``ai.orchestration.workflows``.
"""

from __future__ import annotations

import json
from typing import Any, Literal, Protocol, TypedDict

from openfatture.ai.domain.message import Message, Role
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.ai.runtime.model_calls import generate, generate_streamed
from openfatture.ai.tools.registry import ToolRegistry
from openfatture.platform.extras import require_extra
from openfatture.platform.logging import get_logger

logger = get_logger(__name__)


class _RuntimeProviderAccess(Protocol):
    """Minimal surface of AssistantRuntime needed to build a graph."""

    _provider: BaseLLMProvider
    _tool_registry: ToolRegistry


class ToolLoopState(TypedDict, total=False):
    """State for the multi-node tool-calling graph."""

    tools_enabled: bool
    react: bool
    streaming: bool
    streamed: bool
    user_input: str
    system_prompt: str
    messages: list[dict[str, Any]]
    iteration: int
    max_iterations: int
    content: str
    status: str
    error: str | None
    tokens: int
    usage: dict[str, Any]
    tool_results: list[dict[str, Any]]


def _dict_to_message(data: dict[str, Any]) -> Message:
    role_raw = data.get("role", "user")
    role = Role(role_raw) if isinstance(role_raw, str) else role_raw
    return Message(
        role=role,
        content=data.get("content") or "",
        tool_calls=data.get("tool_calls") or [],
        tool_call_id=data.get("tool_call_id"),
        name=data.get("name"),
    )


def build_tool_loop_graph(
    *,
    provider: BaseLLMProvider,
    tool_registry: ToolRegistry,
    max_iterations: int = 5,
    temperature: float = 0.7,
    max_tokens: int = 1500,
    model_timeout_seconds: float = 120,
    checkpointer: Any = None,
    journal: Any = None,
) -> Any:
    """Compile a LangGraph model↔tools loop.

    Args:
        provider: LLM provider with ``generate`` and tool support metadata.
        tool_registry: ``ToolRegistry`` instance.
        max_iterations: Safety cap for the tool loop.
    """
    require_extra("ai", feature="LangGraph tool loop")
    try:
        from langgraph.config import get_config, get_stream_writer
        from langgraph.graph import END, StateGraph
    except ImportError as exc:
        from openfatture.platform.extras import MissingExtraError

        raise MissingExtraError("ai", feature="LangGraph", cause=exc) from exc

    def _tool_schemas() -> list[dict[str, Any]]:
        if provider.provider_name == "anthropic":
            return list(tool_registry.get_anthropic_tools())
        return list(tool_registry.get_openai_functions())

    def _tool_choice() -> Any:
        if provider.provider_name == "anthropic":
            return {"type": "auto"}
        return "auto"

    async def call_model(state: ToolLoopState) -> ToolLoopState:
        logger.info(
            "assistant_graph_node",
            node="call_model",
            thread_id=get_config().get("configurable", {}).get("thread_id"),
            iteration=state.get("iteration", 0),
        )
        messages = [_dict_to_message(m) for m in state.get("messages") or []]
        if not messages and state.get("user_input"):
            messages = [Message(role=Role.USER, content=state["user_input"])]
        if state.get("react"):
            messages = [
                Message(role=Role.USER, content=f"Observation: {m.content}")
                if m.role == Role.TOOL
                else Message(role=m.role, content=m.content)
                for m in messages
            ]
        use_tools = provider.supports_tools and state.get("tools_enabled", True)
        generate_model = (
            generate_streamed if state.get("streaming") and not state.get("react") else generate
        )
        stream_options = (
            {"emit": get_stream_writer()}
            if state.get("streaming") and not state.get("react")
            else {}
        )
        response = await generate_model(
            provider,
            **stream_options,
            timeout=model_timeout_seconds,
            messages=messages,
            system_prompt=state.get("system_prompt"),
            temperature=temperature,
            max_tokens=max_tokens,
            tools=_tool_schemas() if use_tools else None,
            tool_choice=_tool_choice() if use_tools else None,
        )
        if state.get("react") and response.success:
            from openfatture.ai.domain.response import ToolCall
            from openfatture.ai.orchestration.parsers import ToolCallParser

            parsed = ToolCallParser().parse(response.content)
            if parsed.tool_call:
                response.tool_calls = [
                    ToolCall(
                        id=f"react-{state.get('iteration', 0)}",
                        name=parsed.tool_call.tool_name,
                        arguments=parsed.tool_call.parameters,
                    )
                ]
            elif parsed.is_final:
                response.content = parsed.content
        assistant_msg: dict[str, Any] = {
            "role": "assistant",
            "content": response.content or "",
        }
        if response.has_tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": tc.arguments,
                    },
                }
                for tc in response.tool_calls
            ]
        new_messages = list(state.get("messages") or [])
        if not new_messages and state.get("user_input"):
            new_messages.append({"role": "user", "content": state["user_input"]})
        new_messages.append(assistant_msg)
        usage_tokens = response.usage.total_tokens if response.usage is not None else 0
        tokens = int(usage_tokens or 0) + int(state.get("tokens") or 0)
        usage = dict(state.get("usage") or {})
        current = response.usage
        for key in ("prompt_tokens", "completion_tokens", "total_tokens", "estimated_cost_usd"):
            usage[key] = usage.get(key, 0) + getattr(current, key, 0)
        usage["cost_known"] = usage.get("cost_known", True) and getattr(
            current, "cost_known", False
        )
        return {
            "streamed": bool(response.metadata.get("streamed")),
            "usage": usage,
            "messages": new_messages,
            "content": response.content or "",
            "status": "error"
            if not response.success
            else "tool_calls"
            if response.has_tool_calls
            else "final",
            "error": response.error
            or (
                "max_iterations_reached"
                if response.has_tool_calls
                and int(state.get("iteration") or 0) + 1
                >= int(state.get("max_iterations") or max_iterations)
                else None
            ),
            "tokens": tokens,
            "iteration": int(state.get("iteration") or 0) + 1,
            "max_iterations": int(state.get("max_iterations") or max_iterations),
        }

    async def call_tools(state: ToolLoopState) -> ToolLoopState:
        config = get_config()
        writer = get_stream_writer()
        messages = list(state.get("messages") or [])
        if not messages:
            return {"status": "final"}
        last = messages[-1]
        tool_calls = last.get("tool_calls") or []
        results = list(state.get("tool_results") or [])
        for tc in tool_calls:
            fn = tc.get("function") or {}
            name = fn.get("name") or tc.get("name") or ""
            raw_args = fn.get("arguments", tc.get("arguments", {}))
            if isinstance(raw_args, str):
                try:
                    arguments = json.loads(raw_args)
                except json.JSONDecodeError:
                    arguments = None
            else:
                arguments = raw_args
            tool_call_id = tc.get("id") or name
            logger.info(
                "assistant_graph_tool",
                node="call_tools",
                tool=name,
                tool_call_id=tool_call_id,
                thread_id=config.get("configurable", {}).get("thread_id"),
            )
            approved = None
            if journal and isinstance(arguments, dict):
                from langgraph.types import interrupt

                from openfatture.ai.tools.models import Tool
                from openfatture.ai.tools.registry.policy import confirmation_required
                from openfatture.platform.config import get_settings

                tool = tool_registry.get_tool(name)
                if isinstance(tool, Tool) and confirmation_required(
                    name,
                    tool_requires_confirmation=tool.requires_confirmation,
                    require_confirmation=get_settings().ai_tools_require_confirmation,
                ):
                    approved = interrupt(
                        {
                            "kind": "approval",
                            "tool": name,
                            "parameters": arguments,
                            "tool_call_id": tool_call_id,
                        }
                    )
            reserved = False
            try:
                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments must be a valid JSON object")
                writer(
                    {
                        "event": "tool_start",
                        "tool": name,
                        "parameters": arguments,
                        "tool_call_id": tool_call_id,
                    }
                )
                from openfatture.ai.tools.models import ToolResult

                receipt_id = f"{config.get('configurable', {}).get('thread_id', '')}:{state.get('iteration', 0)}:{tool_call_id}"
                if approved is False:
                    result = ToolResult(
                        success=False,
                        error="Human declined operation",
                        error_type="confirmation_denied",
                        tool_name=name,
                    )
                    cached: Any = result.model_dump(mode="json")
                else:
                    cached = journal.begin(receipt_id, name, arguments) if journal else None
                    reserved = journal is not None and cached is None
                if cached is not None:
                    result = ToolResult.model_validate(cached)
                else:
                    execution_options: dict[str, Any] = (
                        {"source": "human", "confirmed": True} if approved is True else {}
                    )
                    result = await tool_registry.execute_tool(
                        tool_name=name,
                        parameters=arguments,
                        **execution_options,
                    )
                    if journal and (
                        result.metadata.get("outcome_uncertain")
                        or result.error_type in {"TimeoutError", "ConnectionError", "OSError"}
                    ):
                        from openfatture.ai.runtime.durability import UncertainToolOutcome

                        raise UncertainToolOutcome(receipt_id)
                    if journal:
                        journal.complete(receipt_id, result.model_dump(mode="json"))
                content = (
                    json.dumps(result.data, default=str, ensure_ascii=False)
                    if result.success
                    else f"Error: {result.error}"
                )
                results.append(
                    {
                        "tool": name,
                        "parameters": arguments,
                        "success": result.success,
                        "result": result.data
                        if result.success
                        else result.error_type or result.error,
                    }
                )
            except Exception as exc:
                from openfatture.ai.runtime.durability import UncertainToolOutcome

                if isinstance(exc, UncertainToolOutcome):
                    raise
                if reserved:
                    raise UncertainToolOutcome(receipt_id) from exc
                content = f"Error executing tool: {exc}"
                results.append(
                    {"tool": name, "parameters": arguments, "success": False, "result": str(exc)}
                )
            writer({"event": "tool_finished", **results[-1], "tool_call_id": tool_call_id})
            messages.append(
                {
                    "role": "tool",
                    "content": content,
                    "tool_call_id": tool_call_id,
                    "name": name,
                }
            )
        return {
            "messages": messages,
            "tool_results": results,
            "status": "continue",
        }

    def route_after_model(state: ToolLoopState) -> Literal["call_tools", "end"]:
        if state.get("status") == "tool_calls":
            if int(state.get("iteration") or 0) >= int(
                state.get("max_iterations") or max_iterations
            ):
                return "end"
            return "call_tools"
        return "end"

    def route_after_tools(state: ToolLoopState) -> Literal["call_model", "end"]:
        if int(state.get("iteration") or 0) >= int(state.get("max_iterations") or max_iterations):
            return "end"
        return "call_model"

    graph: StateGraph = StateGraph(ToolLoopState)
    graph.add_node("call_model", call_model)
    graph.add_node("call_tools", call_tools)
    graph.set_entry_point("call_model")
    graph.add_conditional_edges(
        "call_model",
        route_after_model,
        {"call_tools": "call_tools", "end": END},
    )
    graph.add_conditional_edges(
        "call_tools",
        route_after_tools,
        {"call_model": "call_model", "end": END},
    )
    compiled = graph.compile(checkpointer=checkpointer)
    logger.info(
        "tool_loop_graph_compiled",
        max_iterations=max_iterations,
        nodes=["call_model", "call_tools"],
    )
    return compiled


def build_assistant_graph(runtime: _RuntimeProviderAccess) -> Any:
    """Build a multi-node tool-loop graph from an :class:`AssistantRuntime`.

    Uses provider/registry primitives only — never ``runtime.run`` — so the
    graph cannot re-enter the product facade (backend circularity).
    """
    provider: BaseLLMProvider = runtime._provider
    registry: ToolRegistry = runtime._tool_registry
    if provider.supports_tools:
        return build_tool_loop_graph(provider=provider, tool_registry=registry)

    # Fallback: single-node plain generation (no tools / no native tool support)
    require_extra("ai", feature="LangGraph assistant graph")
    from langgraph.graph import END, StateGraph

    class SimpleState(TypedDict, total=False):
        user_input: str
        content: str
        status: str
        error: str | None
        tokens: int

    async def run_turn(state: SimpleState) -> SimpleState:
        response = await provider.generate(
            messages=[Message(role=Role.USER, content=state["user_input"])],
        )
        tokens = response.usage.total_tokens if response.usage is not None else 0
        return {
            "user_input": state["user_input"],
            "content": response.content or "",
            "status": response.status.value,
            "error": response.error,
            "tokens": int(tokens or 0),
        }

    graph = StateGraph(SimpleState)
    graph.add_node("assistant_turn", run_turn)
    graph.set_entry_point("assistant_turn")
    graph.add_edge("assistant_turn", END)
    return graph.compile()
