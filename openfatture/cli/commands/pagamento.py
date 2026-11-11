"""Collection ledger CLI: the same application services used by the assistant."""

import json
from typing import Any
from uuid import uuid4

import typer
from rich.console import Console

from openfatture.cli.database import ensure_database
from openfatture.cli.output import remember_result
from openfatture.i18n import _
from openfatture.payment.application import collection_api as api

app = typer.Typer(name="pagamento")
console = Console()


@app.callback()
def prepare() -> None:
    ensure_database()


def show_result(result: Any) -> None:
    remember_result(result)
    console.print(json.dumps(result, ensure_ascii=False, indent=2), markup=False)
    if result.get("error"):
        raise typer.Exit(1)


@app.command("list")
def list_collections(invoice_id: int | None = typer.Option(None, "--invoice")) -> None:
    """List collection ledger entries, optionally for one invoice."""
    show_result(api.get_collections(invoice_id))


@app.command("show")
def show_collections(invoice_id: int) -> None:
    """Show the collection ledger of an invoice."""
    show_result(api.get_collections(invoice_id))


@app.command("record")
def record(
    amount: str,
    invoice_id: int | None = typer.Option(None, "--invoice"),
    payment_id: int | None = typer.Option(None, "--payment"),
    effective_date: str | None = typer.Option(None, "--date"),
    request_id: str | None = typer.Option(None, "--request-id"),
    notes: str | None = typer.Option(None, "--notes"),
) -> None:
    """Record a received amount (idempotent per --request-id)."""
    show_result(
        api.record_collection(
            amount, request_id or str(uuid4()), invoice_id, payment_id, effective_date, notes
        )
    )


@app.command("allocate")
def allocate(
    receipt_id: int,
    invoice_id: int,
    amount: str,
    payment_id: int | None = typer.Option(None, "--payment"),
    request_id: str | None = typer.Option(None, "--request-id"),
) -> None:
    """Allocate part of a recorded receipt to an invoice."""
    show_result(
        api.allocate_collection(
            receipt_id, invoice_id, amount, request_id or str(uuid4()), payment_id
        )
    )


@app.command("reverse")
def reverse(
    entry_id: int,
    amount: str,
    reason: str = typer.Option(..., "--reason"),
    request_id: str | None = typer.Option(None, "--request-id"),
) -> None:
    """Reverse a ledger entry after confirmation; history is preserved."""
    if not typer.confirm(
        _("cli-pagamento-reverse-confirm", amount=amount, entry=str(entry_id)), default=False
    ):
        raise typer.Abort()
    show_result(api.reverse_collection(entry_id, amount, reason, request_id or str(uuid4())))


@app.command("declare-status")
def declare(
    invoice_id: int,
    value: str,
    source: str = typer.Option("owner", "--source"),
    declared_on: str | None = typer.Option(None, "--date"),
    request_id: str | None = typer.Option(None, "--request-id"),
) -> None:
    """Declare an invoice collection status reported by the owner or another source."""
    show_result(
        api.declare_collection_status(
            invoice_id, value, source, request_id or str(uuid4()), declared_on
        )
    )


@app.command("migrate")
def migrate_collections() -> None:
    """Upgrade existing collection data without changing monetary balances."""
    from openfatture.payment.application.collection_migration import upgrade_collection_database
    from openfatture.storage.database import base

    assert base.engine is not None
    upgrade_collection_database(base.engine)
    show_result({"success": True, "message": "Collection migration complete"})


@app.command("bank-receipt")
def bank_receipt(
    transaction_id: str, request_id: str | None = typer.Option(None, "--request-id")
) -> None:
    """Record an imported bank transaction as a collection receipt."""
    show_result(api.record_bank_collection(transaction_id, request_id or str(uuid4())))


@app.command("allocate-batch")
def allocate_batch(
    receipt_id: int,
    allocations: str = typer.Option(..., "--allocations"),
    request_id: str | None = typer.Option(None, "--request-id"),
) -> None:
    """Allocate a receipt across several invoices (JSON --allocations)."""
    show_result(api.allocate_collection_batch(receipt_id, allocations, request_id or str(uuid4())))
