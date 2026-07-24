"""E2E tests for AI agents using real Anthropic provider.

Requires OPENFATTURE_AI_ANTHROPIC_API_KEY to be set.
Run with: pytest -m "anthropic and e2e"
"""

import json

import pytest

from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.agents.tax_advisor import TaxAdvisorAgent
from openfatture.ai.domain.context import InvoiceContext, TaxContext
from openfatture.ai.domain.response import ResponseStatus


@pytest.mark.anthropic
@pytest.mark.e2e
class TestAnthropicInvoiceAssistant:
    """Test InvoiceAssistant with real Anthropic provider."""

    async def test_basic_invoice_description(self, anthropic_provider):
        """Test basic invoice description generation."""
        agent = InvoiceAssistantAgent(provider=anthropic_provider)
        context = InvoiceContext(user_input="3 ore consulenza web")

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        assert response.content
        assert response.usage.total_tokens > 0

        # Validate JSON structure
        response_data = json.loads(response.content)
        assert "descrizione_completa" in response_data
        assert "deliverables" in response_data
        assert "competenze" in response_data

        # Check for Italian business terms
        full_text = response.content.lower()
        business_terms = ["consulenza", "web", "sviluppo", "servizio"]
        assert any(
            term in full_text for term in business_terms
        ), f"No business terms found in: {response.content}"

    async def test_complex_invoice_with_client(self, anthropic_provider):
        """Test invoice description with client context."""
        agent = InvoiceAssistantAgent(provider=anthropic_provider)
        context = InvoiceContext(
            user_input="Sviluppo applicazione mobile per cliente TechCorp", progetto="TechCorp SRL"
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        response_data = json.loads(response.content)

        # Should include client reference
        full_text = response.content.lower()
        assert "techcorp" in full_text or "cliente" in full_text

    async def test_technical_focus_invoice(self, anthropic_provider):
        """Test invoice with technical focus."""
        agent = InvoiceAssistantAgent(provider=anthropic_provider)
        context = InvoiceContext(user_input="Implementazione API REST con FastAPI e PostgreSQL")

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        response_data = json.loads(response.content)

        # Should mention technical skills
        competenze = response_data.get("competenze", [])
        technical_skills = ["python", "fastapi", "postgresql", "api", "rest"]
        found_skills = [
            skill
            for skill in technical_skills
            if any(skill.lower() in comp.lower() for comp in competenze)
        ]
        assert len(found_skills) > 0, f"No technical skills found in: {competenze}"

    async def test_response_latency(self, anthropic_provider):
        """Test response latency is within acceptable bounds."""
        import time

        agent = InvoiceAssistantAgent(provider=anthropic_provider)
        context = InvoiceContext(user_input="1 ora formazione Python")

        start = time.time()
        response = await agent.execute(context)
        latency = time.time() - start

        assert latency < 30.0, f"Response took {latency:.2f}s, expected < 30.0s"
        assert response.status == ResponseStatus.SUCCESS

    async def test_token_usage_tracking(self, anthropic_provider):
        """Test token usage is properly tracked."""
        agent = InvoiceAssistantAgent(provider=anthropic_provider)
        context = InvoiceContext(user_input="Consulenza strategica aziendale")

        response = await agent.execute(context)

        assert response.usage.prompt_tokens > 0
        assert response.usage.completion_tokens > 0
        assert (
            response.usage.total_tokens
            == response.usage.prompt_tokens + response.usage.completion_tokens
        )

        # Cost estimation should be reasonable
        cost = anthropic_provider.estimate_cost(response.usage)
        assert cost > 0 and cost < 1.0  # Should be less than $1 for simple request

    async def test_malformed_prompt_handling(self, anthropic_provider):
        """Test handling of malformed or empty prompts."""
        agent = InvoiceAssistantAgent(provider=anthropic_provider)

        # Test with very short input
        context = InvoiceContext(user_input="x")
        response = await agent.execute(context)

        # Should still succeed and provide reasonable response
        assert response.status == ResponseStatus.SUCCESS
        response_data = json.loads(response.content)
        assert "descrizione_completa" in response_data

    async def test_structured_output_fallback(self, anthropic_provider):
        """Test fallback when structured output fails."""
        agent = InvoiceAssistantAgent(provider=anthropic_provider)
        context = InvoiceContext(user_input="Attività non standard senza descrizione chiara")

        response = await agent.execute(context)

        # Should succeed even if JSON parsing has issues
        assert response.status == ResponseStatus.SUCCESS
        # Content should be valid JSON
        json.loads(response.content)  # Should not raise


@pytest.mark.anthropic
@pytest.mark.e2e
class TestAnthropicTaxAdvisor:
    """Test TaxAdvisor with real Anthropic provider."""

    async def test_standard_vat_rate(self, anthropic_provider):
        """Test standard VAT rate recommendation."""
        agent = TaxAdvisorAgent(provider=anthropic_provider)
        context = TaxContext(
            user_input="Vendita software a cliente italiano", tipo_servizio="software"
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        response_data = json.loads(response.content)

        assert "aliquota_iva" in response_data
        assert "spiegazione" in response_data
        assert "riferimento_normativo" in response_data

        # Should recommend 22% for standard VAT
        aliquota = response_data["aliquota_iva"]
        assert isinstance(aliquota, int | float)
        assert aliquota == 22.0

    async def test_reverse_charge_construction(self, anthropic_provider):
        """Test reverse charge for construction services."""
        agent = TaxAdvisorAgent(provider=anthropic_provider)
        context = TaxContext(
            user_input="Lavori edili per edificio commerciale",
            tipo_servizio="edilizia",
            reverse_charge=True,
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        response_data = json.loads(response.content)

        # Should mention reverse charge or inversione contabile
        full_text = response.content.lower()
        assert any(
            term in full_text for term in ["reverse charge", "inversione contabile", "art. 17"]
        )

    async def test_split_payment_public_administration(self, anthropic_provider):
        """Test split payment for public administration."""
        agent = TaxAdvisorAgent(provider=anthropic_provider)
        context = TaxContext(
            user_input="Fornitura a ente pubblico",
            tipo_servizio="generica",
            cliente_pa=True,
            split_payment=True,
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        response_data = json.loads(response.content)

        # Should mention split payment
        full_text = response.content.lower()
        assert any(term in full_text for term in ["split payment", "scissione pagamenti"])

    async def test_exempt_services(self, anthropic_provider):
        """Test exempt services (medical, education, etc.)."""
        agent = TaxAdvisorAgent(provider=anthropic_provider)
        context = TaxContext(
            user_input="Servizi medici specialistici", tipo_servizio="servizi_medici"
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        response_data = json.loads(response.content)

        # Should recommend 0% VAT for exempt services
        aliquota = response_data["aliquota_iva"]
        assert aliquota == 0.0

        # Should mention exemption
        full_text = response.content.lower()
        assert any(term in full_text for term in ["esente", "esenzione", "natura"])

    async def test_foreign_client_export(self, anthropic_provider):
        """Test export to foreign client (0% VAT)."""
        agent = TaxAdvisorAgent(provider=anthropic_provider)
        context = TaxContext(
            user_input="Esportazione software a cliente francese",
            tipo_servizio="software",
            cliente_estero=True,
            paese_cliente="FR",
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        response_data = json.loads(response.content)

        # Should recommend 0% VAT for exports
        aliquota = response_data["aliquota_iva"]
        assert aliquota == 0.0

    async def test_reduced_vat_rate(self, anthropic_provider):
        """Test reduced VAT rate for specific goods/services."""
        agent = TaxAdvisorAgent(provider=anthropic_provider)
        context = TaxContext(
            user_input="Vendita libri scolastici", tipo_servizio="libri_scolastici"
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        response_data = json.loads(response.content)

        # Should recommend 4% or 10% for reduced rate
        aliquota = response_data["aliquota_iva"]
        assert aliquota in [4.0, 10.0]

    async def test_regime_forfettario(self, anthropic_provider):
        """Test forfettario regime (lump sum taxation)."""
        agent = TaxAdvisorAgent(provider=anthropic_provider)
        context = TaxContext(
            user_input="Consulenza gestionale", tipo_servizio="consulenza", regime_speciale="RF19"
        )

        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        response_data = json.loads(response.content)

        # In forfettario regime, VAT is included in lump sum
        # Should mention forfettario
        full_text = response.content.lower()
        assert any(term in full_text for term in ["forfettario", "regime forfettario", "flat tax"])


@pytest.mark.anthropic
@pytest.mark.e2e
class TestAnthropicProviderCapabilities:
    """Test Anthropic provider specific capabilities."""

    async def test_streaming_support(self, anthropic_provider):
        """Test that Anthropic provider supports streaming."""
        assert anthropic_provider.supports_streaming

        # Test basic streaming
        messages = [{"role": "user", "content": "Hello"}]
        tokens = []
        async for token in anthropic_provider.stream(messages):
            tokens.append(token)
            if len(tokens) >= 5:  # Get first few tokens
                break

        assert len(tokens) > 0
        assert all(isinstance(token, str) for token in tokens)

    async def test_tool_calling_support(self, anthropic_provider):
        """Test that Anthropic provider supports tool calling."""
        assert anthropic_provider.supports_tools

    async def test_token_counting_accuracy(self, anthropic_provider):
        """Test token counting is reasonable."""
        text = "Questo è un testo di prova per contare i token."
        tokens = anthropic_provider.count_tokens(text)

        # Should be reasonable estimate (Anthropic uses different tokenizer)
        assert 10 <= tokens <= 25

        # Empty text should be 0
        assert anthropic_provider.count_tokens("") == 0

    async def test_cost_estimation(self, anthropic_provider):
        """Test cost estimation for different token counts."""
        from openfatture.ai.domain.response import UsageMetrics

        # Low usage
        low_usage = UsageMetrics(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        low_cost = anthropic_provider.estimate_cost(low_usage)
        assert low_cost > 0

        # High usage
        high_usage = UsageMetrics(prompt_tokens=1000, completion_tokens=500, total_tokens=1500)
        high_cost = anthropic_provider.estimate_cost(high_usage)
        assert high_cost > low_cost  # Higher usage should cost more

    async def test_health_check_reliability(self, anthropic_provider):
        """Test health check works consistently."""
        # Should pass multiple times
        for _ in range(3):
            healthy = await anthropic_provider.health_check()
            assert healthy is True

    async def test_error_handling_rate_limits(self, anthropic_provider):
        """Test graceful handling of rate limits (if they occur)."""
        # This test might be skipped if no rate limits occur
        # But ensures error handling works
        agent = InvoiceAssistantAgent(provider=anthropic_provider)
        context = InvoiceContext(user_input="Test rate limit handling")

        response = await agent.execute(context)

        # Should either succeed or fail gracefully
        assert response.status in [ResponseStatus.SUCCESS, ResponseStatus.ERROR]
        if response.status == ResponseStatus.ERROR:
            assert "rate limit" in response.content.lower() or "quota" in response.content.lower()
