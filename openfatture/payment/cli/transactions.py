"""Bank transaction listing, detail, and import commands."""

from pathlib import Path
from uuid import UUID

import typer
from rich.table import Table

from ...utils.async_bridge import run_async
from ..application import create_event_bus
from ..application.services import ReconciliationService
from ..domain.enums import TransactionStatus
from ..infrastructure.importers import ImporterFactory
from ..infrastructure.repository import (
    BankAccountRepository,
    BankTransactionRepository,
    PaymentRepository,
)
from ..matchers import CompositeMatcher, ExactAmountMatcher
from ._app import _build_matching_service, app, console, get_db_session


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
