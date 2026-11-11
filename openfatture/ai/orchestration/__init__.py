"""Orchestration helpers used by the assistant runtime.

- ``react``: ReAct prompt for providers without native tools.
- ``parsers``: tool-call parsing for ReAct output.
- ``resilience``: circuit breaker and retry policy used by the tool registry.

The assistant's tool loop itself lives in ``openfatture.ai.runtime.graph``.
"""
