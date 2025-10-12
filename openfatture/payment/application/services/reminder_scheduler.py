"""Reminder scheduler for payment reminders.

Implements scheduling and execution of payment reminders based on configurable strategies.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog
from sqlalchemy.orm import Session

from ....storage.database.models import StatoPagamento
from ...domain.enums import ReminderStatus, ReminderStrategy
from ...domain.models import PaymentReminder
from ..notifications.notifier import INotifier

if TYPE_CHECKING:
    from ....storage.database.models import Pagamento
    from ...infrastructure.repository import PaymentRepository

logger = structlog.get_logger()


class ReminderRepository:
    """Repository for PaymentReminder persistence.

    Note: This is a simplified repository. In production, implement proper
    repository with SQLAlchemy models.
    """

    def __init__(self, session: Session) -> None:
        """Initialize reminder repository.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def add(self, reminder: PaymentReminder) -> PaymentReminder:
        """Add reminder to database.

        Args:
            reminder: PaymentReminder entity

        Returns:
            Persisted reminder
        """
        self.session.add(reminder)
        self.session.flush()
        return reminder

    def add_all(self, reminders: list[PaymentReminder]) -> list[PaymentReminder]:
        """Add multiple reminders.

        Args:
            reminders: List of PaymentReminder entities

        Returns:
            List of persisted reminders
        """
        self.session.add_all(reminders)
        self.session.flush()
        return reminders

    def get_due_reminders(self, target_date: date | None = None) -> list[PaymentReminder]:
        """Get reminders due on target date.

        Args:
            target_date: Date to check (default: today)

        Returns:
            List of due reminders (not yet sent)
        """
        if target_date is None:
            target_date = date.today()

        reminders = (
            self.session.query(PaymentReminder)
            .filter(
                PaymentReminder.reminder_date == target_date,
                PaymentReminder.sent_date.is_(None),
            )
            .all()
        )

        return reminders

    def delete_by_payment_id(self, payment_id: int) -> int:
        """Delete all unsent reminders for payment.

        Args:
            payment_id: Payment ID

        Returns:
            Number of reminders deleted
        """
        deleted = (
            self.session.query(PaymentReminder)
            .filter(
                PaymentReminder.payment_id == payment_id,
                PaymentReminder.sent_date.is_(None),
            )
            .delete()
        )

        self.session.flush()
        return deleted

    def get_by_id(self, reminder_id: int) -> PaymentReminder | None:
        """Retrieve reminder by ID."""

        return self.session.get(PaymentReminder, reminder_id)

    def list_reminders(
        self,
        status: ReminderStatus | None = None,
        payment_id: int | None = None,
        limit: int | None = None,
    ) -> list[PaymentReminder]:
        """List reminders with optional filters."""

        query = self.session.query(PaymentReminder).order_by(
            PaymentReminder.reminder_date.asc(), PaymentReminder.id.asc()
        )

        if status is not None:
            query = query.filter(PaymentReminder.status == status)

        if payment_id is not None:
            query = query.filter(PaymentReminder.payment_id == payment_id)

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def update(self, reminder: PaymentReminder) -> PaymentReminder:
        """Flush changes to reminder."""

        self.session.flush()
        return reminder


class ReminderScheduler:
    """Scheduler for payment reminders based on strategy.

    Design Pattern: Observer + Template Method
    SOLID: Interface Segregation (separate read/write concerns)

    This service manages the complete lifecycle of payment reminders:
    - Scheduling reminders based on strategy
    - Processing due reminders (background job)
    - Canceling reminders when payment is completed

    Example:
        >>> scheduler = ReminderScheduler(
        ...     reminder_repo=ReminderRepository(session),
        ...     payment_repo=PaymentRepository(session),
        ...     notifier=EmailNotifier(smtp_config)
        ... )
        >>> reminders = await scheduler.schedule_reminders(
        ...     payment_id=123,
        ...     strategy=ReminderStrategy.DEFAULT
        ... )
        >>> print(f"Scheduled {len(reminders)} reminders")
    """

    def __init__(
        self,
        reminder_repo: ReminderRepository,
        payment_repo: "PaymentRepository",
        notifier: INotifier,
    ) -> None:
        """Initialize reminder scheduler.

        Args:
            reminder_repo: Repository for reminders
            payment_repo: Repository for payments
            notifier: Notifier implementation (email, SMS, etc.)
        """
        self.reminder_repo = reminder_repo
        self.payment_repo = payment_repo
        self.notifier = notifier

    async def schedule_reminders(
        self,
        payment_id: int,
        strategy: ReminderStrategy = ReminderStrategy.DEFAULT,
    ) -> list[PaymentReminder]:
        """Schedule reminders for payment according to strategy.

        Workflow:
        1. Get payment and validate
        2. Calculate reminder dates based on strategy
        3. Create PaymentReminder entities
        4. Persist to database
        5. Return scheduled reminders

        Args:
            payment_id: Payment ID
            strategy: Reminder strategy (DEFAULT, AGGRESSIVE, GENTLE, MINIMAL)

        Returns:
            List of scheduled PaymentReminder entities

        Raises:
            ValueError: If payment not found or already paid

        Example:
            >>> reminders = await scheduler.schedule_reminders(
            ...     payment_id=123,
            ...     strategy=ReminderStrategy.AGGRESSIVE
            ... )
            >>> for r in reminders:
            ...     print(f"{r.reminder_date}: {r.days_before_due} days")
        """
        logger.info(
            "scheduling_reminders",
            payment_id=payment_id,
            strategy=strategy.value,
        )

        # 1. Get payment
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        outstanding = self._outstanding_amount(payment)

        # Validate payment is not fully paid
        if outstanding <= Decimal("0.00"):
            raise ValueError(
                f"Payment {payment_id} is already fully paid. "
                "Cannot schedule reminders for paid invoices."
            )

        if payment.data_scadenza < date.today() and outstanding > Decimal("0.00"):
            if getattr(payment, "stato", None) != StatoPagamento.SCADUTO:
                payment.stato = StatoPagamento.SCADUTO
                self.payment_repo.update(payment)

        # 2. Calculate reminder dates
        due_date = payment.data_scadenza
        schedule_days = strategy.get_schedule_days()

        reminders = []
        for days_before_due in schedule_days:
            scheduled_date = due_date + timedelta(days=days_before_due)

            # Skip past dates
            if scheduled_date < date.today():
                logger.debug(
                    "skipping_past_date",
                    scheduled_date=scheduled_date.isoformat(),
                    days_before_due=days_before_due,
                )
                continue

            # Create reminder
            reminder = PaymentReminder(
                payment_id=payment_id,
                payment=payment,
                reminder_date=scheduled_date,
                strategy=strategy,
                email_body=self._build_reminder_message(payment, days_before_due),
                email_subject=f"Reminder: Payment for invoice {payment.fattura.numero if hasattr(payment, 'fattura') and payment.fattura else 'N/A'}",
            )

            reminders.append(reminder)

        # 3. Persist reminders
        if reminders:
            self.reminder_repo.add_all(reminders)

            logger.info(
                "reminders_scheduled",
                payment_id=payment_id,
                strategy=strategy.value,
                count=len(reminders),
            )

        return reminders

    async def process_due_reminders(
        self,
        target_date: date | None = None,
    ) -> int:
        """Process all reminders due today (background job).

        Workflow:
        1. Query reminders with reminder_date = target_date AND not sent
        2. For each reminder:
           - Check payment status (skip if paid)
           - Send notification via notifier
           - Mark as sent (sent_date = now)
        3. Return count of sent reminders

        Args:
            target_date: Date to process (default: today)

        Returns:
            Number of reminders sent

        Example:
            >>> # Run this as a daily cron job
            >>> count = await scheduler.process_due_reminders()
            >>> print(f"Sent {count} reminders")
        """
        if target_date is None:
            target_date = date.today()

        logger.info("processing_due_reminders", target_date=target_date.isoformat())

        # Get due reminders
        reminders = self.reminder_repo.get_due_reminders(target_date)

        if not reminders:
            logger.info("no_due_reminders", target_date=target_date.isoformat())
            return 0

        sent_count = 0
        errors = []

        for reminder in reminders:
            try:
                payment = reminder.payment
                outstanding = self._outstanding_amount(payment)

                if payment.data_scadenza < target_date and outstanding > Decimal("0.00"):
                    if getattr(payment, "stato", None) != StatoPagamento.SCADUTO:
                        payment.stato = StatoPagamento.SCADUTO
                        self.payment_repo.update(payment)

                if outstanding <= Decimal("0.00"):
                    logger.debug(
                        "skipping_paid_reminder",
                        reminder_id=reminder.id,
                        payment_id=payment.id,
                    )
                    # Mark as sent to avoid re-processing
                    reminder.mark_sent()
                    continue

                # Send reminder
                success = await self.notifier.send_reminder(reminder)

                if success:
                    # Mark as sent
                    reminder.mark_sent()
                    sent_count += 1
                else:
                    errors.append(f"Reminder {reminder.id}: Send failed")

            except Exception as e:
                logger.error(
                    "reminder_processing_failed",
                    reminder_id=reminder.id,
                    error=str(e),
                )
                errors.append(f"Reminder {reminder.id}: {e}")

        logger.info(
            "due_reminders_processed",
            target_date=target_date.isoformat(),
            total=len(reminders),
            sent=sent_count,
            errors=len(errors),
        )

        return sent_count

    async def cancel_reminders(
        self,
        payment_id: int,
    ) -> int:
        """Cancel all pending reminders for payment.

        Use when payment is completed to avoid sending unnecessary reminders.

        Args:
            payment_id: Payment ID

        Returns:
            Number of reminders canceled

        Example:
            >>> # After payment is reconciled
            >>> canceled = await scheduler.cancel_reminders(payment_id=123)
            >>> print(f"Canceled {canceled} pending reminders")
        """
        logger.info("canceling_reminders", payment_id=payment_id)

        deleted = self.reminder_repo.delete_by_payment_id(payment_id)

        logger.info(
            "reminders_canceled",
            payment_id=payment_id,
            count=deleted,
        )

        return deleted

    def _build_reminder_message(
        self,
        payment: "Pagamento",
        days_before_due: int,
    ) -> str:
        """Build reminder message text.

        Args:
            payment: Payment entity
            days_before_due: Days relative to due date (negative = after)

        Returns:
            Reminder message string
        """
        invoice = payment.fattura if hasattr(payment, "fattura") else None
        invoice_number = invoice.numero if invoice else "N/A"

        if days_before_due < 0:
            # Overdue
            days_late = -days_before_due
            return (
                f"ATTENTION: Invoice {invoice_number} is {days_late} days overdue. "
                f"Amount due: €{payment.importo_da_pagare}. "
                "Please arrange payment as soon as possible."
            )
        elif days_before_due == 0:
            # Due today
            return (
                f"REMINDER: Invoice {invoice_number} is due TODAY. "
                f"Amount due: €{payment.importo_da_pagare}. "
                "Please proceed with payment."
            )
        else:
            # Before due date
            return (
                f"Reminder: Invoice {invoice_number} falls due in {days_before_due} days "
                f"({payment.data_scadenza.strftime('%d/%m/%Y')}). "
                f"Amount due: €{payment.importo_da_pagare}."
            )

    def __repr__(self) -> str:
        """Human-readable string representation."""
        return f"<ReminderScheduler(" f"notifier={self.notifier.__class__.__name__})>"

    @staticmethod
    def _outstanding_amount(payment: "Pagamento") -> Decimal:
        """Compute outstanding amount for a payment entity."""

        saldo = getattr(payment, "saldo_residuo", None)
        if saldo is not None:
            try:
                converted = Decimal(saldo)
            except (TypeError, ValueError, ArithmeticError):
                pass
            else:
                return converted if converted > Decimal("0.00") else Decimal("0.00")

        due = Decimal(getattr(payment, "importo_da_pagare", getattr(payment, "importo", 0)))
        paid = Decimal(getattr(payment, "importo_pagato", 0))
        residual = due - paid
        return residual if residual > Decimal("0.00") else Decimal("0.00")
