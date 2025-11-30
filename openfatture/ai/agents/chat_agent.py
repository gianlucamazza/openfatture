"""Conversational Chat Agent with tool calling capabilities."""

from collections.abc import AsyncIterator
from typing import Any

from openfatture.ai.domain import AgentConfig, BaseAgent, Message, Role
from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.orchestration.react import ReActOrchestrator
from openfatture.ai.providers import BaseLLMProvider
from openfatture.ai.streaming import StreamEvent
from openfatture.ai.tools import ToolRegistry, get_tool_registry
from openfatture.utils.config import DebugConfig
from openfatture.utils.logging import get_dynamic_logger, get_logger
from openfatture.utils.metrics import MetricsTimer, get_metrics_collector, record_ai_request

logger = get_logger(__name__)


class ChatAgent(BaseAgent[ChatContext]):
    """
    General-purpose conversational agent with tool calling.

    Specialized to use ChatContext for type-safe context handling.

    Features:
    - Multi-turn conversations with memory
    - Function/tool calling for actions (search invoices, get stats, etc.)
    - Context enrichment with business data
    - Streaming support (if provider supports it)
    - Session management integration

    The agent can:
    - Answer questions about invoices and clients
    - Search and retrieve data from the database
    - Provide statistics and insights
    - Guide users through workflows
    - Execute actions via tools (with user confirmation)

    Example:
        User: "Quante fatture ho emesso quest'anno?"
        Agent: [calls get_invoice_stats tool]
        Agent: "Hai emesso 42 fatture nel 2025..."
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        tool_registry: ToolRegistry | None = None,
        enable_tools: bool = True,
        enable_streaming: bool = True,
        debug_config: DebugConfig | None = None,
    ) -> None:
        """
        Initialize Chat Agent.

        Args:
            provider: LLM provider instance
            tool_registry: Tool registry (uses global if None)
            enable_tools: Enable tool calling
            enable_streaming: Enable streaming responses (default: True for better UX)
            debug_config: Debug configuration for logging controls
        """
        # Agent configuration
        config = AgentConfig(
            name="chat_assistant",
            description="General-purpose conversational assistant for OpenFatture",
            version="1.0.0",
            temperature=0.7,  # Balanced creativity
            max_tokens=1500,  # Enough for detailed responses
            tools_enabled=enable_tools,
            memory_enabled=True,
            rag_enabled=True,
            streaming_enabled=enable_streaming,
        )

        super().__init__(config=config, provider=provider)

        # Tool management
        self.tool_registry = tool_registry or get_tool_registry()
        self.enable_tools = enable_tools
        self.debug_config = debug_config

        # Get dynamic logger
        self.logger = get_dynamic_logger(__name__, debug_config)

        self.logger.info(
            "chat_agent_initialized",
            provider=provider.provider_name,
            model=provider.model,
            tools_enabled=enable_tools,
            streaming_enabled=enable_streaming,
            chat_debug_enabled=debug_config.enable_chat_debug if debug_config else False,
        )

    async def validate_input(self, context: ChatContext) -> tuple[bool, str | None]:
        """
        Validate chat context before processing.

        Args:
            context: Chat context

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation
        if not context.user_input or len(context.user_input.strip()) == 0:
            return False, "Input utente richiesto"

        if len(context.user_input) > 5000:
            return False, "Input troppo lungo (max 5000 caratteri)"

        return True, None

    async def execute(self, context: ChatContext, **kwargs: Any) -> AgentResponse:
        """Execute chat agent, injecting tool schemas when native tool calling is available."""
        collector = get_metrics_collector()

        with MetricsTimer("chat_agent_execute", {"agent": self.config.name}):
            try:
                if self.enable_tools and self.provider.supports_tools and context.available_tools:
                    tool_kwargs = dict(kwargs)
                    tool_kwargs.setdefault("tools", self.get_tools_schema())
                    response = await super().execute(context, **tool_kwargs)
                else:
                    response = await super().execute(context, **kwargs)

                # Record successful execution
                collector.increment_counter(
                    "chat_agent_executions", tags={"agent": self.config.name, "success": "true"}
                )
                if hasattr(response, "usage") and response.usage:
                    record_ai_request(
                        provider=self.provider.provider_name,
                        model=self.provider.model,
                        tokens=response.usage.total_tokens,
                        duration_ms=0,  # Would need to track timing separately
                        success=True,
                    )

                return response

            except Exception as e:
                collector.increment_counter(
                    "chat_agent_executions", tags={"agent": self.config.name, "success": "false"}
                )
                collector.record_error("chat_agent_error", str(e), {"agent": self.config.name})
                raise

    async def execute_stream(  # type: ignore[override]
        self, context: ChatContext, **kwargs: Any
    ) -> AsyncIterator[StreamEvent]:
        """
        Execute chat agent with streaming, using ReAct or native tool calling.

        Override BaseAgent.execute_stream() to add tool calling support:
        - ReAct orchestration for providers that don't support native function calling
        - Native tool calling for providers that support it

        Args:
            context: Chat context

        Yields:
            StreamEvent: Typed streaming events (CONTENT, TOOL_START, TOOL_RESULT, etc.)
        """
        # Check if we need ReAct orchestration
        needs_react = (
            self.enable_tools
            and not self.provider.supports_tools
            and len(context.available_tools) > 0
        )

        if needs_react:
            logger.info(
                "using_react_orchestration",
                agent=self.config.name,
                provider=self.provider.provider_name,
                tools_count=len(context.available_tools),
            )

            # Use ReAct orchestrator for tool calling
            orchestrator = ReActOrchestrator(
                provider=self.provider,
                tool_registry=self.tool_registry,
                max_iterations=5,
                debug_config=self.debug_config,
            )

            # Wrap ReAct string chunks in StreamEvent.content()
            async for chunk in orchestrator.stream(context):
                yield StreamEvent.content(chunk)

        elif (
            self.enable_tools and self.provider.supports_tools and len(context.available_tools) > 0
        ):
            # Use native tool calling for providers that support it
            logger.info(
                "using_native_tool_calling",
                agent=self.config.name,
                provider=self.provider.provider_name,
                tools_count=len(context.available_tools),
            )

            async for event in self._execute_stream_with_tools(context, **kwargs):
                yield event

        else:
            # Use standard streaming from BaseAgent
            # (when tools disabled or no tools available)
            logger.debug(
                "using_standard_streaming",
                agent=self.config.name,
                provider=self.provider.provider_name,
                supports_tools=self.provider.supports_tools,
                tools_enabled=self.enable_tools,
                available_tools=len(context.available_tools),
            )

            # Wrap BaseAgent string chunks in StreamEvent.content()
            async for chunk in super().execute_stream(context, **kwargs):
                yield StreamEvent.content(chunk)

    async def _execute_stream_with_tools(
        self,
        context: ChatContext,
        **kwargs: Any,
    ) -> AsyncIterator[StreamEvent]:
        """
        Execute with native tool calling support using streaming.

        Accumulates streaming response, detects tool calls, executes them,
        then continues with follow-up streaming for better UX.

        Args:
            context: Chat context

        Yields:
            StreamEvent: Typed events (CONTENT, TOOL_START, TOOL_PROGRESS, TOOL_RESULT, TOOL_ERROR)
        """
        # Get tools schema for the provider
        tools_schema = self.get_tools_schema()

        # Build prompt
        messages = await self._build_prompt(context)

        logger.info(
            "streaming_with_tools_started",
            agent=self.config.name,
            tools_count=len(tools_schema),
        )

        # Use stream_structured for real-time content and tool call streaming
        accumulated_content = ""
        pending_tool_calls = []

        try:
            stream_kwargs = dict(kwargs)
            stream_kwargs.setdefault("tools", tools_schema)

            async for chunk in self.provider.stream_structured(
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **stream_kwargs,
            ):
                if chunk.content:
                    # Yield content chunk as StreamEvent
                    accumulated_content += chunk.content
                    yield StreamEvent.content(chunk.content)

                elif chunk.tool_call:
                    # Accumulate tool calls
                    pending_tool_calls.append(chunk.tool_call)

                elif chunk.is_final:
                    # End of response - execute any pending tool calls
                    if pending_tool_calls:
                        logger.info(
                            "tool_calls_detected_in_stream",
                            agent=self.config.name,
                            tool_count=len(pending_tool_calls),
                            content_length=len(accumulated_content),
                            tool_names=[tc.name for tc in pending_tool_calls],
                        )

                        # Execute tools with timing
                        import time

                        start_time = time.time()

                        tool_results = await self._handle_tool_calls(
                            [
                                {
                                    "function": {"name": tc.name, "arguments": tc.arguments},
                                    "id": tc.id,
                                }
                                for tc in pending_tool_calls
                            ],
                            context,
                        )

                        execution_time = time.time() - start_time

                        # Emit tool execution events
                        successful_count = 0
                        failed_count = 0

                        for tool_call in pending_tool_calls:
                            tool_name = tool_call.name
                            # tool_call.arguments is already a dict[str, Any]
                            tool_args_dict = tool_call.arguments

                            # Emit TOOL_START event
                            yield StreamEvent.tool_start(
                                tool_name=tool_name,
                                parameters=tool_args_dict,
                            )

                            # Find corresponding result
                            result = next(
                                (r for r in tool_results if r.get("tool_name") == tool_name), None
                            )

                            if result and result.get("result"):
                                tool_data = result["result"]
                                if tool_data.get("success"):
                                    successful_count += 1
                                    # Emit TOOL_RESULT event
                                    yield StreamEvent.tool_result(
                                        tool_name=tool_name,
                                        result=tool_data.get("data", ""),
                                        duration_ms=execution_time * 1000,
                                    )
                                else:
                                    failed_count += 1
                                    error_msg = tool_data.get("error", "Errore sconosciuto")
                                    # Emit TOOL_ERROR event
                                    yield StreamEvent.tool_error(
                                        tool_name=tool_name,
                                        error=error_msg,
                                    )
                            else:
                                failed_count += 1
                                # Emit TOOL_ERROR event
                                yield StreamEvent.tool_error(
                                    tool_name=tool_name,
                                    error="Risultato non disponibile",
                                )

                        # Emit summary metrics event
                        if successful_count > 0 or failed_count > 0:
                            yield StreamEvent.metrics(
                                successful_tools=successful_count,
                                failed_tools=failed_count,
                                execution_time_ms=execution_time * 1000,
                            )

                        # Follow-up conversation with tool results
                        followup_messages = messages.copy()

                        # Add assistant message with tool calls
                        from openfatture.ai.domain.message import Message, Role

                        # Format tool calls for the assistant message
                        tool_calls_for_message = [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.name,
                                    "arguments": tc.arguments,
                                },
                            }
                            for tc in pending_tool_calls
                        ]

                        followup_messages.append(
                            Message(
                                role=Role.ASSISTANT,
                                content=accumulated_content,
                                tool_calls=tool_calls_for_message,
                            )
                        )

                        # Add tool results as separate messages
                        for result in tool_results:
                            tool_data = result.get("result", {})
                            followup_messages.append(
                                Message(
                                    role=Role.TOOL,
                                    content=str(tool_data.get("data", "")),
                                    tool_call_id=result.get("tool_call_id"),
                                )
                            )

                        # Stream follow-up response
                        # (Status message now handled by consumer via METRICS event)

                        followup_content = ""
                        async for followup_chunk in self.provider.stream(
                            messages=followup_messages,
                            temperature=self.config.temperature,
                            max_tokens=self.config.max_tokens,
                        ):
                            followup_content += followup_chunk
                            yield StreamEvent.content(followup_chunk)

                        logger.info(
                            "streaming_with_tools_completed",
                            agent=self.config.name,
                            initial_content_length=len(accumulated_content),
                            followup_content_length=len(followup_content),
                            tools_executed=len(tool_results),
                            successful_tools=successful_count,
                            failed_tools=failed_count,
                            execution_time=execution_time,
                        )
                    else:
                        # No tool calls - just log completion
                        logger.info(
                            "streaming_with_tools_completed_no_tools",
                            agent=self.config.name,
                            content_length=len(accumulated_content),
                        )

        except Exception as e:
            logger.error(
                "streaming_with_tools_failed",
                agent=self.config.name,
                error=str(e),
                accumulated_content_length=len(accumulated_content),
            )
            # Emit error as StreamEvent
            yield StreamEvent.content(f"\n\n❌ Errore durante l'esecuzione: {str(e)}")

    async def _build_prompt(self, context: ChatContext) -> list[Message]:
        """
        Build prompt messages for chat.

        Constructs a conversation with:
        - System prompt with context
        - Conversation history
        - Current user message

        Args:
            context: Chat context

        Returns:
            List of messages for LLM
        """
        messages = []

        # System prompt with context enrichment
        system_prompt = self._build_system_prompt(context)
        messages.append(Message(role=Role.SYSTEM, content=system_prompt))

        # Add conversation history
        for msg in context.conversation_history.get_messages(include_system=False):
            messages.append(msg)

        # Add current user message if not already in history
        if not messages or messages[-1].role != Role.USER:
            messages.append(Message(role=Role.USER, content=context.user_input))

        logger.debug(
            "prompt_built",
            agent=self.config.name,
            total_messages=len(messages),
            history_messages=len(context.conversation_history.messages),
        )

        return messages

    def _build_system_prompt(self, context: ChatContext) -> str:
        """
        Build system prompt with context enrichment.

        Args:
            context: Chat context

        Returns:
            System prompt string
        """
        parts = [
            "Sei un assistente AI specializzato per OpenFatture, un sistema di fatturazione elettronica italiana.",
            "",
            "Il tuo ruolo è:",
            "- Rispondere a domande su fatture e clienti",
            "- Fornire statistiche e insights",
            "- Guidare l'utente attraverso i workflow",
            "- Eseguire azioni tramite tools quando necessario",
            "",
            "Regole:",
            "- Usa un tono professionale ma friendly",
            "- Rispondi in italiano (salvo richiesta diversa)",
            "- Se non hai informazioni sufficienti, chiedi chiarimenti",
            "- Prima di eseguire azioni distruttive, chiedi conferma",
            "- Cita i dati specifici quando disponibili (numeri, date, importi)",
        ]

        # Add business context if available
        if context.current_year_stats:
            stats = context.current_year_stats
            parts.extend(
                [
                    "",
                    "Contesto corrente:",
                    f"- Anno: {stats.get('anno', 'N/A')}",
                    f"- Fatture totali: {stats.get('totale_fatture', 0)}",
                    f"- Importo totale: €{stats.get('importo_totale', 0):.2f}",
                ]
            )

        # Add available tools info
        if self.enable_tools and context.available_tools:
            parts.extend(
                [
                    "",
                    "Strumenti disponibili:",
                    f"- Hai accesso a {len(context.available_tools)} tools",
                    "- Usa i tools per recuperare dati o eseguire azioni",
                    "- I tools includono: ricerca fatture, statistiche, info clienti",
                ]
            )

        if context.relevant_documents:
            parts.extend(
                [
                    "",
                    "Documenti rilevanti dal sistema (fatture correlate):",
                ]
            )
            for doc in context.relevant_documents[:5]:
                parts.append(f"- {doc}")

        if context.knowledge_snippets:
            parts.extend(
                [
                    "",
                    "Fonti normative e note operative da consultare (cita come [numero]):",
                ]
            )
            for idx, snippet in enumerate(context.knowledge_snippets[:5], 1):
                citation = snippet.get("citation") or snippet.get("source") or f"Fonte {idx}"
                excerpt = snippet.get("excerpt", "")
                parts.append(f"[{idx}] {citation} — {excerpt}")

            parts.extend(
                [
                    "",
                    "Usa le fonti sopra per supportare la risposta e indica il riferimento con [numero].",
                ]
            )

        return "\n".join(parts)

    async def _parse_response(
        self,
        response: AgentResponse,
        context: ChatContext,
    ) -> AgentResponse:
        """
        Parse and process LLM response.

        Handles tool calls if present.

        Args:
            response: Raw LLM response
            context: Chat context

        Returns:
            Processed AgentResponse
        """
        # Check for tool calls in response
        # This is provider-specific - simplified here
        # In production, handle OpenAI/Anthropic tool calling formats

        # Add context info to metadata
        response.metadata["session_id"] = context.session_id
        response.metadata["message_count"] = len(context.conversation_history.messages)
        response.metadata["tools_available"] = len(context.available_tools)

        return response

    async def _handle_tool_calls(
        self,
        tool_calls: list[dict[str, Any]],
        context: ChatContext,
    ) -> list[dict[str, Any]]:
        """
        Execute tool calls from LLM.

        Args:
            tool_calls: List of tool call dictionaries
            context: Chat context

        Returns:
            List of tool results
        """
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call.get("function", {}).get("name")
            try:
                # Extract tool info
                parameters = tool_call.get("function", {}).get("arguments", {})

                if not tool_name:
                    continue

                logger.info(
                    "executing_tool",
                    tool_name=tool_name,
                    parameters=parameters,
                )

                # Execute tool
                result = await self.tool_registry.execute_tool(
                    tool_name=tool_name,
                    parameters=parameters,
                    confirm=False,  # In interactive UI, we'll handle confirmation
                )

                results.append(
                    {
                        "tool_call_id": tool_call.get("id"),
                        "tool_name": tool_name,
                        "result": result.to_dict(),
                    }
                )

                # Add to context
                context.tool_results.append(
                    {
                        "tool": tool_name,
                        "parameters": parameters,
                        "result": result.data,
                        "success": result.success,
                    }
                )

            except Exception as e:
                logger.error(
                    "tool_execution_failed",
                    tool_name=tool_name or "unknown",
                    error=str(e),
                )
                results.append(
                    {
                        "tool_call_id": tool_call.get("id"),
                        "tool_name": tool_name or "unknown",
                        "error": str(e),
                    }
                )

        return results

    def get_available_tools(self, category: str | None = None) -> list[str]:
        """
        Get list of available tool names.

        Args:
            category: Filter by category

        Returns:
            List of tool names
        """
        tools = self.tool_registry.list_tools(category=category)
        return [t.name for t in tools]

    def get_tools_schema(self, provider_format: str = "openai") -> list[dict[str, Any]]:
        """
        Get tools schema for function calling.

        Args:
            provider_format: Format ("openai" or "anthropic")

        Returns:
            List of tool schemas
        """
        if provider_format == "anthropic":
            return self.tool_registry.get_anthropic_tools()
        else:
            return self.tool_registry.get_openai_functions()

    async def generate_title(self, context: ChatContext) -> str:
        """
        Generate a title for the conversation based on first message.

        Args:
            context: Chat context

        Returns:
            Generated title
        """
        # Simple implementation - use first user message
        # In production, could use LLM to generate a summary title

        first_message = context.user_input[:50]
        if len(context.user_input) > 50:
            first_message += "..."

        return first_message
