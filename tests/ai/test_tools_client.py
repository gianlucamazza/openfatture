"""Tests for client tools.

Tests focus on individual tool functions in isolation using mocks
to avoid external database and network dependencies.
"""

from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from openfatture.ai.tools.client_tools import (
    get_client_details,
    get_client_stats,
    search_clients,
)
from openfatture.storage.database.models import Cliente


class TestSearchClients:
    """Test search_clients tool function."""

    @patch("openfatture.ai.tools.client_tools.get_session")
    def test_search_clients_basic(self, mock_get_session):
        """Test basic client search without filters."""
        # Mock database session
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Mock query results
        mock_cliente = MagicMock(spec=Cliente)
        mock_cliente.id = 1
        mock_cliente.denominazione = "Test Client SRL"
        mock_cliente.partita_iva = "12345678901"
        mock_cliente.codice_fiscale = "TSTCLN85M01H501Z"
        mock_cliente.email = "test@example.com"
        mock_cliente.fatture = [MagicMock(), MagicMock()]  # 2 invoices

        # Mock query chain
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_cliente]

        result = search_clients()

        assert result["count"] == 1
        assert len(result["clienti"]) == 1
        assert result["clienti"][0]["id"] == 1
        assert result["clienti"][0]["denominazione"] == "Test Client SRL"
        assert result["clienti"][0]["partita_iva"] == "12345678901"
        assert result["clienti"][0]["codice_fiscale"] == "TSTCLN85M01H501Z"
        assert result["clienti"][0]["email"] == "test@example.com"
        assert result["clienti"][0]["fatture_count"] == 2
        assert result["has_more"] is False

    @patch("openfatture.ai.tools.client_tools.get_session")
    def test_search_clients_with_query(self, mock_get_session):
        """Test client search with query filter."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        mock_cliente = MagicMock(spec=Cliente)
        mock_cliente.id = 2
        mock_cliente.denominazione = "Rossi Company"
        mock_cliente.partita_iva = "09876543210"
        mock_cliente.codice_fiscale = "RSSCMP80A01F205X"
        mock_cliente.email = "rossi@example.com"
        mock_cliente.fatture = []

        # Mock query chain
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_cliente]

        result = search_clients(query="rossi")

        assert result["count"] == 1
        assert result["clienti"][0]["denominazione"] == "Rossi Company"

    @patch("openfatture.ai.tools.client_tools.get_session")
    def test_search_clients_with_limit(self, mock_get_session):
        """Test client search with custom limit."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Create multiple mock clients
        mock_clienti = []
        for i in range(5):
            mock_cliente = MagicMock(spec=Cliente)
            mock_cliente.id = i + 1
            mock_cliente.denominazione = f"Client {i + 1}"
            mock_cliente.partita_iva = f"1234567890{i}"
            mock_cliente.codice_fiscale = f"TSTCLN85M01H50{i}Z"
            mock_cliente.email = f"client{i}@example.com"
            mock_cliente.fatture = []
            mock_clienti.append(mock_cliente)

        # Mock query chain
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_clienti[:3]  # Return only 3, indicating limit was hit

        result = search_clients(limit=3)

        assert result["count"] == 3
        assert len(result["clienti"]) == 3
        assert result["has_more"] is True  # Should indicate more results available

    @patch("openfatture.ai.tools.client_tools.get_session")
    def test_search_clients_empty_results(self, mock_get_session):
        """Test client search with no results."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Mock query chain
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = search_clients(query="nonexistent")

        assert result["count"] == 0
        assert result["clienti"] == []
        assert result["has_more"] is False

    @patch("openfatture.ai.tools.client_tools.get_session")
    def test_search_clients_database_error(self, mock_get_session):
        """Test client search with database error."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Mock query to raise exception
        mock_session.query.side_effect = Exception("Database connection failed")

        result = search_clients()

        assert "error" in result
        assert result["count"] == 0
        assert result["clienti"] == []


class TestGetClientDetails:
    """Test get_client_details tool function."""

    @patch("openfatture.ai.tools.client_tools.get_session")
    def test_get_client_details_success(self, mock_get_session):
        """Test successful client details retrieval."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Mock client
        mock_cliente = MagicMock(spec=Cliente)
        mock_cliente.id = 1
        mock_cliente.denominazione = "Test Client SRL"
        mock_cliente.partita_iva = "12345678901"
        mock_cliente.codice_fiscale = "TSTCLN85M01H501Z"
        mock_cliente.indirizzo = "Via Roma 123"
        mock_cliente.cap = "00100"
        mock_cliente.comune = "Roma"
        mock_cliente.provincia = "RM"
        mock_cliente.nazione = "IT"
        mock_cliente.email = "test@example.com"
        mock_cliente.pec = "test@pec.example.com"
        mock_cliente.telefono = "+39 06 1234567"

        # Mock invoices with proper date objects
        from datetime import date

        mock_fattura1 = MagicMock()
        mock_fattura1.id = 1
        mock_fattura1.numero = "001"
        mock_fattura1.anno = 2025
        mock_fattura1.data_emissione = date(2025, 1, 15)
        mock_fattura1.totale = 1000.0
        mock_fattura1.stato.value = "CONSEGNATA"

        mock_fattura2 = MagicMock()
        mock_fattura2.id = 2
        mock_fattura2.numero = "002"
        mock_fattura2.anno = 2025
        mock_fattura2.data_emissione = date(2025, 2, 1)
        mock_fattura2.totale = 2000.0
        mock_fattura2.stato.value = "INVIATA"

        mock_cliente.fatture = [mock_fattura1, mock_fattura2]

        # Mock query chain
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_cliente

        result = get_client_details(cliente_id=1)

        assert result["id"] == 1
        assert result["denominazione"] == "Test Client SRL"
        assert result["partita_iva"] == "12345678901"
        assert result["codice_fiscale"] == "TSTCLN85M01H501Z"
        assert result["indirizzo"]["via"] == "Via Roma 123"
        assert result["indirizzo"]["comune"] == "Roma"
        assert result["contatti"]["email"] == "test@example.com"
        assert result["contatti"]["pec"] == "test@pec.example.com"
        assert result["fatture_count"] == 2
        assert len(result["fatture_recenti"]) == 2
        assert result["fatture_recenti"][0]["numero"] == "002"  # Most recent first

    @patch("openfatture.ai.tools.client_tools.get_session")
    def test_get_client_details_not_found(self, mock_get_session):
        """Test client details retrieval for non-existent client."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Mock query chain returning None
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = get_client_details(cliente_id=999)

        assert "error" in result
        assert "non trovato" in result["error"]

    @patch("openfatture.ai.tools.client_tools.get_session")
    def test_get_client_details_database_error(self, mock_get_session):
        """Test client details retrieval with database error."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Mock query to raise exception
        mock_session.query.side_effect = Exception("Database connection failed")

        result = get_client_details(cliente_id=1)

        assert "error" in result
        assert "Database connection failed" in result["error"]

    @patch("openfatture.ai.tools.client_tools.get_session")
    def test_get_client_details_no_invoices(self, mock_get_session):
        """Test client details retrieval for client with no invoices."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Mock client with no invoices
        mock_cliente = MagicMock(spec=Cliente)
        mock_cliente.id = 1
        mock_cliente.denominazione = "New Client"
        mock_cliente.partita_iva = None
        mock_cliente.codice_fiscale = None
        mock_cliente.indirizzo = None
        mock_cliente.cap = None
        mock_cliente.comune = None
        mock_cliente.provincia = None
        mock_cliente.nazione = None
        mock_cliente.email = None
        mock_cliente.pec = None
        mock_cliente.telefono = None
        mock_cliente.fatture = []

        # Mock query chain
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_cliente

        result = get_client_details(cliente_id=1)

        assert result["id"] == 1
        assert result["denominazione"] == "New Client"
        assert result["partita_iva"] == ""
        assert result["codice_fiscale"] == ""
        assert result["indirizzo"]["via"] == ""
        assert result["contatti"]["email"] == ""
        assert result["fatture_count"] == 0
        assert result["fatture_recenti"] == []


class TestGetClientStats:
    """Test get_client_stats tool function."""

    @patch("openfatture.ai.tools.client_tools.get_session")
    def test_get_client_stats_success(self, mock_get_session):
        """Test successful client statistics retrieval."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Mock query results for different counts
        mock_session.query.return_value.count.side_effect = [100, 80, 60, 20]
        mock_session.query.return_value.filter.return_value.count.side_effect = [80, 60, 20]

        result = get_client_stats()

        assert result["totale_clienti"] == 100
        assert result["con_partita_iva"] == 80
        assert result["con_email"] == 60
        assert result["con_pec"] == 20

    @patch("openfatture.ai.tools.client_tools.get_session")
    def test_get_client_stats_database_error(self, mock_get_session):
        """Test client statistics retrieval with database error."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Mock query to raise exception
        mock_session.query.side_effect = Exception("Database connection failed")

        result = get_client_stats()

        assert "error" in result
        assert "Database connection failed" in result["error"]
