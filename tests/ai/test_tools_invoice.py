"""Unit tests for invoice tools.

Tests focus on individual tool functions in isolation using mocks
to avoid external database and network dependencies.
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from openfatture.ai.tools.invoice_tools import (
    get_invoice_details,
    get_invoice_stats,
    search_invoices,
)
from openfatture.storage.database.models import Fattura, StatoFattura


class TestSearchInvoices:
    """Test search_invoices tool function."""

    @patch("openfatture.ai.tools.invoice_tools.get_session")
    def test_search_invoices_basic(self, mock_get_session):
        """Test basic invoice search without filters."""
        # Mock database session
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Mock query results
        mock_fattura = MagicMock(spec=Fattura)
        mock_fattura.id = 1
        mock_fattura.numero = "001"
        mock_fattura.anno = 2025
        mock_fattura.data_emissione.isoformat.return_value = "2025-01-15"
        mock_fattura.totale = 1000.0
        mock_fattura.stato = StatoFattura.DA_INVIARE
        mock_fattura.note = "Test invoice"

        mock_cliente = MagicMock()
        mock_cliente.denominazione = "Test Client"
        mock_fattura.cliente = mock_cliente

        # Mock query chain
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_fattura]

        # Execute function
        result = search_invoices()

        # Verify result structure
        assert "count" in result
        assert "fatture" in result
        assert "has_more" in result
        assert result["count"] == 1
        assert len(result["fatture"]) == 1
        assert result["fatture"][0]["numero"] == "001"
        assert result["fatture"][0]["cliente"] == "Test Client"

        # Verify database calls
        mock_session.query.assert_called_once_with(Fattura)
        mock_session.close.assert_called_once()

    @patch("openfatture.ai.tools.invoice_tools.get_session")
    def test_search_invoices_with_query(self, mock_get_session):
        """Test invoice search with text query."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Mock empty results
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        # Execute with query
        result = search_invoices(query="test search")

        # Verify query filtering was applied
        assert mock_query.filter.call_count >= 1
        assert result["count"] == 0

    @patch("openfatture.ai.tools.invoice_tools.get_session")
    def test_search_invoices_with_year_filter(self, mock_get_session):
        """Test invoice search filtered by year."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = search_invoices(anno=2024)

        # Verify year filter was applied
        assert mock_query.filter.call_count >= 1
        assert result["count"] == 0

    @patch("openfatture.ai.tools.invoice_tools.get_session")
    def test_search_invoices_with_status_filter(self, mock_get_session):
        """Test invoice search filtered by status."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = search_invoices(stato="da_inviare")

        # Verify status filter was applied
        assert mock_query.filter.call_count >= 1
        assert result["count"] == 0

    @patch("openfatture.ai.tools.invoice_tools.get_session")
    def test_search_invoices_database_error(self, mock_get_session):
        """Test invoice search with database error."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.side_effect = Exception("Database connection failed")
        mock_get_session.return_value = mock_session

        result = search_invoices()

        # Should return error result
        assert "error" in result
        assert result["error"] == "Database connection failed"
        assert result["count"] == 0

        mock_session.close.assert_called_once()

    def test_search_invoices_input_validation(self):
        """Test input validation for search parameters."""
        from openfatture.utils.security import validate_integer_input

        # Test valid inputs
        assert validate_integer_input(2025, min_value=2000, max_value=2100) == 2025
        assert validate_integer_input(1, min_value=1) == 1

        # Test invalid inputs
        with pytest.raises(ValueError):
            validate_integer_input(1999, min_value=2000)  # Too low

        with pytest.raises(ValueError):
            validate_integer_input(2101, max_value=2100)  # Too high

        with pytest.raises(ValueError):
            validate_integer_input("not_a_number")  # Not an integer


class TestGetInvoiceDetails:
    """Test get_invoice_details tool function."""

    @patch("openfatture.ai.tools.invoice_tools.get_session")
    def test_get_invoice_details_success(self, mock_get_session):
        """Test successful invoice details retrieval."""
        # Mock database session
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Mock invoice with relationships
        mock_fattura = MagicMock(spec=Fattura)
        mock_fattura.id = 123
        mock_fattura.numero = "001"
        mock_fattura.anno = 2025
        mock_fattura.data_emissione.isoformat.return_value = "2025-01-15"
        mock_fattura.imponibile = 800.0
        mock_fattura.iva = 200.0
        mock_fattura.totale = 1000.0
        mock_fattura.stato = StatoFattura.DA_INVIARE
        mock_fattura.note = "Test invoice"

        # Mock client
        mock_cliente = MagicMock()
        mock_cliente.id = 456
        mock_cliente.denominazione = "Test Client Srl"
        mock_cliente.partita_iva = "12345678901"
        mock_fattura.cliente = mock_cliente

        # Mock invoice lines
        mock_riga = MagicMock()
        mock_riga.descrizione = "Consulting service"
        mock_riga.quantita = 10.0
        mock_riga.prezzo_unitario = 100.0
        mock_riga.aliquota_iva = 22.0
        mock_fattura.righe = [mock_riga]

        # Mock query
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_fattura

        # Execute function
        result = get_invoice_details(fattura_id=123)

        # Verify result structure
        assert "id" in result
        assert "numero" in result
        assert "cliente" in result
        assert "importi" in result
        assert "righe" in result

        assert result["id"] == 123
        assert result["numero"] == "001"
        assert result["cliente"]["denominazione"] == "Test Client Srl"
        assert result["importi"]["totale"] == 1000.0
        assert len(result["righe"]) == 1

        mock_session.close.assert_called_once()

    @patch("openfatture.ai.tools.invoice_tools.get_session")
    def test_get_invoice_details_not_found(self, mock_get_session):
        """Test invoice details for non-existent invoice."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Mock query returning None
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = get_invoice_details(fattura_id=999)

        assert "error" in result
        assert "Fattura 999 non trovata" in result["error"]

    @patch("openfatture.ai.tools.invoice_tools.get_session")
    def test_get_invoice_details_no_client(self, mock_get_session):
        """Test invoice details when invoice has no associated client."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Mock invoice without client
        mock_fattura = MagicMock(spec=Fattura)
        mock_fattura.id = 123
        mock_fattura.cliente = None

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_fattura

        result = get_invoice_details(fattura_id=123)

        assert "error" in result
        assert "has no associated cliente" in result["error"]

    def test_get_invoice_details_input_validation(self):
        """Test input validation for invoice ID."""
        from openfatture.utils.security import validate_integer_input

        # Valid input
        assert validate_integer_input(123, min_value=1) == 123

        # Invalid inputs
        with pytest.raises(ValueError):
            validate_integer_input(0, min_value=1)  # Too low

        with pytest.raises(ValueError):
            validate_integer_input("not_a_number")  # Not an integer


class TestGetInvoiceStats:
    """Test get_invoice_stats tool function."""

    @patch("openfatture.ai.tools.invoice_tools.get_session")
    def test_get_invoice_stats_success(self, mock_get_session):
        """Test successful invoice statistics retrieval."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Mock query chain - need separate mocks for different filter calls
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query

        # Create separate filter mocks for status counts and total calculation
        mock_filter_status = MagicMock()
        mock_filter_total = MagicMock()

        # Make filter return different mocks based on call pattern
        # For status counts: filter is called with anno and stato
        # For total: filter is called with just anno
        filter_call_count = 0

        def filter_side_effect(*args, **kwargs):
            nonlocal filter_call_count
            filter_call_count += 1
            # First 8 calls are for status counts, 9th is for total
            if filter_call_count <= 8:
                return mock_filter_status
            else:
                return mock_filter_total

        mock_query.filter.side_effect = filter_side_effect

        # Mock count calls for each status (8 statuses)
        mock_filter_status.count.side_effect = [
            5,  # BOZZA
            3,  # DA_INVIARE
            2,  # INVIATA
            1,  # CONSEGNATA
            0,  # ACCETTATA
            0,  # RIFIUTATA
            0,  # SCARTATA
            0,  # ERRORE
        ]

        # Mock total calculation query
        mock_fattura1 = MagicMock()
        mock_fattura1.totale = 1000.0
        mock_fattura2 = MagicMock()
        mock_fattura2.totale = 2000.0
        mock_filter_total.all.return_value = [
            mock_fattura1,
            mock_fattura2,
        ]

        result = get_invoice_stats(anno=2025)

        assert "anno" in result
        assert "totale_fatture" in result
        assert "per_stato" in result
        assert "importo_totale" in result

        assert result["anno"] == 2025
        assert result["totale_fatture"] == 11  # Sum of all statuses
        assert result["per_stato"]["bozza"] == 5
        assert result["per_stato"]["da_inviare"] == 3
        assert result["importo_totale"] == 3000.0

    @patch("openfatture.ai.tools.invoice_tools.get_session")
    def test_get_invoice_stats_current_year(self, mock_get_session):
        """Test invoice stats for current year when no year specified."""
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session

        # Mock query chain - need separate mocks for different filter calls
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query

        # Create separate filter mocks for status counts and total calculation
        mock_filter_status = MagicMock()
        mock_filter_total = MagicMock()

        # Make filter return different mocks based on call pattern
        filter_call_count = 0

        def filter_side_effect(*args, **kwargs):
            nonlocal filter_call_count
            filter_call_count += 1
            # First 8 calls are for status counts, 9th is for total
            if filter_call_count <= 8:
                return mock_filter_status
            else:
                return mock_filter_total

        mock_query.filter.side_effect = filter_side_effect

        # Mock count calls for each status (8 statuses, all zero)
        mock_filter_status.count.side_effect = [0] * 8

        # Mock total calculation query (empty)
        mock_filter_total.all.return_value = []

        result = get_invoice_stats()  # No year specified

        assert "anno" in result
        # Should use current year (mocked datetime would be needed for full test)

    @patch("openfatture.ai.tools.invoice_tools.get_session")
    def test_get_invoice_stats_database_error(self, mock_get_session):
        """Test invoice stats with database error."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.side_effect = Exception("Database error")
        mock_get_session.return_value = mock_session

        result = get_invoice_stats()

        assert "error" in result
        assert result["error"] == "Database error"

    def test_get_invoice_stats_input_validation(self):
        """Test input validation for year parameter."""
        from openfatture.utils.security import validate_integer_input

        # Valid input
        assert validate_integer_input(2025, min_value=2000, max_value=2100) == 2025

        # Invalid inputs
        with pytest.raises(ValueError):
            validate_integer_input(1999, min_value=2000)  # Too low

        with pytest.raises(ValueError):
            validate_integer_input(2101, max_value=2100)  # Too high
