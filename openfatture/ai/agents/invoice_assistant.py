"""Invoice Assistant Agent - Generates professional invoice descriptions."""

from openfatture.ai.agents.models import InvoiceDescriptionOutput
from openfatture.ai.domain import AgentConfig, BaseAgent, Message, Role
from openfatture.ai.domain.context import InvoiceContext
from openfatture.ai.domain.prompt import PromptManager, create_prompt_manager
from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.providers import BaseLLMProvider
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class InvoiceAssistantAgent(BaseAgent):
    """
    AI agent for generating professional invoice descriptions.

    Takes brief service descriptions and expands them into detailed,
    professional text suitable for Italian FatturaPA electronic invoices.

    Features:
    - Expands brief descriptions to professional format
    - Suggests deliverables based on service type
    - Supports IT/EN (primarily IT for Italian invoices)
    - Structured output with Pydantic validation
    - Optional RAG with previous invoices (future)

    Example:
        Input: "3 ore consulenza web"
        Output: Detailed description with activities, deliverables, competenze
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        prompt_manager: PromptManager | None = None,
        use_structured_output: bool = True,
    ) -> None:
        """
        Initialize Invoice Assistant agent.

        Args:
            provider: LLM provider instance
            prompt_manager: Prompt manager (uses default if None)
            use_structured_output: Use Pydantic structured outputs
        """
        # Agent configuration
        config = AgentConfig(
            name="invoice_assistant",
            description="Generates professional Italian invoice descriptions",
            version="1.0.0",
            temperature=0.7,  # Creative but focused
            max_tokens=800,  # Enough for detailed descriptions
            tools_enabled=False,
            memory_enabled=False,
            rag_enabled=True,
        )

        super().__init__(config=config, provider=provider)

        # Prompt management
        self.prompt_manager = prompt_manager or create_prompt_manager()
        self.use_structured_output = use_structured_output

        logger.info(
            "invoice_assistant_initialized",
            provider=provider.provider_name,
            model=provider.model,
            structured_output=use_structured_output,
        )

    async def validate_input(self, context: InvoiceContext) -> tuple[bool, str | None]:
        """
        Validate invoice context before processing.

        Args:
            context: Invoice context with service details

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if not context.servizio_base or len(context.servizio_base.strip()) == 0:
            return False, "servizio_base è richiesto"

        if len(context.servizio_base) > 500:
            return False, "servizio_base troppo lungo (max 500 caratteri)"

        # Validate hours if provided
        if context.ore_lavorate is not None:
            if context.ore_lavorate <= 0:
                return False, "ore_lavorate deve essere positivo"
            if context.ore_lavorate > 1000:
                return False, "ore_lavorate sembra irrealistico (>1000)"

        return True, None

    async def _build_prompt(self, context: InvoiceContext) -> list[Message]:
        """
        Build prompt messages for invoice description generation.

        Args:
            context: Invoice context

        Returns:
            List of messages for LLM
        """
        # Prepare variables for template
        template_vars = {
            "servizio_base": context.servizio_base,
            "ore_lavorate": context.ore_lavorate or 0,
            "tariffa_oraria": context.tariffa_oraria,
            "tecnologie": context.tecnologie,
            "progetto": context.progetto,
            "cliente": context.cliente,
            "deliverables": context.deliverables,
        }

        # Render prompts from template
        try:
            system_prompt, user_prompt = self.prompt_manager.render_with_examples(
                "invoice_assistant", template_vars
            )

            logger.debug(
                "prompt_rendered",
                agent=self.config.name,
                system_length=len(system_prompt),
                user_length=len(user_prompt),
            )

        except FileNotFoundError:
            logger.warning(
                "prompt_template_not_found",
                agent=self.config.name,
                message="Using fallback prompt",
            )

            # Fallback prompt if YAML not found
            system_prompt = self._get_fallback_system_prompt()
            user_prompt = self._build_fallback_user_prompt(context)

        # Build message list
        messages = [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=user_prompt),
        ]

        context_message = self._build_context_message(context)
        if context_message:
            messages.insert(1, Message(role=Role.SYSTEM, content=context_message))

        return messages

    async def _parse_response(
        self,
        response: AgentResponse,
        context: InvoiceContext,
    ) -> AgentResponse:
        """
        Parse and validate LLM response.

        If structured output is enabled, tries to parse as Pydantic model.
        Falls back to plain text if parsing fails.

        Args:
            response: Raw LLM response
            context: Invoice context

        Returns:
            Processed AgentResponse with metadata
        """
        # If using structured output, try to parse
        if self.use_structured_output:
            try:
                import json

                data = json.loads(response.content)
                model = InvoiceDescriptionOutput(**data)

                # Add parsed model to metadata
                response.metadata["parsed_model"] = model.model_dump()
                response.metadata["is_structured"] = True

                logger.info(
                    "structured_output_parsed",
                    agent=self.config.name,
                    deliverables_count=len(model.deliverables),
                    competenze_count=len(model.competenze),
                )

            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(
                    "structured_output_parse_failed",
                    agent=self.config.name,
                    error=str(e),
                    message="Falling back to text response",
                )
                response.metadata["is_structured"] = False

        else:
            response.metadata["is_structured"] = False

        # Add context info to metadata (useful for auditing)
        response.metadata["servizio_base"] = context.servizio_base
        response.metadata["ore_lavorate"] = context.ore_lavorate
        response.metadata["lingua"] = context.lingua_preferita

        return response

    def _build_context_message(self, context: InvoiceContext) -> str | None:
        """
        Build additional context message with RAG snippets if available.

        Args:
            context: Invoice context

        Returns:
            Context string or None
        """
        lines: list[str] = []

        if context.relevant_documents:
            lines.append("Documenti simili recuperati dal sistema:")
            for doc in context.relevant_documents[:3]:
                lines.append(f"- {doc}")

        if context.knowledge_snippets:
            lines.append("")
            lines.append("Linee guida e note rilevanti (cita come [numero]):")
            for idx, snippet in enumerate(context.knowledge_snippets[:3], 1):
                citation = snippet.get("citation") or snippet.get("source") or f"Fonte {idx}"
                excerpt = snippet.get("excerpt", "")
                lines.append(f"[{idx}] {citation} — {excerpt}")
            lines.append(
                "Utilizza le fonti per motivare la descrizione e cita il numero corrispondente."
            )

        return "\n".join(lines).strip() if lines else None

    # Fallback prompts (if YAML not found)

    def _get_fallback_system_prompt(self) -> str:
        """Get fallback system prompt."""
        return """Sei un esperto assistente per fatture elettroniche italiane.
Il tuo compito è espandere brevi descrizioni di servizi professionali in descrizioni
dettagliate e professionali adatte per fatture FatturaPA.

Regole:
- Usa linguaggio professionale ma chiaro in italiano
- Includi dettagli concreti sulle attività svolte
- Suggerisci deliverables quando pertinenti
- Mantieni focus sul valore fornito al cliente
- Rispetta limite di 1000 caratteri per FatturaPA
- Rispondi SOLO con JSON nel formato richiesto
"""

    def _build_fallback_user_prompt(self, context: InvoiceContext) -> str:
        """Build fallback user prompt."""
        prompt_parts = [
            f"Servizio: {context.servizio_base}",
            f"Ore: {context.ore_lavorate or 'Non specificato'}",
        ]

        if context.tecnologie:
            prompt_parts.append(f"Tecnologie: {', '.join(context.tecnologie)}")

        if context.progetto:
            prompt_parts.append(f"Progetto: {context.progetto}")

        if context.cliente:
            prompt_parts.append(f"Cliente: {context.cliente.denominazione}")

        prompt_parts.append("\nGenera una descrizione professionale in formato JSON.")

        return "\n".join(prompt_parts)
