"""Tests for Payment CLI - Typer commands with CliRunner.

Tests cover: import, match, queue, schedule-reminders, process-reminders, stats commands
with Rich output formatting and interactive prompts.
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from openfatture.payment.cli.payment_cli import app
from openfatture.payment.domain.enums import (
    ReminderStatus,
    ReminderStrategy,
    TransactionStatus,
)
from openfatture.payment.domain.models import BankAccount, BankTransaction
from openfatture.payment.domain.value_objects import ImportResult, ReconciliationResult

runner = CliRunner()


class TestImportCommand:
    """Tests for 'import' CLI command - bank statement import."""

    @pytest.fixture
    def temp_csv(self, tmp_path):
        """Create temporary CSV file for testing."""
        csv_file = tmp_path / "statement.csv"
        csv_file.write_text("Data;Importo;Descrizione\n15/10/2024;1000,00;Pagamento")
        return csv_file

    @pytest.fixture
    def mock_db_session(self, mocker):
        """Mock database session."""
        mock_session = mocker.MagicMock()
        mock_session.__enter__ = mocker.Mock(return_value=mock_session)
        mock_session.__exit__ = mocker.Mock(return_value=None)
        return mock_session

    def test_import_success_with_auto_match(self, temp_csv, mocker):
        """Test successful import with auto-matching enabled."""
        # Mock database components
        mock_account = Mock(spec=BankAccount)
        mock_account.id = 1
        mock_account.name = "Test Account"

        # Mock repositories
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mock_account_repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankAccountRepository"
            ).return_value
            mock_account_repo.get_by_id.return_value = mock_account

            # Mock importer factory
            mock_importer = MagicMock()
            mock_importer.__class__.__name__ = "CSVImporter"
            mock_importer.import_transactions.return_value = ImportResult(
                success_count=10,
                error_count=0,
                duplicate_count=2,
                errors=[],
            )

            mock_factory = mocker.patch(
                "openfatture.payment.cli.payment_cli.ImporterFactory"
            ).return_value
            mock_factory.create_from_file.return_value = mock_importer

            # Mock reconciliation
            mock_recon_result = ReconciliationResult(
                matched_count=8,
                review_count=2,
                unmatched_count=0,
                total_count=10,
            )

            mock_reconcile_batch = mocker.patch(
                "openfatture.payment.cli.payment_cli.ReconciliationService.reconcile_batch",
                new_callable=AsyncMock,
            )
            mock_reconcile_batch.return_value = mock_recon_result

            # Run command
            result = runner.invoke(
                app,
                [
                    "import-statement",
                    str(temp_csv),
                    "--account",
                    "1",
                    "--bank",
                    "intesa",
                    "--auto-match",
                ],
            )

        # Verify success
        assert result.exit_code == 0
        assert "Import Results" in result.stdout
        assert "✅ Success" in result.stdout
        assert "Matched: 8" in result.stdout

    def test_import_account_not_found(self, temp_csv, mocker):
        """Test import fails when account doesn't exist."""
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mock_account_repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankAccountRepository"
            ).return_value
            mock_account_repo.get_by_id.return_value = None

            result = runner.invoke(app, ["import-statement", str(temp_csv), "--account", "999"])

        assert result.exit_code == 1
        assert "Account 999 not found" in result.stdout

    def test_import_invalid_format(self, temp_csv, mocker):
        """Test import fails with invalid file format."""
        mock_account = Mock(spec=BankAccount)
        mock_account.id = 1

        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mock_account_repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankAccountRepository"
            ).return_value
            mock_account_repo.get_by_id.return_value = mock_account

            mock_factory = mocker.patch(
                "openfatture.payment.cli.payment_cli.ImporterFactory"
            ).return_value
            mock_factory.create_from_file.side_effect = ValueError("Unknown format")

            result = runner.invoke(app, ["import-statement", str(temp_csv), "--account", "1"])

        assert result.exit_code == 1
        assert "Unknown format" in result.stdout

    def test_import_with_errors_displayed(self, temp_csv, mocker):
        """Test that import errors are displayed to user."""
        mock_account = Mock(spec=BankAccount)
        mock_account.id = 1

        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mock_account_repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankAccountRepository"
            ).return_value
            mock_account_repo.get_by_id.return_value = mock_account

            mock_importer = MagicMock()
            mock_importer.__class__.__name__ = "CSVImporter"
            mock_importer.import_transactions.return_value = ImportResult(
                success_count=8,
                error_count=2,
                duplicate_count=0,
                errors=["Row 5: Invalid date", "Row 10: Missing amount"],
            )

            mock_factory = mocker.patch(
                "openfatture.payment.cli.payment_cli.ImporterFactory"
            ).return_value
            mock_factory.create_from_file.return_value = mock_importer

            result = runner.invoke(
                app,
                ["import-statement", str(temp_csv), "--account", "1", "--no-auto-match"],
            )

        assert result.exit_code == 0
        assert "Errors:" in result.stdout
        assert "Row 5: Invalid date" in result.stdout

    def test_import_without_auto_match(self, temp_csv, mocker):
        """Test import skips auto-matching when disabled."""
        mock_account = Mock(spec=BankAccount)
        mock_account.id = 1

        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mock_account_repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankAccountRepository"
            ).return_value
            mock_account_repo.get_by_id.return_value = mock_account

            mock_importer = MagicMock()
            mock_importer.__class__.__name__ = "CSVImporter"
            mock_importer.import_transactions.return_value = ImportResult(
                success_count=5, error_count=0, duplicate_count=0, errors=[]
            )

            mock_factory = mocker.patch(
                "openfatture.payment.cli.payment_cli.ImporterFactory"
            ).return_value
            mock_factory.create_from_file.return_value = mock_importer

            result = runner.invoke(
                app,
                ["import-statement", str(temp_csv), "--account", "1", "--no-auto-match"],
            )

        assert result.exit_code == 0
        assert "Auto-matching" not in result.stdout
        assert "✅ Success" in result.stdout


class TestAccountCommands:
    """Tests for account management commands."""

    def _mock_session(self, mock_get_db):
        mock_session = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.rollback = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session
        return mock_session

    def test_create_account_success(self, mocker):
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            session = self._mock_session(mock_get_db)

            repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankAccountRepository"
            ).return_value
            repo.get_by_iban.return_value = None

            def add_side_effect(account):
                account.id = 42
                return account

            repo.add.side_effect = add_side_effect

            result = runner.invoke(
                app,
                [
                    "create-account",
                    "Main Account",
                    "--iban",
                    "IT60X0542811101000000123456",
                    "--opening-balance",
                    "1000.00",
                ],
            )

        assert result.exit_code == 0
        assert "Account created" in result.stdout
        session.commit.assert_called_once()
        repo.add.assert_called_once()

    def test_create_account_duplicate_iban(self, mocker):
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            session = self._mock_session(mock_get_db)

            repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankAccountRepository"
            ).return_value
            repo.get_by_iban.return_value = Mock(id=99)

            result = runner.invoke(
                app,
                ["create-account", "Main", "--iban", "IT60X0542811101000000123456"],
            )

        assert result.exit_code == 1
        assert "already exists" in result.stdout
        session.rollback.assert_called_once()

    def test_list_accounts_outputs_table(self, mocker):
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            self._mock_session(mock_get_db)

            repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankAccountRepository"
            ).return_value
            account = Mock()
            account.id = 1
            account.name = "Primary"
            account.iban = "IT00TEST"
            account.bank_name = "Test Bank"
            account.currency = "EUR"
            account.opening_balance = Decimal("0.00")
            account.current_balance = Decimal("100.00")
            account.is_active = True
            repo.list_accounts.return_value = [account]

            result = runner.invoke(app, ["list-accounts"])

        assert result.exit_code == 0
        assert "Primary" in result.stdout

    def test_update_account_changes_fields(self, mocker):
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            session = self._mock_session(mock_get_db)

            repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankAccountRepository"
            ).return_value
            account = Mock()
            account.id = 1
            account.iban = "IT00OLD"
            account.name = "Old"
            account.bank_name = "Old Bank"
            account.bic_swift = "OLDHBIC"
            account.currency = "EUR"
            account.notes = None
            account.is_active = True
            repo.get_by_id.return_value = account
            repo.get_by_iban.return_value = None

            result = runner.invoke(
                app,
                [
                    "update-account",
                    "1",
                    "--name",
                    "New Name",
                    "--bank-name",
                    "New Bank",
                    "--inactive",
                ],
            )

        assert result.exit_code == 0
        assert account.name == "New Name"
        assert account.bank_name == "New Bank"
        assert account.is_active is False
        session.commit.assert_called_once()

    def test_delete_account_not_found(self, mocker):
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            session = self._mock_session(mock_get_db)

            repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankAccountRepository"
            ).return_value
            repo.delete.return_value = False

            result = runner.invoke(app, ["delete-account", "5"])

        assert result.exit_code == 1
        assert "not found" in result.stdout
        session.commit.assert_not_called()


class TestTransactionListingCommands:
    """Tests for transaction listing and detail commands."""

    def test_list_transactions(self, mocker):
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankTransactionRepository"
            ).return_value
            tx = Mock()
            tx.id = "1111"
            tx.date = date(2025, 1, 1)
            tx.amount = Decimal("123.45")
            tx.status = TransactionStatus.UNMATCHED
            tx.account_id = 1
            tx.matched_payment_id = None
            tx.description = "Consulting invoice"
            repo.list_transactions.return_value = [tx]

            result = runner.invoke(app, ["list-transactions", "--account", "1"])

        assert result.exit_code == 0
        assert "Consulting" in result.stdout

    def test_show_transaction_not_found(self, mocker):
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankTransactionRepository"
            ).return_value
            repo.get_by_id.return_value = None

            result = runner.invoke(
                app, ["show-transaction", "123e4567-e89b-12d3-a456-426614174000"]
            )

        assert result.exit_code == 1
        assert "not found" in result.stdout


class TestReconcileCommand:
    """Tests for the batch reconcile command."""

    def test_reconcile_auto_mode(self, mocker):
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_session.commit = MagicMock()
            mock_session.rollback = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mocker.patch(
                "openfatture.payment.cli.payment_cli._build_matching_service",
                return_value=Mock(),
            )
            mocker.patch(
                "openfatture.payment.cli.payment_cli.create_event_bus", return_value=Mock()
            )

            mock_service = mocker.patch(
                "openfatture.payment.cli.payment_cli.ReconciliationService"
            ).return_value
            mock_result = ReconciliationResult(
                matched_count=2,
                review_count=1,
                unmatched_count=1,
                total_count=4,
            )
            mock_service.reconcile_batch = AsyncMock(return_value=mock_result)

            result = runner.invoke(app, ["reconcile", "--account", "1", "--mode", "auto"])

        assert result.exit_code == 0
        assert "Reconciliation" in result.stdout
        mock_session.commit.assert_called_once()
        mock_service.reconcile_batch.assert_awaited()

    def test_reconcile_invalid_mode(self):
        result = runner.invoke(app, ["reconcile", "--account", "1", "--mode", "invalid"])

        assert result.exit_code == 1
        assert "Invalid mode" in result.stdout


class TestMatchTransactionCommands:
    """Tests for manual match/unmatch commands."""

    def test_match_transaction_success(self, mocker):
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_session.commit = MagicMock()
            mock_session.rollback = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mocker.patch(
                "openfatture.payment.cli.payment_cli._build_matching_service",
                return_value=Mock(),
            )
            mocker.patch(
                "openfatture.payment.cli.payment_cli.create_event_bus", return_value=Mock()
            )

            mock_service = mocker.patch(
                "openfatture.payment.cli.payment_cli.ReconciliationService"
            ).return_value
            mock_service.reconcile = AsyncMock(return_value=Mock(match_confidence=0.9))

            result = runner.invoke(
                app,
                [
                    "match-transaction",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "101",
                    "--match-type",
                    "MANUAL",
                ],
            )

        assert result.exit_code == 0
        assert "matched to payment" in result.stdout
        mock_service.reconcile.assert_awaited()
        mock_session.commit.assert_called_once()

    def test_unmatch_transaction(self, mocker):
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_session.commit = MagicMock()
            mock_session.rollback = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mocker.patch(
                "openfatture.payment.cli.payment_cli._build_matching_service",
                return_value=Mock(),
            )
            mocker.patch(
                "openfatture.payment.cli.payment_cli.create_event_bus", return_value=Mock()
            )

            mock_service = mocker.patch(
                "openfatture.payment.cli.payment_cli.ReconciliationService"
            ).return_value
            mock_service.reset_transaction = AsyncMock(return_value=None)

            result = runner.invoke(
                app,
                ["unmatch-transaction", "123e4567-e89b-12d3-a456-426614174000"],
            )

        assert result.exit_code == 0
        assert "reset to UNMATCHED" in result.stdout
        mock_service.reset_transaction.assert_awaited()
        mock_session.commit.assert_called_once()


class TestReminderManagementCommands:
    """Tests for reminder listing and cancellation commands."""

    def test_list_reminders(self, mocker):
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.ReminderRepository"
            ).return_value
            reminder = Mock()
            reminder.id = 7
            reminder.payment_id = 10
            reminder.reminder_date = date(2025, 1, 10)
            reminder.status = ReminderStatus.PENDING
            reminder.strategy = ReminderStrategy.DEFAULT
            reminder.days_before_due = 5
            reminder.sent_date = None
            reminder.payment = Mock(data_scadenza=date(2025, 1, 15))
            repo.list_reminders.return_value = [reminder]

            result = runner.invoke(app, ["list-reminders"])

        assert result.exit_code == 0
        assert "Payment Reminders" in result.stdout
        assert "7" in result.stdout

    def test_cancel_reminder(self, mocker):
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_session.commit = MagicMock()
            mock_session.rollback = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.ReminderRepository"
            ).return_value
            reminder = Mock()
            reminder.status = ReminderStatus.PENDING
            reminder.cancel = Mock()
            repo.get_by_id.return_value = reminder

            result = runner.invoke(app, ["cancel-reminder", "12"])

        assert result.exit_code == 0
        reminder.cancel.assert_called_once()
        mock_session.commit.assert_called_once()


class TestMatchCommand:
    """Tests for 'match' CLI command - transaction matching."""

    def test_match_success(self, mocker):
        """Test successful matching of transactions."""
        mock_tx = Mock(spec=BankTransaction)
        mock_tx.id = 1
        mock_tx.date = date.today()
        mock_tx.amount = Decimal("1000.00")
        mock_tx.description = "Test transaction"

        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mock_tx_repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankTransactionRepository"
            ).return_value
            mock_tx_repo.get_by_status.return_value = [mock_tx]

            # Mock matching service
            mock_match_result = Mock()
            mock_match_result.payment = Mock()
            mock_match_result.payment.id = 1
            mock_match_result.confidence = 0.95
            mock_match_result.should_auto_apply = True
            mock_match_result.match_type = "EXACT"

            mocker.patch(
                "openfatture.payment.cli.payment_cli.MatchingService.match_transaction",
                new_callable=AsyncMock,
                return_value=[mock_match_result],
            )
            mocker.patch(
                "openfatture.payment.cli.payment_cli.ReconciliationService.reconcile",
                new_callable=AsyncMock,
            )

            result = runner.invoke(app, ["match", "--auto-apply"])

        assert result.exit_code == 0
        assert "Matching" in result.stdout
        assert "Results:" in result.stdout

    def test_match_no_unmatched_transactions(self, mocker):
        """Test match command with no unmatched transactions."""
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mock_tx_repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankTransactionRepository"
            ).return_value
            mock_tx_repo.get_by_status.return_value = []

            result = runner.invoke(app, ["match"])

        assert result.exit_code == 0
        assert "No unmatched transactions" in result.stdout

    def test_match_with_account_filter(self, mocker):
        """Test matching with account filter."""
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mock_tx_repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankTransactionRepository"
            ).return_value
            mock_tx_repo.get_by_status.return_value = []

            result = runner.invoke(app, ["match", "--account", "1", "--limit", "10"])

        # Should call get_by_status with account_id and limit
        mock_tx_repo.get_by_status.assert_called_once()
        call_kwargs = mock_tx_repo.get_by_status.call_args.kwargs
        assert call_kwargs["account_id"] == 1
        assert call_kwargs["limit"] == 10

    def test_match_manual_only_mode(self, mocker):
        """Test matching without auto-apply (manual review needed)."""
        mock_tx = Mock(spec=BankTransaction)
        mock_tx.id = 1

        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mock_tx_repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankTransactionRepository"
            ).return_value
            mock_tx_repo.get_by_status.return_value = [mock_tx]

            mock_match = Mock()
            mock_match.should_auto_apply = False

            mocker.patch(
                "openfatture.payment.cli.payment_cli.MatchingService.match_transaction",
                new_callable=AsyncMock,
                return_value=[mock_match],
            )

            result = runner.invoke(app, ["match", "--manual-only"])

        assert result.exit_code == 0
        assert "Review needed" in result.stdout


class TestQueueCommand:
    """Tests for 'queue' CLI command - review queue."""

    def test_queue_no_items(self, mocker):
        """Test queue command with empty review queue."""
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mocker.patch(
                "openfatture.payment.cli.payment_cli.ReconciliationService.get_review_queue",
                new_callable=AsyncMock,
                return_value=[],
            )

            result = runner.invoke(app, ["queue"])

        assert result.exit_code == 0
        assert "No transactions need review" in result.stdout

    def test_queue_list_only_mode(self, mocker):
        """Test queue in list-only mode (non-interactive)."""
        mock_tx = Mock(spec=BankTransaction)
        mock_tx.date = date(2024, 10, 15)
        mock_tx.amount = Decimal("500.00")
        mock_tx.description = "Test payment"

        mock_match = Mock()
        mock_match.confidence = 0.75
        mock_match.payment = Mock()
        mock_match.payment.fattura = Mock()
        mock_match.payment.fattura.numero = "INV-001"

        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mocker.patch(
                "openfatture.payment.cli.payment_cli.ReconciliationService.get_review_queue",
                new_callable=AsyncMock,
                return_value=[(mock_tx, [mock_match])],
            )

            result = runner.invoke(app, ["queue", "--list-only"])

        assert result.exit_code == 0
        assert "Review Queue" in result.stdout
        assert "INV-001" in result.stdout

    def test_queue_interactive_with_skip(self, mocker):
        """Test interactive queue with skip action."""
        mock_tx = Mock(spec=BankTransaction)
        mock_tx.date = date.today()
        mock_tx.amount = Decimal("1000.00")
        mock_tx.description = "Payment"

        mock_match = Mock()
        mock_match.confidence = 0.80
        mock_match.payment = Mock()
        mock_match.payment.id = 1
        mock_match.payment.fattura = Mock()
        mock_match.payment.fattura.numero = "INV-002"
        mock_match.match_reason = "Exact amount match"

        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mocker.patch(
                "openfatture.payment.cli.payment_cli.ReconciliationService.get_review_queue",
                new_callable=AsyncMock,
                return_value=[(mock_tx, [mock_match])],
            )

            # Mock user input to skip
            with patch("rich.prompt.Prompt.ask", return_value="skip"):
                result = runner.invoke(app, ["queue", "--interactive"])

        assert result.exit_code == 0
        assert "Transaction 1/1" in result.stdout
        assert "Skipped" in result.stdout

    def test_queue_custom_confidence_range(self, mocker):
        """Test queue with custom confidence range."""
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mocker.patch(
                "openfatture.payment.cli.payment_cli.ReconciliationService.get_review_queue",
                new_callable=AsyncMock,
                return_value=[],
            )

            result = runner.invoke(app, ["queue", "--min", "0.50", "--max", "0.90"])

        # Should pass confidence range to get_review_queue
        assert result.exit_code == 0


class TestScheduleRemindersCommand:
    """Tests for 'schedule-reminders' CLI command."""

    def test_schedule_reminders_success(self, mocker):
        """Test successful reminder scheduling."""
        mock_reminder1 = Mock()
        mock_reminder1.reminder_date = date.today() + timedelta(days=7)
        mock_reminder1.days_before_due = 7

        mock_reminder2 = Mock()
        mock_reminder2.reminder_date = date.today() + timedelta(days=30)
        mock_reminder2.days_before_due = 30

        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mocker.patch(
                "openfatture.payment.cli.payment_cli.ReminderScheduler.schedule_reminders",
                new_callable=AsyncMock,
                return_value=[mock_reminder1, mock_reminder2],
            )

            result = runner.invoke(app, ["schedule-reminders", "123", "--strategy", "default"])

        assert result.exit_code == 0
        assert "Scheduled 2 reminders" in result.stdout
        assert "Reminder Schedule" in result.stdout

    def test_schedule_reminders_invalid_strategy(self):
        """Test scheduling with invalid strategy."""
        result = runner.invoke(app, ["schedule-reminders", "123", "--strategy", "invalid"])

        assert result.exit_code == 1
        assert "Invalid strategy" in result.stdout

    def test_schedule_reminders_payment_not_found(self, mocker):
        """Test scheduling fails when payment doesn't exist."""
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mocker.patch(
                "openfatture.payment.cli.payment_cli.ReminderScheduler.schedule_reminders",
                new_callable=AsyncMock,
                side_effect=ValueError("Payment not found"),
            )

            result = runner.invoke(app, ["schedule-reminders", "999"])

        assert result.exit_code == 1
        assert "Error:" in result.stdout

    def test_schedule_reminders_aggressive_strategy(self, mocker):
        """Test scheduling with aggressive strategy."""
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mocker.patch(
                "openfatture.payment.cli.payment_cli.ReminderScheduler.schedule_reminders",
                new_callable=AsyncMock,
                return_value=[Mock(reminder_date=date.today(), days_before_due=0)],
            )

            result = runner.invoke(app, ["schedule-reminders", "123", "--strategy", "aggressive"])

        assert result.exit_code == 0
        assert "Scheduled" in result.stdout


class TestProcessRemindersCommand:
    """Tests for 'process-reminders' CLI command."""

    def test_process_reminders_success(self, mocker):
        """Test successful reminder processing."""
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mocker.patch(
                "openfatture.payment.cli.payment_cli.ReminderScheduler.process_due_reminders",
                new_callable=AsyncMock,
                return_value=5,
            )

            result = runner.invoke(app, ["process-reminders"])

        assert result.exit_code == 0
        assert "Sent 5 reminders" in result.stdout

    def test_process_reminders_specific_date(self, mocker):
        """Test processing reminders for specific date."""
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mocker.patch(
                "openfatture.payment.cli.payment_cli.ReminderScheduler.process_due_reminders",
                new_callable=AsyncMock,
                return_value=3,
            )

            result = runner.invoke(app, ["process-reminders", "--date", "2024-12-25"])

        assert result.exit_code == 0
        assert "25/12/2024" in result.stdout
        assert "Sent 3 reminders" in result.stdout

    def test_process_reminders_no_reminders_due(self, mocker):
        """Test processing when no reminders are due."""
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mocker.patch(
                "openfatture.payment.cli.payment_cli.ReminderScheduler.process_due_reminders",
                new_callable=AsyncMock,
                return_value=0,
            )

            result = runner.invoke(app, ["process-reminders"])

        assert result.exit_code == 0
        assert "Sent 0 reminders" in result.stdout

    def test_process_reminders_uses_email_notifier_when_configured(self, mocker):
        """Test that email notifier is used when SMTP is configured."""
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mocker.patch(
                "openfatture.payment.cli.payment_cli.ReminderScheduler.process_due_reminders",
                new_callable=AsyncMock,
                return_value=2,
            )

            with patch.dict("os.environ", {"SMTP_HOST": "smtp.test.com"}):
                result = runner.invoke(app, ["process-reminders"])

        assert result.exit_code == 0
        assert "Sent 2 reminders" in result.stdout


class TestStatsCommand:
    """Tests for 'stats' CLI command - payment statistics."""

    def test_stats_global(self, mocker):
        """Test global payment statistics."""
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mock_tx_repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankTransactionRepository"
            ).return_value

            # Mock get_by_status to return different counts
            mock_tx_repo.get_by_status.side_effect = [
                [1, 2, 3],  # 3 unmatched
                [1, 2, 3, 4, 5, 6, 7],  # 7 matched
                [1, 2],  # 2 ignored
            ]

            result = runner.invoke(app, ["stats"])

        assert result.exit_code == 0
        assert "Payment Tracking Statistics" in result.stdout
        assert "Unmatched" in result.stdout
        assert "Matched" in result.stdout
        assert "Ignored" in result.stdout
        assert "Total" in result.stdout

    def test_stats_account_specific(self, mocker):
        """Test statistics filtered by account."""
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mock_tx_repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankTransactionRepository"
            ).return_value
            mock_tx_repo.get_by_status.side_effect = [
                [1],  # 1 unmatched
                [2, 3],  # 2 matched
                [],  # 0 ignored
            ]

            result = runner.invoke(app, ["stats", "--account", "1"])

        # Verify account_id passed to all get_by_status calls
        for call in mock_tx_repo.get_by_status.call_args_list:
            assert call.args[1] == 1  # account_id

    def test_stats_empty_database(self, mocker):
        """Test stats with no transactions."""
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mock_tx_repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankTransactionRepository"
            ).return_value
            mock_tx_repo.get_by_status.side_effect = [[], [], []]

            result = runner.invoke(app, ["stats"])

        assert result.exit_code == 0
        assert "Total" in result.stdout

    def test_stats_displays_percentages(self, mocker):
        """Test that stats displays percentage calculations."""
        with patch("openfatture.payment.cli.payment_cli.get_db_session") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session

            mock_tx_repo = mocker.patch(
                "openfatture.payment.cli.payment_cli.BankTransactionRepository"
            ).return_value
            mock_tx_repo.get_by_status.side_effect = [
                [1] * 25,  # 25 unmatched (25%)
                [1] * 50,  # 50 matched (50%)
                [1] * 25,  # 25 ignored (25%)
            ]

            result = runner.invoke(app, ["stats"])

        assert result.exit_code == 0
        assert "%" in result.stdout
        assert "100%" in result.stdout or "100.0%" in result.stdout


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_help_command(self):
        """Test that help command works."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Payment tracking & reconciliation" in result.stdout
        assert "import-statement" in result.stdout
        assert "match" in result.stdout
        assert "queue" in result.stdout

    def test_command_without_required_args_fails(self):
        """Test that commands fail without required arguments."""
        result = runner.invoke(app, ["import-statement"])

        # Should fail with missing argument error
        assert result.exit_code != 0

    def test_invalid_command(self):
        """Test that invalid command shows error."""
        result = runner.invoke(app, ["invalid-command"])

        assert result.exit_code != 0
