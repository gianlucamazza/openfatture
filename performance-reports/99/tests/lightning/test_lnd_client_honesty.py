"""Production LND client must not mock silently."""

from __future__ import annotations

import pytest

from openfatture.lightning.infrastructure.lnd_client import LNDClientError, ProductionLNDClient


@pytest.mark.asyncio
async def test_create_invoice_fails_without_mock_when_rpc_missing() -> None:
    client = ProductionLNDClient(allow_mock=False)
    with pytest.raises(LNDClientError, match="unavailable"):
        await client.create_invoice(1000, "test")


@pytest.mark.asyncio
async def test_create_invoice_mock_only_when_allowed() -> None:
    client = ProductionLNDClient(allow_mock=True)
    invoice = await client.create_invoice(1000, "dev mock")
    assert invoice.payment_hash
    assert invoice.payment_request.startswith("lnbc")


@pytest.mark.asyncio
async def test_get_node_info_fails_without_mock() -> None:
    client = ProductionLNDClient(allow_mock=False)
    with pytest.raises(LNDClientError, match="unavailable"):
        await client.get_node_info()


def test_rpc_ready_false_until_stubs_exist() -> None:
    client = ProductionLNDClient(allow_mock=False)
    assert client.rpc_ready is False
