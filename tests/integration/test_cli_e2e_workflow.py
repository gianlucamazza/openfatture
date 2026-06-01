"""
End-to-end integration tests for CLI workflows.

Tests complete user journeys through the command-line interface:
- Invoice creation and management
- Client management
- Payment reconciliation
- AI assistance
- Batch operations

These exercise the real Typer commands via ``CliRunner`` against a real,
isolated database (the ``runtime_db`` / ``runtime_session`` fixtures from
``tests/conftest.py``). Crucially, CLI commands re-invoke
``init_db(settings.database_url)`` and open their own sessions through the
global session factory; ``runtime_db`` points that factory AND ``get_settings()``
at one file-backed SQLite database, so the data the test seeds is the same data
the command reads.

The locale is pinned to English so label assertions are deterministic; only
locale-independent data tokens (client names, invoice numbers, amounts) are
asserted alongside resolved English labels. External, side-effecting
collaborators are mocked at their boundary: AI providers (so no API key/network
is needed) and PEC/SMTP sending (so no real email is dispatched). Bank-statement
import uses a real temporary file written by the test.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.cli.main import app
from openfatture.payment.domain.models import BankAccount
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)


class _WideCliRunner(CliRunner):
    """CliRunner that renders Rich output at a wide terminal width.

    Under the default 80-column terminal Rich truncates table cells and panel
    bodies (client names, invoice numbers, AI text), which would make substring
    assertions flaky. A fixed wide width keeps the rendered tokens intact and
    deterministic.
    """

    def invoke(self, *args, **kwargs):  # type: ignore[override]
        env = {"COLUMNS": "220", **(kwargs.pop("env", None) or {})}
        return super().invoke(*args, env=env, **kwargs)


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


@pytest.fixture
def app_runner():
    """Create a wide CLI runner for testing."""
    return _WideCliRunner()


def _mock_ai_provider(content: str) -> MagicMock:
    """Build a mock LLM provider whose ``generate`` yields ``content``.

    The agents await ``provider.generate(...)`` and expect an ``AgentResponse``
    with usage metrics; structured-output parsing falls back to plain text when
    the content is not JSON, so the content is rendered verbatim.
    """
    provider = MagicMock()
    provider.provider_name = "mock"
    provider.model = "mock-model"
    provider.generate = AsyncMock(
        return_value=AgentResponse(
            content=content,
            status=ResponseStatus.SUCCESS,
            provider="mock",
            model="mock-model",
            usage=UsageMetrics(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30,
                estimated_cost_usd=0.0,
            ),
        )
    )
    return provider


class TestInvoiceCLIE2E:
    """Test complete invoice creation and management workflow via CLI."""

    def test_create_client_via_app(self, app_runner, runtime_db):
        """Test creating a client through CLI (interactive)."""
        # Prompts (in order): company name, P.IVA, codice fiscale, address,
        # civic number, CAP, city, province, SDI code, PEC, email, phone, notes.
        result = app_runner.invoke(
            app,
            ["cliente", "add", "--interactive"],
            input="\n".join(
                [
                    "Test Client SRL",  # denominazione
                    "12345678903",  # partita_iva (valid checksum)
                    "TSTCLT80A01H501Y",  # codice_fiscale
                    "Via Roma 1",  # indirizzo
                    "1",  # numero_civico
                    "20100",  # cap
                    "Milano",  # comune
                    "MI",  # provincia
                    "ABC1234",  # codice_destinatario
                    "",  # pec (optional)
                    "",  # email (optional)
                    "",  # telefono (optional)
                    "",  # note (optional)
                    "",  # trailing newline guard
                ]
            ),
        )

        assert result.exit_code == 0
        assert "Client added successfully" in result.output

        # Verify persistence in the shared DB.
        session = runtime_db()
        try:
            cliente = session.query(Cliente).filter_by(denominazione="Test Client SRL").first()
            assert cliente is not None
            assert cliente.partita_iva == "12345678903"
        finally:
            session.close()

    def test_create_invoice_via_app(self, app_runner, runtime_db):
        """Creating an invoice with no clients present fails gracefully."""
        # With an empty database the wizard must abort with a clear error
        # instead of crashing.
        result = app_runner.invoke(app, ["fattura", "crea"])

        assert result.exit_code != 0
        assert "No clients found" in result.output

    def test_list_invoices_via_app(self, app_runner, runtime_session):
        """Test listing invoices through CLI."""
        cliente = Cliente(
            denominazione="List Test Client",
            partita_iva="12345678901",
            codice_destinatario="LIST01",
            nazione="IT",
        )
        runtime_session.add(cliente)
        runtime_session.commit()
        runtime_session.refresh(cliente)

        fattura = Fattura(
            numero="001",
            anno=2025,
            data_emissione=date(2025, 1, 15),
            cliente_id=cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("1000.00"),
            iva=Decimal("220.00"),
            totale=Decimal("1220.00"),
        )
        runtime_session.add(fattura)
        runtime_session.commit()

        result = app_runner.invoke(app, ["fattura", "list"])

        assert result.exit_code == 0
        assert "001/2025" in result.output
        assert "List Test Client" in result.output
        # Status column renders the enum value (locale-independent).
        assert "bozza" in result.output.lower()

    def test_generate_xml_via_app(self, app_runner, runtime_session, tmp_path):
        """Test FatturaPA XML generation through CLI."""
        cliente = Cliente(
            denominazione="XML Test Client",
            partita_iva="12345678901",
            codice_fiscale="XMLCLT80A01H501Y",
            codice_destinatario="XML001",
            indirizzo="Via Test 1",
            cap="20100",
            comune="Milano",
            provincia="MI",
            nazione="IT",
        )
        runtime_session.add(cliente)
        runtime_session.commit()
        runtime_session.refresh(cliente)

        fattura = Fattura(
            numero="XML001",
            anno=2025,
            data_emissione=date(2025, 1, 15),
            cliente_id=cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("1000.00"),
            iva=Decimal("220.00"),
            totale=Decimal("1220.00"),
        )
        runtime_session.add(fattura)
        runtime_session.flush()
        runtime_session.add(
            RigaFattura(
                fattura_id=fattura.id,
                numero_riga=1,
                descrizione="Consulenza sviluppo software",
                quantita=Decimal("1"),
                prezzo_unitario=Decimal("1000.00"),
                unita_misura="servizio",
                aliquota_iva=Decimal("22.00"),
                imponibile=Decimal("1000.00"),
                iva=Decimal("220.00"),
                totale=Decimal("1220.00"),
            )
        )
        runtime_session.commit()
        runtime_session.refresh(fattura)

        xml_path = tmp_path / "test_invoice.xml"

        # The official FatturaPA XSD is not bundled in the test environment, so
        # XSD validation is skipped (--no-validate); the builder still produces
        # the XML document under test.
        result = app_runner.invoke(
            app,
            ["fattura", "xml", str(fattura.id), "--output", str(xml_path), "--no-validate"],
        )

        assert result.exit_code == 0
        assert "XML saved to" in result.output
        assert xml_path.exists()
        assert "<?xml" in xml_path.read_text(encoding="utf-8")


class TestPaymentCLIE2E:
    """Test payment reconciliation workflow via CLI."""

    def test_import_bank_statement_via_app(self, app_runner, runtime_session, tmp_path):
        """Test importing a bank statement (real CSV file) through CLI."""
        # A bank account must exist; the import command references it by id.
        account = BankAccount(
            name="Test Account",
            iban="IT60X0542811101000000123456",
            bank_name="Test Bank",
            currency="EUR",
        )
        runtime_session.add(account)
        runtime_session.commit()
        runtime_session.refresh(account)
        account_id = account.id

        # Default CSV layout expected by the importer: Date/Amount/Description/
        # Reference, comma-delimited, ISO dates, dot decimals.
        csv_content = (
            "Date,Amount,Description,Reference\n"
            "2025-01-15,1000.00,Pagamento fattura,INV-2025-001\n"
            "2025-01-16,500.00,Bonifico ricevuto,INV-2025-002\n"
        )
        csv_path = tmp_path / "statement.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = app_runner.invoke(
            app,
            ["payment", "import", str(csv_path), "--account", str(account_id), "--no-auto-match"],
        )

        assert result.exit_code == 0
        # The importer auto-detected the CSV format and parsed both rows; assert
        # on the rendered results table (Success=2, Errors=0). Collapse the Rich
        # table whitespace so the metric/value pairs are matchable.
        assert "Import Results" in result.output
        assert "CSVImporter" in result.output  # format auto-detected
        # Drop Rich box-drawing glyphs, then collapse whitespace so each
        # "<metric> <count>" pair is matchable.
        stripped = result.output.translate({ord(ch): " " for ch in "│┃┏┓┗┛┡┩╇━┳┻┠┨┯┷┌┐└┘├┤┬┴"})
        collapsed = " ".join(stripped.split())
        assert "Success 2" in collapsed
        assert "Errors 0" in collapsed
        assert "Total 2" in collapsed

        # Sanity: the seeded account is the one the command resolved.
        assert runtime_session.query(BankAccount).filter_by(id=account_id).first() is not None

    def test_payment_reconciliation_via_app(self, app_runner, runtime_session):
        """Test payment reconciliation through CLI with no transactions."""
        account = BankAccount(
            name="Recon Account",
            iban="IT60X0542811101000000654321",
            bank_name="Test Bank",
            currency="EUR",
        )
        runtime_session.add(account)
        runtime_session.commit()
        runtime_session.refresh(account)

        result = app_runner.invoke(app, ["payment", "reconcile", "--account", str(account.id)])

        # Runs cleanly even with nothing to reconcile.
        assert result.exit_code == 0
        assert "Reconciliation Summary" in result.output


class TestAIAssistanceE2E:
    """Test AI assistance workflows via CLI."""

    def test_ai_describe_invoice_via_app(self, app_runner, runtime_db):
        """Test AI invoice description through CLI (provider mocked)."""
        provider = _mock_ai_provider(
            "Consulenza informatica specializzata in sviluppo web e mobile."
        )

        # The command binds ``create_provider`` into its own module namespace,
        # so the patch target is that module — not the factory module.
        with patch(
            "openfatture.cli.commands.ai.describe.create_provider",
            return_value=provider,
        ):
            result = app_runner.invoke(
                app, ["ai", "describe", "3 hours web development consulting"]
            )

        assert result.exit_code == 0
        assert "Consulenza informatica" in result.output

    def test_ai_tax_advice_via_app(self, app_runner, runtime_db):
        """Test AI tax advice through CLI (provider mocked)."""
        provider = _mock_ai_provider(
            "Per servizi di consulenza IT, applicare aliquota IVA 22% con regime ordinario."
        )

        with patch(
            "openfatture.cli.commands.ai.vat.create_provider",
            return_value=provider,
        ):
            result = app_runner.invoke(app, ["ai", "suggest-vat", "IT consulting services"])

        assert result.exit_code == 0
        assert "22%" in result.output


class TestBatchOperationsE2E:
    """Test batch operations via CLI."""

    def test_batch_import_invoices_via_app(self, app_runner, runtime_session, tmp_path):
        """Test batch importing invoices through CLI."""
        client1 = Cliente(
            denominazione="Batch Client 1",
            partita_iva="11111111111",
            codice_destinatario="BTC001",
            nazione="IT",
        )
        client2 = Cliente(
            denominazione="Batch Client 2",
            partita_iva="22222222222",
            codice_destinatario="BTC002",
            nazione="IT",
        )
        runtime_session.add(client1)
        runtime_session.add(client2)
        runtime_session.commit()
        runtime_session.refresh(client1)
        runtime_session.refresh(client2)

        # The batch importer requires: numero,anno,cliente_id,descrizione,
        # quantita,prezzo[,aliquota_iva]. cliente_id references real seeded rows.
        csv_content = (
            "numero,anno,cliente_id,descrizione,quantita,prezzo,aliquota_iva\n"
            f"001,2025,{client1.id},Batch Service 1,10,100.00,22.00\n"
            f"002,2025,{client2.id},Batch Service 2,5,200.00,22.00\n"
        )
        csv_path = tmp_path / "invoices.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = app_runner.invoke(app, ["batch", "import", str(csv_path)])

        assert result.exit_code == 0
        assert "All invoices imported successfully" in result.output

        invoices = runtime_session.query(Fattura).filter_by(anno=2025).all()
        assert len(invoices) >= 2

    def test_batch_create_invoices_via_app(self, app_runner, runtime_session, tmp_path):
        """Test batch creating invoices for a single client through CLI."""
        cliente = Cliente(
            denominazione="Batch Invoice Client",
            partita_iva="12345678901",
            codice_destinatario="BTCINV",
            nazione="IT",
        )
        runtime_session.add(cliente)
        runtime_session.commit()
        runtime_session.refresh(cliente)

        csv_content = (
            "numero,anno,cliente_id,descrizione,quantita,prezzo,aliquota_iva\n"
            f"001,2025,{cliente.id},Batch Service 1,10,100.00,22.00\n"
            f"002,2025,{cliente.id},Batch Service 2,5,200.00,22.00\n"
        )
        csv_path = tmp_path / "invoices.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = app_runner.invoke(app, ["batch", "import", str(csv_path)])

        assert result.exit_code == 0
        assert "All invoices imported successfully" in result.output

        invoices = runtime_session.query(Fattura).filter_by(anno=2025).all()
        assert len(invoices) >= 2


class TestCompleteWorkflowE2E:
    """Test complete end-to-end workflows combining multiple features."""

    def test_full_invoice_lifecycle_via_app(self, app_runner, runtime_session, tmp_path):
        """Test invoice lifecycle: create -> generate XML -> send (mocked PEC)."""
        cliente = Cliente(
            denominazione="Full Lifecycle Client",
            partita_iva="12345678901",
            codice_fiscale="FLC00180A01H501Y",
            codice_destinatario="FLC001",
            indirizzo="Via Lifecycle 1",
            numero_civico="1",
            cap="20100",
            comune="Milano",
            provincia="MI",
            nazione="IT",
        )
        runtime_session.add(cliente)
        runtime_session.commit()
        runtime_session.refresh(cliente)
        cliente_id = cliente.id

        # 1. Create invoice (interactive wizard). Passing --cliente skips the
        #    client picker; remaining prompts: number, issue date, then one line
        #    item (description, quantity, unit price, VAT), an empty description
        #    to stop, then "no" to the ritenuta d'acconto question.
        result1 = app_runner.invoke(
            app,
            ["fattura", "crea", "--cliente", str(cliente_id)],
            input="\n".join(
                [
                    "2025-01-15",  # issue date (ISO) - prompted first
                    "100",  # invoice number
                    "Full lifecycle consulting",  # line 1 description
                    "1",  # quantity
                    "1000.00",  # unit price
                    "22.00",  # VAT rate
                    "",  # empty description -> stop adding lines
                    "n",  # no ritenuta d'acconto
                ]
            ),
        )

        assert result1.exit_code == 0
        assert "Invoice created successfully" in result1.output

        # The invoice year is derived from the entered issue date.
        fattura = runtime_session.query(Fattura).filter_by(numero="100", anno=2025).first()
        assert fattura is not None
        fattura_id = fattura.id

        # 2. Generate XML (validation skipped: official XSD not bundled).
        xml_path = tmp_path / "fattura_100.xml"
        result2 = app_runner.invoke(
            app,
            ["fattura", "xml", str(fattura_id), "--output", str(xml_path), "--no-validate"],
        )

        assert result2.exit_code == 0
        assert xml_path.exists()

        # 3. Send invoice. The PEC boundary and the XSD-dependent validation are
        #    mocked so the command exercises the send flow without network/XSD.
        with (
            patch(
                "openfatture.core.fatture.service.InvoiceService.generate_xml",
                return_value=("<FatturaElettronica/>", None),
            ),
            patch(
                "openfatture.utils.email.sender.TemplatePECSender.send_invoice_to_sdi",
                return_value=(True, None),
            ),
        ):
            result3 = app_runner.invoke(
                app,
                ["fattura", "invia", str(fattura_id)],
                input="y\n",  # confirm "Send invoice to SDI now?"
            )

        assert result3.exit_code == 0
        assert "Invoice sent to SDI via PEC" in result3.output
