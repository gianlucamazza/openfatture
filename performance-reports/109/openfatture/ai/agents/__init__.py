"""Specialized AI agents and the public ChatAgent.

The product entrypoint is ``ChatAgent`` (used by ``openfatture assistant``).
Other agents support workflows and domain-specific prompts; orphan analytics
agents were removed. Long term, multi-step flows should converge on a single
LangGraph assistant runtime (see docs/ARCHITECTURE_REDESIGN.md).
"""
