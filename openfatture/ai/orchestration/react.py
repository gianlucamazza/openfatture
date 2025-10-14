"""ReAct (Reasoning + Acting) orchestrator for tool calling.

Implements the ReAct pattern for LLM providers that don't support
native function calling (like Ollama). Uses prompt engineering to
guide the LLM through a Thought → Action → Observation loop.

Reference: https://arxiv.org/abs/2210.03629
"""

from collections.abc import AsyncIterator
from typing import Any

from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.message import Message, Role
from openfatture.ai.orchestration.parsers import ParsedResponse, ToolCallParser
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.ai.tools.registry import ToolRegistry
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class ReActOrchestrator:
    """
    ReAct orchestrator for tool calling via prompt engineering.

    Manages the loop:
    1. LLM generates: Thought + Action + Action Input
    2. Parse tool call from response
    3. Execute tool via registry
    4. Send Observation back to LLM
    5. Repeat until Final Answer

    Designed for providers like Ollama that don't support
    native function calling but can follow structured prompts.
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        tool_registry: ToolRegistry,
        max_iterations: int = 5,
        parser: ToolCallParser | None = None,
    ) -> None:
        """
        Initialize ReAct orchestrator.

        Args:
            provider: LLM provider instance
            tool_registry: Tool registry for executing tools
            max_iterations: Maximum ReAct loop iterations
            parser: Tool call parser (creates default if None)
        """
        self.provider = provider
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.parser = parser or ToolCallParser()

        # Metrics tracking
        self.metrics = {
            "total_executions": 0,
            "tool_calls_attempted": 0,
            "tool_calls_succeeded": 0,
            "tool_calls_failed": 0,
            "max_iterations_reached": 0,
            "total_iterations": 0,
        }

        logger.info(
            "react_orchestrator_initialized",
            provider=provider.provider_name,
            model=provider.model,
            max_iterations=max_iterations,
        )

    async def execute(self, context: ChatContext) -> str:
        """
        Execute ReAct loop and return final answer.

        Args:
            context: Chat context with user input and history

        Returns:
            Final answer text
        """
        # Track execution
        self.metrics["total_executions"] += 1

        # Build initial messages with ReAct prompt
        messages = self._build_react_messages(context)

        iteration = 0
        final_answer = ""

        logger.info(
            "react_loop_started",
            correlation_id=context.correlation_id,
            max_iterations=self.max_iterations,
        )

        while iteration < self.max_iterations:
            iteration += 1

            logger.debug(
                "react_iteration",
                iteration=iteration,
                max_iterations=self.max_iterations,
                message_count=len(messages),
            )

            # Get LLM response with temperature=0.0 for deterministic tool calling
            response = await self.provider.generate(messages=messages, temperature=0.0)
            response_text = response.content

            # Log raw output for debugging
            logger.debug(
                "react_raw_response",
                iteration=iteration,
                response_preview=response_text[:500],
                response_length=len(response_text),
            )

            # Parse response
            parsed = self.parser.parse(response_text)

            # Check if final answer
            if parsed.is_final:
                final_answer = parsed.content
                logger.info(
                    "react_loop_completed",
                    iterations=iteration,
                    answer_preview=final_answer[:100],
                )
                break

            # Execute tool call
            if parsed.tool_call:
                tool_call = parsed.tool_call
                self.metrics["tool_calls_attempted"] += 1

                # Add assistant message with tool call
                messages.append(
                    Message(
                        role=Role.ASSISTANT,
                        content=response_text,
                    )
                )

                # Execute tool
                logger.info(
                    "executing_tool_in_react",
                    tool_name=tool_call.tool_name,
                    parameters=tool_call.parameters,
                    iteration=iteration,
                )

                try:
                    result = await self.tool_registry.execute_tool(
                        tool_name=tool_call.tool_name,
                        parameters=tool_call.parameters,
                        confirm=False,
                    )

                    if result.success:
                        observation = self._format_observation(result.data)
                        self.metrics["tool_calls_succeeded"] += 1
                    else:
                        observation = f"Error: {result.error}"
                        self.metrics["tool_calls_failed"] += 1

                    logger.info(
                        "tool_executed_in_react",
                        tool_name=tool_call.tool_name,
                        success=result.success,
                        observation_length=len(str(observation)),
                    )

                except Exception as e:
                    observation = f"Error executing tool: {str(e)}"
                    self.metrics["tool_calls_failed"] += 1
                    logger.error(
                        "tool_execution_failed_in_react",
                        tool_name=tool_call.tool_name,
                        error=str(e),
                    )

                # Add observation message
                messages.append(
                    Message(
                        role=Role.USER,
                        content=f"Observation: {observation}",
                    )
                )

            else:
                # No tool call and not final answer - treat as final
                logger.warning(
                    "react_no_tool_or_final",
                    message="Treating as final answer",
                    iteration=iteration,
                )
                final_answer = response_text
                break

        # Max iterations reached
        if not final_answer:
            self.metrics["max_iterations_reached"] += 1
            logger.warning(
                "react_max_iterations_reached",
                iterations=iteration,
                message="Returning last response",
            )
            final_answer = (
                f"Ho raggiunto il limite di iterazioni ({self.max_iterations}). "
                f"Ecco quello che ho trovato finora:\n\n{messages[-1].content if messages else 'Nessun risultato'}"
            )

        # Track total iterations
        self.metrics["total_iterations"] += iteration

        return final_answer

    async def stream(self, context: ChatContext) -> AsyncIterator[str]:
        """
        Execute ReAct loop with streaming of final answer.

        The entire ReAct loop is executed (buffered), then the
        final answer is streamed token-by-token for better UX.

        Args:
            context: Chat context with user input and history

        Yields:
            Chunks of final answer text
        """
        # Build initial messages with ReAct prompt
        messages = self._build_react_messages(context)

        iteration = 0

        logger.info(
            "react_stream_started",
            correlation_id=context.correlation_id,
            max_iterations=self.max_iterations,
        )

        while iteration < self.max_iterations:
            iteration += 1

            logger.debug(
                "react_stream_iteration",
                iteration=iteration,
                max_iterations=self.max_iterations,
            )

            # Buffer response for parsing (temperature=0.0 for deterministic tool calling)
            response_buffer = ""
            async for chunk in self.provider.stream(messages=messages, temperature=0.0):
                response_buffer += chunk

            # Log raw output for debugging
            logger.debug(
                "react_stream_raw_response",
                iteration=iteration,
                response_preview=response_buffer[:500],
                response_length=len(response_buffer),
            )

            # Parse buffered response
            parsed = self.parser.parse(response_buffer)

            # Check if final answer
            if parsed.is_final:
                logger.info(
                    "react_stream_final_answer",
                    iterations=iteration,
                    answer_length=len(parsed.content),
                )

                # Stream final answer token-by-token
                # Split into words for smoother streaming
                words = parsed.content.split()
                for i, word in enumerate(words):
                    if i > 0:
                        yield " "
                    yield word

                break

            # Execute tool call
            if parsed.tool_call:
                tool_call = parsed.tool_call

                # Add assistant message
                messages.append(
                    Message(
                        role=Role.ASSISTANT,
                        content=response_buffer,
                    )
                )

                # Execute tool
                logger.info(
                    "executing_tool_in_stream",
                    tool_name=tool_call.tool_name,
                    parameters=tool_call.parameters,
                    iteration=iteration,
                )

                try:
                    result = await self.tool_registry.execute_tool(
                        tool_name=tool_call.tool_name,
                        parameters=tool_call.parameters,
                        confirm=False,
                    )

                    if result.success:
                        observation = self._format_observation(result.data)
                    else:
                        observation = f"Error: {result.error}"

                except Exception as e:
                    observation = f"Error executing tool: {str(e)}"
                    logger.error(
                        "tool_execution_error_in_stream",
                        tool_name=tool_call.tool_name,
                        error=str(e),
                    )

                # Add observation
                messages.append(
                    Message(
                        role=Role.USER,
                        content=f"Observation: {observation}",
                    )
                )

            else:
                # No tool call and not final - treat as final
                logger.warning(
                    "stream_no_tool_or_final",
                    message="Treating as final answer",
                    iteration=iteration,
                )
                words = response_buffer.split()
                for i, word in enumerate(words):
                    if i > 0:
                        yield " "
                    yield word
                break

        # Max iterations reached
        if iteration >= self.max_iterations:
            logger.warning(
                "stream_max_iterations",
                iterations=iteration,
                message="Returning summary",
            )
            error_msg = f"Ho raggiunto il limite di iterazioni ({self.max_iterations})."
            yield error_msg

    def _build_react_messages(self, context: ChatContext) -> list[Message]:
        """
        Build messages with ReAct system prompt.

        Args:
            context: Chat context

        Returns:
            List of messages including ReAct instructions
        """
        # System prompt with ReAct instructions
        system_prompt = self._build_react_system_prompt(context)

        messages = [Message(role=Role.SYSTEM, content=system_prompt)]

        # Add conversation history
        for msg in context.conversation_history.get_messages(include_system=False):
            messages.append(msg)

        # Add current user input if not already in history
        if not messages or messages[-1].role != Role.USER:
            messages.append(Message(role=Role.USER, content=context.user_input))

        return messages

    def _build_react_system_prompt(self, context: ChatContext) -> str:
        """
        Build ReAct system prompt with tool descriptions.

        Modern implementation (2025) with:
        - XML tags for robust parsing
        - Few-shot examples
        - Explicit instructions against hallucination
        - JSON format for tool inputs

        Args:
            context: Chat context

        Returns:
            System prompt string
        """
        tools = self.tool_registry.list_tools(enabled_only=True)

        tool_descriptions = []
        for tool in tools:
            if tool.parameters:
                params_desc = ", ".join(
                    f"{param.name}: {param.description}" for param in tool.parameters
                )
                tool_descriptions.append(
                    f"- {tool.name}: {tool.description}\n  Parametri: {params_desc}"
                )
            else:
                tool_descriptions.append(f"- {tool.name}: {tool.description}")

        tools_section = "\n".join(tool_descriptions) if tool_descriptions else "Nessun tool disponibile"

        prompt = f"""Sei un assistente AI per OpenFatture, sistema di fatturazione elettronica italiana.

⚠️ CRITICAL: Devi SEMPRE usare i tools disponibili per ottenere dati reali. NON INVENTARE MAI dati.

USA QUESTO FORMATO ESATTO con tag XML:

<thought>Il tuo ragionamento qui</thought>
<action>nome_tool</action>
<action_input>{{"parametro": "valore"}}</action_input>

OPPURE quando hai la risposta completa:

<final_answer>La tua risposta formattata per l'utente</final_answer>

TOOLS DISPONIBILI:
{tools_section}

═══════════════════════════════════════════════════════════════
ESEMPI COMPLETI:
═══════════════════════════════════════════════════════════════

📋 ESEMPIO 1: Statistiche fatture
User: Quante fatture ho emesso quest'anno?

<thought>Devo ottenere le statistiche delle fatture per l'anno corrente 2025 usando il tool get_invoice_stats</thought>
<action>get_invoice_stats</action>
<action_input>{{"year": 2025}}</action_input>

Observation: {{"totale_fatture": 42, "importo_totale": 15000.0, "per_stato": {{"bozza": 5, "da_inviare": 10, "inviata": 27}}}}

<thought>Ho ricevuto i dati reali dal sistema. Ora posso fornire una risposta completa e formattata</thought>
<final_answer>Hai emesso **42 fatture** nel 2025 per un totale di **€15.000,00**.

Distribuzione per stato:
- Bozze: 5
- Da inviare: 10
- Inviate: 27</final_answer>

═══════════════════════════════════════════════════════════════

📋 ESEMPIO 2: Ricerca fatture
User: Mostrami le ultime 3 fatture

<thought>Devo cercare le fatture più recenti usando search_invoices con limit=3</thought>
<action>search_invoices</action>
<action_input>{{"limit": 3, "order_by": "data_emissione"}}</action_input>

Observation: [{{"numero": "003/2025", "cliente": "Acme Corp", "totale": 1200.0, "data": "2025-01-20"}}, {{"numero": "002/2025", "cliente": "Beta Ltd", "totale": 850.0, "data": "2025-01-15"}}, {{"numero": "001/2025", "cliente": "Gamma SpA", "totale": 2100.0, "data": "2025-01-10"}}]

<thought>Ho ricevuto la lista delle fatture. Le presento in una tabella chiara</thought>
<final_answer>Ecco le ultime 3 fatture:

| N. Fattura | Data       | Cliente    | Importo    |
|------------|------------|------------|------------|
| 003/2025   | 20/01/2025 | Acme Corp  | €1.200,00  |
| 002/2025   | 15/01/2025 | Beta Ltd   | €850,00    |
| 001/2025   | 10/01/2025 | Gamma SpA  | €2.100,00  |</final_answer>

═══════════════════════════════════════════════════════════════

REGOLE CRITICHE:
✅ USA SEMPRE i tools - non inventare dati
✅ Segui ESATTAMENTE il formato XML
✅ JSON valido in <action_input>
✅ Rispondi in italiano
✅ Formatta con tabelle/liste quando appropriato

❌ NON inventare numeri fattura
❌ NON inventare nomi clienti
❌ NON inventare importi
❌ NON rispondere senza usare tools quando sono disponibili

Ora rispondi alla domanda dell'utente seguendo gli esempi sopra."""

        # Add business context if available
        if context.current_year_stats:
            stats = context.current_year_stats
            prompt += f"\n\n📊 CONTESTO SISTEMA:\n"
            prompt += f"- Anno corrente: {stats.get('anno', 'N/A')}\n"
            prompt += f"- Fatture totali YTD: {stats.get('totale_fatture', 0)}\n"
            prompt += f"- Importo totale YTD: €{stats.get('importo_totale', 0):.2f}\n"

        return prompt

    def _format_observation(self, data: Any) -> str:
        """
        Format tool result as observation text.

        Args:
            data: Tool result data

        Returns:
            Formatted observation string
        """
        if data is None:
            return "Nessun risultato"

        if isinstance(data, str):
            return data

        if isinstance(data, dict):
            # Format dict nicely
            lines = []
            for key, value in data.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)

        if isinstance(data, list):
            # Format list items
            if not data:
                return "Lista vuota"

            # If list of dicts, format as table-like
            if data and isinstance(data[0], dict):
                lines = []
                for i, item in enumerate(data, 1):
                    item_str = ", ".join(f"{k}={v}" for k, v in item.items())
                    lines.append(f"{i}. {item_str}")
                return "\n".join(lines)

            # Simple list
            return ", ".join(str(item) for item in data)

        return str(data)

    def get_stats(self) -> dict[str, Any]:
        """
        Get orchestrator statistics (legacy method).

        Returns:
            Dictionary with stats
        """
        return {
            "provider": self.provider.provider_name,
            "model": self.provider.model,
            "max_iterations": self.max_iterations,
            "parser_stats": self.parser.get_stats(),
        }

    def get_metrics(self) -> dict[str, Any]:
        """
        Get comprehensive orchestrator metrics including tool calling performance.

        Returns:
            Dictionary with metrics:
            - total_executions: Number of execute() calls
            - tool_calls_attempted: Tools attempted to execute
            - tool_calls_succeeded: Tools executed successfully
            - tool_calls_failed: Tools that failed execution
            - tool_call_success_rate: Success rate (0.0-1.0)
            - max_iterations_reached: Times max iterations hit
            - avg_iterations: Average iterations per execution
            - parser_stats: Parser statistics (XML vs legacy rates)
        """
        # Calculate derived metrics
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
            "parser_stats": self.parser.get_stats(),
            "provider": self.provider.provider_name,
            "model": self.provider.model,
        }
