"""Domain value objects for Lightning Network integration.

Value Objects in DDD:
- Immutable (frozen dataclasses)
- No identity (equality based on attributes)
- Describe characteristics, not entities
"""

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class LightningInvoice:
    """BOLT-11 Lightning invoice value object.

    Represents a Lightning Network payment request following BOLT-11 specification.
    Immutable and has no identity - equality based on payment_hash.
    """

    payment_hash: str
    payment_request: str  # Full BOLT-11 encoded string
    amount_msat: int | None  # Amount in millisatoshis (None for zero-amount invoices)
    description: str
    expiry_timestamp: int  # Unix timestamp when invoice expires
    created_at: datetime
    fallback_addr: str | None = None  # On-chain fallback address
    payee_pubkey: str | None = None  # Payee's public key
    routing_hints: list[dict[str, Any]] | None = None

    def __post_init__(self) -> None:
        """Validate Lightning invoice constraints."""
        # Validate payment hash format (64 hex chars)
        if not re.match(r"^[0-9a-f]{64}$", self.payment_hash):
            raise ValueError(f"Invalid payment_hash format: {self.payment_hash}")

        # Validate amount (must be positive if specified)
        if self.amount_msat is not None and self.amount_msat <= 0:
            raise ValueError(f"Amount must be positive, got {self.amount_msat}")

        # Validate expiry timestamp (must be in future)
        now = int(datetime.now(UTC).timestamp())
        if self.expiry_timestamp <= now:
            raise ValueError(f"Expiry timestamp must be in future, got {self.expiry_timestamp}")

        # Validate payee pubkey if provided (66 hex chars for compressed pubkey)
        if self.payee_pubkey and not re.match(r"^[0-9a-f]{66}$", self.payee_pubkey):
            raise ValueError(f"Invalid payee_pubkey format: {self.payee_pubkey}")

    @property
    def amount_sat(self) -> float | None:
        """Get amount in satoshis (human-readable)."""
        return self.amount_msat / 1000 if self.amount_msat else None

    @property
    def is_expired(self) -> bool:
        """Check if invoice has expired."""
        now = int(datetime.now(UTC).timestamp())
        return now >= self.expiry_timestamp

    @property
    def expires_at(self) -> datetime:
        """Get expiry time as datetime object."""
        return datetime.fromtimestamp(self.expiry_timestamp, UTC)

    @property
    def time_to_expiry_seconds(self) -> int:
        """Get seconds until expiry (negative if expired)."""
        now = int(datetime.now(UTC).timestamp())
        return self.expiry_timestamp - now

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "payment_hash": self.payment_hash,
            "payment_request": self.payment_request,
            "amount_msat": self.amount_msat,
            "amount_sat": self.amount_sat,
            "description": self.description,
            "expiry_timestamp": self.expiry_timestamp,
            "created_at": self.created_at.isoformat(),
            "fallback_addr": self.fallback_addr,
            "payee_pubkey": self.payee_pubkey,
            "routing_hints": self.routing_hints or [],
            "is_expired": self.is_expired,
        }


@dataclass(frozen=True)
class PaymentPreimage:
    """Lightning payment preimage value object.

    The preimage is a 32-byte secret that, when hashed with SHA256,
    produces the payment_hash. It's revealed when payment is settled.
    """

    value: str  # 64-character hex string

    def __post_init__(self) -> None:
        """Validate preimage format."""
        if not re.match(r"^[0-9a-f]{64}$", self.value):
            raise ValueError(f"Invalid preimage format: must be 64 hex chars, got {self.value}")

    @property
    def bytes(self) -> bytes:
        """Get preimage as bytes."""
        return bytes.fromhex(self.value)

    def verify_payment_hash(self, payment_hash: str) -> bool:
        """Verify that this preimage produces the given payment_hash."""
        import hashlib

        computed_hash = hashlib.sha256(self.bytes).hexdigest()
        return computed_hash == payment_hash


@dataclass(frozen=True)
class ChannelInfo:
    """Lightning channel information value object."""

    channel_id: str
    capacity_sat: int
    local_balance_sat: int
    remote_balance_sat: int
    status: str
    peer_pubkey: str
    peer_alias: str | None = None
    fee_rate_milli_msat: int | None = None
    last_update: datetime | None = None

    def __post_init__(self) -> None:
        """Validate channel info constraints."""
        if self.capacity_sat <= 0:
            raise ValueError(f"Channel capacity must be positive, got {self.capacity_sat}")

        if self.local_balance_sat < 0 or self.remote_balance_sat < 0:
            raise ValueError("Channel balances cannot be negative")

        if self.local_balance_sat + self.remote_balance_sat > self.capacity_sat:
            raise ValueError("Sum of balances cannot exceed capacity")

    @property
    def inbound_capacity_sat(self) -> int:
        """Get inbound capacity (how much we can receive)."""
        return self.capacity_sat - self.local_balance_sat

    @property
    def outbound_capacity_sat(self) -> int:
        """Get outbound capacity (how much we can send)."""
        return self.local_balance_sat

    @property
    def inbound_ratio(self) -> float:
        """Get ratio of inbound capacity (0.0-1.0)."""
        return self.inbound_capacity_sat / self.capacity_sat if self.capacity_sat > 0 else 0.0

    @property
    def outbound_ratio(self) -> float:
        """Get ratio of outbound capacity (0.0-1.0)."""
        return self.outbound_capacity_sat / self.capacity_sat if self.capacity_sat > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "channel_id": self.channel_id,
            "capacity_sat": self.capacity_sat,
            "local_balance_sat": self.local_balance_sat,
            "remote_balance_sat": self.remote_balance_sat,
            "inbound_capacity_sat": self.inbound_capacity_sat,
            "outbound_capacity_sat": self.outbound_capacity_sat,
            "inbound_ratio": self.inbound_ratio,
            "outbound_ratio": self.outbound_ratio,
            "status": self.status,
            "peer_pubkey": self.peer_pubkey,
            "peer_alias": self.peer_alias,
            "fee_rate_milli_msat": self.fee_rate_milli_msat,
            "last_update": self.last_update.isoformat() if self.last_update else None,
        }


@dataclass(frozen=True)
class NodeInfo:
    """Lightning node information value object."""

    pubkey: str
    alias: str
    color: str
    num_peers: int
    num_channels: int
    total_capacity_sat: int
    addresses: list[str]
    features: dict[str, Any]
    synced_to_chain: bool
    synced_to_graph: bool

    def __post_init__(self) -> None:
        """Validate node info constraints."""
        # Validate pubkey format (66 hex chars for compressed pubkey)
        if not re.match(r"^[0-9a-f]{66}$", self.pubkey):
            raise ValueError(f"Invalid pubkey format: {self.pubkey}")

    @property
    def is_synced(self) -> bool:
        """Check if node is fully synced."""
        return self.synced_to_chain and self.synced_to_graph

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pubkey": self.pubkey,
            "alias": self.alias,
            "color": self.color,
            "num_peers": self.num_peers,
            "num_channels": self.num_channels,
            "total_capacity_sat": self.total_capacity_sat,
            "addresses": self.addresses,
            "features": self.features,
            "synced_to_chain": self.synced_to_chain,
            "synced_to_graph": self.synced_to_graph,
            "is_synced": self.is_synced,
        }


# ============================================================================
# TAX & COMPLIANCE VALUE OBJECTS (Italian Fiscal Compliance)
# ============================================================================


@dataclass(frozen=True)
class TaxableAmount:
    """Importo con tracking fiscale per calcolo plusvalenze.

    Rappresenta un importo in EUR con il tasso di cambio BTC/EUR al momento
    della transazione, necessario per calcolare capital gains fiscali.

    Attributes:
        amount_eur: Importo in Euro
        btc_eur_rate: Tasso di cambio BTC/EUR al momento della transazione
        timestamp: Data e ora della transazione
    """

    amount_eur: Decimal
    btc_eur_rate: Decimal
    timestamp: datetime

    def __post_init__(self) -> None:
        """Validate taxable amount constraints."""
        if self.amount_eur < 0:
            raise ValueError(f"Amount must be non-negative, got {self.amount_eur}")

        if self.btc_eur_rate <= 0:
            raise ValueError(f"BTC/EUR rate must be positive, got {self.btc_eur_rate}")

        # Validate timestamp is not in future
        now = datetime.now(UTC)
        if self.timestamp > now:
            raise ValueError(f"Timestamp cannot be in future: {self.timestamp} > {now}")

    @property
    def amount_btc(self) -> Decimal:
        """Get amount in BTC (calculated from EUR and rate)."""
        return self.amount_eur / self.btc_eur_rate

    @property
    def amount_sat(self) -> int:
        """Get amount in satoshis."""
        return int(self.amount_btc * Decimal("100000000"))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "amount_eur": str(self.amount_eur),
            "amount_btc": str(self.amount_btc),
            "amount_sat": self.amount_sat,
            "btc_eur_rate": str(self.btc_eur_rate),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass(frozen=True)
class CapitalGain:
    """Plusvalenza o minusvalenza fiscale su crypto-attività.

    Rappresenta il guadagno (o perdita) fiscale derivante dalla conversione
    di Bitcoin in EUR tramite pagamento Lightning Network.

    Dal 2025 in Italia:
    - Tutte le plusvalenze sono tassabili (no soglia 2.000 EUR)
    - Aliquota: 26% (2025) → 33% (2026+)
    - Da dichiarare in Quadro RT (redditi diversi)

    Attributes:
        payment_hash: Hash del pagamento Lightning
        acquisition_cost_eur: Costo di acquisizione BTC (se noto)
        sale_price_eur: Prezzo di vendita (importo pagamento in EUR)
        gain_loss_eur: Plusvalenza (positivo) o minusvalenza (negativo)
        tax_year: Anno fiscale di competenza
    """

    payment_hash: str
    acquisition_cost_eur: Decimal | None
    sale_price_eur: Decimal
    gain_loss_eur: Decimal
    tax_year: int

    def __post_init__(self) -> None:
        """Validate capital gain constraints."""
        # Validate payment hash format
        if not re.match(r"^[0-9a-f]{64}$", self.payment_hash):
            raise ValueError(f"Invalid payment_hash format: {self.payment_hash}")

        # Validate acquisition cost if provided
        if self.acquisition_cost_eur is not None and self.acquisition_cost_eur < 0:
            raise ValueError(f"Acquisition cost cannot be negative: {self.acquisition_cost_eur}")

        # Validate sale price
        if self.sale_price_eur < 0:
            raise ValueError(f"Sale price cannot be negative: {self.sale_price_eur}")

        # Validate gain/loss calculation
        if self.acquisition_cost_eur is not None:
            expected_gain = self.sale_price_eur - self.acquisition_cost_eur
            if abs(self.gain_loss_eur - expected_gain) > Decimal("0.01"):
                raise ValueError(
                    f"Gain/loss mismatch: expected {expected_gain}, got {self.gain_loss_eur}"
                )

        # Validate tax year
        current_year = datetime.now(UTC).year
        if self.tax_year < 2000 or self.tax_year > current_year + 1:
            raise ValueError(f"Invalid tax year: {self.tax_year}")

    @property
    def is_taxable(self) -> bool:
        """Check if capital gain is taxable.

        Dal 2025 in Italia: tutte le plusvalenze sono tassabili,
        indipendentemente dall'importo (eliminata soglia 2.000 EUR).
        """
        return self.gain_loss_eur > 0

    @property
    def tax_rate_2025(self) -> Decimal:
        """Get tax rate for 2025 (26%)."""
        return Decimal("0.26")

    @property
    def tax_rate_2026_onwards(self) -> Decimal:
        """Get tax rate for 2026 onwards (33%)."""
        return Decimal("0.33")

    @property
    def tax_owed_eur(self) -> Decimal:
        """Calculate tax owed based on year and gain."""
        if not self.is_taxable:
            return Decimal("0.00")

        rate = self.tax_rate_2025 if self.tax_year <= 2025 else self.tax_rate_2026_onwards
        # Quantize to 2 decimal places for EUR amounts
        return (self.gain_loss_eur * rate).quantize(Decimal("0.01"))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "payment_hash": self.payment_hash,
            "acquisition_cost_eur": (
                str(self.acquisition_cost_eur) if self.acquisition_cost_eur else None
            ),
            "sale_price_eur": str(self.sale_price_eur),
            "gain_loss_eur": str(self.gain_loss_eur),
            "tax_year": self.tax_year,
            "is_taxable": self.is_taxable,
            "tax_owed_eur": str(self.tax_owed_eur),
        }


@dataclass(frozen=True)
class QuadroRWData:
    """Dati per compilazione Quadro RW (monitoraggio attività finanziarie estere).

    Il Quadro RW serve per dichiarare cripto-attività detenute, anche se custodite
    in Italia. Necessario per tutti gli importi, indipendentemente dalla giacenza.

    Attributes:
        tax_year: Anno fiscale di riferimento
        total_holdings_eur: Valore totale detenuto al 31/12
        average_holdings_eur: Giacenza media annuale (per calcolo IVAFE)
        num_transactions: Numero totale transazioni nell'anno
        total_inflows_eur: Totale entrate (acquisti BTC)
        total_outflows_eur: Totale uscite (vendite BTC)
    """

    tax_year: int
    total_holdings_eur: Decimal
    average_holdings_eur: Decimal
    num_transactions: int
    total_inflows_eur: Decimal = Decimal("0")
    total_outflows_eur: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        """Validate Quadro RW data constraints."""
        # Validate tax year
        current_year = datetime.now(UTC).year
        if self.tax_year < 2000 or self.tax_year > current_year:
            raise ValueError(f"Invalid tax year: {self.tax_year}")

        # Validate amounts are non-negative
        if self.total_holdings_eur < 0:
            raise ValueError(f"Total holdings cannot be negative: {self.total_holdings_eur}")

        if self.average_holdings_eur < 0:
            raise ValueError(f"Average holdings cannot be negative: {self.average_holdings_eur}")

        if self.total_inflows_eur < 0:
            raise ValueError(f"Total inflows cannot be negative: {self.total_inflows_eur}")

        if self.total_outflows_eur < 0:
            raise ValueError(f"Total outflows cannot be negative: {self.total_outflows_eur}")

        # Validate num_transactions
        if self.num_transactions < 0:
            raise ValueError(f"Number of transactions cannot be negative: {self.num_transactions}")

    @property
    def requires_declaration(self) -> bool:
        """Check if Quadro RW declaration is required.

        Dal 2025: SEMPRE obbligatorio dichiarare cripto-attività,
        indipendentemente dall'importo detenuto.
        """
        return True  # Always required from 2025 onwards

    @property
    def ivafe_tax_rate(self) -> Decimal:
        """IVAFE tax rate for crypto-assets (0.2% of average holdings)."""
        return Decimal("0.002")

    @property
    def ivafe_tax_owed_eur(self) -> Decimal:
        """Calculate IVAFE tax owed on average holdings.

        IVAFE (Imposta sul Valore delle Attività Finanziarie all'Estero)
        applies at 0.2% of average yearly holdings.

        Note: Verificare con commercialista se applicabile a Lightning/BTC.
        """
        # IVAFE might not apply to crypto in all interpretations
        # Return 0 for now, to be confirmed with tax advisor
        return Decimal("0")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tax_year": self.tax_year,
            "total_holdings_eur": str(self.total_holdings_eur),
            "average_holdings_eur": str(self.average_holdings_eur),
            "num_transactions": self.num_transactions,
            "total_inflows_eur": str(self.total_inflows_eur),
            "total_outflows_eur": str(self.total_outflows_eur),
            "requires_declaration": self.requires_declaration,
            "ivafe_tax_rate": str(self.ivafe_tax_rate),
            "ivafe_tax_owed_eur": str(self.ivafe_tax_owed_eur),
        }
