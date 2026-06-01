"""Tests for the invoice creation wizard in the Web UI.

The service-layer tests exercise the real Streamlit service adapters
(``openfatture.web.services.*``) against a real, isolated database wired into
the global session factory via the ``runtime_db`` / ``runtime_session``
fixtures (see ``tests/conftest.py``). Data is seeded through the same database
the services read/write, so assertions are made on real results instead of
mocked SQLAlchemy query chains. AI and Streamlit collaborators stay mocked.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from openfatture.payment.domain.models import BankAccount
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    StatoFattura,
    TipoDocumento,
)
from openfatture.web.services.client_service import StreamlitClientService
from openfatture.web.services.invoice_service import StreamlitInvoiceService
from openfatture.web.services.payment_service import StreamlitPaymentService


@pytest.fixture(autouse=True)
def _reset_web_db_session():
    """Drop any Streamlit-cached DB session between tests.

    ``get_db_session()`` memoises a session in ``st.session_state``, which is a
    process-wide proxy in bare (non-``streamlit run``) mode. Without this reset
    a session bound to a previous test's (torn-down) ``runtime_db`` would leak
    into the next test, so each service test must start from a clean slate.
    """
    from openfatture.web.utils.cache import clear_db_session

    clear_db_session()
    yield
    clear_db_session()


def _seed_cliente(session, denominazione="Test Client") -> Cliente:
    """Persist a client into the runtime database and return it."""
    cliente = Cliente(
        denominazione=denominazione,
        partita_iva="12345678901",
        codice_destinatario="ABC1234",
        nazione="IT",
    )
    session.add(cliente)
    session.commit()
    session.refresh(cliente)
    return cliente


def _seed_fattura(session, cliente: Cliente, *, numero="001", anno=2024) -> Fattura:
    """Persist a sendable invoice (with a client) into the runtime database."""
    fattura = Fattura(
        numero=numero,
        anno=anno,
        data_emissione=date(anno, 1, 15),
        cliente_id=cliente.id,
        tipo_documento=TipoDocumento.TD01,
        stato=StatoFattura.INVIATA,
        imponibile=Decimal("100.00"),
        iva=Decimal("22.00"),
        totale=Decimal("122.00"),
    )
    session.add(fattura)
    session.commit()
    session.refresh(fattura)
    return fattura


class TestInvoiceCreationWizard:
    """Test the invoice creation wizard functionality."""

    def test_wizard_state_initialization(self):
        """Test that wizard state initializes correctly."""
        # Test the wizard state structure
        wizard_state = {"current_step": 1, "data": {}}
        assert wizard_state["current_step"] == 1
        assert wizard_state["data"] == {}

    def test_step_validation_logic(self):
        """Test step validation logic."""
        # Test step 1 without client selected
        wizard_state: dict = {"current_step": 1}
        has_client = "selected_client" in wizard_state
        assert not has_client

        # Test step 1 with client selected
        wizard_state["selected_client"] = {"id": 1, "denominazione": "Test Client"}
        has_client = "selected_client" in wizard_state
        assert has_client

        # Test step 2 with valid details
        wizard_state["invoice_details"] = {
            "numero": "001",
            "anno": 2024,
            "data_emissione": date(2024, 1, 1),
            "data_scadenza": date(2024, 2, 1),
            "oggetto": "Test invoice",
            "note": "Test notes",
        }
        has_details = "invoice_details" in wizard_state
        assert has_details

        # Test step 3 without products
        wizard_state["line_items"] = []
        has_products = len(wizard_state.get("line_items", [])) > 0
        assert not has_products

        # Test step 3 with products
        wizard_state["line_items"] = [
            {
                "descrizione": "Test product",
                "quantita": 1.0,
                "prezzo_unitario": 100.0,
                "aliquota_iva": 22,
            }
        ]
        has_products = len(wizard_state.get("line_items", [])) > 0
        assert has_products

    def test_invoice_creation_service(self, runtime_session):
        """Test the invoice creation service against a real database.

        Seeds a real client, creates an invoice through the real service (which
        opens its own session via ``db_session_scope``/``get_db_session`` on the
        runtime database), and asserts on the persisted result.
        """
        cliente = _seed_cliente(runtime_session)

        service = StreamlitInvoiceService()
        result = service.create_invoice(
            cliente_id=cliente.id,
            numero="001",
            anno=2024,
            data_emissione=date(2024, 1, 1),
            righe_data=[
                {
                    "descrizione": "Test",
                    "quantita": 1.0,
                    "prezzo_unitario": 100.0,
                    "aliquota_iva": 22,
                }
            ],
        )

        # The service returns a real, persisted Fattura.
        assert result is not None
        assert result.numero == "001"
        assert result.anno == 2024
        assert result.cliente_id == cliente.id
        assert result.totale == Decimal("122.00")

        # Verify it was actually written to the database.
        stored = runtime_session.query(Fattura).filter(Fattura.id == result.id).first()
        assert stored is not None
        assert len(stored.righe) == 1
        assert stored.righe[0].descrizione == "Test"

    def test_client_service(self, runtime_session):
        """Test the client service against a real database.

        Seeds real clients and asserts ``get_clients`` returns them as
        serialised dictionaries from the runtime database.
        """
        _seed_cliente(runtime_session, denominazione="Test Client")

        service = StreamlitClientService()
        clients = service.get_clients()

        assert len(clients) == 1
        assert clients[0]["denominazione"] == "Test Client"
        assert clients[0]["partita_iva"] == "12345678901"

    @patch("openfatture.web.services.ai_service.get_ai_service")
    def test_ai_service_integration(self, mock_get_service):
        """Test AI service integration."""
        # Mock the AI service
        mock_ai_service = Mock()
        mock_get_service.return_value = mock_ai_service

        # Mock AI response
        mock_response = Mock()
        mock_response.content = "Descrizione professionale del servizio"
        mock_ai_service.generate_invoice_description.return_value = mock_response

        # Test the integration
        from openfatture.web.services.ai_service import get_ai_service

        service = get_ai_service()
        result = service.generate_invoice_description("Test input")

        assert result.content == "Descrizione professionale del servizio"
        mock_ai_service.generate_invoice_description.assert_called_once_with("Test input")


class TestPaymentService:
    """Test the payment service functionality."""

    def test_payment_import(self, runtime_session, tmp_path):
        """Test payment import against a real database.

        Seeds a real bank account, provides a real CSV statement file, and runs
        the import through the real service so persistence hits the runtime
        database. Only the uploaded-file boundary is provided via ``tmp_path``.
        """
        account = BankAccount(
            name="Test Account",
            iban="IT60X0542811101000000123456",
            bank_name="Test Bank",
            currency="EUR",
            opening_balance=Decimal("0.00"),
        )
        runtime_session.add(account)
        runtime_session.commit()
        runtime_session.refresh(account)
        account_id = account.id

        # Minimal CSV matching the default importer field mapping
        # (Date / Amount / Description / Reference).
        csv_content = (
            "Date,Amount,Description,Reference\n"
            "2024-01-05,100.00,Bonifico cliente A,REF001\n"
            "2024-01-06,250.50,Bonifico cliente B,REF002\n"
            "2024-01-07,75.00,Bonifico cliente C,REF003\n"
        )
        file_content = csv_content.encode("utf-8")

        service = StreamlitPaymentService()
        result = service.import_bank_statement(
            account_id=account_id,
            file_content=file_content,
            filename="test.csv",
        )

        assert result["success"] is True
        assert result["transactions_imported"] == 3
        assert "3 transactions" in result["message"]

    def test_payment_matching(self, runtime_session):
        """Test payment matching against a real database.

        Seeds real sendable invoices so ``get_potential_matches`` returns real
        candidates with confidence scores from the runtime database.
        """
        cliente = _seed_cliente(runtime_session, denominazione="Test Client")
        fattura = _seed_fattura(runtime_session, cliente, numero="001", anno=2024)

        service = StreamlitPaymentService()
        matches = service.get_potential_matches(123)

        assert len(matches) == 1
        assert matches[0]["id"] == fattura.id
        assert matches[0]["numero"] == "001"
        assert matches[0]["cliente"] == "Test Client"
        assert matches[0]["totale"] == 122.0
        assert matches[0]["confidence"] == 0.5
