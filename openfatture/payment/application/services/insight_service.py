"""AI-backed service for analyzing bank transaction narratives."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from openfatture.ai.domain.context import PaymentInsightContext
from openfatture.ai.domain.response import ResponseStatus
from openfatture.payment.domain.value_objects import PaymentInsight

if TYPE_CHECKING:
    from ....ai.agents.payment_insight_agent import PaymentInsightAgent
    from ...domain.models import BankTransaction
    from ...storage.database.models import Pagamento

logger = structlog.get_logger()


class TransactionInsightService:
    """Facade around PaymentInsightAgent providing domain-friendly insights."""

    def __init__(self, agent: PaymentInsightAgent) -> None:
        self.agent = agent

    async def analyze(
        self,
        transaction: BankTransaction,
        payments: list[Pagamento],
    ) -> PaymentInsight | None:
        """Analyze a bank transaction description/reference and return AI insight."""

        context = PaymentInsightContext(
            user_input=transaction.description or transaction.reference or "",
            transaction_description=transaction.description or "",
            transaction_reference=transaction.reference,
            transaction_amount=float(transaction.amount),
            transaction_date=transaction.date,
            counterparty=transaction.counterparty,
            counterparty_iban=transaction.counterparty_iban,
            candidate_payments=[self._serialize_payment(p) for p in payments],
        )

        try:
            response = await self.agent.execute(context)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "payment_insight_agent_failed",
                error=str(exc),
                transaction_id=str(transaction.id),
            )
            return None

        if response.status != ResponseStatus.SUCCESS:
            logger.info(
                "payment_insight_agent_non_success",
                status=response.status.value,
                error=response.error,
            )
            return None

        payload: dict[str, Any] | None = response.metadata.get("parsed_model")
        if not payload:
            logger.info(
                "payment_insight_missing_payload",
                transaction_id=str(transaction.id),
            )
            return None

        insight = PaymentInsight.from_payload(payload)
        logger.debug(
            "payment_insight_generated",
            transaction_id=str(transaction.id),
            confidence=insight.confidence,
            probable_invoice_numbers=insight.probable_invoice_numbers,
        )
        return insight

    def _serialize_payment(self, payment: Pagamento) -> dict[str, Any]:
        """Serialize payment details for AI context consumption."""

        invoice_number = None
        if hasattr(payment, "fattura") and payment.fattura is not None:
            invoice_number = getattr(payment.fattura, "numero", None)

        return {
            "payment_id": getattr(payment, "id", None),
            "due_date": payment.data_scadenza.isoformat() if payment.data_scadenza else None,
            "total_amount": float(payment.importo),
            "outstanding_amount": float(getattr(payment, "saldo_residuo", payment.importo)),
            "status": (
                payment.stato.value if hasattr(payment.stato, "value") else str(payment.stato)
            ),
            "invoice_number": invoice_number,
        }
