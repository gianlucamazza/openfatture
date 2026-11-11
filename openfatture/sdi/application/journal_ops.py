"""Human-confirmed SDI journal operations (submissions and imported receipts)."""

from __future__ import annotations

import json
from typing import Any

from openfatture.sdi.application.submissions import (
    SubmissionResolutionError,
    resolve_submission,
)
from openfatture.sdi.notifiche.parser import NotificaSDI
from openfatture.sdi.notifiche.processor import NotificationProcessor
from openfatture.storage.database.models import SDINotificationRecord, SDISubmissionAttempt
from openfatture.storage.session import db_session

ASSOCIABLE_OUTCOMES = frozenset({"unassociated", "association_conflict"})


def list_sdi_journal() -> dict[str, list[dict[str, Any]]]:
    """Return recorded PEC submission attempts and imported receipts (read-only)."""
    with db_session() as session:
        submissions = [
            {
                "id": a.id,
                "invoice_id": a.invoice_id,
                "filename": a.filename,
                "outcome": a.outcome,
            }
            for a in session.query(SDISubmissionAttempt).order_by(SDISubmissionAttempt.id)
        ]
        receipts = [
            {
                "id": r.id,
                "invoice_id": r.invoice_id,
                "outcome": r.outcome,
                "source": r.source,
            }
            for r in session.query(SDINotificationRecord).order_by(SDINotificationRecord.id)
        ]
    return {"submissions": submissions, "receipts": receipts}


def associate_receipt(receipt_id: int, invoice_id: int, evidence: str) -> dict[str, Any]:
    """Associate an unresolved receipt; callers must obtain human confirmation first."""
    with db_session() as session:
        receipt = session.get(SDINotificationRecord, receipt_id)
        if receipt is None or receipt.outcome not in ASSOCIABLE_OUTCOMES:
            return {"error": "Receipt cannot be associated", "error_code": "receipt_not_associable"}
        success, error, _notification = NotificationProcessor(session).process_notification(
            NotificaSDI.model_validate(json.loads(receipt.payload)),
            associated_invoice_id=invoice_id,
            association_note=evidence,
        )
    if not success:
        return {"error": error or "Receipt association failed"}
    return {"success": True, "receipt_id": receipt_id, "invoice_id": invoice_id}


def resolve_submission_attempt(attempt_id: int, *, sent: bool, evidence: str) -> dict[str, Any]:
    """Resolve an uncertain PEC attempt; callers must obtain human confirmation first."""
    with db_session() as session:
        try:
            resolve_submission(session, attempt_id, sent=sent, note=evidence)
        except SubmissionResolutionError as exc:
            session.rollback()
            return {"error": str(exc), "error_code": exc.code}
    return {"success": True, "attempt_id": attempt_id, "sent": sent}
