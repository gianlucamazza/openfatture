"""Dashboard service for fetching statistics and metrics."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from openfatture.payment.application.services.payment_overview import (
    PaymentDueSummary,
    collect_payment_due_summary,
)
from openfatture.payment.domain.enums import TransactionStatus
from openfatture.payment.infrastructure.repository import BankTransactionRepository
from openfatture.storage.database.models import Cliente, Fattura, StatoFattura


class DashboardService:
    """Service for fetching dashboard data."""

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db

    def get_total_invoices(self) -> int:
        """Get total number of invoices."""
        return self.db.query(Fattura).count()

    def get_total_clients(self) -> int:
        """Get total number of clients."""
        return self.db.query(Cliente).count()

    def get_total_revenue(self) -> Decimal:
        """Get total revenue from all invoices."""
        total = self.db.query(func.sum(Fattura.totale)).scalar()
        return total or Decimal("0")

    def get_revenue_this_month(self) -> Decimal:
        """Get revenue for current month."""
        now = datetime.now()
        total = (
            self.db.query(func.sum(Fattura.totale))
            .filter(
                extract("year", Fattura.data_emissione) == now.year,
                extract("month", Fattura.data_emissione) == now.month,
            )
            .scalar()
        )
        return total or Decimal("0")

    def get_revenue_this_year(self) -> Decimal:
        """Get revenue for current year."""
        now = datetime.now()
        total = (
            self.db.query(func.sum(Fattura.totale))
            .filter(extract("year", Fattura.data_emissione) == now.year)
            .scalar()
        )
        return total or Decimal("0")

    def get_invoices_by_status(self) -> list[tuple[str, int]]:
        """Get invoice count grouped by status."""
        id_column = cast(Any, Fattura.id)
        results = self.db.query(Fattura.stato, func.count(id_column)).group_by(Fattura.stato).all()
        return [(stato.value, count) for stato, count in results]

    def get_pending_amount(self) -> Decimal:
        """Get total amount from pending invoices."""
        total = (
            self.db.query(func.sum(Fattura.totale))
            .filter(Fattura.stato.in_([StatoFattura.BOZZA, StatoFattura.DA_INVIARE]))
            .scalar()
        )
        return total or Decimal("0")

    def get_sent_not_accepted(self) -> int:
        """Get count of invoices sent but not yet accepted."""
        return self.db.query(Fattura).filter(Fattura.stato == StatoFattura.INVIATA).count()

    def get_monthly_revenue(self, months: int = 6) -> list[tuple[str, Decimal]]:
        """
        Get revenue for last N months.

        Args:
            months: Number of months to retrieve

        Returns:
            List of (month_name, revenue) tuples
        """
        now = datetime.now()
        results = []

        for i in range(months - 1, -1, -1):
            # Calculate month/year
            target_date = now - timedelta(days=30 * i)
            month = target_date.month
            year = target_date.year

            # Query revenue for that month
            revenue = (
                self.db.query(func.sum(Fattura.totale))
                .filter(
                    extract("year", Fattura.data_emissione) == year,
                    extract("month", Fattura.data_emissione) == month,
                )
                .scalar()
            ) or Decimal("0")

            month_name = target_date.strftime("%b %Y")
            results.append((month_name, revenue))

        return results

    def get_top_clients(self, limit: int = 5) -> list[tuple[str, int, Decimal]]:
        """
        Get top clients by revenue.

        Args:
            limit: Number of clients to return

        Returns:
            List of (client_name, invoice_count, total_revenue) tuples
        """
        results = (
            self.db.query(
                Cliente.denominazione,
                func.count(cast(Any, Fattura.id)),
                func.sum(Fattura.totale),
            )
            .join(Fattura)
            .group_by(Cliente.id, Cliente.denominazione)
            .order_by(func.sum(Fattura.totale).desc())
            .limit(limit)
            .all()
        )

        return [(name, count, total or Decimal("0")) for name, count, total in results]

    def get_recent_invoices(self, limit: int = 5) -> list[Fattura]:
        """
        Get most recent invoices.

        Args:
            limit: Number of invoices to return

        Returns:
            List of Invoice objects
        """
        return self.db.query(Fattura).order_by(Fattura.data_emissione.desc()).limit(limit).all()

    def get_payment_due_summary(
        self, window_days: int = 30, max_upcoming: int = 10
    ) -> PaymentDueSummary:
        """Return grouped payment due data for dashboard."""
        return collect_payment_due_summary(self.db, window_days, max_upcoming)

    def get_payment_stats(self) -> dict[str, int]:
        """Get payment tracking statistics."""
        tx_repo = BankTransactionRepository(self.db)
        return {
            "unmatched": len(tx_repo.get_by_status(TransactionStatus.UNMATCHED)),
            "matched": len(tx_repo.get_by_status(TransactionStatus.MATCHED)),
            "ignored": len(tx_repo.get_by_status(TransactionStatus.IGNORED)),
        }
