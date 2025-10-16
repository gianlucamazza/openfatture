"""
Unit tests for fattura CLI command functions.

Tests the actual command logic with proper mocking of dependencies.
"""

from unittest.mock import MagicMock, patch

import pytest

from openfatture.cli.commands.fattura import (
    crea_fattura,
    genera_xml,
    list_fatture,
)


class TestListFattureFunction:
    """Test list_fatture function directly."""

    @patch("openfatture.cli.commands.fattura._get_session")
    @patch("openfatture.cli.commands.fattura.ensure_db")
    def test_list_fatture_empty(self, mock_ensure_db, mock_get_session):
        """Test listing when no invoices exist."""
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

        with patch("openfatture.cli.commands.fattura.console") as mock_console:
            list_fatture(stato=None, anno=None, limit=50)

            # Should print "No invoices found"
            mock_console.print.assert_called()

    @patch("openfatture.cli.commands.fattura._get_session")
    @patch("openfatture.cli.commands.fattura.ensure_db")
    def test_list_fatture_with_data(self, mock_ensure_db, mock_get_session, sample_fattura):
        """Test listing invoices with data."""
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db

        # Mock the query chain
        mock_query = mock_db.query.return_value.order_by.return_value
        mock_query.limit.return_value.all.return_value = [sample_fattura]

        with patch("openfatture.cli.commands.fattura.console") as mock_console:
            list_fatture(stato=None, anno=None, limit=50)

            # Should print table
            mock_console.print.assert_called()


class TestShowFatturaFunction:
    """Test show_fattura function directly."""

    @patch("openfatture.cli.commands.fattura.typer.Exit")
    @patch("openfatture.cli.commands.fattura._get_session")
    @patch("openfatture.cli.commands.fattura.ensure_db")
    def test_genera_xml_invoice_not_found(self, mock_ensure_db, mock_get_session, mock_exit):
        """Test XML generation for non-existent invoice."""
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_exit.side_effect = SystemExit(1)

        with patch("openfatture.cli.commands.fattura.console") as mock_console:
            with pytest.raises(SystemExit):
                genera_xml(999, output=None, no_validate=False)

            mock_console.print.assert_called()
            mock_exit.assert_called_once_with(1)


class TestCreaFatturaFunction:
    """Test crea_fattura function directly."""

    @patch("openfatture.cli.commands.fattura.typer.Exit")
    @patch("openfatture.cli.commands.fattura._get_session")
    @patch("openfatture.cli.commands.fattura.ensure_db")
    def test_crea_no_clients(self, mock_ensure_db, mock_get_session, mock_exit):
        """Test creating invoice when no clients exist."""
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db
        mock_db.query.return_value.order_by.return_value.all.return_value = []

        mock_exit.side_effect = SystemExit(1)

        with patch("openfatture.cli.commands.fattura.console") as mock_console:
            with pytest.raises(SystemExit):
                crea_fattura(None)

            mock_console.print.assert_called()
            mock_exit.assert_called_once_with(1)

    @patch("openfatture.cli.commands.fattura.typer.Exit")
    @patch("openfatture.cli.commands.fattura._get_session")
    @patch("openfatture.cli.commands.fattura.ensure_db")
    def test_crea_client_not_found(self, mock_ensure_db, mock_get_session, mock_exit):
        """Test creating invoice with non-existent client ID."""
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_exit.side_effect = SystemExit(1)

        with patch("openfatture.cli.commands.fattura.console") as mock_console:
            with pytest.raises(SystemExit):
                crea_fattura(999)

            mock_console.print.assert_called()
            mock_exit.assert_called_once_with(1)
