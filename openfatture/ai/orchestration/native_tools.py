"""Native tool calling orchestrator.

Drives the tool-calling loop for providers that support *native* function
calling (OpenAI, Anthropic). Unlike :class:`ReActOrchestrator`, which relies on
XML prompt engineering for providers without native support (Ollama), this
orchestrator passes the tool schemas directly to ``provider.generate(...)`` and
consumes the structured ``AgentResponse.tool_calls`` returned by the provider.

Loop:
    1. Call ``provider.generate(messages, tools=...)``.
    2. If ``response.has_tool_calls`` execute each tool via the ToolRegistry.
    3. Re-inject the assistant tool-call message and tool result messages.
    4. Repeat until the model returns a tool-call-free response or
       ``max_iterations`` is reached.

The execution path reuses the existing ``ToolRegistry.execute_tool`` (which
already wraps rate limiting, circuit breakers and bulkheads), so no resilience
logic is reimplemented here.
"""

from __future__ import annotations

import json
from typing import Any

from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.message import Message, Role
from openfatture.ai.domain.response import AgentResponse, ToolCall
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.ai.tools.registry import ToolRegistry
from openfatture.utils.config import DebugConfig
from openfatture.utils.logging import get_dynamic_logger, get_logger

logger = get_logger(__name__)


class NativeToolOrchestrator:
    """Orchestrate native tool calling for tool-capable providers.

    Mirrors the public surface of :class:`ReActOrchestrator` where it matters
    (constructor, ``execute``, ``get_metrics``) so callers can dispatch between
    the two without special-casing the return contract.
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        tool_registry: ToolRegistry,
        max_iterations: int = 5,
        debug_config: DebugConfig | None = None,
    ) -> None:
        """Initialize the native tool orchestrator.

        Args:
            provider: Tool-capable LLM provider instance.
            tool_registry: Registry used to execute tools.
            max_iterations: Maximum tool-calling loop iterations.
            debug_config: Optional debug configuration for tracing controls.
        """
        self.provider = provider
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.debug_config = debug_config

        self.logger = get_dynamic_logger(__name__, debug_config)

        # Metrics tracking (kept structurally compatible with ReActOrchestrator)
        self.metrics: dict[str, Any] = {
            "total_executions": 0,
            "tool_calls_attempted": 0,
            "tool_calls_succeeded": 0,
            "tool_calls_failed": 0,
            "max_iterations_reached": 0,
            "total_iterations": 0,
        }

        self.logger.info(
            "native_tool_orchestrator_initialized",
            provider=provider.provider_name,
            model=provider.model,
            max_iterations=max_iterations,
        )

    def _tool_schemas(self) -> list[dict[str, Any]]:
        """Build provider-specific tool schemas from the registry."""
        if self.provider.provider_name == "anthropic":
            return self.tool_registry.get_anthropic_tools()
        return self.tool_registry.get_openai_functions()

    def _tool_choice(self) -> Any:
        """Return the provider-appropriate ``tool_choice`` value for auto mode."""
        if self.provider.provider_name == "anthropic":
            return {"type": "auto"}
        return "auto"

    async def execute(
        self,
        context: ChatContext,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AgentResponse:
        """Run the native tool-calling loop and return the final response.

        Args:
            context: Chat context (used for correlation id and tool results).
            messages: Conversation messages (already includes system prompt
                if the provider expects it inline; ``system_prompt`` is passed
                separately for providers that take it out-of-band).
            system_prompt: Optional system prompt forwarded to the provider.
            temperature: Optional temperature override.
            max_tokens: Optional max tokens override.
            **kwargs: Extra provider kwargs (must not contain ``tools``/
                ``tool_choice``; those are managed internally).

        Returns:
            The final :class:`AgentResponse` (tool-call free) from the provider.
        """
        self.metrics["total_executions"] += 1

        tools_schema = self._tool_schemas()
        working_messages = list(messages)
        iteration = 0
        last_response: AgentResponse | None = None

        logger.info(
            "native_tool_loop_started",
            correlation_id=context.correlation_id,
            provider=self.provider.provider_name,
            max_iterations=self.max_iterations,
            tools_count=len(tools_schema),
        )

        while iteration < self.max_iterations:
            iteration += 1

            response = await self.provider.generate(
                messages=working_messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools_schema,
                tool_choice=self._tool_choice(),
                **kwargs,
            )
            last_response = response

            if not response.has_tool_calls:
                logger.info(
                    "native_tool_loop_completed",
                    correlation_id=context.correlation_id,
                    iterations=iteration,
                )
                self.metrics["total_iterations"] += iteration
                return response

            # Re-inject the assistant message carrying the tool calls.
            working_messages.append(
                Message(
                    role=Role.ASSISTANT,
                    content=response.content,
                    tool_calls=[
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": tc.arguments,
                            },
                        }
                        for tc in response.tool_calls
                    ],
                )
            )

            # Execute each tool call and re-inject results.
            for tool_call in response.tool_calls:
                tool_message = await self._execute_tool_call(tool_call, context)
                working_messages.append(tool_message)

        # Max iterations reached without a tool-call-free response.
        self.metrics["max_iterations_reached"] += 1
        self.metrics["total_iterations"] += iteration
        logger.warning(
            "native_tool_max_iterations_reached",
            correlation_id=context.correlation_id,
            iterations=iteration,
        )

        if last_response is not None:
            last_response.metadata["max_iterations_reached"] = True
            return last_response

        return AgentResponse(content="", provider=self.provider.provider_name)

    async def _execute_tool_call(
        self,
        tool_call: ToolCall,
        context: ChatContext,
    ) -> Message:
        """Execute a single tool call and build the tool result message.

        Args:
            tool_call: The tool call requested by the model.
            context: Chat context (tool results are recorded for downstream use).

        Returns:
            A ``Role.TOOL`` message containing the serialized result.
        """
        self.metrics["tool_calls_attempted"] += 1

        logger.info(
            "executing_tool_native",
            tool_name=tool_call.name,
            parameters=tool_call.arguments,
        )

        try:
            result = await self.tool_registry.execute_tool(
                tool_name=tool_call.name,
                parameters=tool_call.arguments,
                confirm=False,
            )

            if result.success:
                self.metrics["tool_calls_succeeded"] += 1
                content = self._serialize_result(result.data)
            else:
                self.metrics["tool_calls_failed"] += 1
                content = f"Error: {result.error}"

            # Record result on the call and in the context for observability.
            tool_call.result = result.data if result.success else None
            tool_call.error = None if result.success else result.error

            context.tool_results.append(
                {
                    "tool": tool_call.name,
                    "parameters": tool_call.arguments,
                    "result": result.data,
                    "success": result.success,
                }
            )

        except Exception as exc:  # pragma: no cover - defensive
            self.metrics["tool_calls_failed"] += 1
            content = f"Error executing tool: {exc}"
            tool_call.error = str(exc)
            logger.error(
                "tool_execution_failed_native",
                tool_name=tool_call.name,
                error=str(exc),
            )

        return Message(
            role=Role.TOOL,
            content=content,
            tool_call_id=tool_call.id,
            name=tool_call.name,
        )

    @staticmethod
    def _serialize_result(data: Any) -> str:
        """Serialize tool result data into a string for the model."""
        if data is None:
            return ""
        if isinstance(data, str):
            return data
        try:
            return json.dumps(data, default=str, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(data)

    def get_metrics(self) -> dict[str, Any]:
        """Return orchestrator metrics including derived rates."""
        tool_call_success_rate = 0.0
        if self.metrics["tool_calls_attempted"] > 0:
            tool_call_success_rate = (
                self.metrics["tool_calls_succeeded"] / self.metrics["tool_calls_attempted"]
            )

        avg_iterations = 0.0
        if self.metrics["total_executions"] > 0:
            avg_iterations = self.metrics["total_iterations"] / self.metrics["total_executions"]

        return {
            **self.metrics,
            "tool_call_success_rate": tool_call_success_rate,
            "avg_iterations": avg_iterations,
            "provider": self.provider.provider_name,
            "model": self.provider.model,
        }
