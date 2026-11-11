"""Read-only statistics about the registry's per-tool circuit breakers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from openfatture.ai.orchestration.resilience import CircuitBreaker, CircuitState


def circuit_breaker_stats(breakers: Mapping[str, CircuitBreaker]) -> dict[str, dict[str, Any]]:
    """State and counters of each tool's circuit breaker, keyed by tool name."""
    return {
        tool_name: {
            "state": breaker.state.state.value,
            "failure_count": breaker.state.failure_count,
            "success_count": breaker.state.success_count,
            "last_failure_time": (
                breaker.state.last_failure_time.isoformat()
                if breaker.state.last_failure_time
                else None
            ),
            "last_state_change": breaker.state.last_state_change.isoformat(),
        }
        for tool_name, breaker in breakers.items()
    }


def circuit_breaker_summary(breakers: Mapping[str, CircuitBreaker]) -> dict[str, Any]:
    """Totals by state plus the per-tool details."""
    states = [breaker.state.state for breaker in breakers.values()]
    return {
        "total": len(breakers),
        "by_state": {state.value: states.count(state) for state in CircuitState},
        "details": circuit_breaker_stats(breakers),
    }
