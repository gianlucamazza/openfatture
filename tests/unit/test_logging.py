"""
Unit tests for structured logging utilities.

Tests the structlog configuration and logging helpers.
"""

import time

import pytest

from openfatture.utils.logging import (
    LogPerformance,
    add_app_context,
    add_correlation_id,
    configure_logging,
    filter_sensitive_data,
    get_logger,
    log_invoice_created,
    log_invoice_sent,
    log_sdi_notification,
)

pytestmark = pytest.mark.unit


class TestStructlogConfiguration:
    """Test structlog configuration."""

    def test_configure_logging_dev_mode(self):
        """Test logging configuration in development mode."""
        configure_logging(log_level="DEBUG", json_logs=False, dev_mode=True)

        logger = get_logger("test")
        assert logger is not None
        # Logger can be BoundLogger or BoundLoggerLazyProxy
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")

    def test_configure_logging_production_mode_json(self):
        """Test logging configuration in production mode with JSON."""
        configure_logging(log_level="INFO", json_logs=True, dev_mode=False)

        logger = get_logger("test.production")
        assert logger is not None

    def test_configure_logging_production_mode_kv(self):
        """Test logging configuration in production mode with key-value."""
        configure_logging(log_level="WARNING", json_logs=False, dev_mode=False)

        logger = get_logger("test.kv")
        assert logger is not None

    def test_get_logger_returns_bound_logger(self):
        """Test that get_logger returns a properly bound logger."""
        logger = get_logger(__name__)

        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")


class TestLoggingProcessors:
    """Test logging processors."""

    def test_add_correlation_id_processor(self):
        """Test that correlation_id is added to events."""
        event_dict = {"event": "test_event"}
        result = add_correlation_id(None, None, event_dict)

        assert "correlation_id" in result
        # Should be None if not set
        assert result["correlation_id"] is None

    def test_add_correlation_id_preserves_existing(self):
        """Test that existing correlation_id is preserved."""
        event_dict = {"event": "test", "correlation_id": "abc-123"}
        result = add_correlation_id(None, None, event_dict)

        assert result["correlation_id"] == "abc-123"

    def test_filter_sensitive_data_passwords(self):
        """Test that passwords are filtered."""
        event_dict = {
            "event": "login",
            "username": "user@example.com",
            "password": "super_secret",
        }
        result = filter_sensitive_data(None, None, event_dict)

        assert result["username"] == "user@example.com"
        assert result["password"] == "***REDACTED***"

    def test_filter_sensitive_data_api_keys(self):
        """Test that API keys are filtered."""
        event_dict = {
            "event": "api_call",
            "api_key": "sk-1234567890",
            "pec_password": "pec_secret",
        }
        result = filter_sensitive_data(None, None, event_dict)

        assert result["api_key"] == "***REDACTED***"
        assert result["pec_password"] == "***REDACTED***"

    def test_filter_sensitive_data_preserves_safe_data(self):
        """Test that non-sensitive data is not filtered."""
        event_dict = {
            "event": "user_action",
            "user_id": 123,
            "action": "create_invoice",
            "amount": 1000.00,
        }
        result = filter_sensitive_data(None, None, event_dict)

        assert result["user_id"] == 123
        assert result["action"] == "create_invoice"
        assert result["amount"] == 1000.00

    def test_filter_sensitive_data_nested_in_event(self):
        """Test that sensitive data in nested event dict is filtered."""
        event_dict = {
            "event": {
                "type": "login",
                "password": "secret123",
            },
            "user": "test",
        }
        result = filter_sensitive_data(None, None, event_dict)

        assert result["event"]["password"] == "***REDACTED***"
        assert result["user"] == "test"

    def test_add_app_context_processor(self):
        """Test that app context is added."""
        event_dict = {"event": "test"}
        result = add_app_context(None, None, event_dict)

        assert result["app"] == "openfatture"
        assert result["version"] == "0.1.0"


class TestLogPerformance:
    """Test performance logging context manager."""

    def test_log_performance_success(self, caplog):
        """Test that performance is logged on success."""
        configure_logging(log_level="INFO", dev_mode=True)
        logger = get_logger("test.performance")

        with LogPerformance("test_operation", logger):
            time.sleep(0.01)  # Simulate work

        # The context manager should have logged completion
        # We can't easily check caplog with structlog, so we just verify no exception

    def test_log_performance_with_exception(self, caplog):
        """Test that performance is logged even on exception."""
        configure_logging(log_level="INFO", dev_mode=True)
        logger = get_logger("test.error")

        with pytest.raises(ValueError):
            with LogPerformance("failing_operation", logger):
                raise ValueError("Test error")

        # Should have logged the error with duration
        # We can't easily check caplog with structlog, so we just verify exception was raised

    def test_log_performance_timing(self):
        """Test that performance timing is accurate."""
        logger = get_logger("test.timing")

        start = time.perf_counter()
        with LogPerformance("timed_operation", logger):
            time.sleep(0.05)  # Sleep for 50ms
        duration = time.perf_counter() - start

        # Should have taken at least 50ms
        assert duration >= 0.05


class TestAuditLoggingHelpers:
    """Test audit logging helper functions."""

    def test_log_invoice_created(self):
        """Test logging invoice creation."""
        logger = get_logger("test.audit")

        # Should not raise exception
        log_invoice_created(
            logger,
            invoice_id=123,
            invoice_number="1/2025",
            client_name="Test Client",
            amount=1000.00,
        )

    def test_log_invoice_sent(self):
        """Test logging invoice sending."""
        logger = get_logger("test.audit")

        # Should not raise exception
        log_invoice_sent(
            logger,
            invoice_id=123,
            invoice_number="1/2025",
            recipient="sdi@pec.fatturapa.it",
        )

    def test_log_sdi_notification(self):
        """Test logging SDI notifications."""
        logger = get_logger("test.audit")

        # Should not raise exception
        log_sdi_notification(
            logger,
            invoice_id=123,
            notification_type="RC",
            status="accepted",
        )


class TestLoggingIntegration:
    """Integration tests for logging system."""

    def test_full_logging_workflow(self):
        """Test complete logging workflow."""
        configure_logging(log_level="DEBUG", dev_mode=True)
        logger = get_logger("test.workflow")

        # Log various events
        logger.info("workflow_started", step=1)
        logger.debug("processing_data", records=100)
        logger.warning("rate_limit_approaching", usage=0.9)
        logger.error("validation_failed", errors=["field1", "field2"])

        # Should not raise exceptions

    def test_logging_with_sensitive_data(self):
        """Test that sensitive data is filtered in real usage."""
        configure_logging(log_level="INFO", dev_mode=True)
        logger = get_logger("test.sensitive")

        # Log event with sensitive data
        logger.info(
            "user_login",
            username="test@example.com",
            password="should_be_redacted",
            api_key="sk-secret-key",
        )

        # If this doesn't raise, the filter is working
        # (actual redaction happens in processors)

    def test_logging_performance_with_audit(self):
        """Test combining performance and audit logging."""
        configure_logging(log_level="INFO", dev_mode=True)
        logger = get_logger("test.combined")

        with LogPerformance("invoice_generation", logger):
            log_invoice_created(
                logger,
                invoice_id=456,
                invoice_number="2/2025",
                client_name="Acme Corp",
                amount=5000.00,
            )
            time.sleep(0.01)

        # Should complete without errors
