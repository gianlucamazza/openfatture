"""Domain entities for Lightning Network integration.

Entities in DDD:
- Have identity (unique ID)
- Mutable lifecycle
- Encapsulate business logic
- Mapped to database tables via SQLAlchemy
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ...storage.database.base import Base, IntPKMixin
from .enums import ChannelStatus, InvoiceStatus, NodeStatus

if TYPE_CHECKING:
    from .value_objects import ChannelInfo, NodeInfo


class LightningNode(IntPKMixin, Base):
    """Lightning Network node entity.

    Represents a Lightning Network node that can send/receive payments.
    This is typically the merchant's own node running LND or similar.
    """

    __tablename__ = "lightning_nodes"

    # Node identity
    pubkey: Mapped[str] = mapped_column(String(66), unique=True, nullable=False, index=True)
    alias: Mapped[str] = mapped_column(String(32), nullable=False)
    color: Mapped[str] = mapped_column(String(6), nullable=False)  # Hex color

    # Connection details
    addresses: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # Features and capabilities
    features: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Status tracking
    status: Mapped[NodeStatus] = mapped_column(
        String(20), nullable=False, default=NodeStatus.UNKNOWN
    )
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return f"<LightningNode(id={self.id}, pubkey={self.pubkey[:8]}..., alias='{self.alias}', status='{self.status.value}')>"

    def update_from_node_info(self, node_info: "NodeInfo") -> None:
        """Update node entity from NodeInfo value object."""
        self.alias = node_info.alias
        self.color = node_info.color
        self.addresses = node_info.addresses
        self.features = node_info.features
        self.last_seen = datetime.now(UTC)

        # Update sync status
        if node_info.is_synced:
            self.last_sync = datetime.now(UTC)

    def mark_connected(self) -> None:
        """Mark node as connected."""
        self.status = NodeStatus.CONNECTED
        self.last_seen = datetime.now(UTC)

    def mark_disconnected(self) -> None:
        """Mark node as disconnected."""
        self.status = NodeStatus.DISCONNECTED

    @property
    def is_connected(self) -> bool:
        """Check if node is currently connected."""
        return self.status == NodeStatus.CONNECTED


class LightningChannel(IntPKMixin, Base):
    """Lightning channel entity.

    Represents a payment channel between this node and a peer.
    Channels have capacity and balances that change with payments.
    """

    __tablename__ = "lightning_channels"

    # Channel identity
    channel_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    # Peer information
    peer_pubkey: Mapped[str] = mapped_column(String(66), nullable=False, index=True)
    peer_alias: Mapped[str | None] = mapped_column(String(32))

    # Channel properties
    capacity_sat: Mapped[int] = mapped_column(Integer, nullable=False)
    local_balance_sat: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    remote_balance_sat: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Status and lifecycle
    status: Mapped[ChannelStatus] = mapped_column(
        String(20), nullable=False, default=ChannelStatus.PENDING_OPEN
    )

    # Fee settings
    fee_base_msat: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    fee_rate_milli_msat: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Timestamps
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return (
            f"<LightningChannel(id={self.id}, channel_id={self.channel_id}, "
            f"capacity={self.capacity_sat}, status='{self.status.value}')>"
        )

    def update_from_channel_info(self, channel_info: "ChannelInfo") -> None:
        """Update channel entity from ChannelInfo value object."""
        self.peer_alias = channel_info.peer_alias
        self.capacity_sat = channel_info.capacity_sat
        self.local_balance_sat = channel_info.local_balance_sat
        self.remote_balance_sat = channel_info.remote_balance_sat
        self.fee_rate_milli_msat = channel_info.fee_rate_milli_msat or self.fee_rate_milli_msat

        # Update status if changed
        if channel_info.status != self.status:
            old_status = self.status
            self.status = ChannelStatus(channel_info.status)

            # Set timestamps based on status changes
            if self.status == ChannelStatus.OPEN and old_status != ChannelStatus.OPEN:
                self.opened_at = datetime.now(UTC)
            elif (
                self.status in (ChannelStatus.CLOSED, ChannelStatus.FORCE_CLOSING)
                and not self.closed_at
            ):
                self.closed_at = datetime.now(UTC)

    @property
    def inbound_capacity_sat(self) -> int:
        """Get current inbound capacity (how much we can receive)."""
        return self.capacity_sat - self.local_balance_sat

    @property
    def outbound_capacity_sat(self) -> int:
        """Get current outbound capacity (how much we can send)."""
        return self.local_balance_sat

    @property
    def inbound_ratio(self) -> float:
        """Get ratio of inbound capacity (0.0-1.0)."""
        return self.inbound_capacity_sat / self.capacity_sat if self.capacity_sat > 0 else 0.0

    @property
    def outbound_ratio(self) -> float:
        """Get ratio of outbound capacity (0.0-1.0)."""
        return self.outbound_capacity_sat / self.capacity_sat if self.capacity_sat > 0 else 0.0

    @property
    def is_active(self) -> bool:
        """Check if channel is active for payments."""
        return self.status.is_active

    def can_receive_amount(self, amount_sat: int) -> bool:
        """Check if channel can receive the specified amount."""
        return self.inbound_capacity_sat >= amount_sat

    def can_send_amount(self, amount_sat: int) -> bool:
        """Check if channel can send the specified amount."""
        return self.outbound_capacity_sat >= amount_sat


class LightningInvoiceRecord(IntPKMixin, Base):
    """Lightning invoice record entity.

    Tracks Lightning invoices created by the system.
    Links to payments and potentially to fatture.
    """

    __tablename__ = "lightning_invoices"

    # Invoice identity
    payment_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    # Invoice data (stored as JSON for flexibility)
    payment_request: Mapped[str] = mapped_column(Text, nullable=False)  # Full BOLT-11
    amount_msat: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    expiry_timestamp: Mapped[int] = mapped_column(Integer, nullable=False)

    # Status and lifecycle
    status: Mapped[InvoiceStatus] = mapped_column(
        String(20), nullable=False, default=InvoiceStatus.PENDING
    )

    # Settlement data (filled when invoice is settled)
    preimage: Mapped[str | None] = mapped_column(String(64))
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fee_paid_msat: Mapped[int | None] = mapped_column(Integer)  # Fee paid by sender

    # Relationships
    fattura_id: Mapped[int | None] = mapped_column(
        Integer, index=True
    )  # Link to fattura if applicable

    # ========================================================================
    # TAX & COMPLIANCE FIELDS (Italian Fiscal Compliance)
    # ========================================================================

    # Tax tracking fields for capital gains calculation
    btc_eur_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=2), nullable=True, comment="BTC/EUR rate at settlement"
    )
    eur_amount_declared: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=True,
        comment="EUR amount for tax declaration",
    )
    capital_gain_eur: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=True,
        comment="Capital gain/loss for tax purposes",
    )
    acquisition_cost_eur: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=True,
        comment="BTC acquisition cost (if known)",
    )

    # Anti-money laundering (AML) compliance
    aml_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Client identity verified for AML"
    )
    aml_verification_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Date of AML verification"
    )
    exceeds_aml_threshold: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Payment exceeds AML threshold (5000 EUR)",
    )

    # Accounting integration fields
    accounting_entry_ref: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Reference to accounting system entry"
    )
    fatturapa_payment_method: Mapped[str | None] = mapped_column(
        String(4),
        nullable=True,
        default="MP23",
        comment="FatturaPA payment method code (MP23=Other)",
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return (
            f"<LightningInvoiceRecord(id={self.id}, payment_hash={self.payment_hash[:8]}..., "
            f"status='{self.status.value}', amount_msat={self.amount_msat})>"
        )

    def mark_settled(self, preimage: str, fee_paid_msat: int | None = None) -> None:
        """Mark invoice as settled with payment details."""
        self.status = InvoiceStatus.SETTLED
        self.preimage = preimage
        self.settled_at = datetime.now(UTC)
        self.fee_paid_msat = fee_paid_msat

    def mark_expired(self) -> None:
        """Mark invoice as expired."""
        if self.status == InvoiceStatus.PENDING:
            self.status = InvoiceStatus.EXPIRED

    def mark_cancelled(self) -> None:
        """Mark invoice as cancelled."""
        if self.status == InvoiceStatus.PENDING:
            self.status = InvoiceStatus.CANCELLED

    @property
    def is_settled(self) -> bool:
        """Check if invoice has been settled."""
        return self.status == InvoiceStatus.SETTLED

    @property
    def is_expired(self) -> bool:
        """Check if invoice has expired."""
        if self.status != InvoiceStatus.PENDING:
            return False
        now = int(datetime.now(UTC).timestamp())
        return now >= self.expiry_timestamp

    @property
    def amount_sat(self) -> float | None:
        """Get amount in satoshis."""
        return self.amount_msat / 1000 if self.amount_msat else None

    @property
    def expires_at(self) -> datetime:
        """Get expiry time as datetime."""
        return datetime.fromtimestamp(self.expiry_timestamp, UTC)

    # ========================================================================
    # TAX & COMPLIANCE METHODS
    # ========================================================================

    def calculate_capital_gain(
        self,
        acquisition_cost_eur: Decimal | None = None,
    ) -> Decimal | None:
        """Calculate capital gain for this payment.

        Args:
            acquisition_cost_eur: BTC acquisition cost (uses stored value if not provided)

        Returns:
            Capital gain/loss in EUR, or None if insufficient data

        Note:
            This method does NOT save the result. Use `store_tax_data()` to persist.
        """
        if self.eur_amount_declared is None:
            return None

        cost = acquisition_cost_eur or self.acquisition_cost_eur
        if cost is None:
            # Cannot calculate gain without acquisition cost
            return None

        return self.eur_amount_declared - cost

    def store_tax_data(
        self,
        btc_eur_rate: Decimal,
        eur_amount: Decimal,
        acquisition_cost_eur: Decimal | None = None,
    ) -> None:
        """Store tax-related data for this payment.

        Args:
            btc_eur_rate: BTC/EUR exchange rate at settlement
            eur_amount: EUR amount for tax declaration
            acquisition_cost_eur: BTC acquisition cost (if known)
        """
        self.btc_eur_rate = btc_eur_rate
        self.eur_amount_declared = eur_amount

        if acquisition_cost_eur is not None:
            self.acquisition_cost_eur = acquisition_cost_eur
            self.capital_gain_eur = self.calculate_capital_gain(acquisition_cost_eur)

    def mark_aml_verified(self) -> None:
        """Mark this payment as AML-verified."""
        self.aml_verified = True
        self.aml_verification_date = datetime.now(UTC)

    def requires_aml_verification(self, threshold_eur: Decimal = Decimal("5000")) -> bool:
        """Check if this payment requires AML verification.

        Args:
            threshold_eur: AML threshold in EUR (default 5000)

        Returns:
            True if payment exceeds threshold and not yet verified
        """
        if self.aml_verified:
            return False

        if self.eur_amount_declared is None:
            return False

        return self.eur_amount_declared >= threshold_eur

    @property
    def has_taxable_capital_gain(self) -> bool:
        """Check if this payment has a taxable capital gain."""
        if self.capital_gain_eur is None:
            return False
        return self.capital_gain_eur > 0

    @property
    def tax_year(self) -> int | None:
        """Get tax year for this payment (based on settlement date)."""
        if self.settled_at is None:
            return None
        return self.settled_at.year
