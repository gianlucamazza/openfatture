"""Tax calculation and compliance service for Lightning payments.

This service handles all tax-related calculations for Lightning Network payments
in accordance with Italian fiscal regulations (2025+).

Key responsibilities:
- Calculate capital gains/losses on BTC → EUR conversions
- Check Anti-Money Laundering (AML) thresholds
- Generate Quadro RW data for tax declarations
- Publish tax-related domain events
"""

from datetime import UTC, datetime
from decimal import Decimal

from openfatture.core.events.base import get_global_event_bus
from openfatture.lightning.domain.events import (
    LightningAMLAlertEvent,
    LightningPaymentTaxableEvent,
    LightningTaxDataStored,
)
from openfatture.lightning.domain.value_objects import CapitalGain, QuadroRWData
from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository


class TaxCalculationService:
    """Service for tax calculations and fiscal compliance.

    This service provides methods to:
    - Calculate capital gains for individual Lightning payments
    - Check if payments exceed AML thresholds
    - Generate annual tax reports (Quadro RW)
    - Track and publish tax-related events
    """

    def __init__(
        self,
        invoice_repository: LightningInvoiceRepository,
        aml_threshold_eur: Decimal = Decimal("5000.00"),
        enable_event_publishing: bool = True,
    ):
        """Initialize the tax calculation service.

        Args:
            invoice_repository: Repository for Lightning invoice records
            aml_threshold_eur: AML threshold in EUR (default 5,000)
            enable_event_publishing: Whether to publish events (disable for testing)
        """
        self.invoice_repo = invoice_repository
        self.aml_threshold_eur = aml_threshold_eur
        self.enable_events = enable_event_publishing
        self.event_bus = get_global_event_bus()

    async def calculate_capital_gain(
        self,
        payment_hash: str,
        btc_eur_rate: Decimal,
        eur_amount: Decimal,
        acquisition_cost_eur: Decimal | None = None,
    ) -> CapitalGain:
        """Calculate capital gain for a Lightning payment.

        Args:
            payment_hash: Payment hash of the Lightning invoice
            btc_eur_rate: BTC/EUR exchange rate at settlement
            eur_amount: EUR amount of the payment
            acquisition_cost_eur: Original BTC acquisition cost (if known)

        Returns:
            CapitalGain value object with tax information

        Raises:
            ValueError: If payment_hash is invalid or invoice not found
        """
        # Validate invoice exists
        invoice = self.invoice_repo.find_by_payment_hash(payment_hash)
        if not invoice:
            raise ValueError(f"Invoice not found: {payment_hash}")

        # Calculate gain/loss
        if acquisition_cost_eur is not None:
            gain_loss = eur_amount - acquisition_cost_eur
        else:
            # Unknown acquisition cost - cannot calculate gain
            gain_loss = Decimal("0")

        # Determine tax year
        tax_year = invoice.settled_at.year if invoice.settled_at else datetime.now(UTC).year

        # Create CapitalGain value object
        capital_gain = CapitalGain(
            payment_hash=payment_hash,
            acquisition_cost_eur=acquisition_cost_eur,
            sale_price_eur=eur_amount,
            gain_loss_eur=gain_loss,
            tax_year=tax_year,
        )

        return capital_gain

    async def store_tax_data_for_payment(
        self,
        payment_hash: str,
        btc_eur_rate: Decimal,
        eur_amount: Decimal,
        acquisition_cost_eur: Decimal | None = None,
        publish_events: bool = True,
    ) -> None:
        """Store tax data for a Lightning payment and publish events.

        This method:
        1. Stores tax-related data in the invoice record
        2. Calculates capital gain if acquisition cost is known
        3. Publishes tax-related events
        4. Checks AML threshold

        Args:
            payment_hash: Payment hash of the Lightning invoice
            btc_eur_rate: BTC/EUR exchange rate at settlement
            eur_amount: EUR amount of the payment
            acquisition_cost_eur: Original BTC acquisition cost (if known)
            publish_events: Whether to publish events (default True)

        Raises:
            ValueError: If invoice not found
        """
        # Find invoice
        invoice = self.invoice_repo.find_by_payment_hash(payment_hash)
        if not invoice:
            raise ValueError(f"Invoice not found: {payment_hash}")

        # Store tax data in invoice record
        invoice.store_tax_data(
            btc_eur_rate=btc_eur_rate,
            eur_amount=eur_amount,
            acquisition_cost_eur=acquisition_cost_eur,
        )

        # Check if exceeds AML threshold
        if eur_amount >= self.aml_threshold_eur:
            invoice.exceeds_aml_threshold = True

        # Save to database
        self.invoice_repo.save(invoice)

        # Publish events if enabled
        if publish_events and self.enable_events:
            await self._publish_tax_events(invoice, btc_eur_rate, eur_amount)

    async def check_aml_threshold(
        self,
        payment_hash: str,
        amount_eur: Decimal,
        client_id: int | None = None,
        client_name: str | None = None,
    ) -> bool:
        """Check if a payment exceeds the AML threshold.

        Args:
            payment_hash: Payment hash
            amount_eur: Payment amount in EUR
            client_id: Optional client ID
            client_name: Optional client name

        Returns:
            True if threshold exceeded, False otherwise
        """
        exceeds_threshold = amount_eur >= self.aml_threshold_eur

        if exceeds_threshold and self.enable_events:
            # Find invoice to check if already verified
            invoice = self.invoice_repo.find_by_payment_hash(payment_hash)
            already_verified = invoice.aml_verified if invoice else False

            # Publish AML alert event
            event = LightningAMLAlertEvent(
                payment_hash=payment_hash,
                amount_eur=float(amount_eur),
                threshold_eur=float(self.aml_threshold_eur),
                client_id=client_id,
                client_name=client_name,
                verification_required=not already_verified,
                already_verified=already_verified,
                fattura_id=invoice.fattura_id if invoice else None,
            )
            await self.event_bus.publish_async(event)

        return exceeds_threshold

    async def generate_quadro_rw_data(
        self,
        tax_year: int,
    ) -> QuadroRWData:
        """Generate Quadro RW data for a specific tax year.

        Quadro RW (Monitoraggio fiscale) is required for declaring
        crypto-asset holdings to Italian tax authorities.

        Args:
            tax_year: Tax year (e.g., 2025)

        Returns:
            QuadroRWData with aggregated holdings and transactions
        """
        # Get all settled invoices in the tax year
        start_date = datetime(tax_year, 1, 1, tzinfo=UTC)
        end_date = datetime(tax_year, 12, 31, 23, 59, 59, tzinfo=UTC)

        invoices = self.invoice_repo.find_settled_in_date_range(start_date, end_date)

        # Calculate totals
        total_inflows = Decimal("0")
        total_outflows = Decimal("0")
        num_transactions = len(invoices)

        for invoice in invoices:
            if invoice.eur_amount_declared:
                # Lightning payments are outflows (BTC → EUR)
                total_outflows += invoice.eur_amount_declared

        # For Lightning, we receive BTC by creating invoices
        # So holdings = accumulated received - accumulated spent
        # This is simplified - in production, integrate with wallet balance
        total_holdings = Decimal("0")  # Placeholder
        average_holdings = Decimal("0")  # Placeholder

        # Create QuadroRWData
        quadro_rw = QuadroRWData(
            tax_year=tax_year,
            total_holdings_eur=total_holdings,
            average_holdings_eur=average_holdings,
            num_transactions=num_transactions,
            total_inflows_eur=total_inflows,
            total_outflows_eur=total_outflows,
        )

        return quadro_rw

    async def get_taxable_payments_for_year(
        self,
        tax_year: int,
    ) -> list[dict]:
        """Get all payments with taxable capital gains for a year.

        Args:
            tax_year: Tax year to query

        Returns:
            List of dictionaries with payment and tax data
        """
        # Get taxable invoices from repository
        # Note: We'll need to add this method to the repository
        # For now, use date range query
        start_date = datetime(tax_year, 1, 1, tzinfo=UTC)
        end_date = datetime(tax_year, 12, 31, 23, 59, 59, tzinfo=UTC)

        all_invoices = self.invoice_repo.find_settled_in_date_range(start_date, end_date)

        # Filter to only taxable payments
        taxable_payments = []
        for invoice in all_invoices:
            if invoice.has_taxable_capital_gain:
                taxable_payments.append(
                    {
                        "payment_hash": invoice.payment_hash,
                        "settled_at": invoice.settled_at,
                        "eur_amount": (
                            float(invoice.eur_amount_declared)
                            if invoice.eur_amount_declared
                            else 0.0
                        ),
                        "capital_gain_eur": (
                            float(invoice.capital_gain_eur) if invoice.capital_gain_eur else 0.0
                        ),
                        "btc_eur_rate": (
                            float(invoice.btc_eur_rate) if invoice.btc_eur_rate else 0.0
                        ),
                        "tax_year": tax_year,
                        "fattura_id": invoice.fattura_id,
                    }
                )

        return taxable_payments

    async def calculate_total_tax_owed(
        self,
        tax_year: int,
    ) -> Decimal:
        """Calculate total tax owed on capital gains for a year.

        Args:
            tax_year: Tax year

        Returns:
            Total tax owed in EUR
        """
        taxable_payments = await self.get_taxable_payments_for_year(tax_year)

        total_gain = Decimal("0")
        for payment in taxable_payments:
            total_gain += Decimal(str(payment["capital_gain_eur"]))

        # Determine tax rate based on year
        if tax_year <= 2025:
            tax_rate = Decimal("0.26")  # 26%
        else:
            tax_rate = Decimal("0.33")  # 33%

        total_tax = (total_gain * tax_rate).quantize(Decimal("0.01"))
        return total_tax

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    async def _publish_tax_events(
        self,
        invoice,
        btc_eur_rate: Decimal,
        eur_amount: Decimal,
    ) -> None:
        """Publish tax-related events for an invoice.

        Args:
            invoice: LightningInvoiceRecord entity
            btc_eur_rate: BTC/EUR rate
            eur_amount: EUR amount
        """
        # Publish TaxDataStored event
        stored_event = LightningTaxDataStored(
            payment_hash=invoice.payment_hash,
            btc_eur_rate=float(btc_eur_rate),
            eur_amount_declared=float(eur_amount),
            acquisition_cost_eur=(
                float(invoice.acquisition_cost_eur) if invoice.acquisition_cost_eur else None
            ),
            capital_gain_eur=(
                float(invoice.capital_gain_eur) if invoice.capital_gain_eur else None
            ),
            tax_year=invoice.tax_year,
        )
        await self.event_bus.publish_async(stored_event)

        # If has taxable gain, publish PaymentTaxableEvent
        if invoice.has_taxable_capital_gain:
            taxable_event = LightningPaymentTaxableEvent(
                payment_hash=invoice.payment_hash,
                payment_amount_eur=float(eur_amount),
                capital_gain_eur=(
                    float(invoice.capital_gain_eur) if invoice.capital_gain_eur else None
                ),
                tax_year=invoice.tax_year or datetime.now(UTC).year,
                requires_quadro_rw=True,  # Always required from 2025
                exceeds_aml_threshold=invoice.exceeds_aml_threshold,
                fattura_id=invoice.fattura_id,
            )
            await self.event_bus.publish_async(taxable_event)


def create_tax_calculation_service(
    invoice_repository: LightningInvoiceRepository | None = None,
    aml_threshold_eur: Decimal = Decimal("5000.00"),
) -> TaxCalculationService:
    """Factory function to create TaxCalculationService.

    Args:
        invoice_repository: Optional repository (creates default if None)
        aml_threshold_eur: AML threshold in EUR

    Returns:
        Configured TaxCalculationService instance
    """
    if invoice_repository is None:
        invoice_repository = LightningInvoiceRepository()

    return TaxCalculationService(
        invoice_repository=invoice_repository,
        aml_threshold_eur=aml_threshold_eur,
        enable_event_publishing=True,
    )
