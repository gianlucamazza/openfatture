"""Per-tool resilience: bulkheads and circuit-breaker policies.

Read tools tolerate more concurrency and failures than write tools; any other
tool gets the library defaults.
"""

from __future__ import annotations

import asyncio

from openfatture.ai.orchestration.resilience import BulkheadConfig, CircuitBreakerConfig

_READ_TOOLS = frozenset(
    {
        "search_invoices",
        "get_invoice_details",
        "get_invoice_stats",
        "search_clients",
        "get_client_details",
        "get_client_stats",
        "search_knowledge_base",
        "generate_vat_report",
        "generate_client_report",
        "get_due_dates",
        "export_invoices_to_csv",
        "export_clients_to_csv",
        "search_preventivi",
        "get_preventivo_details",
        "get_payment_status",
        "search_payments",
        "search_bank_transactions",
        "get_payment_stats",
        "search_prodotti",
        "get_prodotto_details",
        "get_pdf_configuration",
        "list_sdi_notifications",
        "get_sdi_notification_details",
        "check_invoice_sdi_status",
        "verify_signature",
        "check_certificate_status",
    }
)

# XML validation is read-only for the circuit breaker; its bulkhead keeps the defaults.
_CIRCUIT_READ_TOOLS = _READ_TOOLS | {"validate_invoice_xml"}

_WRITE_TOOLS = frozenset(
    {
        "create_invoice",
        "create_riga",
        "send_invoice_to_sdi",
        "create_client",
        "update_client",
        "delete_invoice",
        "reconcile_payment",
        "import_invoices_from_csv",
        "import_clients_from_csv",
        "bulk_update_invoices_status",
        "create_preventivo",
        "update_preventivo_status",
        "convert_preventivo_to_invoice",
        "create_prodotto",
        "update_prodotto",
        "delete_prodotto",
        "generate_invoice_pdf",
        "generate_preventivo_pdf",
        "process_sdi_notification_file",
        "sign_invoice_xml",
        "update_invoice",
        "update_invoice_status",
        "delete_client",
        "update_preventivo",
        "delete_preventivo",
        "update_riga",
        "delete_riga",
        "create_manual_payment",
        "update_payment",
        "delete_payment",
        "import_bank_transactions",
    }
)


def bulkhead_config_for(tool_name: str) -> BulkheadConfig:
    """Concurrency limits: reads run wider and wait longer than writes."""
    if tool_name in _READ_TOOLS:
        return BulkheadConfig(max_concurrent_executions=10, acquisition_timeout_seconds=15.0)
    if tool_name in _WRITE_TOOLS:
        return BulkheadConfig(max_concurrent_executions=2, acquisition_timeout_seconds=5.0)
    return BulkheadConfig()


def circuit_breaker_config_for(tool_name: str) -> CircuitBreakerConfig:
    """Failure policy: reads are lenient and recover fast, writes trip early."""
    if tool_name in _CIRCUIT_READ_TOOLS:
        return CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=3,
            timeout_seconds=30,
            half_open_max_calls=5,
        )
    if tool_name in _WRITE_TOOLS:
        return CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=1,
            timeout_seconds=120,
            half_open_max_calls=2,
        )
    return CircuitBreakerConfig()


class Bulkhead:
    """Concurrency limit for one tool that counts its waiting and running callers.

    ``queued`` is the number of callers currently blocked in :meth:`acquire`;
    ``active`` is the number holding a slot.
    """

    def __init__(self, config: BulkheadConfig) -> None:
        self.config = config
        self._semaphore = asyncio.Semaphore(config.max_concurrent_executions)
        self._queued = 0
        self._active = 0

    @property
    def queued(self) -> int:
        return self._queued

    @property
    def active(self) -> int:
        return self._active

    async def acquire(self) -> bool:
        """Wait for a slot; return False when the acquisition timeout expires."""
        self._queued += 1
        try:
            await asyncio.wait_for(
                self._semaphore.acquire(), timeout=self.config.acquisition_timeout_seconds
            )
        except TimeoutError:
            return False
        finally:
            self._queued -= 1
        self._active += 1
        return True

    def release(self) -> None:
        """Give back a slot obtained with :meth:`acquire`."""
        self._active -= 1
        self._semaphore.release()
