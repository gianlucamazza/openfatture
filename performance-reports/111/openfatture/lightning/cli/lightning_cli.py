"""Internal Lightning helpers (not registered on the public CLI).

Production paths must use settings + honest LND client (no silent mock).
"""

from __future__ import annotations

from openfatture.lightning.application.services.invoice_service import LightningInvoiceService
from openfatture.lightning.application.services.payment_service import LightningPaymentService
from openfatture.lightning.infrastructure.lnd_client import ProductionLNDClient
from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository
from openfatture.platform.config import get_settings


def get_lnd_client() -> ProductionLNDClient:
    """Build LND client from application settings."""
    settings = get_settings()
    return ProductionLNDClient(
        host=settings.lightning_host,
        cert_path=settings.lightning_cert_path,
        macaroon_path=settings.lightning_macaroon_path,
        timeout_seconds=settings.lightning_timeout_seconds,
        max_retries=settings.lightning_max_retries,
        circuit_breaker_failures=settings.lightning_circuit_breaker_failures,
        circuit_breaker_timeout=settings.lightning_circuit_breaker_timeout,
        allow_mock=settings.lightning_allow_mock,
    )


def get_services() -> tuple[LightningInvoiceService, LightningPaymentService]:
    """Get Lightning application services."""
    lnd_client = get_lnd_client()
    invoice_repo = LightningInvoiceRepository()
    invoice_service = LightningInvoiceService(lnd_client)
    payment_service = LightningPaymentService(lnd_client, invoice_repo)
    return invoice_service, payment_service
