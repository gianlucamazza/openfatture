"""CLI commands for Lightning Network management."""

import asyncio
from decimal import Decimal

import typer

from ..application.services.invoice_service import LightningInvoiceService
from ..application.services.payment_service import LightningPaymentService
from ..infrastructure.lnd_client import LNDClient
from ..infrastructure.repository import LightningInvoiceRepository

# CLI app
app = typer.Typer(name="lightning", help="Lightning Network payment management commands")


def get_lnd_client() -> LNDClient:
    """Get configured LND client."""
    # In production, this would read from settings
    # For now, use mock client
    return LNDClient()


def get_services():
    """Get Lightning services."""
    lnd_client = get_lnd_client()
    invoice_repo = LightningInvoiceRepository()
    invoice_service = LightningInvoiceService(lnd_client)
    payment_service = LightningPaymentService(lnd_client, invoice_repo)

    return invoice_service, payment_service


@app.command()
def info():
    """Show Lightning node information."""

    async def _info():
        lnd_client = get_lnd_client()
        try:
            node_info = await lnd_client.get_node_info()
            typer.echo("Lightning Node Information:")
            typer.echo(f"  Pubkey: {node_info.pubkey}")
            typer.echo(f"  Alias: {node_info.alias}")
            typer.echo(f"  Color: {node_info.color}")
            typer.echo(f"  Peers: {node_info.num_peers}")
            typer.echo(f"  Channels: {node_info.num_channels}")
            typer.echo(f"  Total Capacity: {node_info.total_capacity_sat:,} sat")
            typer.echo(f"  Synced: {node_info.is_synced}")
        except Exception as e:
            typer.echo(f"Error getting node info: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_info())


@app.command()
def channels():
    """List Lightning channels."""

    async def _channels():
        lnd_client = get_lnd_client()
        try:
            channels = await lnd_client.list_channels()
            if not channels:
                typer.echo("No channels found")
                return

            typer.echo("Lightning Channels:")
            typer.echo("-" * 80)
            for ch in channels:
                typer.echo(f"Channel ID: {ch.channel_id}")
                typer.echo(f"  Peer: {ch.peer_alias or ch.peer_pubkey[:16]}...")
                typer.echo(f"  Capacity: {ch.capacity_sat:,} sat")
                typer.echo(f"  Local Balance: {ch.local_balance_sat:,} sat")
                typer.echo(f"  Remote Balance: {ch.remote_balance_sat:,} sat")
                typer.echo(f"  Inbound Capacity: {ch.inbound_capacity_sat:,} sat")
                typer.echo(f"  Status: {ch.status}")
                typer.echo()

        except Exception as e:
            typer.echo(f"Error listing channels: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_channels())


@app.command()
def balance():
    """Show Lightning wallet balance."""

    async def _balance():
        lnd_client = get_lnd_client()
        try:
            # In a real LND client, this would be a separate call
            # For mock, we'll show channel balances
            channels = await lnd_client.list_channels()

            total_local = sum(ch.local_balance_sat for ch in channels)
            total_remote = sum(ch.remote_balance_sat for ch in channels)

            typer.echo("Lightning Wallet Balance:")
            typer.echo(f"  Total Local Balance: {total_local:,} sat")
            typer.echo(f"  Total Remote Balance: {total_remote:,} sat")
            typer.echo(f"  Total Capacity: {total_local + total_remote:,} sat")

        except Exception as e:
            typer.echo(f"Error getting balance: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_balance())


@app.command()
def create_invoice(
    amount: int | None = typer.Option(None, help="Amount in satoshis (omit for zero-amount)"),
    description: str = typer.Option(..., help="Invoice description"),
    expiry_hours: int = typer.Option(24, help="Invoice expiry in hours"),
):
    """Create a new Lightning invoice."""

    async def _create_invoice():
        invoice_service, _ = get_services()

        try:
            if amount:
                # Convert sat to EUR for service (mock conversion)
                eur_amount = Decimal(str(amount)) / Decimal("100000000") * Decimal("45000")
                invoice = await invoice_service.create_zero_amount_invoice(
                    description=description, expiry_hours=expiry_hours
                )
                # Override amount for display
                invoice = invoice._replace(amount_msat=amount * 1000)
            else:
                invoice = await invoice_service.create_zero_amount_invoice(
                    description=description, expiry_hours=expiry_hours
                )

            typer.echo("Lightning Invoice Created:")
            typer.echo(f"  Payment Hash: {invoice.payment_hash}")
            typer.echo(f"  Amount: {invoice.amount_sat or 'Zero-amount'} sat")
            typer.echo(f"  Description: {invoice.description}")
            typer.echo(f"  Expiry: {invoice.expires_at}")
            typer.echo()
            typer.echo("Payment Request:")
            typer.echo(invoice.payment_request)
            typer.echo()
            typer.echo("⚡ Use this payment request in your Lightning wallet")

        except Exception as e:
            typer.echo(f"Error creating invoice: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_create_invoice())


@app.command()
def list_invoices(
    status: str | None = typer.Option(None, help="Filter by status (pending, settled, expired)"),
    limit: int = typer.Option(10, help="Maximum number of invoices to show"),
):
    """List Lightning invoices."""

    async def _list_invoices():
        _, payment_service = get_services()
        invoice_repo = LightningInvoiceRepository()

        try:
            if status:
                if status == "pending":
                    invoices = invoice_repo.find_pending()
                elif status == "settled":
                    # This would need a proper query method
                    invoices = []
                elif status == "expired":
                    invoices = invoice_repo.find_expired_pending()
                else:
                    typer.echo(f"Invalid status: {status}", err=True)
                    raise typer.Exit(1)
            else:
                # Get recent invoices (this would need a proper query)
                invoices = invoice_repo.find_pending()[:limit]

            if not invoices:
                typer.echo("No invoices found")
                return

            typer.echo("Lightning Invoices:")
            typer.echo("-" * 100)
            for inv in invoices[:limit]:
                typer.echo(f"Hash: {inv.payment_hash[:16]}...")
                typer.echo(f"  Amount: {inv.amount_sat or 'Zero-amount'} sat")
                typer.echo(f"  Status: {inv.status.value}")
                typer.echo(f"  Created: {inv.created_at}")
                typer.echo(f"  Expires: {inv.expires_at}")
                if inv.fattura_id:
                    typer.echo(f"  Fattura ID: {inv.fattura_id}")
                typer.echo()

        except Exception as e:
            typer.echo(f"Error listing invoices: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_list_invoices())


@app.command()
def decode_invoice(payment_request: str):
    """Decode a Lightning invoice (BOLT-11)."""

    async def _decode_invoice():
        invoice_service, _ = get_services()

        try:
            if not invoice_service.validate_bolt11_invoice(payment_request):
                typer.echo("Invalid BOLT-11 invoice format", err=True)
                raise typer.Exit(1)

            typer.echo("Invoice appears valid (full decoding requires lightning-payencode library)")
            typer.echo(f"Payment Request: {payment_request}")

            # Try to extract basic info from the string
            if payment_request.startswith("lnbc"):
                typer.echo("Network: Bitcoin mainnet")
            elif payment_request.startswith("lntb"):
                typer.echo("Network: Bitcoin testnet")

        except Exception as e:
            typer.echo(f"Error decoding invoice: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_decode_invoice())


@app.command()
def monitor_start():
    """Start payment monitoring."""

    async def _monitor_start():
        _, payment_service = get_services()

        try:
            await payment_service.start_monitoring()
            typer.echo("Lightning payment monitoring started")
            typer.echo("Press Ctrl+C to stop...")

            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            await payment_service.stop_monitoring()
            typer.echo("\nLightning payment monitoring stopped")
        except Exception as e:
            typer.echo(f"Error in payment monitoring: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_monitor_start())


@app.command()
def monitor_stop():
    """Stop payment monitoring."""

    async def _monitor_stop():
        _, payment_service = get_services()

        try:
            await payment_service.stop_monitoring()
            typer.echo("Lightning payment monitoring stopped")
        except Exception as e:
            typer.echo(f"Error stopping monitoring: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_monitor_stop())


@app.command()
def stats():
    """Show Lightning payment statistics."""

    async def _stats():
        _, payment_service = get_services()

        try:
            stats = await payment_service.get_payment_stats()

            typer.echo("Lightning Payment Statistics (30 days):")
            typer.echo(f"  Total Payments: {stats['total_payments_30d']}")
            typer.echo(f"  Total Amount: {stats['total_amount_msat_30d']:,} msat")
            typer.echo(f"  Total Fees: {stats['total_fees_msat_30d']:,} msat")
            typer.echo(f"  Average Payment: {stats['average_payment_msat']:,.0f} msat")
            typer.echo(f"  Average Fee: {stats['average_fee_msat']:,.0f} msat")
            typer.echo(f"  Success Rate: {stats['success_rate']:.1%}")

        except Exception as e:
            typer.echo(f"Error getting statistics: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_stats())


@app.command()
def simulate_payment(payment_hash: str):
    """Simulate a payment for testing (development only)."""

    async def _simulate_payment():
        _, payment_service = get_services()

        try:
            success = await payment_service.simulate_payment(payment_hash)
            if success:
                typer.echo(f"✓ Payment simulated for invoice: {payment_hash[:8]}...")
            else:
                typer.echo("✗ Payment simulation failed", err=True)
                raise typer.Exit(1)

        except Exception as e:
            typer.echo(f"Error simulating payment: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_simulate_payment())


if __name__ == "__main__":
    app()
