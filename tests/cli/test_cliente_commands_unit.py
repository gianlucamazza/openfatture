"""
Unit tests for cliente CLI command functions.

These exercise the commands end-to-end against a real, isolated database
(``runtime_db``) instead of mocking SQLAlchemy query chains: data is seeded
through the same database the command reads, and the locale is pinned to English
so message assertions are deterministic. Genuine error-path tests force a DB
failure by patching the real ``db_session`` seam on the command module.
"""

from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from openfatture.cli.commands.cliente import add_cliente, app
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    StatoFattura,
    TipoDocumento,
)

runner = CliRunner()


@pytest.fixture(autouse=True)
def _english_locale():
    """Pin the locale to English so message assertions are deterministic."""
    from openfatture.i18n import get_locale, set_locale

    previous = get_locale()
    set_locale("en")
    try:
        yield
    finally:
        set_locale(previous)


def _seed_cliente(session, *, denominazione="Acme Corporation", **overrides) -> Cliente:
    """Persist a client into the runtime database and return it."""
    data = {
        "denominazione": denominazione,
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


def _seed_fattura(session, cliente: Cliente) -> Fattura:
    """Persist a minimal invoice for ``cliente`` into the runtime database."""
    fattura = Fattura(
        numero="1",
        anno=2025,
        data_emissione=date(2025, 1, 15),
        cliente_id=cliente.id,
        tipo_documento=TipoDocumento.TD01,
        stato=StatoFattura.BOZZA,
        imponibile=Decimal("1000.00"),
        iva=Decimal("220.00"),
        totale=Decimal("1220.00"),
    )
    session.add(fattura)
    session.commit()
    session.refresh(fattura)
    return fattura


@contextmanager
def _failing_db_session(exc: Exception):
    """A ``db_session()`` replacement whose add/commit raise ``exc``."""
    db = MagicMock()
    db.add.side_effect = exc
    db.commit.side_effect = exc
    yield db


class TestListClientiFunction:
    """Test the 'list' command."""

    def test_list_clienti_empty(self, runtime_db):
        """Test listing when no clients exist."""
        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "No clients found" in result.stdout

    def test_list_clienti_with_data(self, runtime_session):
        """Test listing clients with data."""
        _seed_cliente(runtime_session, denominazione="Test Client")

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "Test Client" in result.stdout


class TestShowClienteFunction:
    """Test the 'show' command."""

    def test_show_cliente_not_found(self, runtime_db):
        """Test showing non-existent client."""
        result = runner.invoke(app, ["show", "999"])

        assert result.exit_code == 1
        assert "Client not found" in result.stdout

    def test_show_cliente_success(self, runtime_session):
        """Test showing client details."""
        cliente = _seed_cliente(runtime_session)

        result = runner.invoke(app, ["show", str(cliente.id)])

        assert result.exit_code == 0
        assert "Acme Corporation" in result.stdout


class TestDeleteClienteFunction:
    """Test the 'delete' command."""

    def test_delete_cliente_not_found(self, runtime_db):
        """Test deleting non-existent client."""
        result = runner.invoke(app, ["delete", "999"])

        assert result.exit_code == 1
        assert "Client not found" in result.stdout

    @patch("openfatture.cli.commands.cliente.Confirm.ask")
    def test_delete_cliente_with_invoices(self, mock_confirm_ask, runtime_session):
        """Test deleting client with existing invoices (should prompt and cancel)."""
        cliente = _seed_cliente(runtime_session)
        _seed_fattura(runtime_session, cliente)
        cliente_id = cliente.id

        mock_confirm_ask.return_value = False  # User cancels

        result = runner.invoke(app, ["delete", str(cliente_id)])

        assert result.exit_code == 0
        assert "Cancelled" in result.stdout
        # The invoice warning prompt must have been shown to the user.
        mock_confirm_ask.assert_called()

        # Client must still exist (deletion was cancelled).
        runtime_session.expire_all()
        assert runtime_session.get(Cliente, cliente_id) is not None

    def test_delete_cliente_success(self, runtime_session):
        """Test successful client deletion."""
        cliente = _seed_cliente(runtime_session)
        cliente_id = cliente.id

        # --force skips the confirmation prompt.
        result = runner.invoke(app, ["delete", str(cliente_id), "--force"])

        assert result.exit_code == 0
        assert "deleted" in result.stdout

        # Client must be gone from the database.
        runtime_session.expire_all()
        assert runtime_session.get(Cliente, cliente_id) is None


class TestAddClienteFunction:
    """Test the 'add' command / add_cliente function."""

    def test_add_cliente_basic(self, runtime_session):
        """Test adding client with basic information."""
        result = runner.invoke(
            app,
            ["add", "Test Client", "--piva", "12345678901"],
        )

        assert result.exit_code == 0
        assert "Client added successfully" in result.stdout

        # Client should have been persisted.
        runtime_session.expire_all()
        cliente = (
            runtime_session.query(Cliente).filter(Cliente.denominazione == "Test Client").first()
        )
        assert cliente is not None
        assert cliente.partita_iva == "12345678901"

    def test_add_cliente_validation_error(self, runtime_db):
        """Test that a database error during add aborts the command.

        ``add_cliente`` runs inside ``db_session()``, which rolls back and
        re-raises any exception. A failure in ``db.add`` therefore propagates
        out of the command instead of silently succeeding.
        """

        def fake_session():
            return _failing_db_session(ValueError("Database error"))

        with patch(
            "openfatture.cli.commands.cliente.db_session",
            side_effect=fake_session,
        ):
            with pytest.raises(ValueError, match="Database error"):
                add_cliente(
                    "Test Client",
                    partita_iva="12345678901",
                    codice_fiscale=None,
                    codice_destinatario=None,
                    pec=None,
                    interactive=False,
                )

    def test_add_cliente_duplicate_piva(self, runtime_db):
        """Test that a duplicate partita IVA (constraint violation) aborts the command.

        ``db.add`` raising ``IntegrityError`` (e.g. a duplicate VAT number)
        propagates out of the ``db_session()`` context after rollback.
        """
        from sqlalchemy.exc import IntegrityError

        def fake_session():
            return _failing_db_session(IntegrityError(None, None, Exception("Duplicate PIVA")))

        with patch(
            "openfatture.cli.commands.cliente.db_session",
            side_effect=fake_session,
        ):
            with pytest.raises(IntegrityError):
                add_cliente(
                    "Test Client",
                    partita_iva="12345678901",
                    codice_fiscale=None,
                    codice_destinatario=None,
                    pec=None,
                    interactive=False,
                )
