"""Tests for Lightning repository compliance queries."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from openfatture.lightning.domain.enums import InvoiceStatus
from openfatture.lightning.domain.models import LightningInvoiceRecord
from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository


@pytest.fixture
def invoice_repo(db_session):
    """Create invoice repository fixture."""
    return LightningInvoiceRepository(session=db_session)


@pytest.fixture
def sample_invoices_compliance(db_session, invoice_repo):
    """Create sample invoices for compliance testing."""
    invoices = []

    # Invoice 1: Below AML threshold, 2025, with capital gain
    inv1 = LightningInvoiceRecord(
        payment_hash="a" * 64,
        payment_request="lnbc1" * 20,
        amount_msat=100000000,
        description="Payment 1",
        expiry_timestamp=int((datetime.now(UTC) + timedelta(hours=24)).timestamp()),
        status=InvoiceStatus.SETTLED,
        settled_at=datetime(2025, 3, 15, tzinfo=UTC),
        preimage="b" * 64,
    )
    inv1.store_tax_data(
        btc_eur_rate=Decimal("50000.00"),
        eur_amount=Decimal("2000.00"),
        acquisition_cost_eur=Decimal("1500.00"),
    )
    invoice_repo.save(inv1)
    invoices.append(inv1)

    # Invoice 2: Above AML threshold, 2025, not verified
    inv2 = LightningInvoiceRecord(
        payment_hash="c" * 64,
        payment_request="lnbc2" * 20,
        amount_msat=500000000,
        description="Payment 2",
        expiry_timestamp=int((datetime.now(UTC) + timedelta(hours=24)).timestamp()),
        status=InvoiceStatus.SETTLED,
        settled_at=datetime(2025, 6, 20, tzinfo=UTC),
        preimage="d" * 64,
    )
    inv2.store_tax_data(
        btc_eur_rate=Decimal("55000.00"),
        eur_amount=Decimal("6000.00"),
        acquisition_cost_eur=Decimal("5000.00"),
    )
    inv2.exceeds_aml_threshold = True
    invoice_repo.save(inv2)
    invoices.append(inv2)

    # Invoice 3: Above AML threshold, 2025, verified
    inv3 = LightningInvoiceRecord(
        payment_hash="e" * 64,
        payment_request="lnbc3" * 20,
        amount_msat=800000000,
        description="Payment 3",
        expiry_timestamp=int((datetime.now(UTC) + timedelta(hours=24)).timestamp()),
        status=InvoiceStatus.SETTLED,
        settled_at=datetime(2025, 9, 10, tzinfo=UTC),
        preimage="f" * 64,
    )
    inv3.store_tax_data(
        btc_eur_rate=Decimal("60000.00"),
        eur_amount=Decimal("8000.00"),
        acquisition_cost_eur=Decimal("7000.00"),
    )
    inv3.exceeds_aml_threshold = True
    inv3.mark_aml_verified()
    invoice_repo.save(inv3)
    invoices.append(inv3)

    # Invoice 4: 2024 invoice (for tax year filtering)
    inv4 = LightningInvoiceRecord(
        payment_hash="1" * 64,
        payment_request="lnbc4" * 20,
        amount_msat=200000000,
        description="Payment 2024",
        expiry_timestamp=int((datetime.now(UTC) + timedelta(hours=24)).timestamp()),
        status=InvoiceStatus.SETTLED,
        settled_at=datetime(2024, 12, 31, tzinfo=UTC),
        preimage="2" * 64,
    )
    inv4.store_tax_data(
        btc_eur_rate=Decimal("45000.00"),
        eur_amount=Decimal("3000.00"),
        acquisition_cost_eur=Decimal("2500.00"),
    )
    invoice_repo.save(inv4)
    invoices.append(inv4)

    # Invoice 5: Settled but missing tax data
    inv5 = LightningInvoiceRecord(
        payment_hash="3" * 64,
        payment_request="lnbc5" * 20,
        amount_msat=150000000,
        description="Payment no tax data",
        expiry_timestamp=int((datetime.now(UTC) + timedelta(hours=24)).timestamp()),
        status=InvoiceStatus.SETTLED,
        settled_at=datetime(2025, 1, 10, tzinfo=UTC),
        preimage="4" * 64,
    )
    # No tax data stored
    invoice_repo.save(inv5)
    invoices.append(inv5)

    # Invoice 6: Pending (not settled)
    inv6 = LightningInvoiceRecord(
        payment_hash="5" * 64,
        payment_request="lnbc6" * 20,
        amount_msat=100000000,
        description="Payment pending",
        expiry_timestamp=int((datetime.now(UTC) + timedelta(hours=24)).timestamp()),
        status=InvoiceStatus.PENDING,
    )
    invoice_repo.save(inv6)
    invoices.append(inv6)

    return invoices


# ============================================================================
# AML THRESHOLD QUERIES
# ============================================================================


def test_find_exceeding_aml_threshold(invoice_repo, sample_invoices_compliance):
    """Test finding invoices exceeding AML threshold."""
    results = invoice_repo.find_exceeding_aml_threshold(threshold_eur=5000.0)

    # Should find inv2 (6000 EUR) and inv3 (8000 EUR)
    assert len(results) == 2
    payment_hashes = [inv.payment_hash for inv in results]
    assert "c" * 64 in payment_hashes
    assert "e" * 64 in payment_hashes


def test_find_exceeding_aml_threshold_custom_threshold(invoice_repo, sample_invoices_compliance):
    """Test AML threshold query with custom threshold."""
    results = invoice_repo.find_exceeding_aml_threshold(threshold_eur=7000.0)

    # Only inv3 (8000 EUR) exceeds 7000
    assert len(results) == 1
    assert results[0].payment_hash == "e" * 64


def test_find_unverified_aml_payments(invoice_repo, sample_invoices_compliance):
    """Test finding unverified AML payments."""
    results = invoice_repo.find_unverified_aml_payments(threshold_eur=5000.0)

    # Should find only inv2 (6000 EUR, not verified)
    # inv3 is verified, so excluded
    assert len(results) == 1
    assert results[0].payment_hash == "c" * 64
    assert results[0].aml_verified is False


def test_count_by_aml_status(invoice_repo, sample_invoices_compliance):
    """Test counting invoices by AML status."""
    counts = invoice_repo.count_by_aml_status(threshold_eur=5000.0)

    assert counts["total_over_threshold"] == 2  # inv2, inv3
    assert counts["verified"] == 1  # inv3
    assert counts["unverified"] == 1  # inv2


# ============================================================================
# CAPITAL GAINS QUERIES
# ============================================================================


def test_find_with_capital_gains_all(invoice_repo, sample_invoices_compliance):
    """Test finding all invoices with capital gains."""
    results = invoice_repo.find_with_capital_gains()

    # Should find inv1, inv2, inv3, inv4 (all with capital_gain_eur set)
    assert len(results) == 4
    payment_hashes = [inv.payment_hash for inv in results]
    assert "a" * 64 in payment_hashes
    assert "c" * 64 in payment_hashes
    assert "e" * 64 in payment_hashes
    assert "1" * 64 in payment_hashes


def test_find_with_capital_gains_by_year(invoice_repo, sample_invoices_compliance):
    """Test finding capital gains for specific tax year."""
    results = invoice_repo.find_with_capital_gains(tax_year=2025)

    # Should find inv1, inv2, inv3 (2025 only)
    assert len(results) == 3
    payment_hashes = [inv.payment_hash for inv in results]
    assert "a" * 64 in payment_hashes
    assert "c" * 64 in payment_hashes
    assert "e" * 64 in payment_hashes
    assert "1" * 64 not in payment_hashes  # 2024


def test_find_with_capital_gains_2024(invoice_repo, sample_invoices_compliance):
    """Test finding capital gains for 2024."""
    results = invoice_repo.find_with_capital_gains(tax_year=2024)

    # Should find only inv4 (2024)
    assert len(results) == 1
    assert results[0].payment_hash == "1" * 64


# ============================================================================
# QUADRO RW QUERIES
# ============================================================================


def test_find_requiring_quadro_rw(invoice_repo, sample_invoices_compliance):
    """Test finding invoices requiring Quadro RW declaration."""
    results = invoice_repo.find_requiring_quadro_rw(tax_year=2025)

    # Should find all settled 2025 invoices with EUR amount
    # inv1, inv2, inv3 (inv5 has no EUR amount)
    assert len(results) == 3
    payment_hashes = [inv.payment_hash for inv in results]
    assert "a" * 64 in payment_hashes
    assert "c" * 64 in payment_hashes
    assert "e" * 64 in payment_hashes


def test_find_requiring_quadro_rw_2024(invoice_repo, sample_invoices_compliance):
    """Test Quadro RW for 2024."""
    results = invoice_repo.find_requiring_quadro_rw(tax_year=2024)

    # Should find only inv4
    assert len(results) == 1
    assert results[0].payment_hash == "1" * 64


# ============================================================================
# TAX YEAR QUERIES
# ============================================================================


def test_find_by_tax_year_2025(invoice_repo, sample_invoices_compliance):
    """Test finding invoices by tax year 2025."""
    results = invoice_repo.find_by_tax_year(tax_year=2025)

    # Should find inv1, inv2, inv3, inv5 (all settled in 2025)
    assert len(results) == 4
    payment_hashes = [inv.payment_hash for inv in results]
    assert "a" * 64 in payment_hashes
    assert "c" * 64 in payment_hashes
    assert "e" * 64 in payment_hashes
    assert "3" * 64 in payment_hashes  # inv5


def test_find_by_tax_year_2024(invoice_repo, sample_invoices_compliance):
    """Test finding invoices by tax year 2024."""
    results = invoice_repo.find_by_tax_year(tax_year=2024)

    # Should find only inv4
    assert len(results) == 1
    assert results[0].payment_hash == "1" * 64


def test_find_by_tax_year_empty(invoice_repo, sample_invoices_compliance):
    """Test finding invoices for year with no data."""
    results = invoice_repo.find_by_tax_year(tax_year=2023)

    assert len(results) == 0


# ============================================================================
# MISSING TAX DATA QUERIES
# ============================================================================


def test_find_with_missing_tax_data(invoice_repo, sample_invoices_compliance):
    """Test finding invoices with missing tax data."""
    results = invoice_repo.find_with_missing_tax_data()

    # Should find only inv5 (settled but no tax data)
    assert len(results) == 1
    assert results[0].payment_hash == "3" * 64
    assert results[0].btc_eur_rate is None
    assert results[0].eur_amount_declared is None


def test_find_with_missing_tax_data_excludes_pending(invoice_repo, sample_invoices_compliance):
    """Test that pending invoices are excluded from missing tax data."""
    results = invoice_repo.find_with_missing_tax_data()

    # inv6 is pending, should not appear
    payment_hashes = [inv.payment_hash for inv in results]
    assert "5" * 64 not in payment_hashes


# ============================================================================
# EDGE CASES & COMBINATIONS
# ============================================================================


def test_aml_threshold_zero_returns_all_settled(invoice_repo, sample_invoices_compliance):
    """Test that zero threshold returns all settled with EUR amount."""
    results = invoice_repo.find_exceeding_aml_threshold(threshold_eur=0.0)

    # Should find all settled invoices with EUR amount
    # inv1, inv2, inv3, inv4 (inv5 has no EUR amount)
    assert len(results) == 4


def test_aml_threshold_very_high_returns_none(invoice_repo, sample_invoices_compliance):
    """Test that very high threshold returns no results."""
    results = invoice_repo.find_exceeding_aml_threshold(threshold_eur=100000.0)

    assert len(results) == 0


def test_capital_gains_filter_excludes_pending(invoice_repo, sample_invoices_compliance):
    """Test that pending invoices are excluded from capital gains query."""
    results = invoice_repo.find_with_capital_gains()

    # inv6 is pending, should not appear
    payment_hashes = [inv.payment_hash for inv in results]
    assert "5" * 64 not in payment_hashes


def test_repository_queries_with_empty_database(invoice_repo):
    """Test all repository queries with empty database."""
    # All queries should return empty lists
    assert invoice_repo.find_exceeding_aml_threshold() == []
    assert invoice_repo.find_unverified_aml_payments() == []
    assert invoice_repo.find_with_capital_gains() == []
    assert invoice_repo.find_requiring_quadro_rw(2025) == []
    assert invoice_repo.find_by_tax_year(2025) == []
    assert invoice_repo.find_with_missing_tax_data() == []

    # Count should return zeros
    counts = invoice_repo.count_by_aml_status()
    assert counts["total_over_threshold"] == 0
    assert counts["verified"] == 0
    assert counts["unverified"] == 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_compliance_workflow_integration(invoice_repo, sample_invoices_compliance):
    """Test complete compliance workflow using repository queries."""
    # Step 1: Find all invoices requiring Quadro RW for 2025
    quadro_rw_invoices = invoice_repo.find_requiring_quadro_rw(2025)
    assert len(quadro_rw_invoices) == 3

    # Step 2: Find invoices with capital gains for tax calculation
    capital_gains = invoice_repo.find_with_capital_gains(tax_year=2025)
    assert len(capital_gains) == 3

    # Step 3: Check AML compliance
    aml_counts = invoice_repo.count_by_aml_status(5000.0)
    assert aml_counts["unverified"] == 1

    # Step 4: Find unverified payments for compliance officer
    unverified = invoice_repo.find_unverified_aml_payments(5000.0)
    assert len(unverified) == 1

    # Step 5: Find invoices with missing tax data
    missing_data = invoice_repo.find_with_missing_tax_data()
    assert len(missing_data) == 1


def test_tax_year_boundary_conditions(db_session, invoice_repo):
    """Test tax year queries at year boundaries."""
    # Create invoice on last day of 2025
    inv_2025_end = LightningInvoiceRecord(
        payment_hash="a" * 64,
        payment_request="lnbc" * 20,
        amount_msat=100000000,
        description="End of year",
        expiry_timestamp=int((datetime.now(UTC) + timedelta(hours=24)).timestamp()),
        status=InvoiceStatus.SETTLED,
        settled_at=datetime(2025, 12, 31, 23, 59, 59, tzinfo=UTC),
        preimage="b" * 64,
    )
    inv_2025_end.store_tax_data(btc_eur_rate=Decimal("50000.00"), eur_amount=Decimal("1000.00"))
    invoice_repo.save(inv_2025_end)

    # Create invoice on first day of 2026
    inv_2026_start = LightningInvoiceRecord(
        payment_hash="c" * 64,
        payment_request="lnbc" * 20,
        amount_msat=100000000,
        description="Start of year",
        expiry_timestamp=int((datetime.now(UTC) + timedelta(hours=24)).timestamp()),
        status=InvoiceStatus.SETTLED,
        settled_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
        preimage="d" * 64,
    )
    inv_2026_start.store_tax_data(btc_eur_rate=Decimal("50000.00"), eur_amount=Decimal("1000.00"))
    invoice_repo.save(inv_2026_start)

    # Query 2025
    results_2025 = invoice_repo.find_by_tax_year(2025)
    assert len(results_2025) == 1
    assert results_2025[0].payment_hash == "a" * 64

    # Query 2026
    results_2026 = invoice_repo.find_by_tax_year(2026)
    assert len(results_2026) == 1
    assert results_2026[0].payment_hash == "c" * 64
