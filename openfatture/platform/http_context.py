"""Shared HTTP client for the current application lifespan."""

from contextvars import ContextVar

import httpx

shared_http_client: ContextVar[httpx.AsyncClient | None] = ContextVar(
    "shared_http_client", default=None
)
