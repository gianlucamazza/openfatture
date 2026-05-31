"""Tests for invoice CLI commands.

These exercise the Typer commands end-to-end against a real, isolated database
(``runtime_db``) instead of mocking SQLAlchemy query chains: data is seeded
through the same database the command reads, and the locale is pinned to English
so label assertions are deterministic. Genuine error paths (e.g. the DB raising
mid-operation) inject failures via the real ``db_session`` seam.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from openfatture.cli.commands.fattura import app
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)


class _WideCliRunner(CliRunner):
    """CliRunner that renders Rich output at a wide terminal width.

    Under the default 80-column terminal Rich truncates table cells (client
    names, invoice numbers), which would make substring assertions flaky. A
    fixed wide width keeps the rendered tokens intact and deterministic.
    """

    def invoke(self, *args, **kwargs):  # type: ignore[override]
        env = {"COLUMNS": "220", **(kwargs.pop("env", None) or {})}
        return super().invoke(*args, env=env, **kwargs)


runner = _WideCliRunner()
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


def _make_cliente(
    session: Session,
    denominazione: str = "Acme Corporation",
    codice: str = "ABC1234",
) -> Cliente:
    cliente = Cliente(
        denominazione=denominazione,
        partita_iva="12345678901",
        codice_destinatario=codice,
        nazione="IT",
    )
    session.add(cliente)
    session.commit()
    session.refresh(cliente)
    return cliente


def _make_fattura(
    session: Session,
    *,
    numero: str,
    cliente: Cliente,
    anno: int = 2025,
    mese: int = 1,
    stato: StatoFattura = StatoFattura.BOZZA,
    tipo_documento: TipoDocumento = TipoDocumento.TD01,
    imponibile: Decimal = Decimal("1000.00"),
    iva: Decimal = Decimal("220.00"),
    ritenuta_acconto: Decimal | None = None,
    aliquota_ritenuta: Decimal | None = None,
    importo_bollo: Decimal | None = None,
) -> Fattura:
    totale = imponibile + iva
    fattura = Fattura(
        numero=numero,
        anno=anno,
        data_emissione=date(anno, mese, 15),
        cliente_id=cliente.id,
        tipo_documento=tipo_documento,
        stato=stato,
        imponibile=imponibile,
        iva=iva,
        ritenuta_acconto=ritenuta_acconto,
        aliquota_ritenuta=aliquota_ritenuta,
        importo_bollo=importo_bollo,
        totale=totale,
    )
    session.add(fattura)
    session.flush()
    session.add(
        RigaFattura(
            fattura_id=fattura.id,
            numero_riga=1,
            descrizione="Consulenza sviluppo software",
            quantita=Decimal("1"),
            prezzo_unitario=imponibile,
            unita_misura="servizio",
            aliquota_iva=Decimal("22.00"),
            imponibile=imponibile,
            iva=iva,
            totale=totale,
        )
    )
    session.commit()
    session.refresh(fattura)
    return fattura


class TestListFattureCommand:
    """Test 'fattura list' command."""

    def test_list_fatture_empty(self, runtime_db):
        """Test listing when no invoices exist."""
        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "No invoices found" in result.stdout

    def test_list_fatture_with_data(self, runtime_session):
        """Test listing invoices with data."""
        cliente = _make_cliente(runtime_session)
        _make_fattura(runtime_session, numero="1", cliente=cliente)

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "Invoices" in result.stdout  # Table is shown
        assert "Acme Corporation" in result.stdout

    def test_list_fatture_with_filters(self, runtime_session):
        """Test listing with status and year filters."""
        cliente = _make_cliente(runtime_session)
        _make_fattura(
            runtime_session,
            numero="1",
            cliente=cliente,
            anno=2025,
            stato=StatoFattura.BOZZA,
        )

        result = runner.invoke(app, ["list", "--stato", "bozza", "--anno", "2025"])

        assert result.exit_code == 0
        # Should filter by status and year and still show the matching invoice
        assert "Acme Corporation" in result.stdout

    def test_list_fatture_invalid_status(self, runtime_db):
        """Test listing with invalid status filter."""
        result = runner.invoke(app, ["list", "--stato", "invalid"])

        # Should show error but not exit with error code
        assert "Invalid status" in result.stdout


class TestShowFatturaCommand:
    """Test 'fattura show' command."""

    def test_show_fattura_not_found(self, runtime_db):
        """Test showing non-existent invoice."""
        result = runner.invoke(app, ["show", "999"])

        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_show_fattura_success(self, runtime_session):
        """Test showing invoice details."""
        cliente = _make_cliente(runtime_session)
        fattura = _make_fattura(runtime_session, numero="1", cliente=cliente)

        result = runner.invoke(app, ["show", str(fattura.id)])

        assert result.exit_code == 0
        assert "Invoice 1/2025" in result.stdout
        assert "Acme Corporation" in result.stdout
        assert "1000" in result.stdout  # Imponibile

    def test_show_fattura_with_ritenuta(self, runtime_session):
        """Test showing invoice with ritenuta."""
        cliente = _make_cliente(runtime_session)
        fattura = _make_fattura(
            runtime_session,
            numero="2",
            cliente=cliente,
            mese=2,
            stato=StatoFattura.DA_INVIARE,
            tipo_documento=TipoDocumento.TD06,
            ritenuta_acconto=Decimal("200.00"),
            aliquota_ritenuta=Decimal("20.00"),
        )

        result = runner.invoke(app, ["show", str(fattura.id)])

        assert result.exit_code == 0
        # "Withholding" is the English label for ritenuta d'acconto.
        assert "Withholding" in result.stdout


class TestDeleteFatturaCommand:
    """Test 'fattura delete' command."""

    def test_delete_fattura_not_found(self, runtime_db):
        """Test deleting non-existent invoice."""
        result = runner.invoke(app, ["delete", "999"])

        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_delete_fattura_sent_invoice_blocked(self, runtime_session):
        """Test that sent invoices cannot be deleted."""
        cliente = _make_cliente(runtime_session)
        fattura = _make_fattura(
            runtime_session,
            numero="1",
            cliente=cliente,
            stato=StatoFattura.INVIATA,
        )

        result = runner.invoke(app, ["delete", str(fattura.id)])

        assert result.exit_code == 1
        assert "Cannot delete invoice" in result.stdout

    def test_delete_fattura_with_force(self, runtime_session):
        """Test deleting invoice with --force flag."""
        cliente = _make_cliente(runtime_session)
        fattura = _make_fattura(
            runtime_session,
            numero="1",
            cliente=cliente,
            stato=StatoFattura.BOZZA,
        )
        fattura_id = fattura.id

        result = runner.invoke(app, ["delete", str(fattura_id), "--force"])

        assert result.exit_code == 0
        assert "deleted" in result.stdout
        # Row is really gone from the shared database.
        assert runtime_session.query(Fattura).filter(Fattura.id == fattura_id).first() is None


class TestGeneraXMLCommand:
    """Test 'fattura xml' command."""

    def test_genera_xml_invoice_not_found(self, runtime_db):
        """Test XML generation for non-existent invoice."""
        result = runner.invoke(app, ["xml", "999"])

        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_genera_xml_success(self, runtime_session):
        """Test successful XML generation."""
        cliente = _make_cliente(runtime_session)
        fattura = _make_fattura(runtime_session, numero="1", cliente=cliente)

        with patch("openfatture.core.fatture.service.InvoiceService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.generate_xml.return_value = ("<?xml...>", None)
            mock_path = Mock()
            mock_path.absolute.return_value = "/path/to/xml"
            mock_service.get_xml_path.return_value = mock_path

            result = runner.invoke(app, ["xml", str(fattura.id), "--no-validate"])

            assert result.exit_code == 0
            assert "generated" in result.stdout.lower()
            mock_service.generate_xml.assert_called_once()

    def test_genera_xml_with_error(self, runtime_session):
        """Test XML generation with error."""
        cliente = _make_cliente(runtime_session)
        fattura = _make_fattura(runtime_session, numero="1", cliente=cliente)

        with patch("openfatture.core.fatture.service.InvoiceService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.generate_xml.return_value = ("", "Validation error")

            result = runner.invoke(app, ["xml", str(fattura.id)])

            assert result.exit_code == 1
            # Error should be displayed (either "Error" or the actual error message)
            assert len(result.stdout) > 0

    def test_genera_xml_custom_output(self, runtime_session, tmp_path):
        """Test XML generation with custom output path."""
        cliente = _make_cliente(runtime_session)
        fattura = _make_fattura(runtime_session, numero="1", cliente=cliente)

        output_file = tmp_path / "test.xml"

        with patch("openfatture.core.fatture.service.InvoiceService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.generate_xml.return_value = ("<xml>content</xml>", None)

            result = runner.invoke(
                app, ["xml", str(fattura.id), "--output", str(output_file), "--no-validate"]
            )

            assert result.exit_code == 0
            assert output_file.exists()
            assert output_file.read_text() == "<xml>content</xml>"


class TestInviaFatturaCommand:
    """Test 'fattura invia' command."""

    def test_invia_invoice_not_found(self, runtime_db):
        """Test sending non-existent invoice."""
        result = runner.invoke(app, ["invia", "999"])

        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_invia_xml_generation_fails(self, runtime_session):
        """Test sending when XML generation fails."""
        cliente = _make_cliente(runtime_session)
        fattura = _make_fattura(runtime_session, numero="1", cliente=cliente)

        with patch("openfatture.core.fatture.service.InvoiceService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.generate_xml.return_value = ("", "XML error")

            result = runner.invoke(app, ["invia", str(fattura.id)])

            assert result.exit_code == 1
            assert "XML generation failed" in result.stdout

    @patch("openfatture.cli.commands.fattura.Confirm")
    def test_invia_user_cancels(self, mock_confirm, runtime_session):
        """Test sending when user cancels confirmation."""
        cliente = _make_cliente(runtime_session)
        fattura = _make_fattura(runtime_session, numero="1", cliente=cliente)

        # User says no to confirmation
        mock_confirm.ask.return_value = False

        with patch("openfatture.core.fatture.service.InvoiceService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.generate_xml.return_value = ("<xml/>", None)

            result = runner.invoke(app, ["invia", str(fattura.id)])

            assert result.exit_code == 0
            # User cancelled - command exits gracefully

    @patch("openfatture.cli.commands.fattura.Confirm")
    def test_invia_success(self, mock_confirm, runtime_session):
        """Test successful invoice sending."""
        cliente = _make_cliente(runtime_session)
        fattura = _make_fattura(runtime_session, numero="1", cliente=cliente)

        # User confirms sending
        mock_confirm.ask.return_value = True

        with (
            patch("openfatture.core.fatture.service.InvoiceService") as mock_service_class,
            patch("openfatture.utils.email.sender.TemplatePECSender") as mock_pec_class,
            patch("openfatture.sdi.pec_sender.sender.create_log_entry"),
        ):
            mock_service = mock_service_class.return_value
            mock_service.generate_xml.return_value = ("<xml/>", None)
            mock_service.get_xml_path.return_value = Mock()

            mock_pec = mock_pec_class.return_value
            mock_pec.send_invoice_to_sdi.return_value = (True, None)

            result = runner.invoke(app, ["invia", str(fattura.id)])

            assert result.exit_code == 0
            assert "sent" in result.stdout.lower()
            mock_pec.send_invoice_to_sdi.assert_called_once()


class TestCreaFatturaCommand:
    """Test 'fattura crea' command."""

    def test_crea_no_clients(self, runtime_db):
        """Test creating invoice when no clients exist."""
        result = runner.invoke(app, ["crea"])

        assert result.exit_code == 1
        assert "No clients found" in result.stdout

    def test_crea_client_not_found(self, runtime_db):
        """Test creating invoice with non-existent client ID."""
        result = runner.invoke(app, ["crea", "--cliente", "999"])

        assert result.exit_code == 1
        assert "Invalid client selection" in result.stdout

    @patch("openfatture.cli.commands.fattura.Prompt")
    @patch("openfatture.cli.commands.fattura.IntPrompt")
    @patch("openfatture.cli.commands.fattura.FloatPrompt")
    @patch("openfatture.cli.commands.fattura.Confirm")
    def test_crea_successful_with_line_items(
        self,
        mock_confirm,
        mock_float_prompt,
        mock_int_prompt,
        mock_prompt,
        runtime_session,
    ):
        """Test successful invoice creation with line items."""
        cliente = _make_cliente(runtime_session)

        # Mock user inputs
        mock_prompt.ask.side_effect = [
            "001",  # invoice number
            "2025-01-15",  # issue date
            "Development services",  # item 1 description
            "",  # end items
        ]
        mock_float_prompt.ask.side_effect = [
            10.0,  # quantity
            50.0,  # unit price
            22.0,  # VAT rate
        ]
        mock_confirm.ask.side_effect = [
            False,  # no ritenuta
            False,  # no bollo
        ]

        result = runner.invoke(app, ["crea", "--cliente", str(cliente.id)])

        assert result.exit_code == 0
        assert "Invoice created successfully" in result.stdout
        # The command stamps invoices with the current year.
        assert f"001/{date.today().year}" in result.stdout
        # Invoice persisted to the shared database.
        created = runtime_session.query(Fattura).filter(Fattura.numero == "001").first()
        assert created is not None
        assert len(created.righe) == 1

    @patch("openfatture.cli.commands.fattura.Prompt")
    @patch("openfatture.cli.commands.fattura.IntPrompt")
    @patch("openfatture.cli.commands.fattura.FloatPrompt")
    @patch("openfatture.cli.commands.fattura.Confirm")
    def test_crea_cancelled_no_items(
        self,
        mock_confirm,
        mock_float_prompt,
        mock_int_prompt,
        mock_prompt,
        runtime_session,
    ):
        """Test invoice creation cancelled when no items added."""
        cliente = _make_cliente(runtime_session)

        # Mock user inputs - empty description immediately
        mock_prompt.ask.side_effect = [
            "001",  # invoice number
            "2025-01-15",  # issue date
            "",  # no items
        ]

        result = runner.invoke(app, ["crea", "--cliente", str(cliente.id)])

        assert result.exit_code == 0
        assert "No items added. Invoice creation cancelled" in result.stdout
        # Rolled back: nothing persisted.
        assert runtime_session.query(Fattura).filter(Fattura.numero == "001").first() is None

    @patch("openfatture.cli.commands.fattura.Prompt")
    @patch("openfatture.cli.commands.fattura.IntPrompt")
    @patch("openfatture.cli.commands.fattura.FloatPrompt")
    @patch("openfatture.cli.commands.fattura.Confirm")
    def test_crea_with_ritenuta_and_bollo(
        self,
        mock_confirm,
        mock_float_prompt,
        mock_int_prompt,
        mock_prompt,
        runtime_session,
    ):
        """Test invoice creation with ritenuta and bollo."""
        cliente = _make_cliente(runtime_session)

        # Mock user inputs
        mock_prompt.ask.side_effect = [
            "001",  # invoice number
            "2025-01-15",  # issue date
            "Consulting",  # item description
            "",  # end items
        ]
        mock_float_prompt.ask.side_effect = [
            1.0,  # quantity
            100.0,  # unit price
            0.0,  # VAT rate (0% for bollo)
            20.0,  # ritenuta rate
        ]
        mock_confirm.ask.side_effect = [
            True,  # yes ritenuta
            True,  # yes bollo
        ]

        result = runner.invoke(app, ["crea", "--cliente", str(cliente.id)])

        assert result.exit_code == 0
        assert "Invoice created successfully" in result.stdout
        # The crea summary table uses literal labels (not i18n keys).
        assert "Ritenuta" in result.stdout
        assert "Bollo" in result.stdout
        # Persisted with ritenuta and bollo applied.
        created = runtime_session.query(Fattura).filter(Fattura.numero == "001").first()
        assert created is not None
        assert created.ritenuta_acconto == Decimal("20.00")
        assert created.importo_bollo == Decimal("2.00")

    @patch("openfatture.cli.commands.fattura.Prompt")
    @patch("openfatture.cli.commands.fattura.IntPrompt")
    @patch("openfatture.cli.commands.fattura.FloatPrompt")
    @patch("openfatture.cli.commands.fattura.Confirm")
    def test_crea_client_selection_interactive(
        self,
        mock_confirm,
        mock_float_prompt,
        mock_int_prompt,
        mock_prompt,
        runtime_session,
    ):
        """Test client selection in interactive mode."""
        cliente = _make_cliente(runtime_session)

        # Mock client selection (pick the seeded client by id)
        mock_int_prompt.ask.return_value = cliente.id

        # Mock user inputs
        mock_prompt.ask.side_effect = [
            "001",  # invoice number
            "2025-01-15",  # issue date
            "",  # no items
        ]

        result = runner.invoke(app, ["crea"])

        assert result.exit_code == 0
        assert "No items added. Invoice creation cancelled" in result.stdout
        mock_int_prompt.ask.assert_called_once()

    @patch("openfatture.cli.commands.fattura.Prompt")
    @patch("openfatture.cli.commands.fattura.db_session")
    def test_crea_database_error(self, mock_db_session, mock_prompt, runtime_db):
        """Test invoice creation surfaces a database error.

        ``crea`` has no try/except of its own: a failure mid-creation must
        propagate (rollback is the ``db_session`` context manager's job, covered
        by its own tests). We inject the failure at the real ``db_session`` seam
        — making ``db.add`` raise — and assert the error surfaces instead of the
        command reporting success. ``rollback`` is asserted to confirm the
        context manager's exit path runs on the way out.
        """
        cliente = Mock()
        cliente.id = 1
        cliente.denominazione = "Acme Corporation"

        mock_db = MagicMock()
        db_error = RuntimeError("Database connection failed")

        # Emulate the real db_session contract: yield the session, and on an
        # exception inside the block, roll back and re-raise.
        class _CtxManager:
            def __enter__(self):
                return mock_db

            def __exit__(self, exc_type, exc, tb):
                if exc_type is not None:
                    mock_db.rollback()
                return False  # propagate

        mock_db_session.return_value = _CtxManager()
        # Client lookup succeeds, invoice-number lookup returns no previous invoice.
        mock_db.query.return_value.filter.return_value.first.return_value = cliente
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )
        # Adding the invoice blows up.
        mock_db.add.side_effect = db_error

        mock_prompt.ask.side_effect = [
            "001",  # invoice number
            "2025-01-15",  # issue date
        ]

        result = runner.invoke(app, ["crea", "--cliente", "1"])

        assert result.exit_code != 0
        assert result.exception is db_error
        mock_db.rollback.assert_called_once()


class TestEnsureDB:
    """Test database initialization helper."""

    @patch("openfatture.cli.commands.fattura.get_settings")
    @patch("openfatture.cli.commands.fattura.init_db")
    def test_ensure_db_calls_init(self, mock_init_db, mock_settings):
        """Test that ensure_db calls init_db with correct URL."""
        from openfatture.cli.commands.fattura import ensure_db

        mock_settings_instance = Mock()
        mock_settings_instance.database_url = "sqlite:///test.db"
        mock_settings.return_value = mock_settings_instance

        ensure_db()

        mock_init_db.assert_called_once_with("sqlite:///test.db")
