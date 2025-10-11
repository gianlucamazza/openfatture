"""
Tests for report CLI commands.
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from openfatture.cli.commands.report import app
from openfatture.storage.database.models import StatoPagamento

runner = CliRunner()
pytestmark = pytest.mark.unit


class TestReportIVACommand:
    """Test 'report iva' command."""

    @patch("openfatture.cli.commands.report.SessionLocal")
    @patch("openfatture.cli.commands.report.init_db")
    def test_report_iva_no_data(self, mock_init_db, mock_session_local):
        """Test VAT report with no data."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = runner.invoke(app, ["iva", "--anno", "2025"])

        assert result.exit_code == 0
        assert "No invoices found" in result.stdout

    @patch("openfatture.cli.commands.report.SessionLocal")
    @patch("openfatture.cli.commands.report.init_db")
    def test_report_iva_with_data(self, mock_init_db, mock_session_local):
        """Test VAT report with invoice data."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Create mock invoices with righe
        mock_fattura1 = Mock()
        mock_fattura1.imponibile = Decimal("1000.00")
        mock_fattura1.iva = Decimal("220.00")
        mock_fattura1.totale = Decimal("1220.00")
        mock_riga1 = Mock()
        mock_riga1.aliquota_iva = Decimal("22")
        mock_riga1.imponibile = Decimal("1000.00")
        mock_riga1.iva = Decimal("220.00")
        mock_fattura1.righe = [mock_riga1]

        mock_fattura2 = Mock()
        mock_fattura2.imponibile = Decimal("500.00")
        mock_fattura2.iva = Decimal("110.00")
        mock_fattura2.totale = Decimal("610.00")
        mock_riga2 = Mock()
        mock_riga2.aliquota_iva = Decimal("22")
        mock_riga2.imponibile = Decimal("500.00")
        mock_riga2.iva = Decimal("110.00")
        mock_fattura2.righe = [mock_riga2]

        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [
            mock_fattura1,
            mock_fattura2,
        ]

        result = runner.invoke(app, ["iva", "--anno", "2025"])

        assert result.exit_code == 0
        assert "VAT Report" in result.stdout
        assert "VAT Summary" in result.stdout
        assert "1,500" in result.stdout  # Total imponibile
        assert "330" in result.stdout  # Total IVA
        assert "1,830" in result.stdout  # Total revenue

    @patch("openfatture.cli.commands.report.SessionLocal")
    @patch("openfatture.cli.commands.report.init_db")
    def test_report_iva_with_quarter(self, mock_init_db, mock_session_local):
        """Test VAT report with quarter filter."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_fattura = Mock()
        mock_fattura.imponibile = Decimal("1000.00")
        mock_fattura.iva = Decimal("220.00")
        mock_fattura.totale = Decimal("1220.00")
        mock_riga = Mock()
        mock_riga.aliquota_iva = Decimal("22")
        mock_riga.imponibile = Decimal("1000.00")
        mock_riga.iva = Decimal("220.00")
        mock_fattura.righe = [mock_riga]

        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [
            mock_fattura
        ]

        result = runner.invoke(app, ["iva", "--anno", "2025", "--trimestre", "Q1"])

        assert result.exit_code == 0
        assert "Q1" in result.stdout
        assert "1-3" in result.stdout

    @patch("openfatture.cli.commands.report.SessionLocal")
    @patch("openfatture.cli.commands.report.init_db")
    def test_report_iva_invalid_quarter(self, mock_init_db, mock_session_local):
        """Test VAT report with invalid quarter."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        result = runner.invoke(app, ["iva", "--anno", "2025", "--trimestre", "Q5"])

        assert result.exit_code == 0
        assert "Invalid quarter" in result.stdout

    @patch("openfatture.cli.commands.report.SessionLocal")
    @patch("openfatture.cli.commands.report.init_db")
    def test_report_iva_default_year(self, mock_init_db, mock_session_local):
        """Test VAT report uses current year by default."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = runner.invoke(app, ["iva"])

        assert result.exit_code == 0
        current_year = date.today().year
        assert str(current_year) in result.stdout

    @patch("openfatture.cli.commands.report.SessionLocal")
    @patch("openfatture.cli.commands.report.init_db")
    def test_report_iva_full_year(self, mock_init_db, mock_session_local):
        """Test VAT report for full year (no quarter)."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = runner.invoke(app, ["iva", "--anno", "2025"])

        assert result.exit_code == 0
        assert "Full year" in result.stdout

    @patch("openfatture.cli.commands.report.SessionLocal")
    @patch("openfatture.cli.commands.report.init_db")
    def test_report_iva_excludes_bozza(self, mock_init_db, mock_session_local):
        """Test VAT report excludes draft invoices."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Verify filter excludes BOZZA status
        mock_query = mock_db.query.return_value.filter.return_value.filter.return_value
        mock_query.all.return_value = []

        result = runner.invoke(app, ["iva", "--anno", "2025"])

        assert result.exit_code == 0
        # Query should filter out BOZZA status
        assert mock_db.query.called


class TestReportClientiCommand:
    """Test 'report clienti' command."""

    @patch("openfatture.cli.commands.report.SessionLocal")
    @patch("openfatture.cli.commands.report.init_db")
    def test_report_clienti_no_data(self, mock_init_db, mock_session_local):
        """Test client report with no data."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = (
            []
        )

        result = runner.invoke(app, ["clienti", "--anno", "2025"])

        assert result.exit_code == 0
        assert "No invoices found" in result.stdout

    @patch("openfatture.cli.commands.report.SessionLocal")
    @patch("openfatture.cli.commands.report.init_db")
    def test_report_clienti_with_data(self, mock_init_db, mock_session_local, sample_cliente):
        """Test client report with data."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Mock aggregation results
        mock_results = [
            (1, 5, Decimal("5000.00")),  # (cliente_id, num_fatture, totale_fatturato)
            (2, 3, Decimal("3000.00")),
        ]

        mock_db.query.return_value.filter.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = (
            mock_results
        )

        # Mock cliente query
        mock_cliente1 = Mock()
        mock_cliente1.denominazione = "Client A"
        mock_cliente2 = Mock()
        mock_cliente2.denominazione = "Client B"

        def get_cliente(cliente_id):
            if cliente_id == 1:
                return mock_cliente1
            return mock_cliente2

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_cliente1,
            mock_cliente2,
        ]

        result = runner.invoke(app, ["clienti", "--anno", "2025"])

        assert result.exit_code == 0
        assert "Client Revenue Report" in result.stdout
        assert "Top Clients" in result.stdout
        assert "5,000" in result.stdout
        assert "3,000" in result.stdout
        assert "8,000" in result.stdout  # Total


class FakeCliente:
    def __init__(self, denominazione: str):
        self.denominazione = denominazione
        self.nome = denominazione


class FakeFattura:
    def __init__(self, numero: str, anno: int, cliente: FakeCliente):
        self.numero = numero
        self.anno = anno
        self.cliente = cliente


class FakePagamento:
    def __init__(
        self,
        numero: str,
        anno: int,
        cliente: str,
        data_scadenza: date,
        importo: Decimal,
        importo_pagato: Decimal,
        stato: StatoPagamento = StatoPagamento.DA_PAGARE,
    ):
        self.fattura = FakeFattura(numero, anno, FakeCliente(cliente))
        self.data_scadenza = data_scadenza
        self.importo = importo
        self.importo_pagato = importo_pagato
        self.stato = stato

    @property
    def saldo_residuo(self) -> Decimal:
        residuo = self.importo - self.importo_pagato
        return residuo if residuo > Decimal("0.00") else Decimal("0.00")


class TestReportScadenzeCommand:
    """Test 'report scadenze' command."""

    @patch("openfatture.cli.commands.report.SessionLocal")
    @patch("openfatture.cli.commands.report.init_db")
    def test_report_scadenze_no_outstanding(self, mock_init_db, mock_session_local):
        """Should inform when there are no pending payments."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = runner.invoke(app, ["scadenze"])

        assert result.exit_code == 0
        assert "No outstanding payments" in result.stdout

    @patch("openfatture.cli.commands.report.SessionLocal")
    @patch("openfatture.cli.commands.report.init_db")
    def test_report_scadenze_with_categories(self, mock_init_db, mock_session_local):
        """Should group payments into overdue, due soon, and upcoming."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        today = date.today()
        payments = [
            FakePagamento(
                numero="001",
                anno=2025,
                cliente="Client Overdue",
                data_scadenza=today - timedelta(days=5),
                importo=Decimal("1000.00"),
                importo_pagato=Decimal("200.00"),
                stato=StatoPagamento.PAGATO_PARZIALE,
            ),
            FakePagamento(
                numero="002",
                anno=2025,
                cliente="Client Soon",
                data_scadenza=today + timedelta(days=3),
                importo=Decimal("500.00"),
                importo_pagato=Decimal("0.00"),
            ),
            FakePagamento(
                numero="003",
                anno=2025,
                cliente="Client Future",
                data_scadenza=today + timedelta(days=21),
                importo=Decimal("250.00"),
                importo_pagato=Decimal("0.00"),
            ),
        ]

        mock_query.all.return_value = payments

        result = runner.invoke(app, ["scadenze"])

        assert result.exit_code == 0
        assert "Scaduti" in result.stdout
        assert "In scadenza" in result.stdout
        assert "Prossimi pagamenti" in result.stdout
        assert "001/2025" in result.stdout
        assert "002/2025" in result.stdout
        assert "003/2025" in result.stdout
        assert "Client Overdue" in result.stdout
        assert "Client Soon" in result.stdout
        assert "Client Future" in result.stdout

    @patch("openfatture.cli.commands.report.SessionLocal")
    @patch("openfatture.cli.commands.report.init_db")
    def test_report_clienti_default_year(self, mock_init_db, mock_session_local):
        """Test client report uses current year by default."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = (
            []
        )

        result = runner.invoke(app, ["clienti"])

        assert result.exit_code == 0
        current_year = date.today().year
        assert str(current_year) in result.stdout

    @patch("openfatture.cli.commands.report.SessionLocal")
    @patch("openfatture.cli.commands.report.init_db")
    def test_report_clienti_sorted_by_revenue(self, mock_init_db, mock_session_local):
        """Test client report is sorted by revenue (descending)."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Mock results already sorted
        mock_results = [
            (1, 5, Decimal("10000.00")),  # Highest
            (2, 3, Decimal("5000.00")),
            (3, 2, Decimal("1000.00")),  # Lowest
        ]

        mock_db.query.return_value.filter.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = (
            mock_results
        )

        mock_cliente = Mock()
        mock_cliente.denominazione = "Test Client"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cliente

        result = runner.invoke(app, ["clienti", "--anno", "2025"])

        assert result.exit_code == 0
        # Should show ranking
        assert "1" in result.stdout  # Rank 1
        assert "2" in result.stdout  # Rank 2
        assert "3" in result.stdout  # Rank 3


class TestEnsureDB:
    """Test database initialization helper."""

    @patch("openfatture.cli.commands.report.get_settings")
    @patch("openfatture.cli.commands.report.init_db")
    def test_ensure_db_calls_init(self, mock_init_db, mock_settings):
        """Test that ensure_db calls init_db with correct URL."""
        from openfatture.cli.commands.report import ensure_db

        mock_settings_instance = Mock()
        mock_settings_instance.database_url = "sqlite:///test.db"
        mock_settings.return_value = mock_settings_instance

        ensure_db()

        mock_init_db.assert_called_once_with("sqlite:///test.db")
