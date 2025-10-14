import json
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from openfatture.ai.domain.response import AgentResponse, ResponseStatus
from openfatture.payment.application.services.insight_service import TransactionInsightService
from openfatture.payment.domain.enums import ImportSource
from openfatture.payment.domain.models import BankTransaction
from openfatture.payment.domain.value_objects import PaymentInsight
from openfatture.storage.database.models import Pagamento, StatoPagamento


class StubInsightAgent:
    def __init__(self, payload: dict, status: ResponseStatus = ResponseStatus.SUCCESS):
        self.payload = payload
        self.status = status

    async def execute(self, context):
        return AgentResponse(
            content=json.dumps(self.payload) if self.payload else "",
            status=self.status,
            metadata={"parsed_model": self.payload} if self.payload else {},
            error="Test error" if self.status != ResponseStatus.SUCCESS else None,
        )


class FailingInsightAgent:
    async def execute(self, context):
        raise Exception("Agent failed")


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

    service = TransactionInsightService(agent=StubInsightAgent(payload))  # type: ignore
    insight = await service.analyze(transaction, [payment])

    assert isinstance(insight, PaymentInsight)
    assert insight.is_partial_payment is True
    assert insight.probable_invoice_numbers == ["INV-2024-001"]
    assert insight.suggested_allocation_amount == 400.0


@pytest.mark.asyncio
async def test_transaction_insight_service_handles_agent_failure():
    """Test that agent failures are handled gracefully."""
    transaction = BankTransaction(
        account_id=1,
        date=date(2024, 10, 10),
        amount=Decimal("400.00"),
        description="Test transaction",
        import_source=ImportSource.MANUAL,
    )

    service = TransactionInsightService(agent=FailingInsightAgent())  # type: ignore
    insight = await service.analyze(transaction, [])

    assert insight is None


@pytest.mark.asyncio
async def test_transaction_insight_service_handles_non_success_status():
    """Test handling of non-success agent responses."""
    transaction = BankTransaction(
        account_id=1,
        date=date(2024, 10, 10),
        amount=Decimal("400.00"),
        description="Test transaction",
        import_source=ImportSource.MANUAL,
    )

    service = TransactionInsightService(agent=StubInsightAgent({}, ResponseStatus.ERROR))  # type: ignore
    insight = await service.analyze(transaction, [])

    assert insight is None


@pytest.mark.asyncio
async def test_transaction_insight_service_handles_missing_payload():
    """Test handling of responses without parsed_model metadata."""
    transaction = BankTransaction(
        account_id=1,
        date=date(2024, 10, 10),
        amount=Decimal("400.00"),
        description="Test transaction",
        import_source=ImportSource.MANUAL,
    )

    service = TransactionInsightService(agent=StubInsightAgent(None))  # type: ignore
    insight = await service.analyze(transaction, [])

    assert insight is None


def test_serialize_payment():
    """Test the _serialize_payment method."""
    service = TransactionInsightService(agent=None)  # type: ignore

    payment = Pagamento(
        fattura_id=1,
        importo=Decimal("1000.00"),
        importo_pagato=Decimal("0.00"),
        data_scadenza=date(2024, 10, 31),
        stato=StatoPagamento.DA_PAGARE,
    )
    payment.id = 10
    # Don't set fattura to avoid SQLAlchemy relationship issues

    result = service._serialize_payment(payment)

    expected = {
        "payment_id": 10,
        "due_date": "2024-10-31",
        "total_amount": 1000.0,
        "outstanding_amount": 1000.0,  # saldo_residuo = importo - importo_pagato = 1000 - 0
        "status": "da_pagare",
        "invoice_number": None,  # No fattura set
    }
    assert result == expected
