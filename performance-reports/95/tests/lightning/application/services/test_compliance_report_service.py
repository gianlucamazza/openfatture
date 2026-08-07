"""Tests for ComplianceReportService."""

import csv
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from io import StringIO

import pytest

from openfatture.lightning.application.services.compliance_report_service import (
    AMLComplianceReport,
    ComplianceReportService,
    TaxYearSummary,
    create_compliance_report_service,
)
from openfatture.lightning.application.services.tax_calculation_service import (
    TaxCalculationService,
)
from openfatture.lightning.domain.enums import InvoiceStatus
from openfatture.lightning.domain.models import LightningInvoiceRecord
from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository


@pytest.fixture
def invoice_repo(db_session):
    """Create invoice repository fixture."""
    return LightningInvoiceRepository(session=db_session)


@pytest.fixture
def tax_service(invoice_repo):
    """Create tax service fixture."""
    return TaxCalculationService(
        invoice_repository=invoice_repo, aml_threshold_eur=Decimal("5000.00")
    )


@pytest.fixture
def compliance_service(tax_service, invoice_repo):
    """Create compliance report service fixture."""
    return ComplianceReportService(tax_service=tax_service, invoice_repository=invoice_repo)


@pytest.fixture
def sample_invoices_2025(db_session, invoice_repo):
    """Create sample invoices for testing."""
    invoices = []

    # Invoice 1: Below AML threshold, with capital gain
    inv1 = LightningInvoiceRecord(
        payment_hash="a" * 64,
        payment_request="lnbc1000..." * 10,
        amount_msat=100000000,  # 100 sats
        description="Test payment 1",
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

    # Invoice 2: Above AML threshold, not verified
    inv2 = LightningInvoiceRecord(
        payment_hash="c" * 64,
        payment_request="lnbc5000..." * 10,
        amount_msat=500000000,  # 500 sats
        description="Test payment 2",
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

    # Invoice 3: Above AML threshold, verified
    inv3 = LightningInvoiceRecord(
        payment_hash="e" * 64,
        payment_request="lnbc8000..." * 10,
        amount_msat=800000000,  # 800 sats
        description="Test payment 3",
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

    # Invoice 4: 2024 invoice (should not appear in 2025 reports)
    inv4 = LightningInvoiceRecord(
        payment_hash="1" * 64,
        payment_request="lnbc2000..." * 10,
        amount_msat=200000000,
        description="Test payment 2024",
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

    return invoices


# ============================================================================
# FACTORY FUNCTION TESTS
# ============================================================================


def test_create_compliance_report_service_defaults(db_session):
    """Test factory function with default parameters."""
    # Need to provide a session-based repository to avoid database initialization errors
    repo = LightningInvoiceRepository(session=db_session)
    service = create_compliance_report_service(invoice_repository=repo)

    assert isinstance(service, ComplianceReportService)
    assert isinstance(service.tax_service, TaxCalculationService)
    assert isinstance(service.invoice_repo, LightningInvoiceRepository)


def test_create_compliance_report_service_custom(tax_service, invoice_repo):
    """Test factory function with custom parameters."""
    service = create_compliance_report_service(
        tax_service=tax_service, invoice_repository=invoice_repo
    )

    assert service.tax_service is tax_service
    assert service.invoice_repo is invoice_repo


# ============================================================================
# TAX YEAR SUMMARY TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_generate_tax_year_summary_2025(compliance_service, sample_invoices_2025):
    """Test generating tax year summary for 2025."""
    summary = await compliance_service.generate_tax_year_summary(2025)

    assert isinstance(summary, TaxYearSummary)
    assert summary.tax_year == 2025
    assert summary.num_payments == 3  # Only 2025 invoices
    assert summary.total_revenue_eur == Decimal("16000.00")  # 2000 + 6000 + 8000
    assert summary.total_capital_gains_eur == Decimal("2500.00")  # 500 + 1000 + 1000
    assert summary.num_aml_alerts == 2  # inv2 and inv3
    assert summary.num_aml_verified == 1  # Only inv3
    assert summary.avg_payment_eur == Decimal("5333.33")  # 16000 / 3
    assert summary.max_payment_eur == Decimal("8000.00")  # inv3
    assert summary.quadro_rw_required is True

    # Tax calculation: 2500 * 0.26 = 650
    assert summary.total_tax_owed_eur == Decimal("650.00")


@pytest.mark.asyncio
async def test_generate_tax_year_summary_empty_year(compliance_service):
    """Test generating summary for year with no invoices."""
    summary = await compliance_service.generate_tax_year_summary(2026)

    assert summary.tax_year == 2026
    assert summary.num_payments == 0
    assert summary.total_revenue_eur == Decimal("0.00")
    assert summary.total_capital_gains_eur == Decimal("0.00")
    assert summary.total_tax_owed_eur == Decimal("0.00")
    assert summary.avg_payment_eur == Decimal("0.00")
    assert summary.max_payment_eur == Decimal("0.00")


# ============================================================================
# QUADRO RW REPORT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_generate_quadro_rw_report_json(compliance_service, sample_invoices_2025):
    """Test Quadro RW report generation in JSON format."""
    report_json = await compliance_service.generate_quadro_rw_report(2025, output_format="json")

    data = json.loads(report_json)
    assert data["tax_year"] == 2025
    assert data["num_transactions"] == 3
    assert "generated_at" in data


@pytest.mark.asyncio
async def test_generate_quadro_rw_report_csv(compliance_service, sample_invoices_2025):
    """Test Quadro RW report generation in CSV format."""
    report_csv = await compliance_service.generate_quadro_rw_report(2025, output_format="csv")

    reader = csv.reader(StringIO(report_csv))
    rows = list(reader)

    assert rows[0] == ["Metric", "Value"]
    assert rows[1] == ["Tax Year", "2025"]
    assert rows[4] == ["Number of Transactions", "3"]  # Row 4, not row 3


# ============================================================================
# AML COMPLIANCE REPORT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_generate_aml_compliance_report(compliance_service, sample_invoices_2025):
    """Test AML compliance report generation."""
    report = await compliance_service.generate_aml_compliance_report()

    assert isinstance(report, AMLComplianceReport)
    assert report.total_payments_over_threshold == 2  # inv2 and inv3
    assert report.total_verified == 1  # Only inv3
    assert report.total_pending_verification == 1  # Only inv2
    assert report.threshold_eur == Decimal("5000.00")
    assert len(report.payments_requiring_action) == 1  # Only inv2 pending

    # Check pending payment details
    pending = report.payments_requiring_action[0]
    assert pending["payment_hash"] == "c" * 64
    assert pending["amount_eur"] == 6000.0
    assert "days_since_settlement" in pending


@pytest.mark.asyncio
async def test_generate_aml_compliance_report_custom_threshold(
    compliance_service, sample_invoices_2025
):
    """Test AML report with custom threshold."""
    report = await compliance_service.generate_aml_compliance_report(
        threshold_eur=Decimal("7000.00")
    )

    # Only inv3 exceeds 7000 EUR
    assert report.total_payments_over_threshold == 1
    assert report.threshold_eur == Decimal("7000.00")


# ============================================================================
# CAPITAL GAINS REPORT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_generate_capital_gains_report_csv(compliance_service, sample_invoices_2025):
    """Test capital gains report in CSV format."""
    report_csv = await compliance_service.generate_capital_gains_report(2025, output_format="csv")

    reader = csv.reader(StringIO(report_csv))
    rows = list(reader)

    assert rows[0] == [
        "Payment Hash",
        "Settled At",
        "EUR Amount",
        "Capital Gain EUR",
        "BTC/EUR Rate",
        "Tax Year",
        "Fattura ID",
    ]
    assert len(rows) == 4  # Header + 3 payments


@pytest.mark.asyncio
async def test_generate_capital_gains_report_json(compliance_service, sample_invoices_2025):
    """Test capital gains report in JSON format."""
    report_json = await compliance_service.generate_capital_gains_report(2025, output_format="json")

    data = json.loads(report_json)
    assert data["tax_year"] == 2025
    assert data["num_taxable_payments"] == 3
    assert len(data["payments"]) == 3
    assert "generated_at" in data


# ============================================================================
# FILE EXPORT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_export_tax_year_summary_json(compliance_service, sample_invoices_2025, tmp_path):
    """Test exporting tax year summary to JSON file."""
    output_file = tmp_path / "summary_2025.json"

    await compliance_service.export_tax_year_summary_to_file(
        2025, output_file, output_format="json"
    )

    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert data["tax_year"] == 2025
    assert data["num_payments"] == 3


@pytest.mark.asyncio
async def test_export_tax_year_summary_csv(compliance_service, sample_invoices_2025, tmp_path):
    """Test exporting tax year summary to CSV file."""
    output_file = tmp_path / "summary_2025.csv"

    await compliance_service.export_tax_year_summary_to_file(2025, output_file, output_format="csv")

    assert output_file.exists()
    content = output_file.read_text()
    assert "Tax Year,2025" in content
    assert "Number of Payments,3" in content


@pytest.mark.asyncio
async def test_export_aml_compliance_report_json(
    compliance_service, sample_invoices_2025, tmp_path
):
    """Test exporting AML compliance report to JSON file."""
    output_file = tmp_path / "aml_report.json"

    await compliance_service.export_aml_compliance_report_to_file(output_file, output_format="json")

    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert data["total_payments_over_threshold"] == 2
    assert data["total_verified"] == 1


@pytest.mark.asyncio
async def test_export_aml_compliance_report_csv(compliance_service, sample_invoices_2025, tmp_path):
    """Test exporting AML compliance report to CSV file."""
    output_file = tmp_path / "aml_report.csv"

    await compliance_service.export_aml_compliance_report_to_file(output_file, output_format="csv")

    assert output_file.exists()
    content = output_file.read_text()
    reader = csv.reader(StringIO(content))
    rows = list(reader)

    assert rows[0] == [
        "Payment Hash",
        "Settled At",
        "Amount EUR",
        "Fattura ID",
        "Days Since Settlement",
    ]
    assert len(rows) == 2  # Header + 1 pending payment (inv2)


# ============================================================================
# EDGE CASES & ERROR HANDLING
# ============================================================================


@pytest.mark.asyncio
async def test_tax_year_summary_with_no_capital_gains(db_session, invoice_repo):
    """Test summary when invoices have no capital gain data."""
    # Create a fresh compliance service for this test
    tax_service = TaxCalculationService(
        invoice_repository=invoice_repo, aml_threshold_eur=Decimal("5000.00")
    )
    compliance_service = ComplianceReportService(
        tax_service=tax_service, invoice_repository=invoice_repo
    )

    # Create invoice without tax data
    inv = LightningInvoiceRecord(
        payment_hash="f" * 64,
        payment_request="lnbc..." * 10,
        amount_msat=100000000,
        description="No tax data",
        expiry_timestamp=int((datetime.now(UTC) + timedelta(hours=24)).timestamp()),
        status=InvoiceStatus.SETTLED,
        settled_at=datetime(2025, 1, 1, tzinfo=UTC),
        preimage="1" * 64,
    )
    invoice_repo.save(inv)

    summary = await compliance_service.generate_tax_year_summary(2025)

    # Should handle gracefully
    assert summary.num_payments == 0  # No taxable payments
    assert summary.total_capital_gains_eur == Decimal("0.00")


@pytest.mark.asyncio
async def test_aml_report_with_no_over_threshold_payments(db_session, invoice_repo):
    """Test AML report when no payments exceed threshold."""
    # Create a fresh service without sample data
    tax_service = TaxCalculationService(
        invoice_repository=invoice_repo, aml_threshold_eur=Decimal("5000.00")
    )
    compliance_service = ComplianceReportService(
        tax_service=tax_service, invoice_repository=invoice_repo
    )

    report = await compliance_service.generate_aml_compliance_report()

    # With no sample invoices loaded
    assert report.total_payments_over_threshold == 0
    assert report.total_verified == 0
    assert report.total_pending_verification == 0
    assert len(report.payments_requiring_action) == 0


# ============================================================================
# DATACLASS TESTS
# ============================================================================


def test_tax_year_summary_dataclass():
    """Test TaxYearSummary dataclass creation."""
    summary = TaxYearSummary(
        tax_year=2025,
        num_payments=10,
        total_revenue_eur=Decimal("50000.00"),
        total_capital_gains_eur=Decimal("10000.00"),
        total_tax_owed_eur=Decimal("2600.00"),
        num_aml_alerts=2,
        num_aml_verified=1,
        avg_payment_eur=Decimal("5000.00"),
        max_payment_eur=Decimal("15000.00"),
        quadro_rw_required=True,
    )

    assert summary.tax_year == 2025
    assert summary.num_payments == 10
    assert summary.quadro_rw_required is True


def test_aml_compliance_report_dataclass():
    """Test AMLComplianceReport dataclass creation."""
    report = AMLComplianceReport(
        report_date=datetime.now(UTC),
        total_payments_over_threshold=5,
        total_verified=3,
        total_pending_verification=2,
        threshold_eur=Decimal("5000.00"),
        payments_requiring_action=[],
    )

    assert report.total_payments_over_threshold == 5
    assert report.total_verified == 3
    assert report.total_pending_verification == 2
    assert isinstance(report.payments_requiring_action, list)
