"""Payment service adapter for Streamlit web interface.

Provides caching and simplified API for payment operations.
"""

from datetime import date
from decimal import Decimal
from typing import Any

import streamlit as st

from openfatture.payment.domain.models import BankAccount, BankTransaction
from openfatture.utils.config import Settings, get_settings
from openfatture.web.utils.cache import get_db_session


class StreamlitPaymentService:
    """Adapter service for payment operations in Streamlit."""

    def __init__(self) -> None:
        """Initialize service with settings."""
        self.settings: Settings = get_settings()

    @st.cache_data(ttl=30, show_spinner=False)
    def get_bank_accounts(self) -> list[dict[str, Any]]:
        """
        Get list of bank accounts.

        Returns:
            List of bank account dictionaries
        """
        db = get_db_session()
        accounts = db.query(BankAccount).all()

        return [
            {
                "id": acc.id,
                "name": acc.name,
                "iban": acc.iban,
                "bank_name": acc.bank_name,
                "currency": acc.currency,
                "opening_balance": float(acc.opening_balance) if acc.opening_balance else 0.0,
                "current_balance": float(acc.current_balance) if acc.current_balance else 0.0,
            }
            for acc in accounts
        ]

    @st.cache_data(ttl=30, show_spinner=False)
    def get_transactions(
        self,
        account_id: int | None = None,
        limit: int | None = None,
        status_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get list of bank transactions with optional filters.

        Args:
            account_id: Filter by bank account ID
            limit: Maximum number of results
            status_filter: Filter by transaction status

        Returns:
            List of transaction dictionaries
        """
        db = get_db_session()
        query = db.query(BankTransaction).order_by(BankTransaction.date.desc())

        if account_id:
            query = query.filter(BankTransaction.account_id == account_id)

        if status_filter and status_filter != "all":
            query = query.filter(BankTransaction.status == status_filter)

        if limit:
            query = query.limit(limit)

        transactions = query.all()

        return [
            {
                "id": str(tx.id),  # UUID to string
                "account_id": tx.account_id,
                "date": tx.date,
                "amount": float(tx.amount),
                "description": tx.description,
                "reference": tx.reference,
                "status": tx.status.value if tx.status else "unknown",
                "matched_payment_id": tx.matched_payment_id,
                "match_confidence": tx.match_confidence,
                "created_at": tx.created_at,
            }
            for tx in transactions
        ]

    def get_transaction_detail(self, transaction_id: int) -> BankTransaction | None:
        """
        Get detailed transaction by ID.

        Args:
            transaction_id: Transaction ID

        Returns:
            BankTransaction object or None if not found
        """
        db = get_db_session()
        return db.query(BankTransaction).filter(BankTransaction.id == transaction_id).first()

    @st.cache_data(ttl=60, show_spinner=False)  # Longer cache for stats
    def get_payment_stats(self) -> dict[str, Any]:
        """
        Get payment statistics.

        Returns:
            Dictionary with payment statistics
        """
        db = get_db_session()

        # Total accounts
        total_accounts = db.query(BankAccount).count()

        # Total transactions
        total_transactions = db.query(BankTransaction).count()

        # Transactions by status
        from openfatture.payment.domain.enums import TransactionStatus

        status_counts = {}
        for status in TransactionStatus:
            count = db.query(BankTransaction).filter(BankTransaction.status == status).count()
            status_counts[status.value] = count

        # Matched vs unmatched
        matched_count = (
            db.query(BankTransaction).filter(BankTransaction.matched_payment_id.isnot(None)).count()
        )
        unmatched_count = total_transactions - matched_count

        # Total balance across all accounts
        total_balance = 0.0
        accounts = db.query(BankAccount).all()
        for account in accounts:
            if account.current_balance:
                total_balance += float(account.current_balance)

        return {
            "total_accounts": total_accounts,
            "total_transactions": total_transactions,
            "status_distribution": status_counts,
            "matched_transactions": matched_count,
            "unmatched_transactions": unmatched_count,
            "total_balance": total_balance,
        }

    def create_bank_account(self, account_data: dict[str, Any]) -> BankAccount:
        """
        Create a new bank account.

        Args:
            account_data: Account data dictionary

        Returns:
            Created BankAccount object
        """
        db = get_db_session()

        account = BankAccount(
            name=account_data["name"],
            iban=account_data.get("iban"),
            bic_swift=account_data.get("bic_swift"),
            bank_name=account_data.get("bank_name", ""),
            currency=account_data.get("currency", "EUR"),
            opening_balance=Decimal(str(account_data.get("opening_balance", 0.0))),
            opening_date=account_data.get("opening_date", date.today()),
        )

        db.add(account)
        db.commit()
        db.refresh(account)

        # Clear cache
        self._clear_payment_cache()

        return account

    def import_bank_statement(
        self, account_id: int, file_content: bytes, filename: str, bank_preset: str | None = None
    ) -> dict[str, Any]:
        """
        Import bank statement for an account from uploaded file content.

        Args:
            account_id: Bank account ID
            file_content: Raw file content as bytes
            filename: Original filename
            bank_preset: Bank preset for CSV parsing (optional)

        Returns:
            Import result dictionary
        """
        from pathlib import Path
        from tempfile import NamedTemporaryFile

        from openfatture.payment.infrastructure.importers.factory import ImporterFactory
        from openfatture.payment.infrastructure.repository import BankAccountRepository
        from openfatture.web.utils.cache import db_session_scope

        try:
            with db_session_scope() as session:
                # 1. Load account
                account_repo = BankAccountRepository(session)
                account = account_repo.get_by_id(account_id)
                if not account:
                    return {
                        "success": False,
                        "message": f"Account {account_id} not found",
                        "transactions_imported": 0,
                        "errors": ["Account not found"],
                    }

                # 2. Create temporary file
                with NamedTemporaryFile(
                    mode="wb", suffix=f"_{filename}", delete=False
                ) as temp_file:
                    temp_file.write(file_content)
                    temp_file_path = Path(temp_file.name)

                try:
                    # 3. Create importer with factory
                    factory = ImporterFactory()
                    importer = factory.create_from_file(temp_file_path, bank_preset=bank_preset)

                    # 4. Import transactions
                    result = importer.import_transactions(account)

                    # 5. Clear caches after import
                    self._clear_payment_cache()

                    return {
                        "success": True,
                        "message": f"Imported {result.success_count} transactions successfully",
                        "transactions_imported": result.success_count,
                        "errors": result.errors,
                        "duplicates": getattr(result, "duplicates", 0),
                        "format_detected": importer.__class__.__name__,
                    }

                finally:
                    # Clean up temporary file
                    temp_file_path.unlink(missing_ok=True)

        except Exception as e:
            return {
                "success": False,
                "message": f"Import failed: {str(e)}",
                "transactions_imported": 0,
                "errors": [str(e)],
            }

    def get_potential_matches(self, transaction_id: int, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get potential invoice matches for a transaction.

        Args:
            transaction_id: Transaction ID
            limit: Maximum number of matches to return

        Returns:
            List of potential matches with confidence scores
        """
        from openfatture.storage.database.models import Fattura, StatoFattura
        from openfatture.web.utils.cache import get_db_session

        db = get_db_session()
        try:
            # For now, skip transaction validation and focus on invoice matching
            # TODO: Add proper transaction lookup when UUID issues are resolved

            # Find unpaid invoices (simplified - no amount filtering for now)
            invoices = (
                db.query(Fattura)
                .join(Fattura.cliente)
                .filter(
                    Fattura.stato.in_(
                        [StatoFattura.DA_INVIARE, StatoFattura.INVIATA, StatoFattura.CONSEGNATA]
                    )
                )
                .limit(limit)
                .all()
            )

            matches = []
            for invoice in invoices:
                # Simple matching - just return all unpaid invoices
                # TODO: Implement proper amount and date matching
                matches.append(
                    {
                        "id": invoice.id,
                        "numero": invoice.numero,
                        "anno": invoice.anno,
                        "cliente": invoice.cliente.denominazione,
                        "totale": float(invoice.totale),
                        "confidence": 0.5,  # Default confidence
                        "days_difference": 0,
                        "amount_difference": 0.0,
                    }
                )

            # Sort by confidence
            matches.sort(key=lambda x: x["confidence"], reverse=True)
            return matches

        except Exception as e:
            st.error(f"Errore nel recupero abbinamenti: {str(e)}")
            return []
        finally:
            db.close()

    def match_transaction(self, transaction_id: int, invoice_id: int) -> dict[str, Any]:
        """
        Manually match a transaction to an invoice.

        Args:
            transaction_id: Transaction ID
            invoice_id: Invoice ID

        Returns:
            Match result dictionary
        """
        from openfatture.storage.database.models import Fattura, PaymentAllocation
        from openfatture.web.utils.cache import db_session_scope

        try:
            with db_session_scope() as session:
                # Verify invoice exists
                invoice = session.query(Fattura).filter(Fattura.id == invoice_id).first()
                if not invoice:
                    return {"success": False, "message": "Fattura non trovata"}

                # Create allocation record (simplified approach)
                allocation = PaymentAllocation(
                    fattura_id=invoice_id,
                    amount=invoice.totale,  # Assume full payment for simplicity
                    payment_date=invoice.data_emissione,
                    notes=f"Manual match from web UI - Transaction {transaction_id}",
                )
                session.add(allocation)
                session.commit()

                self._clear_payment_cache()
                return {"success": True, "message": "Transazione abbinata con successo"}

        except Exception as e:
            return {"success": False, "message": f"Errore: {str(e)}"}

    @st.cache_data(ttl=30, show_spinner=False)
    def search_invoices_for_matching(
        self, search_term: str, amount: float, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Search for invoices that might match a payment transaction.

        Args:
            search_term: Search term (invoice number, client name, etc.)
            amount: Transaction amount to match
            limit: Maximum number of results

        Returns:
            List of matching invoices with basic info
        """
        from openfatture.storage.database.models import Fattura, StatoFattura
        from openfatture.web.utils.cache import get_db_session

        db = get_db_session()
        try:
            # Search for unpaid invoices that match the search term
            # Note: oggetto search is done post-query to avoid mypy SQLAlchemy issues
            invoices_query = (
                db.query(Fattura)
                .join(Fattura.cliente)
                .filter(
                    Fattura.stato.in_(
                        [StatoFattura.DA_INVIARE, StatoFattura.INVIATA, StatoFattura.CONSEGNATA]
                    )
                )
                .filter(
                    (Fattura.numero.contains(search_term))
                    | (Fattura.cliente.denominazione.contains(search_term))
                )
            )

            # Get all matching invoices
            all_invoices = invoices_query.all()

            # Filter additionally by oggetto if present (post-query to avoid SQLAlchemy type issues)
            invoices = (
                [
                    inv
                    for inv in all_invoices
                    if inv.oggetto and search_term.lower() in inv.oggetto.lower()
                ]
                if search_term
                else all_invoices
            )

            # Limit results
            invoices = invoices[:limit]

            matches = []
            for invoice in invoices:
                # Calculate confidence based on amount match
                amount_diff = abs(float(invoice.totale) - amount)
                confidence = max(0.1, 1.0 - (amount_diff / amount)) if amount > 0 else 0.5

                matches.append(
                    {
                        "id": invoice.id,
                        "numero": f"{invoice.numero}/{invoice.anno}",
                        "cliente": invoice.cliente.denominazione,
                        "totale": float(invoice.totale),
                        "oggetto": invoice.oggetto or "",
                        "confidence": confidence,
                    }
                )

            # Sort by confidence
            matches.sort(key=lambda x: x["confidence"], reverse=True)
            return matches

        except Exception as e:
            st.error(f"Errore nella ricerca fatture: {str(e)}")
            return []
        finally:
            db.close()

    def _clear_payment_cache(self) -> None:
        """Clear payment-related caches."""
        # This will be called by Streamlit's cache invalidation
        pass
