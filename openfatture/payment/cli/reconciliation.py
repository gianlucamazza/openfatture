"""Transaction matching and reconciliation commands."""

from uuid import UUID

import typer
from rich.progress import track
from rich.prompt import Prompt
from rich.table import Table

from ..application import create_event_bus
from ..application.services import ReconciliationService
from ..domain.enums import MatchType, TransactionStatus
from ..infrastructure.repository import (
    BankTransactionRepository,
    PaymentRepository,
)
from ..matchers import CompositeMatcher, ExactAmountMatcher
from ._app import _build_matching_service, _run, app, console, get_db_session


@app.command()
def match(
    account_id: int | None = typer.Option(None, "--account", "-a", help="Filter by account"),
    confidence: float = typer.Option(0.60, "--confidence", "-c", min=0.0, max=1.0),
    auto_apply: bool = typer.Option(True, "--auto-apply/--manual-only"),
    limit: int | None = typer.Option(None, "--limit", "-l", help="Max transactions to match"),
) -> None:
    """Match unmatched transactions to payments.

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
            console.print("[green]No unmatched transactions[/]")
            return

        console.print(f"[cyan]Matching {len(unmatched)} transactions...[/]")

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
        console.print(f" [green]Matched: {matched_count}[/]")
        console.print(f" [yellow]Review needed: {review_count}[/]")


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
        console.print("[red]Invalid mode. Use 'auto' or 'preview'.[/]")
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

            summary = Table(title="Reconciliation Summary", show_header=True)
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
            console.print(f"[red]Reconciliation failed: {exc}[/]")
            raise typer.Exit(1) from exc


@app.command()
def queue(
    account_id: int | None = typer.Option(None, "--account", "-a"),
    interactive: bool = typer.Option(True, "--interactive/--list-only"),
    confidence_min: float = typer.Option(0.60, "--min", min=0.0, max=1.0),
    confidence_max: float = typer.Option(0.84, "--max", min=0.0, max=1.0),
) -> None:
    """Review queue for manual reconciliation.

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
            console.print("[green]No transactions need review[/]")
            return

        if interactive:
            # Interactive mode
            console.print(f"[bold cyan]Review Queue: {len(review_queue)} transactions[/]\n")

            for i, (tx, matches) in enumerate(review_queue, 1):
                console.print(f"[bold]Transaction {i}/{len(review_queue)}[/]")
                console.print(f"  Date: {tx.date.strftime('%d/%m/%Y')}")
                console.print(f"  Amount: [green]€{tx.amount}[/]")
                console.print(f"  Description: {tx.description}")

                # Suggestions table
                table = Table(title="Suggested Matches", show_header=True)
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
                    console.print("[green]Reconciled[/]\n")

                elif action == "ignore":
                    reason = Prompt.ask("Reason (optional)", default="")
                    _run(reconciliation_service.ignore_transaction(tx.id, reason))
                    console.print("[yellow]Ignored[/]\n")

                elif action == "quit":
                    break
                else:
                    console.print("[dim]Skipped[/]\n")

        else:
            # List-only mode
            table = Table(title=f"Review Queue ({len(review_queue)} items)")
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
                f"[green]Transaction {transaction_id} matched to payment {payment_id} ({match_type.value})[/]"
            )
            if tx.match_confidence is not None:
                console.print(f"  Confidence: {tx.match_confidence:.2%}")
        except ValueError as exc:
            session.rollback()
            console.print(f"[red]{exc}[/]")
            raise typer.Exit(1) from exc
        except Exception as exc:  # pragma: no cover - defensive logging
            session.rollback()
            console.print(f"[red]Failed to match transaction: {exc}[/]")
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
            console.print(f"[green]Transaction {transaction_id} reset to UNMATCHED[/]")
        except ValueError as exc:
            session.rollback()
            console.print(f"[red]{exc}[/]")
            raise typer.Exit(1) from exc
        except Exception as exc:  # pragma: no cover - defensive logging
            session.rollback()
            console.print(f"[red]Failed to reset transaction: {exc}[/]")
            raise typer.Exit(1) from exc
