"""Pytest fixtures for Payment module tests."""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from openfatture.payment.domain.enums import (
    MatchType,
    ReminderStatus,
    ReminderStrategy,
    TransactionStatus,
)
from openfatture.payment.domain.models import (
    BankAccount,
    BankTransaction,
    PaymentReminder,
)
from openfatture.storage.database.models import Cliente, Fattura, Pagamento, StatoPagamento


@pytest.fixture
def sample_cliente(db_session: Session) -> Cliente:
    """Create a sample cliente for testing."""
    cliente = Cliente(
        denominazione="Test Client S.r.l.",
        partita_iva="12345678901",
        codice_fiscale="TSTCLN80A01H501X",
        codice_destinatario="XXXXXXX",
        indirizzo="Via Test",
        numero_civico="1",
        cap="00100",
        comune="Roma",
        provincia="RM",
        nazione="IT",
    )
    db_session.add(cliente)
    db_session.commit()
    db_session.refresh(cliente)
    return cliente


@pytest.fixture
def sample_fattura(db_session: Session, sample_cliente: Cliente) -> Fattura:
    """Create a sample fattura for testing."""
    from openfatture.storage.database.models import TipoDocumento, StatoFattura

    fattura = Fattura(
        numero="001",
        anno=2024,
        data_emissione=date.today(),
        cliente_id=sample_cliente.id,
        imponibile=Decimal("1000.00"),
        iva=Decimal("220.00"),
        totale=Decimal("1220.00"),
        tipo_documento=TipoDocumento.TD01,
        stato=StatoFattura.INVIATA,
    )
    db_session.add(fattura)
    db_session.commit()
    db_session.refresh(fattura)
    return fattura


@pytest.fixture
def bank_account(db_session: Session) -> BankAccount:
    """Create a sample bank account for testing."""
    account = BankAccount(
        name="Conto Corrente Intesa",
        iban="IT60X0542811101000000123456",
        bic_swift="BCITITMM",
        bank_name="Intesa Sanpaolo",
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def bank_transaction(db_session: Session, bank_account: BankAccount) -> BankTransaction:
    """Create a sample bank transaction for testing."""
    transaction = BankTransaction(
        id=uuid4(),
        account_id=bank_account.id,
        date=date.today() - timedelta(days=5),
        amount=Decimal("1000.00"),
        description="Pagamento fattura 2025/001",
        status=TransactionStatus.UNMATCHED,
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    return transaction


@pytest.fixture
def matched_transaction(db_session: Session, bank_account: BankAccount) -> BankTransaction:
    """Create a matched transaction for testing."""
    transaction = BankTransaction(
        id=uuid4(),
        account_id=bank_account.id,
        date=date.today() - timedelta(days=10),
        amount=Decimal("500.00"),
        description="Bonifico da cliente",
        status=TransactionStatus.MATCHED,
        matched_payment_id=1,  # Assume payment exists
        match_confidence=0.95,
        match_type=MatchType.AUTO,
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    return transaction


@pytest.fixture
def payment_with_reminder(db_session: Session, sample_fattura: Fattura) -> Pagamento:
    """Create a payment for testing reminders."""
    payment = Pagamento(
        fattura_id=sample_fattura.id,
        importo=Decimal("1220.00"),
        data_scadenza=date.today() + timedelta(days=30),
        stato=StatoPagamento.DA_PAGARE,
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment


@pytest.fixture
def payment_reminder(db_session: Session, payment_with_reminder: Pagamento) -> PaymentReminder:
    """Create a payment reminder for testing."""
    reminder = PaymentReminder(
        payment_id=payment_with_reminder.id,
        reminder_date=date.today(),
        strategy=ReminderStrategy.DEFAULT,
        status=ReminderStatus.PENDING,
    )
    db_session.add(reminder)
    db_session.commit()
    db_session.refresh(reminder)
    return reminder


@pytest.fixture
def multiple_transactions(db_session: Session, bank_account: BankAccount) -> list[BankTransaction]:
    """Create multiple transactions for batch testing."""
    transactions = [
        BankTransaction(
            id=uuid4(),
            account_id=bank_account.id,
            date=date.today() - timedelta(days=i),
            amount=Decimal(f"{100 * (i + 1)}.00"),
            description=f"Transaction {i + 1}",
            status=TransactionStatus.UNMATCHED,
        )
        for i in range(5)
    ]

    for tx in transactions:
        db_session.add(tx)

    db_session.commit()

    for tx in transactions:
        db_session.refresh(tx)

    return transactions
