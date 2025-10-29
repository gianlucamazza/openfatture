"""Tests for Lightning liquidity management service."""

from unittest.mock import AsyncMock

import pytest

from openfatture.lightning.application.services.liquidity_service import (
    LightningLiquidityService,
    LiquidityMetrics,
)
from openfatture.lightning.domain.value_objects import ChannelInfo


class TestLightningLiquidityService:
    """Test Lightning liquidity management functionality."""

    @pytest.fixture
    def mock_lnd_client_liquidity(self, mock_lnd_client):
        """Mock LND client configured for liquidity testing."""
        client = mock_lnd_client

        # Mock some channels with different liquidity levels
        mock_channels = [
            ChannelInfo(
                channel_id="ch1",
                capacity_sat=1_000_000,
                local_balance_sat=810_000,  # High outbound (81%)
                remote_balance_sat=190_000,  # Low inbound (19% < 20% min)
                status="open",
                peer_pubkey="peer1",
                peer_alias="Peer One",
                fee_rate_milli_msat=1000,
                last_update=None,
            ),
            ChannelInfo(
                channel_id="ch2",
                capacity_sat=500_000,
                local_balance_sat=100_000,  # Low outbound (20%)
                remote_balance_sat=400_000,  # High inbound (80%)
                status="open",
                peer_pubkey="peer2",
                peer_alias="Peer Two",
                fee_rate_milli_msat=800,
                last_update=None,
            ),
            ChannelInfo(
                channel_id="ch3",
                capacity_sat=750_000,
                local_balance_sat=375_000,  # Balanced (50%)
                remote_balance_sat=375_000,  # Balanced (50%)
                status="open",
                peer_pubkey="peer3",
                peer_alias="Peer Three",
                fee_rate_milli_msat=500,
                last_update=None,
            ),
        ]

        # Mock the list_channels method
        async def mock_list_channels():
            return mock_channels

        client.list_channels = mock_list_channels
        return client

    @pytest.fixture
    def liquidity_service(self, mock_lnd_client_liquidity):
        """Liquidity service for testing."""
        return LightningLiquidityService(
            lnd_client=mock_lnd_client_liquidity,
            min_inbound_ratio=0.2,
            target_inbound_ratio=0.5,
            max_outbound_ratio=0.7,
        )

    @pytest.mark.asyncio
    async def test_check_liquidity_calculates_metrics(self, liquidity_service):
        """Test that liquidity check calculates correct metrics."""
        metrics = await liquidity_service.check_liquidity()

        assert isinstance(metrics, LiquidityMetrics)
        assert metrics.channel_count == 3
        assert metrics.total_capacity_sat == 2_250_000  # 1M + 500k + 750k

        # Check ratios are calculated correctly
        expected_inbound_ratio = (190_000 + 400_000 + 375_000) / 2_250_000  # ~0.429
        assert abs(metrics.inbound_ratio - expected_inbound_ratio) < 0.01

        expected_outbound_ratio = (810_000 + 100_000 + 375_000) / 2_250_000  # ~0.571
        assert abs(metrics.outbound_ratio - expected_outbound_ratio) < 0.01

    @pytest.mark.asyncio
    async def test_check_liquidity_detects_low_liquidity(self, liquidity_service):
        """Test that low liquidity channels are detected."""
        metrics = await liquidity_service.check_liquidity()

        # ch1 has low inbound (20% < 20% min), so should be in low_liquidity_channels
        assert "ch1" in metrics.low_liquidity_channels

        # ch2 has high inbound (80%), ch3 is balanced (50%)
        assert "ch2" not in metrics.low_liquidity_channels
        assert "ch3" not in metrics.low_liquidity_channels

    @pytest.mark.asyncio
    async def test_check_liquidity_detects_high_liquidity(self, liquidity_service):
        """Test that high liquidity channels are detected."""
        metrics = await liquidity_service.check_liquidity()

        # ch1 has high outbound (80% > 70% max), so should be in high_liquidity_channels
        assert "ch1" in metrics.high_liquidity_channels

        # ch2 has low outbound (20%), ch3 is balanced (50%)
        assert "ch2" not in metrics.high_liquidity_channels
        assert "ch3" not in metrics.high_liquidity_channels

    @pytest.mark.asyncio
    async def test_get_rebalancing_opportunities(self, liquidity_service):
        """Test rebalancing opportunity detection."""
        opportunities = await liquidity_service.get_rebalancing_opportunities()

        # Should find opportunities to move from ch1 (high outbound) to ch2 (low inbound)
        assert len(opportunities) > 0

        # Check that opportunities are sorted by priority
        for i in range(len(opportunities) - 1):
            assert opportunities[i].priority >= opportunities[i + 1].priority

    @pytest.mark.asyncio
    async def test_get_liquidity_report(self, liquidity_service):
        """Test comprehensive liquidity report generation."""
        report = await liquidity_service.get_liquidity_report()

        required_keys = [
            "timestamp",
            "liquidity_score",
            "metrics",
            "alerts",
            "rebalancing_opportunities",
            "recommendations",
        ]

        for key in required_keys:
            assert key in report

        # Check metrics structure
        metrics = report["metrics"]
        assert "total_capacity_sat" in metrics
        assert "inbound_ratio" in metrics
        assert "outbound_ratio" in metrics

        # Check alerts structure
        alerts = report["alerts"]
        assert "low_liquidity_channels" in alerts
        assert "high_liquidity_channels" in alerts

        # Should have recommendations
        assert isinstance(report["recommendations"], list)

    @pytest.mark.asyncio
    async def test_monitoring_start_stop(self, liquidity_service):
        """Test liquidity monitoring start/stop functionality."""
        # Should be able to start monitoring
        await liquidity_service.start_monitoring()
        assert liquidity_service._monitoring_task is not None
        assert not liquidity_service._monitoring_task.done()

        # Should be able to stop monitoring
        await liquidity_service.stop_monitoring()
        assert liquidity_service._monitoring_task.done()

    @pytest.mark.asyncio
    async def test_empty_channels_handling(self, mock_lnd_client):
        """Test handling of nodes with no channels."""
        # Create a mock client with no channels
        mock_client = mock_lnd_client
        mock_client.list_channels = AsyncMock(return_value=[])

        service = LightningLiquidityService(mock_client)

        metrics = await service.check_liquidity()

        assert metrics.channel_count == 0
        assert metrics.total_capacity_sat == 0
        assert metrics.inbound_ratio == 0.0
        assert metrics.outbound_ratio == 0.0
