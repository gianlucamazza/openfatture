"""Stub file for grpc package.

Minimal type hints for grpc to satisfy mypy type checking.
"""

from collections.abc import Sequence
from typing import Any

# Common types
class Channel:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    async def close(self) -> None: ...

class ChannelCredentials:
    pass

def ssl_channel_credentials(
    root_certificates: bytes | None = None,
    private_key: bytes | None = None,
    certificate_chain: bytes | None = None,
) -> ChannelCredentials: ...
def insecure_channel(target: str, options: Sequence[tuple[str, Any]] | None = None) -> Channel: ...
def secure_channel(
    target: str,
    credentials: ChannelCredentials,
    options: Sequence[tuple[str, Any]] | None = None,
) -> Channel: ...
def __getattr__(name: str) -> Any: ...
