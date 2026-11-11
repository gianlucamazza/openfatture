"""Durable single-attempt PEC submission and explicit uncertainty resolution."""

import hashlib
from collections.abc import Callable
from contextvars import ContextVar
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from typing import Any

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import object_session

from openfatture.billing.application.invoice_status import change_status
from openfatture.storage.database.models import Fattura, SDISubmissionAttempt, StatoFattura

_single_submission: ContextVar[bool] = ContextVar("sdi_single_submission", default=False)


def single_submission_active() -> bool:
    return _single_submission.get()


def journaled_submission(
    method: Callable[..., tuple[bool, str | None]],
) -> Callable[..., tuple[bool, str | None]]:
    @wraps(method)
    def wrapped(
        sender: Any, invoice: Fattura, path: Path, signed: bool = False
    ) -> tuple[bool, str | None]:
        if invoice.issued_elsewhere:
            return False, "Cannot send historical invoice issued elsewhere"
        if invoice.stato not in {StatoFattura.BOZZA, StatoFattura.DA_INVIARE}:
            return False, "Invoice is not in a sendable state"
        if not sender.settings.pec_address:
            return False, "PEC address not configured"
        if not sender.settings.pec_password:
            return False, "PEC password not configured"
        if not path.exists():
            return False, f"XML file not found: {path}"
        session = object_session(invoice)
        if session is None or invoice.id is None:
            return False, "Persist the invoice before attempting SDI submission"
        if (
            session.query(SDISubmissionAttempt)
            .filter(
                SDISubmissionAttempt.filename == path.name,
                SDISubmissionAttempt.invoice_id != invoice.id,
            )
            .first()
        ):
            return (
                False,
                "Filename already identifies another invoice; choose a distinct transmission filename",
            )
        attempt = SDISubmissionAttempt(
            invoice_id=invoice.id,
            active_invoice_id=invoice.id,
            filename=path.name,
            xml_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            outcome="pending",
        )
        try:
            session.add(attempt)
            session.commit()  # Durable claim before any external effect.
        except IntegrityError:
            session.rollback()
            return (
                False,
                "Submission already sent or uncertain; inspect its journal before retrying",
            )
        except Exception:
            session.rollback()
            return False, "Cannot persist submission claim; no email sent"
        attempt_id = attempt.id
        token = _single_submission.set(True)
        try:
            success, error = method(sender, invoice, path, signed)
            if not success:
                attempt.outcome, attempt.reason = "uncertain", error
                session.commit()
                return (
                    False,
                    f"{error}; submission outcome requires verification; automatic retry blocked",
                )
            # The transport implementations do not mutate lifecycle fields.
            session.refresh(invoice)
            if invoice.stato in {StatoFattura.BOZZA, StatoFattura.DA_INVIARE}:
                change_status(
                    session, invoice, StatoFattura.INVIATA, data_invio_sdi=datetime.now(UTC)
                )
            attempt.outcome = "sent"
            session.commit()
            return True, None
        except Exception:
            session.rollback()
            # The previously committed pending claim remains and prevents a duplicate.
            return False, f"Submission {attempt_id} requires verification; automatic retry blocked"
        finally:
            _single_submission.reset(token)

    return wrapped


def resolve_submission(session: Any, attempt_id: int, *, sent: bool, note: str) -> None:
    """Called only by a human-confirmed CLI command after checking transport evidence."""
    if not note.strip():
        raise ValueError("Verification evidence is required")
    attempt = session.query(SDISubmissionAttempt).filter_by(id=attempt_id).with_for_update().one()
    if attempt.outcome not in {"pending", "uncertain"}:
        raise ValueError("Only unresolved submissions can be resolved")
    previous = attempt.outcome
    invoice = session.get(Fattura, attempt.invoice_id)
    if sent:
        if invoice.stato in {StatoFattura.BOZZA, StatoFattura.DA_INVIARE}:
            change_status(session, invoice, StatoFattura.INVIATA)
        outcome, active = "confirmed_sent", invoice.id
    else:
        if invoice.numero_sdi or invoice.stato not in {StatoFattura.BOZZA, StatoFattura.DA_INVIARE}:
            raise ValueError("Recorded SDI evidence contradicts a not-sent resolution")
        change_status(session, invoice, invoice.stato)
        outcome, active = "confirmed_not_sent", None
    from typing import cast

    from sqlalchemy.engine import CursorResult

    result = session.execute(
        update(SDISubmissionAttempt)
        .where(SDISubmissionAttempt.id == attempt_id, SDISubmissionAttempt.outcome == previous)
        .values(
            outcome=outcome, active_invoice_id=active, reason=note, resolved_at=datetime.now(UTC)
        )
    )
    if cast(CursorResult[Any], result).rowcount != 1:
        raise ValueError("Submission was resolved concurrently; reload")
    session.commit()
