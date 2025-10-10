import json
from datetime import date
from decimal import Decimal

import pytest

from openfatture.ai.domain.response import AgentResponse, ResponseStatus
from openfatture.payment.application.services.insight_service import TransactionInsightService
from openfatture.payment.domain.enums import ImportSource
from openfatture.payment.domain.models import BankTransaction
from openfatture.payment.domain.value_objects import PaymentInsight
from openfatture.storage.database.models import Pagamento, StatoPagamento


class StubInsightAgent:
    def __init__(self, payload: dict):
        self.payload = payload

    async def execute(self, context):
        return AgentResponse(
            content=json.dumps(self.payload),
            status=ResponseStatus.SUCCESS,
            metadata={"parsed_model": self.payload},
        )


@pytest.mark.asyncio
async def test_transaction_insight_service_returns_payment_insight():
    transaction = BankTransaction(
        account_id=1,
        date=date(2024, 10, 10),
        amount=Decimal("400.00"),
        description="Acconto fattura INV-2024-001",
        import_source=ImportSource.MANUAL,
    )
    transaction.reference = "INV-2024-001"

    payment = Pagamento(
        fattura_id=1,
        importo=Decimal("1000.00"),
        importo_pagato=Decimal("0.00"),
        data_scadenza=date(2024, 10, 31),
        stato=StatoPagamento.DA_PAGARE,
    )
    payment.id = 10

    payload = {
        "probable_invoice_numbers": ["INV-2024-001"],
        "is_partial_payment": True,
        "suggested_allocation_amount": 400.0,
        "keywords": ["acconto"],
        "confidence": 0.82,
        "summary": "Pagamento parziale del 40% per INV-2024-001",
    }

    service = TransactionInsightService(agent=StubInsightAgent(payload))
    insight = await service.analyze(transaction, [payment])

    assert isinstance(insight, PaymentInsight)
    assert insight.is_partial_payment is True
    assert insight.probable_invoice_numbers == ["INV-2024-001"]
    assert float(insight.suggested_allocation_amount) == pytest.approx(400.0)
