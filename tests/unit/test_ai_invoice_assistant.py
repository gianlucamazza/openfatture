"""Unit tests for Invoice Assistant agent."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.agents.models import InvoiceDescriptionOutput
from openfatture.ai.domain.context import InvoiceContext
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
                    "descrizione_completa": "Consulenza professionale per sviluppo web\n\nAttività svolte:\n- Analisi requisiti\n- Sviluppo codice\n- Testing",
                    "deliverables": ["Codice sorgente", "Documentazione"],
                    "competenze": ["Python", "FastAPI"],
                    "durata_ore": 3.0,
                    "note": "Progetto completato con successo",
                }
            ),
            status=ResponseStatus.SUCCESS,
            model="mock-model",
            provider="mock",
            usage=UsageMetrics(
                prompt_tokens=100, completion_tokens=200, total_tokens=300, estimated_cost_usd=0.01
            ),
            latency_ms=500.0,
        )

    provider.generate = AsyncMock(side_effect=mock_generate)

    return provider


@pytest.fixture
def mock_prompt_manager():
    """Create a mock prompt manager."""
    manager = MagicMock()

    def mock_render(*args, **kwargs):
        return (
            "System prompt for invoice assistant",
            "User prompt: Generate description for service",
        )

    manager.render_with_examples = MagicMock(side_effect=mock_render)

    return manager


@pytest.fixture
def invoice_assistant(mock_provider, mock_prompt_manager):
    """Create Invoice Assistant agent with mocked dependencies."""
    agent = InvoiceAssistantAgent(
        provider=mock_provider, prompt_manager=mock_prompt_manager, use_structured_output=True
    )
    return agent


@pytest.mark.asyncio
@pytest.mark.ai
class TestInvoiceAssistantAgent:
    """Test suite for Invoice Assistant agent."""

    async def test_agent_initialization(self, invoice_assistant):
        """Test agent is initialized correctly."""
        assert invoice_assistant.config.name == "invoice_assistant"
        assert invoice_assistant.config.temperature == 0.7
        assert invoice_assistant.config.max_tokens == 800
        assert invoice_assistant.use_structured_output is True

    async def test_basic_description_generation(self, invoice_assistant):
        """Test basic invoice description generation."""
        context = InvoiceContext(
            user_input="3 ore consulenza web",
            servizio_base="3 ore consulenza web",
            ore_lavorate=3.0,
        )

        response = await invoice_assistant.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        assert response.agent_name == "invoice_assistant"
        assert response.content is not None
        assert response.usage.total_tokens == 300

    async def test_structured_output_parsing(self, invoice_assistant):
        """Test structured output is parsed correctly."""
        context = InvoiceContext(
            user_input="5 ore sviluppo backend",
            servizio_base="5 ore sviluppo backend",
            ore_lavorate=5.0,
        )

        response = await invoice_assistant.execute(context)

        # Check structured output
        assert response.metadata.get("is_structured") is True
        assert "parsed_model" in response.metadata

        model = response.metadata["parsed_model"]
        assert "descrizione_completa" in model
        assert "deliverables" in model
        assert "competenze" in model

    async def test_validation_required_fields(self, invoice_assistant):
        """Test validation of required fields."""
        # Missing servizio_base
        context = InvoiceContext(user_input="", servizio_base="", ore_lavorate=5.0)

        is_valid, error = await invoice_assistant.validate_input(context)

        assert is_valid is False
        assert "servizio_base è richiesto" in error

    async def test_validation_field_length(self, invoice_assistant):
        """Test validation of field lengths."""
        # servizio_base too long
        context = InvoiceContext(
            user_input="test", servizio_base="x" * 501, ore_lavorate=5.0  # Max is 500
        )

        is_valid, error = await invoice_assistant.validate_input(context)

        assert is_valid is False
        assert "troppo lungo" in error

    async def test_validation_hours_positive(self, invoice_assistant):
        """Test validation of hours being positive."""
        context = InvoiceContext(
            user_input="test", servizio_base="Consulenza", ore_lavorate=-5.0  # Invalid
        )

        is_valid, error = await invoice_assistant.validate_input(context)

        assert is_valid is False
        assert "positivo" in error

    async def test_validation_hours_realistic(self, invoice_assistant):
        """Test validation of hours being realistic."""
        context = InvoiceContext(
            user_input="test", servizio_base="Consulenza", ore_lavorate=10000.0  # Unrealistic
        )

        is_valid, error = await invoice_assistant.validate_input(context)

        assert is_valid is False
        assert "irrealistico" in error

    async def test_context_with_technologies(self, invoice_assistant):
        """Test context includes technologies."""
        context = InvoiceContext(
            user_input="sviluppo API",
            servizio_base="sviluppo API",
            ore_lavorate=8.0,
            tecnologie=["Python", "FastAPI", "PostgreSQL"],
        )

        response = await invoice_assistant.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        # Verify technologies are in metadata
        assert context.tecnologie == ["Python", "FastAPI", "PostgreSQL"]

    async def test_context_with_project(self, invoice_assistant):
        """Test context includes project information."""
        context = InvoiceContext(
            user_input="sviluppo backend",
            servizio_base="sviluppo backend",
            ore_lavorate=10.0,
            progetto="Sistema E-commerce",
            tariffa_oraria=100.0,
        )

        response = await invoice_assistant.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        assert context.progetto == "Sistema E-commerce"
        assert context.tariffa_oraria == 100.0

    async def test_context_with_deliverables(self, invoice_assistant):
        """Test context includes deliverables."""
        context = InvoiceContext(
            user_input="audit sicurezza",
            servizio_base="audit sicurezza",
            ore_lavorate=8.0,
            deliverables=["Report audit", "Piano remediation"],
        )

        response = await invoice_assistant.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        assert len(context.deliverables) == 2

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

        agent = InvoiceAssistantAgent(
            provider=mock_provider, prompt_manager=mock_prompt_manager, use_structured_output=True
        )

        context = InvoiceContext(user_input="test", servizio_base="test", ore_lavorate=1.0)

        response = await agent.execute(context)

        # Should fallback gracefully
        assert response.metadata.get("is_structured") is False

    async def test_metadata_includes_context_info(self, invoice_assistant):
        """Test response metadata includes context information."""
        context = InvoiceContext(
            user_input="consulenza",
            servizio_base="consulenza IT",
            ore_lavorate=5.0,
            lingua_preferita="it",
        )

        response = await invoice_assistant.execute(context)

        assert response.metadata["servizio_base"] == "consulenza IT"
        assert response.metadata["ore_lavorate"] == 5.0
        assert response.metadata["lingua"] == "it"

    async def test_prompt_building_with_all_fields(self, invoice_assistant):
        """Test prompt is built correctly with all fields."""
        context = InvoiceContext(
            user_input="sviluppo completo",
            servizio_base="sviluppo completo",
            ore_lavorate=40.0,
            tariffa_oraria=80.0,
            progetto="Portale Aziendale",
            tecnologie=["React", "Node.js", "MongoDB"],
            deliverables=["Codice", "Documentazione", "Tests"],
        )

        # Execute to trigger prompt building
        response = await invoice_assistant.execute(context)

        # Verify prompt manager was called with correct variables
        call_args = invoice_assistant.prompt_manager.render_with_examples.call_args

        assert call_args is not None
        template_vars = call_args[0][1]

        assert template_vars["servizio_base"] == "sviluppo completo"
        assert template_vars["ore_lavorate"] == 40.0
        assert template_vars["tariffa_oraria"] == 80.0
        assert template_vars["progetto"] == "Portale Aziendale"
        assert template_vars["tecnologie"] == ["React", "Node.js", "MongoDB"]
        assert template_vars["deliverables"] == ["Codice", "Documentazione", "Tests"]

    async def test_fallback_prompt_when_yaml_not_found(self, mock_provider):
        """Test fallback prompt is used when YAML template not found."""
        # Mock prompt manager to raise FileNotFoundError
        mock_pm = MagicMock()
        mock_pm.render_with_examples = MagicMock(
            side_effect=FileNotFoundError("Template not found")
        )

        agent = InvoiceAssistantAgent(
            provider=mock_provider, prompt_manager=mock_pm, use_structured_output=True
        )

        context = InvoiceContext(user_input="test", servizio_base="test service", ore_lavorate=2.0)

        response = await agent.execute(context)

        # Should use fallback and still work
        assert response.status == ResponseStatus.SUCCESS

    async def test_cost_tracking(self, invoice_assistant):
        """Test cost tracking in agent metrics."""
        context = InvoiceContext(user_input="test", servizio_base="test", ore_lavorate=1.0)

        # Execute multiple times
        for _ in range(3):
            await invoice_assistant.execute(context)

        # Check metrics
        metrics = invoice_assistant.get_metrics()

        assert metrics["total_requests"] == 3
        assert metrics["total_tokens"] == 900  # 300 * 3
        assert metrics["total_cost_usd"] == 0.03  # 0.01 * 3


@pytest.mark.ai
class TestInvoiceDescriptionOutput:
    """Test structured output model."""

    def test_valid_model_creation(self):
        """Test creating a valid model."""
        model = InvoiceDescriptionOutput(
            descrizione_completa="Consulenza professionale...",
            deliverables=["Codice", "Docs"],
            competenze=["Python", "FastAPI"],
            durata_ore=5.0,
            note="Completato",
        )

        assert model.descrizione_completa == "Consulenza professionale..."
        assert len(model.deliverables) == 2
        assert len(model.competenze) == 2
        assert model.durata_ore == 5.0
        assert model.note == "Completato"

    def test_description_length_limit(self):
        """Test description respects FatturaPA 1000 char limit."""
        # This should fail validation
        with pytest.raises(ValueError):
            InvoiceDescriptionOutput(
                descrizione_completa="x" * 1001, deliverables=[], competenze=[]  # Over limit
            )

    def test_default_values(self):
        """Test default values are set correctly."""
        model = InvoiceDescriptionOutput(descrizione_completa="Test description")

        assert model.deliverables == []
        assert model.competenze == []
        assert model.durata_ore is None
        assert model.note is None

    def test_model_serialization(self):
        """Test model can be serialized to dict."""
        model = InvoiceDescriptionOutput(
            descrizione_completa="Test",
            deliverables=["A", "B"],
            competenze=["Python"],
            durata_ore=3.0,
        )

        data = model.model_dump()

        assert data["descrizione_completa"] == "Test"
        assert data["deliverables"] == ["A", "B"]
        assert data["competenze"] == ["Python"]
        assert data["durata_ore"] == 3.0

    def test_json_serialization(self):
        """Test model can be serialized to JSON."""
        model = InvoiceDescriptionOutput(
            descrizione_completa="Test description",
            deliverables=["Deliverable 1"],
            competenze=["Skill 1"],
            durata_ore=2.5,
        )

        json_str = model.model_dump_json()
        data = json.loads(json_str)

        assert data["descrizione_completa"] == "Test description"
        assert data["durata_ore"] == 2.5
