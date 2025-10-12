"""Notification system for payment reminders.

Implements Strategy pattern for multiple notification channels.
"""

import asyncio
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import TYPE_CHECKING

import structlog
from jinja2 import Environment, FileSystemLoader

from openfatture.utils.config import Settings, get_settings

if TYPE_CHECKING:
    from ...domain.models import PaymentReminder

logger = structlog.get_logger()


@dataclass
class SMTPConfig:
    """SMTP server configuration."""

    host: str
    port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    from_email: str = ""
    from_name: str = "OpenFatture"


class INotifier(ABC):
    """Abstract notifier interface.

    Design Pattern: Strategy
    SOLID: Interface Segregation (focused interface for notification)
    """

    @abstractmethod
    async def send_reminder(self, reminder: "PaymentReminder") -> bool:
        """Send payment reminder notification.

        Args:
            reminder: PaymentReminder entity

        Returns:
            True if sent successfully, False otherwise
        """
        pass


class EmailNotifier(INotifier):
    """Email-based reminder notifications using SMTP.

    Features:
    - HTML email templates with Jinja2
    - SMTP with TLS support
    - Template rendering with payment context
    - Error handling and logging

    Example:
        >>> config = SMTPConfig(
        ...     host="smtp.gmail.com",
        ...     port=587,
        ...     username="your@email.com",
        ...     password="yourpassword",
        ...     from_email="noreply@openfatture.com"
        ... )
        >>> notifier = EmailNotifier(config, template_dir=Path("templates"))
        >>> await notifier.send_reminder(reminder)
    """

    def __init__(
        self,
        smtp_config: SMTPConfig,
        template_dir: Path | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize email notifier.

        Args:
            smtp_config: SMTP server configuration
            template_dir: Directory containing email templates
        """
        self.smtp_config = smtp_config
        self.settings = settings or get_settings()
        self.env: Environment | None = None

        # Setup Jinja2 environment
        if template_dir and template_dir.exists():
            self.env = Environment(loader=FileSystemLoader(template_dir))
        else:
            # Use default template directory
            default_template_dir = Path(__file__).parent.parent.parent / "templates"
            if default_template_dir.exists():
                self.env = Environment(loader=FileSystemLoader(default_template_dir))
            else:
                logger.warning("email_template_dir_not_found", template_dir=template_dir)

    async def send_reminder(self, reminder: "PaymentReminder") -> bool:
        """Send payment reminder via email.

        Workflow:
        1. Load payment + invoice data
        2. Render email template with context
        3. Send via SMTP
        4. Log result

        Args:
            reminder: PaymentReminder entity

        Returns:
            True if sent successfully
        """
        try:
            # Get payment and invoice
            payment = reminder.payment
            invoice = payment.fattura if hasattr(payment, "fattura") else None

            if not invoice:
                logger.error(
                    "reminder_missing_invoice",
                    reminder_id=reminder.id,
                    payment_id=reminder.payment_id,
                )
                return False

            # Prepare email context
            context = {
                "reminder": reminder,
                "payment": payment,
                "invoice": invoice,
                "days_to_due": reminder.days_before_due,
                "company_name": (
                    self.settings.cedente_denominazione
                    or self.smtp_config.from_name
                    or "OpenFatture"
                ),
            }

            # Render template
            html_body = await self._render_template("reminder_email.html", context)
            text_body = await self._render_template(
                "reminder_email.txt", context, fallback_text=True
            )

            # Send email
            await self._send_email(
                to_email=invoice.cliente.email if hasattr(invoice, "cliente") else None,
                subject=f"Payment Reminder - Invoice {invoice.numero}",
                html_body=html_body,
                text_body=text_body,
            )

            logger.info(
                "reminder_sent",
                reminder_id=reminder.id,
                payment_id=reminder.payment_id,
                invoice_number=invoice.numero,
            )

            return True

        except Exception as e:
            logger.error(
                "reminder_send_failed",
                reminder_id=reminder.id,
                error=str(e),
            )
            return False

    async def _render_template(
        self,
        template_name: str,
        context: dict,
        fallback_text: bool = False,
    ) -> str:
        """Render Jinja2 template with context.

        Args:
            template_name: Template filename
            context: Template context variables
            fallback_text: If True and template not found, return simple text

        Returns:
            Rendered template string
        """
        if self.env:
            try:
                template = self.env.get_template(template_name)
                return template.render(**context)
            except Exception as e:
                logger.warning(
                    "template_render_failed",
                    template=template_name,
                    error=str(e),
                )

        # Fallback: simple text
        if fallback_text:
            return self._get_fallback_text(context)

        return ""

    def _get_fallback_text(self, context: dict) -> str:
        """Generate simple fallback text when template not available.

        Args:
            context: Email context

        Returns:
            Simple text message
        """
        payment = context.get("payment")
        invoice = context.get("invoice")
        days_to_due = context.get("days_to_due", 0)

        if days_to_due < 0:
            status = f"ATTENTION: {abs(days_to_due)} days overdue"
        elif days_to_due == 0:
            status = "DUE TODAY"
        else:
            status = f"Due in {days_to_due} days"

        company_name = (
            context.get("company_name")
            or self.settings.cedente_denominazione
            or self.smtp_config.from_name
            or "OpenFatture"
        )

        return f"""
Payment Reminder

{status}

Invoice: {invoice.numero if invoice else 'N/A'}
Amount: €{payment.importo_da_pagare if payment else 0}
Due date: {payment.data_scadenza.strftime('%d/%m/%Y') if payment else 'N/A'}

Kind regards,
{company_name}
        """.strip()

    async def _send_email(
        self,
        to_email: str | None,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> None:
        """Send email via SMTP.

        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML body
            text_body: Plain text body

        Raises:
            ValueError: If to_email is None
            smtplib.SMTPException: If sending fails
        """
        if not to_email:
            raise ValueError("Recipient email is required")

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.smtp_config.from_name} <{self.smtp_config.from_email}>"
        msg["To"] = to_email

        # Attach both text and HTML parts
        part1 = MIMEText(text_body, "plain", "utf-8")
        part2 = MIMEText(html_body, "html", "utf-8")

        msg.attach(part1)
        msg.attach(part2)

        # Send via SMTP
        with smtplib.SMTP(self.smtp_config.host, self.smtp_config.port) as server:
            if self.smtp_config.use_tls:
                server.starttls()

            if self.smtp_config.username and self.smtp_config.password:
                server.login(self.smtp_config.username, self.smtp_config.password)

            server.send_message(msg)

        logger.debug("email_sent", to=to_email, subject=subject)


class ConsoleNotifier(INotifier):
    """Console output notifier for development/testing.

    Prints reminder details to console instead of sending actual notifications.
    """

    async def send_reminder(self, reminder: "PaymentReminder") -> bool:
        """Print reminder to console.

        Args:
            reminder: PaymentReminder entity

        Returns:
            Always True
        """
        payment = reminder.payment
        invoice = payment.fattura if hasattr(payment, "fattura") else None

        print(f"\n{'='*60}")
        print(f"[REMINDER] Payment #{reminder.payment_id}")
        print(f"{'='*60}")
        if invoice:
            print(f"Invoice: {invoice.numero}")
        print(f"Amount: €{payment.importo_da_pagare if payment else 0}")
        print(f"Due Date: {payment.data_scadenza.strftime('%d/%m/%Y') if payment else 'N/A'}")
        print(f"Days to Due: {reminder.days_before_due}")
        print(f"Strategy: {reminder.strategy.value if reminder.strategy else 'N/A'}")
        print(f"{'='*60}\n")

        return True


class CompositeNotifier(INotifier):
    """Composite notifier for sending via multiple channels.

    Implements Composite pattern to send notifications through multiple
    channels (email + SMS + webhook) simultaneously.

    Example:
        >>> notifier = CompositeNotifier([
        ...     EmailNotifier(smtp_config),
        ...     SMSNotifier(sms_config),
        ...     WebhookNotifier(webhook_url)
        ... ])
        >>> await notifier.send_reminder(reminder)  # Sends to all channels
    """

    def __init__(self, notifiers: list[INotifier]) -> None:
        """Initialize composite notifier.

        Args:
            notifiers: List of notifier instances
        """
        self.notifiers = notifiers

    async def send_reminder(self, reminder: "PaymentReminder") -> bool:
        """Send reminder via all configured channels.

        Args:
            reminder: PaymentReminder entity

        Returns:
            True if ALL notifiers succeeded, False if any failed
        """
        results = await asyncio.gather(
            *[notifier.send_reminder(reminder) for notifier in self.notifiers],
            return_exceptions=True,
        )

        # Check if all succeeded
        success = all(
            result is True if not isinstance(result, Exception) else False for result in results
        )

        if not success:
            logger.warning(
                "composite_notifier_partial_failure",
                reminder_id=reminder.id,
                total_notifiers=len(self.notifiers),
                results=results,
            )

        return success

    def __repr__(self) -> str:
        """Human-readable string representation."""
        notifier_types = [n.__class__.__name__ for n in self.notifiers]
        return f"<CompositeNotifier(channels=[{', '.join(notifier_types)}])>"
