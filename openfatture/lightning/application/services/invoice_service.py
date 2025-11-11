"""Lightning invoice generation and management service."""

import hashlib
from decimal import Decimal

from openfatture.core.events.base import get_global_event_bus
from openfatture.lightning.domain.events import LightningInvoiceCreated
from openfatture.lightning.domain.value_objects import LightningInvoice
from openfatture.lightning.infrastructure.lnd_client import LNDClient
from openfatture.lightning.infrastructure.rate_provider import (
    BTCConversionService,
    create_btc_conversion_service,
)
from openfatture.utils.config import Settings, get_settings


class LightningInvoiceService:
    """Service for creating and managing Lightning invoices.

    This service handles Lightning invoice creation with optional
    Italian tax compliance tracking integration.
    """

    def __init__(
        self,
        lnd_client: LNDClient,
        btc_converter: BTCConversionService | None = None,
        default_expiry_hours: int = 24,
        tax_service=None,  # Type hint would create circular import
        invoice_repository=None,  # Optional repository for tax tracking
    ):
        """Initialize the invoice service.

        Args:
            lnd_client: LND gRPC client
            btc_converter: BTC/EUR converter (creates default if None)
            default_expiry_hours: Default invoice expiry in hours
            tax_service: Optional TaxCalculationService for compliance
            invoice_repository: Optional repository for saving tax data
        """
        self.lnd_client = lnd_client
        self.btc_converter = btc_converter or create_btc_conversion_service(get_settings())
        self.default_expiry_hours = default_expiry_hours
        self.tax_service = tax_service  # Optional, for tax compliance
        self.invoice_repo = invoice_repository  # Optional, for persistence
        self.event_bus = get_global_event_bus()

    async def create_invoice_from_fattura(
        self,
        fattura_id: int,
        totale_eur: Decimal,
        descrizione: str,
        cliente_nome: str,
        expiry_hours: int | None = None,
        # NEW: Tax compliance parameters
        track_tax_data: bool = True,
        acquisition_cost_eur: Decimal | None = None,
        cliente_id: int | None = None,
    ) -> LightningInvoice:
        """Create a Lightning invoice from fattura data.

        Args:
            fattura_id: ID of the fattura
            totale_eur: Total amount in EUR
            descrizione: Invoice description
            cliente_nome: Client name for description
            expiry_hours: Invoice expiry in hours (uses default if None)
            track_tax_data: Whether to track tax data (default True)
            acquisition_cost_eur: BTC acquisition cost for capital gains (optional)
            cliente_id: Client ID for AML alerts (optional)

        Returns:
            Created LightningInvoice

        Raises:
            BTCConversionError: If EUR to BTC conversion fails
            LNDClientError: If LND invoice creation fails

        Note:
            Tax tracking requires tax_service and invoice_repository to be set.
            If not available, invoice is created without tax tracking.
        """
        # Convert EUR to BTC
        btc_amount = await self.btc_converter.convert_eur_to_btc(totale_eur)

        # Get current BTC/EUR rate for tax tracking
        rate_info = await self.btc_converter.get_rate_info()
        btc_eur_rate = rate_info.get("rate") or rate_info.get("current_rate")

        if btc_eur_rate is None:
            # Fallback: derive rate by converting 1 BTC to EUR
            btc_eur_rate = float(await self.btc_converter.convert_btc_to_eur(Decimal("1")))

        # Convert to millisatoshis (1 sat = 1000 msat)
        amount_msat = int(btc_amount * Decimal("100000000") * Decimal("1000"))

        # Create enhanced description
        enhanced_description = f"Fattura #{fattura_id} - {descrizione} - Cliente: {cliente_nome}"

        # Ensure description fits BOLT-11 limits (639 bytes max)
        if len(enhanced_description.encode("utf-8")) > 639:
            enhanced_description = enhanced_description[:200] + "..."

        # Create invoice
        expiry_seconds = (expiry_hours or self.default_expiry_hours) * 3600
        invoice = await self.lnd_client.create_invoice(
            amount_msat=amount_msat, description=enhanced_description, expiry_seconds=expiry_seconds
        )

        # TAX COMPLIANCE: Store tax data if enabled and services available
        if track_tax_data and self.tax_service and self.invoice_repo:
            try:
                # Check AML threshold
                await self.tax_service.check_aml_threshold(
                    payment_hash=invoice.payment_hash,
                    amount_eur=totale_eur,
                    client_id=cliente_id,
                    client_name=cliente_nome,
                )

                # Store preliminary tax data (will be updated on settlement)
                # We save the BTC/EUR rate NOW for accurate tracking
                invoice_record = self.invoice_repo.find_by_payment_hash(invoice.payment_hash)
                if invoice_record:
                    invoice_record.btc_eur_rate = btc_eur_rate
                    invoice_record.eur_amount_declared = totale_eur
                    invoice_record.acquisition_cost_eur = acquisition_cost_eur
                    invoice_record.fattura_id = fattura_id

                    # Mark if exceeds AML threshold
                    if totale_eur >= self.tax_service.aml_threshold_eur:
                        invoice_record.exceeds_aml_threshold = True

                    self.invoice_repo.save(invoice_record)

            except Exception as e:
                # Tax tracking failure should not block invoice creation
                # Log error but continue
                print(f"Warning: Tax tracking failed for invoice {invoice.payment_hash}: {e}")

        # Publish domain event
        event = LightningInvoiceCreated(
            payment_hash=invoice.payment_hash,
            payment_request=invoice.payment_request,
            amount_msat=invoice.amount_msat,
            description=invoice.description,
            expiry_timestamp=invoice.expiry_timestamp,
            fattura_id=fattura_id,
        )
        await self.event_bus.publish_async(event)

        return invoice

    async def create_zero_amount_invoice(
        self, descrizione: str, expiry_hours: int | None = None
    ) -> LightningInvoice:
        """Create a zero-amount Lightning invoice.

        Zero-amount invoices allow payers to specify the amount when paying.

        Args:
            descrizione: Invoice description
            expiry_hours: Invoice expiry in hours (uses default if None)

        Returns:
            Created LightningInvoice
        """
        expiry_seconds = (expiry_hours or self.default_expiry_hours) * 3600

        invoice = await self.lnd_client.create_invoice(
            amount_msat=None,  # Zero-amount
            description=descrizione,
            expiry_seconds=expiry_seconds,
        )

        # Publish domain event
        event = LightningInvoiceCreated(
            payment_hash=invoice.payment_hash,
            payment_request=invoice.payment_request,
            amount_msat=None,
            description=invoice.description,
            expiry_timestamp=invoice.expiry_timestamp,
            fattura_id=None,
        )
        await self.event_bus.publish_async(event)

        return invoice

    async def get_invoice_status(self, payment_hash: str) -> dict:
        """Get the current status of a Lightning invoice.

        Args:
            payment_hash: Payment hash of the invoice

        Returns:
            Dictionary with invoice status information
        """
        return await self.lnd_client.lookup_invoice(payment_hash)

    def generate_payment_hash(self, invoice_data: str) -> str:
        """Generate a payment hash from invoice data.

        This is a utility method for generating payment hashes.
        In production LND, this is handled by LND itself.

        Args:
            invoice_data: String data to hash

        Returns:
            64-character hex payment hash
        """
        return hashlib.sha256(invoice_data.encode("utf-8")).hexdigest()

    def validate_bolt11_invoice(self, bolt11_string: str) -> bool:
        """Validate a BOLT-11 invoice string format.

        This is a basic validation. Full BOLT-11 parsing would require
        the lightning-payencode library.

        Args:
            bolt11_string: BOLT-11 invoice string

        Returns:
            True if format appears valid
        """
        if not bolt11_string.startswith("lnbc"):
            return False

        # Check for bech32 checksum (last 6 characters should be valid bech32)
        # This is a simplified check
        if len(bolt11_string) < 100:  # Minimum viable length
            return False

        return True

    async def finalize_tax_data_on_settlement(
        self,
        payment_hash: str,
    ) -> bool:
        """Finalize tax data after a payment is settled.

        This method should be called by PaymentService when an invoice
        is settled, to calculate and store capital gains.

        Args:
            payment_hash: Payment hash of the settled invoice

        Returns:
            True if tax data was finalized, False if not available

        Note:
            Requires tax_service to be configured.
        """
        if not self.tax_service or not self.invoice_repo:
            return False

        try:
            invoice = self.invoice_repo.find_by_payment_hash(payment_hash)
            if not invoice:
                return False

            # Skip if no tax data was stored during creation
            if not invoice.eur_amount_declared or not invoice.btc_eur_rate:
                return False

            # Calculate and store capital gain
            if invoice.acquisition_cost_eur is not None:
                capital_gain = invoice.eur_amount_declared - invoice.acquisition_cost_eur
                invoice.capital_gain_eur = capital_gain
                self.invoice_repo.save(invoice)

                # Publish taxable event if gain is positive
                if capital_gain > 0:
                    await self.tax_service.store_tax_data_for_payment(
                        payment_hash=payment_hash,
                        btc_eur_rate=invoice.btc_eur_rate,
                        eur_amount=invoice.eur_amount_declared,
                        acquisition_cost_eur=invoice.acquisition_cost_eur,
                        publish_events=True,
                    )

            return True

        except Exception as e:
            print(f"Error finalizing tax data for {payment_hash}: {e}")
            return False

    async def calculate_fees_estimate(self, amount_msat: int, description: str = "") -> dict:
        """Estimate fees for a Lightning payment.

        This provides a rough estimate based on typical routing fees.
        In production, you would query the Lightning network for actual routes.

        Args:
            amount_msat: Payment amount in millisatoshis
            description: Optional payment description

        Returns:
            Dictionary with fee estimates
        """
        # Typical Lightning fees: 0.01-0.1% of payment amount
        amount_sat = amount_msat / 1000
        min_fee_sat = max(1, int(amount_sat * 0.0001))  # 0.01%
        max_fee_sat = max(10, int(amount_sat * 0.001))  # 0.1%

        return {
            "estimated_min_fee_sat": min_fee_sat,
            "estimated_max_fee_sat": max_fee_sat,
            "estimated_min_fee_eur": float(
                Decimal(str(min_fee_sat))
                / Decimal("100000000")
                * await self.btc_converter.convert_btc_to_eur(Decimal("1"))
            ),
            "estimated_max_fee_eur": float(
                Decimal(str(max_fee_sat))
                / Decimal("100000000")
                * await self.btc_converter.convert_btc_to_eur(Decimal("1"))
            ),
            "typical_success_rate": 0.95,  # 95% success rate for well-connected nodes
        }


def create_lightning_invoice_service(
    settings: Settings | None = None,
    enable_tax_tracking: bool = True,
) -> LightningInvoiceService:
    """Factory function to create Lightning invoice service from settings.

    Args:
        settings: Application settings (uses get_settings() if None)
        enable_tax_tracking: Whether to enable Italian tax compliance tracking

    Returns:
        Configured LightningInvoiceService instance
    """
    if settings is None:
        settings = get_settings()

    # Create LND client
    lnd_client = LNDClient(
        host=settings.lightning_host,
        cert_path=settings.lightning_cert_path,
        macaroon_path=settings.lightning_macaroon_path,
        timeout_seconds=settings.lightning_timeout_seconds,
        max_retries=settings.lightning_max_retries,
        circuit_breaker_failures=settings.lightning_circuit_breaker_failures,
        circuit_breaker_timeout=settings.lightning_circuit_breaker_timeout,
    )

    # Create BTC converter
    btc_converter = create_btc_conversion_service(settings)

    # Optionally create tax service and repository (avoid circular imports)
    tax_service = None
    invoice_repo = None

    if enable_tax_tracking:
        try:
            # Lazy import to avoid circular dependency
            from openfatture.lightning.application.services.tax_calculation_service import (
                create_tax_calculation_service,
            )
            from openfatture.lightning.infrastructure.repository import (
                LightningInvoiceRepository,
            )

            invoice_repo = LightningInvoiceRepository()
            tax_service = create_tax_calculation_service(
                invoice_repository=invoice_repo,
                aml_threshold_eur=getattr(
                    settings, "lightning_aml_threshold_eur", Decimal("5000.00")
                ),
            )
        except ImportError:
            # Tax tracking dependencies not available
            pass

    return LightningInvoiceService(
        lnd_client=lnd_client,
        btc_converter=btc_converter,
        default_expiry_hours=settings.lightning_default_expiry_hours,
        tax_service=tax_service,
        invoice_repository=invoice_repo,
    )
