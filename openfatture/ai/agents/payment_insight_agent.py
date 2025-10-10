"""Agent specialized in analyzing bank transaction narratives."""

from __future__ import annotations

import json

import structlog
from pydantic import ValidationError

from openfatture.ai.agents.models import PaymentInsightOutput
from openfatture.ai.domain import AgentConfig, BaseAgent, Message, Role
from openfatture.ai.domain.context import PaymentInsightContext
from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.providers import BaseLLMProvider

logger = structlog.get_logger(__name__)


class PaymentInsightAgent(BaseAgent):
    """LLM agent that classifies causali to support partial payment detection."""

    def __init__(
        self,
        provider: BaseLLMProvider,
        temperature: float = 0.2,
        max_tokens: int = 600,
    ) -> None:
        config = AgentConfig(
            name="payment_insight",
            description="Analizza causali bancarie per individuare pagamenti parziali e riferimenti fattura",
            version="1.0.0",
            temperature=temperature,
            max_tokens=max_tokens,
            tools_enabled=False,
            memory_enabled=False,
        )
        super().__init__(config=config, provider=provider)

    async def validate_input(self, context: PaymentInsightContext) -> tuple[bool, str | None]:
        if not context.transaction_description and not context.transaction_reference:
            return False, "transaction_description or transaction_reference required"
        if context.transaction_amount is None:
            return False, "transaction_amount richiesto"
        return True, None

    async def _build_prompt(self, context: PaymentInsightContext) -> list[Message]:
        candidate_lines = []
        for candidate in context.candidate_payments[:10]:
            candidate_lines.append(
                " - ID {payment_id} | Fattura {invoice_number} | Residuo €{outstanding_amount:.2f} | "
                "Scadenza {due_date}".format(
                    payment_id=candidate.get("payment_id", "N/A"),
                    invoice_number=candidate.get("invoice_number", "N/A"),
                    outstanding_amount=candidate.get("outstanding_amount", 0.0),
                    due_date=candidate.get("due_date", "N/A"),
                )
            )

        candidates_block = (
            "\n".join(candidate_lines) if candidate_lines else " - Nessun candidato disponibile"
        )

        user_prompt = (
            "Analizza la causale di un movimento bancario e fornisci un output JSON conforme allo schema richiesto.\n"
            "Dettagli movimento:\n"
            f"Descrizione: {context.transaction_description or 'N/D'}\n"
            f"Riferimento: {context.transaction_reference or 'N/D'}\n"
            f"Importo movimento: €{context.transaction_amount:.2f}\n"
            f"Data operazione: {context.transaction_date.isoformat()}\n"
            f"Controparte: {context.counterparty or 'N/D'}\n"
            f"IBAN controparte: {context.counterparty_iban or 'N/D'}\n\n"
            "Pagamenti candidati:\n"
            f"{candidates_block}\n\n"
            "Indica se la causale suggerisce un pagamento parziale/acconto, eventuali numeri di fattura coinvolti,"
            " parole chiave rilevanti e un eventuale importo suggerito da allocare se differente dall'intero movimento."
        )

        system_prompt = (
            "Sei un analista finanziario che classifica causali bancarie. "
            "Rispondi SOLO con JSON conforme allo schema: "
            '{"probable_invoice_numbers": ["..."], '
            '"is_partial_payment": true|false, '
            '"suggested_allocation_amount": null|float, '
            '"keywords": ["..."], '
            '"confidence": float, '
            '"summary": null|string}.'
        )

        return [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=user_prompt),
        ]

    async def _parse_response(
        self,
        response: AgentResponse,
        context: PaymentInsightContext,
    ) -> AgentResponse:
        try:
            data = json.loads(response.content)
            model = PaymentInsightOutput(**data)
            response.metadata["parsed_model"] = model.model_dump()
            response.metadata["is_structured"] = True
            logger.debug(
                "payment_insight_parsed",
                probable_invoice_numbers=len(model.probable_invoice_numbers),
                is_partial=model.is_partial_payment,
            )
        except (json.JSONDecodeError, ValidationError) as exc:
            response.metadata["is_structured"] = False
            logger.warning(
                "payment_insight_parse_failed",
                error=str(exc),
                raw_response=response.content[:200],
            )

        return response
