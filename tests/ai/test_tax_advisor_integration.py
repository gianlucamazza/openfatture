"""Integration tests for Tax Advisor agent.

These tests verify the agent works with mocked provider responses
that simulate real LLM API behavior for various fiscal scenarios.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from openfatture.ai.agents.tax_advisor import TaxAdvisorAgent
from openfatture.ai.domain.context import TaxContext
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.providers.base import BaseLLMProvider


@pytest.fixture
def mock_provider_with_response():
    """Create a mock provider that returns JSON responses."""

    def create_mock(response_data):
        provider = MagicMock(spec=BaseLLMProvider)
        provider.provider_name = "mock"
        provider.model = "mock-model"

        async def mock_generate(messages, **kwargs):
            return AgentResponse(
                content=json.dumps(response_data),
                status=ResponseStatus.SUCCESS,
                model="mock-model",
                provider="mock",
                usage=UsageMetrics(
                    prompt_tokens=150,
                    completion_tokens=200,
                    total_tokens=350,
                    estimated_cost_usd=0.008
                ),
                latency_ms=450.0
            )

        provider.generate = AsyncMock(side_effect=mock_generate)
        return provider

    return create_mock


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.ai
class TestTaxAdvisorIntegration:
    """Integration tests for Tax Advisor."""

    async def test_standard_vat_rate(self, mock_provider_with_response):
        """Test standard VAT rate suggestion (22%)."""
        mock_response = {
            "aliquota_iva": 22.0,
            "codice_natura": None,
            "reverse_charge": False,
            "split_payment": False,
            "regime_speciale": None,
            "spiegazione": "Le prestazioni di consulenza IT rientrano nel regime ordinario IVA con aliquota standard del 22%.",
            "riferimento_normativo": "Art. 1, DPR 633/72",
            "note_fattura": None,
            "confidence": 1.0,
            "raccomandazioni": []
        }

        provider = mock_provider_with_response(mock_response)
        agent = TaxAdvisorAgent(provider=provider)

        context = TaxContext(
            user_input="consulenza IT",
            tipo_servizio="consulenza IT"
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        assert response.metadata["is_structured"] is True

        model = response.metadata["parsed_model"]
        assert model["aliquota_iva"] == 22.0
        assert model["reverse_charge"] is False

    async def test_reverse_charge_edilizia(self, mock_provider_with_response):
        """Test reverse charge for construction sector."""
        mock_response = {
            "aliquota_iva": 22.0,
            "codice_natura": "N6.7",
            "reverse_charge": True,
            "split_payment": False,
            "regime_speciale": "REVERSE_CHARGE_EDILIZIA",
            "spiegazione": "Per servizi resi al settore edile si applica il reverse charge.",
            "riferimento_normativo": "Art. 17, c. 6, lett. a-ter, DPR 633/72",
            "note_fattura": "Inversione contabile - art. 17 c. 6 lett. a-ter DPR 633/72",
            "confidence": 0.95,
            "raccomandazioni": [
                "Verificare che il cliente operi nel settore edile",
                "Non addebitare IVA in fattura"
            ]
        }

        provider = mock_provider_with_response(mock_response)
        agent = TaxAdvisorAgent(provider=provider)

        context = TaxContext(
            user_input="consulenza IT per azienda edile",
            tipo_servizio="consulenza IT per azienda edile"
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        model = response.metadata["parsed_model"]
        assert model["reverse_charge"] is True
        assert model["codice_natura"] == "N6.7"
        assert "edile" in model["spiegazione"].lower()

    async def test_split_payment_pa(self, mock_provider_with_response):
        """Test split payment for Public Administration."""
        mock_response = {
            "aliquota_iva": 22.0,
            "codice_natura": None,
            "reverse_charge": False,
            "split_payment": True,
            "regime_speciale": "SPLIT_PAYMENT",
            "spiegazione": "Per servizi resi alla PA si applica lo split payment.",
            "riferimento_normativo": "Art. 17-ter, DPR 633/72",
            "note_fattura": "Scissione dei pagamenti - art. 17-ter DPR 633/72",
            "confidence": 1.0,
            "raccomandazioni": [
                "Indicare IVA in fattura normalmente",
                "La PA verserà IVA all'Erario"
            ]
        }

        provider = mock_provider_with_response(mock_response)
        agent = TaxAdvisorAgent(provider=provider)

        context = TaxContext(
            user_input="consulenza IT per Comune",
            tipo_servizio="consulenza IT",
            cliente_pa=True
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        model = response.metadata["parsed_model"]
        assert model["split_payment"] is True
        assert model["aliquota_iva"] == 22.0

    async def test_exempt_services(self, mock_provider_with_response):
        """Test exempt services (formazione, sanità)."""
        mock_response = {
            "aliquota_iva": 0.0,
            "codice_natura": "N4",
            "reverse_charge": False,
            "split_payment": False,
            "regime_speciale": "ESENTE",
            "spiegazione": "Le prestazioni di formazione professionale sono esenti da IVA.",
            "riferimento_normativo": "Art. 10, comma 1, n. 20, DPR 633/72",
            "note_fattura": "Operazione esente IVA ai sensi dell'art. 10, c. 1, n. 20, DPR 633/72",
            "confidence": 0.90,
            "raccomandazioni": [
                "Verificare finalità educative riconosciute"
            ]
        }

        provider = mock_provider_with_response(mock_response)
        agent = TaxAdvisorAgent(provider=provider)

        context = TaxContext(
            user_input="formazione professionale",
            tipo_servizio="formazione professionale"
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        model = response.metadata["parsed_model"]
        assert model["aliquota_iva"] == 0.0
        assert model["codice_natura"] == "N4"

    async def test_reduced_vat_rate(self, mock_provider_with_response):
        """Test reduced VAT rate (10%, 4%)."""
        mock_response = {
            "aliquota_iva": 4.0,
            "codice_natura": None,
            "reverse_charge": False,
            "split_payment": False,
            "regime_speciale": None,
            "spiegazione": "I libri beneficiano dell'aliquota IVA ridotta al 4%.",
            "riferimento_normativo": "Tabella A, parte II, n. 18, DPR 633/72",
            "note_fattura": None,
            "confidence": 1.0,
            "raccomandazioni": []
        }

        provider = mock_provider_with_response(mock_response)
        agent = TaxAdvisorAgent(provider=provider)

        context = TaxContext(
            user_input="libri scolastici",
            tipo_servizio="libri scolastici"
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        model = response.metadata["parsed_model"]
        assert model["aliquota_iva"] == 4.0

    async def test_regime_forfettario(self, mock_provider_with_response):
        """Test regime forfettario (no VAT)."""
        mock_response = {
            "aliquota_iva": 0.0,
            "codice_natura": "N2.2",
            "reverse_charge": False,
            "split_payment": False,
            "regime_speciale": "FORFETTARIO",
            "spiegazione": "I soggetti in regime forfettario non addebitano IVA.",
            "riferimento_normativo": "Art. 1, commi 54-89, Legge 190/2014",
            "note_fattura": "Operazione senza applicazione dell'IVA ai sensi dell'art. 1, comma 58, L. 190/2014",
            "confidence": 1.0,
            "raccomandazioni": [
                "Verificare requisiti regime forfettario"
            ]
        }

        provider = mock_provider_with_response(mock_response)
        agent = TaxAdvisorAgent(provider=provider)

        context = TaxContext(
            user_input="consulenza regime forfettario",
            tipo_servizio="consulenza commerciale",
            regime_speciale="FORFETTARIO"
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        model = response.metadata["parsed_model"]
        assert model["aliquota_iva"] == 0.0
        assert model["codice_natura"] == "N2.2"

    async def test_export_extra_ue(self, mock_provider_with_response):
        """Test export to non-EU countries."""
        mock_response = {
            "aliquota_iva": 0.0,
            "codice_natura": "N3.1",
            "reverse_charge": False,
            "split_payment": False,
            "regime_speciale": "EXPORT",
            "spiegazione": "Prestazioni verso clienti extra-UE non imponibili in Italia.",
            "riferimento_normativo": "Art. 7-ter, DPR 633/72",
            "note_fattura": "Operazione non imponibile IVA - art. 7-ter DPR 633/72",
            "confidence": 0.85,
            "raccomandazioni": [
                "Verificare residenza fiscale committente",
                "Conservare documentazione"
            ]
        }

        provider = mock_provider_with_response(mock_response)
        agent = TaxAdvisorAgent(provider=provider)

        context = TaxContext(
            user_input="consulenza IT",
            tipo_servizio="consulenza IT",
            cliente_estero=True,
            paese_cliente="US"
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        model = response.metadata["parsed_model"]
        assert model["aliquota_iva"] == 0.0
        assert model["codice_natura"] == "N3.1"

    async def test_validation_prevents_execution(self, mock_provider_with_response):
        """Test validation prevents execution with invalid input."""
        provider = mock_provider_with_response({})
        agent = TaxAdvisorAgent(provider=provider)

        # Invalid context (empty tipo_servizio)
        context = TaxContext(
            user_input="",
            tipo_servizio=""
        )

        response = await agent.execute(context)

        # Should fail validation before calling LLM
        assert response.status == ResponseStatus.ERROR
        assert "tipo_servizio è richiesto" in response.error

    async def test_provider_error_handling(self):
        """Test handling of provider errors."""
        # Create a provider that raises an error
        provider = MagicMock(spec=BaseLLMProvider)
        provider.provider_name = "error_provider"
        provider.model = "error-model"
        provider.generate = AsyncMock(side_effect=Exception("API Error: Rate limit"))

        agent = TaxAdvisorAgent(provider=provider)

        context = TaxContext(
            user_input="test",
            tipo_servizio="test service"
        )

        response = await agent.execute(context)

        # Should handle error gracefully
        assert response.status == ResponseStatus.ERROR
        assert response.error is not None

    async def test_metrics_tracking(self, mock_provider_with_response):
        """Test metrics are tracked correctly."""
        mock_response = {
            "aliquota_iva": 22.0,
            "spiegazione": "Standard rate",
            "riferimento_normativo": "Art. 1, DPR 633/72",
            "confidence": 0.95,
            "raccomandazioni": []
        }

        provider = mock_provider_with_response(mock_response)
        agent = TaxAdvisorAgent(provider=provider)

        # Execute 3 times
        for i in range(3):
            context = TaxContext(
                user_input=f"test {i}",
                tipo_servizio=f"test service {i}"
            )
            await agent.execute(context)

        # Check metrics
        metrics = agent.get_metrics()
        assert metrics["total_requests"] == 3
        assert metrics["total_tokens"] == 1050  # 350 * 3
        assert metrics["avg_tokens_per_request"] == 350

    async def test_cleanup_resources(self, mock_provider_with_response):
        """Test agent cleanup works correctly."""
        mock_response = {
            "aliquota_iva": 22.0,
            "spiegazione": "Test",
            "riferimento_normativo": "Test",
            "confidence": 1.0,
            "raccomandazioni": []
        }

        provider = mock_provider_with_response(mock_response)
        agent = TaxAdvisorAgent(provider=provider)

        context = TaxContext(
            user_input="test",
            tipo_servizio="test"
        )

        await agent.execute(context)

        # Cleanup should log metrics
        await agent.cleanup()

        # Agent should still have metrics
        assert agent.total_requests > 0
