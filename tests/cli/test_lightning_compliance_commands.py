"""Tests for Lightning compliance CLI commands."""

import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from typer.testing import CliRunner

from openfatture.cli.commands.lightning import app
from openfatture.lightning.domain.enums import InvoiceStatus
from openfatture.lightning.domain.models import LightningInvoiceRecord
from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository
from openfatture.storage.database.base import get_session, init_db

runner = CliRunner()


@pytest.fixture(scope="function")
def test_db():
    """Create temporary database file for integration tests."""
    # Use temporary file instead of :memory: to share between sessions
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    db_url = f"sqlite:///{db_path}"
    init_db(db_url)

    yield db_url

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def invoice_repo(test_db):
    """Create invoice repository fixture using shared DB."""
    session = get_session()
    yield LightningInvoiceRepository(session=session)
    session.close()


@pytest.fixture
def sample_compliance_invoices(test_db, invoice_repo):
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

    return invoices


# ============================================================================
# COMPLIANCE-CHECK COMMAND TESTS
# ============================================================================


def test_compliance_check_success(test_db, invoice_repo):
    """Test compliance-check command with compliant data."""
    # Create compliant invoices (all AML payments verified)
    from datetime import UTC, datetime, timedelta
    from decimal import Decimal

    # Invoice 1: Below threshold
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

    # Invoice 2: Above threshold, verified
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
    inv2.mark_aml_verified()
    invoice_repo.save(inv2)

    result = runner.invoke(app, ["compliance-check", "--tax-year", "2025"])

    assert result.exit_code == 0
    assert "Lightning Compliance Check - 2025" in result.stdout
    assert "Tax Year Summary" in result.stdout
    assert "AML Compliance" in result.stdout
    assert "Quadro RW Declaration" in result.stdout
    assert "All Compliance Checks Passed" in result.stdout


def test_compliance_check_unverified_aml(test_db, sample_compliance_invoices):
    """Test compliance-check command with unverified AML payment."""
    result = runner.invoke(app, ["compliance-check", "--tax-year", "2025"])

    assert result.exit_code == 1  # Should fail with unverified payments
    assert "Lightning Compliance Check - 2025" in result.stdout
    assert "Compliance Issues Found" in result.stdout
    assert "unverified AML payment(s)" in result.stdout


def test_compliance_check_verbose(test_db, sample_compliance_invoices):
    """Test compliance-check command with verbose flag."""
    result = runner.invoke(app, ["compliance-check", "--tax-year", "2025", "--verbose"])

    assert "Lightning Compliance Check - 2025" in result.stdout
    # With verbose flag and unverified payments, should show details
    if "Unverified AML Payments:" in result.stdout:
        # Should show payment hash of unverified payment (truncated to 8 chars)
        assert "cccccccc" in result.stdout


def test_compliance_check_empty_year(test_db):
    """Test compliance-check for year with no data."""
    result = runner.invoke(app, ["compliance-check", "--tax-year", "2023"])

    assert result.exit_code == 0
    assert "0" in result.stdout  # No payments


# ============================================================================
# REPORT QUADRO-RW TESTS
# ============================================================================


def test_report_quadro_rw_json(test_db, sample_compliance_invoices, tmp_path):
    """Test Quadro RW report generation in JSON format."""
    output_file = tmp_path / "quadro_rw_2025.json"

    result = runner.invoke(
        app,
        [
            "report",
            "quadro-rw",
            "--tax-year",
            "2025",
            "--format",
            "json",
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Generating Quadro RW Report - 2025 (JSON)" in result.stdout
    assert "Report saved to" in result.stdout
    assert output_file.exists()

    # Check file content - Quadro RW contains aggregate data, not individual payments
    content = output_file.read_text()
    assert "tax_year" in content
    assert "total_holdings_eur" in content
    assert "num_transactions" in content


def test_report_quadro_rw_csv(test_db, sample_compliance_invoices):
    """Test Quadro RW report generation in CSV format."""
    result = runner.invoke(app, ["report", "quadro-rw", "--tax-year", "2025", "--format", "csv"])

    assert result.exit_code == 0
    assert "Generating Quadro RW Report - 2025 (CSV)" in result.stdout
    assert "Total invoices in report: 3" in result.stdout

    # CSV should be printed to stdout - Quadro RW contains aggregate data
    assert "Tax Year" in result.stdout or "tax_year" in result.stdout.lower()
    assert "Holdings" in result.stdout or "Transactions" in result.stdout


def test_report_quadro_rw_invalid_format(test_db):
    """Test Quadro RW report with invalid format."""
    result = runner.invoke(app, ["report", "quadro-rw", "--tax-year", "2025", "--format", "xml"])

    assert result.exit_code == 1
    assert "Invalid format" in result.stdout


# ============================================================================
# REPORT CAPITAL-GAINS TESTS
# ============================================================================


def test_report_capital_gains_csv(test_db, sample_compliance_invoices):
    """Test capital gains report generation in CSV format."""
    result = runner.invoke(
        app, ["report", "capital-gains", "--tax-year", "2025", "--format", "csv"]
    )

    assert result.exit_code == 0
    assert "Generating Capital Gains Report - 2025 (CSV)" in result.stdout
    assert "Total invoices with gains: 3" in result.stdout
    assert "Total capital gains:" in result.stdout
    assert "Estimated tax" in result.stdout

    # Should show 26% tax rate for 2025
    assert "26%" in result.stdout


def test_report_capital_gains_json(test_db, sample_compliance_invoices, tmp_path):
    """Test capital gains report generation in JSON format."""
    output_file = tmp_path / "capital_gains_2025.json"

    result = runner.invoke(
        app,
        [
            "report",
            "capital-gains",
            "--tax-year",
            "2025",
            "--format",
            "json",
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert output_file.exists()


# ============================================================================
# REPORT AML TESTS
# ============================================================================


def test_report_aml(test_db, sample_compliance_invoices):
    """Test AML compliance report generation."""
    result = runner.invoke(app, ["report", "aml", "--threshold", "5000"])

    assert result.exit_code == 0
    assert "Generating AML Compliance Report" in result.stdout
    assert "Total over threshold: 2" in result.stdout
    assert "Verified: 1" in result.stdout
    assert "Unverified: 1" in result.stdout
    assert "Compliance rate:" in result.stdout

    # Should have JSON output
    assert '"threshold_eur"' in result.stdout
    assert '"compliance_rate"' in result.stdout


def test_report_aml_with_output_file(test_db, sample_compliance_invoices, tmp_path):
    """Test AML report with output file."""
    output_file = tmp_path / "aml_report.json"

    result = runner.invoke(
        app, ["report", "aml", "--threshold", "5000", "--output", str(output_file)]
    )

    assert result.exit_code == 0
    assert output_file.exists()

    # Check JSON structure
    import json

    data = json.loads(output_file.read_text())
    assert "threshold_eur" in data
    assert "total_over_threshold" in data
    assert "payments_over_threshold" in data


# ============================================================================
# AML LIST-UNVERIFIED TESTS
# ============================================================================


def test_aml_list_unverified(test_db, sample_compliance_invoices):
    """Test listing unverified AML payments."""
    result = runner.invoke(app, ["aml", "list-unverified", "--threshold", "5000"])

    assert result.exit_code == 0
    assert "Unverified AML Payments" in result.stdout
    assert "Unverified Payments (1 total)" in result.stdout
    # Should show payment hash cccc...
    assert "cccccccccccc" in result.stdout


def test_aml_list_unverified_verbose(test_db, sample_compliance_invoices):
    """Test listing unverified AML payments with verbose flag."""
    result = runner.invoke(app, ["aml", "list-unverified", "--threshold", "5000", "--verbose"])

    assert result.exit_code == 0
    # With verbose flag, table should show additional columns
    # Check for table output structure
    assert "Unverified Payments" in result.stdout


def test_aml_list_unverified_none(test_db, invoice_repo):
    """Test listing unverified AML payments when all are verified."""
    # Create invoices with all verified
    from datetime import UTC, datetime, timedelta
    from decimal import Decimal

    # Invoice above threshold, but verified
    inv = LightningInvoiceRecord(
        payment_hash="z" * 64,
        payment_request="lnbc_verified" * 20,
        amount_msat=800000000,
        description="Verified payment",
        expiry_timestamp=int((datetime.now(UTC) + timedelta(hours=24)).timestamp()),
        status=InvoiceStatus.SETTLED,
        settled_at=datetime(2025, 9, 10, tzinfo=UTC),
        preimage="y" * 64,
    )
    inv.store_tax_data(
        btc_eur_rate=Decimal("60000.00"),
        eur_amount=Decimal("8000.00"),
        acquisition_cost_eur=Decimal("7000.00"),
    )
    inv.exceeds_aml_threshold = True
    inv.mark_aml_verified()
    invoice_repo.save(inv)

    result = runner.invoke(app, ["aml", "list-unverified", "--threshold", "5000"])

    assert result.exit_code == 0
    assert "No unverified payments found" in result.stdout


# ============================================================================
# AML VERIFY TESTS
# ============================================================================


def test_aml_verify_payment(test_db, sample_compliance_invoices):
    """Test verifying an AML payment."""
    # Get unverified payment hash
    payment_hash = "c" * 64

    result = runner.invoke(
        app,
        [
            "aml",
            "verify",
            payment_hash,
            "--verified-by",
            "compliance@example.com",
            "--notes",
            "ID verified",
        ],
    )

    assert result.exit_code == 0
    assert "Verifying AML Payment" in result.stdout
    assert "Payment verified successfully" in result.stdout
    assert "compliance@example.com" in result.stdout
    assert "ID verified" in result.stdout

    # Check that invoice is now verified in DB
    session = get_session()
    repo = LightningInvoiceRepository(session=session)
    invoice = repo.find_by_payment_hash(payment_hash)
    session.close()
    assert invoice.aml_verified is True
    assert invoice.aml_verification_date is not None


def test_aml_verify_already_verified(test_db, sample_compliance_invoices):
    """Test verifying an already verified payment."""
    # Use already verified payment
    payment_hash = "e" * 64

    result = runner.invoke(
        app,
        ["aml", "verify", payment_hash, "--verified-by", "compliance@example.com"],
    )

    assert result.exit_code == 0
    assert "already verified" in result.stdout


def test_aml_verify_not_found(test_db):
    """Test verifying a non-existent payment."""
    result = runner.invoke(
        app,
        ["aml", "verify", "nonexistent" * 5, "--verified-by", "compliance@example.com"],
    )

    assert result.exit_code == 1
    assert "Invoice not found" in result.stdout


def test_aml_verify_with_client_id(test_db, sample_compliance_invoices):
    """Test verifying payment with client ID."""
    payment_hash = "c" * 64

    result = runner.invoke(
        app,
        [
            "aml",
            "verify",
            payment_hash,
            "--verified-by",
            "compliance@example.com",
            "--client-id",
            "42",
        ],
    )

    assert result.exit_code == 0
    assert "Payment verified successfully" in result.stdout


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_full_compliance_workflow(test_db, sample_compliance_invoices):
    """Test complete compliance workflow from check to verification."""
    # Step 1: Initial compliance check (should fail with unverified)
    result1 = runner.invoke(app, ["compliance-check", "--tax-year", "2025"])
    assert result1.exit_code == 1
    assert "Compliance Issues Found" in result1.stdout

    # Step 2: List unverified payments
    result2 = runner.invoke(app, ["aml", "list-unverified"])
    assert result2.exit_code == 0
    assert "1 total" in result2.stdout

    # Step 3: Verify the payment
    payment_hash = "c" * 64
    result3 = runner.invoke(
        app,
        ["aml", "verify", payment_hash, "--verified-by", "compliance@example.com"],
    )
    assert result3.exit_code == 0

    # Step 4: Compliance check should now pass
    result4 = runner.invoke(app, ["compliance-check", "--tax-year", "2025"])
    assert result4.exit_code == 0
    assert "All Compliance Checks Passed" in result4.stdout

    # Step 5: Generate reports
    result5 = runner.invoke(
        app, ["report", "capital-gains", "--tax-year", "2025", "--format", "csv"]
    )
    assert result5.exit_code == 0
    assert "Total invoices with gains: 3" in result5.stdout


def test_report_generation_for_empty_database(test_db):
    """Test all reports with empty database."""
    # Quadro RW
    result1 = runner.invoke(app, ["report", "quadro-rw", "--tax-year", "2025", "--format", "json"])
    assert result1.exit_code == 0
    assert "Total invoices in report: 0" in result1.stdout

    # Capital gains
    result2 = runner.invoke(
        app, ["report", "capital-gains", "--tax-year", "2025", "--format", "csv"]
    )
    assert result2.exit_code == 0

    # AML
    result3 = runner.invoke(app, ["report", "aml"])
    assert result3.exit_code == 0
    assert '"total_over_threshold": 0' in result3.stdout


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


def test_compliance_check_database_error(test_db, monkeypatch):
    """Test compliance check with database error."""

    # Mock the service method to raise an error
    original_method = None

    def mock_generate_tax_year_summary(*args, **kwargs):
        raise RuntimeError("Database connection failed")

    from openfatture.lightning.application.services import compliance_report_service

    monkeypatch.setattr(
        compliance_report_service.ComplianceReportService,
        "generate_tax_year_summary",
        mock_generate_tax_year_summary,
    )

    result = runner.invoke(app, ["compliance-check", "--tax-year", "2025"])

    assert result.exit_code == 1
    assert (
        "Error running compliance check" in result.stdout
        or "Database connection failed" in result.stdout
    )
