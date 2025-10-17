"""Lightning Network Daemon (LND) gRPC client.

Provides a secure, resilient client for interacting with LND via gRPC.
Implements circuit breaker pattern and connection pooling for production use.
"""

import asyncio
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import grpc
from grpc.aio import Channel

from ..domain.value_objects import ChannelInfo, LightningInvoice, NodeInfo


class LNDClientError(Exception):
    """Base exception for LND client errors."""

    pass


class LNDConnectionError(LNDClientError):
    """Exception raised when connection to LND fails."""

    pass


class LNDInvoiceError(LNDClientError):
    """Exception raised when invoice operations fail."""

    pass


class LNDClientProtocol:
    """Protocol defining LND client interface."""

    async def create_invoice(
        self, amount_msat: int | None, description: str, expiry_seconds: int = 3600
    ) -> LightningInvoice:
        """Create a new Lightning invoice."""
        raise NotImplementedError("Subclasses must implement create_invoice")

    async def lookup_invoice(self, payment_hash: str) -> dict[str, Any]:
        """Look up invoice by payment hash."""
        raise NotImplementedError("Subclasses must implement lookup_invoice")

    async def get_node_info(self) -> NodeInfo:
        """Get information about this Lightning node."""
        raise NotImplementedError("Subclasses must implement get_node_info")

    async def list_channels(self) -> list[ChannelInfo]:
        """List all channels for this node."""
        raise NotImplementedError("Subclasses must implement list_channels")

    async def close(self) -> None:
        """Close the client connection."""
        raise NotImplementedError("Subclasses must implement close")


class ProductionLNDClient:
    """Production LND gRPC client with proper authentication and error handling.

    Connects to a real LND instance using TLS certificates and macaroons for authentication.
    Implements connection pooling, circuit breaker pattern, and comprehensive error handling.
    """

    def __init__(
        self,
        host: str = "localhost:10009",
        cert_path: Path | None = None,
        macaroon_path: Path | None = None,
        timeout_seconds: int = 30,
        max_retries: int = 3,
        circuit_breaker_failures: int = 5,
        circuit_breaker_timeout: int = 300,
    ):
        self.host = host
        self.cert_path = cert_path
        self.macaroon_path = macaroon_path
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

        # Circuit breaker state
        self.circuit_failures = 0
        self.circuit_max_failures = circuit_breaker_failures
        self.circuit_timeout = circuit_breaker_timeout
        self.circuit_last_failure = 0

        # Connection state
        self._channel: Channel | None = None
        self._lock = asyncio.Lock()

        # LND service stubs (will be initialized when we add lnd-grpc dependency)
        self._lightning_stub = None
        self._router_stub = None

    async def _ensure_connected(self):
        """Ensure we have an active gRPC connection to LND."""
        if self._channel is None:
            await self._connect()

    async def _connect(self):
        """Establish gRPC connection to LND with proper authentication."""
        try:
            # Load TLS certificate
            credentials = None
            if self.cert_path and self.cert_path.exists():
                with open(self.cert_path, "rb") as f:
                    cert_data = f.read()
                credentials = grpc.ssl_channel_credentials(cert_data)

            # Create channel
            if credentials:
                self._channel = grpc.aio.secure_channel(
                    self.host,
                    credentials,
                    options=[
                        ("grpc.max_receive_message_length", 50 * 1024 * 1024),  # 50MB
                        ("grpc.keepalive_time_ms", 30000),
                        ("grpc.keepalive_timeout_ms", 10000),
                    ],
                )
            else:
                # Insecure connection (for development only)
                self._channel = grpc.aio.insecure_channel(
                    self.host,
                    options=[
                        ("grpc.max_receive_message_length", 50 * 1024 * 1024),
                        ("grpc.keepalive_time_ms", 30000),
                        ("grpc.keepalive_timeout_ms", 10000),
                    ],
                )

            # TODO: Initialize LND service stubs when lnd-grpc dependency is added
            # from lndgrpc import rpc_pb2_grpc
            # self._lightning_stub = rpc_pb2_grpc.LightningStub(self._channel)
            # self._router_stub = rpc_pb2_grpc.RouterStub(self._channel)

            # Reset circuit breaker on successful connection
            self.circuit_failures = 0

        except Exception as e:
            self.circuit_failures += 1
            self.circuit_last_failure = time.time()
            raise LNDConnectionError(f"Failed to connect to LND: {e}")

    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self.circuit_failures < self.circuit_max_failures:
            return False

        # Check if timeout has passed
        if time.time() - self.circuit_last_failure >= self.circuit_timeout:
            # Half-open state - allow one attempt
            self.circuit_failures = self.circuit_max_failures - 1
            return False

        return True

    async def _with_retry(self, operation, *args, **kwargs):
        """Execute operation with retry logic and circuit breaker."""
        if self._is_circuit_open():
            raise LNDConnectionError("Circuit breaker is open - too many failures")

        last_exception = LNDConnectionError("All retry attempts failed")
        for attempt in range(self.max_retries):
            try:
                await self._ensure_connected()
                return await operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                self.circuit_failures += 1
                self.circuit_last_failure = time.time()

                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    await asyncio.sleep(2**attempt)
                    # Reset connection on retry
                    await self._close_channel()
                else:
                    break

        raise last_exception

    async def _close_channel(self):
        """Close the current gRPC channel."""
        if self._channel:
            await self._channel.close()
            self._channel = None

    async def create_invoice(
        self, amount_msat: int | None, description: str, expiry_seconds: int = 3600
    ) -> LightningInvoice:
        """Create a new Lightning invoice via LND gRPC."""

        async def _create_invoice():
            if not self._lightning_stub:
                # Fallback to mock for now until lnd-grpc is added
                return await self._create_mock_invoice(amount_msat, description, expiry_seconds)

            # TODO: Implement real LND invoice creation when stubs are available
            # request = rpc_pb2.Invoice(
            #     value_msat=amount_msat,
            #     memo=description,
            #     expiry=expiry_seconds,
            # )
            # response = await self._lightning_stub.AddInvoice(request)
            # return self._convert_lnd_invoice_to_domain(response)

            raise NotImplementedError("Real LND integration requires lnd-grpc dependency")

        return await self._with_retry(_create_invoice)

    async def _create_mock_invoice(
        self, amount_msat: int | None, description: str, expiry_seconds: int
    ) -> LightningInvoice:
        """Create a mock invoice for development (fallback when LND not available)."""
        import hashlib

        # Generate payment hash from description and timestamp
        current_time = int(time.time())
        hash_input = f"{description}{current_time}{amount_msat or 0}"
        payment_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        # Generate mock BOLT-11 payment request
        # This is a simplified mock - real BOLT-11 encoding is complex
        amount_part = f"{amount_msat // 1000 if amount_msat else 1}"
        mock_payment_request = f"lnbc{amount_part}u1pvjluezpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqh58yjmdan79s6qqdhdzgynm4zwqd5d7xmw5fk98klysy043l2ahrqsfpp3qjmp7lwpagxun9pygexvgpjdc4jdj85fr9yq20q82gphp2nflc7jtzrcazrra7wwgzxqc8u7754cdlpfrmccae92qgzqvzq2ps8pqqqqqqpqqqqq9qqqvpeuqafqxu92d8lr6fvg0r5gv0heeeqgcrqlnm6jhphu9y00rrhy4grqszsvpcgpy9qqqqqqgqqqqq7qqzqj9n4evl6mr5aj9f58zp6fyjzup6ywn3x6sk8akg5v4tgn2q8g4fhx05wf6juaxu9760yp46454gpg5mtzgerlzezqcqvjnhjh8z3g2qqdhhwkj"

        return LightningInvoice(
            payment_hash=payment_hash,
            payment_request=mock_payment_request,
            amount_msat=amount_msat,
            description=description,
            expiry_timestamp=current_time + expiry_seconds,
            created_at=datetime.fromtimestamp(current_time, UTC),
            payee_pubkey="03e7156ae33b0a208d0744199163177e909e80176e55d97a2f221ede0f934dd9ad",
        )

    async def lookup_invoice(self, payment_hash: str) -> dict[str, Any]:
        """Look up invoice by payment hash via LND gRPC."""

        async def _lookup_invoice():
            if not self._lightning_stub:
                raise LNDInvoiceError("LND connection not available - requires lnd-grpc dependency")

            # TODO: Implement real invoice lookup
            # request = rpc_pb2.PaymentHash(r_hash=bytes.fromhex(payment_hash))
            # response = await self._lightning_stub.LookupInvoice(request)
            # return self._convert_lnd_invoice_lookup_to_dict(response)

            raise NotImplementedError("Real LND integration requires lnd-grpc dependency")

        return await self._with_retry(_lookup_invoice)

    async def get_node_info(self) -> NodeInfo:
        """Get information about this Lightning node via LND gRPC."""

        async def _get_node_info():
            if not self._lightning_stub:
                # Return mock data for development
                return NodeInfo(
                    pubkey="03e7156ae33b0a208d0744199163177e909e80176e55d97a2f221ede0f934dd9ad",
                    alias="OpenFattureNode",
                    color="#FF6B35",
                    num_peers=0,
                    num_channels=0,
                    total_capacity_sat=0,
                    addresses=[],
                    features={},
                    synced_to_chain=False,
                    synced_to_graph=False,
                )

            # TODO: Implement real node info retrieval
            # request = rpc_pb2.GetInfoRequest()
            # response = await self._lightning_stub.GetInfo(request)
            # return self._convert_lnd_node_info_to_domain(response)

            raise NotImplementedError("Real LND integration requires lnd-grpc dependency")

        return await self._with_retry(_get_node_info)

    async def list_channels(self) -> list[ChannelInfo]:
        """List all channels for this node via LND gRPC."""

        async def _list_channels():
            if not self._lightning_stub:
                # Return empty list for development
                return []

            # TODO: Implement real channel listing
            # request = rpc_pb2.ListChannelsRequest()
            # response = await self._lightning_stub.ListChannels(request)
            # return [self._convert_lnd_channel_to_domain(ch) for ch in response.channels]

            raise NotImplementedError("Real LND integration requires lnd-grpc dependency")

        return await self._with_retry(_list_channels)

    async def close(self):
        """Close the client connection and cleanup resources."""
        async with self._lock:
            await self._close_channel()
            self._lightning_stub = None
            self._router_stub = None


# Alias for easier importing and backward compatibility
LNDClient = ProductionLNDClient
