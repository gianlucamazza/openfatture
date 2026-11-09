"""Shared lifecycle policy and conditional updates for all invoice adapters."""

from typing import Any, cast

from sqlalchemy import update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from openfatture.storage.database.models import Fattura, StatoFattura


class InvoiceStateConflict(ValueError):
    """The invoice changed after it was read."""


def validate_manual_transition(invoice: Fattura, target: StatoFattura) -> None:
    if target == invoice.stato:
        return
    if invoice.issued_elsewhere:
        raise ValueError("Historical invoices cannot change status manually")
    editable = {StatoFattura.BOZZA, StatoFattura.DA_INVIARE}
    if invoice.stato not in editable or target not in editable:
        raise ValueError("Manual status changes only allow bozza and da_inviare")
    if target == StatoFattura.DA_INVIARE and (not invoice.righe or not invoice.cliente):
        raise ValueError("Invoice requires a client and line items before sending")
    if target == StatoFattura.DA_INVIARE:
        from openfatture.platform.config import get_settings
        from openfatture.sdi.validator.xsd_validator import FatturaPAValidator
        from openfatture.sdi.xml_builder.fatturapa import FatturaPABuilder

        xml = FatturaPABuilder(get_settings()).build(invoice)
        valid, error = FatturaPAValidator().validate(xml)
        if not valid:
            raise ValueError(f"Invoice XML validation failed: {error}")


def receipt_transition(current: StatoFattura, target: StatoFattura | None) -> str:
    if target is None:
        return "unsupported"
    if target == current:
        return "applied"
    terminal = {StatoFattura.ACCETTATA, StatoFattura.RIFIUTATA, StatoFattura.SCARTATA}
    if current in terminal:
        return "conflict" if target in terminal else "out_of_order"
    # A scarto contradicts a delivery or recipient outcome for the same transmission.
    if target == StatoFattura.SCARTATA and current == StatoFattura.CONSEGNATA:
        return "conflict"
    ranks = {
        StatoFattura.BOZZA: 0,
        StatoFattura.DA_INVIARE: 0,
        StatoFattura.INVIATA: 1,
        StatoFattura.ERRORE: 2,
        StatoFattura.CONSEGNATA: 3,
    }
    if ranks.get(target, 4) < ranks.get(current, 0):
        return "out_of_order"
    return "applied"


def change_status(
    session: Session, invoice: Fattura, target: StatoFattura, **values: object
) -> None:
    """Compare-and-set avoids overwriting concurrent SDI/manual updates."""
    result = session.execute(
        update(Fattura)
        .where(
            Fattura.id == invoice.id,
            Fattura.stato == invoice.stato,
            Fattura.issued_elsewhere == invoice.issued_elsewhere,
            Fattura.numero_sdi == invoice.numero_sdi,
            Fattura.updated_at == invoice.updated_at,
        )
        .values(stato=target, **values)
        .execution_options(synchronize_session=False, autoflush=False)
    )
    if cast(CursorResult[Any], result).rowcount != 1:
        raise InvoiceStateConflict("Invoice state changed; reload before retrying")
    session.flush()
    session.expire(invoice)
