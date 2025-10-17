"""Unit tests for PEC sender."""

import smtplib
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from openfatture.sdi.pec_sender.sender import PECSender, create_log_entry
from openfatture.storage.database.models import StatoFattura
from openfatture.utils.rate_limiter import RateLimiter

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


class TestPECSenderRetryLogic:
    """Tests for PEC sender retry logic and error handling."""

    @patch("openfatture.sdi.pec_sender.sender.smtplib.SMTP_SSL")
    @patch("time.sleep")
    def test_retry_on_transient_smtp_errors(
        self, mock_sleep, mock_smtp_ssl, test_settings, sample_fattura, tmp_path
    ):
        """Test retry logic for transient SMTP errors."""
        # Arrange
        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text('<?xml version="1.0"?><FatturaElettronica/>')

        mock_server = MagicMock()
        # Fail twice, then succeed on third try
        mock_server.send_message.side_effect = [
            smtplib.SMTPServerDisconnected("Connection lost"),
            smtplib.SMTPConnectError(421, "Server busy"),
            None,  # Success
        ]
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        sender = PECSender(test_settings, max_retries=3)

        # Act
        success, error = sender.send_invoice(sample_fattura, xml_path)

        # Assert
        assert success is True
        assert error is None
        assert sample_fattura.stato == StatoFattura.INVIATA

        # Verify retry count
        assert mock_server.send_message.call_count == 3

        # Verify exponential backoff was applied
        assert mock_sleep.call_count == 2

    @patch("openfatture.sdi.pec_sender.sender.smtplib.SMTP_SSL")
    @patch("time.sleep")
    def test_no_retry_on_auth_errors(
        self, mock_sleep, mock_smtp_ssl, test_settings, sample_fattura, tmp_path
    ):
        """Test that authentication errors are not retried."""
        # Arrange
        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text('<?xml version="1.0"?><FatturaElettronica/>')

        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Auth failed")
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        sender = PECSender(test_settings, max_retries=3)

        # Act
        success, error = sender.send_invoice(sample_fattura, xml_path)

        # Assert
        assert success is False
        assert "authentication failed" in error.lower()

        # Should only try once (no retries for auth errors)
        assert mock_server.login.call_count == 1
        mock_sleep.assert_not_called()

    @patch("openfatture.sdi.pec_sender.sender.smtplib.SMTP_SSL")
    @patch("time.sleep")
    def test_max_retries_exceeded(
        self, mock_sleep, mock_smtp_ssl, test_settings, sample_fattura, tmp_path
    ):
        """Test behavior when max retries are exceeded."""
        # Arrange
        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text('<?xml version="1.0"?><FatturaElettronica/>')

        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPServerDisconnected("Connection lost")
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        sender = PECSender(test_settings, max_retries=3)

        # Act
        success, error = sender.send_invoice(sample_fattura, xml_path)

        # Assert
        assert success is False
        assert "Failed after 3 attempts" in error
        assert "Connection lost" in error

        # Should have tried max_retries times
        assert mock_server.send_message.call_count == 3

    @patch("openfatture.sdi.pec_sender.sender.smtplib.SMTP_SSL")
    @patch("time.sleep")
    def test_exponential_backoff_delays(
        self, mock_sleep, mock_smtp_ssl, test_settings, sample_fattura, tmp_path
    ):
        """Test exponential backoff increases delay between retries."""
        # Arrange
        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text('<?xml version="1.0"?><FatturaElettronica/>')

        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPServerDisconnected("Connection lost")
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        sender = PECSender(test_settings, max_retries=3)

        # Act
        success, error = sender.send_invoice(sample_fattura, xml_path)

        # Assert - verify delays increase
        assert mock_sleep.call_count == 2  # 2 retries = 2 sleeps
        delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert delays[0] < delays[1]  # Second delay should be longer than first

    @patch("openfatture.sdi.pec_sender.sender.smtplib.SMTP_SSL")
    def test_unexpected_exception_no_retry(
        self, mock_smtp_ssl, test_settings, sample_fattura, tmp_path
    ):
        """Test that unexpected exceptions are not retried."""
        # Arrange
        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text('<?xml version="1.0"?><FatturaElettronica/>')

        mock_server = MagicMock()
        mock_server.login.side_effect = ValueError("Unexpected error")
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        sender = PECSender(test_settings, max_retries=3)

        # Act
        success, error = sender.send_invoice(sample_fattura, xml_path)

        # Assert
        assert success is False
        assert "Error sending PEC" in error

        # Should only try once
        assert mock_server.login.call_count == 1


class TestPECSenderRateLimiting:
    """Tests for PEC sender rate limiting functionality."""

    def test_rate_limiting_blocks_when_exceeded(self, test_settings, sample_fattura, tmp_path):
        """Test that rate limiting blocks when limit is exceeded."""
        # Arrange
        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text('<?xml version="1.0"?><FatturaElettronica/>')

        # Create mock rate limiter that always returns False (blocked)
        mock_rate_limiter = Mock(spec=RateLimiter)
        mock_rate_limiter.get_wait_time.return_value = 0
        mock_rate_limiter.acquire.return_value = False  # Rate limit exceeded

        sender = PECSender(test_settings, rate_limit=mock_rate_limiter, max_retries=1)

        # Act
        success, error = sender.send_invoice(sample_fattura, xml_path)

        # Assert
        assert success is False
        assert "Rate limit exceeded" in error

        # Verify rate limiter was called
        mock_rate_limiter.get_wait_time.assert_called_once()
        mock_rate_limiter.acquire.assert_called_once_with(blocking=True, timeout=30)

    def test_custom_rate_limiter_integration(self, test_settings):
        """Test PEC sender with custom rate limiter."""
        # Arrange
        custom_limiter = RateLimiter(max_calls=5, period=30)
        sender = PECSender(test_settings, rate_limit=custom_limiter)

        # Assert
        assert sender.rate_limiter == custom_limiter
        assert sender.rate_limiter.max_calls == 5
        assert sender.rate_limiter.period == 30

    def test_default_rate_limiter_settings(self, test_settings):
        """Test default rate limiter is configured correctly."""
        sender = PECSender(test_settings)

        # Default should be 10 emails per minute
        assert sender.rate_limiter is not None
        # Note: Can't easily verify max_calls/period without accessing internals
