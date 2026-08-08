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

    user_input: str
    system_prompt: str
    messages: list[dict[str, Any]]
    iteration: int
    max_iterations: int
    content: str
    status: str
    error: str | None
    tokens: int
    tool_results: list[dict[str, Any]]


def _message_to_dict(msg: Message | dict[str, Any]) -> dict[str, Any]:
    if isinstance(msg, dict):
        return msg
    data: dict[str, Any] = {
        "role": msg.role.value,
        "content": msg.content or "",
    }
    if msg.tool_calls:
        data["tool_calls"] = msg.tool_calls
    if msg.tool_call_id:
        data["tool_call_id"] = msg.tool_call_id
    if msg.name:
        data["name"] = msg.name
    return data


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
) -> Any:
    """Compile a LangGraph model↔tools loop.

    Args:
        provider: LLM provider with ``generate`` and tool support metadata.
        tool_registry: ``ToolRegistry`` instance.
        max_iterations: Safety cap for the tool loop.
    """
    require_extra("ai", feature="LangGraph tool loop")
    try:
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
        messages = [_dict_to_message(m) for m in state.get("messages") or []]
        if not messages and state.get("user_input"):
            messages = [Message(role=Role.USER, content=state["user_input"])]
        use_tools = provider.supports_tools
        response = await provider.generate(
            messages=messages,
            system_prompt=state.get("system_prompt"),
            tools=_tool_schemas() if use_tools else None,
            tool_choice=_tool_choice() if use_tools else None,
        )
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
        return {
            **state,
            "messages": new_messages,
            "content": response.content or "",
            "status": "tool_calls" if response.has_tool_calls else "final",
            "error": response.error,
            "tokens": tokens,
            "iteration": int(state.get("iteration") or 0) + 1,
            "max_iterations": int(state.get("max_iterations") or max_iterations),
        }

    async def call_tools(state: ToolLoopState) -> ToolLoopState:
        messages = list(state.get("messages") or [])
        if not messages:
            return {**state, "status": "final"}
        last = messages[-1]
        tool_calls = last.get("tool_calls") or []
        results = list(state.get("tool_results") or [])
        for tc in tool_calls:
            fn = tc.get("function") or {}
            name = fn.get("name") or tc.get("name") or ""
            raw_args = fn.get("arguments") or tc.get("arguments") or {}
            if isinstance(raw_args, str):
                try:
                    arguments = json.loads(raw_args) if raw_args else {}
                except json.JSONDecodeError:
                    arguments = {}
            else:
                arguments = dict(raw_args)
            tool_call_id = tc.get("id") or name
            try:
                result = await tool_registry.execute_tool(
                    tool_name=name,
                    parameters=arguments,
                    confirm=False,
                )
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
                        "result": result.data if result.success else result.error,
                    }
                )
            except Exception as exc:
                content = f"Error executing tool: {exc}"
                results.append(
                    {"tool": name, "parameters": arguments, "success": False, "result": str(exc)}
                )
            messages.append(
                {
                    "role": "tool",
                    "content": content,
                    "tool_call_id": tool_call_id,
                    "name": name,
                }
            )
        return {
            **state,
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
    compiled = graph.compile()
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
