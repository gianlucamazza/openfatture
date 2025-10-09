"""Conversational Chat Agent with tool calling capabilities."""

from typing import Any, Optional

from openfatture.ai.domain import AgentConfig, BaseAgent, Message, Role
from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.response import AgentResponse, ResponseStatus
from openfatture.ai.providers import BaseLLMProvider
from openfatture.ai.tools import ToolRegistry, get_tool_registry
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class ChatAgent(BaseAgent):
    """
    General-purpose conversational agent with tool calling.

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
        tool_registry: Optional[ToolRegistry] = None,
        enable_tools: bool = True,
        enable_streaming: bool = False,
    ) -> None:
        """
        Initialize Chat Agent.

        Args:
            provider: LLM provider instance
            tool_registry: Tool registry (uses global if None)
            enable_tools: Enable tool calling
            enable_streaming: Enable streaming responses
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
            streaming_enabled=enable_streaming,
        )

        super().__init__(config=config, provider=provider)

        # Tool management
        self.tool_registry = tool_registry or get_tool_registry()
        self.enable_tools = enable_tools

        logger.info(
            "chat_agent_initialized",
            provider=provider.provider_name,
            model=provider.model,
            tools_enabled=enable_tools,
            streaming_enabled=enable_streaming,
        )

    async def validate_input(self, context: ChatContext) -> tuple[bool, Optional[str]]:
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
            try:
                # Extract tool info
                tool_name = tool_call.get("function", {}).get("name")
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
                    tool_name=tool_name,
                    error=str(e),
                )
                results.append(
                    {
                        "tool_call_id": tool_call.get("id"),
                        "tool_name": tool_name,
                        "error": str(e),
                    }
                )

        return results

    def get_available_tools(self, category: Optional[str] = None) -> list[str]:
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
