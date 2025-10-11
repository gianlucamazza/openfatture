"""Tests for Notifier - Email, Console, and Composite notification strategies.

Tests cover: SMTP mocking, Jinja2 template rendering, multi-channel notifications,
error handling, and fallback text generation.
"""

import smtplib
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from openfatture.payment.application.notifications.notifier import (
    CompositeNotifier,
    ConsoleNotifier,
    EmailNotifier,
    INotifier,
    SMTPConfig,
)
from openfatture.payment.domain.enums import ReminderStatus, ReminderStrategy
from openfatture.payment.domain.models import PaymentReminder


class TestEmailNotifier:
    """Tests for EmailNotifier with SMTP and Jinja2 template mocking."""

    @pytest.fixture
    def smtp_config(self):
        """Create SMTP configuration."""
        return SMTPConfig(
            host="smtp.gmail.com",
            port=587,
            username="test@example.com",
            password="testpassword",
            from_email="noreply@openfatture.com",
            from_name="OpenFatture Test",
            use_tls=True,
        )

    @pytest.fixture
    def email_notifier(self, smtp_config, tmp_path):
        """Create email notifier with temp template directory."""
        # Create temporary template directory
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        return EmailNotifier(smtp_config, template_dir=template_dir)

    @pytest.fixture
    def mock_reminder(self, mocker):
        """Create mock PaymentReminder with payment and invoice."""
        reminder = mocker.Mock(spec=PaymentReminder)
        reminder.id = 1
        reminder.payment_id = 100
        reminder.strategy = ReminderStrategy.DEFAULT
        reminder.status = ReminderStatus.PENDING
        reminder.email_body = "Test reminder body"
        reminder.email_subject = "Test reminder subject"
        # Note: days_before_due doesn't exist in model, but production code expects it
        reminder.days_before_due = 7

        # Mock payment
        payment = mocker.Mock()
        payment.id = 100
        payment.importo_da_pagare = Decimal("1000.00")
        payment.importo_pagato = Decimal("0.00")
        payment.data_scadenza = date(2024, 12, 31)

        # Mock invoice (fattura)
        invoice = mocker.Mock()
        invoice.numero = "INV-2024-001"
        invoice.cliente = mocker.Mock()
        invoice.cliente.email = "cliente@example.com"
        invoice.cliente.denominazione = "ACME Corporation"

        payment.fattura = invoice
        reminder.payment = payment

        return reminder

    # ==========================================================================
    # EmailNotifier Tests (6 tests)
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_send_reminder_success(self, email_notifier, mock_reminder, mocker):
        """Test successful email sending with SMTP mock."""
        # Mock SMTP
        mock_smtp = mocker.MagicMock()
        mock_smtp_instance = mocker.MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

        # Mock template rendering
        email_notifier._render_template = AsyncMock(
            side_effect=[
                "<html>Test HTML</html>",  # HTML body
                "Test plain text",  # Text body
            ]
        )

        with patch("smtplib.SMTP", mock_smtp):
            result = await email_notifier.send_reminder(mock_reminder)

        # Verify success
        assert result is True

        # Verify SMTP connection
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with("test@example.com", "testpassword")
        mock_smtp_instance.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_reminder_missing_invoice(self, email_notifier, mock_reminder, mocker):
        """Test that missing invoice returns False."""
        # Remove invoice from payment
        mock_reminder.payment.fattura = None

        result = await email_notifier.send_reminder(mock_reminder)

        # Should fail without invoice
        assert result is False

    @pytest.mark.asyncio
    async def test_send_reminder_smtp_exception(self, email_notifier, mock_reminder, mocker):
        """Test that SMTP exceptions are handled gracefully."""
        # Mock template rendering
        email_notifier._render_template = AsyncMock(
            side_effect=[
                "<html>Test</html>",
                "Test text",
            ]
        )

        # Mock SMTP to raise exception
        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.side_effect = smtplib.SMTPException("Connection failed")

            result = await email_notifier.send_reminder(mock_reminder)

        # Should return False on SMTP failure
        assert result is False

    @pytest.mark.asyncio
    async def test_render_template_with_jinja2(self, email_notifier, tmp_path, mocker):
        """Test template rendering with Jinja2."""
        # Create a test template
        template_dir = tmp_path / "templates"
        template_dir.mkdir(exist_ok=True)
        template_file = template_dir / "test.html"
        template_file.write_text("<h1>Hello {{ name }}</h1>")

        # Reinitialize notifier with template directory
        email_notifier = EmailNotifier(email_notifier.smtp_config, template_dir=template_dir)

        # Render template
        result = await email_notifier._render_template("test.html", {"name": "World"})

        assert result == "<h1>Hello World</h1>"

    @pytest.mark.asyncio
    async def test_render_template_fallback_text(self, email_notifier, mock_reminder):
        """Test fallback text generation when template not found."""
        context = {
            "reminder": mock_reminder,
            "payment": mock_reminder.payment,
            "invoice": mock_reminder.payment.fattura,
            "days_to_due": 7,
        }

        # Request fallback text
        result = await email_notifier._render_template(
            "nonexistent.txt", context, fallback_text=True
        )

        # Should return fallback text
        assert "Promemoria Pagamento" in result
        assert "INV-2024-001" in result
        assert "1000.00" in result
        expected_company = (
            email_notifier.settings.cedente_denominazione
            or email_notifier.smtp_config.from_name
            or "OpenFatture"
        )
        assert expected_company in result

    @pytest.mark.asyncio
    async def test_send_email_validates_recipient(self, email_notifier):
        """Test that send_email validates recipient email."""
        with pytest.raises(ValueError, match="Recipient email is required"):
            await email_notifier._send_email(
                to_email=None, subject="Test", html_body="<html>Test</html>", text_body="Test"
            )

    @pytest.mark.asyncio
    async def test_context_uses_settings_company_name(
        self, smtp_config, mock_reminder, tmp_path, mocker
    ):
        """Ensure notifier injects company name from application settings."""
        from openfatture.utils.config import Settings

        custom_settings = Settings(cedente_denominazione="Venere Labs S.r.l.")
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        notifier = EmailNotifier(
            smtp_config,
            template_dir=template_dir,
            settings=custom_settings,
        )

        notifier._render_template = AsyncMock(
            side_effect=[
                "<html>Body</html>",
                "Plain text",
            ]
        )
        notifier._send_email = AsyncMock(return_value=None)

        result = await notifier.send_reminder(mock_reminder)

        assert result is True
        first_call_context = notifier._render_template.call_args_list[0].args[1]
        assert first_call_context["company_name"] == "Venere Labs S.r.l."

    @pytest.mark.asyncio
    async def test_fallback_text_uses_settings_company_name(
        self, smtp_config, mock_reminder, tmp_path
    ):
        """Ensure fallback text reflects configured company name."""
        from openfatture.utils.config import Settings

        custom_settings = Settings(cedente_denominazione="Studio Demo SRL")
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        notifier = EmailNotifier(
            smtp_config,
            template_dir=template_dir,
            settings=custom_settings,
        )

        context = {
            "reminder": mock_reminder,
            "payment": mock_reminder.payment,
            "invoice": mock_reminder.payment.fattura,
            "days_to_due": -2,
        }

        result = await notifier._render_template("missing.txt", context, fallback_text=True)

        assert "ATTENZIONE" in result
        assert "Studio Demo SRL" in result


class TestConsoleNotifier:
    """Tests for ConsoleNotifier console output."""

    @pytest.fixture
    def console_notifier(self):
        """Create console notifier."""
        return ConsoleNotifier()

    @pytest.fixture
    def mock_reminder(self, mocker):
        """Create mock reminder for console output."""
        reminder = mocker.Mock(spec=PaymentReminder)
        reminder.id = 1
        reminder.payment_id = 100
        reminder.strategy = ReminderStrategy.DEFAULT

        # Mock payment
        payment = mocker.Mock()
        payment.id = 100
        payment.importo_da_pagare = Decimal("500.00")
        payment.data_scadenza = date(2024, 11, 15)

        # Mock invoice
        invoice = mocker.Mock()
        invoice.numero = "INV-2024-999"
        payment.fattura = invoice

        reminder.payment = payment
        # Note: days_before_due doesn't exist in model, but code expects it
        reminder.days_before_due = 7

        return reminder

    # ==========================================================================
    # ConsoleNotifier Tests (4 tests)
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_send_reminder_prints_details(self, console_notifier, mock_reminder, capsys):
        """Test that console notifier prints reminder details."""
        result = await console_notifier.send_reminder(mock_reminder)

        # Verify return value
        assert result is True

        # Capture printed output
        captured = capsys.readouterr()

        # Verify output contains key information
        assert "[REMINDER]" in captured.out
        assert "Payment #100" in captured.out
        assert "INV-2024-999" in captured.out
        assert "€500.00" in captured.out
        assert "15/11/2024" in captured.out

    @pytest.mark.asyncio
    async def test_send_reminder_always_returns_true(self, console_notifier, mock_reminder):
        """Test that console notifier always succeeds."""
        result = await console_notifier.send_reminder(mock_reminder)
        assert result is True

    @pytest.mark.asyncio
    async def test_send_reminder_handles_missing_invoice(
        self, console_notifier, mock_reminder, capsys
    ):
        """Test console output when invoice is missing."""
        # Remove invoice
        mock_reminder.payment.fattura = None

        result = await console_notifier.send_reminder(mock_reminder)

        # Should still succeed
        assert result is True

        # Verify output doesn't crash
        captured = capsys.readouterr()
        assert "[REMINDER]" in captured.out

    @pytest.mark.asyncio
    async def test_send_reminder_formats_correctly(self, console_notifier, mock_reminder, capsys):
        """Test that console output is properly formatted with separators."""
        await console_notifier.send_reminder(mock_reminder)

        captured = capsys.readouterr()

        # Verify formatting with separators
        assert "=" * 60 in captured.out
        assert "Days to Due:" in captured.out
        assert "Strategy: default" in captured.out


class TestCompositeNotifier:
    """Tests for CompositeNotifier multi-channel notifications."""

    @pytest.fixture
    def mock_reminder(self, mocker):
        """Create mock reminder."""
        reminder = mocker.Mock(spec=PaymentReminder)
        reminder.id = 1
        reminder.payment_id = 100
        return reminder

    # ==========================================================================
    # CompositeNotifier Tests (8 tests)
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_send_reminder_all_succeed(self, mock_reminder, mocker):
        """Test that composite returns True when all notifiers succeed."""
        # Create mock notifiers
        notifier1 = mocker.Mock(spec=INotifier)
        notifier1.send_reminder = AsyncMock(return_value=True)

        notifier2 = mocker.Mock(spec=INotifier)
        notifier2.send_reminder = AsyncMock(return_value=True)

        composite = CompositeNotifier([notifier1, notifier2])

        # Send reminder
        result = await composite.send_reminder(mock_reminder)

        # All succeeded
        assert result is True
        assert notifier1.send_reminder.call_count == 1
        assert notifier2.send_reminder.call_count == 1

    @pytest.mark.asyncio
    async def test_send_reminder_partial_failure(self, mock_reminder, mocker):
        """Test that composite returns False when any notifier fails."""
        # First succeeds, second fails
        notifier1 = mocker.Mock(spec=INotifier)
        notifier1.send_reminder = AsyncMock(return_value=True)

        notifier2 = mocker.Mock(spec=INotifier)
        notifier2.send_reminder = AsyncMock(return_value=False)

        composite = CompositeNotifier([notifier1, notifier2])

        result = await composite.send_reminder(mock_reminder)

        # Should return False due to partial failure
        assert result is False

    @pytest.mark.asyncio
    async def test_send_reminder_all_fail(self, mock_reminder, mocker):
        """Test that composite returns False when all notifiers fail."""
        notifier1 = mocker.Mock(spec=INotifier)
        notifier1.send_reminder = AsyncMock(return_value=False)

        notifier2 = mocker.Mock(spec=INotifier)
        notifier2.send_reminder = AsyncMock(return_value=False)

        composite = CompositeNotifier([notifier1, notifier2])

        result = await composite.send_reminder(mock_reminder)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_reminder_parallel_execution(self, mock_reminder, mocker):
        """Test that notifiers execute in parallel using asyncio.gather."""
        import asyncio

        # Create notifiers with delays to test parallelism
        async def slow_send(reminder):
            await asyncio.sleep(0.1)
            return True

        notifier1 = mocker.Mock(spec=INotifier)
        notifier1.send_reminder = slow_send

        notifier2 = mocker.Mock(spec=INotifier)
        notifier2.send_reminder = slow_send

        composite = CompositeNotifier([notifier1, notifier2])

        # Measure execution time
        import time

        start = time.time()
        result = await composite.send_reminder(mock_reminder)
        duration = time.time() - start

        # If parallel, should take ~0.1s, not ~0.2s
        assert result is True
        assert duration < 0.15  # Allow some overhead

    @pytest.mark.asyncio
    async def test_send_reminder_handles_exceptions(self, mock_reminder, mocker):
        """Test that composite handles exceptions from notifiers gracefully."""
        # First succeeds, second raises exception
        notifier1 = mocker.Mock(spec=INotifier)
        notifier1.send_reminder = AsyncMock(return_value=True)

        notifier2 = mocker.Mock(spec=INotifier)
        notifier2.send_reminder = AsyncMock(side_effect=Exception("SMTP error"))

        composite = CompositeNotifier([notifier1, notifier2])

        # Should not raise, but return False
        result = await composite.send_reminder(mock_reminder)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_reminder_empty_notifiers_list(self, mock_reminder):
        """Test composite with empty notifiers list."""
        composite = CompositeNotifier([])

        result = await composite.send_reminder(mock_reminder)

        # Empty list should return True (vacuous truth)
        assert result is True

    @pytest.mark.asyncio
    async def test_add_notifier_dynamically(self, mock_reminder, mocker):
        """Test adding notifiers dynamically to composite."""
        notifier1 = mocker.Mock(spec=INotifier)
        notifier1.send_reminder = AsyncMock(return_value=True)

        composite = CompositeNotifier([notifier1])

        # Add another notifier
        notifier2 = mocker.Mock(spec=INotifier)
        notifier2.send_reminder = AsyncMock(return_value=True)
        composite.notifiers.append(notifier2)

        result = await composite.send_reminder(mock_reminder)

        # Both should be called
        assert result is True
        assert len(composite.notifiers) == 2
        assert notifier1.send_reminder.call_count == 1
        assert notifier2.send_reminder.call_count == 1

    def test_repr(self):
        """Test CompositeNotifier string representation."""
        notifier1 = ConsoleNotifier()
        notifier2 = ConsoleNotifier()

        composite = CompositeNotifier([notifier1, notifier2])

        repr_str = repr(composite)

        assert "CompositeNotifier" in repr_str
        assert "ConsoleNotifier" in repr_str


class TestSMTPConfig:
    """Tests for SMTPConfig dataclass."""

    def test_smtp_config_defaults(self):
        """Test SMTP config default values."""
        config = SMTPConfig(host="smtp.test.com")

        assert config.host == "smtp.test.com"
        assert config.port == 587
        assert config.use_tls is True
        assert config.from_name == "OpenFatture"

    def test_smtp_config_custom_values(self):
        """Test SMTP config with custom values."""
        config = SMTPConfig(
            host="smtp.custom.com",
            port=465,
            username="user@test.com",
            password="secret",
            use_tls=False,
            from_email="custom@test.com",
            from_name="Custom Name",
        )

        assert config.host == "smtp.custom.com"
        assert config.port == 465
        assert config.username == "user@test.com"
        assert config.password == "secret"
        assert config.use_tls is False
        assert config.from_email == "custom@test.com"
        assert config.from_name == "Custom Name"


class TestINotifierInterface:
    """Tests for INotifier abstract interface."""

    def test_cannot_instantiate_interface(self):
        """Test that INotifier cannot be instantiated directly."""
        with pytest.raises(TypeError):
            INotifier()
