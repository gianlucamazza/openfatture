"""Bank account management commands."""

from decimal import Decimal

import typer
from rich.table import Table

from ..domain.models import BankAccount
from ..infrastructure.repository import BankAccountRepository
from ._app import app, console, get_db_session


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
                        f"[red]An account with IBAN {iban} already exists (ID {existing.id}).[/]"
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
            console.print(f"[green]Account created with ID {account.id}[/]")
        except typer.Exit:
            session.rollback()
            raise
        except Exception as exc:  # pragma: no cover - defensive logging
            session.rollback()
            console.print(f"[red]Failed to create account: {exc}[/]")
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
            console.print("[yellow]No bank accounts configured yet.[/]")
            return

        table = Table(title="Bank Accounts", show_lines=False)
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
                "" if account.is_active else "",
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
            console.print(f"[red]Account {account_id} not found[/]")
            raise typer.Exit(1)

        try:
            if iban and iban != account.iban:
                existing = repo.get_by_iban(iban)
                if existing and existing.id != account.id:
                    console.print(
                        f"[red]Another account with IBAN {iban} exists (ID {existing.id}).[/]"
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
            console.print(f"[green]Account {account_id} updated[/]")
        except typer.Exit:
            session.rollback()
            raise
        except Exception as exc:  # pragma: no cover - defensive logging
            session.rollback()
            console.print(f"[red]Failed to update account: {exc}[/]")
            raise typer.Exit(1) from exc


@app.command(name="delete-account")
def delete_account(account_id: int = typer.Argument(..., help="Account ID to delete")) -> None:
    """Delete a bank account (and related transactions)."""
    with get_db_session() as session:
        repo = BankAccountRepository(session)
        try:
            deleted = repo.delete(account_id)
            if not deleted:
                console.print(f"[yellow]Account {account_id} not found[/]")
                raise typer.Exit(1)

            session.commit()
            console.print(f"[green]Account {account_id} deleted[/]")
        except typer.Exit:
            session.rollback()
            raise
        except Exception as exc:  # pragma: no cover - defensive logging
            session.rollback()
            console.print(f"[red]Failed to delete account: {exc}[/]")
            raise typer.Exit(1) from exc
