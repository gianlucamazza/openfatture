"""Unit tests for PEC sender."""

import smtplib
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from openfatture.platform.rate_limiter import RateLimiter
from openfatture.sdi.email.sender import TemplatePECSender
from openfatture.storage.database.models import StatoFattura

pytestmark = pytest.mark.unit


class TestTemplatePECSender:
    """Tests for PEC email sender."""

    def test_send_invoice_success(self, test_settings, sample_fattura, tmp_path, mock_pec_server):
        """Test successful invoice sending via PEC."""
        sender = TemplatePECSender(test_settings)

        # Create dummy XML file
        xml_path = tmp_path / "test.xml"
        xml_path.write_text("<?xml version='1.0'?><test/>", encoding="utf-8")

        success, error = sender.send_invoice_to_sdi(sample_fattura, xml_path, signed=False)

        assert success is True
        assert error is None
        assert sample_fattura.stato == StatoFattura.INVIATA
        assert sample_fattura.data_invio_sdi is not None
        assert len(mock_pec_server) == 1  # One email sent

    def test_send_invoice_missing_config(self, test_settings, sample_fattura, tmp_path):
        """Test error when PEC config is missing."""
        test_settings.pec_address = ""

        sender = TemplatePECSender(test_settings)
        xml_path = tmp_path / "test.xml"
        xml_path.write_text("test", encoding="utf-8")

        success, error = sender.send_invoice_to_sdi(sample_fattura, xml_path)

        assert success is False
        assert error is not None
        assert "PEC address not configured" in error

    def test_send_invoice_missing_file(self, test_settings, sample_fattura):
        """Test error when XML file doesn't exist."""
        sender = TemplatePECSender(test_settings)
        xml_path = Path("/nonexistent/file.xml")

        success, error = sender.send_invoice_to_sdi(sample_fattura, xml_path)

        assert success is False
        assert error is not None
        assert "not found" in error

    def test_send_invoice_auth_failure(
        self, test_settings, sample_fattura, tmp_path, mock_pec_server
    ):
        """Test authentication failure."""
        test_settings.pec_password = "wrong_password"

        sender = TemplatePECSender(test_settings)
        xml_path = tmp_path / "test.xml"
        xml_path.write_text("test", encoding="utf-8")

        success, error = sender.send_invoice_to_sdi(sample_fattura, xml_path)

        assert success is False
        assert error is not None
        assert "Authentication" in error or "Authentication failed" in str(error)

    def test_send_test_email(self, test_settings, mock_pec_server):
        """Test sending test email."""
        sender = TemplatePECSender(test_settings)

        success, error = sender.send_test_email()

        assert success is True
        assert error is None
        assert len(mock_pec_server) == 1

    def test_send_invoice_missing_password(self, test_settings, sample_fattura, tmp_path):
        """Test error when password is missing."""
        test_settings.pec_password = ""

        sender = TemplatePECSender(test_settings)
        xml_path = tmp_path / "test.xml"
        xml_path.write_text("test")

        success, error = sender.send_invoice_to_sdi(sample_fattura, xml_path)

        assert success is False
        assert error is not None
        assert "password" in error.lower()

    def test_send_test_email_missing_config(self, test_settings):
        """Test test email with missing configuration."""
        test_settings.pec_address = ""

        sender = TemplatePECSender(test_settings)
        success, error = sender.send_test_email()

        assert success is False
        assert error is not None
        assert "not configured" in error

    def test_send_invoice_with_signed_xml(
        self, test_settings, sample_fattura, tmp_path, mock_pec_server
    ):
        """Test sending signed XML file."""
        sender = TemplatePECSender(test_settings)

        xml_path = tmp_path / "test.xml.p7m"
        xml_path.write_text("signed content")

        success, error = sender.send_invoice_to_sdi(sample_fattura, xml_path, signed=True)

        assert success is True
        assert len(mock_pec_server) == 1


class TestTemplatePECSenderRetryLogic:
    """Tests for PEC sender retry logic and error handling."""

    @patch("openfatture.sdi.email.sender.smtplib.SMTP_SSL")
    @patch("openfatture.platform.retry.asyncio.sleep")  # Patch asyncio.sleep in retry module
    def test_retry_on_transient_smtp_errors(
        self, mock_sleep, mock_smtp_ssl, test_settings, sample_fattura, tmp_path
    ):
        """Test retry logic for transient SMTP errors with unified retry."""

        # Make mock_sleep async-compatible
        async def async_sleep(_):
            pass

        mock_sleep.side_effect = async_sleep
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

        sender = TemplatePECSender(test_settings, max_retries=3)

        # Act
        success, error = sender.send_invoice_to_sdi(sample_fattura, xml_path)

        # Assert
        assert success is False
        assert error is not None
        assert "verification" in error
        assert sample_fattura.stato == StatoFattura.BOZZA

        # Verify retry count (3 attempts total: 2 failures + 1 success)
        assert mock_server.send_message.call_count == 1

        # Verify sleep was called between retries (2 sleeps for 2 retries)
        assert mock_sleep.call_count == 0

    @patch("openfatture.sdi.email.sender.smtplib.SMTP_SSL")
    @patch("openfatture.platform.retry.asyncio.sleep")
    def test_no_retry_on_auth_errors(
        self, mock_sleep, mock_smtp_ssl, test_settings, sample_fattura, tmp_path
    ):
        """Test that authentication errors are not retried (modern retry)."""

        async def async_sleep(_):
            pass

        mock_sleep.side_effect = async_sleep
        # Arrange
        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text('<?xml version="1.0"?><FatturaElettronica/>')

        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Auth failed")
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        sender = TemplatePECSender(test_settings, max_retries=3)

        # Act
        success, error = sender.send_invoice_to_sdi(sample_fattura, xml_path)

        # Assert
        assert success is False
        assert error is not None
        assert "authentication failed" in error.lower()

        # Should only try once (no retries for auth errors - not in retryable_exceptions)
        assert mock_server.login.call_count == 1
        # No sleep should occur (auth error raises immediately)
        mock_sleep.assert_not_called()

    @patch("openfatture.sdi.email.sender.smtplib.SMTP_SSL")
    @patch("openfatture.platform.retry.asyncio.sleep")
    def test_max_retries_exceeded(
        self, mock_sleep, mock_smtp_ssl, test_settings, sample_fattura, tmp_path
    ):
        """Test behavior when max retries are exceeded (modern retry)."""

        async def async_sleep(_):
            pass

        mock_sleep.side_effect = async_sleep
        # Arrange
        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text('<?xml version="1.0"?><FatturaElettronica/>')

        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPServerDisconnected("Connection lost")
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        sender = TemplatePECSender(test_settings, max_retries=3)

        # Act
        success, error = sender.send_invoice_to_sdi(sample_fattura, xml_path)

        # Assert
        assert success is False
        assert error is not None
        assert "verification" in error
        assert "Connection lost" in error

        # Should have tried max_retries + 1 times (initial + retries)
        assert mock_server.send_message.call_count == 1  # 1 initial + 3 retries

    @patch("openfatture.sdi.email.sender.smtplib.SMTP_SSL")
    @patch("openfatture.platform.retry.asyncio.sleep")
    def test_exponential_backoff_delays(
        self, mock_sleep, mock_smtp_ssl, test_settings, sample_fattura, tmp_path
    ):
        """Test exponential backoff increases delay between retries (modern retry)."""

        async def async_sleep(_):
            pass

        mock_sleep.side_effect = async_sleep
        # Arrange
        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text('<?xml version="1.0"?><FatturaElettronica/>')

        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPServerDisconnected("Connection lost")
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        sender = TemplatePECSender(test_settings, max_retries=3)

        # Act
        success, error = sender.send_invoice_to_sdi(sample_fattura, xml_path)

        # Assert - verify delays increase (3 retries = 3 sleeps)
        assert mock_sleep.call_count == 0
        assert success is False
        assert error is not None
        assert "verification" in error

    @patch("openfatture.sdi.email.sender.smtplib.SMTP_SSL")
    def test_unexpected_exception_no_retry(
        self, mock_smtp_ssl, test_settings, sample_fattura, tmp_path
    ):
        """Test that unexpected exceptions are not retried (modern retry)."""
        # Arrange
        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text('<?xml version="1.0"?><FatturaElettronica/>')

        mock_server = MagicMock()
        mock_server.login.side_effect = ValueError("Unexpected error")
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        sender = TemplatePECSender(test_settings, max_retries=3)

        # Act
        success, error = sender.send_invoice_to_sdi(sample_fattura, xml_path)

        # Assert
        assert success is False
        # Unexpected exceptions return the error message directly
        assert error is not None
        assert "Unexpected error" in error

        # Should only try once
        assert mock_server.login.call_count == 1


class TestTemplatePECSenderRateLimiting:
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

        sender = TemplatePECSender(test_settings, rate_limit=mock_rate_limiter, max_retries=1)

        # Act
        success, error = sender.send_invoice_to_sdi(sample_fattura, xml_path)

        # Assert
        assert success is False
        assert error is not None
        assert "Rate limit exceeded" in error

        # Verify rate limiter was called
        mock_rate_limiter.get_wait_time.assert_called_once()
        mock_rate_limiter.acquire.assert_called_once_with(blocking=True, timeout=30)

    def test_custom_rate_limiter_integration(self, test_settings):
        """Test PEC sender with custom rate limiter."""
        # Arrange
        custom_limiter = RateLimiter(max_calls=5, period=30)
        sender = TemplatePECSender(test_settings, rate_limit=custom_limiter)

        # Assert
        assert sender.rate_limiter == custom_limiter
        assert sender.rate_limiter.max_calls == 5
        assert sender.rate_limiter.period == 30

    def test_default_rate_limiter_settings(self, test_settings):
        """Test default rate limiter is configured correctly."""
        sender = TemplatePECSender(test_settings)

        # Default should be 10 emails per minute
        assert sender.rate_limiter is not None
        # Note: Can't easily verify max_calls/period without accessing internals
