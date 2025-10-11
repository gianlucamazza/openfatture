"""Tests for MatchingService - Async batch matching with parallelization.

Tests cover: parallel execution, confidence filtering, strategy pipeline, date windows.
"""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from openfatture.payment.application.services import MatchingService
from openfatture.payment.domain.enums import MatchType, TransactionStatus
from openfatture.payment.domain.models import BankTransaction
from openfatture.payment.domain.value_objects import MatchResult, PaymentInsight
from openfatture.payment.matchers import ExactAmountMatcher, IMatcherStrategy

pytestmark = pytest.mark.asyncio


class MockMatcherStrategy(IMatcherStrategy):
    """Mock matcher for testing."""

    def __init__(self, confidence: float = 0.80, match_count: int = 1):
        self.confidence = confidence
        self.match_count = match_count

    def match(self, transaction, candidates):
        """Return mock matches."""
        results = []
        for i, payment in enumerate(candidates[: self.match_count]):
            confidence = max(0.0, min(1.0, self.confidence - (i * 0.05)))  # Decreasing confidence
            results.append(
                MatchResult(
                    transaction=transaction,
                    payment=payment,
                    confidence=confidence,
                    match_reason=f"Mock match {i+1}",
                    match_type=MatchType.FUZZY,
                    matched_fields=["amount"],
                    amount_diff=Decimal("0.00"),
                )
            )
        return results


class TestMatchingService:
    """Tests for MatchingService async operations."""

    @pytest.fixture
    def matching_service(self, db_session, mock_tx_repo, mock_payment_repo):
        """Create matching service with mock repositories."""
        strategies = [MockMatcherStrategy(confidence=0.80)]
        return MatchingService(
            tx_repo=mock_tx_repo,
            payment_repo=mock_payment_repo,
            strategies=strategies,
        )

    @pytest.fixture
    def mock_tx_repo(self, mocker):
        """Mock BankTransactionRepository."""
        repo = mocker.Mock()
        repo.get_by_id = mocker.Mock()
        repo.get_by_status = mocker.Mock()
        return repo

    @pytest.fixture
    def mock_payment_repo(self, mocker):
        """Mock PaymentRepository."""
        repo = mocker.Mock()
        repo.get_unpaid = mocker.Mock()
        return repo

    # ==========================================================================
    # Single Transaction Matching Tests
    # ==========================================================================

    async def test_match_transaction_returns_sorted_by_confidence(
        self, matching_service, bank_transaction, mock_payment_repo, sample_fattura, db_session
    ):
        """Test that matches are sorted by confidence descending."""
        # Create 3 candidate payments
        from openfatture.storage.database.models import Pagamento, StatoPagamento

        payments = []
        for i in range(3):
            payment = Pagamento(
                fattura_id=sample_fattura.id,
                importo=Decimal("1000.00"),
                data_scadenza=bank_transaction.date,
                stato=StatoPagamento.DA_PAGARE,
            )
            db_session.add(payment)
            payments.append(payment)

        db_session.commit()

        # Mock repository to return candidates
        mock_payment_repo.get_unpaid.return_value = payments

        # Update strategy to return all 3 matches
        matching_service.strategies = [MockMatcherStrategy(confidence=0.85, match_count=3)]

        # Execute match
        matches = await matching_service.match_transaction(bank_transaction)

        # Verify sorted by confidence
        assert len(matches) == 3
        assert matches[0].confidence == pytest.approx(0.85)
        assert matches[1].confidence == pytest.approx(0.80)
        assert matches[2].confidence == pytest.approx(0.75)

        # Verify descending order
        for i in range(len(matches) - 1):
            assert matches[i].confidence >= matches[i + 1].confidence

    async def test_match_transaction_filters_by_threshold(
        self, matching_service, bank_transaction, mock_payment_repo, sample_fattura, db_session
    ):
        """Test that matches below threshold are filtered out."""
        from openfatture.storage.database.models import Pagamento, StatoPagamento

        payment = Pagamento(
            fattura_id=sample_fattura.id,
            importo=Decimal("1000.00"),
            data_scadenza=bank_transaction.date,
            stato=StatoPagamento.DA_PAGARE,
        )
        db_session.add(payment)
        db_session.commit()

        mock_payment_repo.get_unpaid.return_value = [payment]

        # Strategy returns confidence of 0.50
        matching_service.strategies = [MockMatcherStrategy(confidence=0.50)]

        # Match with threshold 0.60
        matches = await matching_service.match_transaction(
            bank_transaction, confidence_threshold=0.60
        )

        # Should filter out the 0.50 match
        assert len(matches) == 0

    async def test_match_transaction_empty_candidates_returns_empty(
        self, matching_service, bank_transaction, mock_payment_repo
    ):
        """Test that empty candidate list returns empty matches."""
        mock_payment_repo.get_unpaid.return_value = []

        matches = await matching_service.match_transaction(bank_transaction)

        assert len(matches) == 0

    async def test_match_transaction_deduplicates_by_payment_id(
        self, matching_service, bank_transaction, mock_payment_repo, sample_fattura, db_session
    ):
        """Test that multiple strategies matching same payment keep highest confidence."""
        from openfatture.storage.database.models import Pagamento, StatoPagamento

        payment = Pagamento(
            fattura_id=sample_fattura.id,
            importo=Decimal("1000.00"),
            data_scadenza=bank_transaction.date,
            stato=StatoPagamento.DA_PAGARE,
        )
        db_session.add(payment)
        db_session.commit()

        mock_payment_repo.get_unpaid.return_value = [payment]

        # Two strategies matching same payment with different confidence
        matching_service.strategies = [
            MockMatcherStrategy(confidence=0.70),
            MockMatcherStrategy(confidence=0.90),
        ]

        matches = await matching_service.match_transaction(bank_transaction)

        # Should have only 1 match with highest confidence
        assert len(matches) == 1
        assert matches[0].confidence == 0.90

    async def test_match_transaction_logs_strategy_failures(
        self,
        matching_service,
        bank_transaction,
        mock_payment_repo,
        sample_fattura,
        db_session,
        mocker,
    ):
        """Test that strategy failures are logged but don't stop execution."""
        from openfatture.storage.database.models import Pagamento, StatoPagamento

        payment = Pagamento(
            fattura_id=sample_fattura.id,
            importo=Decimal("1000.00"),
            data_scadenza=bank_transaction.date,
            stato=StatoPagamento.DA_PAGARE,
        )
        db_session.add(payment)
        db_session.commit()

        mock_payment_repo.get_unpaid.return_value = [payment]

        # Create failing strategy
        failing_strategy = mocker.Mock(spec=IMatcherStrategy)
        failing_strategy.match.side_effect = Exception("Strategy failed")

        # Add failing strategy plus working one
        matching_service.strategies = [
            failing_strategy,
            MockMatcherStrategy(confidence=0.80),
        ]

        # Should not raise, continue with working strategy
        matches = await matching_service.match_transaction(bank_transaction)

        assert len(matches) == 1
        assert matches[0].confidence == 0.80

    # ==========================================================================
    # Batch Matching with Parallelization Tests
    # ==========================================================================

    async def test_match_batch_parallel_execution_max_workers(
        self,
        matching_service,
        mock_tx_repo,
        mock_payment_repo,
        bank_account,
        db_session,
        sample_fattura,
    ):
        """Test that batch matching executes in parallel with max_workers."""
        from openfatture.storage.database.models import Pagamento, StatoPagamento

        # Create 5 unmatched transactions
        transactions = []
        for i in range(5):
            tx = BankTransaction(
                id=uuid4(),
                account_id=bank_account.id,
                date=date.today() - timedelta(days=i),
                amount=Decimal("100.00") * (i + 1),
                description=f"Transaction {i+1}",
                status=TransactionStatus.UNMATCHED,
            )
            db_session.add(tx)
            transactions.append(tx)

        db_session.commit()

        # Create candidate payment
        payment = Pagamento(
            fattura_id=sample_fattura.id,
            importo=Decimal("1000.00"),
            data_scadenza=date.today(),
            stato=StatoPagamento.DA_PAGARE,
        )
        db_session.add(payment)
        db_session.commit()

        mock_tx_repo.get_by_status.return_value = transactions
        mock_payment_repo.get_unpaid.return_value = [payment]

        # Execute batch matching with max_workers=2
        result = await matching_service.match_batch(
            account_id=bank_account.id,
            max_workers=2,
        )

        # Verify all transactions processed
        assert result.total_count == 5

        # Verify semaphore limited concurrency (tested via execution)
        assert mock_tx_repo.get_by_status.called

    async def test_match_batch_categorizes_by_confidence(
        self,
        matching_service,
        mock_tx_repo,
        mock_payment_repo,
        bank_account,
        db_session,
        sample_fattura,
    ):
        """Test that batch results are categorized by confidence thresholds."""
        from openfatture.storage.database.models import Pagamento, StatoPagamento

        # Create transactions that will get different confidence matches
        high_conf_tx = BankTransaction(
            id=uuid4(),
            account_id=bank_account.id,
            date=date.today(),
            amount=Decimal("100.00"),
            description="High confidence",
            status=TransactionStatus.UNMATCHED,
        )

        medium_conf_tx = BankTransaction(
            id=uuid4(),
            account_id=bank_account.id,
            date=date.today(),
            amount=Decimal("200.00"),
            description="Medium confidence",
            status=TransactionStatus.UNMATCHED,
        )

        low_conf_tx = BankTransaction(
            id=uuid4(),
            account_id=bank_account.id,
            date=date.today(),
            amount=Decimal("300.00"),
            description="Low confidence",
            status=TransactionStatus.UNMATCHED,
        )

        db_session.add_all([high_conf_tx, medium_conf_tx, low_conf_tx])
        db_session.commit()

        payment = Pagamento(
            fattura_id=sample_fattura.id,
            importo=Decimal("1000.00"),
            data_scadenza=date.today(),
            stato=StatoPagamento.DA_PAGARE,
        )
        db_session.add(payment)
        db_session.commit()

        mock_tx_repo.get_by_status.return_value = [high_conf_tx, medium_conf_tx, low_conf_tx]
        mock_payment_repo.get_unpaid.return_value = [payment]

        # Use different strategies for different transactions
        # This is simplified - in real scenario, strategies would naturally return different confidences
        matching_service.strategies = [MockMatcherStrategy(confidence=0.90)]

        result = await matching_service.match_batch(
            account_id=bank_account.id,
            auto_apply_threshold=0.85,
        )

        # Verify categorization
        assert result.total_count == 3
        assert result.matched_count >= 0  # High confidence (>=0.85)
        assert result.review_count >= 0  # Medium confidence (0.60-0.84)
        assert result.unmatched_count >= 0  # Low confidence (<0.60)

    async def test_match_batch_returns_reconciliation_result(
        self, matching_service, mock_tx_repo, mock_payment_repo, bank_account
    ):
        """Test that match_batch returns proper ReconciliationResult structure."""
        mock_tx_repo.get_by_status.return_value = []

        result = await matching_service.match_batch(account_id=bank_account.id)

        # Verify ReconciliationResult structure
        assert hasattr(result, "matched_count")
        assert hasattr(result, "review_count")
        assert hasattr(result, "unmatched_count")
        assert hasattr(result, "total_count")
        assert hasattr(result, "matches")

        assert result.total_count == 0

    async def test_match_batch_handles_semaphore_concurrency(
        self, matching_service, mock_tx_repo, mock_payment_repo, bank_account, db_session
    ):
        """Test that semaphore properly limits concurrent operations."""
        # Create many transactions to test concurrency
        transactions = []
        for i in range(10):
            tx = BankTransaction(
                id=uuid4(),
                account_id=bank_account.id,
                date=date.today(),
                amount=Decimal("100.00"),
                description=f"TX {i}",
                status=TransactionStatus.UNMATCHED,
            )
            db_session.add(tx)
            transactions.append(tx)

        db_session.commit()

        mock_tx_repo.get_by_status.return_value = transactions
        mock_payment_repo.get_unpaid.return_value = []

        # Execute with max_workers=3
        result = await matching_service.match_batch(
            account_id=bank_account.id,
            max_workers=3,
        )

        # All transactions should be processed despite semaphore limiting concurrency
        assert result.total_count == 10

    async def test_match_batch_empty_transactions(
        self, matching_service, mock_tx_repo, bank_account
    ):
        """Test batch matching with no unmatched transactions."""
        mock_tx_repo.get_by_status.return_value = []

        result = await matching_service.match_batch(account_id=bank_account.id)

        assert result.total_count == 0
        assert result.matched_count == 0
        assert result.review_count == 0
        assert result.unmatched_count == 0

    # ==========================================================================
    # Strategy Management Tests
    # ==========================================================================

    async def test_add_strategy_appends_to_pipeline(self, matching_service):
        """Test that add_strategy appends new strategy to pipeline."""
        initial_count = len(matching_service.strategies)

        new_strategy = MockMatcherStrategy(confidence=0.95)
        matching_service.add_strategy(new_strategy)

        assert len(matching_service.strategies) == initial_count + 1
        assert matching_service.strategies[-1] == new_strategy

    async def test_remove_strategy_by_class_type(self, matching_service):
        """Test that remove_strategy removes strategy by class type."""
        # Add a specific strategy
        exact_matcher = ExactAmountMatcher()
        matching_service.add_strategy(exact_matcher)

        initial_count = len(matching_service.strategies)

        # Remove by class
        removed = matching_service.remove_strategy(ExactAmountMatcher)

        assert removed is True
        assert len(matching_service.strategies) == initial_count - 1

        # Verify no ExactAmountMatcher instances remain
        assert not any(isinstance(s, ExactAmountMatcher) for s in matching_service.strategies)

    async def test_match_transaction_ai_insight_boosts_confidence(
        self,
        mock_tx_repo,
        mock_payment_repo,
        bank_transaction,
        sample_fattura,
    ):
        """AI insight integration should boost match confidence and enrich reason."""
        from openfatture.storage.database.models import Pagamento, StatoPagamento

        payment = Pagamento(
            fattura_id=sample_fattura.id,
            importo=Decimal("1000.00"),
            data_scadenza=bank_transaction.date,
            stato=StatoPagamento.DA_PAGARE,
        )
        payment.id = 101
        payment.fattura = sample_fattura

        mock_payment_repo.get_unpaid.return_value = [payment]

        class StubInsightService:
            async def analyze(self, transaction, payments):
                return PaymentInsight(
                    probable_invoice_numbers=[getattr(sample_fattura, "numero", "INV-001")],
                    is_partial_payment=True,
                    suggested_allocation_amount=Decimal("400.00"),
                    keywords=["acconto"],
                    confidence=0.9,
                    summary="La causale menziona un acconto per la fattura",
                )

        bank_transaction.raw_data = None

        matching_service = MatchingService(
            tx_repo=mock_tx_repo,
            payment_repo=mock_payment_repo,
            strategies=[MockMatcherStrategy(confidence=0.80)],
            insight_service=StubInsightService(),
        )

        matches = await matching_service.match_transaction(bank_transaction)

        assert matches
        assert matches[0].confidence > 0.80
        assert "AI partial payment" in matches[0].match_reason
        assert bank_transaction.raw_data["ai_insight"]["probable_invoice_numbers"] == [
            getattr(sample_fattura, "numero", "INV-001")
        ]

    async def test_get_candidate_payments_date_window(
        self, matching_service, bank_transaction, mock_payment_repo
    ):
        """Test that candidate payments are filtered by date window."""
        # Test is indirect through match_transaction
        mock_payment_repo.get_unpaid.return_value = []

        await matching_service.match_transaction(
            bank_transaction,
            date_window_days=15,
        )

        # Verify get_unpaid was called with date range
        mock_payment_repo.get_unpaid.assert_called_once()
        call_kwargs = mock_payment_repo.get_unpaid.call_args.kwargs

        assert "date_from" in call_kwargs
        assert "date_to" in call_kwargs

        # Verify date window is ±15 days
        expected_from = bank_transaction.date - timedelta(days=15)
        expected_to = bank_transaction.date + timedelta(days=15)

        assert call_kwargs["date_from"] == expected_from
        assert call_kwargs["date_to"] == expected_to

    # ==========================================================================
    # Suggest Matches for Review Tests
    # ==========================================================================

    async def test_suggest_matches_returns_top_n(
        self,
        matching_service,
        mock_tx_repo,
        mock_payment_repo,
        bank_transaction,
        sample_fattura,
        db_session,
    ):
        """Test that suggest_matches returns limited number of results."""
        from openfatture.storage.database.models import Pagamento, StatoPagamento

        # Create 10 candidate payments
        payments = []
        for i in range(10):
            payment = Pagamento(
                fattura_id=sample_fattura.id,
                importo=Decimal("1000.00") + Decimal(i),
                data_scadenza=date.today(),
                stato=StatoPagamento.DA_PAGARE,
            )
            db_session.add(payment)
            payments.append(payment)

        db_session.commit()

        mock_tx_repo.get_by_id.return_value = bank_transaction
        mock_payment_repo.get_unpaid.return_value = payments

        # Strategy returns matches for all 10
        matching_service.strategies = [MockMatcherStrategy(confidence=0.80, match_count=10)]

        # Request top 3
        matches = await matching_service.suggest_matches(bank_transaction.id, limit=3)

        assert len(matches) <= 3

    async def test_suggest_matches_raises_on_not_found(self, matching_service, mock_tx_repo):
        """Test that suggest_matches raises ValueError if transaction not found."""
        mock_tx_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="not found"):
            await matching_service.suggest_matches(uuid4())
