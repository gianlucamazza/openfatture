"""
Unit tests for cliente CLI command functions.

Tests the actual command logic with proper mocking of dependencies.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from openfatture.cli.commands.cliente import (
    add_cliente,
    delete_cliente,
    list_clienti,
    show_cliente,
)


class TestListClientiFunction:
    """Test list_clienti function directly."""

    @patch("openfatture.cli.commands.cliente._get_session")
    @patch("openfatture.cli.commands.cliente.ensure_db")
    def test_list_clienti_empty(self, mock_ensure_db, mock_get_session):
        """Test listing when no clients exist."""
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db
        mock_db.query.return_value.order_by.return_value.all.return_value = []

        with patch("openfatture.cli.commands.cliente.console") as mock_console:
            list_clienti()

            mock_console.print.assert_called()

    @patch("openfatture.cli.commands.cliente._get_session")
    @patch("openfatture.cli.commands.cliente.ensure_db")
    def test_list_clienti_with_data(self, mock_ensure_db, mock_get_session, sample_cliente):
        """Test listing clients with data."""
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db
        mock_db.query.return_value.order_by.return_value.all.return_value = [sample_cliente]

        with patch("openfatture.cli.commands.cliente.console") as mock_console:
            list_clienti()

            mock_console.print.assert_called()


class TestShowClienteFunction:
    """Test show_cliente function directly."""

    @patch("openfatture.cli.commands.cliente.typer.Exit")
    @patch("openfatture.cli.commands.cliente._get_session")
    @patch("openfatture.cli.commands.cliente.ensure_db")
    def test_show_cliente_not_found(self, mock_ensure_db, mock_get_session, mock_exit):
        """Test showing non-existent client."""
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_exit.side_effect = SystemExit(1)

        with patch("openfatture.cli.commands.cliente.console") as mock_console:
            with pytest.raises(SystemExit):
                show_cliente(999)

            mock_console.print.assert_called()
            mock_exit.assert_called_once_with(1)

    @patch("openfatture.cli.commands.cliente._get_session")
    @patch("openfatture.cli.commands.cliente.ensure_db")
    def test_show_cliente_success(self, mock_ensure_db, mock_get_session, sample_cliente):
        """Test showing client details."""
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = sample_cliente

        with patch("openfatture.cli.commands.cliente.console") as mock_console:
            show_cliente(1)

            mock_console.print.assert_called()


class TestDeleteClienteFunction:
    """Test delete_cliente function directly."""

    @patch("openfatture.cli.commands.cliente.typer.Exit")
    @patch("openfatture.cli.commands.cliente._get_session")
    @patch("openfatture.cli.commands.cliente.ensure_db")
    def test_delete_cliente_not_found(self, mock_ensure_db, mock_get_session, mock_exit):
        """Test deleting non-existent client."""
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_exit.side_effect = SystemExit(1)

        with patch("openfatture.cli.commands.cliente.console") as mock_console:
            with pytest.raises(SystemExit):
                delete_cliente(999)

            mock_console.print.assert_called()
            mock_exit.assert_called_once_with(1)

    @patch("openfatture.cli.commands.cliente.Confirm.ask")
    @patch("openfatture.cli.commands.cliente._get_session")
    @patch("openfatture.cli.commands.cliente.ensure_db")
    def test_delete_cliente_with_invoices(self, mock_ensure_db, mock_get_session, mock_confirm_ask):
        """Test deleting client with existing invoices (should prompt and cancel)."""
        mock_cliente = Mock()
        mock_cliente.fatture = [Mock()]  # Mock that client has invoices

        mock_db = MagicMock()
        mock_get_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cliente

        mock_confirm_ask.return_value = False  # User cancels

        with patch("openfatture.cli.commands.cliente.console") as mock_console:
            delete_cliente(1)

            # Should not delete
            mock_db.delete.assert_not_called()
            mock_db.commit.assert_not_called()
            mock_console.print.assert_called()

    @patch("openfatture.cli.commands.cliente._get_session")
    @patch("openfatture.cli.commands.cliente.ensure_db")
    def test_delete_cliente_success(self, mock_ensure_db, mock_get_session, sample_cliente):
        """Test successful client deletion."""
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = sample_cliente
        # Mock that client has no invoices
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        with patch("openfatture.cli.commands.cliente.console") as mock_console:
            delete_cliente(1)

            mock_db.delete.assert_called_once_with(sample_cliente)
            mock_db.commit.assert_called_once()
            mock_console.print.assert_called()


class TestAddClienteFunction:
    """Test add_cliente function directly."""

    @patch("openfatture.cli.commands.cliente._get_session")
    @patch("openfatture.cli.commands.cliente.ensure_db")
    def test_add_cliente_basic(self, mock_ensure_db, mock_get_session):
        """Test adding client with basic information."""
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db

        # Mock successful client creation
        mock_cliente = Mock()
        mock_cliente.id = 1
        mock_cliente.denominazione = "Test Client"
        mock_db.refresh.return_value = mock_cliente

        with patch("openfatture.cli.commands.cliente.console") as mock_console:
            add_cliente(
                "Test Client",
                partita_iva="12345678901",
                codice_fiscale=None,
                codice_destinatario=None,
                pec=None,
                interactive=False,
            )

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_console.print.assert_called()

    @patch("openfatture.cli.commands.cliente.typer.Exit")
    @patch("openfatture.cli.commands.cliente._get_session")
    @patch("openfatture.cli.commands.cliente.ensure_db")
    def test_add_cliente_validation_error(self, mock_ensure_db, mock_get_session, mock_exit):
        """Test adding client with database error."""
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db

        mock_exit.side_effect = SystemExit(1)

        # Mock db.add to raise an exception
        mock_db.add.side_effect = ValueError("Database error")

        with patch("openfatture.cli.commands.cliente.console") as mock_console:
            with pytest.raises(SystemExit):
                add_cliente(
                    "Test Client",
                    partita_iva="12345678901",
                    codice_fiscale=None,
                    codice_destinatario=None,
                    pec=None,
                    interactive=False,
                )

            mock_console.print.assert_called()
            mock_exit.assert_called_once_with(1)

    @patch("openfatture.cli.commands.cliente.typer.Exit")
    @patch("openfatture.cli.commands.cliente._get_session")
    @patch("openfatture.cli.commands.cliente.ensure_db")
    def test_add_cliente_duplicate_piva(self, mock_ensure_db, mock_get_session, mock_exit):
        """Test adding client with duplicate partita IVA (database constraint violation)."""
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db

        mock_exit.side_effect = SystemExit(1)

        # Mock commit to raise IntegrityError for duplicate
        from sqlalchemy.exc import IntegrityError

        mock_db.commit.side_effect = IntegrityError(None, None, Exception("Duplicate PIVA"))

        with patch("openfatture.cli.commands.cliente.console") as mock_console:
            with pytest.raises(SystemExit):
                add_cliente(
                    "Test Client",
                    partita_iva="12345678901",
                    codice_fiscale=None,
                    codice_destinatario=None,
                    pec=None,
                    interactive=False,
                )

            mock_console.print.assert_called()
            mock_exit.assert_called_once_with(1)
