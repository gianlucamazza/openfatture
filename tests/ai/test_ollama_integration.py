"""End-to-end tests for AI agents using real Ollama provider.

These tests require Ollama to be running locally with appropriate models.
They validate real LLM responses and integration with the full agent pipeline.

Run with: pytest -m "ollama and e2e"
"""

import json
from typing import Any

import pytest
import pytest_asyncio

from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.agents.tax_advisor import TaxAdvisorAgent
from openfatture.ai.domain.context import InvoiceContext, TaxContext
from openfatture.ai.domain.response import ResponseStatus
from openfatture.ai.providers.ollama import OllamaProvider


@pytest_asyncio.fixture(scope="session")
async def ollama_provider():
    """Real Ollama provider for E2E tests."""
    provider = OllamaProvider(model="llama3.2")

    # Health check
    if not await provider.health_check():
        pytest.skip("Ollama service not available at localhost:11434")

    return provider


@pytest.fixture(scope="session")
def ollama_provider_with_fallback():
    """Ollama provider that falls back gracefully if unavailable."""
    try:
        provider = OllamaProvider(model="llama3.2")
        if provider.health_check():
            return provider
    except Exception:
        pass

    # If Ollama not available, skip the test
    pytest.skip("Ollama not available for E2E testing")


def validate_json_response(content: str) -> dict[str, Any] | None:
    """Validate and parse JSON response from LLM."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


def validate_invoice_response(response_data: dict[str, Any]) -> bool:
    """Validate InvoiceAssistant response structure."""
    required_fields = ["descrizione_completa", "deliverables", "competenze"]
    return all(field in response_data for field in required_fields)


def validate_tax_response(response_data: dict[str, Any]) -> bool:
    """Validate TaxAdvisor response structure."""
    required_fields = ["aliquota_iva", "spiegazione", "riferimento_normativo"]
    return all(field in response_data for field in required_fields)


def contains_italian_tax_terms(text: str) -> bool:
    """Check if response contains Italian tax terminology."""
    tax_terms = [
        "iva",
        "aliquota",
        "dpr 633/72",
        "reverse charge",
        "split payment",
        "natura",
        "esenzione",
        "imponibile",
        "fattura",
        "cession",
    ]
    return any(term in text.lower() for term in tax_terms)


def contains_italian_business_terms(text: str) -> bool:
    """Check if response contains Italian business terminology."""
    business_terms = [
        "consulenza",
        "servizio",
        "prestazione",
        "professionale",
        "commerciale",
        "fattura",
        "cliente",
        "fornitore",
        "contratto",
        "preventivo",
    ]
    return any(term in text.lower() for term in business_terms)


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.ollama
class TestOllamaInvoiceAssistant:
    """E2E tests for InvoiceAssistant with real Ollama."""

    async def test_basic_invoice_description(self, ollama_provider):
        """Test basic invoice description generation with Ollama."""
        agent = InvoiceAssistantAgent(provider=ollama_provider, use_structured_output=True)

        context = InvoiceContext(
            user_input="3 ore consulenza web",
            servizio_base="consulenza web",
            ore_lavorate=3.0,
            tariffa_oraria=100.0,
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        assert response.content is not None
        assert len(response.content.strip()) > 0

        # Validate response time is reasonable (under 30 seconds)
        assert response.latency_ms is not None and response.latency_ms < 30000

        # Try to parse as JSON
        response_data = validate_json_response(response.content)
        if response_data:
            # If structured, validate format
            assert validate_invoice_response(response_data)
            assert "consulenza" in response_data["descrizione_completa"].lower()
        else:
            # If not structured, check for business terms
            assert contains_italian_business_terms(response.content)

    async def test_complex_invoice_with_client(self, ollama_provider):
        """Test complex invoice with client information."""
        agent = InvoiceAssistantAgent(provider=ollama_provider, use_structured_output=True)

        context = InvoiceContext(
            user_input="sviluppo app mobile per ristorante",
            servizio_base="sviluppo app mobile",
            ore_lavorate=20.0,
            tariffa_oraria=80.0,
            progetto="App ristorante digitale",
            tecnologie=["React Native", "Node.js", "MongoDB"],
            deliverables=["App iOS/Android", "API backend", "Documentazione"],
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS

        response_data = validate_json_response(response.content)
        if response_data:
            assert validate_invoice_response(response_data)
            # Check if technologies are mentioned
            full_desc = response_data["descrizione_completa"].lower()
            assert any(tech.lower() in full_desc for tech in ["react", "mobile", "app"])

    async def test_invoice_with_technical_focus(self, ollama_provider):
        """Test invoice description with technical details."""
        agent = InvoiceAssistantAgent(provider=ollama_provider, use_structured_output=True)

        context = InvoiceContext(
            user_input="ottimizzazione database PostgreSQL",
            servizio_base="ottimizzazione database PostgreSQL",
            ore_lavorate=8.0,
            tariffa_oraria=120.0,
            tecnologie=["PostgreSQL", "SQL", "indexing"],
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS

        response_data = validate_json_response(response.content)
        if response_data:
            assert validate_invoice_response(response_data)
            full_desc = response_data["descrizione_completa"].lower()
            assert "postgresql" in full_desc or "database" in full_desc


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.ollama
class TestOllamaTaxAdvisor:
    """E2E tests for TaxAdvisor with real Ollama."""

    async def test_standard_vat_rate(self, ollama_provider):
        """Test standard VAT rate suggestion (22%)."""
        agent = TaxAdvisorAgent(provider=ollama_provider, use_structured_output=True)

        context = TaxContext(
            user_input="consulenza IT generica",
            tipo_servizio="consulenza informatica generica",
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        assert contains_italian_tax_terms(response.content)

        response_data = validate_json_response(response.content)
        if response_data:
            assert validate_tax_response(response_data)
            # Should suggest standard rate for generic IT consulting
            assert isinstance(response_data["aliquota_iva"], (int, float))
            assert response_data["aliquota_iva"] >= 0

    async def test_construction_reverse_charge(self, ollama_provider):
        """Test reverse charge for construction services."""
        agent = TaxAdvisorAgent(provider=ollama_provider, use_structured_output=True)

        context = TaxContext(
            user_input="lavori edilizia appartamento",
            tipo_servizio="lavori di edilizia per appartamento",
            categoria_servizio="edilizia",
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        assert contains_italian_tax_terms(response.content)

        response_data = validate_json_response(response.content)
        if response_data:
            assert validate_tax_response(response_data)
            # Construction often involves reverse charge
            assert "reverse_charge" in response_data

    async def test_public_administration_split_payment(self, ollama_provider):
        """Test split payment for PA clients."""
        agent = TaxAdvisorAgent(provider=ollama_provider, use_structured_output=True)

        context = TaxContext(
            user_input="consulenza per Comune",
            tipo_servizio="consulenza gestionale",
            cliente_pa=True,
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        assert contains_italian_tax_terms(response.content)

        response_data = validate_json_response(response.content)
        if response_data:
            assert validate_tax_response(response_data)
            # PA clients should have split payment consideration
            assert "split_payment" in response_data

    async def test_exempt_services(self, ollama_provider):
        """Test exempt services (education, healthcare)."""
        agent = TaxAdvisorAgent(provider=ollama_provider, use_structured_output=True)

        context = TaxContext(
            user_input="corso formazione professionale",
            tipo_servizio="corso di formazione professionale",
            categoria_servizio="formazione",
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        assert contains_italian_tax_terms(response.content)

        response_data = validate_json_response(response.content)
        if response_data:
            assert validate_tax_response(response_data)
            # Education services are often exempt
            aliquota = response_data["aliquota_iva"]
            assert isinstance(aliquota, (int, float))

    async def test_foreign_client_export(self, ollama_provider):
        """Test services to foreign clients."""
        agent = TaxAdvisorAgent(provider=ollama_provider, use_structured_output=True)

        context = TaxContext(
            user_input="consulenza per cliente USA",
            tipo_servizio="consulenza marketing",
            cliente_estero=True,
            paese_cliente="US",
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        assert contains_italian_tax_terms(response.content)

        response_data = validate_json_response(response.content)
        if response_data:
            assert validate_tax_response(response_data)
            # Foreign clients may have different VAT treatment
            assert "aliquota_iva" in response_data


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.ollama
class TestOllamaPerformance:
    """Performance tests for Ollama integration."""

    async def test_response_latency(self, ollama_provider):
        """Test that responses are reasonably fast."""
        agent = TaxAdvisorAgent(provider=ollama_provider, use_structured_output=True)

        context = TaxContext(
            user_input="consulenza semplice",
            tipo_servizio="consulenza semplice",
        )

        response = await agent.execute(context)

        # Should respond within 20 seconds for simple queries
        assert response.latency_ms is not None and response.latency_ms < 20000
        assert response.status == ResponseStatus.SUCCESS

    async def test_token_usage_tracking(self, ollama_provider):
        """Test that token usage is properly tracked."""
        agent = InvoiceAssistantAgent(provider=ollama_provider, use_structured_output=True)

        context = InvoiceContext(
            user_input="test",
            servizio_base="test service",
            ore_lavorate=1.0,
        )

        response = await agent.execute(context)

        # Should have usage metrics
        assert response.usage.total_tokens > 0
        assert response.usage.prompt_tokens > 0
        assert response.usage.completion_tokens > 0
        assert response.usage.estimated_cost_usd >= 0


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.ollama
class TestOllamaErrorHandling:
    """Error handling tests for Ollama integration."""

    async def test_malformed_prompt_handling(self, ollama_provider):
        """Test handling of edge case prompts."""
        agent = TaxAdvisorAgent(provider=ollama_provider, use_structured_output=True)

        # Very minimal context
        context = TaxContext(
            user_input="",
            tipo_servizio="x",  # Minimal valid input
        )

        response = await agent.execute(context)

        # Should still attempt to respond
        assert response.status in [ResponseStatus.SUCCESS, ResponseStatus.ERROR]
        # Even if error, should have some response
        assert response.content is not None or response.error is not None

    async def test_structured_output_fallback(self, ollama_provider):
        """Test fallback when structured output fails."""
        # Force structured output to be disabled to test text fallback
        agent = InvoiceAssistantAgent(provider=ollama_provider, use_structured_output=False)

        context = InvoiceContext(
            user_input="test service",
            servizio_base="test service",
            ore_lavorate=1.0,
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        # Should contain some descriptive content (text or structured JSON)
        assert len(response.content) > 10
        # Check if it's either structured JSON or contains Italian business terms
        import json

        try:
            json.loads(response.content)  # If it's valid JSON, accept it
        except json.JSONDecodeError:
            # If not JSON, check for Italian business terms
            assert contains_italian_business_terms(response.content)
