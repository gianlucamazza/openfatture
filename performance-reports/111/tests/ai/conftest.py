"""AI-specific test fixtures and configuration."""

import asyncio
from collections.abc import Generator
from typing import Any

import pytest
import pytest_asyncio

from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.storage.database.base import Base


@pytest.fixture(scope="function", autouse=True)
def init_test_database() -> Generator[None, None, None]:
    """Initialize test database for AI tests.

    This fixture automatically initializes an in-memory SQLite database
    for all AI tests that need database access (like feedback tests).
    """
    import openfatture.storage.database.base as db_base
    from openfatture.storage.database.base import init_db

    # Initialize database with in-memory SQLite
    init_db("sqlite:///:memory:")

    yield

    # Cleanup
    if db_base.engine:
        Base.metadata.drop_all(db_base.engine)
        db_base.engine.dispose()
        db_base.engine = None
        db_base.SessionLocal = None


@pytest.fixture(scope="session")
def openai_api_available():
    """Check if OpenAI API key is configured."""
    from openfatture.ai.config import get_ai_settings

    settings = get_ai_settings()
    return bool(settings.openai_api_key and settings.openai_api_key.get_secret_value())


@pytest.fixture(scope="session")
def anthropic_api_available():
    """Check if Anthropic API key is configured."""
    from openfatture.ai.config import get_ai_settings

    settings = get_ai_settings()
    return bool(settings.anthropic_api_key and settings.anthropic_api_key.get_secret_value())


@pytest.fixture(scope="session")
def ollama_available():
    """Check if Ollama service is available."""
    try:
        import httpx

        response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


@pytest_asyncio.fixture(scope="session")
async def openai_provider(openai_api_available):
    """Real OpenAI provider for E2E tests."""
    if not openai_api_available:
        pytest.skip("OpenAI API key not configured (set OPENFATTURE_AI_OPENAI_API_KEY)")

    from openfatture.ai.providers.factory import create_provider

    provider = create_provider("openai")

    # Health check with timeout
    try:
        healthy = await asyncio.wait_for(provider.health_check(), timeout=10.0)
        if not healthy:
            pytest.skip("OpenAI provider health check failed")
    except TimeoutError:
        pytest.skip("OpenAI provider health check timeout")
    except Exception as e:
        pytest.skip(f"OpenAI provider initialization failed: {e}")

    return provider


@pytest_asyncio.fixture(scope="session")
async def anthropic_provider(anthropic_api_available):
    """Real Anthropic provider for E2E tests."""
    if not anthropic_api_available:
        pytest.skip("Anthropic API key not configured (set OPENFATTURE_AI_ANTHROPIC_API_KEY)")

    from openfatture.ai.providers.factory import create_provider

    provider = create_provider("anthropic")

    # Health check with timeout
    try:
        healthy = await asyncio.wait_for(provider.health_check(), timeout=10.0)
        if not healthy:
            pytest.skip("Anthropic provider health check failed")
    except TimeoutError:
        pytest.skip("Anthropic provider health check timeout")
    except Exception as e:
        pytest.skip(f"Anthropic provider initialization failed: {e}")

    return provider


@pytest_asyncio.fixture(scope="session")
async def ollama_provider(ollama_available):
    """Real Ollama provider for E2E tests."""
    if not ollama_available:
        pytest.skip("Ollama service not available at localhost:11434")

    from openfatture.ai.providers.factory import create_provider

    provider = create_provider("ollama")

    # Health check with timeout
    try:
        healthy = await asyncio.wait_for(provider.health_check(), timeout=5.0)
        if not healthy:
            pytest.skip("Ollama provider health check failed")
    except TimeoutError:
        pytest.skip("Ollama provider health check timeout")
    except Exception as e:
        pytest.skip(f"Ollama provider initialization failed: {e}")

    return provider


@pytest.fixture
def mock_provider():
    """Create a mock LLM provider for unit tests."""
    from unittest.mock import AsyncMock, MagicMock

    provider = MagicMock(spec=BaseLLMProvider)
    provider.provider_name = "mock"
    provider.model = "mock-model"
    provider.generate = AsyncMock()
    provider.stream = AsyncMock()
    provider.stream_structured = AsyncMock()
    provider.count_tokens = MagicMock(return_value=10)
    provider.estimate_cost = MagicMock(return_value=0.001)
    provider.health_check = AsyncMock(return_value=True)
    provider.supports_streaming = True
    provider.supports_tools = True
    return provider


@pytest.fixture
def mock_provider_with_response():
    """Create a mock provider that returns a predefined response."""
    from unittest.mock import AsyncMock, MagicMock

    provider = MagicMock(spec=BaseLLMProvider)
    provider.provider_name = "mock"
    provider.model = "mock-model"

    # Mock response
    from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics

    mock_response = AgentResponse(
        content='{"descrizione_completa": "Consulenza informatica", "deliverables": ["Analisi", "Implementazione"], "competenze": ["Python", "SQL"]}',
        status=ResponseStatus.SUCCESS,
        usage=UsageMetrics(prompt_tokens=50, completion_tokens=100, total_tokens=150),
        metadata={"model": "mock-model", "temperature": 0.7},
    )

    provider.generate = AsyncMock(return_value=mock_response)
    provider.stream = AsyncMock()
    provider.stream_structured = AsyncMock()
    provider.count_tokens = MagicMock(return_value=10)
    provider.estimate_cost = MagicMock(return_value=0.001)
    provider.health_check = AsyncMock(return_value=True)
    provider.supports_streaming = True
    provider.supports_tools = True
    return provider


def validate_json_response(content: str) -> dict[str, Any] | None:
    """Validate and parse JSON response from LLM."""
    import json

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
