"""Shared test fixtures for Lightning Network tests."""

import hashlib
import time
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from openfatture.lightning.domain.value_objects import (
    ChannelInfo,
    LightningInvoice,
    NodeInfo,
)


class MockBTCConverter:
    """Mock BTC converter for testing."""

    def __init__(self, eur_to_btc_rate: Decimal = Decimal("0.00002")):
        """Initialize mock converter with fixed rate.

        Args:
            eur_to_btc_rate: EUR to BTC conversion rate (default: 1 EUR = 0.00002 BTC)
        """
        self.eur_to_btc_rate = eur_to_btc_rate
        self.btc_to_eur_rate = Decimal("1") / eur_to_btc_rate

    async def convert_eur_to_btc(self, amount_eur: Decimal) -> Decimal:
        """Convert EUR to BTC."""
        return amount_eur * self.eur_to_btc_rate

    async def convert_btc_to_eur(self, amount_btc: Decimal) -> Decimal:
        """Convert BTC to EUR."""
        return amount_btc * self.btc_to_eur_rate

    async def get_current_rate(self) -> dict[str, Any]:
        """Get current BTC/EUR rate."""
        return {
            "eur_to_btc": float(self.eur_to_btc_rate),
            "btc_to_eur": float(self.btc_to_eur_rate),
            "timestamp": time.time(),
            "source": "mock",
        }


class MockLNDClient:
    """Mock LND client for testing."""

    def __init__(self):
        """Initialize mock LND client."""
        self.invoices: dict[str, dict[str, Any]] = {}
        # Valid compressed pubkey (66 hex chars, must start with 02 or 03)
        self.node_info = NodeInfo(
            pubkey="03e7156ae33b0a208d0744199163177e909e80176e55d97a2f221ede0f934dd9ad",
            alias="MockTestNode",
            color="#00FF00",
            num_peers=5,
            num_channels=3,
            total_capacity_sat=10_000_000,
            addresses=["127.0.0.1:9735"],
            features={"supports_mpp": True},
            synced_to_chain=True,
            synced_to_graph=True,
        )
        self.channels: list[ChannelInfo] = []

    async def create_invoice(
        self, amount_msat: int | None, description: str, expiry_seconds: int = 3600
    ) -> LightningInvoice:
        """Create a mock Lightning invoice."""
        current_time = int(time.time())
        hash_input = f"{description}{current_time}{amount_msat or 0}"
        payment_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        # Generate mock BOLT-11 payment request
        amount_part = f"{amount_msat // 1000 if amount_msat else 1}"
        mock_payment_request = f"lnbc{amount_part}u1pvjluezpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqh58yjmdan79s6"

        invoice = LightningInvoice(
            payment_hash=payment_hash,
            payment_request=mock_payment_request,
            amount_msat=amount_msat,
            description=description,
            expiry_timestamp=current_time + expiry_seconds,
            created_at=datetime.fromtimestamp(current_time, UTC),
            payee_pubkey=self.node_info.pubkey,
        )

        # Store invoice state
        self.invoices[payment_hash] = {
            "payment_hash": payment_hash,
            "payment_request": mock_payment_request,
            "amount_msat": amount_msat,
            "description": description,
            "settled": False,
            "created_at": current_time,
            "expiry_timestamp": current_time + expiry_seconds,
        }

        return invoice

    async def lookup_invoice(self, payment_hash: str) -> dict[str, Any]:
        """Look up invoice by payment hash."""
        if payment_hash not in self.invoices:
            raise ValueError(f"Invoice not found: {payment_hash}")

        return self.invoices[payment_hash]

    async def get_node_info(self) -> NodeInfo:
        """Get mock node info."""
        return self.node_info

    async def list_channels(self) -> list[ChannelInfo]:
        """List mock channels."""
        return self.channels

    async def simulate_payment(self, payment_hash: str) -> bool:
        """Simulate a payment settlement for testing."""
        if payment_hash in self.invoices:
            self.invoices[payment_hash]["settled"] = True
            return True
        return False

    async def close(self):
        """Close mock client (no-op)."""
        pass


@pytest.fixture
def mock_btc_converter():
    """Fixture providing mock BTC converter."""
    return MockBTCConverter()


@pytest.fixture
def mock_lnd_client():
    """Fixture providing mock LND client."""
    return MockLNDClient()


@pytest.fixture
def mock_lnd_client_with_channels(mock_lnd_client):
    """Fixture providing mock LND client with pre-configured channels."""
    mock_lnd_client.channels = [
        ChannelInfo(
            channel_id="ch1",
            capacity_sat=1_000_000,
            local_balance_sat=500_000,
            remote_balance_sat=500_000,
            status="open",
            peer_pubkey="peer1_pubkey",
            peer_alias="Peer One",
            fee_rate_milli_msat=1000,
            last_update=None,
        ),
        ChannelInfo(
            channel_id="ch2",
            capacity_sat=500_000,
            local_balance_sat=250_000,
            remote_balance_sat=250_000,
            status="open",
            peer_pubkey="peer2_pubkey",
            peer_alias="Peer Two",
            fee_rate_milli_msat=800,
            last_update=None,
        ),
    ]
    return mock_lnd_client
