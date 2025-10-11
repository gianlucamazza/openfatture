"""Tests for LangGraph-based invoice workflows."""

from __future__ import annotations

import json
import sys
import types
from collections.abc import AsyncIterator
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy.orm import sessionmaker

# Stub cash flow workflow to avoid heavy ML config during imports
_cash_flow_stub: Any = types.ModuleType("openfatture.ai.orchestration.workflows.cash_flow_analysis")
_cash_flow_stub.CashFlowAnalysisWorkflow = object
_cash_flow_stub.create_cash_flow_workflow = lambda *args, **kwargs: None
sys.modules.setdefault(
    "openfatture.ai.orchestration.workflows.cash_flow_analysis",
    _cash_flow_stub,
)

if TYPE_CHECKING:
    pass

from openfatture.ai.domain.response import AgentResponse, UsageMetrics
from openfatture.ai.orchestration.workflows.compliance_check import ComplianceCheckWorkflow
from openfatture.ai.orchestration.workflows.invoice_creation import InvoiceCreationWorkflow
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.storage.database import base
from openfatture.storage.database.models import Fattura, StatoFattura
from openfatture.utils import config


class FakeLLMProvider(BaseLLMProvider):
    """Deterministic provider for testing AI workflows."""

    def __init__(self, responses: list[str]) -> None:
        super().__init__(api_key=None, model="fake", temperature=0.0, max_tokens=500)
        self._responses = responses
        self._index = 0

    async def generate(
        self, messages, system_prompt=None, temperature=None, max_tokens=None, **kwargs
    ):
        if self._index < len(self._responses):
            content = self._responses[self._index]
        else:
            content = self._responses[-1]
        self._index += 1

        return AgentResponse(
            content=content,
            provider=self.provider_name,
            model=self.model,
            usage=UsageMetrics(),
            confidence=0.98,
        )

    def stream(
        self, messages, system_prompt=None, temperature=None, max_tokens=None, **kwargs
    ) -> AsyncIterator[str]:
        async def iterator() -> AsyncIterator[str]:
            if self._responses:
                yield self._responses[-1]

        return iterator()

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def estimate_cost(self, usage: UsageMetrics) -> float:
        return 0.0

    async def health_check(self) -> bool:
        return True

    @property
    def provider_name(self) -> str:
        return "fake"

    @property
    def supports_streaming(self) -> bool:
        return False

    @property
    def supports_tools(self) -> bool:
        return False


@pytest.mark.asyncio
async def test_invoice_creation_workflow_creates_invoice(
    db_engine,
    db_session,
    test_settings,
    sample_cliente,
):
    """Full execution of the invoice creation workflow populates DB and generates XML."""

    # Ensure global settings/session factories point to the in-memory test engine
    base.SessionLocal = sessionmaker(bind=db_engine)
    base.engine = db_engine
    config._settings = test_settings

    from openfatture.ai.orchestration.workflows import invoice_creation as invoice_module

    invoice_module.SessionLocal = base.SessionLocal

    invoice_response = json.dumps(
        {
            "descrizione_completa": "Sviluppo backend modulare con integrazione API REST e test end-to-end.",
            "deliverables": ["Codice sorgente", "Pipeline CI", "Documentazione"],
            "competenze": ["Python", "FastAPI", "PostgreSQL"],
            "durata_ore": 12,
            "note": "Attività completata in sprint dedicato",
        }
    )

    tax_response = json.dumps(
        {
            "aliquota_iva": 22.0,
            "codice_natura": None,
            "reverse_charge": False,
            "split_payment": False,
            "regime_speciale": None,
            "spiegazione": "Prestazione di servizi professionali soggetta ad IVA ordinaria.",
            "riferimento_normativo": "Art. 3 DPR 633/72",
            "note_fattura": "Operazione imponibile ai sensi dell'art. 3 DPR 633/72",
            "confidence": 0.95,
            "raccomandazioni": ["Indicare nelle note l'avvenuta consegna del codice."],
        }
    )

    provider = FakeLLMProvider([invoice_response, tax_response])

    workflow = InvoiceCreationWorkflow(
        confidence_threshold=0.8,
        enable_checkpointing=False,
        settings=test_settings,
        provider=provider,
        validate_xml=False,
    )

    result = await workflow.execute(
        user_input="Sviluppo backend per portale clienti",
        client_id=sample_cliente.id,
        imponibile=1500.0,
        vat_rate=22.0,
        hours=12,
        hourly_rate=125.0,
        payment_terms_days=30,
    )

    assert result.status == "completed"
    assert result.invoice_id is not None
    assert result.compliance_result is not None
    assert result.compliance_result.success
    assert result.invoice_xml_path
    assert len(result.line_items) == 1

    session = base.SessionLocal()
    try:
        fattura = session.query(Fattura).filter(Fattura.id == result.invoice_id).first()
        assert fattura is not None
        assert fattura.stato == StatoFattura.DA_INVIARE
        assert fattura.totale == Decimal("1830.00")
        assert fattura.righe[0].descrizione.startswith("Sviluppo backend")
    finally:
        session.close()


@pytest.mark.asyncio
async def test_compliance_workflow_produces_report(
    db_engine,
    db_session,
    test_settings,
    sample_fattura,
):
    """Compliance workflow returns structured report data."""

    base.SessionLocal = sessionmaker(bind=db_engine)
    base.engine = db_engine
    config._settings = test_settings

    from openfatture.ai.orchestration.workflows import compliance_check as compliance_module

    compliance_module.SessionLocal = base.SessionLocal

    workflow = ComplianceCheckWorkflow(level="standard", enable_checkpointing=False)

    result = await workflow.execute(invoice_id=sample_fattura.id)

    assert result.compliance_score >= 0.0
    assert isinstance(result.metadata.get("compliance_report"), dict)
    assert result.metadata["compliance_report"]["invoice_id"] == sample_fattura.id
    assert isinstance(result.sdi_patterns_checked, bool)
