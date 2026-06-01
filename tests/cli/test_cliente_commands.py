"""Tests for cliente CLI commands.

These exercise the commands end-to-end against a real, isolated database
(``runtime_db``) instead of mocking SQLAlchemy query chains: data is seeded
through the same database the command reads, and the locale is pinned to
English so label assertions are deterministic. Only genuine error-path tests
mock the ``db_session`` seam to force a database failure.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from openfatture.cli.commands.cliente import app
from openfatture.storage.database.models import Cliente

runner = CliRunner()
pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _english_locale():
    """Pin the locale to English so label assertions are deterministic."""
    from openfatture.i18n import get_locale, set_locale

    previous = get_locale()
    set_locale("en")
    try:
        yield
    finally:
        set_locale(previous)


def _make_cliente(session: Session, **overrides) -> Cliente:
    """Seed a real client row into the runtime database."""
    data = {
        "denominazione": "Acme Corporation",
        "partita_iva": "12345678901",
        "codice_fiscale": "CMPACM80A01H501Z",
        "codice_destinatario": "ABC1234",
        "pec": "acme@pec.it",
        "indirizzo": "Via Roma 1",
        "cap": "20100",
        "comune": "Milano",
        "provincia": "MI",
        "nazione": "IT",
        "email": "contact@acme.com",
        "telefono": "+39 02 12345678",
    }
    data.update(overrides)
    cliente = Cliente(**data)
    session.add(cliente)
    session.commit()
    session.refresh(cliente)
    return cliente


class TestListClientiCommand:
    """Test 'cliente list' command."""

    def test_list_clienti_empty(self, runtime_db):
        """Test listing when no clients exist."""
        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "No clients found" in result.stdout

    def test_list_clienti_with_data(self, runtime_session):
        """Test listing clients with data."""
        cliente = _make_cliente(runtime_session)

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "Clients" in result.stdout
        assert cliente.denominazione in result.stdout

    def test_list_clienti_with_limit(self, runtime_session):
        """Test listing with custom limit returns seeded rows."""
        _make_cliente(runtime_session, denominazione="Alpha SRL", partita_iva="11111111111")
        _make_cliente(runtime_session, denominazione="Beta SRL", partita_iva="22222222222")

        result = runner.invoke(app, ["list", "--limit", "10"])

        assert result.exit_code == 0
        assert "Alpha SRL" in result.stdout
        assert "Beta SRL" in result.stdout


class TestShowClienteCommand:
    """Test 'cliente show' command."""

    def test_show_cliente_not_found(self, runtime_db):
        """Test showing non-existent client."""
        result = runner.invoke(app, ["show", "999"])

        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_show_cliente_success(self, runtime_session):
        """Test showing client details."""
        cliente = _make_cliente(runtime_session)

        result = runner.invoke(app, ["show", str(cliente.id)])

        assert result.exit_code == 0
        assert "Client Details" in result.stdout
        assert cliente.denominazione in result.stdout

    def test_show_cliente_with_full_address(self, runtime_session):
        """Test showing client with full address information."""
        cliente = _make_cliente(
            runtime_session,
            denominazione="Test Client",
            partita_iva="12345678901",
            codice_fiscale="RSSMRA80A01H501U",
            indirizzo="Via Roma 1",
            cap="00100",
            comune="Roma",
            provincia="RM",
            codice_destinatario="ABCDEFG",
            pec="test@pec.it",
            email="test@example.com",
            telefono="0612345678",
        )

        result = runner.invoke(app, ["show", str(cliente.id)])

        assert result.exit_code == 0
        assert "Via Roma 1" in result.stdout
        assert "ABCDEFG" in result.stdout
        assert "test@pec.it" in result.stdout


class TestDeleteClienteCommand:
    """Test 'cliente delete' command."""

    def test_delete_cliente_not_found(self, runtime_db):
        """Test deleting non-existent client."""
        result = runner.invoke(app, ["delete", "999"])

        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_delete_cliente_with_force(self, runtime_session):
        """Test deleting client with --force flag."""
        cliente = _make_cliente(runtime_session, denominazione="Test Client")
        cliente_id = cliente.id

        result = runner.invoke(app, ["delete", str(cliente_id), "--force"])

        assert result.exit_code == 0
        assert "deleted" in result.stdout
        # Row is actually gone from the database.
        assert runtime_session.query(Cliente).filter_by(id=cliente_id).first() is None

    @patch("openfatture.cli.commands.cliente.Confirm")
    def test_delete_cliente_with_invoices_user_cancels(
        self, mock_confirm, runtime_session, seed_fattura
    ):
        """Test deleting client with invoices - user cancels."""
        # seed_fattura creates a client (id from seed_cliente) with one invoice.
        cliente_id = seed_fattura.cliente_id

        # User says no to deletion
        mock_confirm.ask.return_value = False

        result = runner.invoke(app, ["delete", str(cliente_id)])

        assert result.exit_code == 0
        assert "Cancelled" in result.stdout
        # Client must still exist.
        assert runtime_session.query(Cliente).filter_by(id=cliente_id).first() is not None

    @patch("openfatture.cli.commands.cliente.Confirm")
    def test_delete_cliente_with_confirmation(self, mock_confirm, runtime_session):
        """Test deleting client with confirmation."""
        cliente = _make_cliente(runtime_session, denominazione="Test Client")
        cliente_id = cliente.id

        # User confirms deletion
        mock_confirm.ask.return_value = True

        result = runner.invoke(app, ["delete", str(cliente_id)])

        assert result.exit_code == 0
        assert "deleted" in result.stdout
        assert runtime_session.query(Cliente).filter_by(id=cliente_id).first() is None


class TestAddClienteCommand:
    """Test 'cliente add' command."""

    def test_add_cliente_quick_mode(self, runtime_session):
        """Test adding client in quick mode (non-interactive)."""
        result = runner.invoke(app, ["add", "Test Client", "--piva", "12345678901"])

        assert result.exit_code == 0
        assert "Client added successfully" in result.stdout
        # Client was persisted.
        assert (
            runtime_session.query(Cliente).filter_by(denominazione="Test Client").first()
            is not None
        )

    def test_add_cliente_with_all_options(self, runtime_session):
        """Test adding client with all command line options."""
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
        persisted = runtime_session.query(Cliente).filter_by(denominazione="Test Client").first()
        assert persisted is not None
        assert persisted.codice_destinatario == "ABCDEFG"
        assert persisted.pec == "test@pec.it"

    @patch("openfatture.cli.commands.cliente.db_session")
    def test_add_cliente_database_error(self, mock_ds, runtime_db):
        """A database error during add aborts cleanly (exit 1, no traceback).

        The failure is injected at the real ``db_session`` seam by making
        ``db.add`` raise a ``SQLAlchemyError``. The command must catch it,
        print a clean error message, and exit 1 — no raw exception escapes.
        """
        from sqlalchemy.exc import SQLAlchemyError

        mock_db = MagicMock()
        mock_db.add.side_effect = SQLAlchemyError("Database error")
        # Context manager that surfaces the error from the command body.
        mock_ds.return_value.__enter__.return_value = mock_db
        mock_ds.return_value.__exit__.return_value = False

        result = runner.invoke(app, ["add", "Test Client"])

        assert result.exit_code == 1
        # Clean exit: no raw exception propagated to the CLI runner.
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "Error saving client" in result.stdout

    @patch("openfatture.cli.commands.cliente.Prompt")
    def test_add_cliente_interactive_basic(self, mock_prompt, runtime_session):
        """Test adding client in interactive mode."""
        # Mock user inputs for interactive mode
        mock_prompt.ask.side_effect = [
            "Test Interactive Client",  # denominazione
            "12345678901",  # partita_iva
            "RSSMRA80A01H501U",  # codice_fiscale
            "Via Roma 1",  # indirizzo
            "",  # numero_civico
            "00100",  # cap
            "Roma",  # comune
            "RM",  # provincia
            "ABCDEFG",  # SDI code
            "test@pec.it",  # PEC
            "test@example.com",  # email
            "0612345678",  # telefono
            "",  # note
        ]

        result = runner.invoke(app, ["add", "Test", "--interactive"])

        assert result.exit_code == 0
        assert "Client added successfully" in result.stdout
        assert (
            runtime_session.query(Cliente)
            .filter_by(denominazione="Test Interactive Client")
            .first()
            is not None
        )

    @patch("openfatture.cli.commands.cliente.Prompt")
    def test_add_cliente_interactive_invalid_piva(self, mock_prompt, runtime_session):
        """Test adding client in interactive mode with invalid P.IVA."""
        # Mock user inputs - invalid P.IVA
        mock_prompt.ask.side_effect = [
            "Test Client",  # denominazione
            "INVALID",  # partita_iva (INVALID)
            "",  # codice_fiscale (empty)
            "",  # indirizzo
            "",  # numero_civico
            "",  # cap
            "",  # comune
            "",  # provincia
            "",  # SDI code
            "",  # PEC
            "",  # email
            "",  # telefono
            "",  # note
        ]

        result = runner.invoke(app, ["add", "Test", "--interactive"])

        assert result.exit_code == 0
        # The command warns about the invalid P.IVA. The English locale has no
        # translation for this key yet, so it renders the message id verbatim.
        assert "cli-cliente-invalid-piva" in result.stdout


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
