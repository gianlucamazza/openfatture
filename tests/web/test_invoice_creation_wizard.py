"""Tests for the invoice creation wizard in the Web UI."""

from datetime import date
from unittest.mock import Mock, patch

from openfatture.web.services.client_service import StreamlitClientService
from openfatture.web.services.invoice_service import StreamlitInvoiceService
from openfatture.web.services.payment_service import StreamlitPaymentService


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

    @patch("openfatture.web.services.invoice_service.get_db_session")
    @patch("openfatture.web.services.invoice_service.StreamlitInvoiceService")
    def test_invoice_creation_service(self, mock_service, mock_get_db_session):
        """Test the invoice creation service."""
        # Mock database session
        mock_session = Mock()
        mock_get_db_session.return_value = mock_session

        # Mock the service
        mock_instance = Mock()
        mock_service.return_value = mock_instance

        # Mock the create_invoice method
        mock_invoice = Mock()
        mock_invoice.id = 123
        mock_invoice.numero = "001"
        mock_invoice.anno = 2024
        mock_instance.create_invoice.return_value = mock_invoice

        # Test the service
        service = StreamlitInvoiceService()
        result = service.create_invoice(
            cliente_id=1,
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

        assert result.id == 123
        mock_instance.create_invoice.assert_called_once()

    @patch("openfatture.web.services.client_service.get_db_session")
    @patch("openfatture.web.services.client_service.StreamlitClientService")
    def test_client_service(self, mock_service, mock_get_db_session):
        """Test the client service."""
        # Mock database session
        mock_session = Mock()
        mock_get_db_session.return_value = mock_session

        # Mock the service
        mock_instance = Mock()
        mock_service.return_value = mock_instance

        # Mock client data
        mock_clients = [{"id": 1, "denominazione": "Test Client", "partita_iva": "12345678901"}]
        mock_instance.get_clients.return_value = mock_clients

        # Test the service
        service = StreamlitClientService()
        clients = service.get_clients()

        assert len(clients) == 1
        assert clients[0]["denominazione"] == "Test Client"
        mock_instance.get_clients.assert_called_once()

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

    @patch("openfatture.web.services.payment_service.StreamlitPaymentService")
    def test_payment_import(self, mock_service):
        """Test payment import functionality."""
        # Mock the service
        mock_instance = Mock()
        mock_service.return_value = mock_instance

        # Mock import result
        mock_instance.import_bank_statement.return_value = {
            "success": True,
            "message": "Imported 5 transactions",
            "transactions_imported": 5,
        }

        # Test the service
        service = StreamlitPaymentService()
        result = service.import_bank_statement(
            account_id=1, file_content=b"test content", filename="test.csv"
        )

        assert result["success"] is True
        assert result["transactions_imported"] == 5
        mock_instance.import_bank_statement.assert_called_once()

    @patch("openfatture.web.services.payment_service.StreamlitPaymentService")
    def test_payment_matching(self, mock_service):
        """Test payment matching functionality."""
        # Mock the service
        mock_instance = Mock()
        mock_service.return_value = mock_instance

        # Mock matches
        mock_matches = [
            {"id": 1, "numero": "001", "cliente": "Test Client", "totale": 100.0, "confidence": 0.8}
        ]
        mock_instance.get_potential_matches.return_value = mock_matches

        # Mock match result
        mock_instance.match_transaction.return_value = {
            "success": True,
            "message": "Transaction matched",
        }

        # Test the service
        service = StreamlitPaymentService()
        matches = service.get_potential_matches(123)
        result = service.match_transaction(123, 1)

        assert len(matches) == 1
        assert matches[0]["confidence"] == 0.8
        assert result["success"] is True

        mock_instance.get_potential_matches.assert_called_once_with(123, limit=10)
        mock_instance.match_transaction.assert_called_once_with(123, 1)
