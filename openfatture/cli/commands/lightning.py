"""Lightning Network payment management commands."""

from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from openfatture.i18n import _
from openfatture.utils.async_bridge import run_async

app = typer.Typer(name="lightning", help=_("cli-lightning-help"), no_args_is_help=True)
console = Console()

# Sub-commands for compliance
report_app = typer.Typer(name="report", help=_("cli-lightning-report-help"), no_args_is_help=True)
aml_app = typer.Typer(name="aml", help=_("cli-lightning-aml-help"), no_args_is_help=True)

app.add_typer(report_app)
app.add_typer(aml_app)


@app.command("status")
def lightning_status():
    """Show Lightning Network status."""
    from openfatture.utils.config import get_settings

    settings = get_settings()

    console.print(_("cli-lightning-status-title"))

    if not settings.lightning_enabled:
        console.print(_("cli-lightning-status-disabled"))
        console.print(_("cli-lightning-status-disabled-hint-env"))
        console.print(_("cli-lightning-status-disabled-hint-cmd"))
        return

    console.print(_("cli-lightning-status-enabled"))
    console.print(_("cli-lightning-status-host", host=settings.lightning_host))
    console.print(_("cli-lightning-status-timeout", timeout=settings.lightning_timeout_seconds))
    console.print(_("cli-lightning-status-max-retries", max_retries=settings.lightning_max_retries))

    btc_provider = (
        _("cli-lightning-btc-provider-coingecko")
        if settings.lightning_coingecko_enabled
        else (
            _("cli-lightning-btc-provider-cmc")
            if settings.lightning_cmc_enabled
            else _("cli-lightning-btc-provider-fallback")
        )
    )
    console.print(_("cli-lightning-status-btc-provider", provider=btc_provider))

    liquidity_status = (
        _("cli-lightning-liquidity-enabled")
        if settings.lightning_liquidity_enabled
        else _("cli-lightning-liquidity-disabled")
    )
    console.print(_("cli-lightning-status-liquidity", status=liquidity_status))


@app.command("invoice")
def create_invoice():
    """Create a Lightning invoice."""
    from openfatture.utils.config import get_settings

    if not get_settings().lightning_enabled:
        console.print(_("cli-lightning-disabled-error"))
        return

    console.print(_("cli-lightning-invoice-title"))
    console.print(_("cli-lightning-invoice-not-available"))


@app.command("channels")
def list_channels():
    """List Lightning channels."""
    from openfatture.utils.config import get_settings

    if not get_settings().lightning_enabled:
        console.print(_("cli-lightning-disabled-error"))
        return

    console.print(_("cli-lightning-channels-title"))
    console.print(_("cli-lightning-channels-not-available"))


@app.command("liquidity")
def check_liquidity():
    """Check channel liquidity."""
    from openfatture.utils.config import get_settings

    if not get_settings().lightning_enabled:
        console.print(_("cli-lightning-disabled-error"))
        return

    console.print(_("cli-lightning-liquidity-title"))
    console.print(_("cli-lightning-liquidity-not-available"))


# ============================================================================
# COMPLIANCE COMMANDS (Italian Tax & AML Regulations)
# ============================================================================


@app.command("compliance-check")
def compliance_check(
    tax_year: int = typer.Option(
        datetime.now().year, "--tax-year", "-y", help=_("cli-lightning-compliance-opt-tax-year")
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help=_("cli-lightning-compliance-opt-verbose")
    ),
):
    """Run comprehensive compliance check for Italian tax and AML regulations.

    This command checks:
    - Capital gains tax compliance (26% in 2025, 33% from 2026)
    - Anti-Money Laundering (AML) threshold violations (5,000 EUR)
    - Quadro RW declaration requirements
    - Missing tax data on settled invoices

    Example:
        openfatture lightning compliance-check --tax-year 2025
    """

    from openfatture.lightning.application.services.compliance_report_service import (
        create_compliance_report_service,
    )
    from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository
    from openfatture.storage.database.base import get_session

    try:
        session = get_session()
        invoice_repo = LightningInvoiceRepository(session=session)
        compliance_service = create_compliance_report_service(invoice_repository=invoice_repo)

        console.print(_("cli-lightning-compliance-title", year=tax_year))

        # 1. Tax Year Summary
        summary = run_async(compliance_service.generate_tax_year_summary(tax_year))

        console.print(_("cli-lightning-compliance-summary-title"))
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_row(
            _("cli-lightning-compliance-summary-payments"), f"[cyan]{summary.num_payments}[/cyan]"
        )
        table.add_row(
            _("cli-lightning-compliance-summary-revenue"),
            f"[green]{summary.total_revenue_eur:,.2f} €[/green]",
        )
        table.add_row(
            _("cli-lightning-compliance-summary-gains"),
            f"[yellow]{summary.total_capital_gains_eur:,.2f} €[/yellow]",
        )
        table.add_row(
            _("cli-lightning-compliance-summary-tax"),
            f"[red]{summary.total_tax_owed_eur:,.2f} €[/red]",
        )
        console.print(table)
        console.print()

        # 2. AML Compliance
        console.print(_("cli-lightning-compliance-aml-title"))
        aml_table = Table(show_header=False, box=None, padding=(0, 2))
        aml_table.add_row(
            _("cli-lightning-compliance-aml-total"), f"[cyan]{summary.num_aml_alerts}[/cyan]"
        )
        aml_table.add_row(
            _("cli-lightning-compliance-aml-verified"), f"[green]{summary.num_aml_verified}[/green]"
        )
        unverified = summary.num_aml_alerts - summary.num_aml_verified
        status = (
            _("cli-lightning-compliance-aml-status-ok")
            if unverified == 0
            else _("cli-lightning-compliance-aml-status-require", count=unverified)
        )
        aml_table.add_row(
            _("cli-lightning-compliance-aml-unverified"),
            f"[{'green' if unverified == 0 else 'red'}]{status}[/]",
        )
        console.print(aml_table)
        console.print()

        # 3. Quadro RW Check
        quadro_rw_invoices = invoice_repo.find_requiring_quadro_rw(tax_year)
        console.print(_("cli-lightning-compliance-quadro-title"))
        quadro_table = Table(show_header=False, box=None, padding=(0, 2))
        quadro_table.add_row(
            _("cli-lightning-compliance-quadro-count"), f"[cyan]{len(quadro_rw_invoices)}[/cyan]"
        )
        if len(quadro_rw_invoices) > 0:
            quadro_table.add_row(
                _("cli-lightning-compliance-action-required"),
                _("cli-lightning-compliance-quadro-action"),
            )
        else:
            quadro_table.add_row(
                _("cli-lightning-compliance-status"), _("cli-lightning-compliance-quadro-status-ok")
            )
        console.print(quadro_table)
        console.print()

        # 4. Missing Tax Data
        missing_data = invoice_repo.find_with_missing_tax_data()
        console.print(_("cli-lightning-compliance-data-quality-title"))
        missing_table = Table(show_header=False, box=None, padding=(0, 2))
        missing_table.add_row(
            _("cli-lightning-compliance-data-quality-missing"),
            f"[{'red' if missing_data else 'green'}]{len(missing_data)}[/]",
        )
        if missing_data:
            missing_table.add_row(
                _("cli-lightning-compliance-action-required"),
                _("cli-lightning-compliance-data-quality-action"),
            )
        else:
            missing_table.add_row(
                _("cli-lightning-compliance-status"),
                _("cli-lightning-compliance-data-quality-status-ok"),
            )
        console.print(missing_table)
        console.print()

        # Overall Status
        issues = []
        if unverified > 0:
            issues.append(_("cli-lightning-compliance-issue-aml", count=unverified))
        if len(missing_data) > 0:
            issues.append(_("cli-lightning-compliance-issue-missing-data", count=len(missing_data)))

        if issues:
            console.print(_("cli-lightning-compliance-issues-found", issues=", ".join(issues)))
            raise typer.Exit(code=1)
        else:
            console.print(_("cli-lightning-compliance-passed"))

        # Verbose output
        if verbose and unverified > 0:
            console.print(_("cli-lightning-compliance-verbose-title"))
            unverified_payments = invoice_repo.find_unverified_aml_payments(5000.0)
            for inv in unverified_payments:
                settled_date = inv.settled_at.strftime("%Y-%m-%d") if inv.settled_at else "N/A"
                console.print(
                    _(
                        "cli-lightning-compliance-verbose-item",
                        hash=inv.payment_hash[:8],
                        amount=f"{inv.eur_amount_declared:,.2f}",
                        date=settled_date,
                    )
                )
            console.print()

    except typer.Exit:
        # Control-flow exit (e.g. compliance issues found): do not report it as
        # an unexpected error.
        raise
    except Exception as e:
        console.print(_("cli-lightning-compliance-error", error=str(e)))
        raise typer.Exit(code=1)
    finally:
        session.close()


# ============================================================================
# REPORT COMMANDS
# ============================================================================


@report_app.command("quadro-rw")
def generate_quadro_rw_report(
    tax_year: int = typer.Option(
        ..., "--tax-year", "-y", help=_("cli-lightning-report-opt-tax-year")
    ),
    output_format: str = typer.Option(
        "json", "--format", "-f", help=_("cli-lightning-report-opt-format")
    ),
    output_file: Path = typer.Option(
        None, "--output", "-o", help=_("cli-lightning-report-opt-output")
    ),
):
    """Generate Quadro RW declaration report.

    Quadro RW is mandatory for all crypto holdings from 2025 onwards (Italian law).
    This report includes all settled Lightning invoices with EUR amounts for the tax year.

    Example:
        openfatture lightning report quadro-rw --tax-year 2025 --format csv --output quadro_rw_2025.csv
    """
    from typing import cast

    from openfatture.lightning.application.services.compliance_report_service import (
        ReportFormat,
        create_compliance_report_service,
    )
    from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository
    from openfatture.storage.database.base import get_session

    if output_format not in ["json", "csv"]:
        console.print(_("cli-lightning-report-invalid-format"))
        raise typer.Exit(code=1)

    try:
        session = get_session()
        invoice_repo = LightningInvoiceRepository(session=session)
        compliance_service = create_compliance_report_service(invoice_repository=invoice_repo)

        console.print(
            _("cli-lightning-report-quadro-title", year=tax_year, format=output_format.upper())
        )

        # Safe to cast after validation
        report_content = run_async(
            compliance_service.generate_quadro_rw_report(
                tax_year, output_format=cast(ReportFormat, output_format)
            )
        )

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(report_content, encoding="utf-8")
            console.print(_("cli-lightning-report-saved", path=str(output_file)))
        else:
            console.print(report_content)

        # Show summary
        invoices = invoice_repo.find_requiring_quadro_rw(tax_year)
        console.print(_("cli-lightning-report-summary", count=len(invoices)))

    except Exception as e:
        console.print(_("cli-lightning-report-quadro-error", error=str(e)))
        raise typer.Exit(code=1)
    finally:
        session.close()


@report_app.command("capital-gains")
def generate_capital_gains_report(
    tax_year: int = typer.Option(
        ..., "--tax-year", "-y", help=_("cli-lightning-report-opt-tax-year")
    ),
    output_format: str = typer.Option(
        "csv", "--format", "-f", help=_("cli-lightning-report-opt-format")
    ),
    output_file: Path = typer.Option(
        None, "--output", "-o", help=_("cli-lightning-report-opt-output")
    ),
):
    """Generate capital gains tax report.

    Capital gains tax rate:
    - 26% for 2025
    - 33% from 2026 onwards

    This report includes all invoices with capital gains/losses for the tax year.

    Example:
        openfatture lightning report capital-gains --tax-year 2025 --format csv --output gains_2025.csv
    """
    from decimal import Decimal
    from typing import cast

    from openfatture.lightning.application.services.compliance_report_service import (
        ReportFormat,
        create_compliance_report_service,
    )
    from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository
    from openfatture.storage.database.base import get_session

    if output_format not in ["json", "csv"]:
        console.print(_("cli-lightning-report-invalid-format"))
        raise typer.Exit(code=1)

    try:
        session = get_session()
        invoice_repo = LightningInvoiceRepository(session=session)
        compliance_service = create_compliance_report_service(invoice_repository=invoice_repo)

        console.print(
            _("cli-lightning-report-gains-title", year=tax_year, format=output_format.upper())
        )

        # Safe to cast after validation
        report_content = run_async(
            compliance_service.generate_capital_gains_report(
                tax_year, output_format=cast(ReportFormat, output_format)
            )
        )

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(report_content, encoding="utf-8")
            console.print(_("cli-lightning-report-saved", path=str(output_file)))
        else:
            console.print(report_content)

        # Show summary
        invoices = invoice_repo.find_with_capital_gains(tax_year)
        if invoices:
            total_gains = sum(inv.capital_gain_eur for inv in invoices if inv.capital_gain_eur)
            tax_rate_float = 0.26 if tax_year <= 2025 else 0.33
            estimated_tax = total_gains * Decimal(str(tax_rate_float))
            console.print(_("cli-lightning-report-gains-summary-count", count=len(invoices)))
            console.print(
                _("cli-lightning-report-gains-summary-total", total=f"{total_gains:,.2f}")
            )
            console.print(
                _(
                    "cli-lightning-report-gains-summary-tax",
                    rate=int(tax_rate_float * 100),
                    tax=f"{estimated_tax:,.2f}",
                )
            )

    except Exception as e:
        console.print(_("cli-lightning-report-gains-error", error=str(e)))
        raise typer.Exit(code=1)
    finally:
        session.close()


@report_app.command("aml")
def generate_aml_report(
    threshold: float = typer.Option(
        5000.0, "--threshold", "-t", help=_("cli-lightning-aml-opt-threshold")
    ),
    output_format: str = typer.Option(
        "json", "--format", "-f", help=_("cli-lightning-aml-opt-format")
    ),
    output_file: Path = typer.Option(
        None, "--output", "-o", help=_("cli-lightning-report-opt-output")
    ),
):
    """Generate Anti-Money Laundering compliance report.

    Italian AML threshold: 5,000 EUR (D.Lgs. 231/2007)

    This report includes all payments exceeding the threshold with verification status.

    Example:
        openfatture lightning report aml --threshold 5000 --output aml_report.json
    """
    import json
    from decimal import Decimal

    from openfatture.lightning.application.services.compliance_report_service import (
        create_compliance_report_service,
    )
    from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository
    from openfatture.storage.database.base import get_session

    try:
        session = get_session()
        invoice_repo = LightningInvoiceRepository(session=session)
        compliance_service = create_compliance_report_service(invoice_repository=invoice_repo)

        console.print(_("cli-lightning-aml-report-title", threshold=f"{threshold:,.2f}"))

        report = run_async(
            compliance_service.generate_aml_compliance_report(Decimal(str(threshold)))
        )

        # Calculate compliance rate
        compliance_rate = (
            (report.total_verified / report.total_payments_over_threshold * 100)
            if report.total_payments_over_threshold > 0
            else 100.0
        )

        # Convert to JSON
        report_dict = {
            "threshold_eur": float(report.threshold_eur),
            "total_over_threshold": report.total_payments_over_threshold,
            "verified_count": report.total_verified,
            "unverified_count": report.total_pending_verification,
            "compliance_rate": compliance_rate,
            "generated_at": report.report_date.isoformat(),
            "payments_over_threshold": report.payments_requiring_action,
        }

        report_json = json.dumps(report_dict, indent=2, ensure_ascii=False)

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(report_json, encoding="utf-8")
            console.print(_("cli-lightning-report-saved", path=str(output_file)))
        else:
            console.print(report_json)

        # Show summary
        console.print(
            _("cli-lightning-aml-report-summary-total", total=report.total_payments_over_threshold)
        )
        console.print(
            _("cli-lightning-aml-report-summary-verified", verified=report.total_verified)
        )
        unverified_status = (
            _("cli-lightning-aml-report-summary-unverified-ok")
            if report.total_pending_verification == 0
            else _(
                "cli-lightning-aml-report-summary-unverified-warning",
                count=report.total_pending_verification,
            )
        )
        console.print(
            f"[{'red' if report.total_pending_verification > 0 else 'green'}]{unverified_status}[/]"
        )
        console.print(_("cli-lightning-aml-report-summary-rate", rate=f"{compliance_rate:.1f}"))

        if report.total_pending_verification > 0:
            console.print(_("cli-lightning-aml-report-action-required"))
            console.print(_("cli-lightning-aml-report-action-hint"))

    except Exception as e:
        console.print(_("cli-lightning-aml-report-error", error=str(e)))
        raise typer.Exit(code=1)
    finally:
        session.close()


# ============================================================================
# AML COMMANDS
# ============================================================================


@aml_app.command("list-unverified")
def list_unverified_aml_payments(
    threshold: float = typer.Option(
        5000.0, "--threshold", "-t", help=_("cli-lightning-aml-opt-threshold")
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help=_("cli-lightning-aml-opt-verbose")),
):
    """List all unverified AML payments exceeding threshold.

    Shows all payments over the AML threshold (default: 5,000 EUR) that
    require client identity verification according to Italian AML law (D.Lgs. 231/2007).

    Example:
        openfatture lightning aml list-unverified --threshold 5000 --verbose
    """
    from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository
    from openfatture.storage.database.base import get_session

    try:
        session = get_session()
        invoice_repo = LightningInvoiceRepository(session=session)

        console.print(_("cli-lightning-aml-list-title", threshold=f"{threshold:,.2f}"))

        unverified = invoice_repo.find_unverified_aml_payments(threshold_eur=threshold)

        if not unverified:
            console.print(_("cli-lightning-aml-list-empty"))
            return

        # Create table
        table = Table(title=_("cli-lightning-aml-list-table-title", count=len(unverified)))
        table.add_column(_("cli-lightning-aml-list-col-hash"), style="cyan")
        table.add_column(_("cli-lightning-aml-list-col-amount"), style="yellow", justify="right")
        table.add_column(_("cli-lightning-aml-list-col-settled"), style="white")
        table.add_column(_("cli-lightning-aml-list-col-fattura"), style="magenta")

        if verbose:
            table.add_column(_("cli-lightning-aml-list-col-client"), style="blue")
            table.add_column(_("cli-lightning-aml-list-col-description"), style="dim")

        for inv in unverified:
            row = [
                inv.payment_hash[:12] + "...",
                f"{inv.eur_amount_declared:,.2f} €",
                inv.settled_at.strftime("%Y-%m-%d %H:%M") if inv.settled_at else "N/A",
                str(inv.fattura_id) if inv.fattura_id else "-",
            ]

            if verbose:
                # Extract client_id from description or show N/A
                client_id = "-"
                row.extend(
                    [
                        client_id,
                        (
                            inv.description[:40] + "..."
                            if len(inv.description) > 40
                            else inv.description
                        ),
                    ]
                )

            table.add_row(*row)

        console.print(table)
        console.print()

        # Show warning
        console.print(_("cli-lightning-aml-list-action-required"))
        console.print(_("cli-lightning-aml-list-action-hint"))

    except Exception as e:
        console.print(_("cli-lightning-aml-list-error", error=str(e)))
        raise typer.Exit(code=1)
    finally:
        session.close()


@aml_app.command("verify")
def verify_aml_payment(
    payment_hash: str = typer.Argument(..., help=_("cli-lightning-aml-verify-arg-hash")),
    verified_by: str = typer.Option(
        ..., "--verified-by", "-b", help=_("cli-lightning-aml-verify-opt-by")
    ),
    notes: str = typer.Option(None, "--notes", "-n", help=_("cli-lightning-aml-verify-opt-notes")),
    client_id: int = typer.Option(
        None, "--client-id", "-c", help=_("cli-lightning-aml-verify-opt-client")
    ),
):
    """Mark an AML payment as verified.

    Records that client identity has been verified according to AML regulations.
    This should only be done after proper KYC (Know Your Customer) procedures.

    Example:
        openfatture lightning aml verify abc123... --verified-by compliance@example.com --notes "ID verified"
    """
    from datetime import UTC, datetime

    from openfatture.core.events.base import get_global_event_bus
    from openfatture.lightning.domain.events import LightningAMLVerified
    from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository
    from openfatture.storage.database.base import get_session

    try:
        session = get_session()
        invoice_repo = LightningInvoiceRepository(session=session)

        console.print(_("cli-lightning-aml-verify-title", hash=payment_hash[:12]))

        # Find invoice
        invoice = invoice_repo.find_by_payment_hash(payment_hash)
        if not invoice:
            console.print(_("cli-lightning-aml-verify-not-found", hash=payment_hash))
            raise typer.Exit(code=1)

        # Check if already verified
        if invoice.aml_verified:
            verification_date_str = (
                invoice.aml_verification_date.strftime("%Y-%m-%d")
                if invoice.aml_verification_date
                else "unknown date"
            )
            console.print(
                _("cli-lightning-aml-verify-already-verified", date=verification_date_str)
            )
            return

        # Check if exceeds threshold
        if not invoice.exceeds_aml_threshold:
            console.print(_("cli-lightning-aml-verify-below-threshold"))

        # Mark as verified
        invoice.mark_aml_verified()
        invoice_repo.save(invoice)

        # Publish event
        event = LightningAMLVerified(
            payment_hash=payment_hash,
            verified_at=datetime.now(UTC),
            verified_by=verified_by,
            client_id=client_id,
            notes=notes,
        )
        event_bus = get_global_event_bus()
        event_bus.publish(event)

        console.print(_("cli-lightning-aml-verify-success"))

        # Show summary
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_row(
            _("cli-lightning-aml-verify-label-hash"), f"[cyan]{payment_hash[:16]}...[/cyan]"
        )
        table.add_row(
            _("cli-lightning-aml-verify-label-amount"),
            (
                f"[yellow]{invoice.eur_amount_declared:,.2f} €[/yellow]"
                if invoice.eur_amount_declared
                else "[dim]N/A[/dim]"
            ),
        )
        table.add_row(
            _("cli-lightning-aml-verify-label-settled"),
            (
                f"[white]{invoice.settled_at.strftime('%Y-%m-%d %H:%M')}[/white]"
                if invoice.settled_at
                else "[dim]N/A[/dim]"
            ),
        )
        table.add_row(_("cli-lightning-aml-verify-label-by"), f"[green]{verified_by}[/green]")
        table.add_row(
            _("cli-lightning-aml-verify-label-at"),
            (
                f"[green]{invoice.aml_verification_date.strftime('%Y-%m-%d %H:%M')}[/green]"
                if invoice.aml_verification_date
                else "[dim]N/A[/dim]"
            ),
        )
        if notes:
            table.add_row(_("cli-lightning-aml-verify-label-notes"), f"[dim]{notes}[/dim]")

        console.print(table)
        console.print()

    except Exception as e:
        console.print(_("cli-lightning-aml-verify-error", error=str(e)))
        raise typer.Exit(code=1)
    finally:
        session.close()
