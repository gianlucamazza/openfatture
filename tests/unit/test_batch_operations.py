"""Unit tests for batch operations."""

from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, PropertyMock

import pytest

from openfatture.core.batch.operations import (
    bulk_update_status,
    export_invoices_csv,
    import_invoices_csv,
    send_batch,
    validate_batch,
)
from openfatture.storage.database.models import Cliente, Fattura, RigaFattura, StatoFattura

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_cliente():
    """Create mock client."""
    cliente = Mock(spec=Cliente)
    cliente.id = 1
    cliente.denominazione = "Test Client"
    cliente.partita_iva = "12345678901"
    return cliente


@pytest.fixture
def mock_fattura(mock_cliente):
    """Create mock invoice."""
    fattura = Mock(spec=Fattura)
    fattura.id = 1
    fattura.numero = "001"
    fattura.anno = 2025
    fattura.data_emissione = date(2025, 10, 9)
    fattura.cliente_id = 1
    fattura.cliente = mock_cliente
    fattura.imponibile = Decimal("100.00")
    fattura.iva = Decimal("22.00")
    fattura.totale = Decimal("122.00")
    fattura.note = "Test note"
    fattura.stato = StatoFattura.BOZZA
    fattura.righe = []
    return fattura


@pytest.fixture
def mock_riga():
    """Create mock invoice line."""
    riga = Mock(spec=RigaFattura)
    riga.descrizione = "Test product"
    riga.quantita = Decimal("2.0")
    riga.prezzo_unitario = Decimal("50.00")
    riga.aliquota_iva = Decimal("22.0")
    return riga


class TestExportInvoicesCSV:
    """Tests for export_invoices_csv."""

    def test_export_summary_only(self, mock_fattura, tmp_path):
        """Test exporting invoices without lines."""
        output_path = tmp_path / "export.csv"
        invoices = [mock_fattura]

        success, error = export_invoices_csv(invoices, output_path, include_lines=False)

        assert success is True
        assert error is None
        assert output_path.exists()

        # Verify CSV content
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
            assert "numero,anno,data_emissione,cliente,stato" in content
            assert "001,2025,2025-10-09" in content
            assert "Test Client" in content
            assert "Test note" in content

    def test_export_with_lines(self, mock_fattura, mock_riga, tmp_path):
        """Test exporting invoices with lines."""
        output_path = tmp_path / "export_lines.csv"
        mock_fattura.righe = [mock_riga]
        invoices = [mock_fattura]

        success, error = export_invoices_csv(invoices, output_path, include_lines=True)

        assert success is True
        assert error is None
        assert output_path.exists()

        # Verify CSV content includes line data
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
            assert "riga_descrizione,riga_quantita" in content
            assert "Test product" in content

    def test_export_without_lines(self, mock_fattura, tmp_path):
        """Test exporting invoice without lines (empty righe)."""
        output_path = tmp_path / "export_no_lines.csv"
        mock_fattura.righe = []
        invoices = [mock_fattura]

        success, error = export_invoices_csv(invoices, output_path, include_lines=True)

        assert success is True
        assert error is None

    def test_export_error(self, mock_fattura):
        """Test export error handling."""
        invalid_path = Path("/invalid/path/export.csv")
        invoices = [mock_fattura]

        success, error = export_invoices_csv(invoices, invalid_path)

        assert success is False
        assert error is not None
        assert "Export failed" in error


class TestImportInvoicesCSV:
    """Tests for import_invoices_csv."""

    def test_import_success(self, tmp_path, mock_cliente):
        """Test successful CSV import."""
        # Create CSV file
        csv_path = tmp_path / "import.csv"
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("numero,anno,data_emissione,cliente_id,imponibile,iva,totale,note\n")
            f.write("001,2025,2025-10-09,1,100.00,22.00,122.00,Test\n")
            f.write("002,2025,2025-10-10,1,200.00,44.00,244.00,Test2\n")

        # Mock database session
        db_session = Mock()
        db_session.query.return_value.filter.return_value.first.return_value = mock_cliente

        result = import_invoices_csv(csv_path, db_session, default_cliente_id=1)

        assert result.total == 2
        assert result.succeeded == 2
        assert result.failed == 0
        assert db_session.add.call_count == 2
        assert db_session.commit.called

    def test_import_with_errors(self, tmp_path):
        """Test import with invalid data."""
        # Create CSV with invalid data
        csv_path = tmp_path / "import_error.csv"
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("numero,anno,data_emissione,cliente_id,imponibile,iva,totale\n")
            f.write("001,invalid,2025-10-09,1,100.00,22.00,122.00\n")

        db_session = Mock()

        result = import_invoices_csv(csv_path, db_session)

        assert result.total == 1
        assert result.failed == 1
        assert len(result.errors) == 1
        assert db_session.rollback.called

    def test_import_client_not_found(self, tmp_path):
        """Test import with non-existent client."""
        csv_path = tmp_path / "import_no_client.csv"
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("numero,anno,data_emissione,cliente_id,imponibile,iva,totale\n")
            f.write("001,2025,2025-10-09,999,100.00,22.00,122.00\n")

        db_session = Mock()
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = import_invoices_csv(csv_path, db_session)

        assert result.failed == 1
        assert "Client 999 not found" in result.errors[0]

    def test_import_file_not_found(self):
        """Test import with non-existent file."""
        csv_path = Path("/invalid/path.csv")
        db_session = Mock()

        result = import_invoices_csv(csv_path, db_session)

        assert result.failed > 0
        assert db_session.rollback.called


class TestValidateBatch:
    """Tests for validate_batch."""

    def test_validate_success(self, mock_fattura, mock_riga):
        """Test successful batch validation."""
        mock_fattura.righe = [mock_riga]
        invoices = [mock_fattura]

        result = validate_batch(invoices)

        assert result.total == 1
        assert result.succeeded == 1
        assert result.failed == 0

    def test_validate_no_client(self, mock_fattura):
        """Test validation fails with no client."""
        mock_fattura.cliente = None
        invoices = [mock_fattura]

        result = validate_batch(invoices)

        assert result.failed == 1
        assert "no client" in result.errors[0].lower()

    def test_validate_negative_total(self, mock_fattura, mock_riga):
        """Test validation fails with negative total."""
        mock_fattura.righe = [mock_riga]
        mock_fattura.totale = Decimal("-10.00")
        invoices = [mock_fattura]

        result = validate_batch(invoices)

        assert result.failed == 1
        assert "positive" in result.errors[0].lower()

    def test_validate_no_lines(self, mock_fattura):
        """Test validation fails with no lines."""
        mock_fattura.righe = []
        invoices = [mock_fattura]

        result = validate_batch(invoices)

        assert result.failed == 1
        assert "no lines" in result.errors[0].lower()

    def test_validate_with_xsd(self, mock_fattura, mock_riga):
        """Test validation with XSD validator."""
        mock_fattura.righe = [mock_riga]
        invoices = [mock_fattura]

        # Mock XML generator and validator
        xml_generator = Mock(return_value=b"<xml>test</xml>")
        validator = Mock()
        validator.validate.return_value = (True, None)

        result = validate_batch(invoices, xml_generator=xml_generator, validator=validator)

        assert result.succeeded == 1
        assert xml_generator.called
        assert validator.validate.called

    def test_validate_xsd_failure(self, mock_fattura, mock_riga):
        """Test validation fails with XSD errors."""
        mock_fattura.righe = [mock_riga]
        invoices = [mock_fattura]

        xml_generator = Mock(return_value=b"<xml>test</xml>")
        validator = Mock()
        validator.validate.return_value = (False, "XSD validation error")

        result = validate_batch(invoices, xml_generator=xml_generator, validator=validator)

        assert result.failed == 1
        assert "XSD validation" in result.errors[0]


class TestSendBatch:
    """Tests for send_batch."""

    def test_send_success(self, mock_fattura, tmp_path):
        """Test successful batch sending."""
        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text("<xml>test</xml>")

        pec_sender = Mock()
        pec_sender.send_invoice.return_value = (True, None)

        invoices = [mock_fattura]
        xml_paths = [xml_path]

        result = send_batch(invoices, pec_sender, xml_paths)

        assert result.total == 1
        assert result.succeeded == 1
        assert result.failed == 0
        assert pec_sender.send_invoice.called

    def test_send_with_errors(self, mock_fattura, tmp_path):
        """Test sending with some failures."""
        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text("<xml>test</xml>")

        pec_sender = Mock()
        pec_sender.send_invoice.return_value = (False, "Send failed")

        invoices = [mock_fattura]
        xml_paths = [xml_path]

        result = send_batch(invoices, pec_sender, xml_paths)

        assert result.failed == 1
        assert len(result.errors) == 1

    def test_send_mismatch_length(self, mock_fattura, tmp_path):
        """Test sending with mismatched invoice/path counts."""
        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text("<xml>test</xml>")

        pec_sender = Mock()
        invoices = [mock_fattura]
        xml_paths = [xml_path, xml_path]  # Too many paths

        result = send_batch(invoices, pec_sender, xml_paths)

        assert result.failed > 0
        assert "Mismatch" in result.errors[0]


class TestBulkUpdateStatus:
    """Tests for bulk_update_status."""

    def test_bulk_update_success(self, mock_fattura):
        """Test successful bulk status update."""
        invoices = [mock_fattura]
        db_session = Mock()

        result = bulk_update_status(invoices, StatoFattura.INVIATA, db_session)

        assert result.succeeded == 1
        assert result.failed == 0
        assert mock_fattura.stato == StatoFattura.INVIATA
        assert db_session.commit.called

    def test_bulk_update_with_errors(self):
        """Test bulk update with some failures."""
        # Create a mock that raises on status change
        mock_invoice = Mock()
        type(mock_invoice).stato = PropertyMock(side_effect=ValueError("Update failed"))
        mock_invoice.numero = "001"
        mock_invoice.anno = 2025

        invoices = [mock_invoice]
        db_session = Mock()

        result = bulk_update_status(invoices, StatoFattura.INVIATA, db_session)

        assert result.failed == 1
        assert db_session.commit.called

    def test_bulk_update_rollback_on_commit_error(self, mock_fattura):
        """Test rollback on commit error."""
        invoices = [mock_fattura]
        db_session = Mock()
        db_session.commit.side_effect = Exception("Commit failed")

        result = bulk_update_status(invoices, StatoFattura.INVIATA, db_session)

        assert result.failed > 0
        assert db_session.rollback.called
