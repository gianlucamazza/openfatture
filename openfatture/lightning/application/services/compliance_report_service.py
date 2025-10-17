"""Compliance report generation service for Lightning payments.

This service generates tax and compliance reports in various formats (CSV, JSON)
for accountants and tax advisors. Reports include:
- Annual tax summaries
- Quadro RW declarations
- AML compliance reports
- Capital gains detailed breakdown
"""

import csv
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from io import StringIO
from pathlib import Path
from typing import Any, Literal

from openfatture.lightning.application.services.tax_calculation_service import (
    TaxCalculationService,
)
from openfatture.lightning.domain.value_objects import QuadroRWData
from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository


@dataclass
class TaxYearSummary:
    """Summary of tax data for a specific year."""

    tax_year: int
    num_payments: int
    total_revenue_eur: Decimal
    total_capital_gains_eur: Decimal
    total_tax_owed_eur: Decimal
    num_aml_alerts: int
    num_aml_verified: int
    avg_payment_eur: Decimal
    max_payment_eur: Decimal
    quadro_rw_required: bool


@dataclass
class AMLComplianceReport:
    """AML compliance report data."""

    report_date: datetime
    total_payments_over_threshold: int
    total_verified: int
    total_pending_verification: int
    threshold_eur: Decimal
    payments_requiring_action: list[dict[str, Any]]


ReportFormat = Literal["csv", "json"]


class ComplianceReportService:
    """Service for generating tax and compliance reports.

    This service provides methods to generate various reports for
    Italian tax compliance, including:
    - Annual tax year summaries
    - Quadro RW declarations (monitoraggio fiscale)
    - AML compliance reports
    - Detailed capital gains breakdowns
    """

    def __init__(
        self,
        tax_service: TaxCalculationService,
        invoice_repository: LightningInvoiceRepository,
    ):
        """Initialize the compliance report service.

        Args:
            tax_service: Tax calculation service instance
            invoice_repository: Repository for Lightning invoice records
        """
        self.tax_service = tax_service
        self.invoice_repo = invoice_repository

    async def generate_tax_year_summary(self, tax_year: int) -> TaxYearSummary:
        """Generate annual tax summary for a specific year.

        Args:
            tax_year: Tax year (e.g., 2025)

        Returns:
            TaxYearSummary with aggregated data
        """
        # Get all taxable payments for the year
        taxable_payments = await self.tax_service.get_taxable_payments_for_year(tax_year)

        # Calculate totals
        total_revenue = Decimal("0")
        total_capital_gains = Decimal("0")
        max_payment = Decimal("0")

        for payment in taxable_payments:
            eur_amount = Decimal(str(payment["eur_amount"]))
            capital_gain = Decimal(str(payment["capital_gain_eur"]))

            total_revenue += eur_amount
            total_capital_gains += capital_gain
            max_payment = max(max_payment, eur_amount)

        # Get AML statistics
        start_date = datetime(tax_year, 1, 1, tzinfo=UTC)
        end_date = datetime(tax_year, 12, 31, 23, 59, 59, tzinfo=UTC)
        all_invoices = self.invoice_repo.find_settled_in_date_range(start_date, end_date)

        num_aml_alerts = sum(1 for inv in all_invoices if inv.exceeds_aml_threshold)
        num_aml_verified = sum(1 for inv in all_invoices if inv.aml_verified)

        # Calculate total tax owed
        total_tax_owed = await self.tax_service.calculate_total_tax_owed(tax_year)

        # Calculate average payment
        num_payments = len(taxable_payments)
        avg_payment = total_revenue / num_payments if num_payments > 0 else Decimal("0")

        return TaxYearSummary(
            tax_year=tax_year,
            num_payments=num_payments,
            total_revenue_eur=total_revenue.quantize(Decimal("0.01")),
            total_capital_gains_eur=total_capital_gains.quantize(Decimal("0.01")),
            total_tax_owed_eur=total_tax_owed,
            num_aml_alerts=num_aml_alerts,
            num_aml_verified=num_aml_verified,
            avg_payment_eur=avg_payment.quantize(Decimal("0.01")),
            max_payment_eur=max_payment.quantize(Decimal("0.01")),
            quadro_rw_required=True,  # Always required from 2025
        )

    async def generate_quadro_rw_report(
        self, tax_year: int, output_format: ReportFormat = "json"
    ) -> str:
        """Generate Quadro RW declaration report.

        Args:
            tax_year: Tax year
            output_format: Output format ('csv' or 'json')

        Returns:
            Report as string in requested format
        """
        quadro_rw_data = await self.tax_service.generate_quadro_rw_data(tax_year)

        if output_format == "json":
            return self._quadro_rw_to_json(quadro_rw_data)
        else:
            return self._quadro_rw_to_csv(quadro_rw_data)

    async def generate_aml_compliance_report(
        self, threshold_eur: Decimal | None = None
    ) -> AMLComplianceReport:
        """Generate AML compliance report for all time.

        Args:
            threshold_eur: AML threshold (uses service default if None)

        Returns:
            AMLComplianceReport with current status
        """
        threshold = threshold_eur or self.tax_service.aml_threshold_eur

        # Get all invoices exceeding threshold
        # Check against the provided threshold parameter, not the stored flag
        all_invoices = self.invoice_repo.find_all()
        over_threshold = [
            inv
            for inv in all_invoices
            if inv.is_settled and inv.eur_amount_declared and inv.eur_amount_declared >= threshold
        ]

        total_verified = sum(1 for inv in over_threshold if inv.aml_verified)
        total_pending = len(over_threshold) - total_verified

        # Build list of payments requiring action
        payments_requiring_action = []
        for inv in over_threshold:
            if not inv.aml_verified:
                # Calculate days since settlement
                days_since = None
                if inv.settled_at:
                    # Ensure both datetimes are timezone-aware
                    now_aware = datetime.now(UTC)
                    settled_aware = (
                        inv.settled_at
                        if inv.settled_at.tzinfo
                        else inv.settled_at.replace(tzinfo=UTC)
                    )
                    days_since = (now_aware - settled_aware).days

                payments_requiring_action.append(
                    {
                        "payment_hash": inv.payment_hash,
                        "settled_at": inv.settled_at.isoformat() if inv.settled_at else None,
                        "amount_eur": (
                            float(inv.eur_amount_declared) if inv.eur_amount_declared else 0.0
                        ),
                        "fattura_id": inv.fattura_id,
                        "days_since_settlement": days_since,
                    }
                )

        return AMLComplianceReport(
            report_date=datetime.now(UTC),
            total_payments_over_threshold=len(over_threshold),
            total_verified=total_verified,
            total_pending_verification=total_pending,
            threshold_eur=threshold,
            payments_requiring_action=payments_requiring_action,
        )

    async def generate_capital_gains_report(
        self, tax_year: int, output_format: ReportFormat = "csv"
    ) -> str:
        """Generate detailed capital gains breakdown report.

        Args:
            tax_year: Tax year
            output_format: Output format ('csv' or 'json')

        Returns:
            Report as string in requested format
        """
        taxable_payments = await self.tax_service.get_taxable_payments_for_year(tax_year)

        if output_format == "json":
            return json.dumps(
                {
                    "tax_year": tax_year,
                    "num_taxable_payments": len(taxable_payments),
                    "payments": taxable_payments,
                    "generated_at": datetime.now(UTC).isoformat(),
                },
                indent=2,
                default=str,
            )
        else:
            return self._capital_gains_to_csv(taxable_payments)

    async def export_tax_year_summary_to_file(
        self, tax_year: int, output_path: Path, output_format: ReportFormat = "json"
    ) -> None:
        """Export tax year summary to file.

        Args:
            tax_year: Tax year
            output_path: Output file path
            output_format: Output format ('csv' or 'json')
        """
        summary = await self.generate_tax_year_summary(tax_year)

        if output_format == "json":
            content = json.dumps(
                {
                    **asdict(summary),
                    "total_revenue_eur": str(summary.total_revenue_eur),
                    "total_capital_gains_eur": str(summary.total_capital_gains_eur),
                    "total_tax_owed_eur": str(summary.total_tax_owed_eur),
                    "avg_payment_eur": str(summary.avg_payment_eur),
                    "max_payment_eur": str(summary.max_payment_eur),
                },
                indent=2,
            )
        else:
            # CSV format
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Tax Year", summary.tax_year])
            writer.writerow(["Number of Payments", summary.num_payments])
            writer.writerow(["Total Revenue (EUR)", str(summary.total_revenue_eur)])
            writer.writerow(["Total Capital Gains (EUR)", str(summary.total_capital_gains_eur)])
            writer.writerow(["Total Tax Owed (EUR)", str(summary.total_tax_owed_eur)])
            writer.writerow(["AML Alerts", summary.num_aml_alerts])
            writer.writerow(["AML Verified", summary.num_aml_verified])
            writer.writerow(["Average Payment (EUR)", str(summary.avg_payment_eur)])
            writer.writerow(["Max Payment (EUR)", str(summary.max_payment_eur)])
            writer.writerow(["Quadro RW Required", summary.quadro_rw_required])
            content = output.getvalue()

        output_path.write_text(content, encoding="utf-8")

    async def export_aml_compliance_report_to_file(
        self, output_path: Path, output_format: ReportFormat = "json"
    ) -> None:
        """Export AML compliance report to file.

        Args:
            output_path: Output file path
            output_format: Output format ('csv' or 'json')
        """
        report = await self.generate_aml_compliance_report()

        if output_format == "json":
            content = json.dumps(
                {
                    "report_date": report.report_date.isoformat(),
                    "total_payments_over_threshold": report.total_payments_over_threshold,
                    "total_verified": report.total_verified,
                    "total_pending_verification": report.total_pending_verification,
                    "threshold_eur": str(report.threshold_eur),
                    "payments_requiring_action": report.payments_requiring_action,
                },
                indent=2,
                default=str,
            )
        else:
            # CSV format
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(
                [
                    "Payment Hash",
                    "Settled At",
                    "Amount EUR",
                    "Fattura ID",
                    "Days Since Settlement",
                ]
            )
            for payment in report.payments_requiring_action:
                writer.writerow(
                    [
                        payment["payment_hash"],
                        payment["settled_at"],
                        payment["amount_eur"],
                        payment["fattura_id"],
                        payment["days_since_settlement"],
                    ]
                )
            content = output.getvalue()

        output_path.write_text(content, encoding="utf-8")

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _quadro_rw_to_json(self, quadro_rw: QuadroRWData) -> str:
        """Convert QuadroRWData to JSON string."""
        return json.dumps(
            {
                "tax_year": quadro_rw.tax_year,
                "total_holdings_eur": str(quadro_rw.total_holdings_eur),
                "average_holdings_eur": str(quadro_rw.average_holdings_eur),
                "num_transactions": quadro_rw.num_transactions,
                "total_inflows_eur": str(quadro_rw.total_inflows_eur),
                "total_outflows_eur": str(quadro_rw.total_outflows_eur),
                "generated_at": datetime.now(UTC).isoformat(),
            },
            indent=2,
        )

    def _quadro_rw_to_csv(self, quadro_rw: QuadroRWData) -> str:
        """Convert QuadroRWData to CSV string."""
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Tax Year", quadro_rw.tax_year])
        writer.writerow(["Total Holdings (EUR)", str(quadro_rw.total_holdings_eur)])
        writer.writerow(["Average Holdings (EUR)", str(quadro_rw.average_holdings_eur)])
        writer.writerow(["Number of Transactions", quadro_rw.num_transactions])
        writer.writerow(["Total Inflows (EUR)", str(quadro_rw.total_inflows_eur)])
        writer.writerow(["Total Outflows (EUR)", str(quadro_rw.total_outflows_eur)])
        return output.getvalue()

    def _capital_gains_to_csv(self, taxable_payments: list[dict]) -> str:
        """Convert taxable payments list to CSV string."""
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Payment Hash",
                "Settled At",
                "EUR Amount",
                "Capital Gain EUR",
                "BTC/EUR Rate",
                "Tax Year",
                "Fattura ID",
            ]
        )
        for payment in taxable_payments:
            writer.writerow(
                [
                    payment["payment_hash"],
                    payment["settled_at"],
                    payment["eur_amount"],
                    payment["capital_gain_eur"],
                    payment["btc_eur_rate"],
                    payment["tax_year"],
                    payment["fattura_id"],
                ]
            )
        return output.getvalue()

    # ========================================================================
    # SYNC WRAPPERS FOR CLI COMMANDS
    # ========================================================================

    def generate_tax_year_summary_sync(self, tax_year: int) -> TaxYearSummary:
        """Synchronous wrapper for generate_tax_year_summary (for CLI commands).

        Args:
            tax_year: Tax year (e.g., 2025)

        Returns:
            TaxYearSummary with aggregated data
        """
        import asyncio

        return asyncio.run(self.generate_tax_year_summary(tax_year))

    def generate_quadro_rw_report_sync(
        self, tax_year: int, output_format: ReportFormat = "json"
    ) -> str:
        """Synchronous wrapper for generate_quadro_rw_report (for CLI commands).

        Args:
            tax_year: Tax year
            output_format: Output format ('csv' or 'json')

        Returns:
            Report as string in requested format
        """
        import asyncio

        return asyncio.run(self.generate_quadro_rw_report(tax_year, output_format))

    def generate_aml_compliance_report_sync(
        self, threshold_eur: Decimal | None = None
    ) -> AMLComplianceReport:
        """Synchronous wrapper for generate_aml_compliance_report (for CLI commands).

        Args:
            threshold_eur: AML threshold (uses service default if None)

        Returns:
            AMLComplianceReport with current status
        """
        import asyncio

        return asyncio.run(self.generate_aml_compliance_report(threshold_eur))

    def generate_capital_gains_report_sync(
        self, tax_year: int, output_format: ReportFormat = "csv"
    ) -> str:
        """Synchronous wrapper for generate_capital_gains_report (for CLI commands).

        Args:
            tax_year: Tax year
            output_format: Output format ('csv' or 'json')

        Returns:
            Report as string in requested format
        """
        import asyncio

        return asyncio.run(self.generate_capital_gains_report(tax_year, output_format))


def create_compliance_report_service(
    tax_service: TaxCalculationService | None = None,
    invoice_repository: LightningInvoiceRepository | None = None,
) -> ComplianceReportService:
    """Factory function to create ComplianceReportService.

    Args:
        tax_service: Optional tax service (creates default if None)
        invoice_repository: Optional repository (creates default if None)

    Returns:
        Configured ComplianceReportService instance
    """
    if invoice_repository is None:
        invoice_repository = LightningInvoiceRepository()

    if tax_service is None:
        from openfatture.lightning.application.services.tax_calculation_service import (
            create_tax_calculation_service,
        )

        tax_service = create_tax_calculation_service(invoice_repository=invoice_repository)

    return ComplianceReportService(
        tax_service=tax_service,
        invoice_repository=invoice_repository,
    )
