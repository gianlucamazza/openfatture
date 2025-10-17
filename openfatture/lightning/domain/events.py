"""Domain events for Lightning Network integration.

Events represent significant business occurrences in the Lightning domain.
All events are immutable (frozen dataclasses) and include standard metadata.
"""

from dataclasses import dataclass
from datetime import datetime

from ...core.events.base import BaseEvent


@dataclass(frozen=True)
class LightningInvoiceCreated(BaseEvent):
    """Event fired when a Lightning invoice is created."""

    payment_hash: str
    payment_request: str
    amount_msat: int | None
    description: str
    expiry_timestamp: int
    fattura_id: int | None = None  # Linked invoice if created from fattura

    @property
    def context_data(self) -> dict:
        """Additional context for logging/monitoring."""
        return {
            "payment_hash": self.payment_hash,
            "amount_msat": self.amount_msat,
            "has_fattura": self.fattura_id is not None,
            "fattura_id": self.fattura_id,
        }


@dataclass(frozen=True)
class LightningPaymentSettled(BaseEvent):
    """Event fired when a Lightning payment is settled."""

    payment_hash: str
    preimage: str | None  # Preimage may not be immediately available
    amount_msat: int
    fee_paid_msat: int | None  # Fee paid by sender (if available)
    settled_at: datetime
    fattura_id: int | None = None  # Linked invoice if applicable

    @property
    def context_data(self) -> dict:
        """Additional context for logging/monitoring."""
        return {
            "payment_hash": self.payment_hash,
            "amount_msat": self.amount_msat,
            "fee_paid_msat": self.fee_paid_msat,
            "settled_at": self.settled_at.isoformat(),
            "has_fattura": self.fattura_id is not None,
            "fattura_id": self.fattura_id,
        }


@dataclass(frozen=True)
class LightningInvoiceExpired(BaseEvent):
    """Event fired when a Lightning invoice expires without payment."""

    payment_hash: str
    expiry_timestamp: int
    created_at: datetime
    fattura_id: int | None = None

    @property
    def context_data(self) -> dict:
        """Additional context for logging/monitoring."""
        return {
            "payment_hash": self.payment_hash,
            "expiry_timestamp": self.expiry_timestamp,
            "created_at": self.created_at.isoformat(),
            "has_fattura": self.fattura_id is not None,
            "fattura_id": self.fattura_id,
        }


@dataclass(frozen=True)
class LightningChannelOpened(BaseEvent):
    """Event fired when a new Lightning channel is opened."""

    channel_id: str
    peer_pubkey: str
    capacity_sat: int
    local_balance_sat: int
    remote_balance_sat: int

    @property
    def context_data(self) -> dict:
        """Additional context for logging/monitoring."""
        return {
            "channel_id": self.channel_id,
            "peer_pubkey": self.peer_pubkey,
            "capacity_sat": self.capacity_sat,
            "local_balance_sat": self.local_balance_sat,
            "remote_balance_sat": self.remote_balance_sat,
        }


@dataclass(frozen=True)
class LightningChannelClosed(BaseEvent):
    """Event fired when a Lightning channel is closed."""

    channel_id: str
    peer_pubkey: str
    capacity_sat: int
    final_balance_sat: int
    close_type: str  # "cooperative", "force", "breach"

    @property
    def context_data(self) -> dict:
        """Additional context for logging/monitoring."""
        return {
            "channel_id": self.channel_id,
            "peer_pubkey": self.peer_pubkey,
            "capacity_sat": self.capacity_sat,
            "final_balance_sat": self.final_balance_sat,
            "close_type": self.close_type,
        }


@dataclass(frozen=True)
class LightningNodeConnectivityChanged(BaseEvent):
    """Event fired when Lightning node connectivity changes."""

    node_pubkey: str
    old_status: str
    new_status: str
    reason: str | None = None

    @property
    def context_data(self) -> dict:
        """Additional context for logging/monitoring."""
        return {
            "node_pubkey": self.node_pubkey,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class LightningLiquidityAlert(BaseEvent):
    """Event fired when Lightning liquidity falls below threshold."""

    alert_type: str  # "low_inbound", "high_outbound", "channel_unbalanced"
    severity: str  # "warning", "critical"
    current_ratio: float
    threshold_ratio: float
    affected_channels: list[str]

    @property
    def context_data(self) -> dict:
        """Additional context for logging/monitoring."""
        return {
            "alert_type": self.alert_type,
            "severity": self.severity,
            "current_ratio": self.current_ratio,
            "threshold_ratio": self.threshold_ratio,
            "affected_channels_count": len(self.affected_channels),
            "affected_channels": self.affected_channels,
        }


# ============================================================================
# TAX & COMPLIANCE EVENTS (Italian Fiscal Compliance)
# ============================================================================


@dataclass(frozen=True)
class LightningPaymentTaxableEvent(BaseEvent):
    """Event fired when a Lightning payment has tax implications.

    Triggered when a payment settlement creates a taxable capital gain
    that must be reported to Italian tax authorities (Agenzia delle Entrate).

    From 2025:
    - All capital gains are taxable (no 2,000 EUR threshold)
    - Tax rate: 26% (2025) → 33% (2026+)
    - Must be declared in Quadro RT (redditi diversi)
    """

    payment_hash: str
    payment_amount_eur: float  # Amount in EUR
    capital_gain_eur: float | None  # Capital gain/loss (None if unknown cost)
    tax_year: int
    requires_quadro_rw: bool  # Quadro RW declaration required
    exceeds_aml_threshold: bool  # Anti-money laundering threshold
    fattura_id: int | None = None  # Linked invoice if applicable

    @property
    def context_data(self) -> dict:
        """Additional context for logging/monitoring."""
        return {
            "payment_hash": self.payment_hash,
            "payment_amount_eur": self.payment_amount_eur,
            "capital_gain_eur": self.capital_gain_eur,
            "tax_year": self.tax_year,
            "is_taxable": self.capital_gain_eur is not None and self.capital_gain_eur > 0,
            "requires_quadro_rw": self.requires_quadro_rw,
            "exceeds_aml_threshold": self.exceeds_aml_threshold,
            "has_fattura": self.fattura_id is not None,
            "fattura_id": self.fattura_id,
        }


@dataclass(frozen=True)
class LightningAMLAlertEvent(BaseEvent):
    """Event fired when a Lightning payment exceeds AML threshold.

    Italian anti-money laundering regulations (D.Lgs. 231/2007) require
    enhanced due diligence for transactions exceeding 5,000 EUR.

    Compliance officers should be notified when this event is triggered.
    """

    payment_hash: str
    amount_eur: float
    threshold_eur: float  # Usually 5,000 EUR
    client_id: int | None  # Linked client if from fattura
    client_name: str | None  # Client name for alert
    verification_required: bool
    already_verified: bool = False
    fattura_id: int | None = None

    @property
    def context_data(self) -> dict:
        """Additional context for logging/monitoring."""
        return {
            "payment_hash": self.payment_hash,
            "amount_eur": self.amount_eur,
            "threshold_eur": self.threshold_eur,
            "amount_over_threshold": self.amount_eur - self.threshold_eur,
            "client_id": self.client_id,
            "client_name": self.client_name,
            "verification_required": self.verification_required,
            "already_verified": self.already_verified,
            "has_fattura": self.fattura_id is not None,
            "fattura_id": self.fattura_id,
        }


@dataclass(frozen=True)
class LightningTaxDataStored(BaseEvent):
    """Event fired when tax data is stored for a Lightning payment.

    This event is published after `store_tax_data()` is called on an
    invoice record, confirming that fiscal data has been persisted.
    """

    payment_hash: str
    btc_eur_rate: float
    eur_amount_declared: float
    acquisition_cost_eur: float | None
    capital_gain_eur: float | None
    tax_year: int | None

    @property
    def context_data(self) -> dict:
        """Additional context for logging/monitoring."""
        return {
            "payment_hash": self.payment_hash,
            "btc_eur_rate": self.btc_eur_rate,
            "eur_amount_declared": self.eur_amount_declared,
            "acquisition_cost_eur": self.acquisition_cost_eur,
            "capital_gain_eur": self.capital_gain_eur,
            "has_capital_gain": self.capital_gain_eur is not None,
            "tax_year": self.tax_year,
        }


@dataclass(frozen=True)
class LightningAMLVerified(BaseEvent):
    """Event fired when AML verification is completed for a payment.

    Confirms that enhanced due diligence has been performed and
    the client's identity has been verified for compliance purposes.
    """

    payment_hash: str
    verified_at: datetime
    verified_by: str | None  # User/system that performed verification
    client_id: int | None
    notes: str | None = None

    @property
    def context_data(self) -> dict:
        """Additional context for logging/monitoring."""
        return {
            "payment_hash": self.payment_hash,
            "verified_at": self.verified_at.isoformat(),
            "verified_by": self.verified_by,
            "client_id": self.client_id,
            "has_notes": self.notes is not None,
        }
