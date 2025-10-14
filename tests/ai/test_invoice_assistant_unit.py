"""Unit tests for InvoiceAssistantAgent.

These tests focus on individual methods and components in isolation,
using mocks to avoid external dependencies.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.agents.models import InvoiceDescriptionOutput
from openfatture.ai.domain.context import InvoiceContext
from openfatture.ai.domain.prompt import PromptManager
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.storage.database.models import Cliente


@pytest.fixture
def mock_provider():
    """Create a mock LLM provider."""
    provider = MagicMock(spec=BaseLLMProvider)
    provider.provider_name = "mock"
    provider.model = "mock-model"
    provider.generate = AsyncMock()
    return provider


@pytest.fixture
def mock_prompt_manager():
    """Create a mock prompt manager."""
    manager = MagicMock(spec=PromptManager)
    manager.render_with_examples = MagicMock(return_value=("System prompt", "User prompt"))
    return manager


@pytest.fixture
def mock_prompt_manager_error():
    """Create a mock prompt manager that raises FileNotFoundError."""
    manager = MagicMock(spec=PromptManager)
    manager.render_with_examples = MagicMock(side_effect=FileNotFoundError("Template not found"))
    return manager


@pytest.fixture
def sample_context():
    """Create a sample invoice context."""
    return InvoiceContext(
        user_input="3 ore consulenza web",
        servizio_base="consulenza web",
        ore_lavorate=3.0,
        tariffa_oraria=100.0,
        progetto="Sito web",
        tecnologie=["Python", "Django"],
        deliverables=["Codice", "Documentazione"],
    )


@pytest.fixture
def sample_cliente():
    """Create a sample client."""
    return Cliente(
        id=1,
        denominazione="Test Client",
        partita_iva="12345678901",
        codice_destinatario="ABC1234",
    )


class TestInvoiceAssistantAgent:
    """Unit tests for InvoiceAssistantAgent."""

    def test_initialization(self, mock_provider, mock_prompt_manager):
        """Test agent initialization with custom prompt manager."""
        agent = InvoiceAssistantAgent(
            provider=mock_provider,
            prompt_manager=mock_prompt_manager,
            use_structured_output=True,
        )

        assert agent.provider == mock_provider
        assert agent.prompt_manager == mock_prompt_manager
        assert agent.use_structured_output is True
        assert agent.config.name == "invoice_assistant"
        assert agent.config.temperature == 0.7
        assert agent.config.max_tokens == 800

    def test_initialization_default_prompt_manager(self, mock_provider):
        """Test agent initialization with default prompt manager."""
        with patch("openfatture.ai.agents.invoice_assistant.create_prompt_manager") as mock_create:
            mock_create.return_value = MagicMock(spec=PromptManager)
            agent = InvoiceAssistantAgent(provider=mock_provider)

            mock_create.assert_called_once()
            assert agent.prompt_manager is not None

    @pytest.mark.asyncio
    async def test_validate_input_valid(self, mock_provider, sample_context):
        """Test validate_input with valid context."""
        agent = InvoiceAssistantAgent(provider=mock_provider)

        is_valid, error = await agent.validate_input(sample_context)

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_input_missing_servizio_base(self, mock_provider):
        """Test validate_input with missing servizio_base."""
        agent = InvoiceAssistantAgent(provider=mock_provider)
        context = InvoiceContext(
            user_input="test",
            servizio_base="",  # Empty
            ore_lavorate=1.0,
        )

        is_valid, error = await agent.validate_input(context)

        assert is_valid is False
        assert error is not None and "servizio_base è richiesto" in error

    @pytest.mark.asyncio
    async def test_validate_input_whitespace_servizio_base(self, mock_provider):
        """Test validate_input with whitespace-only servizio_base."""
        agent = InvoiceAssistantAgent(provider=mock_provider)
        context = InvoiceContext(
            user_input="test",
            servizio_base="   ",  # Whitespace only
            ore_lavorate=1.0,
        )

        is_valid, error = await agent.validate_input(context)

        assert is_valid is False
        assert error is not None and "servizio_base è richiesto" in error

    @pytest.mark.asyncio
    async def test_validate_input_servizio_base_too_long(self, mock_provider):
        """Test validate_input with servizio_base exceeding length limit."""
        agent = InvoiceAssistantAgent(provider=mock_provider)
        long_service = "a" * 501  # 501 characters
        context = InvoiceContext(
            user_input="test",
            servizio_base=long_service,
            ore_lavorate=1.0,
        )

        is_valid, error = await agent.validate_input(context)

        assert is_valid is False
        assert error is not None and "troppo lungo" in error

    @pytest.mark.asyncio
    async def test_validate_input_negative_hours(self, mock_provider):
        """Test validate_input with negative ore_lavorate."""
        agent = InvoiceAssistantAgent(provider=mock_provider)
        context = InvoiceContext(
            user_input="test",
            servizio_base="test service",
            ore_lavorate=-1.0,  # Negative
        )

        is_valid, error = await agent.validate_input(context)

        assert is_valid is False
        assert error is not None and "deve essere positivo" in error

    @pytest.mark.asyncio
    async def test_validate_input_zero_hours(self, mock_provider):
        """Test validate_input with zero ore_lavorate."""
        agent = InvoiceAssistantAgent(provider=mock_provider)
        context = InvoiceContext(
            user_input="test",
            servizio_base="test service",
            ore_lavorate=0.0,  # Zero
        )

        is_valid, error = await agent.validate_input(context)

        assert is_valid is False
        assert error is not None and "deve essere positivo" in error

    @pytest.mark.asyncio
    async def test_validate_input_unrealistic_hours(self, mock_provider):
        """Test validate_input with unrealistic ore_lavorate."""
        agent = InvoiceAssistantAgent(provider=mock_provider)
        context = InvoiceContext(
            user_input="test",
            servizio_base="test service",
            ore_lavorate=1500.0,  # Unrealistic
        )

        is_valid, error = await agent.validate_input(context)

        assert is_valid is False
        assert error is not None and "irrealistico" in error

    @pytest.mark.asyncio
    async def test_validate_input_none_hours(self, mock_provider):
        """Test validate_input with None ore_lavorate (should be valid)."""
        agent = InvoiceAssistantAgent(provider=mock_provider)
        context = InvoiceContext(
            user_input="test",
            servizio_base="test service",
            ore_lavorate=None,  # None is allowed
        )

        is_valid, error = await agent.validate_input(context)

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_build_prompt_success(self, mock_provider, mock_prompt_manager, sample_context):
        """Test _build_prompt with successful template rendering."""
        agent = InvoiceAssistantAgent(
            provider=mock_provider,
            prompt_manager=mock_prompt_manager,
        )

        messages = await agent._build_prompt(sample_context)

        # Verify prompt manager was called correctly
        mock_prompt_manager.render_with_examples.assert_called_once_with(
            "invoice_assistant",
            {
                "servizio_base": sample_context.servizio_base,
                "ore_lavorate": sample_context.ore_lavorate,
                "tariffa_oraria": sample_context.tariffa_oraria,
                "tecnologie": sample_context.tecnologie,
                "progetto": sample_context.progetto,
                "cliente": sample_context.cliente,
                "deliverables": sample_context.deliverables,
            },
        )

        # Verify message structure
        assert len(messages) == 2
        assert messages[0].role.value == "system"
        assert messages[0].content == "System prompt"
        assert messages[1].role.value == "user"
        assert messages[1].content == "User prompt"

    @pytest.mark.asyncio
    async def test_build_prompt_with_context_message(
        self, mock_provider, mock_prompt_manager, sample_context
    ):
        """Test _build_prompt with relevant documents and knowledge snippets."""
        agent = InvoiceAssistantAgent(
            provider=mock_provider,
            prompt_manager=mock_prompt_manager,
        )

        # Add context data
        sample_context.relevant_documents = ["Similar invoice 1", "Similar invoice 2"]
        sample_context.knowledge_snippets = [
            {"citation": "Source 1", "excerpt": "Important guideline"},
            {"source": "Source 2", "excerpt": "Another guideline"},
        ]

        messages = await agent._build_prompt(sample_context)

        # Should have 3 messages: system, context, user
        assert len(messages) == 3
        assert messages[1].role.value == "system"
        assert "Documenti simili" in messages[1].content
        assert "Linee guida" in messages[1].content

    @pytest.mark.asyncio
    async def test_build_prompt_fallback_on_template_error(
        self, mock_provider, mock_prompt_manager_error, sample_context
    ):
        """Test _build_prompt fallback when template rendering fails."""
        agent = InvoiceAssistantAgent(
            provider=mock_provider,
            prompt_manager=mock_prompt_manager_error,
        )

        messages = await agent._build_prompt(sample_context)

        # Should use fallback prompts
        assert len(messages) == 2
        assert "esperto assistente" in messages[0].content.lower()
        assert "Servizio:" in messages[1].content

    @pytest.mark.asyncio
    async def test_parse_response_structured_success(self, mock_provider):
        """Test _parse_response with successful structured output parsing."""
        agent = InvoiceAssistantAgent(provider=mock_provider, use_structured_output=True)

        # Create response with valid JSON
        response_data = {
            "descrizione_completa": "Test description",
            "deliverables": ["Item 1", "Item 2"],
            "competenze": ["Skill 1"],
            "durata_ore": 2.0,
            "note": "Test note",
        }

        response = AgentResponse(
            content=json.dumps(response_data),
            status=ResponseStatus.SUCCESS,
            model="test-model",
            provider="test-provider",
            usage=UsageMetrics(
                prompt_tokens=100,
                completion_tokens=200,
                total_tokens=300,
                estimated_cost_usd=0.01,
            ),
            latency_ms=100.0,
        )

        context = InvoiceContext(
            user_input="test",
            servizio_base="test service",
            ore_lavorate=2.0,
        )

        parsed_response = await agent._parse_response(response, context)

        # Verify structured parsing
        assert parsed_response.metadata["is_structured"] is True
        assert "parsed_model" in parsed_response.metadata
        model_data = parsed_response.metadata["parsed_model"]
        assert model_data["descrizione_completa"] == "Test description"
        assert len(model_data["deliverables"]) == 2

    @pytest.mark.asyncio
    async def test_parse_response_structured_invalid_json(self, mock_provider):
        """Test _parse_response with invalid JSON in structured output."""
        agent = InvoiceAssistantAgent(provider=mock_provider, use_structured_output=True)

        # Create response with invalid JSON
        response = AgentResponse(
            content="Invalid JSON content",
            status=ResponseStatus.SUCCESS,
            model="test-model",
            provider="test-provider",
            usage=UsageMetrics(
                prompt_tokens=100,
                completion_tokens=200,
                total_tokens=300,
                estimated_cost_usd=0.01,
            ),
            latency_ms=100.0,
        )

        context = InvoiceContext(
            user_input="test",
            servizio_base="test service",
            ore_lavorate=2.0,
        )

        parsed_response = await agent._parse_response(response, context)

        # Should fall back to unstructured
        assert parsed_response.metadata["is_structured"] is False
        assert "parsed_model" not in parsed_response.metadata

    @pytest.mark.asyncio
    async def test_parse_response_structured_invalid_model(self, mock_provider):
        """Test _parse_response with JSON that doesn't match Pydantic model."""
        agent = InvoiceAssistantAgent(provider=mock_provider, use_structured_output=True)

        # Create response with JSON missing required fields
        response_data = {"invalid_field": "value"}

        response = AgentResponse(
            content=json.dumps(response_data),
            status=ResponseStatus.SUCCESS,
            model="test-model",
            provider="test-provider",
            usage=UsageMetrics(
                prompt_tokens=100,
                completion_tokens=200,
                total_tokens=300,
                estimated_cost_usd=0.01,
            ),
            latency_ms=100.0,
        )

        context = InvoiceContext(
            user_input="test",
            servizio_base="test service",
            ore_lavorate=2.0,
        )

        parsed_response = await agent._parse_response(response, context)

        # Should fall back to unstructured
        assert parsed_response.metadata["is_structured"] is False
        assert "parsed_model" not in parsed_response.metadata

    @pytest.mark.asyncio
    async def test_parse_response_unstructured(self, mock_provider):
        """Test _parse_response with unstructured output disabled."""
        agent = InvoiceAssistantAgent(provider=mock_provider, use_structured_output=False)

        response = AgentResponse(
            content="Plain text response",
            status=ResponseStatus.SUCCESS,
            model="test-model",
            provider="test-provider",
            usage=UsageMetrics(
                prompt_tokens=100,
                completion_tokens=200,
                total_tokens=300,
                estimated_cost_usd=0.01,
            ),
            latency_ms=100.0,
        )

        context = InvoiceContext(
            user_input="test",
            servizio_base="test service",
            ore_lavorate=2.0,
            lingua_preferita="en",
        )

        parsed_response = await agent._parse_response(response, context)

        # Should mark as unstructured and add context metadata
        assert parsed_response.metadata["is_structured"] is False
        assert parsed_response.metadata["servizio_base"] == "test service"
        assert parsed_response.metadata["ore_lavorate"] == 2.0
        assert parsed_response.metadata["lingua"] == "en"

    def test_build_context_message_no_context(self, mock_provider):
        """Test _build_context_message with no additional context."""
        agent = InvoiceAssistantAgent(provider=mock_provider)
        context = InvoiceContext(
            user_input="test",
            servizio_base="test service",
        )

        message = agent._build_context_message(context)

        assert message is None

    def test_build_context_message_with_documents(self, mock_provider):
        """Test _build_context_message with relevant documents."""
        agent = InvoiceAssistantAgent(provider=mock_provider)
        context = InvoiceContext(
            user_input="test",
            servizio_base="test service",
            relevant_documents=["Doc 1", "Doc 2", "Doc 3", "Doc 4"],  # More than 3
        )

        message = agent._build_context_message(context)

        assert message is not None
        assert "Documenti simili" in message
        assert "Doc 1" in message
        assert "Doc 2" in message
        assert "Doc 3" in message
        assert "Doc 4" not in message  # Limited to 3

    def test_build_context_message_with_snippets(self, mock_provider):
        """Test _build_context_message with knowledge snippets."""
        agent = InvoiceAssistantAgent(provider=mock_provider)
        context = InvoiceContext(
            user_input="test",
            servizio_base="test service",
            knowledge_snippets=[
                {"citation": "Source A", "excerpt": "Excerpt A"},
                {"source": "Source B", "excerpt": "Excerpt B"},
            ],
        )

        message = agent._build_context_message(context)

        assert message is not None
        assert "Linee guida" in message
        assert "[1] Source A" in message
        assert "[2] Source B" in message
        assert "Utilizza le fonti" in message

    def test_build_context_message_mixed_context(self, mock_provider):
        """Test _build_context_message with both documents and snippets."""
        agent = InvoiceAssistantAgent(provider=mock_provider)
        context = InvoiceContext(
            user_input="test",
            servizio_base="test service",
            relevant_documents=["Doc 1"],
            knowledge_snippets=[{"citation": "Source 1", "excerpt": "Excerpt 1"}],
        )

        message = agent._build_context_message(context)

        assert message is not None
        assert "Documenti simili" in message
        assert "Linee guida" in message

    def test_fallback_system_prompt(self, mock_provider):
        """Test _get_fallback_system_prompt content."""
        agent = InvoiceAssistantAgent(provider=mock_provider)

        prompt = agent._get_fallback_system_prompt()

        assert "esperto assistente" in prompt.lower()
        assert "fatture elettroniche italiane" in prompt.lower()
        assert "JSON" in prompt

    def test_build_fallback_user_prompt_basic(self, mock_provider, sample_context):
        """Test _build_fallback_user_prompt with basic context."""
        agent = InvoiceAssistantAgent(provider=mock_provider)

        prompt = agent._build_fallback_user_prompt(sample_context)

        assert "Servizio: consulenza web" in prompt
        assert "Ore: 3.0" in prompt
        assert "Tecnologie: Python, Django" in prompt
        assert "Progetto: Sito web" in prompt
        assert "JSON" in prompt

    def test_build_fallback_user_prompt_with_client(
        self, mock_provider, sample_context, sample_cliente
    ):
        """Test _build_fallback_user_prompt with client information."""
        agent = InvoiceAssistantAgent(provider=mock_provider)
        sample_context.cliente = sample_cliente

        prompt = agent._build_fallback_user_prompt(sample_context)

        assert "Cliente: Test Client" in prompt

    @pytest.mark.asyncio
    async def test_cleanup_logs_metrics(self, mock_provider):
        """Test cleanup method logs metrics correctly."""
        agent = InvoiceAssistantAgent(provider=mock_provider)

        # Simulate some activity
        agent.total_requests = 5
        agent.total_tokens = 1500
        agent.total_cost = 0.075
        agent.total_errors = 1

        with patch.object(agent.logger, "info") as mock_log:
            await agent.cleanup()

            mock_log.assert_called_once_with(
                "agent_cleanup",
                agent="invoice_assistant",
                total_requests=5,
                total_tokens=1500,
                total_cost_usd=0.075,
                total_errors=1,
            )
