"""Audit trail and statistics commands."""

from uuid import UUID

import typer
from rich.table import Table

from ..domain.enums import TransactionStatus
from ..infrastructure.repository import BankTransactionRepository
from ._app import app, console, get_db_session


@app.command()
def audit(
    limit: int = typer.Option(50, "--limit", "-n", help="Number of records to show"),
    account_id: int | None = typer.Option(None, "--account", "-a", help="Filter by account"),
    payment_id: int | None = typer.Option(None, "--payment", "-p", help="Filter by payment ID"),
    transaction_id: str | None = typer.Option(
        None, "--transaction", "-t", help="Filter by transaction ID"
    ),
) -> None:
    """Payment allocation audit trail.

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
                console.print(f"[red]Invalid transaction ID format: {transaction_id}[/]")
                raise typer.Exit(1)

        # Execute query
        result = session.execute(query)
        allocations = result.scalars().all()

        if not allocations:
            console.print("[dim]No payment allocations found matching the criteria.[/]")
            return

        # Display table
        table = Table(title=f"Payment Allocation Audit Trail (Last {len(allocations)} records)")
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


@app.command()
def stats(
    account_id: int | None = typer.Option(None, "--account", "-a", help="Filter by account"),
) -> None:
    """Payment tracking statistics.

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
        table = Table(title="Payment Tracking Statistics")
        table.add_column("Status", style="bold")
        table.add_column("Count", justify="right", style="cyan")
        table.add_column("Percentage", justify="right", style="dim")

        total = unmatched + matched + ignored

        table.add_row(
            "Unmatched", str(unmatched), f"{unmatched / total * 100:.1f}%" if total else "-"
        )
        table.add_row("Matched", str(matched), f"{matched / total * 100:.1f}%" if total else "-")
        table.add_row("Ignored", str(ignored), f"{ignored / total * 100:.1f}%" if total else "-")
        table.add_row("━" * 15, "━" * 8, "━" * 12)
        table.add_row("[bold]Total", f"[bold]{total}", "100%" if total else "-")

        console.print(table)
