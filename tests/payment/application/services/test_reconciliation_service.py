"""Tests for ReconciliationService - Saga pattern orchestration.

Tests cover: multi-step workflows, state transitions, rollback capabilities,
domain event emission, and error handling.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from openfatture.payment.application.services import ReconciliationService
from openfatture.payment.domain.enums import MatchType, TransactionStatus
from openfatture.payment.domain.models import BankTransaction
from openfatture.payment.domain.value_objects import MatchResult, ReconciliationResult
from openfatture.storage.database.models import Pagamento, StatoPagamento

pytestmark = pytest.mark.asyncio


class TestReconciliationService:
    """Tests for ReconciliationService Saga pattern workflows."""

    def _make_payment(
        self,
        importo: Decimal,
        importo_pagato: Decimal = Decimal("0.00"),
        stato: StatoPagamento = StatoPagamento.DA_PAGARE,
        data_scadenza: date | None = None,
    ) -> Pagamento:
        """Utility helper to create Pagamento instances for tests."""

        return Pagamento(
            fattura_id=1,
            importo=importo,
            importo_pagato=importo_pagato,
            data_scadenza=data_scadenza or date.today(),
            stato=stato,
        )

    @pytest.fixture
    def reconciliation_service(
        self, db_session, mock_tx_repo, mock_payment_repo, mock_matching_service
    ):
        """Create reconciliation service with mocked dependencies."""
        return ReconciliationService(
            tx_repo=mock_tx_repo,
            payment_repo=mock_payment_repo,
            matching_service=mock_matching_service,
            session=db_session,
        )

    @pytest.fixture
    def mock_tx_repo(self, mocker):
        """Mock BankTransactionRepository."""
        repo = mocker.Mock()
        repo.get_by_id = mocker.Mock()
        repo.get_by_status = mocker.Mock()
        repo.update = mocker.Mock()
        return repo

    @pytest.fixture
    def mock_payment_repo(self, mocker):
        """Mock PaymentRepository."""
        repo = mocker.Mock()
        repo.get_by_id = mocker.Mock()
        repo.update = mocker.Mock()
        repo.add_allocation = mocker.Mock()
        repo.get_allocation = mocker.Mock()
        repo.delete_allocation = mocker.Mock()
        return repo

    @pytest.fixture
    def mock_matching_service(self, mocker):
        """Mock MatchingService."""
        service = mocker.Mock()
        service.match_transaction = mocker.AsyncMock()
        service.match_batch = mocker.AsyncMock()
        return service

    @pytest.fixture
    def mock_payment(self, mocker):
        """Create a mock payment object."""
        return Pagamento(
            fattura_id=1,
            importo=Decimal("1000.00"),
            importo_pagato=Decimal("0.00"),
            data_scadenza=date.today(),
            stato=StatoPagamento.DA_PAGARE,
        )

    # ==========================================================================
    # Reconcile Workflow Tests (7 tests)
    # ==========================================================================

    async def test_reconcile_success_updates_transaction_and_payment(
        self, reconciliation_service, mock_tx_repo, mock_payment_repo,
        bank_transaction, mocker
    ):
        """Test successful reconciliation updates both transaction and payment."""
        # Create payment with remaining balance
        payment = self._make_payment(Decimal("1000.00"))
        payment.id = 1

        # Setup mocks
        bank_transaction.status = TransactionStatus.UNMATCHED
        bank_transaction.amount = Decimal("-1000.00")
        mock_tx_repo.get_by_id.return_value = bank_transaction
        mock_payment_repo.get_by_id.return_value = payment

        # Execute reconciliation
        result = await reconciliation_service.reconcile(
            transaction_id=bank_transaction.id,
            payment_id=payment.id,
            match_type=MatchType.MANUAL,
            confidence=1.0,
        )

        # Verify transaction updated
        assert result.status == TransactionStatus.MATCHED
        assert result.matched_payment_id == payment.id
        assert result.match_type == MatchType.MANUAL
        assert result.match_confidence == 1.0
        assert result.matched_at is not None

        # Verify payment amount updated
        assert payment.importo_pagato == Decimal("1000.00")

        # Verify repository update called
        mock_tx_repo.update.assert_called_once_with(bank_transaction)

    async def test_reconcile_validates_transaction_status_unmatched(
        self, reconciliation_service, mock_tx_repo, mock_payment_repo, bank_transaction
    ):
        """Test reconcile raises error if transaction is not UNMATCHED."""
        bank_transaction.status = TransactionStatus.MATCHED
        mock_tx_repo.get_by_id.return_value = bank_transaction

        with pytest.raises(ValueError, match="cannot be reconciled"):
            await reconciliation_service.reconcile(
                transaction_id=bank_transaction.id,
                payment_id=1,
            )

    async def test_reconcile_validates_payment_remaining_balance(
        self, reconciliation_service, mock_tx_repo, mock_payment_repo,
        bank_transaction, mocker
    ):
        """Test reconcile validates payment has remaining balance."""
        # Create fully paid payment
        payment = self._make_payment(
            importo=Decimal("1000.00"),
            importo_pagato=Decimal("1000.00"),
            stato=StatoPagamento.PAGATO,
        )
        payment.id = 1

        bank_transaction.status = TransactionStatus.UNMATCHED
        mock_tx_repo.get_by_id.return_value = bank_transaction
        mock_payment_repo.get_by_id.return_value = payment

        # Should raise error for fully paid payment
        with pytest.raises(ValueError, match="already fully paid"):
            await reconciliation_service.reconcile(
                transaction_id=bank_transaction.id,
                payment_id=payment.id,
            )

    async def test_reconcile_raises_on_fully_paid_payment(
        self, reconciliation_service, mock_tx_repo, mock_payment_repo,
        bank_transaction, mocker
    ):
        """Test reconcile raises ValueError when payment is fully paid."""
        payment = self._make_payment(
            importo=Decimal("500.00"),
            importo_pagato=Decimal("500.00"),
            stato=StatoPagamento.PAGATO,
        )
        payment.id = 1

        bank_transaction.status = TransactionStatus.UNMATCHED
        mock_tx_repo.get_by_id.return_value = bank_transaction
        mock_payment_repo.get_by_id.return_value = payment

        with pytest.raises(ValueError, match="fully paid"):
            await reconciliation_service.reconcile(
                transaction_id=bank_transaction.id,
                payment_id=payment.id,
            )

    async def test_reconcile_warns_on_amount_exceeds_remaining(
        self, reconciliation_service, mock_tx_repo, mock_payment_repo,
        bank_transaction, mocker
    ):
        """Test reconcile logs warning when transaction amount exceeds remaining balance."""
        # Payment with partial balance
        payment = mocker.Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.importo_pagato = Decimal("600.00")  # €400 remaining

        # Transaction exceeds remaining
        bank_transaction.status = TransactionStatus.UNMATCHED
        bank_transaction.amount = Decimal("-500.00")  # Exceeds €400 remaining
        mock_tx_repo.get_by_id.return_value = bank_transaction
        mock_payment_repo.get_by_id.return_value = payment

        # Mock logger to verify warning
        mock_logger = mocker.patch("openfatture.payment.application.services.reconciliation_service.logger")

        # Should complete but log warning
        result = await reconciliation_service.reconcile(
            transaction_id=bank_transaction.id,
            payment_id=payment.id,
            match_type=MatchType.MANUAL,
        )

        # Verify reconciliation succeeded
        assert result.status == TransactionStatus.MATCHED

        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args
        assert "transaction_exceeds_payment" in warning_call[0]

    async def test_reconcile_emits_domain_event(
        self, reconciliation_service, mock_tx_repo, mock_payment_repo,
        bank_transaction, mocker
    ):
        """Test reconcile emits TransactionMatched domain event."""
        payment = mocker.Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.importo_pagato = Decimal("0.00")

        bank_transaction.status = TransactionStatus.UNMATCHED
        bank_transaction.amount = Decimal("-1000.00")
        mock_tx_repo.get_by_id.return_value = bank_transaction
        mock_payment_repo.get_by_id.return_value = payment

        # Spy on _emit_transaction_matched_event
        spy = mocker.spy(reconciliation_service, "_emit_transaction_matched_event")

        await reconciliation_service.reconcile(
            transaction_id=bank_transaction.id,
            payment_id=payment.id,
        )

        # Verify event emission
        spy.assert_called_once()
        args = spy.call_args[0]
        assert args[0] == bank_transaction  # transaction
        assert args[1] == payment  # payment

    async def test_reconcile_rollback_on_exception(
        self, reconciliation_service, mock_tx_repo, mock_payment_repo,
        bank_transaction, mocker
    ):
        """Test reconcile raises RuntimeError on exceptions and logs error."""
        payment = mocker.Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.importo_pagato = Decimal("0.00")

        bank_transaction.status = TransactionStatus.UNMATCHED
        mock_tx_repo.get_by_id.return_value = bank_transaction
        mock_payment_repo.get_by_id.return_value = payment

        # Mock update to raise exception
        mock_tx_repo.update.side_effect = Exception("Database error")

        # Should raise RuntimeError wrapping original exception
        with pytest.raises(RuntimeError, match="Reconciliation failed"):
            await reconciliation_service.reconcile(
                transaction_id=bank_transaction.id,
                payment_id=payment.id,
            )

    # ==========================================================================
    # Ignore Transaction Tests (3 tests)
    # ==========================================================================

    async def test_ignore_transaction_sets_status_ignored(
        self, reconciliation_service, mock_tx_repo, bank_transaction
    ):
        """Test ignore_transaction sets status to IGNORED."""
        bank_transaction.status = TransactionStatus.UNMATCHED
        mock_tx_repo.get_by_id.return_value = bank_transaction

        result = await reconciliation_service.ignore_transaction(
            transaction_id=bank_transaction.id,
            reason="Personal expense",
        )

        assert result.status == TransactionStatus.IGNORED
        mock_tx_repo.update.assert_called_once_with(bank_transaction)

    async def test_ignore_transaction_stores_reason_in_raw_data(
        self, reconciliation_service, mock_tx_repo, bank_transaction
    ):
        """Test ignore_transaction stores reason in raw_data."""
        bank_transaction.status = TransactionStatus.UNMATCHED
        bank_transaction.raw_data = {}
        mock_tx_repo.get_by_id.return_value = bank_transaction

        await reconciliation_service.ignore_transaction(
            transaction_id=bank_transaction.id,
            reason="Bank fee",
        )

        assert bank_transaction.raw_data["ignore_reason"] == "Bank fee"
        assert "ignored_at" in bank_transaction.raw_data

    async def test_ignore_transaction_raises_on_already_matched(
        self, reconciliation_service, mock_tx_repo, bank_transaction
    ):
        """Test ignore_transaction raises error if transaction is MATCHED."""
        bank_transaction.status = TransactionStatus.MATCHED
        mock_tx_repo.get_by_id.return_value = bank_transaction

        with pytest.raises(ValueError, match="already matched"):
            await reconciliation_service.ignore_transaction(
                transaction_id=bank_transaction.id,
            )

    # ==========================================================================
    # Reset Transaction Tests (Undo Reconciliation) (3 tests)
    # ==========================================================================

    async def test_reset_transaction_reverts_payment_amount(
        self, reconciliation_service, mock_tx_repo, mock_payment_repo,
        bank_transaction, mocker
    ):
        """Test reset_transaction reverts payment amount (undo)."""
        payment = mocker.Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.importo_pagato = Decimal("500.00")

        bank_transaction.status = TransactionStatus.MATCHED
        bank_transaction.matched_payment_id = payment.id
        bank_transaction.amount = Decimal("-500.00")
        mock_tx_repo.get_by_id.return_value = bank_transaction
        mock_payment_repo.get_by_id.return_value = payment

        await reconciliation_service.reset_transaction(
            transaction_id=bank_transaction.id,
        )

        # Verify payment amount reverted
        assert payment.importo_pagato == Decimal("0.00")

    async def test_reset_transaction_clears_match_metadata(
        self, reconciliation_service, mock_tx_repo, mock_payment_repo,
        bank_transaction, mocker
    ):
        """Test reset_transaction clears all match metadata."""
        payment = mocker.Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.importo_pagato = Decimal("1000.00")

        bank_transaction.status = TransactionStatus.MATCHED
        bank_transaction.matched_payment_id = payment.id
        bank_transaction.match_type = MatchType.EXACT
        bank_transaction.match_confidence = 0.95
        bank_transaction.matched_at = datetime.utcnow()
        mock_tx_repo.get_by_id.return_value = bank_transaction
        mock_payment_repo.get_by_id.return_value = payment

        result = await reconciliation_service.reset_transaction(
            transaction_id=bank_transaction.id,
        )

        # Verify all match metadata cleared
        assert result.status == TransactionStatus.UNMATCHED
        assert result.matched_payment_id is None
        assert result.match_type is None
        assert result.match_confidence is None
        assert result.matched_at is None

    async def test_reset_transaction_raises_on_not_matched(
        self, reconciliation_service, mock_tx_repo, bank_transaction
    ):
        """Test reset_transaction raises error if transaction is not MATCHED."""
        bank_transaction.status = TransactionStatus.UNMATCHED
        mock_tx_repo.get_by_id.return_value = bank_transaction

        with pytest.raises(ValueError, match="is not matched"):
            await reconciliation_service.reset_transaction(
                transaction_id=bank_transaction.id,
            )

    # ==========================================================================
    # Review Queue Tests (2 tests)
    # ==========================================================================

    async def test_get_review_queue_filters_by_confidence_range(
        self, reconciliation_service, mock_tx_repo, mock_matching_service,
        bank_transaction, mocker
    ):
        """Test get_review_queue filters matches by confidence range."""
        # Mock unmatched transactions
        mock_tx_repo.get_by_status.return_value = [bank_transaction]

        # Mock payment objects
        mock_payment1 = mocker.Mock()
        mock_payment1.id = 1
        mock_payment1.importo_da_pagare = Decimal("100")

        mock_payment2 = mocker.Mock()
        mock_payment2.id = 2
        mock_payment2.importo_da_pagare = Decimal("200")

        # Mock matches with varying confidence
        mock_matches = [
            MatchResult(
                transaction=bank_transaction,
                payment=mock_payment1,
                confidence=0.70,  # In range [0.60, 0.84]
                match_type=MatchType.FUZZY,
                match_reason="Test",
            ),
            MatchResult(
                transaction=bank_transaction,
                payment=mock_payment2,
                confidence=0.50,  # Below range
                match_type=MatchType.FUZZY,
                match_reason="Test",
            ),
        ]
        mock_matching_service.match_transaction.return_value = mock_matches

        # Execute
        queue = await reconciliation_service.get_review_queue(
            confidence_range=(0.60, 0.84),
        )

        # Verify only medium-confidence match returned
        assert len(queue) == 1
        tx, matches = queue[0]
        assert len(matches) == 1
        assert matches[0].confidence == 0.70

    async def test_get_review_queue_returns_transactions_with_matches(
        self, reconciliation_service, mock_tx_repo, mock_matching_service,
        bank_transaction, mocker
    ):
        """Test get_review_queue only returns transactions that have matches."""
        # Create 2 transactions
        tx1 = bank_transaction
        tx2 = BankTransaction(
            id=uuid4(),
            account_id=bank_transaction.account_id,
            date=date.today(),
            amount=Decimal("200.00"),
            description="TX 2",
            status=TransactionStatus.UNMATCHED,
        )

        mock_tx_repo.get_by_status.return_value = [tx1, tx2]

        # Mock payment
        mock_payment = mocker.Mock()
        mock_payment.id = 1
        mock_payment.importo_da_pagare = Decimal("100")

        # tx1 has matches, tx2 has none
        async def mock_match_transaction(tx, confidence_threshold):
            if tx.id == tx1.id:
                return [
                    MatchResult(
                        transaction=tx,
                        payment=mock_payment,
                        confidence=0.70,
                        match_type=MatchType.FUZZY,
                        match_reason="Test",
                    )
                ]
            return []

        mock_matching_service.match_transaction.side_effect = mock_match_transaction

        queue = await reconciliation_service.get_review_queue()

        # Only tx1 should be in queue
        assert len(queue) == 1
        assert queue[0][0].id == tx1.id

    # ==========================================================================
    # Batch Reconciliation Tests (2 tests)
    # ==========================================================================

    async def test_reconcile_batch_auto_applies_high_confidence(
        self, reconciliation_service, mock_matching_service, mock_tx_repo,
        mock_payment_repo, bank_transaction, mocker
    ):
        """Test reconcile_batch auto-applies high-confidence matches."""
        payment = mocker.Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.importo_pagato = Decimal("0.00")

        bank_transaction.status = TransactionStatus.UNMATCHED
        bank_transaction.amount = Decimal("-1000.00")

        # Mock batch matching result
        match_result = MatchResult(
            transaction=bank_transaction,
            payment=payment,
            confidence=0.90,  # Above threshold
            match_type=MatchType.EXACT,
            match_reason="Exact match",
        )

        mock_result = ReconciliationResult(
            matched_count=1,
            review_count=0,
            unmatched_count=0,
            total_count=1,
            matches=[(bank_transaction, [match_result])],
        )

        mock_matching_service.match_batch.return_value = mock_result
        mock_tx_repo.get_by_id.return_value = bank_transaction
        mock_payment_repo.get_by_id.return_value = payment

        # Execute batch with auto_apply=True
        result = await reconciliation_service.reconcile_batch(
            account_id=1,
            auto_apply=True,
            auto_apply_threshold=0.85,
        )

        # Verify reconciliation was applied
        assert result.total_count == 1
        mock_tx_repo.update.assert_called_once()

    async def test_reconcile_batch_handles_errors_gracefully(
        self, reconciliation_service, mock_matching_service, mock_tx_repo,
        mock_payment_repo, bank_transaction, mocker
    ):
        """Test reconcile_batch handles reconciliation errors gracefully."""
        payment = mocker.Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.importo_pagato = Decimal("0.00")

        bank_transaction.status = TransactionStatus.UNMATCHED

        match_result = MatchResult(
            transaction=bank_transaction,
            payment=payment,
            confidence=0.90,
            match_type=MatchType.EXACT,
            match_reason="Test",
        )

        mock_result = ReconciliationResult(
            matched_count=1,
            review_count=0,
            unmatched_count=0,
            total_count=1,
            matches=[(bank_transaction, [match_result])],
        )

        mock_matching_service.match_batch.return_value = mock_result

        # Mock get_by_id to return None (transaction not found error)
        mock_tx_repo.get_by_id.return_value = None

        # Mock logger to verify error logging
        mock_logger = mocker.patch("openfatture.payment.application.services.reconciliation_service.logger")

        # Should not raise, but log errors
        result = await reconciliation_service.reconcile_batch(
            account_id=1,
            auto_apply=True,
        )

        # Verify error was logged
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args
        assert "auto_reconcile_failed" in error_call[0]
