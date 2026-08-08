"""Conversational Chat Agent — prompt/context specialist + structured output.

Tool orchestration for product traffic lives in
:class:`~openfatture.ai.runtime.graph_backend.GraphAssistantBackend`.
This agent keeps structured-output calls and shared prompt helpers; when used
as the ``chat`` rollback backend it delegates tool/plain turns to the same
graph backend so there is a single tool-loop implementation.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from openfatture.ai.domain import AgentConfig, BaseAgent, Message
from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.response import AgentResponse, ResponseStatus
from openfatture.ai.providers import BaseLLMProvider
from openfatture.ai.runtime.constants import DEFAULT_TOOL_MAX_ITERATIONS
from openfatture.ai.streaming import StreamEvent
from openfatture.ai.tools import ToolRegistry, get_tool_registry
from openfatture.platform.config import DebugConfig
from openfatture.platform.logging import get_dynamic_logger, get_logger
from openfatture.platform.metrics import MetricsTimer, get_metrics_collector, record_ai_request

logger = get_logger(__name__)


class ChatAgent(BaseAgent[ChatContext]):
    """
    Conversational assistant agent for OpenFatture.

    Responsibilities:
    - Input validation and context metadata
    - Structured-output generation (``config.output_schema``)
    - Prompt/system builders (shared with the LangGraph product path)
    - Tool/plain/ReAct turns via :class:`GraphAssistantBackend` (single loop)

    Product CLI traffic goes through :class:`AssistantRuntime` (default backend
    ``langgraph``). This class remains for structured agents and ``chat`` rollback.
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        tool_registry: ToolRegistry | None = None,
        enable_tools: bool = True,
        enable_streaming: bool = True,
        debug_config: DebugConfig | None = None,
    ) -> None:
        config = AgentConfig(
            name="chat_assistant",
            description="General-purpose conversational assistant for OpenFatture",
            version="1.1.0",
            temperature=0.7,
            max_tokens=1500,
            tools_enabled=enable_tools,
            memory_enabled=True,
            rag_enabled=True,
            streaming_enabled=enable_streaming,
        )

        super().__init__(config=config, provider=provider)

        self.tool_registry = tool_registry or get_tool_registry()
        self.enable_tools = enable_tools
        self.debug_config = debug_config
        self._graph_backend: Any | None = None

        self.logger = get_dynamic_logger(__name__, debug_config)
        self.logger.info(
            "chat_agent_initialized",
            provider=provider.provider_name,
            model=provider.model,
            tools_enabled=enable_tools,
            streaming_enabled=enable_streaming,
            chat_debug_enabled=debug_config.enable_chat_debug if debug_config else False,
            orchestration="graph_assistant_backend",
        )

    def _get_graph_backend(self) -> Any:
        """Lazy GraphAssistantBackend shared for tool/plain/ReAct turns."""
        if self._graph_backend is None:
            from openfatture.ai.runtime.graph_backend import GraphAssistantBackend

            self._graph_backend = GraphAssistantBackend(
                provider=self.provider,
                tool_registry=self.tool_registry,
                enable_tools=self.enable_tools,
                max_iterations=DEFAULT_TOOL_MAX_ITERATIONS,
                debug_config=self.debug_config,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
        return self._graph_backend

    async def validate_input(self, context: ChatContext) -> tuple[bool, str | None]:
        if not context.user_input or len(context.user_input.strip()) == 0:
            return False, "Input utente richiesto"
        if len(context.user_input) > 5000:
            return False, "Input troppo lungo (max 5000 caratteri)"
        return True, None

    def _ensure_available_tools(self, context: ChatContext) -> None:
        if self.enable_tools and not context.available_tools:
            context.available_tools = self.get_available_tools()

    async def execute(self, context: ChatContext, **kwargs: Any) -> AgentResponse:
        """Execute one turn: structured schema path or shared graph orchestration."""
        collector = get_metrics_collector()
        self._ensure_available_tools(context)

        with MetricsTimer("chat_agent_execute", {"agent": self.config.name}):
            try:
                if self.config.output_schema and self.provider.supports_tools:
                    response = await self._execute_structured(context, **kwargs)
                else:
                    response = await self._get_graph_backend().run(context)
                    response.agent_name = self.config.name
                    response = await self._parse_response(response, context)

                collector.increment_counter(
                    "chat_agent_executions", tags={"agent": self.config.name, "success": "true"}
                )
                if response.usage is not None:
                    record_ai_request(
                        provider=self.provider.provider_name,
                        model=self.provider.model,
                        tokens=response.usage.total_tokens,
                        duration_ms=0,
                        success=True,
                    )
                return response
            except Exception as e:
                collector.increment_counter(
                    "chat_agent_executions", tags={"agent": self.config.name, "success": "false"}
                )
                collector.record_error("chat_agent_error", str(e), {"agent": self.config.name})
                raise

    async def _execute_structured(self, context: ChatContext, **kwargs: Any) -> AgentResponse:
        """Forced structured-output call (not part of the tool-loop graph)."""
        schema = self.config.output_schema
        if schema is None:
            return AgentResponse(
                content="",
                status=ResponseStatus.ERROR,
                agent_name=self.config.name,
                error="output_schema is required for structured execution",
            )

        is_valid, error_msg = await self.validate_input(context)
        if not is_valid:
            return AgentResponse(
                content="",
                status=ResponseStatus.ERROR,
                agent_name=self.config.name,
                error=error_msg,
            )

        messages = await self._build_prompt(context)
        schema_name = schema.get("title") or schema.get("name") or "structured_output"

        structured_kwargs = dict(kwargs)
        if self.provider.provider_name == "anthropic":
            structured_kwargs["tools"] = [
                {
                    "name": schema_name,
                    "description": schema.get(
                        "description", "Return the answer in the required structure."
                    ),
                    "input_schema": schema,
                }
            ]
            structured_kwargs["tool_choice"] = {"type": "tool", "name": schema_name}
        else:
            structured_kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                },
            }

        response = await self.provider.generate(
            messages=messages,
            system_prompt=self.config.system_prompt,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            **structured_kwargs,
        )

        structured = self._extract_structured_payload(response)
        if structured is not None:
            response.metadata["structured"] = structured
            response.metadata["is_structured"] = True
        else:
            response.metadata["is_structured"] = False

        response.agent_name = self.config.name
        return await self._parse_response(response, context)

    @staticmethod
    def _extract_structured_payload(response: AgentResponse) -> dict[str, Any] | None:
        if response.tool_calls:
            return response.tool_calls[0].arguments
        if response.content:
            try:
                parsed = json.loads(response.content)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                return None
        return None

    async def execute_stream(
        self, context: ChatContext, **kwargs: Any
    ) -> AsyncIterator[StreamEvent]:
        """Stream via the shared graph backend (node-granularity tool events)."""
        self._ensure_available_tools(context)
        async for event in self._get_graph_backend().stream(context):
            yield event

    async def _build_prompt(self, context: ChatContext) -> list[Message]:
        from openfatture.ai.runtime.prompt import build_chat_messages

        return build_chat_messages(context, enable_tools=self.enable_tools)

    def _build_system_prompt(self, context: ChatContext) -> str:
        from openfatture.ai.runtime.prompt import build_chat_system_prompt

        return build_chat_system_prompt(context, enable_tools=self.enable_tools)

    async def _parse_response(
        self,
        response: AgentResponse,
        context: ChatContext,
    ) -> AgentResponse:
        response.metadata["session_id"] = context.session_id
        response.metadata["message_count"] = len(context.conversation_history.messages)
        response.metadata["tools_available"] = len(context.available_tools)
        return response

    def get_available_tools(self, category: str | None = None) -> list[str]:
        tools = self.tool_registry.list_tools(category=category)
        return [t.name for t in tools]

    def get_tools_schema(self, provider_format: str = "openai") -> list[dict[str, Any]]:
        if provider_format == "anthropic":
            return self.tool_registry.get_anthropic_tools()
        return self.tool_registry.get_openai_functions()

    async def generate_title(self, context: ChatContext) -> str:
        first_message = context.user_input[:50]
        if len(context.user_input) > 50:
            first_message += "..."
        return first_message
