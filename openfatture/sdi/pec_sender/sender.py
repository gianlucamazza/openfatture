"""PEC email sender for SDI submission."""

import smtplib
import ssl
from datetime import UTC, datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from openfatture.exceptions import ConfigurationError, FileNotFoundError as OFFileNotFoundError, PECError
from openfatture.storage.database.models import Fattura, LogSDI, StatoFattura
from openfatture.utils.config import Settings
from openfatture.utils.logging import get_logger
from openfatture.utils.rate_limiter import RateLimiter

logger = get_logger(__name__)


class PECSender:
    """
    PEC sender for submitting invoices to SDI.

    Sends FatturaPA XML files via certified email (PEC) to the
    Sistema di Interscambio (SDI).

    Features:
    - Rate limiting (10 emails per minute default)
    - Automatic retry with exponential backoff
    - Error handling and logging
    """

    def __init__(
        self,
        settings: Settings,
        rate_limit: RateLimiter | None = None,
        max_retries: int = 3,
    ):
        """
        Initialize PEC sender.

        Args:
            settings: Application configuration
            rate_limit: Custom rate limiter (default: 10 emails/minute)
            max_retries: Maximum retry attempts for transient errors
        """
        self.settings = settings
        # Default: 10 emails per minute to respect PEC server limits
        self.rate_limiter = rate_limit or RateLimiter(max_calls=10, period=60)
        self.max_retries = max_retries

    def send_invoice(
        self, fattura: Fattura, xml_path: Path, signed: bool = False
    ) -> tuple[bool, str | None]:
        """
        Send invoice to SDI via PEC.

        Applies rate limiting and retry logic for robust delivery.

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

        # Apply rate limiting - wait if necessary
        wait_time = self.rate_limiter.get_wait_time()
        if wait_time > 0:
            # Could log this or notify user
            import time

            time.sleep(wait_time)

        # Acquire rate limit permission
        if not self.rate_limiter.acquire(blocking=True, timeout=30):
            return False, "Rate limit exceeded. Please try again later."

        # Send with retry logic
        return self._send_with_retry(fattura, xml_path, signed)

    def _send_with_retry(
        self, fattura: Fattura, xml_path: Path, signed: bool = False
    ) -> tuple[bool, str | None]:
        """
        Send email with retry logic for transient errors.

        Args:
            fattura: Invoice model
            xml_path: Path to XML file
            signed: Whether the XML is signed

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        import time

        from openfatture.utils.rate_limiter import ExponentialBackoff

        backoff = ExponentialBackoff(base=1.0, max_delay=30.0)
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # Create message
                msg = MIMEMultipart()
                msg["From"] = self.settings.pec_address
                msg["To"] = self.settings.sdi_pec_address
                msg["Subject"] = f"Fattura {fattura.numero}/{fattura.anno}"

                # Add body
                body = self._create_email_body(fattura)
                msg.attach(MIMEText(body, "plain", "utf-8"))

                # Attach XML file
                filename = xml_path.name
                with open(xml_path, "rb") as f:
                    attachment = MIMEBase("application", "xml" if not signed else "pkcs7-mime")
                    attachment.set_payload(f.read())
                    encoders.encode_base64(attachment)
                    attachment.add_header(
                        "Content-Disposition", f'attachment; filename="{filename}"'
                    )
                    msg.attach(attachment)

                # Send via SMTP
                context = ssl.create_default_context()

                with smtplib.SMTP_SSL(
                    self.settings.pec_smtp_server,
                    self.settings.pec_smtp_port,
                    context=context,
                ) as server:
                    server.login(self.settings.pec_address, self.settings.pec_password)
                    server.send_message(msg)

                # Update invoice status
                fattura.stato = StatoFattura.INVIATA
                fattura.data_invio_sdi = datetime.now(UTC)

                return True, None

            except smtplib.SMTPAuthenticationError:
                # Authentication errors are not transient - don't retry
                return False, "PEC authentication failed. Check credentials."

            except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError, ConnectionError) as e:
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
                return False, f"Error sending PEC: {e}"

        # All retry attempts failed
        return False, f"Failed after {self.max_retries} attempts. Last error: {last_error}"

    def _create_email_body(self, fattura: Fattura) -> str:
        """
        Create email body text.

        Args:
            fattura: Invoice model

        Returns:
            str: Email body
        """
        return f"""Electronic invoice submission to the SDI (Sistema di Interscambio)

Sender: {self.settings.cedente_denominazione}
VAT number: {self.settings.cedente_partita_iva}

Invoice no. {fattura.numero}/{fattura.anno}
Issue date: {fattura.data_emissione.isoformat()}
Customer: {fattura.cliente.denominazione}
Total amount: €{fattura.totale:.2f}

This message was generated automatically by OpenFatture.
"""

    def send_test_email(self) -> tuple[bool, str | None]:
        """
        Send a test email to verify PEC configuration.

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        if not self.settings.pec_address:
            return False, "PEC address not configured"

        if not self.settings.pec_password:
            return False, "PEC password not configured"

        try:
            msg = MIMEMultipart()
            msg["From"] = self.settings.pec_address
            msg["To"] = self.settings.pec_address  # Send to self for testing
            msg["Subject"] = "OpenFatture - Test PEC Configuration"

            body = """This is a test message to verify the PEC configuration.

If you receive this message, your PEC setup is correct.

OpenFatture
"""
            msg.attach(MIMEText(body, "plain", "utf-8"))

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
            return False, "Authentication failed. Check PEC credentials."

        except smtplib.SMTPException as e:
            return False, f"SMTP error: {e}"

        except Exception as e:
            return False, f"Error: {e}"


def create_log_entry(
    fattura: Fattura, tipo: str, descrizione: str, xml_path: Path | None = None
) -> LogSDI:
    """
    Create a log entry for SDI communication.

    Args:
        fattura: Invoice model
        tipo: Notification type (RC, NS, MC, etc.)
        descrizione: Description
        xml_path: Optional path to notification XML

    Returns:
        LogSDI: Log entry
    """
    return LogSDI(
        fattura_id=fattura.id,
        tipo_notifica=tipo,
        descrizione=descrizione,
        xml_path=str(xml_path) if xml_path else None,
        data_ricezione=datetime.now(UTC),
    )
