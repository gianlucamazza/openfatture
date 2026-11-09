import pytest

from openfatture.ai.tools.models import Tool
from openfatture.platform.logging import redact_sensitive


@pytest.mark.asyncio
async def test_write_failure_is_never_repeated():
    effects = []

    def write():
        effects.append("written")
        raise TimeoutError("unknown outcome")

    result = await Tool(name="write", description="write", func=write).execute()
    assert not result.success
    assert effects == ["written"]
    assert result.retries == 0


def test_nested_credentials_are_redacted():
    payload = {"parameters": [{"api_key": "synthetic", "nested": {"password": "synthetic"}}]}
    assert "synthetic" not in str(redact_sensitive(payload))
    assert payload["parameters"][0]["api_key"] == "synthetic"


@pytest.mark.asyncio
async def test_retry_safe_reads_only_retry_transient_failures():
    count = 0

    def read():
        nonlocal count
        count += 1
        if count == 1:
            raise TimeoutError("transient")
        return "ok"

    result = await Tool(name="read", description="read", func=read, retry_safe=True).execute()
    assert result.success
    assert count == 2
    assert result.retries == 1


@pytest.mark.asyncio
async def test_retry_safe_read_does_not_retry_validation_error():
    count = 0

    def read():
        nonlocal count
        count += 1
        raise ValueError("invalid")

    result = await Tool(name="read", description="read", func=read, retry_safe=True).execute()
    assert not result.success
    assert count == 1
