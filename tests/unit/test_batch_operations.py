"""Unit tests for batch operations."""

from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, PropertyMock

import pytest

from openfatture.billing.batch.operations import (
    bulk_update_status,
    export_invoices_csv,
    import_invoices_csv,
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
    fattura.issued_elsewhere = False
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

    def test_import_success(self, tmp_path, db_session, sample_cliente):
        """Valid rows are imported and committed."""
        csv_path = tmp_path / "import.csv"
        csv_path.write_text(
            "numero,anno,data_emissione,cliente_id,imponibile,iva,totale,note\n"
            f"001,2025,2025-10-09,{sample_cliente.id},100.00,22.00,122.00,Test\n"
            f"002,2025,2025-10-10,{sample_cliente.id},200.00,44.00,244.00,Test2\n",
            encoding="utf-8",
        )

        result = import_invoices_csv(csv_path, db_session)

        assert (result.total, result.succeeded, result.failed) == (2, 2, 0)
        assert db_session.query(Fattura).count() == 2

    def test_duplicate_row_does_not_discard_valid_rows(self, tmp_path, db_session, sample_cliente):
        """A rejected row is reported; the other rows are still committed."""
        csv_path = tmp_path / "import.csv"
        csv_path.write_text(
            "numero,anno,data_emissione,cliente_id,imponibile,iva,totale\n"
            f"1,2026,2026-01-10,{sample_cliente.id},100,22,122\n"
            f"1,2026,2026-01-11,{sample_cliente.id},50,11,61\n"
            f"2,2026,2026-01-12,{sample_cliente.id},10,2.2,12.2\n",
            encoding="utf-8",
        )

        result = import_invoices_csv(csv_path, db_session)

        assert (result.succeeded, result.failed) == (2, 1)
        assert result.errors == ["Row 2: Invoice 1/2026 already exists"]
        stored = {(f.numero, f.anno) for f in db_session.query(Fattura).all()}
        assert stored == {("1", 2026), ("2", 2026)}

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


class TestBulkUpdateStatus:
    """Tests for bulk_update_status."""

    def test_bulk_update_success(self, mock_fattura):
        """Test successful bulk status update."""
        invoices = [mock_fattura]
        db_session = Mock()

        result = bulk_update_status(invoices, StatoFattura.BOZZA, db_session)

        assert result.succeeded == 1
        assert result.failed == 0
        assert mock_fattura.stato == StatoFattura.BOZZA
        assert db_session.commit.called

    def test_bulk_update_with_errors(self):
        """Test bulk update with some failures."""
        # Create a mock that raises on status change
        mock_invoice = Mock()
        type(mock_invoice).stato = PropertyMock(side_effect=ValueError("Update failed"))
        mock_invoice.numero = "001"
        mock_invoice.anno = 2025

        invoices: list[Fattura] = [mock_invoice]
        db_session = Mock()

        result = bulk_update_status(invoices, StatoFattura.BOZZA, db_session)

        assert result.failed == 1
        db_session.commit.assert_not_called()
        db_session.rollback.assert_called_once()

    def test_bulk_update_rollback_on_commit_error(self, mock_fattura):
        """Test rollback on commit error."""
        invoices = [mock_fattura]
        db_session = Mock()
        db_session.commit.side_effect = Exception("Commit failed")

        result = bulk_update_status(invoices, StatoFattura.BOZZA, db_session)

        assert result.failed > 0
        assert db_session.rollback.called
