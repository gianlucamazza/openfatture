"""Unit tests for Tax Advisor agent."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from openfatture.ai.agents.models import TaxSuggestionOutput
from openfatture.ai.agents.tax_advisor import TaxAdvisorAgent
from openfatture.ai.domain.context import TaxContext
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.providers.base import BaseLLMProvider


@pytest.fixture
def mock_provider():
    """Create a mock LLM provider."""
    provider = MagicMock(spec=BaseLLMProvider)
    provider.provider_name = "mock"
    provider.model = "mock-model"

    # Mock the generate method to return a valid JSON response
    async def mock_generate(*args, **kwargs):
        return AgentResponse(
            content=json.dumps(
                {
                    "aliquota_iva": 22.0,
                    "codice_natura": None,
                    "reverse_charge": False,
                    "split_payment": False,
                    "regime_speciale": None,
                    "spiegazione": "Aliquota ordinaria 22%",
                    "riferimento_normativo": "Art. 1, DPR 633/72",
                    "note_fattura": None,
                    "confidence": 0.95,
                    "raccomandazioni": [],
                }
            ),
            status=ResponseStatus.SUCCESS,
            model="mock-model",
            provider="mock",
            usage=UsageMetrics(
                prompt_tokens=100, completion_tokens=150, total_tokens=250, estimated_cost_usd=0.005
            ),
            latency_ms=400.0,
        )

    provider.generate = AsyncMock(side_effect=mock_generate)

    return provider


@pytest.fixture
def mock_prompt_manager():
    """Create a mock prompt manager."""
    manager = MagicMock()

    def mock_render(*args, **kwargs):
        return ("System prompt for tax advisor", "User prompt: Analyze fiscal treatment")

    manager.render_with_examples = MagicMock(side_effect=mock_render)

    return manager


@pytest.fixture
def tax_advisor(mock_provider, mock_prompt_manager):
    """Create Tax Advisor agent with mocked dependencies."""
    agent = TaxAdvisorAgent(
        provider=mock_provider, prompt_manager=mock_prompt_manager, use_structured_output=True
    )
    return agent


@pytest.mark.asyncio
@pytest.mark.ai
class TestTaxAdvisorAgent:
    """Test suite for Tax Advisor agent."""

    async def test_agent_initialization(self, tax_advisor):
        """Test agent is initialized correctly."""
        assert tax_advisor.config.name == "tax_advisor"
        assert tax_advisor.config.temperature == 0.3  # Lower for accuracy
        assert tax_advisor.config.max_tokens == 800
        assert tax_advisor.use_structured_output is True

    async def test_basic_vat_suggestion(self, tax_advisor):
        """Test basic VAT rate suggestion."""
        context = TaxContext(user_input="consulenza IT", tipo_servizio="consulenza IT")

        response = await tax_advisor.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        assert response.agent_name == "tax_advisor"
        assert response.content is not None

    async def test_structured_output_parsing(self, tax_advisor):
        """Test structured output is parsed correctly."""
        context = TaxContext(user_input="consulenza", tipo_servizio="consulenza IT")

        response = await tax_advisor.execute(context)

        # Check structured output
        assert response.metadata.get("is_structured") is True
        assert "parsed_model" in response.metadata

        model = response.metadata["parsed_model"]
        assert "aliquota_iva" in model
        assert "spiegazione" in model
        assert "riferimento_normativo" in model

    async def test_validation_required_fields(self, tax_advisor):
        """Test validation of required fields."""
        # Missing tipo_servizio
        context = TaxContext(user_input="", tipo_servizio="")

        is_valid, error = await tax_advisor.validate_input(context)

        assert is_valid is False
        assert "tipo_servizio è richiesto" in error

    async def test_validation_field_length(self, tax_advisor):
        """Test validation of field lengths."""
        # tipo_servizio too long
        context = TaxContext(user_input="test", tipo_servizio="x" * 501)  # Max is 500

        is_valid, error = await tax_advisor.validate_input(context)

        assert is_valid is False
        assert "troppo lungo" in error

    async def test_validation_negative_amount(self, tax_advisor):
        """Test validation rejects negative amounts."""
        context = TaxContext(user_input="test", tipo_servizio="consulenza", importo=-100.0)

        is_valid, error = await tax_advisor.validate_input(context)

        assert is_valid is False
        assert "negativo" in error

    async def test_validation_unrealistic_amount(self, tax_advisor):
        """Test validation flags unrealistic amounts."""
        context = TaxContext(
            user_input="test", tipo_servizio="consulenza", importo=2_000_000.0  # Over 1M
        )

        is_valid, error = await tax_advisor.validate_input(context)

        assert is_valid is False
        assert "irrealistico" in error

    async def test_validation_country_code(self, tax_advisor):
        """Test validation of country code format."""
        context = TaxContext(
            user_input="test",
            tipo_servizio="consulenza",
            paese_cliente="ITALY",  # Should be 2 letters
        )

        is_valid, error = await tax_advisor.validate_input(context)

        assert is_valid is False
        assert "ISO 2 lettere" in error

    async def test_context_with_pa(self, tax_advisor):
        """Test context with Public Administration client."""
        context = TaxContext(
            user_input="consulenza PA", tipo_servizio="consulenza IT", cliente_pa=True
        )

        response = await tax_advisor.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        assert context.cliente_pa is True

    async def test_context_with_foreign_client(self, tax_advisor):
        """Test context with foreign client."""
        context = TaxContext(
            user_input="consulenza export",
            tipo_servizio="consulenza IT",
            cliente_estero=True,
            paese_cliente="US",
        )

        response = await tax_advisor.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        assert context.cliente_estero is True
        assert context.paese_cliente == "US"

    async def test_context_with_ateco(self, tax_advisor):
        """Test context includes ATECO code."""
        context = TaxContext(
            user_input="consulenza", tipo_servizio="consulenza IT", codice_ateco="62.01.00"
        )

        response = await tax_advisor.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        assert context.codice_ateco == "62.01.00"

    async def test_fallback_when_json_parse_fails(self, mock_provider, mock_prompt_manager):
        """Test fallback to plain text when JSON parsing fails."""

        # Mock provider to return invalid JSON
        async def mock_generate_invalid(*args, **kwargs):
            return AgentResponse(
                content="This is not valid JSON",
                status=ResponseStatus.SUCCESS,
                model="mock-model",
                provider="mock",
                usage=UsageMetrics(prompt_tokens=100, completion_tokens=50, total_tokens=150),
            )

        mock_provider.generate = AsyncMock(side_effect=mock_generate_invalid)

        agent = TaxAdvisorAgent(
            provider=mock_provider, prompt_manager=mock_prompt_manager, use_structured_output=True
        )

        context = TaxContext(user_input="test", tipo_servizio="test service")

        response = await agent.execute(context)

        # Should fallback gracefully
        assert response.metadata.get("is_structured") is False

    async def test_metadata_includes_context_info(self, tax_advisor):
        """Test response metadata includes context information."""
        context = TaxContext(
            user_input="consulenza",
            tipo_servizio="consulenza IT",
            cliente_pa=True,
            cliente_estero=False,
        )

        response = await tax_advisor.execute(context)

        assert response.metadata["tipo_servizio"] == "consulenza IT"
        assert response.metadata["cliente_pa"] is True
        assert response.metadata["cliente_estero"] is False

    async def test_prompt_building_with_all_fields(self, tax_advisor):
        """Test prompt is built correctly with all fields."""
        context = TaxContext(
            user_input="consulenza completa",
            tipo_servizio="consulenza IT",
            categoria_servizio="Software",
            importo=5000.0,
            cliente_pa=True,
            cliente_estero=False,
            paese_cliente="IT",
            codice_ateco="62.01.00",
        )

        # Execute to trigger prompt building
        response = await tax_advisor.execute(context)

        # Verify prompt manager was called with correct variables
        call_args = tax_advisor.prompt_manager.render_with_examples.call_args

        assert call_args is not None
        template_vars = call_args[0][1]

        assert template_vars["tipo_servizio"] == "consulenza IT"
        assert template_vars["categoria_servizio"] == "Software"
        assert template_vars["importo"] == 5000.0
        assert template_vars["cliente_pa"] is True
        assert template_vars["codice_ateco"] == "62.01.00"

    async def test_fallback_prompt_when_yaml_not_found(self, mock_provider):
        """Test fallback prompt is used when YAML template not found."""
        # Mock prompt manager to raise FileNotFoundError
        mock_pm = MagicMock()
        mock_pm.render_with_examples = MagicMock(
            side_effect=FileNotFoundError("Template not found")
        )

        agent = TaxAdvisorAgent(
            provider=mock_provider, prompt_manager=mock_pm, use_structured_output=True
        )

        context = TaxContext(user_input="test", tipo_servizio="test service")

        response = await agent.execute(context)

        # Should use fallback and still work
        assert response.status == ResponseStatus.SUCCESS

    async def test_cost_tracking(self, tax_advisor):
        """Test cost tracking in agent metrics."""
        context = TaxContext(user_input="test", tipo_servizio="test")

        # Execute multiple times
        for _ in range(3):
            await tax_advisor.execute(context)

        # Check metrics
        metrics = tax_advisor.get_metrics()

        assert metrics["total_requests"] == 3
        assert metrics["total_tokens"] == 750  # 250 * 3
        assert metrics["total_cost_usd"] == 0.015  # 0.005 * 3


@pytest.mark.ai
class TestTaxSuggestionOutput:
    """Test structured output model."""

    def test_valid_model_creation(self):
        """Test creating a valid tax suggestion model."""
        model = TaxSuggestionOutput(
            aliquota_iva=22.0,
            spiegazione="Aliquota ordinaria",
            riferimento_normativo="Art. 1, DPR 633/72",
            confidence=0.95,
        )

        assert model.aliquota_iva == 22.0
        assert model.reverse_charge is False
        assert model.split_payment is False
        assert model.confidence == 0.95

    def test_model_with_reverse_charge(self):
        """Test model with reverse charge."""
        model = TaxSuggestionOutput(
            aliquota_iva=22.0,
            codice_natura="N6.2",
            reverse_charge=True,
            spiegazione="Reverse charge edilizia",
            riferimento_normativo="Art. 17, c. 6, lett. a-ter, DPR 633/72",
            note_fattura="Inversione contabile",
        )

        assert model.reverse_charge is True
        assert model.codice_natura == "N6.2"
        assert model.note_fattura == "Inversione contabile"

    def test_model_with_split_payment(self):
        """Test model with split payment."""
        model = TaxSuggestionOutput(
            aliquota_iva=22.0,
            split_payment=True,
            spiegazione="Split payment PA",
            riferimento_normativo="Art. 17-ter, DPR 633/72",
        )

        assert model.split_payment is True

    def test_aliquota_iva_range_validation(self):
        """Test VAT rate must be in valid range."""
        with pytest.raises(ValueError):
            TaxSuggestionOutput(
                aliquota_iva=150.0, spiegazione="Test", riferimento_normativo="Test"  # Over 100
            )

        with pytest.raises(ValueError):
            TaxSuggestionOutput(
                aliquota_iva=-5.0, spiegazione="Test", riferimento_normativo="Test"  # Negative
            )

    def test_codice_natura_pattern_validation(self):
        """Test natura code pattern validation."""
        # Valid patterns
        TaxSuggestionOutput(
            aliquota_iva=0.0, codice_natura="N1", spiegazione="Test", riferimento_normativo="Test"
        )

        TaxSuggestionOutput(
            aliquota_iva=0.0, codice_natura="N6.2", spiegazione="Test", riferimento_normativo="Test"
        )

        # Invalid pattern should fail
        with pytest.raises(ValueError):
            TaxSuggestionOutput(
                aliquota_iva=0.0,
                codice_natura="X99",  # Invalid
                spiegazione="Test",
                riferimento_normativo="Test",
            )

    def test_model_serialization(self):
        """Test model can be serialized to dict."""
        model = TaxSuggestionOutput(
            aliquota_iva=22.0,
            reverse_charge=True,
            spiegazione="Test",
            riferimento_normativo="Art. 17",
            raccomandazioni=["Verifica cliente", "Non addebitare IVA"],
        )

        data = model.model_dump()

        assert data["aliquota_iva"] == 22.0
        assert data["reverse_charge"] is True
        assert len(data["raccomandazioni"]) == 2

    def test_json_serialization(self):
        """Test model can be serialized to JSON."""
        model = TaxSuggestionOutput(
            aliquota_iva=10.0,
            codice_natura="N4",
            spiegazione="Aliquota ridotta",
            riferimento_normativo="Tabella A, DPR 633/72",
            confidence=0.85,
        )

        json_str = model.model_dump_json()
        data = json.loads(json_str)

        assert data["aliquota_iva"] == 10.0
        assert data["codice_natura"] == "N4"
        assert data["confidence"] == 0.85
