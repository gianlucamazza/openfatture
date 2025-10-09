"""Tax Advisor Agent - Suggests correct VAT treatment for Italian invoices."""

from typing import Optional

from openfatture.ai.agents.models import TaxSuggestionOutput
from openfatture.ai.domain import AgentConfig, BaseAgent, Message, Role
from openfatture.ai.domain.context import TaxContext
from openfatture.ai.domain.prompt import PromptManager, create_prompt_manager
from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.providers import BaseLLMProvider
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class TaxAdvisorAgent(BaseAgent):
    """
    AI agent for suggesting correct VAT treatment for Italian invoices.

    Analyzes service/product descriptions and suggests:
    - Correct VAT rate (22%, 10%, 5%, 4%, 0%)
    - Natura IVA codes (N1-N7) for exempt operations
    - Reverse charge applicability
    - Split payment for Public Administration
    - Legal references and explanations

    Features:
    - Knowledge of Italian tax regulations
    - Supports special regimes (forfettario, agricoltura, etc.)
    - Structured output with confidence scores
    - Legal references (DPR 633/72, etc.)

    Example:
        Input: "consulenza IT per azienda edile"
        Output: {
            "aliquota_iva": 22,
            "reverse_charge": True,
            "codice_natura": "N6.2",
            "spiegazione": "Reverse charge edilizia...",
            "riferimento_normativo": "Art. 17, c. 6, lett. a-ter, DPR 633/72"
        }
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        prompt_manager: Optional[PromptManager] = None,
        use_structured_output: bool = True,
    ) -> None:
        """
        Initialize Tax Advisor agent.

        Args:
            provider: LLM provider instance
            prompt_manager: Prompt manager (uses default if None)
            use_structured_output: Use Pydantic structured outputs
        """
        # Agent configuration
        config = AgentConfig(
            name="tax_advisor",
            description="Suggests correct VAT treatment for Italian invoices",
            version="1.0.0",
            temperature=0.3,  # Lower temperature for accuracy
            max_tokens=800,
            tools_enabled=False,
            memory_enabled=False,
            rag_enabled=False,
        )

        super().__init__(config=config, provider=provider)

        # Prompt management
        self.prompt_manager = prompt_manager or create_prompt_manager()
        self.use_structured_output = use_structured_output

        logger.info(
            "tax_advisor_initialized",
            provider=provider.provider_name,
            model=provider.model,
            structured_output=use_structured_output,
        )

    async def validate_input(self, context: TaxContext) -> tuple[bool, Optional[str]]:
        """
        Validate tax context before processing.

        Args:
            context: Tax context with service/product details

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if not context.tipo_servizio or len(context.tipo_servizio.strip()) == 0:
            return False, "tipo_servizio è richiesto"

        if len(context.tipo_servizio) > 500:
            return False, "tipo_servizio troppo lungo (max 500 caratteri)"

        # Validate amount if provided
        if context.importo is not None:
            if context.importo < 0:
                return False, "importo non può essere negativo"
            if context.importo > 1_000_000:
                return False, "importo sembra irrealistico (>1M)"

        # Validate country code
        if context.paese_cliente and len(context.paese_cliente) != 2:
            return False, "paese_cliente deve essere codice ISO 2 lettere (es. IT, FR)"

        return True, None

    async def _build_prompt(self, context: TaxContext) -> list[Message]:
        """
        Build prompt messages for VAT suggestion.

        Args:
            context: Tax context

        Returns:
            List of messages for LLM
        """
        # Prepare variables for template
        template_vars = {
            "tipo_servizio": context.tipo_servizio,
            "categoria_servizio": context.categoria_servizio,
            "importo": context.importo or 0,
            "cliente_pa": context.cliente_pa,
            "cliente_estero": context.cliente_estero,
            "paese_cliente": context.paese_cliente,
            "reverse_charge": context.reverse_charge,
            "split_payment": context.split_payment,
            "regime_speciale": context.regime_speciale,
            "codice_ateco": context.codice_ateco,
            "contratto_tipo": context.contratto_tipo,
        }

        # Render prompts from template
        try:
            system_prompt, user_prompt = self.prompt_manager.render_with_examples(
                "tax_advisor", template_vars
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

        return messages

    async def _parse_response(
        self,
        response: AgentResponse,
        context: TaxContext,
    ) -> AgentResponse:
        """
        Parse and validate LLM response.

        If structured output is enabled, tries to parse as Pydantic model.
        Falls back to plain text if parsing fails.

        Args:
            response: Raw LLM response
            context: Tax context

        Returns:
            Processed AgentResponse with metadata
        """
        # If using structured output, try to parse
        if self.use_structured_output:
            try:
                import json

                data = json.loads(response.content)
                model = TaxSuggestionOutput(**data)

                # Add parsed model to metadata
                response.metadata["parsed_model"] = model.model_dump()
                response.metadata["is_structured"] = True

                logger.info(
                    "structured_output_parsed",
                    agent=self.config.name,
                    aliquota=model.aliquota_iva,
                    reverse_charge=model.reverse_charge,
                    split_payment=model.split_payment,
                    confidence=model.confidence,
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

        # Add context info to metadata
        response.metadata["tipo_servizio"] = context.tipo_servizio
        response.metadata["cliente_pa"] = context.cliente_pa
        response.metadata["cliente_estero"] = context.cliente_estero

        return response

    # Fallback prompts (if YAML not found)

    def _get_fallback_system_prompt(self) -> str:
        """Get fallback system prompt."""
        return """Sei un esperto consulente fiscale italiano specializzato in IVA e FatturaPA.

Il tuo compito è suggerire il corretto trattamento fiscale IVA per servizi e prodotti,
seguendo la normativa italiana.

ALIQUOTE IVA:
- 22%: Aliquota ordinaria (default)
- 10%: Aliquota ridotta (alcuni alimenti, edilizia sociale)
- 5%: Aliquota super-ridotta (alimenti prima necessità)
- 4%: Aliquota minima (libri, prodotti agricoli)
- 0%: Esente (formazione, sanità, alcuni servizi professionali)

CODICI NATURA (per aliquota 0%):
- N1: Escluse ex art.15
- N2: Non soggette (fuori campo IVA)
- N3: Non imponibili (export, intracomunitarie)
- N4: Esenti (formazione, sanità)
- N5: Regime del margine
- N6: Reverse charge (inversione contabile)
- N7: IVA assolta in altro stato UE

REVERSE CHARGE (Art. 17 DPR 633/72):
Applicabile per: edilizia, subappalti, pulizia, demolizione, installazione impianti,
settore energetico, cessione rottami, telecomunicazioni.

SPLIT PAYMENT:
Obbligatorio per fatture emesse verso Pubblica Amministrazione.
L'IVA è versata direttamente dalla PA all'Erario.

REGIME FORFETTARIO (RF19):
No addebito IVA. Dicitura: "Operazione senza applicazione dell'IVA ai sensi dell'art. 1, comma 58, L. 190/2014"

Rispondi SOLO con JSON nel formato richiesto, con spiegazioni chiare e riferimenti normativi."""

    def _build_fallback_user_prompt(self, context: TaxContext) -> str:
        """Build fallback user prompt."""
        prompt_parts = [
            f"Servizio/Prodotto: {context.tipo_servizio}",
        ]

        if context.categoria_servizio:
            prompt_parts.append(f"Categoria: {context.categoria_servizio}")

        if context.importo:
            prompt_parts.append(f"Importo: €{context.importo:.2f}")

        if context.cliente_pa:
            prompt_parts.append("Cliente: Pubblica Amministrazione")

        if context.cliente_estero:
            prompt_parts.append(f"Cliente estero: {context.paese_cliente or 'non specificato'}")

        if context.codice_ateco:
            prompt_parts.append(f"Codice ATECO: {context.codice_ateco}")

        prompt_parts.append("\nSuggerisci il corretto trattamento fiscale IVA in formato JSON.")

        return "\n".join(prompt_parts)
