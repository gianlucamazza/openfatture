"""Lightning Network liquidity management service.

Manages channel liquidity through automated rebalancing, channel opening,
and liquidity provision services integration.
"""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

from openfatture.core.events.base import get_global_event_bus
from openfatture.lightning.domain.enums import LiquidityAlertType
from openfatture.lightning.domain.events import LightningLiquidityAlert
from openfatture.lightning.infrastructure.lnd_client import LNDClient


@dataclass
class LiquidityMetrics:
    """Liquidity metrics for a channel or node."""

    total_inbound_sat: int
    total_outbound_sat: int
    total_capacity_sat: int
    inbound_ratio: float
    outbound_ratio: float
    channel_count: int
    low_liquidity_channels: list[str]
    high_liquidity_channels: list[str]

    @property
    def balanced_ratio(self) -> float:
        """Ratio indicating how balanced the liquidity is (0.0 = perfectly balanced)."""
        return abs(self.inbound_ratio - self.outbound_ratio)


@dataclass
class RebalancingOpportunity:
    """Represents a potential rebalancing opportunity."""

    from_channel: str
    to_channel: str
    amount_sat: int
    estimated_fee_sat: int
    priority: str  # "high", "medium", "low"


class LightningLiquidityService:
    """Service for managing Lightning Network liquidity.

    Monitors channel liquidity, detects imbalances, and provides
    recommendations for rebalancing and liquidity management.
    """

    def __init__(
        self,
        lnd_client: LNDClient,
        min_inbound_ratio: float = 0.1,
        target_inbound_ratio: float = 0.5,
        max_outbound_ratio: float = 0.8,
        check_interval_seconds: int = 3600,
    ):
        """Initialize the liquidity service.

        Args:
            lnd_client: LND gRPC client
            min_inbound_ratio: Minimum acceptable inbound liquidity ratio
            target_inbound_ratio: Target inbound liquidity ratio
            max_outbound_ratio: Maximum acceptable outbound liquidity ratio
            check_interval_seconds: Interval between liquidity checks
        """
        self.lnd_client = lnd_client
        self.min_inbound_ratio = min_inbound_ratio
        self.target_inbound_ratio = target_inbound_ratio
        self.max_outbound_ratio = max_outbound_ratio
        self.check_interval = check_interval_seconds

        self.event_bus = get_global_event_bus()
        self._monitoring_task: asyncio.Task | None = None
        self._last_check: datetime | None = None

    async def start_monitoring(self):
        """Start automatic liquidity monitoring."""
        if self._monitoring_task and not self._monitoring_task.done():
            return  # Already running

        self._monitoring_task = asyncio.create_task(self._monitor_liquidity_loop())
        print(f"Started Lightning liquidity monitoring (interval: {self.check_interval}s)")

    async def stop_monitoring(self):
        """Stop automatic liquidity monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
            print("Stopped Lightning liquidity monitoring")

    async def _monitor_liquidity_loop(self):
        """Main monitoring loop."""
        while True:
            try:
                await self.check_liquidity()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in liquidity monitoring: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def check_liquidity(self) -> LiquidityMetrics:
        """Check current liquidity status and emit alerts if needed.

        Returns:
            Current liquidity metrics
        """
        channels = await self.lnd_client.list_channels()

        # Calculate aggregate metrics
        total_capacity = sum(ch.capacity_sat for ch in channels)
        total_inbound = sum(ch.inbound_capacity_sat for ch in channels)
        total_outbound = sum(ch.outbound_capacity_sat for ch in channels)

        if total_capacity == 0:
            # No channels
            metrics = LiquidityMetrics(
                total_inbound_sat=0,
                total_outbound_sat=0,
                total_capacity_sat=0,
                inbound_ratio=0.0,
                outbound_ratio=0.0,
                channel_count=0,
                low_liquidity_channels=[],
                high_liquidity_channels=[],
            )
        else:
            inbound_ratio = total_inbound / total_capacity
            outbound_ratio = total_outbound / total_capacity

            # Identify problematic channels
            low_liquidity_channels = [
                ch.channel_id for ch in channels if ch.inbound_ratio < self.min_inbound_ratio
            ]
            high_liquidity_channels = [
                ch.channel_id for ch in channels if ch.outbound_ratio > self.max_outbound_ratio
            ]

            metrics = LiquidityMetrics(
                total_inbound_sat=total_inbound,
                total_outbound_sat=total_outbound,
                total_capacity_sat=total_capacity,
                inbound_ratio=inbound_ratio,
                outbound_ratio=outbound_ratio,
                channel_count=len(channels),
                low_liquidity_channels=low_liquidity_channels,
                high_liquidity_channels=high_liquidity_channels,
            )

        # Check for alerts
        await self._check_alerts(metrics)

        self._last_check = datetime.now(UTC)
        return metrics

    async def _check_alerts(self, metrics: LiquidityMetrics):
        """Check metrics and emit alerts if thresholds are breached."""
        alerts_emitted = []

        # Low inbound liquidity alert
        if metrics.inbound_ratio < self.min_inbound_ratio and metrics.channel_count > 0:
            alert = LightningLiquidityAlert(
                alert_type=LiquidityAlertType.LOW_INBOUND,
                severity="critical" if metrics.inbound_ratio < 0.05 else "warning",
                current_ratio=metrics.inbound_ratio,
                threshold_ratio=self.min_inbound_ratio,
                affected_channels=metrics.low_liquidity_channels,
            )
            await self.event_bus.publish_async(alert)
            alerts_emitted.append("low_inbound")

        # High outbound liquidity alert
        if metrics.outbound_ratio > self.max_outbound_ratio and metrics.channel_count > 0:
            alert = LightningLiquidityAlert(
                alert_type=LiquidityAlertType.HIGH_OUTBOUND,
                severity="warning",
                current_ratio=metrics.outbound_ratio,
                threshold_ratio=self.max_outbound_ratio,
                affected_channels=metrics.high_liquidity_channels,
            )
            await self.event_bus.publish_async(alert)
            alerts_emitted.append("high_outbound")

        # Unbalanced channels alert
        if metrics.balanced_ratio > 0.7:  # More than 70% imbalance
            severely_unbalanced = [
                ch.channel_id
                for ch in await self.lnd_client.list_channels()
                if abs(ch.inbound_ratio - ch.outbound_ratio) > 0.8
            ]
            if severely_unbalanced:
                alert = LightningLiquidityAlert(
                    alert_type=LiquidityAlertType.CHANNEL_UNBALANCED,
                    severity="warning",
                    current_ratio=metrics.balanced_ratio,
                    threshold_ratio=0.7,
                    affected_channels=severely_unbalanced,
                )
                await self.event_bus.publish_async(alert)
                alerts_emitted.append("unbalanced")

        if alerts_emitted:
            print(f"Emitted liquidity alerts: {', '.join(alerts_emitted)}")

    async def get_rebalancing_opportunities(self) -> list[RebalancingOpportunity]:
        """Analyze channels and suggest rebalancing opportunities.

        Returns:
            List of rebalancing opportunities sorted by priority
        """
        channels = await self.lnd_client.list_channels()
        opportunities = []

        # Simple rebalancing logic: move from high-outbound to low-inbound channels
        high_outbound = [ch for ch in channels if ch.outbound_ratio > self.max_outbound_ratio]
        low_inbound = [ch for ch in channels if ch.inbound_ratio < self.min_inbound_ratio]

        for source in high_outbound:
            for target in low_inbound:
                if source.channel_id == target.channel_id:
                    continue

                # Calculate rebalancing amount (move towards target ratio)
                source_excess = int(
                    source.outbound_capacity_sat
                    * (source.outbound_ratio - self.target_inbound_ratio)
                )
                target_needed = int(
                    target.capacity_sat * (self.target_inbound_ratio - target.inbound_ratio)
                )

                amount = min(source_excess, target_needed, 1000000)  # Max 1M sats per rebalance

                if amount > 10000:  # Minimum 10k sats
                    # Estimate fee (rough calculation)
                    estimated_fee = max(10, amount // 10000)  # ~0.1% fee

                    priority = "high" if amount > 500000 else "medium"

                    opportunities.append(
                        RebalancingOpportunity(
                            from_channel=source.channel_id,
                            to_channel=target.channel_id,
                            amount_sat=amount,
                            estimated_fee_sat=estimated_fee,
                            priority=priority,
                        )
                    )

        # Sort by priority and amount
        priority_order = {"high": 0, "medium": 1, "low": 2}
        opportunities.sort(key=lambda x: (priority_order[x.priority], -x.amount_sat))

        return opportunities

    async def get_liquidity_report(self) -> dict:
        """Generate a comprehensive liquidity report.

        Returns:
            Dictionary with liquidity analysis and recommendations
        """
        metrics = await self.check_liquidity()
        opportunities = await self.get_rebalancing_opportunities()

        # Calculate liquidity score (0-100)
        if metrics.channel_count == 0:
            liquidity_score = 0
        else:
            inbound_score = min(100, (metrics.inbound_ratio / self.target_inbound_ratio) * 100)
            balance_score = max(0, 100 - (metrics.balanced_ratio * 100))
            liquidity_score = int((inbound_score + balance_score) / 2)

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "liquidity_score": liquidity_score,
            "metrics": {
                "total_capacity_sat": metrics.total_capacity_sat,
                "total_inbound_sat": metrics.total_inbound_sat,
                "total_outbound_sat": metrics.total_outbound_sat,
                "inbound_ratio": round(metrics.inbound_ratio, 3),
                "outbound_ratio": round(metrics.outbound_ratio, 3),
                "balanced_ratio": round(metrics.balanced_ratio, 3),
                "channel_count": metrics.channel_count,
            },
            "alerts": {
                "low_liquidity_channels": len(metrics.low_liquidity_channels),
                "high_liquidity_channels": len(metrics.high_liquidity_channels),
                "low_liquidity_channel_ids": metrics.low_liquidity_channels,
                "high_liquidity_channel_ids": metrics.high_liquidity_channels,
            },
            "rebalancing_opportunities": [
                {
                    "from_channel": opp.from_channel,
                    "to_channel": opp.to_channel,
                    "amount_sat": opp.amount_sat,
                    "estimated_fee_sat": opp.estimated_fee_sat,
                    "priority": opp.priority,
                }
                for opp in opportunities[:5]  # Top 5 opportunities
            ],
            "recommendations": self._generate_recommendations(metrics, opportunities),
        }

    def _generate_recommendations(
        self, metrics: LiquidityMetrics, opportunities: list[RebalancingOpportunity]
    ) -> list[str]:
        """Generate human-readable recommendations based on current state."""
        recommendations = []

        if metrics.channel_count == 0:
            recommendations.append(
                "No Lightning channels found. Consider opening channels to enable Lightning payments."
            )
            return recommendations

        if metrics.inbound_ratio < self.min_inbound_ratio:
            severity = "critical" if metrics.inbound_ratio < 0.05 else "moderate"
            recommendations.append(
                f"{severity.title()} inbound liquidity issue: {metrics.inbound_ratio:.1%} available "
                f"(minimum {self.min_inbound_ratio:.1%}). Consider rebalancing or opening new channels."
            )

        if metrics.outbound_ratio > self.max_outbound_ratio:
            recommendations.append(
                f"High outbound liquidity: {metrics.outbound_ratio:.1%} used "
                f"(maximum {self.max_outbound_ratio:.1%}). Consider rebalancing to improve inbound capacity."
            )

        if opportunities:
            top_opportunity = opportunities[0]
            recommendations.append(
                f"Rebalancing opportunity: Move {top_opportunity.amount_sat:,} sats from "
                f"channel {top_opportunity.from_channel[:8]}... to {top_opportunity.to_channel[:8]}..."
            )

        if metrics.balanced_ratio > 0.5:
            recommendations.append(
                f"Channels are imbalanced (balance ratio: {metrics.balanced_ratio:.1%}). "
                "Consider rebalancing for better payment success rates."
            )

        return recommendations

    async def close(self):
        """Cleanup resources."""
        await self.stop_monitoring()
        if hasattr(self.lnd_client, "close"):
            await self.lnd_client.close()
