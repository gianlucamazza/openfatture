"""
Tests for cliente CLI commands.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from openfatture.cli.commands.cliente import app

runner = CliRunner()
pytestmark = pytest.mark.unit


class TestListClientiCommand:
    """Test 'cliente list' command."""

    @patch("openfatture.cli.commands.cliente.SessionLocal")
    @patch("openfatture.cli.commands.cliente.init_db")
    def test_list_clienti_empty(self, mock_init_db, mock_session_local):
        """Test listing when no clients exist."""
        # Mock database session
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "No clients found" in result.stdout

    @patch("openfatture.cli.commands.cliente.SessionLocal")
    @patch("openfatture.cli.commands.cliente.init_db")
    def test_list_clienti_with_data(self, mock_init_db, mock_session_local, sample_cliente):
        """Test listing clients with data."""
        # Setup mock
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Mock the query chain
        mock_query = mock_db.query.return_value.order_by.return_value
        mock_query.limit.return_value.all.return_value = [sample_cliente]

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "Clients" in result.stdout

    @patch("openfatture.cli.commands.cliente.SessionLocal")
    @patch("openfatture.cli.commands.cliente.init_db")
    def test_list_clienti_with_limit(self, mock_init_db, mock_session_local):
        """Test listing with custom limit."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = runner.invoke(app, ["list", "--limit", "10"])

        assert result.exit_code == 0
        # Verify limit was applied
        mock_db.query.return_value.order_by.return_value.limit.assert_called_once_with(10)


class TestShowClienteCommand:
    """Test 'cliente show' command."""

    @patch("openfatture.cli.commands.cliente.SessionLocal")
    @patch("openfatture.cli.commands.cliente.init_db")
    def test_show_cliente_not_found(self, mock_init_db, mock_session_local):
        """Test showing non-existent client."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = runner.invoke(app, ["show", "999"])

        assert result.exit_code == 1
        assert "not found" in result.stdout

    @patch("openfatture.cli.commands.cliente.SessionLocal")
    @patch("openfatture.cli.commands.cliente.init_db")
    def test_show_cliente_success(self, mock_init_db, mock_session_local, sample_cliente):
        """Test showing client details."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = sample_cliente

        result = runner.invoke(app, ["show", "1"])

        assert result.exit_code == 0
        assert "Client Details" in result.stdout
        assert sample_cliente.denominazione in result.stdout

    @patch("openfatture.cli.commands.cliente.SessionLocal")
    @patch("openfatture.cli.commands.cliente.init_db")
    def test_show_cliente_with_full_address(self, mock_init_db, mock_session_local):
        """Test showing client with full address information."""
        # Create a client with full address
        mock_cliente = Mock()
        mock_cliente.id = 1
        mock_cliente.denominazione = "Test Client"
        mock_cliente.partita_iva = "12345678901"
        mock_cliente.codice_fiscale = "RSSMRA80A01H501U"
        mock_cliente.indirizzo = "Via Roma 1"
        mock_cliente.cap = "00100"
        mock_cliente.comune = "Roma"
        mock_cliente.provincia = "RM"
        mock_cliente.codice_destinatario = "ABCDEFG"
        mock_cliente.pec = "test@pec.it"
        mock_cliente.email = "test@example.com"
        mock_cliente.telefono = "0612345678"
        mock_cliente.fatture = []
        mock_cliente.created_at = Mock()
        mock_cliente.created_at.strftime.return_value = "2025-01-01 12:00"

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cliente

        result = runner.invoke(app, ["show", "1"])

        assert result.exit_code == 0
        assert "Via Roma 1" in result.stdout
        assert "ABCDEFG" in result.stdout
        assert "test@pec.it" in result.stdout


class TestDeleteClienteCommand:
    """Test 'cliente delete' command."""

    @patch("openfatture.cli.commands.cliente.SessionLocal")
    @patch("openfatture.cli.commands.cliente.init_db")
    def test_delete_cliente_not_found(self, mock_init_db, mock_session_local):
        """Test deleting non-existent client."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = runner.invoke(app, ["delete", "999"])

        assert result.exit_code == 1
        assert "not found" in result.stdout

    @patch("openfatture.cli.commands.cliente.SessionLocal")
    @patch("openfatture.cli.commands.cliente.init_db")
    def test_delete_cliente_with_force(self, mock_init_db, mock_session_local):
        """Test deleting client with --force flag."""
        mock_cliente = Mock()
        mock_cliente.id = 1
        mock_cliente.denominazione = "Test Client"
        mock_cliente.fatture = []

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cliente

        result = runner.invoke(app, ["delete", "1", "--force"])

        assert result.exit_code == 0
        assert "deleted" in result.stdout
        mock_db.delete.assert_called_once_with(mock_cliente)
        mock_db.commit.assert_called_once()

    @patch("openfatture.cli.commands.cliente.Confirm")
    @patch("openfatture.cli.commands.cliente.SessionLocal")
    @patch("openfatture.cli.commands.cliente.init_db")
    def test_delete_cliente_with_invoices_user_cancels(
        self, mock_init_db, mock_session_local, mock_confirm
    ):
        """Test deleting client with invoices - user cancels."""
        mock_cliente = Mock()
        mock_cliente.id = 1
        mock_cliente.denominazione = "Test Client"
        mock_cliente.fatture = [Mock(), Mock()]  # 2 invoices

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cliente

        # User says no to deletion
        mock_confirm.ask.return_value = False

        result = runner.invoke(app, ["delete", "1"])

        assert result.exit_code == 0
        assert "Cancelled" in result.stdout
        mock_db.delete.assert_not_called()

    @patch("openfatture.cli.commands.cliente.Confirm")
    @patch("openfatture.cli.commands.cliente.SessionLocal")
    @patch("openfatture.cli.commands.cliente.init_db")
    def test_delete_cliente_with_confirmation(self, mock_init_db, mock_session_local, mock_confirm):
        """Test deleting client with confirmation."""
        mock_cliente = Mock()
        mock_cliente.id = 1
        mock_cliente.denominazione = "Test Client"
        mock_cliente.fatture = []

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cliente

        # User confirms deletion
        mock_confirm.ask.return_value = True

        result = runner.invoke(app, ["delete", "1"])

        assert result.exit_code == 0
        assert "deleted" in result.stdout
        mock_db.delete.assert_called_once()


class TestAddClienteCommand:
    """Test 'cliente add' command."""

    @patch("openfatture.cli.commands.cliente.SessionLocal")
    @patch("openfatture.cli.commands.cliente.init_db")
    def test_add_cliente_quick_mode(self, mock_init_db, mock_session_local):
        """Test adding client in quick mode (non-interactive)."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Mock the created client
        mock_cliente = Mock()
        mock_cliente.id = 1
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock(side_effect=lambda c: setattr(c, "id", 1))

        result = runner.invoke(app, ["add", "Test Client", "--piva", "12345678901"])

        assert result.exit_code == 0
        assert "Client added successfully" in result.stdout

    @patch("openfatture.cli.commands.cliente.SessionLocal")
    @patch("openfatture.cli.commands.cliente.init_db")
    def test_add_cliente_with_all_options(self, mock_init_db, mock_session_local):
        """Test adding client with all command line options."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_cliente = Mock()
        mock_cliente.id = 1
        mock_db.refresh = Mock(side_effect=lambda c: setattr(c, "id", 1))

        result = runner.invoke(
            app,
            [
                "add",
                "Test Client",
                "--piva",
                "12345678901",
                "--cf",
                "RSSMRA80A01H501U",
                "--sdi",
                "ABCDEFG",
                "--pec",
                "test@pec.it",
            ],
        )

        assert result.exit_code == 0
        assert "Client added successfully" in result.stdout

    @patch("openfatture.cli.commands.cliente.SessionLocal")
    @patch("openfatture.cli.commands.cliente.init_db")
    def test_add_cliente_database_error(self, mock_init_db, mock_session_local):
        """Test adding client with database error."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.add.side_effect = Exception("Database error")

        result = runner.invoke(app, ["add", "Test Client"])

        assert result.exit_code == 1
        assert "Error adding client" in result.stdout
        mock_db.rollback.assert_called_once()

    @patch("openfatture.cli.commands.cliente.Prompt")
    @patch("openfatture.cli.commands.cliente.SessionLocal")
    @patch("openfatture.cli.commands.cliente.init_db")
    def test_add_cliente_interactive_basic(self, mock_init_db, mock_session_local, mock_prompt):
        """Test adding client in interactive mode."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_cliente = Mock()
        mock_cliente.id = 1
        mock_db.refresh = Mock(side_effect=lambda c: setattr(c, "id", 1))

        # Mock user inputs for interactive mode
        mock_prompt.ask.side_effect = [
            "Test Interactive Client",  # denominazione
            "12345678901",  # partita_iva
            "RSSMRA80A01H501U",  # codice_fiscale
            "Via Roma 1",  # indirizzo
            "00100",  # cap
            "Roma",  # comune
            "RM",  # provincia
            "ABCDEFG",  # SDI code
            "test@pec.it",  # PEC
            "test@example.com",  # email
            "0612345678",  # telefono
        ]

        result = runner.invoke(app, ["add", "Test", "--interactive"])

        assert result.exit_code == 0
        assert "Client added successfully" in result.stdout

    @patch("openfatture.cli.commands.cliente.Prompt")
    @patch("openfatture.cli.commands.cliente.SessionLocal")
    @patch("openfatture.cli.commands.cliente.init_db")
    def test_add_cliente_interactive_invalid_piva(
        self, mock_init_db, mock_session_local, mock_prompt
    ):
        """Test adding client in interactive mode with invalid P.IVA."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_cliente = Mock()
        mock_cliente.id = 1
        mock_db.refresh = Mock(side_effect=lambda c: setattr(c, "id", 1))

        # Mock user inputs - invalid P.IVA
        mock_prompt.ask.side_effect = [
            "Test Client",  # denominazione
            "INVALID",  # partita_iva (INVALID)
            "",  # codice_fiscale (empty)
            "",  # indirizzo
            "",  # cap
            "",  # comune
            "",  # provincia
            "",  # SDI code
            "",  # PEC
            "",  # email
            "",  # telefono
        ]

        result = runner.invoke(app, ["add", "Test", "--interactive"])

        assert result.exit_code == 0
        assert "Invalid Partita IVA" in result.stdout


class TestEnsureDB:
    """Test database initialization helper."""

    @patch("openfatture.cli.commands.cliente.get_settings")
    @patch("openfatture.cli.commands.cliente.init_db")
    def test_ensure_db_calls_init(self, mock_init_db, mock_settings):
        """Test that ensure_db calls init_db with correct URL."""
        from openfatture.cli.commands.cliente import ensure_db

        mock_settings_instance = Mock()
        mock_settings_instance.database_url = "sqlite:///test.db"
        mock_settings.return_value = mock_settings_instance

        ensure_db()

        mock_init_db.assert_called_once_with("sqlite:///test.db")
