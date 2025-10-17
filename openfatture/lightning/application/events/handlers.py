"""Event handlers for Lightning Network integration.

These handlers connect Lightning events to the broader OpenFatture system,
updating fatture status, triggering notifications, tax compliance, etc.
"""

import structlog

from openfatture.lightning.domain.events import (
    LightningAMLAlertEvent,
    LightningAMLVerified,
    LightningInvoiceExpired,
    LightningPaymentSettled,
    LightningPaymentTaxableEvent,
    LightningTaxDataStored,
)
from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Fattura, Pagamento

logger = structlog.get_logger(__name__)


class LightningPaymentSettledHandler:
    """Handler for LightningPaymentSettled events.

    Updates fattura and pagamento status when Lightning payment is received.
    """

    def __init__(self, session=None):
        self.session = session or get_session()
        self.invoice_repo = LightningInvoiceRepository(self.session)

    async def handle(self, event: LightningPaymentSettled):
        """Handle a settled Lightning payment.

        Args:
            event: LightningPaymentSettled domain event
        """
        print(f"Processing Lightning payment settlement: {event.payment_hash[:8]}...")

        try:
            # Find the invoice record
            invoice_record = self.invoice_repo.find_by_payment_hash(event.payment_hash)
            if not invoice_record:
                print(f"Warning: Invoice record not found for payment hash {event.payment_hash}")
                return

            # If linked to a fattura, update fattura and pagamento
            if invoice_record.fattura_id:
                await self._update_fattura_payment(
                    invoice_record.fattura_id, event.amount_msat, event.settled_at
                )

            # Log successful payment
            print(
                f"✓ Lightning payment processed: {event.amount_msat} msat "
                f"for fattura {invoice_record.fattura_id}"
            )

        except Exception as e:
            print(f"Error processing Lightning payment settlement: {e}")
            # In production, you might want to implement retry logic or dead letter queue

    async def _update_fattura_payment(self, fattura_id: int, amount_msat: int, settled_at):
        """Update fattura and pagamento records for settled payment.

        Args:
            fattura_id: ID of the fattura that was paid
            amount_msat: Payment amount in millisatoshis
            settled_at: When the payment was settled
        """
        # Convert msat to EUR (simplified conversion)
        # In production, this would use the same BTC converter as invoice service
        amount_sat = amount_msat / 1000
        amount_btc = amount_sat / 100_000_000
        # Mock conversion: 1 BTC = 45,000 EUR
        amount_eur = amount_btc * 45_000

        # Find fattura
        fattura = self.session.query(Fattura).filter(Fattura.id == fattura_id).first()
        if not fattura:
            print(f"Warning: Fattura {fattura_id} not found")
            return

        # Find associated pagamento
        pagamento = self.session.query(Pagamento).filter(Pagamento.fattura_id == fattura_id).first()

        if pagamento:
            # Update pagamento with Lightning payment
            from decimal import Decimal

            pagamento.apply_payment(Decimal(str(amount_eur)), settled_at.date())

            # Mark as paid via Lightning (could add a field for payment method)
            if hasattr(pagamento, "modalita"):
                pagamento.modalita = "Lightning Network"

            print(f"Updated pagamento for fattura {fattura_id}: applied {amount_eur:.2f} EUR")

        # Update fattura status if fully paid
        # This would typically be handled by existing business logic

        self.session.commit()


class LightningInvoiceExpiredHandler:
    """Handler for LightningInvoiceExpired events.

    Handles expired Lightning invoices, potentially triggering
    reminders or status updates.
    """

    def __init__(self, session=None):
        self.session = session or get_session()
        self.invoice_repo = LightningInvoiceRepository(self.session)

    async def handle(self, event: LightningInvoiceExpired):
        """Handle an expired Lightning invoice.

        Args:
            event: LightningInvoiceExpired domain event
        """
        print(f"Processing Lightning invoice expiry: {event.payment_hash[:8]}...")

        try:
            # Find the invoice record
            invoice_record = self.invoice_repo.find_by_payment_hash(event.payment_hash)
            if not invoice_record:
                print(f"Warning: Invoice record not found for payment hash {event.payment_hash}")
                return

            # If linked to a fattura, we might want to trigger reminders
            # or update status to indicate Lightning payment option expired
            if invoice_record.fattura_id:
                await self._handle_fattura_invoice_expired(invoice_record.fattura_id)

            print(f"✓ Lightning invoice expiry processed: {event.payment_hash[:8]}...")

        except Exception as e:
            print(f"Error processing Lightning invoice expiry: {e}")

    async def _handle_fattura_invoice_expired(self, fattura_id: int):
        """Handle expiry of Lightning invoice for a fattura.

        Args:
            fattura_id: ID of the fattura whose Lightning invoice expired
        """
        # This could trigger:
        # - Sending a reminder email about expired Lightning payment
        # - Creating a new Lightning invoice with different expiry
        # - Logging for analytics

        fattura = self.session.query(Fattura).filter(Fattura.id == fattura_id).first()
        if fattura:
            print(f"Lightning invoice expired for fattura {fattura_id} (numero: {fattura.numero})")
            # In production, you might queue a reminder or notification here


class LightningPaymentTaxableEventHandler:
    """Handler for LightningPaymentTaxableEvent.

    Handles tax compliance notifications and reporting when a Lightning
    payment creates a taxable event (capital gain) according to Italian law.
    """

    def __init__(self, session=None):
        self.session = session or get_session()
        self.invoice_repo = LightningInvoiceRepository(self.session)

    async def handle(self, event: LightningPaymentTaxableEvent):
        """Handle a taxable Lightning payment event.

        Args:
            event: LightningPaymentTaxableEvent domain event
        """
        logger.info(
            "taxable_payment_event",
            payment_hash=event.payment_hash[:8],
            amount_eur=event.payment_amount_eur,
            capital_gain_eur=event.capital_gain_eur,
            tax_year=event.tax_year,
        )

        try:
            # Find invoice record
            invoice_record = self.invoice_repo.find_by_payment_hash(event.payment_hash)
            if not invoice_record:
                logger.warning(
                    "invoice_not_found_for_taxable_event", payment_hash=event.payment_hash
                )
                return

            # Check if requires Quadro RW declaration
            if event.requires_quadro_rw:
                await self._trigger_quadro_rw_reminder(invoice_record, event)

            # If capital gain is significant, trigger notification
            if event.capital_gain_eur and event.capital_gain_eur > 1000:
                await self._notify_significant_capital_gain(invoice_record, event)

            # Log for audit trail
            logger.info(
                "taxable_event_processed",
                payment_hash=event.payment_hash[:8],
                tax_year=event.tax_year,
                requires_quadro_rw=event.requires_quadro_rw,
            )

        except Exception as e:
            logger.error(
                "error_processing_taxable_event",
                payment_hash=event.payment_hash,
                error=str(e),
            )

    async def _trigger_quadro_rw_reminder(self, invoice_record, event):
        """Trigger reminder for Quadro RW declaration requirement.

        Args:
            invoice_record: LightningInvoiceRecord entity
            event: LightningPaymentTaxableEvent
        """
        logger.info(
            "quadro_rw_reminder_triggered",
            payment_hash=invoice_record.payment_hash[:8],
            tax_year=event.tax_year,
            amount_eur=event.payment_amount_eur,
        )
        # In production, this could:
        # - Send email to accountant
        # - Create task in compliance system
        # - Update dashboard alert

    async def _notify_significant_capital_gain(self, invoice_record, event):
        """Notify about significant capital gain.

        Args:
            invoice_record: LightningInvoiceRecord entity
            event: LightningPaymentTaxableEvent
        """
        logger.warning(
            "significant_capital_gain_detected",
            payment_hash=invoice_record.payment_hash[:8],
            capital_gain_eur=event.capital_gain_eur,
            tax_year=event.tax_year,
        )
        # In production, this could:
        # - Send notification to finance team
        # - Flag for tax advisor review


class LightningAMLAlertEventHandler:
    """Handler for LightningAMLAlertEvent.

    Handles Anti-Money Laundering (AML) compliance alerts when payments
    exceed the legal threshold (5,000 EUR in Italy as of 2025).
    """

    def __init__(self, session=None):
        self.session = session or get_session()
        self.invoice_repo = LightningInvoiceRepository(self.session)

    async def handle(self, event: LightningAMLAlertEvent):
        """Handle an AML alert event.

        Args:
            event: LightningAMLAlertEvent domain event
        """
        logger.warning(
            "aml_alert_triggered",
            payment_hash=event.payment_hash[:8],
            amount_eur=event.amount_eur,
            threshold_eur=event.threshold_eur,
            client_id=event.client_id,
            client_name=event.client_name,
            verification_required=event.verification_required,
        )

        try:
            # Find invoice record
            invoice_record = self.invoice_repo.find_by_payment_hash(event.payment_hash)
            if not invoice_record:
                logger.warning("invoice_not_found_for_aml_alert", payment_hash=event.payment_hash)
                return

            # If verification required, trigger compliance workflow
            if event.verification_required and not event.already_verified:
                await self._trigger_aml_verification_workflow(invoice_record, event)

            # Log AML alert for regulatory audit trail
            await self._log_aml_alert_for_audit(invoice_record, event)

            logger.info(
                "aml_alert_processed",
                payment_hash=event.payment_hash[:8],
                verification_required=event.verification_required,
            )

        except Exception as e:
            logger.error(
                "error_processing_aml_alert", payment_hash=event.payment_hash, error=str(e)
            )

    async def _trigger_aml_verification_workflow(self, invoice_record, event):
        """Trigger AML verification workflow.

        Args:
            invoice_record: LightningInvoiceRecord entity
            event: LightningAMLAlertEvent
        """
        logger.info(
            "aml_verification_workflow_triggered",
            payment_hash=invoice_record.payment_hash[:8],
            amount_eur=event.amount_eur,
            client_name=event.client_name,
        )
        # In production, this could:
        # - Create task for compliance officer
        # - Send email notification
        # - Freeze funds until verification
        # - Request additional client documentation

    async def _log_aml_alert_for_audit(self, invoice_record, event):
        """Log AML alert for regulatory audit trail.

        Args:
            invoice_record: LightningInvoiceRecord entity
            event: LightningAMLAlertEvent
        """
        logger.info(
            "aml_alert_audit_log",
            payment_hash=invoice_record.payment_hash,
            amount_eur=event.amount_eur,
            client_id=event.client_id,
            client_name=event.client_name,
            fattura_id=event.fattura_id,
            timestamp=event.timestamp.isoformat(),
        )
        # In production, this could:
        # - Write to immutable audit log
        # - Send to compliance database
        # - Archive for regulatory inspection


class LightningTaxDataStoredHandler:
    """Handler for LightningTaxDataStored events.

    Handles confirmation that tax data has been successfully stored
    for a Lightning payment.
    """

    def __init__(self, session=None):
        self.session = session or get_session()
        self.invoice_repo = LightningInvoiceRepository(self.session)

    async def handle(self, event: LightningTaxDataStored):
        """Handle tax data stored event.

        Args:
            event: LightningTaxDataStored domain event
        """
        logger.info(
            "tax_data_stored",
            payment_hash=event.payment_hash[:8],
            eur_amount=event.eur_amount_declared,
            btc_eur_rate=event.btc_eur_rate,
            has_capital_gain=event.capital_gain_eur is not None,
            tax_year=event.tax_year,
        )

        try:
            # Verify tax data integrity
            invoice_record = self.invoice_repo.find_by_payment_hash(event.payment_hash)
            if invoice_record:
                await self._verify_tax_data_consistency(invoice_record, event)

            logger.debug(
                "tax_data_storage_confirmed",
                payment_hash=event.payment_hash[:8],
            )

        except Exception as e:
            logger.error(
                "error_processing_tax_data_stored",
                payment_hash=event.payment_hash,
                error=str(e),
            )

    async def _verify_tax_data_consistency(self, invoice_record, event):
        """Verify consistency of stored tax data.

        Args:
            invoice_record: LightningInvoiceRecord entity
            event: LightningTaxDataStored event
        """
        # Sanity checks
        if invoice_record.btc_eur_rate != event.btc_eur_rate:
            logger.warning(
                "tax_data_rate_mismatch",
                payment_hash=event.payment_hash,
                stored_rate=(
                    float(invoice_record.btc_eur_rate) if invoice_record.btc_eur_rate else None
                ),
                event_rate=event.btc_eur_rate,
            )


class LightningAMLVerifiedHandler:
    """Handler for LightningAMLVerified events.

    Handles completion of AML verification process.
    """

    def __init__(self, session=None):
        self.session = session or get_session()
        self.invoice_repo = LightningInvoiceRepository(self.session)

    async def handle(self, event: LightningAMLVerified):
        """Handle AML verification completion event.

        Args:
            event: LightningAMLVerified domain event
        """
        logger.info(
            "aml_verification_completed",
            payment_hash=event.payment_hash[:8],
            verified_by=event.verified_by,
            verified_at=event.verified_at.isoformat(),
            client_id=event.client_id,
        )

        try:
            # Update invoice record
            invoice_record = self.invoice_repo.find_by_payment_hash(event.payment_hash)
            if invoice_record:
                invoice_record.mark_aml_verified()
                self.invoice_repo.save(invoice_record)

                logger.info(
                    "invoice_aml_status_updated",
                    payment_hash=event.payment_hash[:8],
                    verified=True,
                )

        except Exception as e:
            logger.error(
                "error_processing_aml_verification",
                payment_hash=event.payment_hash,
                error=str(e),
            )


# Registry of event handlers
LIGHTNING_EVENT_HANDLERS = {
    # Core Lightning events
    LightningPaymentSettled: LightningPaymentSettledHandler,
    LightningInvoiceExpired: LightningInvoiceExpiredHandler,
    # Tax & Compliance events (NEW!)
    LightningPaymentTaxableEvent: LightningPaymentTaxableEventHandler,
    LightningAMLAlertEvent: LightningAMLAlertEventHandler,
    LightningTaxDataStored: LightningTaxDataStoredHandler,
    LightningAMLVerified: LightningAMLVerifiedHandler,
}


def register_lightning_event_handlers(event_bus):
    """Register all Lightning event handlers with the event bus.

    Args:
        event_bus: The event bus to register handlers with
    """
    for event_type, handler_class in LIGHTNING_EVENT_HANDLERS.items():
        handler_instance = handler_class()

        # Create async wrapper for the handler
        async def async_handler(event, handler=handler_instance):
            await handler.handle(event)

        event_bus.subscribe(event_type, async_handler)
        print(f"Registered Lightning event handler: {event_type.__name__}")


def initialize_lightning_integration():
    """Initialize Lightning integration by registering event handlers.

    This should be called during application startup.
    """
    from openfatture.core.events.base import get_global_event_bus

    event_bus = get_global_event_bus()
    register_lightning_event_handlers(event_bus)
    print("Lightning integration initialized")
