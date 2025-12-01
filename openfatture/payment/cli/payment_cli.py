"""Payment tracking CLI commands.

Provides interactive commands for bank statement import, transaction matching,
reconciliation, and payment reminders.
"""

from openfatture.utils.async_bridge import run_async
import os
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import typer
from rich.console import Console
from rich.progress import track
from rich.prompt import Prompt
from rich.table import Table
from sqlalchemy.orm import Session

from ...ai.agents.payment_insight_agent import PaymentInsightAgent
from ...ai.providers.base import ProviderError
from ...ai.providers.factory import create_provider
from ...storage.database import get_db
from ...utils.logging import get_logger
from ..application import create_event_bus
from ..application.notifications import ConsoleNotifier, EmailNotifier, SMTPConfig
from ..application.services import (
    MatchingService,
    ReconciliationService,
    ReminderRepository,
    ReminderScheduler,
    TransactionInsightService,
)
from ..domain.enums import MatchType, ReminderStatus, ReminderStrategy, TransactionStatus
from ..domain.models import BankAccount
from ..infrastructure.importers import ImporterFactory
from ..infrastructure.repository import (
    BankAccountRepository,
    BankTransactionRepository,
    PaymentRepository,
)
from ..matchers import CompositeMatcher, ExactAmountMatcher, IMatcherStrategy

app = typer.Typer(name="payment", help="💰 Payment tracking & reconciliation", no_args_is_help=True)
console = Console()
logger = get_logger(__name__)

_INSIGHT_SERVICE: TransactionInsightService | None = None
_INSIGHT_INITIALIZED = False


def _run(coro):
    """Execute coroutine synchronously using a fresh event loop."""
    return run_async(coro)


@contextmanager
def get_db_session() -> Iterator[Session]:
    """Provide a managed SQLAlchemy session using the shared generator helper."""
    db_generator = get_db()
    session = next(db_generator)
    try:
        yield session
    finally:
        try:
            db_generator.close()
        except RuntimeError:
            # If the generator is already closed (e.g., during test mocks), ignore.
            pass


# ============================================================================
# ACCOUNT COMMANDS
# ============================================================================


@app.command(name="create-account")
def create_account(
    name: str = typer.Argument(..., help="Account name (e.g., 'Main Business Account')"),
    iban: str | None = typer.Option(
        None, "--iban", help="IBAN (International Bank Account Number)"
    ),
    bank_name: str | None = typer.Option(
        None, "--bank-name", help="Bank name (e.g., 'Intesa Sanpaolo')"
    ),
    bic: str | None = typer.Option(
        None, "--bic", help="BIC/SWIFT code for international transfers"
    ),
    currency: str = typer.Option(
        "EUR", "--currency", help="Currency code (ISO 4217, default: EUR)"
    ),
    opening_balance: float = typer.Option(
        0.00, "--opening-balance", help="Opening balance in account currency (default: 0.00)"
    ),
    notes: str | None = typer.Option(None, "--notes", help="Optional notes about the account"),
) -> None:
    """
    Create a bank account for payment reconciliation.

    Bank accounts are used to import transaction data and automatically match
    payments to outstanding invoices. IBAN is required for most European banks.
    """
    with get_db_session() as session:
        repo = BankAccountRepository(session)
        try:
            if iban:
                existing = repo.get_by_iban(iban)
                if existing:
                    console.print(
                        f"[red]✗ An account with IBAN {iban} already exists (ID {existing.id}).[/]"
                    )
                    raise typer.Exit(1)

            opening_amount = Decimal(str(opening_balance))

            account = BankAccount(
                name=name,
                iban=iban,
                bank_name=bank_name,
                bic_swift=bic,
                currency=currency.upper(),
                opening_balance=opening_amount,
                current_balance=opening_amount,
                notes=notes,
            )
            repo.add(account)
            session.commit()
            console.print(f"[green]✓ Account created with ID {account.id}[/]")
        except typer.Exit:
            session.rollback()
            raise
        except Exception as exc:  # pragma: no cover - defensive logging
            session.rollback()
            console.print(f"[red]✗ Failed to create account: {exc}[/]")
            raise typer.Exit(1) from exc


@app.command(name="list-accounts")
def list_accounts(
    include_inactive: bool = typer.Option(
        False, "--all", help="Include inactive accounts in the result list"
    ),
) -> None:
    """List configured bank accounts."""
    with get_db_session() as session:
        repo = BankAccountRepository(session)
        accounts = repo.list_accounts(include_inactive=include_inactive)

        if not accounts:
            console.print("[yellow]ℹ️  No bank accounts configured yet.[/]")
            return

        table = Table(title="🏦 Bank Accounts", show_lines=False)
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Name", style="bold")
        table.add_column("IBAN", style="dim")
        table.add_column("Bank")
        table.add_column("Currency", justify="center")
        table.add_column("Opening", justify="right")
        table.add_column("Current", justify="right")
        table.add_column("Active", justify="center")

        for account in accounts:
            table.add_row(
                str(account.id),
                account.name,
                account.iban or "-",
                account.bank_name or "-",
                account.currency,
                f"{account.opening_balance:.2f}",
                f"{account.current_balance:.2f}",
                "✅" if account.is_active else "❌",
            )

        console.print(table)


@app.command(name="update-account")
def update_account(
    account_id: int = typer.Argument(..., help="Account ID to update"),
    name: str | None = typer.Option(None, "--name", help="New account name"),
    iban: str | None = typer.Option(None, "--iban", help="New IBAN"),
    bank_name: str | None = typer.Option(None, "--bank-name", help="New bank name"),
    bic: str | None = typer.Option(None, "--bic", help="New BIC/SWIFT code"),
    currency: str | None = typer.Option(None, "--currency", help="New currency code"),
    notes: str | None = typer.Option(None, "--notes", help="Overwrite notes"),
    active: bool | None = typer.Option(
        None, "--active/--inactive", help="Toggle account activation flag"
    ),
) -> None:
    """Update metadata for an existing bank account."""
    with get_db_session() as session:
        repo = BankAccountRepository(session)
        account = repo.get_by_id(account_id)
        if not account:
            console.print(f"[red]✗ Account {account_id} not found[/]")
            raise typer.Exit(1)

        try:
            if iban and iban != account.iban:
                existing = repo.get_by_iban(iban)
                if existing and existing.id != account.id:
                    console.print(
                        f"[red]✗ Another account with IBAN {iban} exists (ID {existing.id}).[/]"
                    )
                    raise typer.Exit(1)
                account.iban = iban

            if name:
                account.name = name
            if bank_name:
                account.bank_name = bank_name
            if bic:
                account.bic_swift = bic
            if currency:
                account.currency = currency.upper()
            if notes is not None:
                account.notes = notes
            if active is not None:
                account.is_active = active

            repo.update(account)
            session.commit()
            console.print(f"[green]✓ Account {account_id} updated[/]")
        except typer.Exit:
            session.rollback()
            raise
        except Exception as exc:  # pragma: no cover - defensive logging
            session.rollback()
            console.print(f"[red]✗ Failed to update account: {exc}[/]")
            raise typer.Exit(1) from exc


@app.command(name="delete-account")
def delete_account(account_id: int = typer.Argument(..., help="Account ID to delete")) -> None:
    """Delete a bank account (and related transactions)."""
    with get_db_session() as session:
        repo = BankAccountRepository(session)
        try:
            deleted = repo.delete(account_id)
            if not deleted:
                console.print(f"[yellow]⚠️  Account {account_id} not found[/]")
                raise typer.Exit(1)

            session.commit()
            console.print(f"[green]✓ Account {account_id} deleted[/]")
        except typer.Exit:
            session.rollback()
            raise
        except Exception as exc:  # pragma: no cover - defensive logging
            session.rollback()
            console.print(f"[red]✗ Failed to delete account: {exc}[/]")
            raise typer.Exit(1) from exc


# ============================================================================
# TRANSACTION COMMANDS
# ============================================================================


@app.command(name="list-transactions")
def list_transactions(
    account_id: int | None = typer.Option(None, "--account", "-a", help="Filter by account ID"),
    status: TransactionStatus | None = typer.Option(
        None, "--status", help="Filter by status (UNMATCHED|MATCHED|IGNORED)"
    ),
    limit: int | None = typer.Option(20, "--limit", "-l", help="Limit results (default: 20)"),
) -> None:
    """List imported bank transactions."""
    with get_db_session() as session:
        tx_repo = BankTransactionRepository(session)
        effective_limit = None if limit is None or limit <= 0 else limit
        transactions = tx_repo.list_transactions(
            account_id=account_id,
            status=status,
            limit=effective_limit,
        )

        if not transactions:
            console.print("[yellow]ℹ️  No transactions found for the given filters.[/]")
            return

        table = Table(title="🔍 Bank Transactions", show_lines=False)
        table.add_column("ID", style="cyan")
        table.add_column("Date", justify="center")
        table.add_column("Amount", justify="right")
        table.add_column("Status", justify="center")
        table.add_column("Account", justify="right")
        table.add_column("Payment", justify="right")
        table.add_column("Description", overflow="fold")

        for tx in transactions:
            table.add_row(
                str(tx.id),
                tx.date.strftime("%d/%m/%Y"),
                f"{tx.amount:.2f}",
                tx.status.value,
                str(tx.account_id),
                str(tx.matched_payment_id) if tx.matched_payment_id else "-",
                (tx.description or "")[:80],
            )

        console.print(table)


@app.command(name="show-transaction")
def show_transaction(transaction_id: UUID = typer.Argument(..., help="Transaction UUID")) -> None:
    """Show detailed information about a transaction."""
    with get_db_session() as session:
        tx_repo = BankTransactionRepository(session)
        transaction = tx_repo.get_by_id(transaction_id)

        if not transaction:
            console.print(f"[red]✗ Transaction {transaction_id} not found[/]")
            raise typer.Exit(1)

        table = Table(title=f"Transaction {transaction_id}", show_header=False)
        table.add_row("Account", str(transaction.account_id))
        table.add_row("Date", transaction.date.strftime("%d/%m/%Y"))
        table.add_row("Amount", f"{transaction.amount:.2f}")
        table.add_row("Status", transaction.status.value)
        table.add_row("Matched Payment", str(transaction.matched_payment_id or "-"))
        table.add_row(
            "Confidence",
            f"{transaction.match_confidence:.2%}" if transaction.match_confidence else "-",
        )
        table.add_row("Match Type", transaction.match_type.value if transaction.match_type else "-")
        table.add_row("Description", transaction.description or "-")
        table.add_row("Reference", transaction.reference or "-")
        table.add_row("Counterparty", transaction.counterparty or "-")
        table.add_row("Counterparty IBAN", transaction.counterparty_iban or "-")
        console.print(table)


# ============================================================================
# COMMAND 1: import
# ============================================================================


@app.command(name="import")
def import_transactions(
    file_path: Path = typer.Argument(..., help="Bank statement file path", exists=True),
    account_id: int = typer.Option(..., "--account", "-a", help="Bank account ID"),
    bank_preset: str | None = typer.Option(
        None, "--bank", "-b", help="Bank preset (intesa|unicredit|revolut|...)"
    ),
    auto_match: bool = typer.Option(True, "--auto-match/--no-auto-match"),
    confidence: float = typer.Option(
        0.85,
        "--confidence",
        "-c",
        min=0.0,
        max=1.0,
        help="Minimum confidence threshold for auto-matching (0.0-1.0, default: 0.85)",
    ),
) -> None:
    """📥 Import bank statement and auto-match transactions.

    Examples:
        # Import Intesa Sanpaolo with auto-matching
        openfatture payment import statement.csv --account 1 --bank intesa

        # Import without auto-matching
        openfatture payment import revolut.csv --account 2 --no-auto-match

        # Custom confidence threshold
        openfatture payment import data.ofx --account 1 --confidence 0.90
    """
    with get_db_session() as session:
        # 1. Load account
        account_repo = BankAccountRepository(session)
        account = account_repo.get_by_id(account_id)
        if not account:
            console.print(f"[red]✗ Account {account_id} not found[/]")
            raise typer.Exit(1)

        # 2. Create importer with factory
        console.print(f"[cyan]📂 Detecting format for {file_path.name}...[/]")
        factory = ImporterFactory()

        try:
            importer = factory.create_from_file(file_path, bank_preset=bank_preset)
            console.print(f"[green]✓ Format detected: {importer.__class__.__name__}[/]")
        except ValueError as e:
            console.print(f"[red]✗ {e}[/]")
            raise typer.Exit(1)

        # 3. Import with progress
        console.print("[cyan]Importing transactions...[/]")
        result = importer.import_transactions(account)

        # 4. Display results table
        table = Table(title="📊 Import Results", show_header=True)
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Count", justify="right", style="bold")

        table.add_row("✅ Success", f"[green]{result.success_count}[/]")
        table.add_row("❌ Errors", f"[red]{result.error_count}[/]")
        table.add_row("🔁 Duplicates", f"[yellow]{result.duplicate_count}[/]")
        table.add_row("━" * 20, "━" * 10)
        table.add_row("📈 Total", f"[bold]{result.total_count}[/]")

        console.print(table)

        # 5. Show errors if any
        if result.errors:
            console.print("\n[red]Errors:[/]")
            for error in result.errors[:5]:  # Show first 5
                console.print(f"  • {error}")

        # 6. Auto-match if enabled
        if auto_match and result.success_count > 0:
            console.print(f"\n[cyan]🔍 Auto-matching with confidence >= {confidence}...[/]")

            # Initialize services
            matching_service = _build_matching_service(
                session,
                strategies=[ExactAmountMatcher(), CompositeMatcher()],
            )
            event_bus = create_event_bus()

            reconciliation_service = ReconciliationService(
                BankTransactionRepository(session),
                PaymentRepository(session),
                matching_service,
                session,
                event_bus=event_bus,
            )

            # Batch reconcile
            recon_result = run_async(
                reconciliation_service.reconcile_batch(
                    account_id, auto_apply=True, auto_apply_threshold=confidence
                )
            )

            # Display reconciliation results
            console.print("\n[bold]Reconciliation Results:[/]")
            console.print(f"  [green]✅ Matched: {recon_result.matched_count}[/]")
            console.print(f"  [yellow]⏳ Review needed: {recon_result.review_count}[/]")
            console.print(f"  [dim]❔ Unmatched: {recon_result.unmatched_count}[/]")

            if recon_result.review_count > 0:
                console.print(
                    "\n[yellow]💡 Tip: Run 'openfatture payment queue' to review medium-confidence matches[/]"
                )


# ============================================================================
# COMMAND 2: match
# ============================================================================


@app.command()
def match(
    account_id: int | None = typer.Option(None, "--account", "-a", help="Filter by account"),
    confidence: float = typer.Option(0.60, "--confidence", "-c", min=0.0, max=1.0),
    auto_apply: bool = typer.Option(True, "--auto-apply/--manual-only"),
    limit: int | None = typer.Option(None, "--limit", "-l", help="Max transactions to match"),
) -> None:
    """🔍 Match unmatched transactions to payments.

    Examples:
        # Match all unmatched with auto-apply
        openfatture payment match --auto-apply

        # Match with custom confidence
        openfatture payment match --confidence 0.75

        # Match specific account
        openfatture payment match --account 1 --limit 50
    """
    with get_db_session() as session:
        tx_repo = BankTransactionRepository(session)
        matching_service = _build_matching_service(
            session,
            strategies=[ExactAmountMatcher(), CompositeMatcher()],
        )

        event_bus = create_event_bus()

        reconciliation_service = ReconciliationService(
            tx_repo,
            PaymentRepository(session),
            matching_service,
            session,
            event_bus=event_bus,
        )

        # Get unmatched transactions
        unmatched = tx_repo.get_by_status(
            TransactionStatus.UNMATCHED, account_id=account_id, limit=limit
        )

        if not unmatched:
            console.print("[green]✅ No unmatched transactions[/]")
            return

        console.print(f"[cyan]🔍 Matching {len(unmatched)} transactions...[/]")

        matched_count = 0
        review_count = 0

        for tx in track(unmatched, description="Matching..."):
            matches = _run(matching_service.match_transaction(tx, confidence))

            if not matches:
                continue

            top_match = matches[0]

            if auto_apply and top_match.should_auto_apply:
                # Auto-reconcile
                _run(
                    reconciliation_service.reconcile(
                        tx.id, top_match.payment.id, top_match.match_type, top_match.confidence
                    )
                )
                matched_count += 1
            else:
                review_count += 1

        # Results
        console.print("\n[bold]Results:[/]")
        console.print(f"  [green]✅ Matched: {matched_count}[/]")
        console.print(f"  [yellow]⏳ Review needed: {review_count}[/]")


# ============================================================================
# COMMAND 3: reconcile (batch)
# ============================================================================


@app.command(name="reconcile")
def reconcile(
    account_id: int = typer.Option(..., "--account", "-a", help="Bank account to reconcile"),
    mode: str = typer.Option(
        "auto",
        "--mode",
        "-m",
        help="Reconciliation mode: 'auto' applies matches, 'preview' only reports",
    ),
    confidence: float = typer.Option(0.85, "--confidence", "-c", min=0.0, max=1.0),
) -> None:
    """Run batch reconciliation for an account."""

    mode_normalized = mode.lower().strip()
    if mode_normalized not in {"auto", "preview"}:
        console.print("[red]✗ Invalid mode. Use 'auto' or 'preview'.[/]")
        raise typer.Exit(1)

    with get_db_session() as session:
        matching_service = _build_matching_service(
            session,
            strategies=[ExactAmountMatcher(), CompositeMatcher()],
        )
        event_bus = create_event_bus()
        reconciliation_service = ReconciliationService(
            BankTransactionRepository(session),
            PaymentRepository(session),
            matching_service,
            session,
            event_bus=event_bus,
        )

        try:
            result = _run(
                reconciliation_service.reconcile_batch(
                    account_id=account_id,
                    auto_apply=mode_normalized == "auto",
                    auto_apply_threshold=confidence,
                )
            )

            if mode_normalized == "auto":
                session.commit()
            else:
                session.rollback()

            summary = Table(title="🤝 Reconciliation Summary", show_header=True)
            summary.add_column("Metric", style="cyan")
            summary.add_column("Value", justify="right")
            summary.add_row("Processed", str(result.total_count))
            summary.add_row("Matched", str(result.matched_count))
            summary.add_row("Needs review", str(result.review_count))
            summary.add_row("Unmatched", str(result.unmatched_count))
            summary.add_row("Match rate", f"{result.match_rate:.1%}")
            console.print(summary)

            if result.errors:
                console.print("\n[red]Errors during reconciliation:[/]")
                for err in result.errors:
                    console.print(f"  • {err}")

            if mode_normalized == "preview" and result.matches:
                preview_table = Table(title="Suggested Matches (top results)")
                preview_table.add_column("Transaction")
                preview_table.add_column("Payment")
                preview_table.add_column("Confidence", justify="right")
                preview_table.add_column("Reason")

                for tx, matches in result.matches[:10]:
                    if not matches:
                        continue
                    top = matches[0]
                    preview_table.add_row(
                        str(tx.id),
                        str(top.payment.id),
                        f"{top.confidence:.1%}",
                        top.match_reason[:60],
                    )

                console.print(preview_table)

        except Exception as exc:  # pragma: no cover - defensive logging
            session.rollback()
            console.print(f"[red]✗ Reconciliation failed: {exc}[/]")
            raise typer.Exit(1) from exc


# ============================================================================
# COMMAND 4: queue (Interactive Review)
# ============================================================================


@app.command()
def queue(
    account_id: int | None = typer.Option(None, "--account", "-a"),
    interactive: bool = typer.Option(True, "--interactive/--list-only"),
    confidence_min: float = typer.Option(0.60, "--min", min=0.0, max=1.0),
    confidence_max: float = typer.Option(0.84, "--max", min=0.0, max=1.0),
) -> None:
    """📋 Review queue for manual reconciliation.

    Interactive mode allows approving/ignoring matches one by one.

    Examples:
        # Interactive review
        openfatture payment queue --interactive

        # List only (no interaction)
        openfatture payment queue --list-only

        # Custom confidence range
        openfatture payment queue --min 0.50 --max 0.90
    """
    with get_db_session() as session:
        matching_service = _build_matching_service(
            session,
            strategies=[ExactAmountMatcher(), CompositeMatcher()],
        )

        event_bus = create_event_bus()

        reconciliation_service = ReconciliationService(
            BankTransactionRepository(session),
            PaymentRepository(session),
            matching_service,
            session,
            event_bus=event_bus,
        )

        # Get review queue
        review_queue = _run(
            reconciliation_service.get_review_queue(
                account_id, confidence_range=(confidence_min, confidence_max)
            )
        )

        if not review_queue:
            console.print("[green]✅ No transactions need review[/]")
            return

        if interactive:
            # Interactive mode
            console.print(f"[bold cyan]📋 Review Queue: {len(review_queue)} transactions[/]\n")

            for i, (tx, matches) in enumerate(review_queue, 1):
                console.print(f"[bold]Transaction {i}/{len(review_queue)}[/]")
                console.print(f"  Date: {tx.date.strftime('%d/%m/%Y')}")
                console.print(f"  Amount: [green]€{tx.amount}[/]")
                console.print(f"  Description: {tx.description}")

                # Suggestions table
                table = Table(title="💡 Suggested Matches", show_header=True)
                table.add_column("#", style="cyan", width=3)
                table.add_column("Invoice", style="yellow")
                table.add_column("Confidence", justify="right", style="green")
                table.add_column("Reason", style="dim")

                for j, match in enumerate(matches[:5], 1):
                    invoice_num = (
                        match.payment.fattura.numero
                        if hasattr(match.payment, "fattura")
                        else f"#{match.payment.id}"
                    )
                    table.add_row(
                        str(j), invoice_num, f"{match.confidence:.1%}", match.match_reason[:40]
                    )

                console.print(table)

                # Prompt action
                action = Prompt.ask(
                    "\n[bold]Action[/]",
                    choices=["approve", "ignore", "skip", "quit"],
                    default="skip",
                )

                if action == "approve" and matches:
                    _run(
                        reconciliation_service.reconcile(
                            tx.id, matches[0].payment.id, MatchType.MANUAL
                        )
                    )
                    console.print("[green]✅ Reconciled[/]\n")

                elif action == "ignore":
                    reason = Prompt.ask("Reason (optional)", default="")
                    _run(reconciliation_service.ignore_transaction(tx.id, reason))
                    console.print("[yellow]⏭️  Ignored[/]\n")

                elif action == "quit":
                    break
                else:
                    console.print("[dim]⏩ Skipped[/]\n")

        else:
            # List-only mode
            table = Table(title=f"📋 Review Queue ({len(review_queue)} items)")
            table.add_column("Date", style="cyan")
            table.add_column("Amount", justify="right", style="green")
            table.add_column("Description", style="yellow")
            table.add_column("Top Match", style="dim")
            table.add_column("Conf.", justify="right")

            for tx, matches in review_queue:
                top_match = matches[0] if matches else None
                invoice_num = (
                    f"Invoice {top_match.payment.fattura.numero}"
                    if top_match and hasattr(top_match.payment, "fattura")
                    else "-"
                )
                table.add_row(
                    tx.date.strftime("%d/%m/%Y"),
                    f"€{tx.amount}",
                    tx.description[:40],
                    invoice_num,
                    f"{top_match.confidence:.1%}" if top_match else "-",
                )

            console.print(table)


# ============================================================================
# COMMAND 5: match single transaction
# ============================================================================


@app.command(name="match-transaction")
def match_transaction(
    transaction_id: UUID = typer.Argument(..., help="Transaction UUID to reconcile"),
    payment_id: int = typer.Argument(..., help="Payment ID to match to"),
    match_type: MatchType = typer.Option(
        MatchType.MANUAL,
        "--match-type",
        "-t",
        help="Match type to record",
        case_sensitive=False,
    ),
    confidence: float | None = typer.Option(
        None, "--confidence", "-c", help="Optional confidence score (0.0-1.0)"
    ),
) -> None:
    """Manually match a transaction to a payment."""
    with get_db_session() as session:
        matching_service = _build_matching_service(
            session,
            strategies=[ExactAmountMatcher(), CompositeMatcher()],
        )
        event_bus = create_event_bus()
        reconciliation_service = ReconciliationService(
            BankTransactionRepository(session),
            PaymentRepository(session),
            matching_service,
            session,
            event_bus=event_bus,
        )

        try:
            tx = _run(
                reconciliation_service.reconcile(
                    transaction_id=transaction_id,
                    payment_id=payment_id,
                    match_type=match_type,
                    confidence=confidence,
                )
            )
            session.commit()
            console.print(
                f"[green]✓ Transaction {transaction_id} matched to payment {payment_id} ({match_type.value})[/]"
            )
            if tx.match_confidence is not None:
                console.print(f"  Confidence: {tx.match_confidence:.2%}")
        except ValueError as exc:
            session.rollback()
            console.print(f"[red]✗ {exc}[/]")
            raise typer.Exit(1) from exc
        except Exception as exc:  # pragma: no cover - defensive logging
            session.rollback()
            console.print(f"[red]✗ Failed to match transaction: {exc}[/]")
            raise typer.Exit(1) from exc


@app.command(name="unmatch-transaction")
def unmatch_transaction(
    transaction_id: UUID = typer.Argument(..., help="Transaction UUID to reset"),
) -> None:
    """Undo a previous reconciliation for a transaction."""

    with get_db_session() as session:
        matching_service = _build_matching_service(
            session,
            strategies=[ExactAmountMatcher(), CompositeMatcher()],
        )
        event_bus = create_event_bus()
        reconciliation_service = ReconciliationService(
            BankTransactionRepository(session),
            PaymentRepository(session),
            matching_service,
            session,
            event_bus=event_bus,
        )

        try:
            _run(reconciliation_service.reset_transaction(transaction_id))
            session.commit()
            console.print(f"[green]✓ Transaction {transaction_id} reset to UNMATCHED[/]")
        except ValueError as exc:
            session.rollback()
            console.print(f"[red]✗ {exc}[/]")
            raise typer.Exit(1) from exc
        except Exception as exc:  # pragma: no cover - defensive logging
            session.rollback()
            console.print(f"[red]✗ Failed to reset transaction: {exc}[/]")
            raise typer.Exit(1) from exc


# ============================================================================
# COMMAND 6: schedule-reminders
# ============================================================================


@app.command(name="schedule-reminders")
def schedule_reminders(
    payment_id: int = typer.Argument(..., help="Payment ID"),
    strategy: str = typer.Option(
        "default", "--strategy", "-s", help="Reminder strategy: default|aggressive|gentle|minimal"
    ),
) -> None:
    """⏰ Schedule payment reminders.

    Strategies:
        - default: [-7, -3, 0, 7, 30] days
        - aggressive: [-10, -7, -3, -1, 0, 3, 7, 15, 30] days
        - gentle: [-7, 0, 15, 30] days
        - minimal: [0, 30] days

    Examples:
        openfatture payment schedule-reminders 123
        openfatture payment schedule-reminders 124 --strategy aggressive
    """
    strategy_map = {
        "default": ReminderStrategy.DEFAULT,
        "aggressive": ReminderStrategy.AGGRESSIVE,
        "gentle": ReminderStrategy.GENTLE,
        "minimal": ReminderStrategy.MINIMAL,
    }

    if strategy not in strategy_map:
        console.print(f"[red]Invalid strategy: {strategy}[/]")
        console.print("Available: default, aggressive, gentle, minimal")
        raise typer.Exit(1)

    with get_db_session() as session:
        # Initialize scheduler
        notifier = ConsoleNotifier()  # Or EmailNotifier with SMTP config
        scheduler = ReminderScheduler(
            ReminderRepository(session), PaymentRepository(session), notifier
        )

        try:
            reminders = _run(scheduler.schedule_reminders(payment_id, strategy_map[strategy]))

            console.print(f"\n[green]✅ Scheduled {len(reminders)} reminders[/]")

            # Display schedule
            table = Table(title="📅 Reminder Schedule")
            table.add_column("Date", style="cyan")
            table.add_column("Days to Due", justify="right", style="yellow")
            table.add_column("Status", style="dim")

            for reminder in reminders:
                payment = getattr(reminder, "payment", None)
                due_date = getattr(payment, "data_scadenza", None) if payment is not None else None
                reminder_date = getattr(reminder, "reminder_date", None)

                days_until_due: int | None
                if isinstance(due_date, date) and isinstance(reminder_date, date):
                    days_until_due = (due_date - reminder_date).days
                else:
                    days_until_due = getattr(reminder, "days_before_due", None)

                if days_until_due is None:
                    status = "❔ Unknown"
                elif days_until_due > 0:
                    status = "⏰ Before due"
                elif days_until_due == 0:
                    status = "📅 Due today"
                else:
                    status = "❗ After due"

                table.add_row(
                    getattr(reminder, "reminder_date", date.today()).strftime("%d/%m/%Y"),
                    str(days_until_due) if days_until_due is not None else "-",
                    status,
                )

            console.print(table)

        except ValueError as e:
            console.print(f"[red]Error: {e}[/]")
            raise typer.Exit(1)


# ============================================================================
# COMMAND 7: process-reminders
# ============================================================================


@app.command(name="process-reminders")
def process_reminders(
    target_date: str | None = typer.Option(
        None, "--date", help="Date to process (YYYY-MM-DD), default: today"
    ),
) -> None:
    """📧 Process due reminders (background job).

    Run this daily via cron to send reminders.

    Examples:
        # Process today's reminders
        openfatture payment process-reminders

        # Process specific date
        openfatture payment process-reminders --date 2024-12-25
    """
    process_date = (
        datetime.strptime(target_date, "%Y-%m-%d").date() if target_date else date.today()
    )

    with get_db_session() as session:
        # Email notifier (requires SMTP config)
        smtp_config = SMTPConfig(
            host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            port=int(os.getenv("SMTP_PORT", 587)),
            username=os.getenv("SMTP_USER", ""),
            password=os.getenv("SMTP_PASSWORD", ""),
            from_email=os.getenv("SMTP_FROM", "noreply@openfatture.com"),
        )

        notifier = EmailNotifier(smtp_config) if os.getenv("SMTP_HOST") else ConsoleNotifier()
        scheduler = ReminderScheduler(
            ReminderRepository(session), PaymentRepository(session), notifier
        )

        console.print(
            f"[cyan]📧 Processing reminders for {process_date.strftime('%d/%m/%Y')}...[/]"
        )

        count = _run(scheduler.process_due_reminders(process_date))

        console.print(f"\n[green]✅ Sent {count} reminders[/]")


# ============================================================================
# COMMAND 8: list reminders
# ============================================================================


@app.command(name="list-reminders")
def list_reminders(
    status: ReminderStatus | None = typer.Option(
        None,
        "--status",
        help="Filter by status (PENDING|SENT|FAILED|CANCELLED)",
        case_sensitive=False,
    ),
    payment_id: int | None = typer.Option(None, "--payment", help="Filter by payment ID"),
    limit: int | None = typer.Option(50, "--limit", "-l", help="Limit results (default: 50)"),
) -> None:
    """List scheduled payment reminders."""

    with get_db_session() as session:
        repo = ReminderRepository(session)
        effective_limit = None if limit is None or limit <= 0 else limit
        reminders = repo.list_reminders(status=status, payment_id=payment_id, limit=effective_limit)

        if not reminders:
            console.print("[yellow]ℹ️  No reminders found for the given filters.[/]")
            return

        table = Table(title="📬 Payment Reminders")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Payment", justify="right")
        table.add_column("Date", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Strategy", justify="center")
        table.add_column("Days", justify="right")
        table.add_column("Sent", justify="center")
        table.add_column("Notes", overflow="fold")

        for reminder in reminders:
            due_date = getattr(reminder.payment, "data_scadenza", None)
            table.add_row(
                str(reminder.id),
                str(reminder.payment_id),
                reminder.reminder_date.strftime("%d/%m/%Y"),
                reminder.status.value,
                reminder.strategy.value,
                str(reminder.days_before_due),
                reminder.sent_date.strftime("%d/%m/%Y") if reminder.sent_date else "-",
                f"Due: {due_date.strftime('%d/%m/%Y')}" if due_date else "-",
            )

        console.print(table)


@app.command(name="cancel-reminder")
def cancel_reminder(reminder_id: int = typer.Argument(..., help="Reminder ID to cancel")) -> None:
    """Cancel a scheduled reminder if it hasn't been sent yet."""

    with get_db_session() as session:
        repo = ReminderRepository(session)
        reminder = repo.get_by_id(reminder_id)
        if not reminder:
            console.print(f"[red]✗ Reminder {reminder_id} not found[/]")
            raise typer.Exit(1)

        if reminder.status == ReminderStatus.SENT:
            console.print(f"[yellow]⚠️  Reminder {reminder_id} already sent; cannot cancel.[/]")
            raise typer.Exit(1)

        reminder.cancel()
        repo.update(reminder)
        session.commit()

        console.print(f"[green]✓ Reminder {reminder_id} cancelled[/]")


# ============================================================================
# COMMAND 8: audit
# ============================================================================


@app.command()
def audit(
    limit: int = typer.Option(50, "--limit", "-n", help="Number of records to show"),
    account_id: int | None = typer.Option(None, "--account", "-a", help="Filter by account"),
    payment_id: int | None = typer.Option(None, "--payment", "-p", help="Filter by payment ID"),
    transaction_id: str | None = typer.Option(
        None, "--transaction", "-t", help="Filter by transaction ID"
    ),
) -> None:
    """📋 Payment allocation audit trail.

    Shows the history of payment allocations with confidence scores,
    match types, and timestamps for auditing and troubleshooting.

    Examples:
        # Recent allocations
        openfatture payment audit

        # Account-specific
        openfatture payment audit --account 1

        # Payment-specific
        openfatture payment audit --payment 123

        # Transaction-specific
        openfatture payment audit --transaction "550e8400-e29b-41d4-a716-446655440000"
    """
    with get_db_session() as session:
        from sqlalchemy import select

        from ..domain.payment_allocation import PaymentAllocation

        # Build query
        query = (
            select(PaymentAllocation).order_by(PaymentAllocation.allocated_at.desc()).limit(limit)
        )

        if payment_id:
            query = query.where(PaymentAllocation.payment_id == payment_id)
        if transaction_id:
            try:
                tx_uuid = UUID(transaction_id)
                query = query.where(PaymentAllocation.transaction_id == tx_uuid)
            except ValueError:
                console.print(f"[red]❌ Invalid transaction ID format: {transaction_id}[/]")
                raise typer.Exit(1)

        # Execute query
        result = session.execute(query)
        allocations = result.scalars().all()

        if not allocations:
            console.print("[dim]No payment allocations found matching the criteria.[/]")
            return

        # Display table
        table = Table(title=f"💰 Payment Allocation Audit Trail (Last {len(allocations)} records)")
        table.add_column("ID", style="dim")
        table.add_column("Payment", style="cyan")
        table.add_column("Transaction", style="magenta")
        table.add_column("Amount", style="green", justify="right")
        table.add_column("Match Type", style="yellow")
        table.add_column("Confidence", style="blue")
        table.add_column("Allocated At", style="dim")
        table.add_column("Notes", style="dim")

        for alloc in allocations:
            confidence = f"{alloc.match_confidence:.2f}" if alloc.match_confidence else "N/A"
            notes = (
                alloc.notes[:30] + "..."
                if alloc.notes and len(alloc.notes) > 30
                else alloc.notes or ""
            )

            table.add_row(
                str(alloc.id),
                f"#{alloc.payment_id}",
                str(alloc.transaction_id)[:8] + "...",
                f"€{alloc.amount}",
                alloc.match_type.value if alloc.match_type else "manual",
                confidence,
                alloc.allocated_at.strftime("%Y-%m-%d %H:%M"),
                notes,
            )

        console.print(table)

        # Summary
        total_amount = sum(alloc.amount for alloc in allocations)
        console.print(f"\n[dim]Total allocated: €{total_amount}[/]")


# ============================================================================
# COMMAND 9: stats
# ============================================================================


@app.command()
def stats(
    account_id: int | None = typer.Option(None, "--account", "-a", help="Filter by account"),
) -> None:
    """📊 Payment tracking statistics.

    Examples:
        # Global stats
        openfatture payment stats

        # Account-specific
        openfatture payment stats --account 1
    """
    with get_db_session() as session:
        tx_repo = BankTransactionRepository(session)

        # Get counts by status
        unmatched = len(tx_repo.get_by_status(TransactionStatus.UNMATCHED, account_id))
        matched = len(tx_repo.get_by_status(TransactionStatus.MATCHED, account_id))
        ignored = len(tx_repo.get_by_status(TransactionStatus.IGNORED, account_id))

        # Display table
        table = Table(title="📊 Payment Tracking Statistics")
        table.add_column("Status", style="bold")
        table.add_column("Count", justify="right", style="cyan")
        table.add_column("Percentage", justify="right", style="dim")

        total = unmatched + matched + ignored

        table.add_row(
            "🔍 Unmatched", str(unmatched), f"{unmatched / total * 100:.1f}%" if total else "-"
        )
        table.add_row("✅ Matched", str(matched), f"{matched / total * 100:.1f}%" if total else "-")
        table.add_row("⏭️  Ignored", str(ignored), f"{ignored / total * 100:.1f}%" if total else "-")
        table.add_row("━" * 15, "━" * 8, "━" * 12)
        table.add_row("[bold]Total", f"[bold]{total}", "100%" if total else "-")

        console.print(table)


if __name__ == "__main__":
    app()
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_transaction_insight_service() -> TransactionInsightService | None:
    """Lazily initialize AI insight service (optional)."""
    global _INSIGHT_SERVICE, _INSIGHT_INITIALIZED

    if _INSIGHT_INITIALIZED:
        return _INSIGHT_SERVICE

    _INSIGHT_INITIALIZED = True

    try:
        provider = create_provider()
        agent = PaymentInsightAgent(provider=provider)
        _INSIGHT_SERVICE = TransactionInsightService(agent=agent)
        logger.info(
            "payment_cli_ai_insight_enabled",
            provider=provider.provider_name,
            model=provider.model,
        )
        console.print(
            "[dim green]🤖 AI payment insight abilitato per analizzare causali e pagamenti parziali[/]"
        )
    except ProviderError as exc:
        logger.info(
            "payment_cli_ai_insight_disabled",
            reason=str(exc),
            provider=exc.provider,
        )
        console.print(
            "[dim yellow]⚠️  AI insight non disponibile (configura le credenziali OPENFATTURE_AI_* per abilitarlo)[/]"
        )
        _INSIGHT_SERVICE = None
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning(
            "payment_cli_ai_insight_error",
            error=str(exc),
            error_type=type(exc).__name__,
        )
        console.print(f"[dim yellow]⚠️  Impossibile inizializzare l'AI insight: {exc}[/]")
        _INSIGHT_SERVICE = None

    return _INSIGHT_SERVICE


def _build_matching_service(
    session: Session,
    *,
    strategies: Sequence[IMatcherStrategy] | None = None,
) -> MatchingService:
    """Factory to create MatchingService with optional AI insight."""
    strategy_list: list[IMatcherStrategy] = (
        list(strategies) if strategies is not None else [ExactAmountMatcher(), CompositeMatcher()]
    )
    tx_repo = BankTransactionRepository(session)
    payment_repo = PaymentRepository(session)
    insight_service = _get_transaction_insight_service()

    return MatchingService(
        tx_repo=tx_repo,
        payment_repo=payment_repo,
        strategies=strategy_list,
        insight_service=insight_service,
    )
