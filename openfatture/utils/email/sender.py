"""
Enhanced PEC sender with email template support.

Extends PECSender with professional HTML+text email templates
for SDI notifications, batch operations, and testing.
"""

import smtplib
import ssl
from datetime import UTC, datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from openfatture.core.batch.processor import BatchResult
from openfatture.sdi.notifiche.parser import NotificaSDI, TipoNotifica
from openfatture.storage.database.models import Fattura, StatoFattura
from openfatture.utils.config import Settings
from openfatture.utils.email.models import (
    BatchSummaryContext,
    EmailAttachment,
    EmailMessage,
    EmailTestContext,
    FatturaInvioContext,
    NotificaSDIContext,
)
from openfatture.utils.email.renderer import TemplateRenderer
from openfatture.utils.rate_limiter import ExponentialBackoff, RateLimiter


class TemplatePECSender:
    """
    PEC sender with template support.

    Enhanced email sender that uses professional HTML+text templates
    for all email types. Maintains backward compatibility with PECSender.

    Features:
    - HTML + text multipart emails
    - Professional templates with i18n
    - Rate limiting (10 emails/minute default)
    - Retry with exponential backoff
    - Type-safe contexts with Pydantic

    Usage:
        sender = TemplatePECSender(settings)
        success, error = sender.send_invoice_to_sdi(fattura, xml_path)
        success, error = sender.notify_consegna(fattura, notification)
    """

    def __init__(
        self,
        settings: Settings,
        rate_limit: RateLimiter | None = None,
        max_retries: int = 3,
        locale: str = "it",
    ):
        """
        Initialize template PEC sender.

        Args:
            settings: Application settings
            rate_limit: Custom rate limiter (default: 10 emails/minute)
            max_retries: Maximum retry attempts for transient errors
            locale: Language code for templates (it, en)
        """
        self.settings = settings
        self.rate_limiter = rate_limit or RateLimiter(max_calls=10, period=60)
        self.max_retries = max_retries
        self.locale = locale

        # Initialize template renderer
        self.renderer = TemplateRenderer(settings=settings, locale=locale)

    def send_invoice_to_sdi(
        self, fattura: Fattura, xml_path: Path, signed: bool = False
    ) -> tuple[bool, str | None]:
        """
        Send invoice to SDI via PEC with professional template.

        Args:
            fattura: Invoice model
            xml_path: Path to XML file (or .p7m if signed)
            signed: Whether the XML is digitally signed

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        # Validate configuration
        if not self.settings.pec_address:
            return False, "PEC address not configured"
        if not self.settings.pec_password:
            return False, "PEC password not configured"
        if not xml_path.exists():
            return False, f"XML file not found: {xml_path}"

        # Create context for template
        context = FatturaInvioContext(
            fattura=fattura,
            cedente={
                "denominazione": self.settings.cedente_denominazione,
                "partita_iva": self.settings.cedente_partita_iva,
                "indirizzo": self.settings.cedente_indirizzo,
                "cap": self.settings.cedente_cap,
                "comune": self.settings.cedente_comune,
            },
            destinatario=self.settings.sdi_pec_address,
            is_signed=signed,
            xml_filename=xml_path.name,
        )

        # Render template
        try:
            html_body, text_body = self.renderer.render_both("sdi/invio_fattura", context)
        except Exception as e:
            return False, f"Template rendering failed: {e}"

        # Create attachment
        attachment = EmailAttachment(
            filename=xml_path.name,
            content=xml_path.read_bytes(),
            mime_type="application/pkcs7-mime" if signed else "application/xml",
        )

        # Create email message
        subject = self.renderer.translations["email"]["sdi"]["invio_fattura"]["subject"]
        subject = subject.replace("{{numero}}", fattura.numero).replace(
            "{{anno}}", str(fattura.anno)
        )

        email = EmailMessage(
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            recipients=[self.settings.sdi_pec_address],
            attachments=[attachment],
        )

        # Send with rate limiting and retry
        success, error = self._send_email(email)

        if success:
            # Update invoice status
            fattura.stato = StatoFattura.INVIATA
            fattura.data_invio_sdi = datetime.now(UTC)

        return success, error

    def notify_consegna(
        self, fattura: Fattura, notification: NotificaSDI
    ) -> tuple[bool, str | None]:
        """
        Send delivery notification email to user.

        Args:
            fattura: Invoice that was delivered
            notification: SDI notification data

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        return self._send_notification_email(fattura, notification, TipoNotifica.RICEVUTA_CONSEGNA)

    def notify_scarto(self, fattura: Fattura, notification: NotificaSDI) -> tuple[bool, str | None]:
        """
        Send rejection notification email to user.

        Args:
            fattura: Invoice that was rejected
            notification: SDI notification data

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        return self._send_notification_email(fattura, notification, TipoNotifica.NOTIFICA_SCARTO)

    def notify_attestazione_trasmissione(
        self, fattura: Fattura, notification: NotificaSDI
    ) -> tuple[bool, str | None]:
        """Send transmission attestation notification."""
        return self._send_notification_email(
            fattura, notification, TipoNotifica.ATTESTAZIONE_TRASMISSIONE
        )

    def notify_mancata_consegna(
        self, fattura: Fattura, notification: NotificaSDI
    ) -> tuple[bool, str | None]:
        """Send failed delivery notification."""
        return self._send_notification_email(fattura, notification, TipoNotifica.MANCATA_CONSEGNA)

    def notify_esito(
        self, fattura: Fattura, notification: NotificaSDI, accepted: bool
    ) -> tuple[bool, str | None]:
        """Send outcome notification (acceptance or rejection by customer)."""
        template_name = (
            "sdi/notifica_esito_accettata" if accepted else "sdi/notifica_esito_rifiutata"
        )
        return self._send_notification_email(
            fattura, notification, TipoNotifica.NOTIFICA_ESITO, template_name=template_name
        )

    def send_batch_summary(
        self, result: BatchResult, operation_type: str, recipients: list[str]
    ) -> tuple[bool, str | None]:
        """
        Send batch operation summary email.

        Args:
            result: Batch operation result
            operation_type: Type of operation (import, export, validate, send)
            recipients: Email recipients

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        if not recipients:
            return False, "No recipients specified"

        # Create context
        context = BatchSummaryContext(
            result=result,
            operation_type=operation_type,
            timestamp=datetime.now(),
        )

        # Render template
        try:
            html_body, text_body = self.renderer.render_both("batch/riepilogo_batch", context)
        except Exception as e:
            return False, f"Template rendering failed: {e}"

        # Create subject
        subject = self.renderer.translations["email"]["batch"]["summary"]["subject"]
        subject = subject.replace("{{operation}}", operation_type)

        email = EmailMessage(
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            recipients=recipients,
        )

        return self._send_email(email)

    def send_test_email(self) -> tuple[bool, str | None]:
        """
        Send test email to verify PEC configuration.

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        if not self.settings.pec_address:
            return False, "PEC address not configured"
        if not self.settings.pec_password:
            return False, "PEC password not configured"

        # Create context
        context = EmailTestContext(
            smtp_server=self.settings.pec_smtp_server,
            smtp_port=self.settings.pec_smtp_port,
            pec_address=self.settings.pec_address,
            test_time=datetime.now(),
        )

        # Render template
        try:
            html_body, text_body = self.renderer.render_both("test/test_email", context)
        except Exception as e:
            return False, f"Template rendering failed: {e}"

        subject = self.renderer.translations["email"]["test"]["subject"]

        email = EmailMessage(
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            recipients=[self.settings.pec_address],  # Send to self
        )

        return self._send_email(email)

    def _send_notification_email(
        self,
        fattura: Fattura,
        notification: NotificaSDI,
        tipo_notifica: TipoNotifica,
        template_name: str | None = None,
    ) -> tuple[bool, str | None]:
        """
        Send SDI notification email to user.

        Args:
            fattura: Related invoice
            notification: SDI notification
            tipo_notifica: Notification type
            template_name: Override template name

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        # Check if notification emails are enabled
        if not getattr(self.settings, "notification_enabled", True):
            return True, None  # Silently skip

        recipient = getattr(self.settings, "notification_email", None)
        if not recipient:
            return False, "Notification email not configured"

        # Create context
        context = NotificaSDIContext(
            notification=notification,
            fattura=fattura,
            cliente=fattura.cliente,
            tipo_notifica=tipo_notifica,
        )

        # Determine template name
        if template_name is None:
            template_map = {
                TipoNotifica.RICEVUTA_CONSEGNA: "sdi/notifica_consegna",
                TipoNotifica.NOTIFICA_SCARTO: "sdi/notifica_scarto",
                TipoNotifica.ATTESTAZIONE_TRASMISSIONE: "sdi/notifica_attestazione",
                TipoNotifica.MANCATA_CONSEGNA: "sdi/notifica_mancata_consegna",
            }
            template_name = template_map.get(tipo_notifica)

        if not template_name:
            return False, f"No template for notification type: {tipo_notifica}"

        # Render template
        try:
            html_body, text_body = self.renderer.render_both(template_name, context)
        except Exception as e:
            return False, f"Template rendering failed: {e}"

        # Get subject from i18n
        tipo_key = tipo_notifica.value.lower()
        subject_key = (
            f"email.sdi.notifica_{tipo_key}.subject"
            if tipo_key != "rc"
            else "email.sdi.notifica_consegna.subject"
        )

        # Fallback subject
        subject = f"Notifica SDI - Fattura {fattura.numero}/{fattura.anno}"

        try:
            subject_template = self.renderer.translations
            for key in subject_key.split("."):
                subject_template = subject_template[key]
            subject = subject_template.replace("{{numero}}", fattura.numero).replace(
                "{{anno}}", str(fattura.anno)
            )
        except (KeyError, TypeError):
            pass  # Use fallback

        email = EmailMessage(
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            recipients=[recipient],
        )

        return self._send_email(email)

    def _send_email(self, email: EmailMessage) -> tuple[bool, str | None]:
        """
        Send email with rate limiting and retry logic.

        Args:
            email: Email message to send

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        # Apply rate limiting
        wait_time = self.rate_limiter.get_wait_time()
        if wait_time > 0:
            import time

            time.sleep(wait_time)

        if not self.rate_limiter.acquire(blocking=True, timeout=30):
            return False, "Rate limit exceeded. Please try again later."

        # Send with retry logic
        return self._send_with_retry(email)

    def _send_with_retry(self, email: EmailMessage) -> tuple[bool, str | None]:
        """
        Send email with retry logic for transient errors.

        Args:
            email: Email message to send

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        import time

        backoff = ExponentialBackoff(base=1.0, max_delay=30.0)
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # Create multipart message
                msg = MIMEMultipart("alternative")
                msg["From"] = self.settings.pec_address
                msg["To"] = ", ".join(email.recipients)
                msg["Subject"] = email.subject

                # Add text part (plain text fallback)
                text_part = MIMEText(email.text_body, "plain", "utf-8")
                msg.attach(text_part)

                # Add HTML part
                html_part = MIMEText(email.html_body, "html", "utf-8")
                msg.attach(html_part)

                # Add attachments
                for attachment in email.attachments:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.content)
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{attachment.filename}"',
                    )
                    msg.attach(part)

                # Send via SMTP
                context = ssl.create_default_context()

                with smtplib.SMTP_SSL(
                    self.settings.pec_smtp_server,
                    self.settings.pec_smtp_port,
                    context=context,
                ) as server:
                    server.login(self.settings.pec_address, self.settings.pec_password)
                    server.send_message(msg)

                return True, None

            except smtplib.SMTPAuthenticationError:
                # Authentication errors are permanent - don't retry
                return False, "PEC authentication failed. Check credentials."

            except (
                smtplib.SMTPServerDisconnected,
                smtplib.SMTPConnectError,
                ConnectionError,
            ) as e:
                # Transient network errors - retry with backoff
                last_error = str(e)
                if attempt < self.max_retries - 1:
                    delay = backoff.get_delay(attempt)
                    time.sleep(delay)
                continue

            except smtplib.SMTPException as e:
                # Other SMTP errors
                last_error = str(e)
                if attempt < self.max_retries - 1:
                    delay = backoff.get_delay(attempt)
                    time.sleep(delay)
                continue

            except Exception as e:
                # Unexpected errors - return immediately
                return False, f"Error sending email: {e}"

        # All retry attempts failed
        return False, f"Failed after {self.max_retries} attempts. Last error: {last_error}"
