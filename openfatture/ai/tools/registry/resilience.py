"""Per-tool resilience: bulkheads and circuit-breaker policies.

Read tools tolerate more concurrency and failures than tools that write;
a tool of unknown risk gets the library defaults.
"""

from __future__ import annotations

import asyncio

from openfatture.ai.orchestration.resilience import BulkheadConfig, CircuitBreakerConfig
from openfatture.ai.tools.models import ToolRisk


def bulkhead_config_for(risk: ToolRisk | None) -> BulkheadConfig:
    """Concurrency limits: reads run wider and wait longer than writes."""
    if risk is None:
        return BulkheadConfig()
    if risk in (ToolRisk.READ, ToolRisk.LOOKUP):
        return BulkheadConfig(max_concurrent_executions=10, acquisition_timeout_seconds=15.0)
    return BulkheadConfig(max_concurrent_executions=2, acquisition_timeout_seconds=5.0)


def circuit_breaker_config_for(risk: ToolRisk | None) -> CircuitBreakerConfig:
    """Failure policy: reads are lenient and recover fast, writes trip early."""
    if risk is None:
        return CircuitBreakerConfig()
    if risk in (ToolRisk.READ, ToolRisk.LOOKUP):
        return CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=3,
            timeout_seconds=30,
            half_open_max_calls=5,
        )
    return CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=1,
        timeout_seconds=120,
        half_open_max_calls=2,
    )


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
