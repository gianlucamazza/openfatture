"""Domain enums for Lightning Network integration."""

from enum import Enum


class InvoiceStatus(str, Enum):
    """Lightning invoice status.

    Lifecycle:
        PENDING → SETTLED (payment received)
        PENDING → EXPIRED (time expired)
        PENDING → CANCELLED (manually cancelled)
    """

    PENDING = "pending"  # Invoice created, waiting for payment
    SETTLED = "settled"  # Payment received and settled
    EXPIRED = "expired"  # Invoice expired without payment
    CANCELLED = "cancelled"  # Manually cancelled

    def __str__(self) -> str:
        return self.value


class ChannelStatus(str, Enum):
    """Lightning channel status."""

    PENDING_OPEN = "pending_open"  # Channel opening in progress
    OPEN = "open"  # Channel active and usable
    PENDING_CLOSE = "pending_close"  # Channel closing in progress
    CLOSED = "closed"  # Channel closed
    FORCE_CLOSING = "force_closing"  # Channel force closing

    def __str__(self) -> str:
        return self.value

    @property
    def is_active(self) -> bool:
        """Whether the channel is active for payments."""
        return self in (ChannelStatus.OPEN,)


class PaymentStatus(str, Enum):
    """Lightning payment status."""

    IN_FLIGHT = "in_flight"  # Payment attempt in progress
    SUCCEEDED = "succeeded"  # Payment completed successfully
    FAILED = "failed"  # Payment failed

    def __str__(self) -> str:
        return self.value


class NodeStatus(str, Enum):
    """Lightning node connection status."""

    CONNECTED = "connected"  # Node is reachable
    DISCONNECTED = "disconnected"  # Node is not reachable
    UNKNOWN = "unknown"  # Status cannot be determined

    def __str__(self) -> str:
        return self.value


class LiquidityAlertType(str, Enum):
    """Types of liquidity alerts."""

    LOW_INBOUND = "low_inbound"  # Inbound liquidity below minimum threshold
    HIGH_OUTBOUND = "high_outbound"  # Outbound liquidity above maximum threshold
    CHANNEL_UNBALANCED = "channel_unbalanced"  # Channels are severely imbalanced

    def __str__(self) -> str:
        return self.value
