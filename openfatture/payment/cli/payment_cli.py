"""Payment tracking CLI commands.

Provides interactive commands for bank statement import, transaction matching,
reconciliation, and payment reminders.
"""

import asyncio
import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

import typer
from rich.console import Console
from rich.progress import Progress, track
from rich.prompt import Confirm, Prompt
from rich.table import Table
from sqlalchemy.orm import Session

from ...storage.database import get_db
from ..application.notifications import ConsoleNotifier, EmailNotifier, SMTPConfig
from ..application.services import (
    MatchingService,
    ReconciliationService,
    ReminderRepository,
    ReminderScheduler,
)
from ..domain.enums import MatchType, ReminderStrategy, TransactionStatus
from ..infrastructure.importers import ImporterFactory
from ..infrastructure.repository import (
    BankAccountRepository,
    BankTransactionRepository,
    PaymentRepository,
)
from ..matchers import CompositeMatcher, ExactAmountMatcher

app = typer.Typer(name="payment", help="💰 Payment tracking & reconciliation")
console = Console()


def get_db_session():
    """Get database session from context."""
    # This will be provided by the main CLI context
    return next(get_db())


# ============================================================================
# COMMAND 1: import
# ============================================================================


@app.command()
def import_statement(
    file_path: Path = typer.Argument(..., help="Bank statement file path", exists=True),
    account_id: int = typer.Option(..., "--account", "-a", help="Bank account ID"),
    bank_preset: Optional[str] = typer.Option(
        None, "--bank", "-b", help="Bank preset (intesa|unicredit|revolut|...)"
    ),
    auto_match: bool = typer.Option(True, "--auto-match/--no-auto-match"),
    confidence: float = typer.Option(0.85, "--confidence", "-c", min=0.0, max=1.0),
):
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
        console.print(f"[cyan]Importing transactions...[/]")
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
            matching_service = MatchingService(
                BankTransactionRepository(session),
                PaymentRepository(session),
                strategies=[ExactAmountMatcher(), CompositeMatcher()],
            )

            reconciliation_service = ReconciliationService(
                BankTransactionRepository(session),
                PaymentRepository(session),
                matching_service,
                session,
            )

            # Batch reconcile
            loop = asyncio.get_event_loop()
            recon_result = loop.run_until_complete(
                reconciliation_service.reconcile_batch(
                    account_id, auto_apply=True, auto_apply_threshold=confidence
                )
            )

            # Display reconciliation results
            console.print(f"\n[bold]Reconciliation Results:[/]")
            console.print(f"  [green]✅ Matched: {recon_result.matched_count}[/]")
            console.print(f"  [yellow]⏳ Review needed: {recon_result.review_count}[/]")
            console.print(f"  [dim]❔ Unmatched: {recon_result.unmatched_count}[/]")

            if recon_result.review_count > 0:
                console.print(
                    f"\n[yellow]💡 Tip: Run 'openfatture payment queue' to review medium-confidence matches[/]"
                )


# ============================================================================
# COMMAND 2: match
# ============================================================================


@app.command()
def match(
    account_id: Optional[int] = typer.Option(None, "--account", "-a", help="Filter by account"),
    confidence: float = typer.Option(0.60, "--confidence", "-c", min=0.0, max=1.0),
    auto_apply: bool = typer.Option(True, "--auto-apply/--manual-only"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Max transactions to match"),
):
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
        matching_service = MatchingService(
            tx_repo,
            PaymentRepository(session),
            strategies=[ExactAmountMatcher(), CompositeMatcher()],
        )

        reconciliation_service = ReconciliationService(
            tx_repo, PaymentRepository(session), matching_service, session
        )

        # Get unmatched transactions
        unmatched = tx_repo.get_by_status(TransactionStatus.UNMATCHED, account_id=account_id, limit=limit)

        if not unmatched:
            console.print("[green]✅ No unmatched transactions[/]")
            return

        console.print(f"[cyan]🔍 Matching {len(unmatched)} transactions...[/]")

        matched_count = 0
        review_count = 0

        loop = asyncio.get_event_loop()

        for tx in track(unmatched, description="Matching..."):
            matches = loop.run_until_complete(matching_service.match_transaction(tx, confidence))

            if not matches:
                continue

            top_match = matches[0]

            if auto_apply and top_match.should_auto_apply:
                # Auto-reconcile
                loop.run_until_complete(
                    reconciliation_service.reconcile(
                        tx.id, top_match.payment.id, top_match.match_type, top_match.confidence
                    )
                )
                matched_count += 1
            else:
                review_count += 1

        # Results
        console.print(f"\n[bold]Results:[/]")
        console.print(f"  [green]✅ Matched: {matched_count}[/]")
        console.print(f"  [yellow]⏳ Review needed: {review_count}[/]")


# ============================================================================
# COMMAND 3: queue (Interactive Review)
# ============================================================================


@app.command()
def queue(
    account_id: Optional[int] = typer.Option(None, "--account", "-a"),
    interactive: bool = typer.Option(True, "--interactive/--list-only"),
    confidence_min: float = typer.Option(0.60, "--min", min=0.0, max=1.0),
    confidence_max: float = typer.Option(0.84, "--max", min=0.0, max=1.0),
):
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
        matching_service = MatchingService(
            BankTransactionRepository(session),
            PaymentRepository(session),
            strategies=[ExactAmountMatcher(), CompositeMatcher()],
        )

        reconciliation_service = ReconciliationService(
            BankTransactionRepository(session),
            PaymentRepository(session),
            matching_service,
            session,
        )

        # Get review queue
        loop = asyncio.get_event_loop()
        review_queue = loop.run_until_complete(
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
                    table.add_row(str(j), invoice_num, f"{match.confidence:.1%}", match.match_reason[:40])

                console.print(table)

                # Prompt action
                action = Prompt.ask(
                    "\n[bold]Action[/]", choices=["approve", "ignore", "skip", "quit"], default="skip"
                )

                if action == "approve" and matches:
                    loop.run_until_complete(
                        reconciliation_service.reconcile(tx.id, matches[0].payment.id, MatchType.MANUAL)
                    )
                    console.print("[green]✅ Reconciled[/]\n")

                elif action == "ignore":
                    reason = Prompt.ask("Reason (optional)", default="")
                    loop.run_until_complete(reconciliation_service.ignore_transaction(tx.id, reason))
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
# COMMAND 4: schedule-reminders
# ============================================================================


@app.command(name="schedule-reminders")
def schedule_reminders(
    payment_id: int = typer.Argument(..., help="Payment ID"),
    strategy: str = typer.Option(
        "default", "--strategy", "-s", help="Reminder strategy: default|aggressive|gentle|minimal"
    ),
):
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
            loop = asyncio.get_event_loop()
            reminders = loop.run_until_complete(scheduler.schedule_reminders(payment_id, strategy_map[strategy]))

            console.print(f"\n[green]✅ Scheduled {len(reminders)} reminders[/]")

            # Display schedule
            table = Table(title="📅 Reminder Schedule")
            table.add_column("Date", style="cyan")
            table.add_column("Days to Due", justify="right", style="yellow")
            table.add_column("Status", style="dim")

            for reminder in reminders:
                status = "⏰ Before due" if reminder.days_before_due > 0 else "❗ After due"
                table.add_row(reminder.scheduled_date.strftime("%d/%m/%Y"), str(reminder.days_before_due), status)

            console.print(table)

        except ValueError as e:
            console.print(f"[red]Error: {e}[/]")
            raise typer.Exit(1)


# ============================================================================
# COMMAND 5: process-reminders
# ============================================================================


@app.command(name="process-reminders")
def process_reminders(
    target_date: Optional[str] = typer.Option(None, "--date", help="Date to process (YYYY-MM-DD), default: today"),
):
    """📧 Process due reminders (background job).

    Run this daily via cron to send reminders.

    Examples:
        # Process today's reminders
        openfatture payment process-reminders

        # Process specific date
        openfatture payment process-reminders --date 2024-12-25
    """
    process_date = datetime.strptime(target_date, "%Y-%m-%d").date() if target_date else date.today()

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
        scheduler = ReminderScheduler(ReminderRepository(session), PaymentRepository(session), notifier)

        console.print(f"[cyan]📧 Processing reminders for {process_date.strftime('%d/%m/%Y')}...[/]")

        loop = asyncio.get_event_loop()
        count = loop.run_until_complete(scheduler.process_due_reminders(process_date))

        console.print(f"\n[green]✅ Sent {count} reminders[/]")


# ============================================================================
# COMMAND 6: stats
# ============================================================================


@app.command()
def stats(
    account_id: Optional[int] = typer.Option(None, "--account", "-a", help="Filter by account"),
):
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
            "🔍 Unmatched", str(unmatched), f"{unmatched/total*100:.1f}%" if total else "-"
        )
        table.add_row("✅ Matched", str(matched), f"{matched/total*100:.1f}%" if total else "-")
        table.add_row("⏭️  Ignored", str(ignored), f"{ignored/total*100:.1f}%" if total else "-")
        table.add_row("━" * 15, "━" * 8, "━" * 12)
        table.add_row("[bold]Total", f"[bold]{total}", "100%" if total else "-")

        console.print(table)


if __name__ == "__main__":
    app()
