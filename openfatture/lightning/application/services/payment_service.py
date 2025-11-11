"""Lightning payment monitoring and settlement service."""

import asyncio
import time
from datetime import UTC, datetime

from openfatture.core.events.base import get_global_event_bus
from openfatture.lightning.domain.enums import InvoiceStatus
from openfatture.lightning.domain.events import LightningPaymentSettled
from openfatture.lightning.infrastructure.lnd_client import LNDClient
from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository


class LightningPaymentService:
    """Service for monitoring and processing Lightning payments."""

    def __init__(
        self,
        lnd_client: LNDClient,
        invoice_repository: LightningInvoiceRepository,
        polling_interval_seconds: int = 30,
        max_concurrent_checks: int = 10,
    ):
        """Initialize the payment service.

        Args:
            lnd_client: LND gRPC client
            invoice_repository: Repository for invoice records
            polling_interval_seconds: How often to check for settlements
            max_concurrent_checks: Max concurrent invoice checks
        """
        self.lnd_client = lnd_client
        self.invoice_repo = invoice_repository
        self.polling_interval = polling_interval_seconds
        self.max_concurrent = max_concurrent_checks
        self.event_bus = get_global_event_bus()

        # Monitoring state
        self._monitoring_task: asyncio.Task | None = None
        self._is_monitoring = False

    async def start_monitoring(self):
        """Start the payment monitoring loop."""
        if self._is_monitoring:
            return

        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        print("Lightning payment monitoring started")

    async def stop_monitoring(self):
        """Stop the payment monitoring loop."""
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        print("Lightning payment monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop that checks for settled payments."""
        while self._is_monitoring:
            try:
                await self._check_pending_invoices()
                await self._cleanup_expired_invoices()
            except Exception as e:
                print(f"Error in payment monitoring loop: {e}")

            await asyncio.sleep(self.polling_interval)

    async def _check_pending_invoices(self):
        """Check all pending invoices for settlement."""
        pending_invoices = self.invoice_repo.find_pending()

        if not pending_invoices:
            return

        # Process invoices in batches to avoid overwhelming LND
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def check_invoice(invoice_record):
            async with semaphore:
                await self._check_single_invoice(invoice_record)

        # Create tasks for all pending invoices
        tasks = [check_invoice(invoice) for invoice in pending_invoices]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_single_invoice(self, invoice_record):
        """Check a single invoice for settlement."""
        try:
            # Query LND for current invoice status
            lnd_data = await self.lnd_client.lookup_invoice(invoice_record.payment_hash)

            if lnd_data.get("settled"):
                # Invoice has been settled!
                await self._process_settlement(invoice_record, lnd_data)

        except Exception as e:
            print(f"Error checking invoice {invoice_record.payment_hash}: {e}")

    async def _process_settlement(self, invoice_record, lnd_data: dict):
        """Process a settled invoice."""
        # Update invoice record
        invoice_record.status = InvoiceStatus.SETTLED
        invoice_record.settled_at = datetime.fromtimestamp(lnd_data["settle_date"], UTC)

        # Extract preimage if available
        preimage = lnd_data.get("payment_preimage")
        if preimage:
            invoice_record.preimage = preimage

        # Extract fee paid by sender (if available from LND)
        fee_paid_msat = lnd_data.get("fee_paid_msat")
        if fee_paid_msat:
            invoice_record.fee_paid_msat = fee_paid_msat

        # Save to database
        self.invoice_repo.save(invoice_record)

        # Publish domain event
        event = LightningPaymentSettled(
            payment_hash=invoice_record.payment_hash,
            preimage=preimage,
            amount_msat=invoice_record.amount_msat,
            fee_paid_msat=fee_paid_msat,
            settled_at=invoice_record.settled_at,
            fattura_id=invoice_record.fattura_id,
        )
        await self.event_bus.publish_async(event)

        print(
            f"Lightning payment settled: {invoice_record.payment_hash[:8]}... "
            f"({invoice_record.amount_msat} msat)"
        )

    async def _cleanup_expired_invoices(self):
        """Mark expired pending invoices."""
        expired_invoices = self.invoice_repo.find_expired_pending()

        for invoice in expired_invoices:
            invoice.status = InvoiceStatus.EXPIRED
            self.invoice_repo.save(invoice)

            print(f"Lightning invoice expired: {invoice.payment_hash[:8]}...")

    async def force_check_invoice(self, payment_hash: str) -> bool:
        """Manually check a specific invoice for settlement.

        Args:
            payment_hash: Payment hash to check

        Returns:
            True if invoice was settled, False otherwise
        """
        invoice_record = self.invoice_repo.find_by_payment_hash(payment_hash)
        if not invoice_record:
            raise ValueError(f"Invoice not found: {payment_hash}")

        if invoice_record.status != InvoiceStatus.PENDING:
            return False  # Already processed

        try:
            lnd_data = await self.lnd_client.lookup_invoice(payment_hash)

            if lnd_data.get("settled"):
                await self._process_settlement(invoice_record, lnd_data)
                return True

        except Exception as e:
            print(f"Error checking invoice {payment_hash}: {e}")

        return False

    async def get_payment_stats(self) -> dict:
        """Get payment statistics.

        Returns:
            Dictionary with payment statistics
        """
        # Get all settled invoices from last 30 days
        thirty_days_ago = datetime.now(UTC).timestamp() - (30 * 24 * 3600)
        start_date = datetime.fromtimestamp(thirty_days_ago, UTC)

        settled_invoices = self.invoice_repo.find_settled_in_date_range(
            start_date, datetime.now(UTC)
        )

        total_amount_msat = sum(inv.amount_msat or 0 for inv in settled_invoices)
        total_fees_msat = sum(inv.fee_paid_msat or 0 for inv in settled_invoices)

        return {
            "total_payments_30d": len(settled_invoices),
            "total_amount_msat_30d": total_amount_msat,
            "total_fees_msat_30d": total_fees_msat,
            "average_payment_msat": (
                total_amount_msat / len(settled_invoices) if settled_invoices else 0
            ),
            "average_fee_msat": total_fees_msat / len(settled_invoices) if settled_invoices else 0,
            "success_rate": len(settled_invoices)
            / max(1, len(settled_invoices) + len(self.invoice_repo.find_expired_pending())),
        }

    async def simulate_payment(self, payment_hash: str) -> bool:
        """Simulate a payment for testing purposes.

        This method is only available in mock/development mode.
        In production, payments can only be settled by actual Lightning transactions.

        Args:
            payment_hash: Payment hash to simulate payment for

        Returns:
            True if simulation succeeded
        """
        # This is a development/testing helper
        # In production LND, this would not exist
        if not hasattr(self.lnd_client, "_invoices"):
            raise RuntimeError("Payment simulation only available in mock mode")

        invoice_record = self.invoice_repo.find_by_payment_hash(payment_hash)
        if not invoice_record:
            raise ValueError(f"Invoice not found: {payment_hash}")

        # Simulate settlement in mock LND client
        mock_lnd_data = {
            "settled": True,
            "settle_date": int(time.time()),
            "payment_preimage": "00" * 32,  # Mock preimage
            "fee_paid_msat": 1000,  # Mock fee
        }

        # Update mock LND client state if available
        if hasattr(self.lnd_client, "simulate_payment"):
            try:
                await self.lnd_client.simulate_payment(payment_hash)
            except Exception:
                # Best-effort update for test environments
                pass

        await self._process_settlement(invoice_record, mock_lnd_data)
        return True
