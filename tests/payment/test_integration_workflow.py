"""Integration tests for complete payment tracking workflow.

These tests cover end-to-end scenarios combining multiple components:
- Bank account setup
- Transaction import (CSV)
- Auto-matching with multiple strategies
- Reconciliation
- Payment reminders
- Metrics tracking

Focus: Realistic business workflows, not unit test isolation.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from sqlalchemy.orm import Session

from openfatture.payment import (
    BankAccount,
    BankTransaction,
    MatchResult,
    ReconciliationResult,
    ImportResult,
    TransactionStatus,
    MatchType,
    ReminderStatus,
    PaymentReminder,
)
from openfatture.payment.domain.enums import ImportSource, ReminderStrategy
from openfatture.payment.infrastructure.importers.csv_importer import CSVConfig, CSVImporter
from openfatture.payment.infrastructure.repository import (
    BankAccountRepository,
    BankTransactionRepository,
    PaymentRepository,
)
from openfatture.payment.application.services.matching_service import MatchingService
from openfatture.payment.application.services.reconciliation_service import ReconciliationService
from openfatture.payment.matchers import ExactAmountMatcher, FuzzyStringMatcher, CompositeMatcher
from openfatture.storage.database.models import (
    Pagamento,
    Cliente,
    Fattura,
    TipoDocumento,
    StatoFattura,
    StatoPagamento,
)
from openfatture.storage.database import get_db, init_db


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    init_db()
    session = next(get_db())
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_cliente(db_session):
    """Create a sample cliente for testing."""
    import uuid

    # Use unique partita_iva to avoid UNIQUE constraint failures
    piva_suffix = str(uuid.uuid4().int)[:11]
    cliente = Cliente(
        denominazione="ACME Corporation S.r.l.",
        partita_iva=piva_suffix,
        codice_fiscale=f"ACME{str(uuid.uuid4().int)[:12]}",
        codice_destinatario="XXXXXXX",
        indirizzo="Via Roma",
        numero_civico="123",
        cap="20100",
        comune="Milano",
        provincia="MI",
        nazione="IT",
    )
    db_session.add(cliente)
    db_session.commit()
    return cliente


@pytest.fixture
def sample_bank_account(db_session):
    """Create a sample bank account."""
    import uuid

    # Use unique IBAN for each test run to avoid UNIQUE constraint failures
    account = BankAccount(
        name="Intesa Sanpaolo Business",
        iban=f"IT{str(uuid.uuid4().int)[:24]}",  # Generate unique IBAN
        bic_swift="BPMOIT22XXX",
        bank_name="Intesa Sanpaolo",
        currency="EUR",
        opening_balance=Decimal("10000.00"),
        current_balance=Decimal("10000.00"),
        is_active=True,
    )
    db_session.add(account)
    db_session.commit()
    return account


@pytest.fixture
def sample_fatture(db_session, sample_cliente):
    """Create sample invoices for testing."""
    fatture = []
    for i in range(1, 4):
        fattura = Fattura(
            numero=f"{i:03d}",
            anno=2024,
            data_emissione=date(2024, 10, 1),
            cliente_id=sample_cliente.id,
            imponibile=Decimal(f"{i * 500}.00"),
            iva=Decimal(f"{i * 110}.00"),
            totale=Decimal(f"{i * 610}.00"),
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.INVIATA,
        )
        db_session.add(fattura)
        fatture.append(fattura)

    db_session.commit()
    return fatture


@pytest.fixture
def sample_payments(db_session, sample_fatture):
    """Create sample payments for matching."""
    payments = []

    for i, fattura in enumerate(sample_fatture, start=1):
        payment = Pagamento(
            fattura_id=fattura.id,
            importo=Decimal(f"{i * 500}.00"),
            data_scadenza=date(2024, 10, 31),
            stato=StatoPagamento.DA_PAGARE,
        )
        db_session.add(payment)
        payments.append(payment)

    db_session.commit()
    return payments


class TestCompletePaymentWorkflow:
    """Test complete end-to-end payment workflows."""

    @pytest.mark.asyncio
    async def test_csv_import_match_reconcile_workflow(
        self, db_session, sample_bank_account, sample_payments
    ):
        """Test complete workflow: CSV Import → Match → Reconcile.

        Scenario:
        1. Import transactions from CSV
        2. Auto-match with payments using composite matcher
        3. Auto-reconcile high-confidence matches
        4. Verify payment amounts updated
        """
        # STEP 1: Create CSV with transactions
        csv_content = """Data;Importo;Descrizione;Riferimento
15/10/2024;500,00;Bonifico ricevuto;INV-2024-001
16/10/2024;1000,00;Pagamento fattura;INV-2024-002
17/10/2024;1500,00;Bonifico;INV-2024-003"""

        with NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_path = Path(f.name)

        # STEP 2: Import transactions
        config = CSVConfig(
            delimiter=";",
            field_mapping={
                "date": "Data",
                "amount": "Importo",
                "description": "Descrizione",
                "reference": "Riferimento",
            },
            date_format="%d/%m/%Y",
            decimal_separator=",",
        )

        importer = CSVImporter(csv_path, config)
        transactions = importer.parse(sample_bank_account)

        for tx in transactions:
            db_session.add(tx)
        db_session.commit()

        assert len(transactions) == 3
        assert all(tx.status == TransactionStatus.UNMATCHED for tx in transactions)

        # STEP 3: Setup matching service with multiple strategies
        tx_repo = BankTransactionRepository(db_session)
        payment_repo = PaymentRepository(db_session)

        matching_service = MatchingService(
            tx_repo=tx_repo,
            payment_repo=payment_repo,
            strategies=[
                ExactAmountMatcher(
                    date_tolerance_days=30
                ),  # Allow wider date window for realistic scenarios
                CompositeMatcher(),
            ],
        )

        # STEP 4: Match transactions
        all_matches = []
        for tx in transactions:
            matches = await matching_service.match_transaction(tx, confidence_threshold=0.70)
            if matches:
                all_matches.append((tx, matches))

        assert len(all_matches) >= 2  # At least 2 should match

        # STEP 5: Reconcile high-confidence matches
        reconciliation_service = ReconciliationService(
            tx_repo=tx_repo,
            payment_repo=payment_repo,
            matching_service=matching_service,
        )

        reconciled_count = 0
        for tx, matches in all_matches:
            if matches[0].confidence >= 0.80:
                await reconciliation_service.reconcile(
                    transaction_id=tx.id,
                    payment_id=matches[0].payment.id,
                    match_type=matches[0].match_type,
                    confidence=matches[0].confidence,
                )
                reconciled_count += 1

        assert reconciled_count >= 2

        # STEP 6: Verify payments updated
        for payment in sample_payments:
            db_session.refresh(payment)
            # Payments that were reconciled should have data_pagamento set
            if payment.data_pagamento is not None:
                assert payment.stato in [StatoPagamento.PAGATO, StatoPagamento.PAGATO_PARZIALE]

        # Cleanup
        csv_path.unlink()

    def test_bank_account_transaction_relationship(self, db_session, sample_bank_account):
        """Test BankAccount → BankTransaction relationship."""
        # Create transactions
        tx1 = BankTransaction(
            account=sample_bank_account,
            date=date.today(),
            amount=Decimal("100.00"),
            description="Test transaction 1",
            import_source=ImportSource.MANUAL,
        )
        tx2 = BankTransaction(
            account=sample_bank_account,
            date=date.today(),
            amount=Decimal("200.00"),
            description="Test transaction 2",
            import_source=ImportSource.MANUAL,
        )

        db_session.add_all([tx1, tx2])
        db_session.commit()

        # Verify relationship
        db_session.refresh(sample_bank_account)
        assert len(sample_bank_account.transactions) == 2
        assert tx1 in sample_bank_account.transactions
        assert tx2 in sample_bank_account.transactions

    def test_transaction_lifecycle_states(self, db_session, sample_bank_account, sample_payments):
        """Test transaction state transitions: UNMATCHED → MATCHED → UNMATCHED."""
        # Create transaction
        tx = BankTransaction(
            account=sample_bank_account,
            date=date.today(),
            amount=Decimal("500.00"),
            description="Test payment",
            import_source=ImportSource.CSV,
        )
        db_session.add(tx)
        db_session.commit()

        # Initial state
        assert tx.status == TransactionStatus.UNMATCHED
        assert tx.matched_payment_id is None

        # Match to payment
        payment = sample_payments[0]
        tx.match_to_payment(payment, confidence=0.95, match_type=MatchType.EXACT)
        db_session.commit()

        assert tx.status == TransactionStatus.MATCHED
        assert tx.matched_payment_id == payment.id
        assert tx.match_confidence == 0.95

        # Unmatch
        tx.unmatch()
        db_session.commit()

        assert tx.status == TransactionStatus.UNMATCHED
        assert tx.matched_payment_id is None
        assert tx.match_confidence is None

    def test_transaction_ignore_workflow(self, db_session, sample_bank_account):
        """Test ignoring non-business transactions."""
        # Bank fee (should be ignored)
        tx = BankTransaction(
            account=sample_bank_account,
            date=date.today(),
            amount=Decimal("-5.00"),  # Negative = outgoing
            description="Bank fees Q4",
            import_source=ImportSource.CSV,
        )
        db_session.add(tx)
        db_session.commit()

        # Ignore transaction
        tx.ignore()
        db_session.commit()

        assert tx.status == TransactionStatus.IGNORED
        assert not tx.is_incoming
        assert tx.is_outgoing

    def test_payment_reminder_model(self, db_session, sample_payments):
        """Test PaymentReminder model and lifecycle."""
        payment = sample_payments[0]

        # Create reminder
        db_session.refresh(payment)  # Ensure fattura relationship is loaded
        reminder = PaymentReminder(
            payment_id=payment.id,
            reminder_date=date.today() + timedelta(days=7),
            status=ReminderStatus.PENDING,
            strategy=ReminderStrategy.DEFAULT,
            email_template="default",
            email_subject=f"Reminder: Payment for invoice {payment.fattura.numero} due soon",
        )

        db_session.add(reminder)
        db_session.commit()

        # Test transitions
        assert reminder.status == ReminderStatus.PENDING

        reminder.mark_sent()
        assert reminder.status == ReminderStatus.SENT
        assert reminder.sent_date is not None

        # Test cancel
        reminder2 = PaymentReminder(
            payment_id=payment.id,
            reminder_date=date.today(),
            status=ReminderStatus.PENDING,
            strategy=ReminderStrategy.GENTLE,
        )
        db_session.add(reminder2)
        db_session.commit()

        reminder2.cancel()
        assert reminder2.status == ReminderStatus.CANCELLED

    def test_match_result_value_object(self):
        """Test MatchResult value object properties."""
        from unittest.mock import Mock

        transaction = Mock()
        transaction.id = uuid4()
        transaction.amount = Decimal("100.00")

        payment = Mock()
        payment.id = 1
        payment.importo = Decimal("100.00")

        # High confidence match
        high_match = MatchResult(
            transaction=transaction,
            payment=payment,
            confidence=0.95,
            match_type=MatchType.EXACT,
            match_reason="Exact amount and reference",
            amount_diff=Decimal("0.00"),
        )

        assert high_match.should_auto_apply is True
        assert high_match.is_high_confidence is True
        assert not high_match.is_medium_confidence
        assert not high_match.is_low_confidence

        # Medium confidence match
        medium_match = MatchResult(
            transaction=transaction,
            payment=payment,
            confidence=0.70,
            match_type=MatchType.FUZZY,
            match_reason="Fuzzy description match",
            amount_diff=Decimal("0.00"),
        )

        assert medium_match.should_auto_apply is False
        assert not medium_match.is_high_confidence
        assert medium_match.is_medium_confidence

    def test_reconciliation_result_value_object(self):
        """Test ReconciliationResult value object calculations."""
        result = ReconciliationResult(
            matched_count=10,
            review_count=5,
            unmatched_count=3,
            total_count=18,
            total_amount_matched=Decimal("15000.00"),
        )

        assert result.match_rate == 10 / 18
        assert result.total_count == 18
        assert not result.has_errors

        # With errors
        result_with_errors = ReconciliationResult(
            matched_count=5,
            review_count=2,
            unmatched_count=1,
            total_count=8,
            errors=["Transaction TX-001 failed validation"],
        )

        assert result_with_errors.has_errors
        assert len(result_with_errors.errors) == 1

    def test_import_result_value_object(self):
        """Test ImportResult value object calculations."""
        result = ImportResult(
            success_count=15,
            error_count=3,
            duplicate_count=2,
            errors=["Row 5: Invalid date", "Row 12: Missing amount", "Row 20: Parse error"],
        )

        assert result.total_count == 20
        assert result.success_rate == 15 / 20
        assert result.has_errors
        assert len(result.errors) == 3

    def test_bank_account_balance_update(self, db_session, sample_bank_account):
        """Test bank account balance updates."""
        initial_balance = sample_bank_account.current_balance

        # Incoming payment
        sample_bank_account.update_balance(Decimal("500.00"))
        assert sample_bank_account.current_balance == initial_balance + Decimal("500.00")

        # Outgoing payment
        sample_bank_account.update_balance(Decimal("-200.00"))
        assert sample_bank_account.current_balance == initial_balance + Decimal("300.00")

    @pytest.mark.asyncio
    async def test_batch_reconciliation_workflow(
        self, db_session, sample_bank_account, sample_payments
    ):
        """Test batch reconciliation with auto-apply."""
        # Create multiple transactions
        transactions = [
            BankTransaction(
                account=sample_bank_account,
                date=date(2024, 10, 15),
                amount=Decimal("500.00"),
                description=f"Payment for INV-2024-001",
                reference="INV-2024-001",
                import_source=ImportSource.CSV,
            ),
            BankTransaction(
                account=sample_bank_account,
                date=date(2024, 10, 16),
                amount=Decimal("1000.00"),
                description=f"Payment for INV-2024-002",
                reference="INV-2024-002",
                import_source=ImportSource.CSV,
            ),
        ]

        for tx in transactions:
            db_session.add(tx)
        db_session.commit()

        # Setup services
        tx_repo = BankTransactionRepository(db_session)
        payment_repo = PaymentRepository(db_session)

        matching_service = MatchingService(
            tx_repo=tx_repo,
            payment_repo=payment_repo,
            strategies=[ExactAmountMatcher(date_tolerance_days=30)],
        )

        reconciliation_service = ReconciliationService(
            tx_repo=tx_repo,
            payment_repo=payment_repo,
            matching_service=matching_service,
        )

        # Batch reconcile
        result = await reconciliation_service.reconcile_batch(
            account_id=sample_bank_account.id,
            auto_apply=True,
            auto_apply_threshold=0.85,
        )

        assert result.total_count >= 2
        assert result.matched_count >= 1  # At least one should auto-match


class TestCSVImportVariants:
    """Test CSV import with various formats."""

    def test_csv_italian_format(self, db_session, sample_bank_account):
        """Test Italian CSV format (semicolon, comma decimals)."""
        csv_content = """Data;Importo;Descrizione
15/10/2024;1.234,56;Bonifico ricevuto
16/10/2024;500,00;Pagamento"""

        with NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_path = Path(f.name)

        config = CSVConfig(
            delimiter=";",
            field_mapping={"date": "Data", "amount": "Importo", "description": "Descrizione"},
            date_format="%d/%m/%Y",
            decimal_separator=",",
            thousands_separator=".",
        )

        importer = CSVImporter(csv_path, config)
        transactions = importer.parse(sample_bank_account)

        assert len(transactions) == 2
        assert transactions[0].amount == Decimal("1234.56")
        assert transactions[1].amount == Decimal("500.00")

        csv_path.unlink()

    def test_csv_us_format(self, db_session, sample_bank_account):
        """Test US CSV format (comma delimiter, dot decimals)."""
        csv_content = """Date,Amount,Description
2024-10-15,1234.56,Wire transfer received
2024-10-16,500.00,Payment"""

        with NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_path = Path(f.name)

        config = CSVConfig(
            delimiter=",",
            field_mapping={"date": "Date", "amount": "Amount", "description": "Description"},
            date_format="%Y-%m-%d",
            decimal_separator=".",
        )

        importer = CSVImporter(csv_path, config)
        transactions = importer.parse(sample_bank_account)

        assert len(transactions) == 2
        assert transactions[0].amount == Decimal("1234.56")

        csv_path.unlink()
