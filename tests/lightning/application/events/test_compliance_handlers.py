"""Tests for compliance event handlers."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from openfatture.lightning.application.events.handlers import (
    LightningAMLAlertEventHandler,
    LightningAMLVerifiedHandler,
    LightningPaymentTaxableEventHandler,
    LightningTaxDataStoredHandler,
)
from openfatture.lightning.domain.enums import InvoiceStatus
from openfatture.lightning.domain.events import (
    LightningAMLAlertEvent,
    LightningAMLVerified,
    LightningPaymentTaxableEvent,
    LightningTaxDataStored,
)
from openfatture.lightning.domain.models import LightningInvoiceRecord
from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository


@pytest.fixture
def invoice_repo(db_session):
    """Create invoice repository fixture."""
    return LightningInvoiceRepository(session=db_session)


@pytest.fixture
def sample_invoice(db_session, invoice_repo):
    """Create sample invoice for testing."""
    invoice = LightningInvoiceRecord(
        payment_hash="a" * 64,
        payment_request="lnbc1000..." * 10,
        amount_msat=100000000,
        description="Test payment",
        expiry_timestamp=int((datetime.now(UTC) + timedelta(hours=24)).timestamp()),
        status=InvoiceStatus.SETTLED,
        settled_at=datetime(2025, 6, 15, tzinfo=UTC),
        preimage="b" * 64,
    )
    invoice.store_tax_data(
        btc_eur_rate=Decimal("50000.00"),
        eur_amount=Decimal("2000.00"),
        acquisition_cost_eur=Decimal("1500.00"),
    )
    invoice_repo.save(invoice)
    return invoice


# ============================================================================
# LightningPaymentTaxableEventHandler Tests
# ============================================================================


@pytest.mark.asyncio
async def test_taxable_event_handler_basic(db_session, invoice_repo, sample_invoice):
    """Test basic taxable event handling."""
    handler = LightningPaymentTaxableEventHandler(session=db_session)

    event = LightningPaymentTaxableEvent(
        payment_hash=sample_invoice.payment_hash,
        payment_amount_eur=2000.0,
        capital_gain_eur=500.0,
        tax_year=2025,
        requires_quadro_rw=True,
        exceeds_aml_threshold=False,
        fattura_id=None,
    )

    # Should not raise
    await handler.handle(event)


@pytest.mark.asyncio
async def test_taxable_event_handler_invoice_not_found(db_session):
    """Test handling when invoice not found."""
    handler = LightningPaymentTaxableEventHandler(session=db_session)

    event = LightningPaymentTaxableEvent(
        payment_hash="nonexistent" + "f" * 53,
        payment_amount_eur=2000.0,
        capital_gain_eur=500.0,
        tax_year=2025,
        requires_quadro_rw=True,
        exceeds_aml_threshold=False,
    )

    # Should not raise (logs warning)
    await handler.handle(event)


@pytest.mark.asyncio
async def test_taxable_event_handler_significant_capital_gain(
    db_session, invoice_repo, sample_invoice
):
    """Test handling of significant capital gain (>1000 EUR)."""
    handler = LightningPaymentTaxableEventHandler(session=db_session)

    event = LightningPaymentTaxableEvent(
        payment_hash=sample_invoice.payment_hash,
        payment_amount_eur=10000.0,
        capital_gain_eur=1500.0,  # Triggers notification
        tax_year=2025,
        requires_quadro_rw=True,
        exceeds_aml_threshold=False,
    )

    with patch.object(handler, "_notify_significant_capital_gain", new=AsyncMock()) as mock_notify:
        await handler.handle(event)
        mock_notify.assert_called_once()


@pytest.mark.asyncio
async def test_taxable_event_handler_quadro_rw_reminder(db_session, invoice_repo, sample_invoice):
    """Test Quadro RW reminder triggering."""
    handler = LightningPaymentTaxableEventHandler(session=db_session)

    event = LightningPaymentTaxableEvent(
        payment_hash=sample_invoice.payment_hash,
        payment_amount_eur=2000.0,
        capital_gain_eur=500.0,
        tax_year=2025,
        requires_quadro_rw=True,  # Should trigger reminder
        exceeds_aml_threshold=False,
    )

    with patch.object(handler, "_trigger_quadro_rw_reminder", new=AsyncMock()) as mock_trigger:
        await handler.handle(event)
        mock_trigger.assert_called_once()


# ============================================================================
# LightningAMLAlertEventHandler Tests
# ============================================================================


@pytest.mark.asyncio
async def test_aml_alert_handler_basic(db_session, invoice_repo, sample_invoice):
    """Test basic AML alert handling."""
    handler = LightningAMLAlertEventHandler(session=db_session)

    event = LightningAMLAlertEvent(
        payment_hash=sample_invoice.payment_hash,
        amount_eur=6000.0,
        threshold_eur=5000.0,
        client_id=1,
        client_name="Test Client",
        verification_required=True,
        already_verified=False,
    )

    await handler.handle(event)


@pytest.mark.asyncio
async def test_aml_alert_handler_verification_required(db_session, invoice_repo, sample_invoice):
    """Test AML alert with verification required."""
    handler = LightningAMLAlertEventHandler(session=db_session)

    event = LightningAMLAlertEvent(
        payment_hash=sample_invoice.payment_hash,
        amount_eur=6000.0,
        threshold_eur=5000.0,
        client_id=1,
        client_name="Test Client",
        verification_required=True,
        already_verified=False,
    )

    with patch.object(
        handler, "_trigger_aml_verification_workflow", new=AsyncMock()
    ) as mock_trigger:
        await handler.handle(event)
        mock_trigger.assert_called_once()


@pytest.mark.asyncio
async def test_aml_alert_handler_already_verified(db_session, invoice_repo, sample_invoice):
    """Test AML alert when already verified."""
    handler = LightningAMLAlertEventHandler(session=db_session)

    event = LightningAMLAlertEvent(
        payment_hash=sample_invoice.payment_hash,
        amount_eur=6000.0,
        threshold_eur=5000.0,
        client_id=1,
        client_name="Test Client",
        verification_required=False,
        already_verified=True,
    )

    with patch.object(
        handler, "_trigger_aml_verification_workflow", new=AsyncMock()
    ) as mock_trigger:
        await handler.handle(event)
        mock_trigger.assert_not_called()


@pytest.mark.asyncio
async def test_aml_alert_handler_audit_logging(db_session, invoice_repo, sample_invoice):
    """Test AML alert audit logging."""
    handler = LightningAMLAlertEventHandler(session=db_session)

    event = LightningAMLAlertEvent(
        payment_hash=sample_invoice.payment_hash,
        amount_eur=6000.0,
        threshold_eur=5000.0,
        client_id=1,
        client_name="Test Client",
        verification_required=True,
        already_verified=False,
        fattura_id=42,
    )

    with patch.object(handler, "_log_aml_alert_for_audit", new=AsyncMock()) as mock_log:
        await handler.handle(event)
        mock_log.assert_called_once()


# ============================================================================
# LightningTaxDataStoredHandler Tests
# ============================================================================


@pytest.mark.asyncio
async def test_tax_data_stored_handler_basic(db_session, invoice_repo, sample_invoice):
    """Test basic tax data stored handling."""
    handler = LightningTaxDataStoredHandler(session=db_session)

    event = LightningTaxDataStored(
        payment_hash=sample_invoice.payment_hash,
        btc_eur_rate=50000.0,
        eur_amount_declared=2000.0,
        acquisition_cost_eur=1500.0,
        capital_gain_eur=500.0,
        tax_year=2025,
    )

    await handler.handle(event)


@pytest.mark.asyncio
async def test_tax_data_stored_handler_consistency_check(db_session, invoice_repo, sample_invoice):
    """Test tax data consistency verification."""
    handler = LightningTaxDataStoredHandler(session=db_session)

    event = LightningTaxDataStored(
        payment_hash=sample_invoice.payment_hash,
        btc_eur_rate=50000.0,  # Matches sample_invoice
        eur_amount_declared=2000.0,
        acquisition_cost_eur=1500.0,
        capital_gain_eur=500.0,
        tax_year=2025,
    )

    with patch.object(handler, "_verify_tax_data_consistency", new=AsyncMock()) as mock_verify:
        await handler.handle(event)
        mock_verify.assert_called_once()


@pytest.mark.asyncio
async def test_tax_data_stored_handler_rate_mismatch_warning(
    db_session, invoice_repo, sample_invoice
):
    """Test warning when BTC/EUR rate mismatches."""
    handler = LightningTaxDataStoredHandler(session=db_session)

    # Create event with different rate
    event = LightningTaxDataStored(
        payment_hash=sample_invoice.payment_hash,
        btc_eur_rate=55000.0,  # Different from stored 50000.0
        eur_amount_declared=2000.0,
        acquisition_cost_eur=1500.0,
        capital_gain_eur=500.0,
        tax_year=2025,
    )

    # Should log warning but not raise
    await handler.handle(event)


# ============================================================================
# LightningAMLVerifiedHandler Tests
# ============================================================================


@pytest.mark.asyncio
async def test_aml_verified_handler_basic(db_session, invoice_repo, sample_invoice):
    """Test basic AML verification completion."""
    handler = LightningAMLVerifiedHandler(session=db_session)

    event = LightningAMLVerified(
        payment_hash=sample_invoice.payment_hash,
        verified_at=datetime.now(UTC),
        verified_by="compliance_officer@example.com",
        client_id=1,
        notes="Identity documents verified",
    )

    await handler.handle(event)

    # Verify invoice was marked as AML verified
    updated_invoice = invoice_repo.find_by_payment_hash(sample_invoice.payment_hash)
    assert updated_invoice.aml_verified is True
    assert updated_invoice.aml_verification_date is not None


@pytest.mark.asyncio
async def test_aml_verified_handler_invoice_not_found(db_session):
    """Test AML verification when invoice not found."""
    handler = LightningAMLVerifiedHandler(session=db_session)

    event = LightningAMLVerified(
        payment_hash="nonexistent" + "f" * 53,
        verified_at=datetime.now(UTC),
        verified_by="compliance_officer@example.com",
        client_id=1,
    )

    # Should not raise (logs error)
    await handler.handle(event)


@pytest.mark.asyncio
async def test_aml_verified_handler_updates_timestamp(db_session, invoice_repo, sample_invoice):
    """Test that AML verification updates timestamp."""
    handler = LightningAMLVerifiedHandler(session=db_session)

    verification_time = datetime.now(UTC)
    event = LightningAMLVerified(
        payment_hash=sample_invoice.payment_hash,
        verified_at=verification_time,
        verified_by="compliance_officer@example.com",
        client_id=1,
    )

    await handler.handle(event)

    updated_invoice = invoice_repo.find_by_payment_hash(sample_invoice.payment_hash)
    assert updated_invoice.aml_verification_date is not None
    # Should be close to verification_time (within a few seconds)
    # Ensure both are timezone-aware
    verification_date = updated_invoice.aml_verification_date
    if verification_date.tzinfo is None:
        verification_date = verification_date.replace(tzinfo=UTC)
    time_diff = abs((verification_date - verification_time).total_seconds())
    assert time_diff < 5  # Within 5 seconds


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_taxable_event_handler_error_handling(db_session, invoice_repo):
    """Test error handling in taxable event handler."""
    handler = LightningPaymentTaxableEventHandler(session=db_session)

    # Create event with invalid payment hash that will cause errors
    event = LightningPaymentTaxableEvent(
        payment_hash="invalid",  # Invalid hash
        payment_amount_eur=2000.0,
        capital_gain_eur=500.0,
        tax_year=2025,
        requires_quadro_rw=True,
        exceeds_aml_threshold=False,
    )

    # Should not raise, just log error
    await handler.handle(event)


@pytest.mark.asyncio
async def test_aml_alert_handler_error_handling(db_session):
    """Test error handling in AML alert handler."""
    handler = LightningAMLAlertEventHandler(session=db_session)

    event = LightningAMLAlertEvent(
        payment_hash="invalid",
        amount_eur=6000.0,
        threshold_eur=5000.0,
        client_id=1,
        client_name="Test Client",
        verification_required=True,
        already_verified=False,
    )

    # Should not raise
    await handler.handle(event)


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_multiple_handlers_for_same_invoice(db_session, invoice_repo, sample_invoice):
    """Test multiple handlers processing events for the same invoice."""
    # Create handlers
    taxable_handler = LightningPaymentTaxableEventHandler(session=db_session)
    aml_handler = LightningAMLAlertEventHandler(session=db_session)
    tax_data_handler = LightningTaxDataStoredHandler(session=db_session)
    aml_verified_handler = LightningAMLVerifiedHandler(session=db_session)

    # Simulate event sequence
    # 1. Tax data stored
    tax_data_event = LightningTaxDataStored(
        payment_hash=sample_invoice.payment_hash,
        btc_eur_rate=50000.0,
        eur_amount_declared=6000.0,
        acquisition_cost_eur=5000.0,
        capital_gain_eur=1000.0,
        tax_year=2025,
    )
    await tax_data_handler.handle(tax_data_event)

    # 2. Taxable event
    taxable_event = LightningPaymentTaxableEvent(
        payment_hash=sample_invoice.payment_hash,
        payment_amount_eur=6000.0,
        capital_gain_eur=1000.0,
        tax_year=2025,
        requires_quadro_rw=True,
        exceeds_aml_threshold=True,
    )
    await taxable_handler.handle(taxable_event)

    # 3. AML alert
    aml_event = LightningAMLAlertEvent(
        payment_hash=sample_invoice.payment_hash,
        amount_eur=6000.0,
        threshold_eur=5000.0,
        client_id=1,
        client_name="Test Client",
        verification_required=True,
        already_verified=False,
    )
    await aml_handler.handle(aml_event)

    # 4. AML verified
    aml_verified_event = LightningAMLVerified(
        payment_hash=sample_invoice.payment_hash,
        verified_at=datetime.now(UTC),
        verified_by="compliance@example.com",
        client_id=1,
    )
    await aml_verified_handler.handle(aml_verified_event)

    # Verify final state
    final_invoice = invoice_repo.find_by_payment_hash(sample_invoice.payment_hash)
    assert final_invoice.aml_verified is True
    assert final_invoice.btc_eur_rate == Decimal("50000.00")
