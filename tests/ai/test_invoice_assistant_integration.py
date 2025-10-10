"""Integration tests for Invoice Assistant agent.

These tests verify the agent works with mocked provider responses
that simulate real LLM API behavior.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.config import AISettings
from openfatture.ai.domain.context import InvoiceContext
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.storage.database.models import Cliente


@pytest.fixture
def ai_settings():
    """Create AI settings for testing."""
    return AISettings(
        provider="openai",
        openai_api_key="sk-test-key",
        openai_model="gpt-5",
        temperature=0.7,
        max_tokens=800,
    )


@pytest.fixture
def sample_cliente_ai():
    """Create a sample client for AI context."""
    return Cliente(
        id=1,
        denominazione="Acme Corporation",
        partita_iva="12345678901",
        codice_destinatario="ABC1234",
    )


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
                    completion_tokens=250,
                    total_tokens=400,
                    estimated_cost_usd=0.01,
                ),
                latency_ms=500.0,
            )

        provider.generate = AsyncMock(side_effect=mock_generate)
        return provider

    return create_mock


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.ai
class TestInvoiceAssistantIntegration:
    """Integration tests for Invoice Assistant."""

    async def test_end_to_end_with_mock_provider(self, mock_provider_with_response):
        """Test end-to-end flow with mocked provider response."""
        mock_response = {
            "descrizione_completa": (
                "Consulenza professionale per sviluppo web e architettura software\n\n"
                "Attività svolte:\n"
                "- Analisi dei requisiti funzionali e non funzionali del progetto\n"
                "- Progettazione dell'architettura applicativa\n"
                "- Sviluppo di componenti front-end con framework moderni\n"
                "- Implementazione API REST con autenticazione sicura\n\n"
                "Durata: 3 ore"
            ),
            "deliverables": [
                "Documentazione architetturale",
                "Codice sorgente",
                "Specifiche tecniche",
            ],
            "competenze": ["Architettura software", "Sviluppo web", "API REST"],
            "durata_ore": 3.0,
            "note": "Consulenza tecnica per definizione architettura",
        }

        # Create provider and agent
        provider = mock_provider_with_response(mock_response)
        agent = InvoiceAssistantAgent(provider=provider)

        # Create context
        context = InvoiceContext(
            user_input="3 ore consulenza web",
            servizio_base="3 ore consulenza web",
            ore_lavorate=3.0,
        )

        # Execute
        response = await agent.execute(context)

        # Verify
        assert response.status == ResponseStatus.SUCCESS
        assert "parsed_model" in response.metadata
        assert response.metadata["is_structured"] is True

        model = response.metadata["parsed_model"]
        assert "consulenza professionale" in model["descrizione_completa"].lower()
        assert len(model["deliverables"]) > 0
        assert len(model["competenze"]) > 0

    async def test_with_complex_context(self, mock_provider_with_response, sample_cliente_ai):
        """Test with complex context including client and project."""
        mock_response = {
            "descrizione_completa": (
                "Sviluppo backend e implementazione servizi API RESTful "
                "per il progetto Sistema E-commerce\n\n"
                "Attività svolte:\n"
                "- Design e implementazione endpoints API\n"
                "- Integrazione con database PostgreSQL\n"
                "- Sistema di autenticazione JWT\n\n"
                "Durata: 8 ore"
            ),
            "deliverables": ["Codice backend", "API REST", "Documentazione OpenAPI"],
            "competenze": ["Python", "FastAPI", "PostgreSQL", "JWT"],
            "durata_ore": 8.0,
            "note": "Implementazione completa backend",
        }

        provider = mock_provider_with_response(mock_response)
        agent = InvoiceAssistantAgent(provider=provider)

        context = InvoiceContext(
            user_input="sviluppo backend API",
            servizio_base="sviluppo backend API",
            ore_lavorate=8.0,
            tariffa_oraria=100.0,
            progetto="Sistema E-commerce",
            tecnologie=["Python", "FastAPI", "PostgreSQL"],
            cliente=sample_cliente_ai,
            deliverables=["API REST", "Documentazione"],
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        model = response.metadata["parsed_model"]
        assert "backend" in model["descrizione_completa"].lower()
        assert "PostgreSQL" in model["competenze"]

    async def test_validation_prevents_execution(self, mock_provider_with_response):
        """Test validation prevents execution with invalid input."""
        provider = mock_provider_with_response({})
        agent = InvoiceAssistantAgent(provider=provider)

        # Invalid context (empty servizio_base)
        context = InvoiceContext(user_input="", servizio_base="", ore_lavorate=5.0)

        response = await agent.execute(context)

        # Should fail validation before calling LLM
        assert response.status == ResponseStatus.ERROR
        assert "servizio_base è richiesto" in response.error

    async def test_provider_error_handling(self):
        """Test handling of provider errors."""
        # Create a provider that raises an error
        provider = MagicMock(spec=BaseLLMProvider)
        provider.provider_name = "error_provider"
        provider.model = "error-model"
        provider.generate = AsyncMock(side_effect=Exception("API Error: Rate limit exceeded"))

        agent = InvoiceAssistantAgent(provider=provider)

        context = InvoiceContext(user_input="test", servizio_base="test service", ore_lavorate=1.0)

        response = await agent.execute(context)

        # Should handle error gracefully
        assert response.status == ResponseStatus.ERROR
        assert response.error is not None

    async def test_metrics_tracking(self, mock_provider_with_response):
        """Test metrics are tracked correctly."""
        mock_response = {
            "descrizione_completa": "Test description",
            "deliverables": ["Test"],
            "competenze": ["Testing"],
            "durata_ore": 1.0,
        }

        provider = mock_provider_with_response(mock_response)
        agent = InvoiceAssistantAgent(provider=provider)

        # Execute 3 times
        for i in range(3):
            context = InvoiceContext(
                user_input=f"test {i}", servizio_base=f"test service {i}", ore_lavorate=1.0 + i
            )
            await agent.execute(context)

        # Check metrics
        metrics = agent.get_metrics()
        assert metrics["total_requests"] == 3
        assert metrics["total_tokens"] == 1200  # 400 * 3
        assert metrics["avg_tokens_per_request"] == 400

    async def test_language_preference(self, mock_provider_with_response):
        """Test language preference is respected."""
        mock_response = {
            "descrizione_completa": "Professional web consulting",
            "deliverables": ["Code", "Documentation"],
            "competenze": ["Web Development"],
            "durata_ore": 2.0,
        }

        provider = mock_provider_with_response(mock_response)
        agent = InvoiceAssistantAgent(provider=provider)

        context = InvoiceContext(
            user_input="web consulting",
            servizio_base="web consulting",
            ore_lavorate=2.0,
            lingua_preferita="en",
        )

        response = await agent.execute(context)

        # Verify language is in metadata
        assert response.metadata["lingua"] == "en"

    async def test_cleanup_resources(self, mock_provider_with_response):
        """Test agent cleanup works correctly."""
        mock_response = {
            "descrizione_completa": "Test",
            "deliverables": [],
            "competenze": [],
            "durata_ore": 1.0,
        }

        provider = mock_provider_with_response(mock_response)
        agent = InvoiceAssistantAgent(provider=provider)

        context = InvoiceContext(user_input="test", servizio_base="test", ore_lavorate=1.0)

        await agent.execute(context)

        # Cleanup should log metrics
        await agent.cleanup()

        # Agent should still have metrics
        assert agent.total_requests > 0
