"""Stub file for grpc.aio (async gRPC) module.

Minimal type hints for grpc.aio to satisfy mypy type checking.
"""

from collections.abc import Sequence
from typing import Any

class Channel:
    """Async gRPC channel."""

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    async def close(self) -> None: ...
    def __await__(self) -> Any: ...

def insecure_channel(target: str, options: Sequence[tuple[str, Any]] | None = None) -> Channel: ...
def secure_channel(
    target: str,
    credentials: Any,
    options: Sequence[tuple[str, Any]] | None = None,
) -> Channel: ...
def __getattr__(name: str) -> Any: ...
