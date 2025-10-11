"""Repository pattern for payment tracking data access.

Implements the Repository pattern to abstract database operations and provide
a clean interface for the domain layer. Follows Hexagonal Architecture principles.
"""

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.enums import TransactionStatus
from ..domain.models import BankAccount, BankTransaction
from ..domain.payment_allocation import PaymentAllocation

if TYPE_CHECKING:
    from ...storage.database.models import Pagamento


class BankAccountRepository:
    """Repository for BankAccount aggregate root.

    Provides CRUD operations and domain-specific queries for bank accounts.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def add(self, account: BankAccount) -> BankAccount:
        """Add a new bank account.

        Args:
            account: BankAccount entity

        Returns:
            The persisted account with ID assigned
        """
        self.session.add(account)
        self.session.flush()
        return account

    def get_by_id(self, account_id: int) -> BankAccount | None:
        """Get bank account by ID.

        Args:
            account_id: Account ID

        Returns:
            BankAccount if found, None otherwise
        """
        return self.session.get(BankAccount, account_id)

    def get_by_iban(self, iban: str) -> BankAccount | None:
        """Get bank account by IBAN.

        Args:
            iban: IBAN string

        Returns:
            BankAccount if found, None otherwise
        """
        stmt = select(BankAccount).where(BankAccount.iban == iban)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_active_accounts(self) -> list[BankAccount]:
        """Get all active bank accounts.

        Returns:
            List of active BankAccount entities
        """
        stmt = select(BankAccount).where(BankAccount.is_active == True)  # noqa: E712
        return list(self.session.execute(stmt).scalars())

    def update(self, account: BankAccount) -> BankAccount:
        """Update an existing bank account.

        Args:
            account: BankAccount with updated fields

        Returns:
            Updated account
        """
        self.session.flush()
        return account

    def delete(self, account_id: int) -> bool:
        """Delete a bank account.

        Args:
            account_id: Account ID to delete

        Returns:
            True if deleted, False if not found
        """
        account = self.get_by_id(account_id)
        if account:
            self.session.delete(account)
            self.session.flush()
            return True
        return False


class BankTransactionRepository:
    """Repository for BankTransaction entities.

    Provides CRUD and query operations for bank transactions with
    support for reconciliation workflows.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def add(self, transaction: BankTransaction) -> BankTransaction:
        """Add a new bank transaction.

        Args:
            transaction: BankTransaction entity

        Returns:
            The persisted transaction
        """
        self.session.add(transaction)
        self.session.flush()
        return transaction

    def add_batch(self, transactions: list[BankTransaction]) -> list[BankTransaction]:
        """Add multiple transactions in batch.

        Args:
            transactions: List of BankTransaction entities

        Returns:
            List of persisted transactions
        """
        self.session.add_all(transactions)
        self.session.flush()
        return transactions

    def get_by_id(self, transaction_id: UUID) -> BankTransaction | None:
        """Get transaction by UUID.

        Args:
            transaction_id: Transaction UUID

        Returns:
            BankTransaction if found, None otherwise
        """
        return self.session.get(BankTransaction, transaction_id)

    def get_by_status(
        self, status: TransactionStatus, account_id: int | None = None, limit: int | None = None
    ) -> list[BankTransaction]:
        """Get transactions by status.

        Args:
            status: Transaction status to filter by
            account_id: Optional account ID filter
            limit: Optional maximum number of results

        Returns:
            List of matching transactions
        """
        stmt = select(BankTransaction).where(BankTransaction.status == status)

        if account_id is not None:
            stmt = stmt.where(BankTransaction.account_id == account_id)

        stmt = stmt.order_by(BankTransaction.date.desc())

        if limit is not None:
            stmt = stmt.limit(limit)

        return list(self.session.execute(stmt).scalars())

    def get_unmatched(
        self,
        account_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[BankTransaction]:
        """Get unmatched transactions for reconciliation.

        Args:
            account_id: Optional account ID filter
            date_from: Optional start date filter
            date_to: Optional end date filter

        Returns:
            List of unmatched transactions
        """
        stmt = select(BankTransaction).where(BankTransaction.status == TransactionStatus.UNMATCHED)

        if account_id is not None:
            stmt = stmt.where(BankTransaction.account_id == account_id)

        if date_from is not None:
            stmt = stmt.where(BankTransaction.date >= date_from)

        if date_to is not None:
            stmt = stmt.where(BankTransaction.date <= date_to)

        stmt = stmt.order_by(BankTransaction.date.desc())

        return list(self.session.execute(stmt).scalars())

    def update(self, transaction: BankTransaction) -> BankTransaction:
        """Update an existing transaction.

        Args:
            transaction: BankTransaction with updated fields

        Returns:
            Updated transaction
        """
        self.session.flush()
        return transaction


class PaymentRepository:
    """Repository for Pagamento entities (read-only wrapper).

    Provides read-only access to payment records for reconciliation.
    Write operations should go through the main invoice/payment service.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def get_by_id(self, payment_id: int) -> "Pagamento | None":
        """Get payment by ID.

        Args:
            payment_id: Payment ID

        Returns:
            Pagamento if found, None otherwise
        """
        from ...storage.database.models import Pagamento

        return self.session.get(Pagamento, payment_id)

    def get_unpaid(
        self, date_from: date | None = None, date_to: date | None = None
    ) -> list["Pagamento"]:
        """Get unpaid payments for reconciliation.

        Args:
            date_from: Optional start date filter (due date)
            date_to: Optional end date filter (due date)

        Returns:
            List of unpaid payments
        """
        from ...storage.database.models import Pagamento, StatoPagamento

        stmt = select(Pagamento).where(
            Pagamento.stato.in_([StatoPagamento.DA_PAGARE, StatoPagamento.PAGATO_PARZIALE])
        )

        if date_from is not None:
            stmt = stmt.where(Pagamento.data_scadenza >= date_from)

        if date_to is not None:
            stmt = stmt.where(Pagamento.data_scadenza <= date_to)

        stmt = stmt.order_by(Pagamento.data_scadenza.asc())

        return list(self.session.execute(stmt).scalars())

    def update(self, payment: "Pagamento") -> "Pagamento":
        """Flush changes to a payment entity."""

        self.session.flush()
        return payment

    def add_allocation(self, allocation: PaymentAllocation) -> PaymentAllocation:
        """Persist a payment allocation linking transaction and payment."""

        self.session.add(allocation)
        self.session.flush()
        return allocation

    def get_allocation(self, payment_id: int, transaction_id: UUID) -> PaymentAllocation | None:
        """Fetch allocation for a specific payment/transaction pair."""

        stmt = select(PaymentAllocation).where(
            PaymentAllocation.payment_id == payment_id,
            PaymentAllocation.transaction_id == transaction_id,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_allocations_for_payment(self, payment_id: int) -> list[PaymentAllocation]:
        """Return allocations recorded for the given payment."""

        stmt = select(PaymentAllocation).where(PaymentAllocation.payment_id == payment_id)
        return list(self.session.execute(stmt).scalars())

    def delete_allocation(self, allocation: PaymentAllocation) -> None:
        """Delete a previously stored payment allocation."""

        self.session.delete(allocation)
        self.session.flush()
