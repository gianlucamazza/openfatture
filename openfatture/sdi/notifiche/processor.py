"""
SDI notification processor.

Processes parsed notifications and updates invoice status in database.
Optionally sends email notifications to configured recipients.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from openfatture.billing.application.invoice_status import change_status, receipt_transition
from openfatture.events import SDINotificationReceivedEvent, get_global_event_bus
from openfatture.platform.logging import get_logger
from openfatture.sdi.notifiche.parser import NotificaSDI, SDINotificationParser, TipoNotifica
from openfatture.storage.database.models import (
    Fattura,
    LogSDI,
    SDIInvoiceIdentity,
    SDINotificationRecord,
    SDISubmissionAttempt,
    StatoFattura,
)

logger = get_logger(__name__)

# (success, error, notification) as returned to callers.
type ProcessingResult = tuple[bool, str | None, NotificaSDI | None]


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
        TipoNotifica.ATTESTAZIONE_TRASMISSIONE: StatoFattura.ERRORE,  # Transmission attested but delivery impossible
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

    def process_file(self, xml_path: Path) -> ProcessingResult:
        """
        Process notification XML file.

        Args:
            xml_path: Path to notification XML

        Returns:
            Tuple[bool, Optional[str], Optional[NotificaSDI]]: (success, error, notification)
        """
        raw = xml_path.read_text(encoding="utf-8") if xml_path.exists() else None
        success, error, notification = self.parser.parse_file(xml_path)
        if not success or notification is None:
            if raw is not None:
                digest = hashlib.sha256(raw.encode()).hexdigest()
                if not self.db.query(SDINotificationRecord).filter_by(raw_sha256=digest).first():
                    self.db.add(
                        SDINotificationRecord(
                            fingerprint=digest,
                            raw_sha256=digest,
                            payload="{}",
                            raw_xml=raw,
                            outcome="unsupported",
                            reason=error,
                        )
                    )
                    self.db.commit()
            return False, f"Parsing failed: {error}", None
        return self.process_notification(notification, raw_xml=raw)

    def process_notification(
        self,
        notification: NotificaSDI,
        *,
        raw_xml: str | None = None,
        associated_invoice_id: int | None = None,
        association_note: str | None = None,
    ) -> ProcessingResult:
        """Persist evidence, associate exactly, and apply a conditional transition."""
        try:
            outcome = self._record_and_apply(
                notification, raw_xml, associated_invoice_id, association_note
            )
        except IntegrityError:
            self.db.rollback()
            return (
                False,
                "Duplicate or conflicting concurrent SDI receipt; reload before retrying",
                notification,
            )
        except Exception as exc:
            self.db.rollback()
            return False, f"Failed to process notification: {exc}", notification
        if not isinstance(outcome, Fattura):
            return outcome
        self._announce(outcome, notification)
        return True, None, notification

    def _record_and_apply(
        self,
        notification: NotificaSDI,
        raw_xml: str | None,
        associated_invoice_id: int | None,
        association_note: str | None,
    ) -> Fattura | ProcessingResult:
        """Store the receipt evidence; return the updated invoice or the final result."""
        payload = notification.model_dump(mode="json")
        semantic = {k: v for k, v in payload.items() if k != "data_ricezione"}
        fingerprint = hashlib.sha256(json.dumps(semantic, sort_keys=True).encode()).hexdigest()
        record = self.db.query(SDINotificationRecord).filter_by(fingerprint=fingerprint).first()
        if record and (
            associated_invoice_id is None
            or record.outcome not in {"unassociated", "association_conflict"}
        ):
            return (
                record.outcome == "applied",
                None if record.outcome == "applied" else record.outcome,
                notification,
            )
        if record is None:
            record = SDINotificationRecord(
                fingerprint=fingerprint,
                payload=json.dumps(payload),
                raw_xml=raw_xml,
                raw_sha256=hashlib.sha256(raw_xml.encode()).hexdigest() if raw_xml else None,
                outcome="unassociated",
            )
            self.db.add(record)
        try:
            invoice = self._find_invoice(notification)
        except ValueError as exc:
            record.outcome, record.reason = "association_conflict", str(exc)
            self.db.commit()
            return False, str(exc), notification
        if associated_invoice_id is not None:
            invoice = self._associate_manually(
                record, invoice, associated_invoice_id, association_note
            )
        if invoice is None:
            self.db.commit()
            return (
                False,
                f"Invoice not found for notification: {notification.identificativo_sdi}",
                notification,
            )
        return self._apply_receipt(record, invoice, notification)

    def _associate_manually(
        self,
        record: SDINotificationRecord,
        matched: Fattura | None,
        invoice_id: int,
        note: str | None,
    ) -> Fattura | None:
        """Bind the receipt to an operator-chosen invoice, never against recorded identity."""
        if not note or not note.strip():
            raise ValueError("Manual association requires evidence/reference notes")
        if matched is not None and matched.id != invoice_id:
            raise ValueError("Explicit association contradicts recorded identity")
        invoice = self.db.get(Fattura, invoice_id)
        record.reason = note
        record.source = "manual_association"
        return invoice

    def _apply_receipt(
        self, record: SDINotificationRecord, invoice: Fattura, notification: NotificaSDI
    ) -> Fattura | ProcessingResult:
        """Apply the receipt's status transition to ``invoice`` and commit the evidence."""
        if invoice.numero_sdi and invoice.numero_sdi != notification.identificativo_sdi:
            raise ValueError("SDI identifier conflicts with recorded invoice")
        record.invoice_id = invoice.id
        target = self._determine_new_status(notification)
        record.outcome = receipt_transition(invoice.stato, target)
        if record.outcome != "applied":
            self.db.commit()
            return False, record.outcome, notification
        self._claim_identity(invoice, notification)
        values: dict[str, Any] = {
            "numero_sdi": notification.identificativo_sdi or invoice.numero_sdi
        }
        # Do not invent delivery/transmission event dates from import timestamps.
        if notification.tipo == TipoNotifica.RICEVUTA_CONSEGNA and notification.data_evento:
            values["data_consegna_sdi"] = notification.data_evento
        assert target is not None
        change_status(self.db, invoice, target, **values)
        self._add_notification_note(invoice, notification)
        self.db.add(
            LogSDI(
                fattura_id=invoice.id,
                tipo_notifica=notification.tipo,
                descrizione=notification.messaggio or "",
                data_ricezione=notification.data_ricezione,
            )
        )
        self.db.commit()
        return invoice

    def _claim_identity(self, invoice: Fattura, notification: NotificaSDI) -> None:
        """Reserve the SDI identifier for ``invoice``; it may belong to one invoice only."""
        identity = (
            self.db.query(SDIInvoiceIdentity)
            .filter_by(identifier=notification.identificativo_sdi)
            .first()
        )
        if identity and identity.invoice_id != invoice.id:
            raise ValueError("SDI identifier already belongs to another invoice")
        if notification.identificativo_sdi and identity is None:
            self.db.add(
                SDIInvoiceIdentity(
                    identifier=notification.identificativo_sdi, invoice_id=invoice.id
                )
            )

    def _announce(self, invoice: Fattura, notification: NotificaSDI) -> None:
        """Publish the event and send email; failures after commit only log a warning."""
        try:
            bus = get_global_event_bus()
            if bus:
                bus.publish(
                    SDINotificationReceivedEvent(
                        notification_type=notification.tipo,
                        invoice_id=invoice.id,
                        invoice_number=f"{invoice.numero}/{invoice.anno}",
                        message=notification.messaggio or "",
                        notification_id=int(notification.identificativo_sdi)
                        if notification.identificativo_sdi.isdigit()
                        else None,
                    )
                )
            if self.email_sender:
                self._send_email_notification(invoice, notification)
        except Exception as exc:
            logger.warning("sdi_post_commit_notification_failed", error=str(exc))

    def _find_invoice(self, notification: NotificaSDI) -> Fattura | None:
        matches = (
            self.db.query(Fattura)
            .filter(Fattura.numero_sdi == notification.identificativo_sdi)
            .all()
            if notification.identificativo_sdi
            else []
        )
        filename = Path(notification.nome_file).name
        file_ids = {
            a.invoice_id
            for a in self.db.query(SDISubmissionAttempt)
            .filter(SDISubmissionAttempt.filename.in_([filename, filename + ".p7m"]))
            .all()
        }
        file_matches = [
            f
            for f in self.db.query(Fattura).all()
            if f.id in file_ids
            or any(
                path and Path(path).name == filename for path in (f.xml_path, f.xml_firmato_path)
            )
        ]
        if len(matches) > 1 or len(file_matches) > 1:
            raise ValueError("Ambiguous SDI notification association")
        if matches and file_matches and matches[0].id != file_matches[0].id:
            raise ValueError("SDI identifier conflicts with invoice filename")
        candidates = matches or file_matches
        if (
            candidates
            and candidates[0].numero_sdi
            and candidates[0].numero_sdi != notification.identificativo_sdi
        ):
            raise ValueError("SDI identifier conflicts with recorded transmission")
        return candidates[0] if candidates else None

    def _determine_new_status(self, notification: NotificaSDI) -> StatoFattura | None:
        """
        Determine new invoice status from notification.

        Args:
            notification: Notification data

        Returns:
            New status or None if no change needed
        """
        if notification.tipo in self.STATUS_MAPPING:
            status = self.STATUS_MAPPING[TipoNotifica(notification.tipo)]

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
            f"SDI Notification ({notification.tipo}): "
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
            fattura: Invoice that received the notification
            notification: SDI notification details

        Note:
            If email_sender is None, this method does nothing (graceful degradation).
        """
        # Graceful handling: if no email sender configured, just return
        if self.email_sender is None:
            return

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
            logger.warning("notification_email_failed", error=str(e))


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
