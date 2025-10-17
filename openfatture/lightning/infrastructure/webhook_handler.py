"""Lightning Network webhook handler for real-time payment notifications.

Handles incoming webhooks from LND and other Lightning services,
processing payment events and updating the system state accordingly.
"""

import hashlib
import hmac
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse

from ...core.events.base import get_global_event_bus
from ..domain.events import (
    LightningChannelClosed,
    LightningChannelOpened,
    LightningInvoiceCreated,
    LightningInvoiceExpired,
    LightningPaymentSettled,
)


class LightningWebhookHandler:
    """Handles Lightning Network webhook notifications.

    Processes real-time events from LND and other Lightning services,
    updating invoices, payments, and emitting domain events.
    """

    def __init__(self, webhook_secret: str | None = None):
        """Initialize the webhook handler.

        Args:
            webhook_secret: Secret for webhook signature verification
        """
        self.webhook_secret = webhook_secret
        self.event_bus = get_global_event_bus()

    async def handle_webhook(self, request: Request) -> Response:
        """Handle incoming webhook request.

        Args:
            request: FastAPI request object

        Returns:
            HTTP response

        Raises:
            HTTPException: If webhook is invalid or processing fails
        """
        try:
            # Verify webhook signature if secret is configured
            if self.webhook_secret:
                await self._verify_signature(request)

            # Parse webhook payload
            payload = await request.json()

            # Process the webhook based on type
            await self._process_webhook(payload)

            return JSONResponse(content={"status": "ok", "processed": True}, status_code=200)

        except Exception as e:
            print(f"Webhook processing error: {e}")
            raise HTTPException(status_code=500, detail="Webhook processing failed")

    async def _verify_signature(self, request: Request):
        """Verify webhook signature for security.

        Args:
            request: FastAPI request object

        Raises:
            HTTPException: If signature verification fails
        """
        # This method should only be called when webhook_secret is set
        assert (
            self.webhook_secret is not None
        ), "webhook_secret must be set for signature verification"

        signature = request.headers.get("X-LND-Signature")
        if not signature:
            raise HTTPException(status_code=401, detail="Missing webhook signature")

        # Get raw body for signature verification
        body = await request.body()

        # Verify HMAC signature
        expected_signature = hmac.new(
            self.webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    async def _process_webhook(self, payload: dict[str, Any]):
        """Process webhook payload based on event type.

        Args:
            payload: Webhook payload from LND
        """
        event_type = payload.get("event_type") or payload.get("type")

        if not event_type:
            print(f"Webhook missing event_type: {payload}")
            return

        print(f"Processing Lightning webhook: {event_type}")

        # Route to appropriate handler
        handlers = {
            "invoice_created": self._handle_invoice_created,
            "invoice_settled": self._handle_invoice_settled,
            "invoice_expired": self._handle_invoice_expired,
            "channel_opened": self._handle_channel_opened,
            "channel_closed": self._handle_channel_closed,
            "payment_received": self._handle_payment_received,
            "payment_sent": self._handle_payment_sent,
        }

        handler = handlers.get(event_type)
        if handler:
            await handler(payload)
        else:
            print(f"Unknown webhook event type: {event_type}")

    async def _handle_invoice_created(self, payload: dict[str, Any]):
        """Handle invoice creation event."""
        # Extract invoice data from payload
        invoice_data = payload.get("invoice", {})

        # Create domain event
        event = LightningInvoiceCreated(
            payment_hash=invoice_data.get("payment_hash", ""),
            payment_request=invoice_data.get("payment_request", ""),
            amount_msat=invoice_data.get("amount_msat"),
            description=invoice_data.get("description", ""),
            expiry_timestamp=invoice_data.get("expiry_timestamp", 0),
            fattura_id=invoice_data.get("custom_data", {}).get("fattura_id"),
        )

        await self.event_bus.publish_async(event)

    async def _handle_invoice_settled(self, payload: dict[str, Any]):
        """Handle invoice settlement event."""
        invoice_data = payload.get("invoice", {})

        # Create payment settled event
        event = LightningPaymentSettled(
            payment_hash=invoice_data.get("payment_hash", ""),
            preimage=invoice_data.get("preimage", ""),
            amount_msat=invoice_data.get("amount_msat", 0),
            fee_paid_msat=invoice_data.get("fee_paid_msat"),
            settled_at=datetime.fromtimestamp(
                invoice_data.get("settled_at", datetime.now(UTC).timestamp()), UTC
            ),
            fattura_id=invoice_data.get("custom_data", {}).get("fattura_id"),
        )

        await self.event_bus.publish_async(event)

    async def _handle_invoice_expired(self, payload: dict[str, Any]):
        """Handle invoice expiry event."""
        invoice_data = payload.get("invoice", {})

        event = LightningInvoiceExpired(
            payment_hash=invoice_data.get("payment_hash", ""),
            expiry_timestamp=invoice_data.get("expiry_timestamp", 0),
            created_at=datetime.fromtimestamp(
                invoice_data.get("created_at", datetime.now(UTC).timestamp()), UTC
            ),
            fattura_id=invoice_data.get("custom_data", {}).get("fattura_id"),
        )

        await self.event_bus.publish_async(event)

    async def _handle_channel_opened(self, payload: dict[str, Any]):
        """Handle channel opened event."""
        channel_data = payload.get("channel", {})

        event = LightningChannelOpened(
            channel_id=channel_data.get("channel_id", ""),
            peer_pubkey=channel_data.get("peer_pubkey", ""),
            capacity_sat=channel_data.get("capacity_sat", 0),
            local_balance_sat=channel_data.get("local_balance_sat", 0),
            remote_balance_sat=channel_data.get("remote_balance_sat", 0),
        )

        await self.event_bus.publish_async(event)

    async def _handle_channel_closed(self, payload: dict[str, Any]):
        """Handle channel closed event."""
        channel_data = payload.get("channel", {})

        event = LightningChannelClosed(
            channel_id=channel_data.get("channel_id", ""),
            peer_pubkey=channel_data.get("peer_pubkey", ""),
            capacity_sat=channel_data.get("capacity_sat", 0),
            final_balance_sat=channel_data.get("final_balance_sat", 0),
            close_type=channel_data.get("close_type", "cooperative"),
        )

        await self.event_bus.publish_async(event)

    async def _handle_payment_received(self, payload: dict[str, Any]):
        """Handle payment received event (alternative to invoice_settled)."""
        # This might be a duplicate of invoice_settled, but handle it anyway
        payment_data = payload.get("payment", {})

        # Only process if we have the necessary data
        if "payment_hash" in payment_data and "preimage" in payment_data:
            event = LightningPaymentSettled(
                payment_hash=payment_data["payment_hash"],
                preimage=payment_data["preimage"],
                amount_msat=payment_data.get("amount_msat", 0),
                fee_paid_msat=payment_data.get("fee_paid_msat"),
                settled_at=datetime.now(UTC),
                fattura_id=payment_data.get("custom_data", {}).get("fattura_id"),
            )

            await self.event_bus.publish_async(event)

    async def _handle_payment_sent(self, payload: dict[str, Any]):
        """Handle payment sent event."""
        # For now, just log outgoing payments
        # Could emit a custom event for payment tracking
        payment_data = payload.get("payment", {})
        print(f"Outgoing Lightning payment: {payment_data.get('payment_hash', 'unknown')}")

    async def health_check(self) -> dict[str, Any]:
        """Health check for webhook handler.

        Returns:
            Health status information
        """
        return {
            "status": "healthy",
            "webhook_secret_configured": self.webhook_secret is not None,
            "timestamp": datetime.now(UTC).isoformat(),
        }


# FastAPI route helper
def create_lightning_webhook_route(handler: LightningWebhookHandler):
    """Create a FastAPI route for Lightning webhooks.

    Returns:
        FastAPI route function
    """

    async def lightning_webhook(request: Request) -> Response:
        return await handler.handle_webhook(request)

    return lightning_webhook


# Standalone webhook server for testing/development
async def run_webhook_server(
    host: str = "0.0.0.0", port: int = 8080, webhook_secret: str | None = None
):
    """Run a standalone webhook server for testing.

    Args:
        host: Server host
        port: Server port
        webhook_secret: Webhook secret for signature verification
    """
    from fastapi import FastAPI

    app = FastAPI(title="OpenFatture Lightning Webhook Server")
    handler = LightningWebhookHandler(webhook_secret=webhook_secret)

    @app.post("/webhook/lightning")
    async def lightning_webhook(request: Request) -> Response:
        return await handler.handle_webhook(request)

    @app.get("/health")
    async def health():
        return await handler.health_check()

    print(f"Starting Lightning webhook server on {host}:{port}")
    print(f"Webhook endpoint: POST http://{host}:{port}/webhook/lightning")

    # Note: In production, use a proper ASGI server like uvicorn
    import uvicorn

    config = uvicorn.Config(app, host=host, port=port)
    server = uvicorn.Server(config)
    await server.serve()
