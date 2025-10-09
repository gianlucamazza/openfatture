"""Unit tests for PEC sender."""

from pathlib import Path

import pytest

from openfatture.sdi.pec_sender.sender import PECSender, create_log_entry
from openfatture.storage.database.models import StatoFattura

pytestmark = pytest.mark.unit


class TestPECSender:
    """Tests for PEC email sender."""

    def test_send_invoice_success(self, test_settings, sample_fattura, tmp_path, mock_pec_server):
        """Test successful invoice sending via PEC."""
        sender = PECSender(test_settings)

        # Create dummy XML file
        xml_path = tmp_path / "test.xml"
        xml_path.write_text("<?xml version='1.0'?><test/>", encoding="utf-8")

        success, error = sender.send_invoice(sample_fattura, xml_path, signed=False)

        assert success is True
        assert error is None
        assert sample_fattura.stato == StatoFattura.INVIATA
        assert sample_fattura.data_invio_sdi is not None
        assert len(mock_pec_server) == 1  # One email sent

    def test_send_invoice_missing_config(self, test_settings, sample_fattura, tmp_path):
        """Test error when PEC config is missing."""
        test_settings.pec_address = ""

        sender = PECSender(test_settings)
        xml_path = tmp_path / "test.xml"
        xml_path.write_text("test", encoding="utf-8")

        success, error = sender.send_invoice(sample_fattura, xml_path)

        assert success is False
        assert "PEC address not configured" in error

    def test_send_invoice_missing_file(self, test_settings, sample_fattura):
        """Test error when XML file doesn't exist."""
        sender = PECSender(test_settings)
        xml_path = Path("/nonexistent/file.xml")

        success, error = sender.send_invoice(sample_fattura, xml_path)

        assert success is False
        assert "not found" in error

    def test_send_invoice_auth_failure(
        self, test_settings, sample_fattura, tmp_path, mock_pec_server
    ):
        """Test authentication failure."""
        test_settings.pec_password = "wrong_password"

        sender = PECSender(test_settings)
        xml_path = tmp_path / "test.xml"
        xml_path.write_text("test", encoding="utf-8")

        success, error = sender.send_invoice(sample_fattura, xml_path)

        assert success is False
        assert "Authentication" in error or "Authentication failed" in str(error)

    def test_send_test_email(self, test_settings, mock_pec_server):
        """Test sending test email."""
        sender = PECSender(test_settings)

        success, error = sender.send_test_email()

        assert success is True
        assert error is None
        assert len(mock_pec_server) == 1

    def test_create_log_entry(self, sample_fattura):
        """Test creating log entry."""
        log = create_log_entry(
            sample_fattura,
            tipo="RC",
            descrizione="Ricevuta consegna",
        )

        assert log.fattura_id == sample_fattura.id
        assert log.tipo_notifica == "RC"
        assert log.descrizione == "Ricevuta consegna"
        assert log.data_ricezione is not None

    def test_create_log_entry_with_xml_path(self, sample_fattura, tmp_path):
        """Test creating log entry with XML path."""
        xml_path = tmp_path / "notification.xml"
        xml_path.write_text("<xml/>")

        log = create_log_entry(
            sample_fattura, tipo="NS", descrizione="Notifica scarto", xml_path=xml_path
        )

        assert log.xml_path == str(xml_path)
        assert log.tipo_notifica == "NS"

    def test_send_invoice_missing_password(self, test_settings, sample_fattura, tmp_path):
        """Test error when password is missing."""
        test_settings.pec_password = ""

        sender = PECSender(test_settings)
        xml_path = tmp_path / "test.xml"
        xml_path.write_text("test")

        success, error = sender.send_invoice(sample_fattura, xml_path)

        assert success is False
        assert "password" in error.lower()

    def test_send_test_email_missing_config(self, test_settings):
        """Test test email with missing configuration."""
        test_settings.pec_address = ""

        sender = PECSender(test_settings)
        success, error = sender.send_test_email()

        assert success is False
        assert "not configured" in error

    def test_create_email_body(self, test_settings, sample_fattura):
        """Test email body creation."""
        sender = PECSender(test_settings)

        body = sender._create_email_body(sample_fattura)

        assert isinstance(body, str)
        assert test_settings.cedente_denominazione in body
        assert sample_fattura.numero in body
        assert str(sample_fattura.anno) in body
        assert sample_fattura.cliente.denominazione in body

    def test_send_invoice_with_signed_xml(
        self, test_settings, sample_fattura, tmp_path, mock_pec_server
    ):
        """Test sending signed XML file."""
        sender = PECSender(test_settings)

        xml_path = tmp_path / "test.xml.p7m"
        xml_path.write_text("signed content")

        success, error = sender.send_invoice(sample_fattura, xml_path, signed=True)

        assert success is True
        assert len(mock_pec_server) == 1
