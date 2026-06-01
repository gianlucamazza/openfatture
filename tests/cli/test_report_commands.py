"""Tests for report CLI commands.

These exercise the commands end-to-end against a real, isolated database
(``runtime_db``) instead of mocking SQLAlchemy query chains: data is seeded
through the same database the command reads, and the locale is pinned to
English so label assertions are deterministic.
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from openfatture.cli.commands.report import app
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    Pagamento,
    RigaFattura,
    StatoFattura,
    StatoPagamento,
    TipoDocumento,
)

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


def _make_cliente(session: Session, denominazione: str, codice: str) -> Cliente:
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
    imponibile: Decimal,
    iva: Decimal,
    anno: int = 2025,
    mese: int = 6,
    stato: StatoFattura = StatoFattura.INVIATA,
) -> Fattura:
    fattura = Fattura(
        numero=numero,
        anno=anno,
        data_emissione=date(anno, mese, 15),
        cliente_id=cliente.id,
        tipo_documento=TipoDocumento.TD01,
        stato=stato,
        imponibile=imponibile,
        iva=iva,
        totale=imponibile + iva,
    )
    session.add(fattura)
    session.flush()
    session.add(
        RigaFattura(
            fattura_id=fattura.id,
            numero_riga=1,
            descrizione="Servizio",
            quantita=Decimal("1"),
            prezzo_unitario=imponibile,
            unita_misura="servizio",
            aliquota_iva=Decimal("22.00"),
            imponibile=imponibile,
            iva=iva,
            totale=imponibile + iva,
        )
    )
    session.commit()
    session.refresh(fattura)
    return fattura


class TestReportIVACommand:
    """Test 'report iva' command."""

    def test_report_iva_no_data(self, runtime_db):
        result = runner.invoke(app, ["iva", "--anno", "2025"])
        assert result.exit_code == 0
        assert "No invoices found" in result.stdout

    def test_report_iva_with_data(self, runtime_session):
        cliente = _make_cliente(runtime_session, "Acme", "ABC1234")
        _make_fattura(
            runtime_session,
            numero="1",
            cliente=cliente,
            imponibile=Decimal("1000.00"),
            iva=Decimal("220.00"),
        )
        _make_fattura(
            runtime_session,
            numero="2",
            cliente=cliente,
            imponibile=Decimal("500.00"),
            iva=Decimal("110.00"),
        )

        result = runner.invoke(app, ["iva", "--anno", "2025"])

        assert result.exit_code == 0
        assert "VAT Report" in result.stdout
        assert "VAT Summary" in result.stdout
        assert "1,500" in result.stdout  # Total imponibile
        assert "330" in result.stdout  # Total IVA
        assert "1,830" in result.stdout  # Total revenue

    def test_report_iva_with_quarter(self, runtime_session):
        cliente = _make_cliente(runtime_session, "Acme", "ABC1234")
        _make_fattura(
            runtime_session,
            numero="1",
            cliente=cliente,
            imponibile=Decimal("1000.00"),
            iva=Decimal("220.00"),
            mese=2,  # Q1
        )

        result = runner.invoke(app, ["iva", "--anno", "2025", "--trimestre", "Q1"])

        assert result.exit_code == 0
        assert "Q1" in result.stdout
        assert "1-3" in result.stdout

    def test_report_iva_invalid_quarter(self, runtime_db):
        result = runner.invoke(app, ["iva", "--anno", "2025", "--trimestre", "Q5"])
        assert result.exit_code == 0
        assert "Invalid quarter" in result.stdout

    def test_report_iva_default_year(self, runtime_db):
        result = runner.invoke(app, ["iva"])
        assert result.exit_code == 0
        assert str(date.today().year) in result.stdout

    def test_report_iva_full_year(self, runtime_db):
        result = runner.invoke(app, ["iva", "--anno", "2025"])
        assert result.exit_code == 0
        assert "Full year" in result.stdout

    def test_report_iva_excludes_bozza(self, runtime_session):
        cliente = _make_cliente(runtime_session, "Acme", "ABC1234")
        # Only a draft invoice exists -> report must treat the period as empty.
        _make_fattura(
            runtime_session,
            numero="1",
            cliente=cliente,
            imponibile=Decimal("1000.00"),
            iva=Decimal("220.00"),
            stato=StatoFattura.BOZZA,
        )

        result = runner.invoke(app, ["iva", "--anno", "2025"])

        assert result.exit_code == 0
        assert "No invoices found" in result.stdout


class TestReportClientiCommand:
    """Test 'report clienti' command."""

    def test_report_clienti_no_data(self, runtime_db):
        result = runner.invoke(app, ["clienti", "--anno", "2025"])
        assert result.exit_code == 0
        assert "No invoices found" in result.stdout

    def test_report_clienti_with_data(self, runtime_session):
        client_a = _make_cliente(runtime_session, "Client A", "AAA0001")
        client_b = _make_cliente(runtime_session, "Client B", "BBB0001")
        _make_fattura(
            runtime_session,
            numero="1",
            cliente=client_a,
            imponibile=Decimal("5000.00"),
            iva=Decimal("0.00"),
        )
        _make_fattura(
            runtime_session,
            numero="2",
            cliente=client_b,
            imponibile=Decimal("3000.00"),
            iva=Decimal("0.00"),
        )

        result = runner.invoke(app, ["clienti", "--anno", "2025"])

        assert result.exit_code == 0
        assert "Client Revenue Report" in result.stdout
        assert "Top Clients" in result.stdout
        assert "5,000" in result.stdout
        assert "3,000" in result.stdout
        assert "Client A" in result.stdout
        assert "Client B" in result.stdout

    def test_report_clienti_default_year(self, runtime_db):
        result = runner.invoke(app, ["clienti"])
        assert result.exit_code == 0
        assert str(date.today().year) in result.stdout

    def test_report_clienti_sorted_by_revenue(self, runtime_session):
        client_a = _make_cliente(runtime_session, "Client A", "AAA0001")
        client_b = _make_cliente(runtime_session, "Client B", "BBB0001")
        _make_fattura(
            runtime_session,
            numero="1",
            cliente=client_a,
            imponibile=Decimal("10000.00"),
            iva=Decimal("0.00"),
        )
        _make_fattura(
            runtime_session,
            numero="2",
            cliente=client_b,
            imponibile=Decimal("5000.00"),
            iva=Decimal("0.00"),
        )

        result = runner.invoke(app, ["clienti", "--anno", "2025"])

        assert result.exit_code == 0
        # Highest revenue client appears before the lower one.
        assert result.stdout.index("Client A") < result.stdout.index("Client B")


class TestReportScadenzeCommand:
    """Test 'report scadenze' command."""

    def _make_pagamento(
        self,
        session: Session,
        *,
        numero: str,
        cliente_name: str,
        data_scadenza: date,
        importo: Decimal,
        importo_pagato: Decimal,
        stato: StatoPagamento = StatoPagamento.DA_PAGARE,
    ) -> None:
        cliente = _make_cliente(session, cliente_name, numero.zfill(7))
        fattura = _make_fattura(
            session,
            numero=numero,
            cliente=cliente,
            imponibile=importo,
            iva=Decimal("0.00"),
        )
        session.add(
            Pagamento(
                fattura_id=fattura.id,
                data_scadenza=data_scadenza,
                importo=importo,
                importo_pagato=importo_pagato,
                stato=stato,
            )
        )
        session.commit()

    def test_report_scadenze_no_outstanding(self, runtime_db):
        result = runner.invoke(app, ["scadenze"])
        assert result.exit_code == 0
        assert "No outstanding payments" in result.stdout

    def test_report_scadenze_with_categories(self, runtime_session):
        today = date.today()
        self._make_pagamento(
            runtime_session,
            numero="001",
            cliente_name="Client Overdue",
            data_scadenza=today - timedelta(days=5),
            importo=Decimal("1000.00"),
            importo_pagato=Decimal("200.00"),
            stato=StatoPagamento.PAGATO_PARZIALE,
        )
        self._make_pagamento(
            runtime_session,
            numero="002",
            cliente_name="Client Soon",
            data_scadenza=today + timedelta(days=3),
            importo=Decimal("500.00"),
            importo_pagato=Decimal("0.00"),
        )
        self._make_pagamento(
            runtime_session,
            numero="003",
            cliente_name="Client Future",
            data_scadenza=today + timedelta(days=21),
            importo=Decimal("250.00"),
            importo_pagato=Decimal("0.00"),
        )

        result = runner.invoke(app, ["scadenze"])

        assert result.exit_code == 0
        assert "Overdue" in result.stdout
        assert "Due soon" in result.stdout
        assert "Upcoming" in result.stdout
        assert "Client Overdue" in result.stdout
        assert "Client Soon" in result.stdout
        assert "Client Future" in result.stdout


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
