"""Lightning payment monitoring and settlement service."""

import asyncio
import time
from datetime import UTC, datetime
from typing import Any

from openfatture.events.base import get_global_event_bus
from openfatture.lightning.domain.enums import InvoiceStatus
from openfatture.lightning.domain.events import LightningPaymentSettled
from openfatture.lightning.domain.models import LightningInvoiceRecord
from openfatture.lightning.infrastructure.lnd_client import ProductionLNDClient
from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository
from openfatture.platform.logging import get_logger

logger = get_logger(__name__)


class LightningPaymentService:
    """Service for monitoring and processing Lightning payments."""

    def __init__(
        self,
        lnd_client: ProductionLNDClient,
        invoice_repository: LightningInvoiceRepository,
        polling_interval_seconds: int = 30,
        max_concurrent_checks: int = 10,
    ) -> None:
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

    async def start_monitoring(self) -> None:
        """Start the payment monitoring loop."""
        if self._is_monitoring:
            return

        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Lightning payment monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop the payment monitoring loop."""
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Lightning payment monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop that checks for settled payments."""
        while self._is_monitoring:
            try:
                await self._check_pending_invoices()
                await self._cleanup_expired_invoices()
            except Exception as e:
                logger.error(f"Error in payment monitoring loop: {e}")

            await asyncio.sleep(self.polling_interval)

    async def _check_pending_invoices(self) -> None:
        """Check all pending invoices for settlement."""
        pending_invoices = self.invoice_repo.find_pending()

        if not pending_invoices:
            return

        # Process invoices in batches to avoid overwhelming LND
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def check_invoice(invoice_record: LightningInvoiceRecord) -> None:
            async with semaphore:
                await self._check_single_invoice(invoice_record)

        # Create tasks for all pending invoices
        tasks = [check_invoice(invoice) for invoice in pending_invoices]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_single_invoice(self, invoice_record: LightningInvoiceRecord) -> None:
        """Check a single invoice for settlement."""
        try:
            # Query LND for current invoice status
            lnd_data = await self.lnd_client.lookup_invoice(invoice_record.payment_hash)

            if lnd_data.get("settled"):
                # Invoice has been settled!
                await self._process_settlement(invoice_record, lnd_data)

        except Exception as e:
            logger.error(f"Error checking invoice {invoice_record.payment_hash}: {e}")

    async def _process_settlement(
        self, invoice_record: LightningInvoiceRecord, lnd_data: dict[str, Any]
    ) -> None:
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

        # Zero-amount invoices carry no amount until settlement: LND reports the
        # amount actually paid, which is what the domain event must carry.
        settled_amount_msat = lnd_data.get("amt_paid_msat") or invoice_record.amount_msat
        if settled_amount_msat is None:
            raise ValueError(
                f"Settled invoice {invoice_record.payment_hash} has no amount: "
                "neither amt_paid_msat nor a stored amount_msat is available"
            )

        # Publish domain event
        event = LightningPaymentSettled(
            payment_hash=invoice_record.payment_hash,
            preimage=preimage,
            amount_msat=settled_amount_msat,
            fee_paid_msat=fee_paid_msat,
            settled_at=invoice_record.settled_at,
            fattura_id=invoice_record.fattura_id,
        )
        await self.event_bus.publish_async(event)

        logger.info(
            "lightning_payment_settled",
            payment_hash_prefix=invoice_record.payment_hash[:8],
            amount_msat=invoice_record.amount_msat,
        )

    async def _cleanup_expired_invoices(self) -> None:
        """Mark expired pending invoices."""
        expired_invoices = self.invoice_repo.find_expired_pending()

        for invoice in expired_invoices:
            invoice.status = InvoiceStatus.EXPIRED
            self.invoice_repo.save(invoice)

            logger.info(f"Lightning invoice expired: {invoice.payment_hash[:8]}...")

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
            logger.error(f"Error checking invoice {payment_hash}: {e}")

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

    #: Amount credited when simulating the payment of a zero-amount invoice.
    DEFAULT_SIMULATED_AMOUNT_MSAT = 1_000_000  # 1000 sat

    async def simulate_payment(self, payment_hash: str, amount_msat: int | None = None) -> bool:
        """Simulate a payment settlement (dev/test only).

        Requires ``lnd_client.allow_mock is True`` (wired from
        ``settings.lightning_allow_mock``). Never available on production
        clients.

        Args:
            payment_hash: Payment hash to simulate payment for
            amount_msat: Amount the simulated payer sends. Defaults to the
                invoice amount, or to DEFAULT_SIMULATED_AMOUNT_MSAT for
                zero-amount invoices.

        Returns:
            True if simulation succeeded

        Raises:
            RuntimeError: If the LND client does not allow mock settlement
            ValueError: If the invoice is not found
        """
        allow_mock = bool(getattr(self.lnd_client, "allow_mock", False))
        if not allow_mock:
            raise RuntimeError(
                "Payment simulation requires lightning_allow_mock=true "
                "(ProductionLNDClient(allow_mock=True)). Real settlements "
                "only come from LND payment events."
            )

        invoice_record = self.invoice_repo.find_by_payment_hash(payment_hash)
        if not invoice_record:
            raise ValueError(f"Invoice not found: {payment_hash}")

        paid_msat = (
            amount_msat
            if amount_msat is not None
            else invoice_record.amount_msat or self.DEFAULT_SIMULATED_AMOUNT_MSAT
        )

        mock_lnd_data: dict[str, Any] = {
            "settled": True,
            "settle_date": int(time.time()),
            "payment_preimage": "00" * 32,
            "fee_paid_msat": 1000,
            "amt_paid_msat": paid_msat,
        }

        simulate = getattr(self.lnd_client, "simulate_payment", None)
        if callable(simulate):
            await simulate(payment_hash)

        await self._process_settlement(invoice_record, mock_lnd_data)
        return True
