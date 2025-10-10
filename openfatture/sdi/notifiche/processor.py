"""
SDI notification processor.

Processes parsed notifications and updates invoice status in database.
Optionally sends email notifications to configured recipients.
"""

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from openfatture.sdi.notifiche.parser import NotificaSDI, SDINotificationParser, TipoNotifica
from openfatture.storage.database.models import Fattura, LogSDI, StatoFattura


class NotificationProcessor:
    """
    Processes SDI notifications and updates database.

    Updates invoice status based on SDI notification type.

    Usage:
        processor = NotificationProcessor(db_session)
        processor.process_file(Path("RC_IT01234567890_00001.xml"))
    """

    # Mapping notification types to invoice status
    STATUS_MAPPING = {
        TipoNotifica.ATTESTAZIONE_TRASMISSIONE: StatoFattura.INVIATA,  # Sent to SDI
        TipoNotifica.RICEVUTA_CONSEGNA: StatoFattura.CONSEGNATA,  # Delivered to recipient
        TipoNotifica.NOTIFICA_SCARTO: StatoFattura.SCARTATA,  # Rejected by SDI
        TipoNotifica.MANCATA_CONSEGNA: StatoFattura.ERRORE,  # Delivery failed
        TipoNotifica.NOTIFICA_ESITO: None,  # Depends on esito value
    }

    def __init__(self, db_session: Session, email_sender: Any | None = None):
        """
        Initialize notification processor.

        Args:
            db_session: SQLAlchemy database session
            email_sender: Optional TemplatePECSender for email notifications
        """
        self.db = db_session
        self.parser = SDINotificationParser()
        self.email_sender = email_sender

    def process_file(self, xml_path: Path) -> tuple[bool, str | None, NotificaSDI | None]:
        """
        Process notification XML file.

        Args:
            xml_path: Path to notification XML

        Returns:
            Tuple[bool, Optional[str], Optional[NotificaSDI]]: (success, error, notification)
        """
        # Parse notification
        success, error, notification = self.parser.parse_file(xml_path)

        if not success:
            return False, f"Parsing failed: {error}", None

        if notification is None:
            return False, "Notification parsing returned None", None

        # Process notification
        return self.process_notification(notification)

    def process_notification(
        self, notification: NotificaSDI
    ) -> tuple[bool, str | None, NotificaSDI | None]:
        """
        Process parsed notification and update database.

        Args:
            notification: Parsed notification

        Returns:
            Tuple[bool, Optional[str], Optional[NotificaSDI]]: (success, error, notification)
        """
        try:
            # Find invoice by SDI identifier or filename
            fattura = self._find_invoice(notification)

            if not fattura:
                return (
                    False,
                    f"Invoice not found for notification: {notification.identificativo_sdi}",
                    notification,
                )

            # Update invoice status based on notification type
            new_status = self._determine_new_status(notification)

            if new_status:
                fattura.stato = new_status

            # Store notification details in notes/metadata
            self._add_notification_note(fattura, notification)

            # Save notification to database log
            log_sdi = LogSDI(
                fattura_id=fattura.id,
                tipo_notifica=notification.tipo.value,
                descrizione=notification.messaggio or "",
                data_ricezione=notification.data_ricezione,
            )
            self.db.add(log_sdi)

            # Commit changes
            self.db.commit()

            # Send email notification if email sender is configured
            if self.email_sender:
                self._send_email_notification(fattura, notification)

            return True, None, notification

        except Exception as e:
            self.db.rollback()
            return False, f"Failed to process notification: {e}", notification

    def _find_invoice(self, notification: NotificaSDI) -> Fattura | None:
        """
        Find invoice by SDI identifier or filename.

        Args:
            notification: Notification data

        Returns:
            Invoice if found, None otherwise
        """
        # Try to find by SDI identifier (stored in progressivo_invio or similar)
        # For now, we'll search by filename pattern
        # In production, you'd store the SDI ID when sending the invoice

        # Extract invoice number from filename (e.g., IT01234567890_00001.xml)
        # This is a simplified approach - adjust based on your filename format
        filename = notification.nome_file

        # Try to match invoices - this is a basic implementation
        # In production, store SDI identifier when sending invoice
        fatture = self.db.query(Fattura).all()

        for fattura in fatture:
            # Match based on invoice number pattern in filename
            # This is simplified - implement proper matching logic
            if f"{fattura.numero}" in filename or f"{fattura.anno}" in filename:
                return fattura

        return None

    def _determine_new_status(self, notification: NotificaSDI) -> StatoFattura | None:
        """
        Determine new invoice status from notification.

        Args:
            notification: Notification data

        Returns:
            New status or None if no change needed
        """
        if notification.tipo in self.STATUS_MAPPING:
            status = self.STATUS_MAPPING[notification.tipo]

            # Special handling for NotificaEsito
            if notification.tipo == TipoNotifica.NOTIFICA_ESITO:
                if notification.esito_committente == "EC01":
                    return StatoFattura.ACCETTATA  # Accepted by recipient
                elif notification.esito_committente == "EC02":
                    return StatoFattura.RIFIUTATA  # Rejected by recipient

            return status

        return None

    def _add_notification_note(self, fattura: Fattura, notification: NotificaSDI) -> None:
        """
        Add notification details to invoice notes.

        Args:
            fattura: Invoice to update
            notification: Notification data
        """
        note = (
            f"SDI Notification ({notification.tipo.value}): "
            f"{notification.messaggio} "
            f"[{notification.data_ricezione.isoformat()}]"
        )

        # Add errors if any
        if notification.lista_errori:
            note += f"\nErrors: {'; '.join(notification.lista_errori)}"

        # Append to existing notes or create new
        if fattura.note:
            fattura.note += f"\n{note}"
        else:
            fattura.note = note

    def _send_email_notification(self, fattura: Fattura, notification: NotificaSDI) -> None:
        """
        Send email notification for SDI event.

        Args:
            fattura: Invoice related to notification
            notification: Notification data
        """
        try:
            # Determine which notification method to call based on type
            if notification.tipo == TipoNotifica.ATTESTAZIONE_TRASMISSIONE:
                self.email_sender.notify_attestazione_trasmissione(fattura, notification)
            elif notification.tipo == TipoNotifica.RICEVUTA_CONSEGNA:
                self.email_sender.notify_consegna(fattura, notification)
            elif notification.tipo == TipoNotifica.NOTIFICA_SCARTO:
                self.email_sender.notify_scarto(fattura, notification)
            elif notification.tipo == TipoNotifica.MANCATA_CONSEGNA:
                self.email_sender.notify_mancata_consegna(fattura, notification)
            elif notification.tipo == TipoNotifica.NOTIFICA_ESITO:
                # Determine if accepted or rejected
                accepted = notification.esito_committente == "EC01"
                self.email_sender.notify_esito(fattura, notification, accepted)

        except Exception as e:
            # Log error but don't fail the notification processing
            # In production, use proper logging
            print(f"Warning: Failed to send email notification: {e}")


def process_notification_directory(
    notification_dir: Path, db_session: Session
) -> tuple[int, int, list[str]]:
    """
    Process all notifications in a directory.

    Args:
        notification_dir: Directory containing notification XML files
        db_session: Database session

    Returns:
        Tuple[int, int, list[str]]: (processed_count, error_count, error_messages)
    """
    processor = NotificationProcessor(db_session)

    processed = 0
    errors = 0
    error_messages = []

    # Find all XML files
    for xml_file in notification_dir.glob("*.xml"):
        success, error, _ = processor.process_file(xml_file)

        if success:
            processed += 1
        else:
            errors += 1
            error_messages.append(f"{xml_file.name}: {error}")

    return processed, errors, error_messages
