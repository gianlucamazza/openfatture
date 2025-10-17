"""Repository implementations for Lightning Network domain entities.

Provides data access abstraction following the Repository pattern.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from openfatture.lightning.domain.models import (
    LightningChannel,
    LightningInvoiceRecord,
    LightningNode,
)
from openfatture.storage.database.base import SessionLocal, get_session


class LightningNodeRepository:
    """Repository for LightningNode entities."""

    def __init__(self, session: Session | None = None):
        self.session = session or (SessionLocal() if SessionLocal is not None else get_session())

    def save(self, node: LightningNode) -> LightningNode:
        """Save or update a Lightning node."""
        self.session.add(node)
        self.session.commit()
        return node

    def find_by_pubkey(self, pubkey: str) -> LightningNode | None:
        """Find node by public key."""
        stmt = select(LightningNode).where(LightningNode.pubkey == pubkey)
        return self.session.execute(stmt).scalar_one_or_none()

    def find_all(self) -> list[LightningNode]:
        """Find all Lightning nodes."""
        stmt = select(LightningNode)
        return list(self.session.execute(stmt).scalars())

    def find_connected(self) -> list[LightningNode]:
        """Find all connected Lightning nodes."""
        from openfatture.lightning.domain.enums import NodeStatus

        stmt = select(LightningNode).where(LightningNode.status == NodeStatus.CONNECTED)
        return list(self.session.execute(stmt).scalars())


class LightningChannelRepository:
    """Repository for LightningChannel entities."""

    def __init__(self, session: Session | None = None):
        self.session = session or (SessionLocal() if SessionLocal is not None else get_session())

    def save(self, channel: LightningChannel) -> LightningChannel:
        """Save or update a Lightning channel."""
        self.session.add(channel)
        self.session.commit()
        return channel

    def find_by_channel_id(self, channel_id: str) -> LightningChannel | None:
        """Find channel by channel ID."""
        stmt = select(LightningChannel).where(LightningChannel.channel_id == channel_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def find_by_peer_pubkey(self, peer_pubkey: str) -> list[LightningChannel]:
        """Find all channels with a specific peer."""
        stmt = select(LightningChannel).where(LightningChannel.peer_pubkey == peer_pubkey)
        return list(self.session.execute(stmt).scalars())

    def find_active(self) -> list[LightningChannel]:
        """Find all active channels."""
        from openfatture.lightning.domain.enums import ChannelStatus

        stmt = select(LightningChannel).where(LightningChannel.status == ChannelStatus.OPEN)
        return list(self.session.execute(stmt).scalars())

    def find_with_low_inbound_capacity(
        self, threshold_ratio: float = 0.2
    ) -> list[LightningChannel]:
        """Find channels with low inbound capacity."""
        from openfatture.lightning.domain.enums import ChannelStatus

        stmt = select(LightningChannel).where(
            LightningChannel.status == ChannelStatus.OPEN,
            (LightningChannel.capacity_sat - LightningChannel.local_balance_sat)
            / LightningChannel.capacity_sat
            < threshold_ratio,
        )
        return list(self.session.execute(stmt).scalars())


class LightningInvoiceRepository:
    """Repository for LightningInvoiceRecord entities."""

    def __init__(self, session: Session | None = None):
        self.session = session or (SessionLocal() if SessionLocal is not None else get_session())

    def save(self, invoice: LightningInvoiceRecord) -> LightningInvoiceRecord:
        """Save or update a Lightning invoice record."""
        self.session.add(invoice)
        self.session.commit()
        return invoice

    def find_by_payment_hash(self, payment_hash: str) -> LightningInvoiceRecord | None:
        """Find invoice by payment hash."""
        stmt = select(LightningInvoiceRecord).where(
            LightningInvoiceRecord.payment_hash == payment_hash
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def find_pending(self) -> list[LightningInvoiceRecord]:
        """Find all pending invoices."""
        from openfatture.lightning.domain.enums import InvoiceStatus

        stmt = select(LightningInvoiceRecord).where(
            LightningInvoiceRecord.status == InvoiceStatus.PENDING
        )
        return list(self.session.execute(stmt).scalars())

    def find_expired_pending(self) -> list[LightningInvoiceRecord]:
        """Find pending invoices that have expired."""
        import time

        from openfatture.lightning.domain.enums import InvoiceStatus

        current_time = int(time.time())

        stmt = select(LightningInvoiceRecord).where(
            LightningInvoiceRecord.status == InvoiceStatus.PENDING,
            LightningInvoiceRecord.expiry_timestamp <= current_time,
        )
        return list(self.session.execute(stmt).scalars())

    def find_by_fattura_id(self, fattura_id: int) -> list[LightningInvoiceRecord]:
        """Find all invoices linked to a specific fattura."""
        stmt = select(LightningInvoiceRecord).where(LightningInvoiceRecord.fattura_id == fattura_id)
        return list(self.session.execute(stmt).scalars())

    def find_settled_in_date_range(self, start_date, end_date) -> list[LightningInvoiceRecord]:
        """Find settled invoices within date range."""
        from openfatture.lightning.domain.enums import InvoiceStatus

        stmt = select(LightningInvoiceRecord).where(
            LightningInvoiceRecord.status == InvoiceStatus.SETTLED,
            LightningInvoiceRecord.settled_at.between(start_date, end_date),
        )
        return list(self.session.execute(stmt).scalars())

    def find_all(self) -> list[LightningInvoiceRecord]:
        """Find all Lightning invoice records."""
        stmt = select(LightningInvoiceRecord)
        return list(self.session.execute(stmt).scalars())

    # ========================================================================
    # COMPLIANCE-SPECIFIC QUERIES (Italian Tax & AML Regulations)
    # ========================================================================

    def find_exceeding_aml_threshold(
        self, threshold_eur: float = 5000.0
    ) -> list[LightningInvoiceRecord]:
        """Find all settled invoices exceeding AML threshold.

        Args:
            threshold_eur: AML threshold in EUR (default 5000.0)

        Returns:
            List of invoices exceeding the threshold
        """
        from decimal import Decimal

        from openfatture.lightning.domain.enums import InvoiceStatus

        stmt = select(LightningInvoiceRecord).where(
            LightningInvoiceRecord.status == InvoiceStatus.SETTLED,
            LightningInvoiceRecord.eur_amount_declared.is_not(None),
            LightningInvoiceRecord.eur_amount_declared >= Decimal(str(threshold_eur)),
        )
        return list(self.session.execute(stmt).scalars())

    def find_unverified_aml_payments(
        self, threshold_eur: float = 5000.0
    ) -> list[LightningInvoiceRecord]:
        """Find all settled invoices exceeding AML threshold without verification.

        Args:
            threshold_eur: AML threshold in EUR (default 5000.0)

        Returns:
            List of unverified invoices exceeding threshold
        """
        from decimal import Decimal

        from openfatture.lightning.domain.enums import InvoiceStatus

        stmt = select(LightningInvoiceRecord).where(
            LightningInvoiceRecord.status == InvoiceStatus.SETTLED,
            LightningInvoiceRecord.eur_amount_declared.is_not(None),
            LightningInvoiceRecord.eur_amount_declared >= Decimal(str(threshold_eur)),
            LightningInvoiceRecord.aml_verified == False,  # noqa: E712
        )
        return list(self.session.execute(stmt).scalars())

    def find_with_capital_gains(self, tax_year: int | None = None) -> list[LightningInvoiceRecord]:
        """Find all settled invoices with capital gains.

        Args:
            tax_year: Optional tax year filter

        Returns:
            List of invoices with capital gains data
        """
        from openfatture.lightning.domain.enums import InvoiceStatus

        stmt = select(LightningInvoiceRecord).where(
            LightningInvoiceRecord.status == InvoiceStatus.SETTLED,
            LightningInvoiceRecord.capital_gain_eur.is_not(None),
        )

        if tax_year:
            from datetime import UTC, datetime

            start_date = datetime(tax_year, 1, 1, tzinfo=UTC)
            end_date = datetime(tax_year, 12, 31, 23, 59, 59, tzinfo=UTC)
            stmt = stmt.where(LightningInvoiceRecord.settled_at.between(start_date, end_date))

        return list(self.session.execute(stmt).scalars())

    def find_requiring_quadro_rw(self, tax_year: int) -> list[LightningInvoiceRecord]:
        """Find all invoices requiring Quadro RW declaration for a tax year.

        Quadro RW is required for all crypto holdings from 2025 onwards.

        Args:
            tax_year: Tax year

        Returns:
            List of invoices requiring Quadro RW
        """
        from datetime import UTC, datetime

        from openfatture.lightning.domain.enums import InvoiceStatus

        start_date = datetime(tax_year, 1, 1, tzinfo=UTC)
        end_date = datetime(tax_year, 12, 31, 23, 59, 59, tzinfo=UTC)

        stmt = select(LightningInvoiceRecord).where(
            LightningInvoiceRecord.status == InvoiceStatus.SETTLED,
            LightningInvoiceRecord.settled_at.between(start_date, end_date),
            LightningInvoiceRecord.eur_amount_declared.is_not(None),
        )

        return list(self.session.execute(stmt).scalars())

    def find_by_tax_year(self, tax_year: int) -> list[LightningInvoiceRecord]:
        """Find all settled invoices for a specific tax year.

        Args:
            tax_year: Tax year (e.g., 2025)

        Returns:
            List of invoices settled in the tax year
        """
        from datetime import UTC, datetime

        from openfatture.lightning.domain.enums import InvoiceStatus

        start_date = datetime(tax_year, 1, 1, tzinfo=UTC)
        end_date = datetime(tax_year, 12, 31, 23, 59, 59, tzinfo=UTC)

        stmt = select(LightningInvoiceRecord).where(
            LightningInvoiceRecord.status == InvoiceStatus.SETTLED,
            LightningInvoiceRecord.settled_at.between(start_date, end_date),
        )

        return list(self.session.execute(stmt).scalars())

    def count_by_aml_status(self, threshold_eur: float = 5000.0) -> dict[str, int]:
        """Get count of invoices by AML verification status.

        Args:
            threshold_eur: AML threshold in EUR (default 5000.0)

        Returns:
            Dictionary with counts: total_over_threshold, verified, unverified
        """
        exceeding = self.find_exceeding_aml_threshold(threshold_eur)
        verified = sum(1 for inv in exceeding if inv.aml_verified)
        unverified = len(exceeding) - verified

        return {
            "total_over_threshold": len(exceeding),
            "verified": verified,
            "unverified": unverified,
        }

    def find_with_missing_tax_data(self) -> list[LightningInvoiceRecord]:
        """Find settled invoices missing tax data.

        These invoices are settled but don't have BTC/EUR rate or EUR amount stored,
        which is required for tax compliance.

        Returns:
            List of invoices with missing tax data
        """
        from openfatture.lightning.domain.enums import InvoiceStatus

        stmt = select(LightningInvoiceRecord).where(
            LightningInvoiceRecord.status == InvoiceStatus.SETTLED,
            (
                (LightningInvoiceRecord.btc_eur_rate.is_(None))
                | (LightningInvoiceRecord.eur_amount_declared.is_(None))
            ),
        )

        return list(self.session.execute(stmt).scalars())
