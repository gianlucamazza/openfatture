"""Utilities to summarize payment due dates for reports and dashboards."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session, joinedload

if TYPE_CHECKING:
    from ....storage.database.models import Fattura, Pagamento, StatoPagamento


@dataclass(frozen=True)
class PaymentDueEntry:
    """Row representing a single payment with outstanding balance."""

    payment_id: int
    invoice_ref: str
    client_name: str
    due_date: date
    days_delta: int
    residual: Decimal
    paid: Decimal
    total: Decimal
    status: StatoPagamento


@dataclass(frozen=True)
class PaymentDueSummary:
    """Aggregated payments grouped by urgency."""

    overdue: list[PaymentDueEntry]
    due_soon: list[PaymentDueEntry]
    upcoming: list[PaymentDueEntry]
    total_outstanding: Decimal
    hidden_upcoming: int


def _compute_residual(payment: Pagamento) -> Decimal:
    """Return outstanding amount for payment."""
    saldo = getattr(payment, "saldo_residuo", None)
    if saldo is not None:
        try:
            converted = Decimal(saldo)
        except (TypeError, ValueError, ArithmeticError):
            pass
        else:
            return converted if converted > Decimal("0.00") else Decimal("0.00")

    due = Decimal(getattr(payment, "importo", 0))
    paid = Decimal(getattr(payment, "importo_pagato", 0))
    residual = due - paid
    return residual if residual > Decimal("0.00") else Decimal("0.00")


def _client_name(fattura: Fattura | None) -> str:
    if fattura is None or getattr(fattura, "cliente", None) is None:
        return "N/D"

    cliente = fattura.cliente
    denominazione = getattr(cliente, "denominazione", None)
    if denominazione:
        return denominazione

    nome = getattr(cliente, "nome", "")
    cognome = getattr(cliente, "cognome", "")
    return " ".join(part for part in [nome, cognome] if part).strip() or "N/D"


def collect_payment_due_summary(
    session: Session,
    window_days: int = 14,
    max_upcoming: int = 20,
) -> PaymentDueSummary:
    """Gather outstanding payments grouped by urgency window.

    Args:
        session: Active SQLAlchemy session.
        window_days: Number of days considered as "due soon".
        max_upcoming: Maximum upcoming items included in summary (rest is counted).

    Returns:
        PaymentDueSummary containing grouped entries and aggregate totals.
    """
    from ....storage.database.models import Fattura, Pagamento, StatoPagamento

    today = date.today()
    due_soon_threshold = today + timedelta(days=window_days)

    payments = (
        session.query(Pagamento)
        .options(joinedload(Pagamento.fattura).joinedload(Fattura.cliente))
        .filter(Pagamento.stato != StatoPagamento.PAGATO)
        .order_by(Pagamento.data_scadenza.asc())
        .all()
    )

    overdue: list[PaymentDueEntry] = []
    due_soon: list[PaymentDueEntry] = []
    upcoming_full: list[PaymentDueEntry] = []
    total_outstanding = Decimal("0.00")

    for payment in payments:
        residual = _compute_residual(payment)
        if residual <= Decimal("0.00"):
            continue

        fattura = getattr(payment, "fattura", None)
        due_date = getattr(payment, "data_scadenza", None) or today
        days_delta = (due_date - today).days

        entry = PaymentDueEntry(
            payment_id=getattr(payment, "id", 0),
            invoice_ref=(
                f"{getattr(fattura, 'numero', 'N/A')}/{getattr(fattura, 'anno', '')}"
                if fattura
                else "N/A"
            ),
            client_name=_client_name(fattura),
            due_date=due_date,
            days_delta=days_delta,
            residual=residual,
            paid=Decimal(getattr(payment, "importo_pagato", 0)),
            total=Decimal(getattr(payment, "importo", 0)),
            status=getattr(payment, "stato", StatoPagamento.DA_PAGARE),
        )

        total_outstanding += residual

        if due_date < today:
            overdue.append(entry)
        elif due_date <= due_soon_threshold:
            due_soon.append(entry)
        else:
            upcoming_full.append(entry)

    upcoming_full.sort(key=lambda item: (item.days_delta, item.invoice_ref))
    hidden_upcoming = max(0, len(upcoming_full) - max_upcoming)
    upcoming = upcoming_full[:max_upcoming]

    return PaymentDueSummary(
        overdue=overdue,
        due_soon=due_soon,
        upcoming=upcoming,
        total_outstanding=total_outstanding,
        hidden_upcoming=hidden_upcoming,
    )
