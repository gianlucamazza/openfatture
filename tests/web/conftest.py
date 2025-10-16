"""Pytest fixtures for web module tests.

Provides:
- Mock Streamlit session_state
- Mock database sessions
- Mock AI providers
- Sample test data
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, Mock

import pytest


@pytest.fixture
def mock_streamlit_session():
    """Mock Streamlit session_state for testing."""
    session_state = {}

    class MockSessionState:
        def __getitem__(self, key):
            return session_state[key]

        def __setitem__(self, key, value):
            session_state[key] = value

        def __contains__(self, key):
            return key in session_state

        def __delitem__(self, key):
            del session_state[key]

        def get(self, key, default=None):
            return session_state.get(key, default)

        def keys(self):
            return session_state.keys()

    return MockSessionState()


@pytest.fixture
def mock_db_session():
    """Mock SQLAlchemy database session for testing."""
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.order_by.return_value = session
    session.limit.return_value = session
    session.all.return_value = []
    session.first.return_value = None
    session.count.return_value = 0
    return session


@pytest.fixture
def sample_invoice_data():
    """Sample invoice data for testing."""
    return {
        "id": 1,
        "numero": "001",
        "anno": 2024,
        "data_emissione": date(2024, 1, 15),
        "cliente_id": 1,
        "imponibile": Decimal("1000.00"),
        "iva": Decimal("220.00"),
        "totale": Decimal("1220.00"),
        "stato": "BOZZA",
    }


@pytest.fixture
def sample_righe_data():
    """Sample invoice line items for testing."""
    return [
        {
            "descrizione": "Consulenza sviluppo software",
            "quantita": 10,
            "prezzo_unitario": 100.0,
            "aliquota_iva": 22,
        },
        {
            "descrizione": "Manutenzione sistema",
            "quantita": 5,
            "prezzo_unitario": 50.0,
            "aliquota_iva": 22,
        },
    ]


@pytest.fixture
def sample_cliente():
    """Sample client for testing."""
    cliente = Mock()
    cliente.id = 1
    cliente.denominazione = "Test Client SRL"
    cliente.partita_iva = "IT12345678901"
    cliente.codice_fiscale = "12345678901"
    return cliente


@pytest.fixture
def mock_ai_provider():
    """Mock AI provider for testing."""
    provider = MagicMock()

    # Mock generate method
    async def mock_generate(*args, **kwargs):
        return {
            "content": "Test AI response",
            "usage": {"total_tokens": 100, "estimated_cost_usd": 0.001},
        }

    provider.generate.side_effect = mock_generate

    # Mock stream method
    async def mock_stream(*args, **kwargs):
        yield "Test "
        yield "streamed "
        yield "response"

    provider.stream.return_value = mock_stream()

    return provider


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = Mock()
    settings.cedente_partita_iva = "IT98765432109"
    settings.cedente_denominazione = "Test Company"
    settings.cedente_regime_fiscale = "RF01"
    settings.ai_provider = "openai"
    settings.ai_model = "gpt-4"
    settings.ai_api_key = "test-key"
    settings.ai_chat_enabled = True
    settings.database_url = "sqlite:///:memory:"
    settings.debug_config.enabled = False
    return settings
