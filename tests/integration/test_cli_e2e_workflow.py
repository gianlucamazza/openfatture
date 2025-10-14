"""
End-to-end integration tests for CLI workflows.

Tests complete user journeys through the command-line interface:
- Invoice creation and management
- Client management
- Payment reconciliation
- AI assistance
- Batch operations

These tests use the actual CLI commands and verify the full workflow.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from openfatture.cli.main import app
from openfatture.storage.database import get_db, init_db
from openfatture.storage.database.models import Cliente, Fattura, StatoFattura, TipoDocumento
from openfatture.utils.config import get_settings


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    init_db("sqlite:///:memory:")
    session = next(get_db())
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def app_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_config():
    """Create a temporary config file."""
    config_data = {
        "cedente": {
            "denominazione": "Test Company S.r.l.",
            "partita_iva": "12345678901",
            "codice_fiscale": "TSTCMP80A01H501Y",
            "regime_fiscale": "RF01",
            "indirizzo": "Via Test 123",
            "numero_civico": "123",
            "cap": "20100",
            "comune": "Milano",
            "provincia": "MI",
            "nazione": "IT",
        },
        "sdi": {
            "pec_address": "test@pec.fatturapa.it",
            "pec_username": "test@example.com",
            "pec_password": "testpass",
        },
        "ai": {
            "provider": "openai",
            "openai_api_key": "sk-test-key",
            "openai_model": "gpt-4",
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        config_path = Path(f.name)

    yield config_path
    config_path.unlink()


class TestInvoiceCLIE2E:
    """Test complete invoice creation and management workflow via CLI."""

    def test_create_appent_via_app(self, app_runner, db_session, temp_config):
        """Test creating a appent through CLI."""
        with patch("openfatture.utils.config.get_settings") as mock_settings:
            mock_settings.return_value.archivio_dir = Path("/tmp/test")

            # Create appent interactively
            result = app_runner.invoke(
                app,
                ["appente", "crea"],
                input="\n".join(
                    [
                        "Test Client SRL",  # denominazione
                        "12345678901",  # partita_iva
                        "TSTCLT80A01H501Y",  # codice_fiscale
                        "ABC1234",  # codice_destinatario
                        "Via Roma 1",  # indirizzo
                        "1",  # numero_civico
                        "20100",  # cap
                        "Milano",  # comune
                        "MI",  # provincia
                        "",  # email (optional)
                        "",  # pec (optional)
                        "",  # telefono (optional)
                        "",  # note (optional)
                    ]
                ),
            )

            assert result.exit_code == 0
            assert "Cliente creato con successo" in result.output

            # Verify appent was created
            appente = db_session.query(Cliente).filter_by(denominazione="Test Client SRL").first()
            assert appente is not None
            assert appente.partita_iva == "12345678901"

    def test_create_invoice_via_app(self, app_runner, db_session, temp_config):
        """Test creating an invoice through CLI."""
        # First create a appent
        appente = Cliente(
            denominazione="CLI Test Client",
            partita_iva="12345678901",
            codice_fiscale="CLITST80A01H501Y",
            codice_destinatario="CLITST",
            indirizzo="Via CLI 1",
            numero_civico="1",
            cap="20100",
            comune="Milano",
            provincia="MI",
        )
        db_session.add(appente)
        db_session.commit()

        with patch("openfatture.utils.config.get_settings") as mock_settings:
            mock_settings.return_value.archivio_dir = Path("/tmp/test")

            # Create invoice interactively
            result = app_runner.invoke(
                app,
                ["fattura", "crea"],
                input="\n".join(
                    [
                        "001",  # numero
                        "2025",  # anno
                        "15/01/2025",  # data_emissione
                        "CLI Test Client",  # appente (search)
                        "1",  # select appent
                        "TD01",  # tipo_documento
                        "Consulenza IT",  # descrizione riga 1
                        "10",  # quantita
                        "100.00",  # prezzo_unitario
                        "ore",  # unita_misura
                        "22.00",  # aliquota_iva
                        "",  # note fattura
                        "",  # add another line? (no)
                    ]
                ),
            )

            assert result.exit_code == 0
            assert "Fattura creata con successo" in result.output

            # Verify invoice was created
            fattura = db_session.query(Fattura).filter_by(numero="001", anno=2025).first()
            assert fattura is not None
            assert fattura.totale == 1220.00  # 1000 + 220 IVA

    def test_list_invoices_via_app(self, app_runner, db_session, temp_config):
        """Test listing invoices through CLI."""
        # Create test data
        appente = Cliente(
            denominazione="List Test Client",
            partita_iva="12345678901",
            codice_destinatario="LIST01",
        )
        db_session.add(appente)
        db_session.commit()

        fattura = Fattura(
            numero="001",
            anno=2025,
            data_emissione="2025-01-15",
            appente_id=appente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=1000.00,
            iva=220.00,
            totale=1220.00,
        )
        db_session.add(fattura)
        db_session.commit()

        with patch("openfatture.utils.config.get_settings") as mock_settings:
            mock_settings.return_value.archivio_dir = Path("/tmp/test")

            result = app_runner.invoke(app, ["fattura", "lista"])

            assert result.exit_code == 0
            assert "001/2025" in result.output
            assert "List Test Client" in result.output
            assert "BOZZA" in result.output

    def test_generate_pdf_via_app(self, app_runner, db_session, temp_config, tmp_path):
        """Test PDF generation through CLI."""
        # Create test invoice
        appente = Cliente(
            denominazione="PDF Test Client",
            partita_iva="12345678901",
            codice_destinatario="PDF001",
        )
        db_session.add(appente)
        db_session.commit()

        fattura = Fattura(
            numero="PDF001",
            anno=2025,
            data_emissione="2025-01-15",
            appente_id=appente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=1000.00,
            iva=220.00,
            totale=1220.00,
        )
        db_session.add(fattura)
        db_session.commit()

        pdf_path = tmp_path / "test_invoice.pdf"

        with patch("openfatture.utils.config.get_settings") as mock_settings:
            mock_settings.return_value.archivio_dir = Path("/tmp/test")

            result = app_runner.invoke(app, ["fattura", "pdf", "PDF001", "--output", str(pdf_path)])

            assert result.exit_code == 0
            assert "PDF generato" in result.output
            assert pdf_path.exists()


class TestPaymentCLIE2E:
    """Test payment reconciliation workflow via CLI."""

    def test_import_bank_statement_via_app(self, app_runner, db_session, tmp_path):
        """Test importing bank statements through CLI."""
        # Create CSV file
        csv_content = """Data;Importo;Descrizione;Riferimento
15/01/2025;1000,00;Pagamento fattura;INV-2025-001
16/01/2025;500,00;Bonifico ricevuto;INV-2025-002"""

        csv_path = tmp_path / "statement.csv"
        csv_path.write_text(csv_content)

        with patch("openfatture.utils.config.get_settings") as mock_settings:
            mock_settings.return_value.archivio_dir = Path("/tmp/test")

            result = app_runner.invoke(
                app,
                [
                    "payment",
                    "import",
                    str(csv_path),
                    "--format",
                    "csv",
                    "--iban",
                    "IT1234567890123456789012345",
                ],
            )

            assert result.exit_code == 0
            assert "Transazioni importate" in result.output

    def test_payment_reconciliation_via_app(self, app_runner, db_session, temp_config):
        """Test payment reconciliation through CLI."""
        with patch("openfatture.utils.config.get_settings") as mock_settings:
            mock_settings.return_value.archivio_dir = Path("/tmp/test")

            result = app_runner.invoke(app, ["payment", "reconcile"])

            # Should run without errors (even if no transactions to reconcile)
            assert result.exit_code == 0


class TestAIAssistanceE2E:
    """Test AI assistance workflows via CLI."""

    @patch("openfatture.ai.providers.factory.LLMProviderFactory.create_provider")
    def test_ai_describe_invoice_via_app(self, mock_factory, app_runner, temp_config):
        """Test AI invoice description through CLI."""
        # Mock AI provider
        mock_provider = MagicMock()
        mock_provider.generate.return_value = (
            "Consulenza informatica specializzata in sviluppo web e mobile."
        )
        mock_factory.return_value = mock_provider

        with patch("openfatture.utils.config.get_settings") as mock_settings:
            mock_settings.return_value.archivio_dir = Path("/tmp/test")

            result = app_runner.invoke(
                app, ["ai", "describe", "3 hours web development consulting"]
            )

            assert result.exit_code == 0
            assert "Consulenza informatica" in result.output

    @patch("openfatture.ai.providers.factory.LLMProviderFactory.create_provider")
    def test_ai_tax_advice_via_app(self, mock_factory, app_runner, temp_config):
        """Test AI tax advice through CLI."""
        # Mock AI provider
        mock_provider = MagicMock()
        mock_provider.generate.return_value = (
            "Per servizi di consulenza IT, applicare aliquota IVA 22% con regime ordinario."
        )
        mock_factory.return_value = mock_provider

        with patch("openfatture.utils.config.get_settings") as mock_settings:
            mock_settings.return_value.archivio_dir = Path("/tmp/test")

            result = app_runner.invoke(app, ["ai", "suggest-vat", "IT consulting services"])

            assert result.exit_code == 0
            assert "22%" in result.output


class TestBatchOperationsE2E:
    """Test batch operations via CLI."""

    def test_batch_import_appents_via_app(self, app_runner, db_session, tmp_path, temp_config):
        """Test batch importing appents through CLI."""
        # Create CSV file
        csv_content = """denominazione,partita_iva,codice_fiscale,codice_destinatario,indirizzo,cap,comune,provincia
Batch Client 1,11111111111,BTC00180A01H501Y,BTC001,Via Batch 1,20100,Milano,MI
Batch Client 2,22222222222,BTC00280A01H501Y,BTC002,Via Batch 2,20100,Milano,MI"""

        csv_path = tmp_path / "appents.csv"
        csv_path.write_text(csv_content)

        with patch("openfatture.utils.config.get_settings") as mock_settings:
            mock_settings.return_value.archivio_dir = Path("/tmp/test")

            result = app_runner.invoke(app, ["batch", "import-appents", str(csv_path)])

            assert result.exit_code == 0
            assert "Clienti importati" in result.output

            # Verify appents were created
            appents = (
                db_session.query(Cliente).filter(Cliente.denominazione.like("Batch Client%")).all()
            )
            assert len(appents) == 2

    def test_batch_create_invoices_via_app(self, app_runner, db_session, tmp_path, temp_config):
        """Test batch creating invoices through CLI."""
        # Create appents first
        appente = Cliente(
            denominazione="Batch Invoice Client",
            partita_iva="12345678901",
            codice_destinatario="BTCINV",
        )
        db_session.add(appente)
        db_session.commit()

        # Create CSV file
        csv_content = """numero,anno,data_emissione,appente,descrizione,quantita,prezzo_unitario,unita_misura,aliquota_iva
001,2025,15/01/2025,Batch Invoice Client,Batch Service 1,10,100.00,ore,22.00
002,2025,16/01/2025,Batch Invoice Client,Batch Service 2,5,200.00,ore,22.00"""

        csv_path = tmp_path / "invoices.csv"
        csv_path.write_text(csv_content)

        with patch("openfatture.utils.config.get_settings") as mock_settings:
            mock_settings.return_value.archivio_dir = Path("/tmp/test")

            result = app_runner.invoke(app, ["batch", "create-invoices", str(csv_path)])

            assert result.exit_code == 0
            assert "Fatture create" in result.output

            # Verify invoices were created
            invoices = db_session.query(Fattura).filter_by(anno=2025).all()
            assert len(invoices) >= 2


class TestCompleteWorkflowE2E:
    """Test complete end-to-end workflows combining multiple features."""

    def test_full_invoice_lifecycle_via_app(self, app_runner, db_session, tmp_path, temp_config):
        """Test complete invoice lifecycle: create → generate PDF → send."""
        # Create appent
        appente = Cliente(
            denominazione="Full Lifecycle Client",
            partita_iva="12345678901",
            codice_fiscale="FLC00180A01H501Y",
            codice_destinatario="FLC001",
            indirizzo="Via Lifecycle 1",
            numero_civico="1",
            cap="20100",
            comune="Milano",
            provincia="MI",
        )
        db_session.add(appente)
        db_session.commit()

        invoice_num = "FLC001"
        pdf_path = tmp_path / f"fattura_{invoice_num}.pdf"

        with (
            patch("openfatture.utils.config.get_settings") as mock_settings,
            patch("openfatture.sdi.pec_sender.sender.PECSender.send_invoice") as mock_send,
        ):
            mock_settings.return_value.archivio_dir = Path("/tmp/test")
            mock_send.return_value = (True, None)

            # 1. Create invoice
            result1 = app_runner.invoke(
                app,
                ["fattura", "crea"],
                input="\n".join(
                    [
                        invoice_num,  # numero
                        "2025",  # anno
                        "15/01/2025",  # data_emissione
                        "Full Lifecycle Client",  # appente
                        "1",  # select appent
                        "TD01",  # tipo_documento
                        "Full lifecycle test",  # descrizione
                        "1",  # quantita
                        "1000.00",  # prezzo_unitario
                        "servizio",  # unita_misura
                        "22.00",  # aliquota_iva
                        "",  # note
                        "",  # another line? (no)
                    ]
                ),
            )

            assert result1.exit_code == 0
            assert "Fattura creata" in result1.output

            # 2. Generate PDF
            result2 = app_runner.invoke(
                app, ["fattura", "pdf", invoice_num, "--output", str(pdf_path)]
            )

            assert result2.exit_code == 0
            assert pdf_path.exists()

            # 3. Validate invoice
            result3 = app_runner.invoke(app, ["fattura", "valida", invoice_num])

            assert result3.exit_code == 0
            assert "valid" in result3.output.lower()

            # 4. Send invoice (mocked)
            result4 = app_runner.invoke(app, ["pec", "invia", invoice_num])

            assert result4.exit_code == 0
            assert "inviata" in result4.output.lower()

            # Verify final state
            fattura = db_session.query(Fattura).filter_by(numero=invoice_num, anno=2025).first()
            assert fattura.stato == StatoFattura.INVIATA
