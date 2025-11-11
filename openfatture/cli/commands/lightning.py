"""Lightning Network payment management commands."""

import asyncio
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="lightning", help="⚡ Lightning Network payment management", no_args_is_help=True
)
console = Console()

# Sub-commands for compliance
report_app = typer.Typer(name="report", help="📊 Generate compliance reports", no_args_is_help=True)
aml_app = typer.Typer(name="aml", help="🔍 Anti-Money Laundering management", no_args_is_help=True)

app.add_typer(report_app)
app.add_typer(aml_app)


@app.command("status")
def lightning_status():
    """Show Lightning Network status."""
    from openfatture.utils.config import get_settings

    settings = get_settings()

    typer.echo("⚡ Lightning Network Status")

    if not settings.lightning_enabled:
        typer.echo("Status: ❌ Disabled")
        typer.echo("Set lightning_enabled=true in .env to enable Lightning payments")
        typer.echo("Use 'openfatture config set lightning_enabled true' to enable")
        return

    typer.echo("Status: ✅ Enabled")
    typer.echo(f"Host: {settings.lightning_host}")
    typer.echo(f"Timeout: {settings.lightning_timeout_seconds}s")
    typer.echo(f"Max retries: {settings.lightning_max_retries}")
    typer.echo(
        f"BTC Provider: {'CoinGecko' if settings.lightning_coingecko_enabled else 'CoinMarketCap' if settings.lightning_cmc_enabled else 'Fallback'}"
    )
    typer.echo(
        f"Liquidity monitoring: {'Enabled' if settings.lightning_liquidity_enabled else 'Disabled'}"
    )


@app.command("invoice")
def create_invoice():
    """Create a Lightning invoice."""
    from openfatture.utils.config import get_settings

    if not get_settings().lightning_enabled:
        typer.echo(
            "❌ Lightning is disabled. Enable with: openfatture config set lightning_enabled true"
        )
        return

    typer.echo("⚡ Lightning Invoice Creation")
    typer.echo("Feature not yet available - Lightning integration in development")


@app.command("channels")
def list_channels():
    """List Lightning channels."""
    from openfatture.utils.config import get_settings

    if not get_settings().lightning_enabled:
        typer.echo(
            "❌ Lightning is disabled. Enable with: openfatture config set lightning_enabled true"
        )
        return

    typer.echo("⚡ Lightning Channels")
    typer.echo("No channels configured - Lightning integration in development")


@app.command("liquidity")
def check_liquidity():
    """Check channel liquidity."""
    from openfatture.utils.config import get_settings

    if not get_settings().lightning_enabled:
        typer.echo(
            "❌ Lightning is disabled. Enable with: openfatture config set lightning_enabled true"
        )
        return

    typer.echo("⚡ Channel Liquidity")
    typer.echo("Liquidity monitoring not available - Lightning integration in development")


# ============================================================================
# COMPLIANCE COMMANDS (Italian Tax & AML Regulations)
# ============================================================================


@app.command("compliance-check")
def compliance_check(
    tax_year: int = typer.Option(
        datetime.now().year, "--tax-year", "-y", help="Tax year to check (default: current year)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
):
    """🔍 Run comprehensive compliance check for Italian tax and AML regulations.

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

        console.print(f"\n[bold cyan]🔍 Lightning Compliance Check - {tax_year}[/bold cyan]\n")

        # 1. Tax Year Summary
        summary = asyncio.run(compliance_service.generate_tax_year_summary(tax_year))

        console.print("[bold]📊 Tax Year Summary[/bold]")
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_row("Number of payments:", f"[cyan]{summary.num_payments}[/cyan]")
        table.add_row("Total revenue (EUR):", f"[green]{summary.total_revenue_eur:,.2f} €[/green]")
        table.add_row(
            "Total capital gains (EUR):",
            f"[yellow]{summary.total_capital_gains_eur:,.2f} €[/yellow]",
        )
        table.add_row(
            "Estimated tax owed (EUR):", f"[red]{summary.total_tax_owed_eur:,.2f} €[/red]"
        )
        console.print(table)
        console.print()

        # 2. AML Compliance
        console.print("[bold]🛡️ AML Compliance (Threshold: 5,000 EUR)[/bold]")
        aml_table = Table(show_header=False, box=None, padding=(0, 2))
        aml_table.add_row("Total over threshold:", f"[cyan]{summary.num_aml_alerts}[/cyan]")
        aml_table.add_row("Verified:", f"[green]{summary.num_aml_verified}[/green]")
        unverified = summary.num_aml_alerts - summary.num_aml_verified
        status = "✅ OK" if unverified == 0 else f"⚠️  {unverified} REQUIRE VERIFICATION"
        aml_table.add_row("Unverified:", f"[{'green' if unverified == 0 else 'red'}]{status}[/]")
        console.print(aml_table)
        console.print()

        # 3. Quadro RW Check
        quadro_rw_invoices = invoice_repo.find_requiring_quadro_rw(tax_year)
        console.print("[bold]📋 Quadro RW Declaration (Mandatory from 2025)[/bold]")
        quadro_table = Table(show_header=False, box=None, padding=(0, 2))
        quadro_table.add_row(
            "Invoices requiring declaration:", f"[cyan]{len(quadro_rw_invoices)}[/cyan]"
        )
        if len(quadro_rw_invoices) > 0:
            quadro_table.add_row(
                "Action required:",
                "[yellow]⚠️  Declare all crypto holdings in Quadro RW[/yellow]",
            )
        else:
            quadro_table.add_row("Status:", "[green]✅ No declarations required[/green]")
        console.print(quadro_table)
        console.print()

        # 4. Missing Tax Data
        missing_data = invoice_repo.find_with_missing_tax_data()
        console.print("[bold]⚠️  Data Quality[/bold]")
        missing_table = Table(show_header=False, box=None, padding=(0, 2))
        missing_table.add_row(
            "Invoices with missing tax data:",
            f"[{'red' if missing_data else 'green'}]{len(missing_data)}[/]",
        )
        if missing_data:
            missing_table.add_row(
                "Action required:",
                "[red]❌ Add BTC/EUR rate and EUR amount for tax compliance[/red]",
            )
        else:
            missing_table.add_row("Status:", "[green]✅ All settled invoices have tax data[/green]")
        console.print(missing_table)
        console.print()

        # Overall Status
        issues = []
        if unverified > 0:
            issues.append(f"{unverified} unverified AML payment(s)")
        if len(missing_data) > 0:
            issues.append(f"{len(missing_data)} invoice(s) missing tax data")

        if issues:
            console.print(f"[bold red]❌ Compliance Issues Found: {', '.join(issues)}[/bold red]\n")
            raise typer.Exit(code=1)
        else:
            console.print("[bold green]✅ All Compliance Checks Passed[/bold green]\n")

        # Verbose output
        if verbose and unverified > 0:
            console.print("[bold]Unverified AML Payments:[/bold]")
            unverified_payments = invoice_repo.find_unverified_aml_payments(5000.0)
            for inv in unverified_payments:
                console.print(
                    f"  • {inv.payment_hash[:8]}... - {inv.eur_amount_declared:,.2f} EUR - "
                    f"Settled: {inv.settled_at.strftime('%Y-%m-%d') if inv.settled_at else 'N/A'}"
                )
            console.print()

    except Exception as e:
        console.print(f"[bold red]❌ Error running compliance check: {e}[/bold red]")
        raise typer.Exit(code=1)
    finally:
        session.close()


# ============================================================================
# REPORT COMMANDS
# ============================================================================


@report_app.command("quadro-rw")
def generate_quadro_rw_report(
    tax_year: int = typer.Option(..., "--tax-year", "-y", help="Tax year for report"),
    output_format: str = typer.Option("json", "--format", "-f", help="Output format: json or csv"),
    output_file: Path = typer.Option(
        None, "--output", "-o", help="Output file path (optional, prints to stdout if not provided)"
    ),
):
    """📋 Generate Quadro RW declaration report.

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
        console.print("[bold red]❌ Invalid format. Use 'json' or 'csv'[/bold red]")
        raise typer.Exit(code=1)

    try:
        session = get_session()
        invoice_repo = LightningInvoiceRepository(session=session)
        compliance_service = create_compliance_report_service(invoice_repository=invoice_repo)

        console.print(
            f"\n[bold cyan]📋 Generating Quadro RW Report - {tax_year} ({output_format.upper()})[/bold cyan]\n"
        )

        # Safe to cast after validation
        report_content = asyncio.run(
            compliance_service.generate_quadro_rw_report(
                tax_year, output_format=cast(ReportFormat, output_format)
            )
        )

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(report_content, encoding="utf-8")
            console.print(f"[green]✅ Report saved to: {output_file}[/green]\n")
        else:
            console.print(report_content)

        # Show summary
        invoices = invoice_repo.find_requiring_quadro_rw(tax_year)
        console.print(f"[cyan]📊 Total invoices in report: {len(invoices)}[/cyan]")

    except Exception as e:
        console.print(f"[bold red]❌ Error generating Quadro RW report: {e}[/bold red]")
        raise typer.Exit(code=1)
    finally:
        session.close()


@report_app.command("capital-gains")
def generate_capital_gains_report(
    tax_year: int = typer.Option(..., "--tax-year", "-y", help="Tax year for report"),
    output_format: str = typer.Option("csv", "--format", "-f", help="Output format: json or csv"),
    output_file: Path = typer.Option(
        None, "--output", "-o", help="Output file path (optional, prints to stdout if not provided)"
    ),
):
    """💰 Generate capital gains tax report.

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
        console.print("[bold red]❌ Invalid format. Use 'json' or 'csv'[/bold red]")
        raise typer.Exit(code=1)

    try:
        session = get_session()
        invoice_repo = LightningInvoiceRepository(session=session)
        compliance_service = create_compliance_report_service(invoice_repository=invoice_repo)

        console.print(
            f"\n[bold cyan]💰 Generating Capital Gains Report - {tax_year} ({output_format.upper()})[/bold cyan]\n"
        )

        # Safe to cast after validation
        report_content = asyncio.run(
            compliance_service.generate_capital_gains_report(
                tax_year, output_format=cast(ReportFormat, output_format)
            )
        )

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(report_content, encoding="utf-8")
            console.print(f"[green]✅ Report saved to: {output_file}[/green]\n")
        else:
            console.print(report_content)

        # Show summary
        invoices = invoice_repo.find_with_capital_gains(tax_year)
        if invoices:
            total_gains = sum(inv.capital_gain_eur for inv in invoices if inv.capital_gain_eur)
            tax_rate_float = 0.26 if tax_year <= 2025 else 0.33
            estimated_tax = total_gains * Decimal(str(tax_rate_float))
            console.print(f"[cyan]📊 Total invoices with gains: {len(invoices)}[/cyan]")
            console.print(f"[yellow]💰 Total capital gains: {total_gains:,.2f} EUR[/yellow]")
            console.print(
                f"[red]💸 Estimated tax ({int(tax_rate_float * 100)}%): {estimated_tax:,.2f} EUR[/red]"
            )

    except Exception as e:
        console.print(f"[bold red]❌ Error generating capital gains report: {e}[/bold red]")
        raise typer.Exit(code=1)
    finally:
        session.close()


@report_app.command("aml")
def generate_aml_report(
    threshold: float = typer.Option(5000.0, "--threshold", "-t", help="AML threshold in EUR"),
    output_format: str = typer.Option("json", "--format", "-f", help="Output format: json only"),
    output_file: Path = typer.Option(
        None, "--output", "-o", help="Output file path (optional, prints to stdout if not provided)"
    ),
):
    """🛡️ Generate Anti-Money Laundering compliance report.

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

        console.print(
            f"\n[bold cyan]🛡️ Generating AML Compliance Report (Threshold: {threshold:,.2f} EUR)[/bold cyan]\n"
        )

        report = asyncio.run(
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
            console.print(f"[green]✅ Report saved to: {output_file}[/green]\n")
        else:
            console.print(report_json)

        # Show summary
        console.print(
            f"[cyan]📊 Total over threshold: {report.total_payments_over_threshold}[/cyan]"
        )
        console.print(f"[green]✅ Verified: {report.total_verified}[/green]")
        console.print(
            f"[{'red' if report.total_pending_verification > 0 else 'green'}]{'⚠️ ' if report.total_pending_verification > 0 else '✅ '}Unverified: {report.total_pending_verification}[/]"
        )
        console.print(f"[yellow]📈 Compliance rate: {compliance_rate:.1f}%[/yellow]")

        if report.total_pending_verification > 0:
            console.print(
                "\n[bold yellow]⚠️  Action Required: Verify unverified payments with AML process[/bold yellow]"
            )
            console.print(
                "[dim]Use: openfatture lightning aml list-unverified to see details[/dim]\n"
            )

    except Exception as e:
        console.print(f"[bold red]❌ Error generating AML report: {e}[/bold red]")
        raise typer.Exit(code=1)
    finally:
        session.close()


# ============================================================================
# AML COMMANDS
# ============================================================================


@aml_app.command("list-unverified")
def list_unverified_aml_payments(
    threshold: float = typer.Option(5000.0, "--threshold", "-t", help="AML threshold in EUR"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
):
    """🔍 List all unverified AML payments exceeding threshold.

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

        console.print(
            f"\n[bold cyan]🔍 Unverified AML Payments (Threshold: {threshold:,.2f} EUR)[/bold cyan]\n"
        )

        unverified = invoice_repo.find_unverified_aml_payments(threshold_eur=threshold)

        if not unverified:
            console.print("[green]✅ No unverified payments found[/green]\n")
            return

        # Create table
        table = Table(title=f"Unverified Payments ({len(unverified)} total)")
        table.add_column("Payment Hash", style="cyan")
        table.add_column("Amount (EUR)", style="yellow", justify="right")
        table.add_column("Settled At", style="white")
        table.add_column("Fattura ID", style="magenta")

        if verbose:
            table.add_column("Client ID", style="blue")
            table.add_column("Description", style="dim")

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
        console.print(
            "[bold yellow]⚠️  Action Required: These payments require client identity verification[/bold yellow]"
        )
        console.print(
            "[dim]Use: openfatture lightning aml verify <payment-hash> --verified-by <email>[/dim]\n"
        )

    except Exception as e:
        console.print(f"[bold red]❌ Error listing unverified payments: {e}[/bold red]")
        raise typer.Exit(code=1)
    finally:
        session.close()


@aml_app.command("verify")
def verify_aml_payment(
    payment_hash: str = typer.Argument(..., help="Payment hash to verify"),
    verified_by: str = typer.Option(..., "--verified-by", "-b", help="Email of person verifying"),
    notes: str = typer.Option(None, "--notes", "-n", help="Verification notes (optional)"),
    client_id: int = typer.Option(None, "--client-id", "-c", help="Client ID (optional)"),
):
    """✅ Mark an AML payment as verified.

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

        console.print(
            f"\n[bold cyan]✅ Verifying AML Payment: {payment_hash[:12]}...[/bold cyan]\n"
        )

        # Find invoice
        invoice = invoice_repo.find_by_payment_hash(payment_hash)
        if not invoice:
            console.print(f"[bold red]❌ Invoice not found: {payment_hash}[/bold red]")
            raise typer.Exit(code=1)

        # Check if already verified
        if invoice.aml_verified:
            verification_date_str = (
                invoice.aml_verification_date.strftime("%Y-%m-%d")
                if invoice.aml_verification_date
                else "unknown date"
            )
            console.print(
                f"[yellow]⚠️  Payment already verified on {verification_date_str}[/yellow]"
            )
            return

        # Check if exceeds threshold
        if not invoice.exceeds_aml_threshold:
            console.print(
                "[yellow]⚠️  Payment does not exceed AML threshold, but marking as verified anyway[/yellow]"
            )

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

        console.print("[green]✅ Payment verified successfully[/green]\n")

        # Show summary
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_row("Payment Hash:", f"[cyan]{payment_hash[:16]}...[/cyan]")
        table.add_row(
            "Amount (EUR):",
            (
                f"[yellow]{invoice.eur_amount_declared:,.2f} €[/yellow]"
                if invoice.eur_amount_declared
                else "[dim]N/A[/dim]"
            ),
        )
        table.add_row(
            "Settled At:",
            (
                f"[white]{invoice.settled_at.strftime('%Y-%m-%d %H:%M')}[/white]"
                if invoice.settled_at
                else "[dim]N/A[/dim]"
            ),
        )
        table.add_row("Verified By:", f"[green]{verified_by}[/green]")
        table.add_row(
            "Verified At:",
            (
                f"[green]{invoice.aml_verification_date.strftime('%Y-%m-%d %H:%M')}[/green]"
                if invoice.aml_verification_date
                else "[dim]N/A[/dim]"
            ),
        )
        if notes:
            table.add_row("Notes:", f"[dim]{notes}[/dim]")

        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"[bold red]❌ Error verifying payment: {e}[/bold red]")
        raise typer.Exit(code=1)
    finally:
        session.close()
