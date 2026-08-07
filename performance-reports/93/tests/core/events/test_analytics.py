"""Tests for EventAnalytics service."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from openfatture.core.events.analytics import EventAnalytics
from openfatture.core.events.repository import EventRepository
from openfatture.storage.database.models import EventLog


class TestEventAnalytics:
    """Test EventAnalytics functionality."""

    @pytest.fixture
    def mock_repo(self) -> Mock:
        """Create a mock EventRepository."""
        return Mock(spec=EventRepository)

    @pytest.fixture
    def analytics(self, mock_repo: Mock) -> EventAnalytics:
        """Create EventAnalytics instance with mock repository."""
        return EventAnalytics(mock_repo)

    def test_init_with_repo(self, mock_repo: Mock) -> None:
        """Test initialization with custom repository."""
        analytics = EventAnalytics(mock_repo)
        assert analytics.repo == mock_repo

    def test_init_without_repo(self) -> None:
        """Test initialization without repository (creates new instance)."""
        analytics = EventAnalytics()
        assert isinstance(analytics.repo, EventRepository)

    def test_get_daily_activity(self, analytics: EventAnalytics, mock_repo: Mock) -> None:
        """Test daily activity aggregation."""
        # Mock events
        now = datetime.now()
        events = [
            EventLog(
                event_id="1",
                event_type="TestEvent",
                event_data='{"test": "data"}',
                occurred_at=now - timedelta(days=1),
                entity_type="invoice",
                entity_id=1,
            ),
            EventLog(
                event_id="2",
                event_type="TestEvent",
                event_data='{"test": "data2"}',
                occurred_at=now - timedelta(days=1),
                entity_type="invoice",
                entity_id=2,
            ),
        ]
        mock_repo.get_all.return_value = events

        result = analytics.get_daily_activity(days=7)

        assert len(result) == 1
        assert result[0]["date"] == (now - timedelta(days=1)).strftime("%Y-%m-%d")
        assert result[0]["count"] == 2

    def test_get_weekly_activity(self, analytics: EventAnalytics, mock_repo: Mock) -> None:
        """Test weekly activity aggregation."""
        now = datetime.now()
        events = [
            EventLog(
                event_id="1",
                event_type="TestEvent",
                event_data='{"test": "data"}',
                occurred_at=now - timedelta(weeks=1),
                entity_type=None,
                entity_id=None,
            ),
        ]
        mock_repo.get_all.return_value = events

        result = analytics.get_weekly_activity(weeks=4)

        assert len(result) == 1
        # Check that result contains week key and count
        assert "count" in result[0]
        assert result[0]["count"] == 1

    def test_get_monthly_activity(self, analytics: EventAnalytics, mock_repo: Mock) -> None:
        """Test monthly activity aggregation."""
        now = datetime.now()
        events = [
            EventLog(
                event_id="1",
                event_type="TestEvent",
                event_data='{"test": "data"}',
                occurred_at=now - timedelta(days=30),
                entity_type=None,
                entity_id=None,
            ),
        ]
        mock_repo.get_all.return_value = events

        result = analytics.get_monthly_activity(months=3)

        assert len(result) == 1
        assert "count" in result[0]
        assert result[0]["count"] == 1

    def test_get_event_type_distribution(self, analytics: EventAnalytics, mock_repo: Mock) -> None:
        """Test event type distribution calculation."""
        mock_repo.get_stats.return_value = {
            "total_events": 10,
            "events_by_type": {"InvoiceCreated": 6, "ClientCreated": 4},
        }

        result = analytics.get_event_type_distribution()

        assert len(result) == 2
        # Check ordering by count descending
        assert result[0]["event_type"] == "InvoiceCreated"
        assert result[0]["count"] == 6
        assert result[0]["percentage"] == 60.0
        assert result[1]["event_type"] == "ClientCreated"
        assert result[1]["count"] == 4
        assert result[1]["percentage"] == 40.0

    def test_get_event_type_distribution_empty(
        self, analytics: EventAnalytics, mock_repo: Mock
    ) -> None:
        """Test event type distribution with no events."""
        mock_repo.get_stats.return_value = {
            "total_events": 0,
            "events_by_type": {},
        }

        result = analytics.get_event_type_distribution()

        assert result == []

    def test_get_entity_activity(self, analytics: EventAnalytics, mock_repo: Mock) -> None:
        """Test entity activity distribution."""
        mock_repo.get_stats.return_value = {
            "events_by_entity": {"invoice": 5, "client": 3},
        }

        result = analytics.get_entity_activity()

        assert len(result) == 2
        assert result[0]["entity_type"] == "invoice"
        assert result[0]["count"] == 5
        assert result[1]["entity_type"] == "client"
        assert result[1]["count"] == 3

    def test_get_top_entities(self, analytics: EventAnalytics, mock_repo: Mock) -> None:
        """Test getting top entities by activity."""
        events = [
            EventLog(
                event_id="1",
                event_type="TestEvent",
                event_data='{"test": "data"}',
                occurred_at=datetime.now(),
                entity_type="invoice",
                entity_id=1,
            ),
            EventLog(
                event_id="2",
                event_type="TestEvent",
                event_data='{"test": "data"}',
                occurred_at=datetime.now(),
                entity_type="invoice",
                entity_id=1,
            ),
            EventLog(
                event_id="3",
                event_type="TestEvent",
                event_data='{"test": "data"}',
                occurred_at=datetime.now(),
                entity_type="invoice",
                entity_id=2,
            ),
        ]
        mock_repo.get_all.return_value = events

        result = analytics.get_top_entities("invoice", limit=2)

        assert len(result) == 2
        # Entity 1 should have 2 events, entity 2 should have 1
        assert result[0]["entity_id"] == 1
        assert result[0]["event_count"] == 2
        assert result[1]["entity_id"] == 2
        assert result[1]["event_count"] == 1

    def test_get_activity_trends_increasing(
        self, analytics: EventAnalytics, mock_repo: Mock
    ) -> None:
        """Test activity trends calculation - increasing."""
        now = datetime.now()
        recent_start = now - timedelta(days=7)
        previous_start = now - timedelta(days=14)

        mock_repo.count.side_effect = [10, 5]  # recent, previous

        result = analytics.get_activity_trends(days=7)

        assert result["recent_count"] == 10
        assert result["previous_count"] == 5
        assert result["change"] == 5
        assert result["change_percent"] == 100.0
        assert result["trend"] == "increasing"

    def test_get_activity_trends_decreasing(
        self, analytics: EventAnalytics, mock_repo: Mock
    ) -> None:
        """Test activity trends calculation - decreasing."""
        now = datetime.now()
        recent_start = now - timedelta(days=7)
        previous_start = now - timedelta(days=14)

        mock_repo.count.side_effect = [3, 8]  # recent, previous

        result = analytics.get_activity_trends(days=7)

        assert result["recent_count"] == 3
        assert result["previous_count"] == 8
        assert result["change"] == -5
        assert result["change_percent"] == -62.5
        assert result["trend"] == "decreasing"

    def test_get_activity_trends_stable(self, analytics: EventAnalytics, mock_repo: Mock) -> None:
        """Test activity trends calculation - stable."""
        now = datetime.now()
        recent_start = now - timedelta(days=7)
        previous_start = now - timedelta(days=14)

        mock_repo.count.side_effect = [5, 5]  # recent, previous

        result = analytics.get_activity_trends(days=7)

        assert result["recent_count"] == 5
        assert result["previous_count"] == 5
        assert result["change"] == 0
        assert result["change_percent"] == 0.0
        assert result["trend"] == "stable"

    def test_get_hourly_distribution(self, analytics: EventAnalytics, mock_repo: Mock) -> None:
        """Test hourly distribution calculation."""
        now = datetime.now()
        events = [
            EventLog(
                event_id="1",
                event_type="TestEvent",
                event_data='{"test": "data"}',
                occurred_at=now.replace(hour=9),
                entity_type=None,
                entity_id=None,
            ),
            EventLog(
                event_id="2",
                event_type="TestEvent",
                event_data='{"test": "data"}',
                occurred_at=now.replace(hour=9),
                entity_type=None,
                entity_id=None,
            ),
            EventLog(
                event_id="3",
                event_type="TestEvent",
                event_data='{"test": "data"}',
                occurred_at=now.replace(hour=15),
                entity_type=None,
                entity_id=None,
            ),
        ]
        mock_repo.get_all.return_value = events

        result = analytics.get_hourly_distribution(days=1)

        assert len(result) == 24  # All 24 hours
        assert result[9]["hour"] == 9
        assert result[9]["count"] == 2
        assert result[15]["hour"] == 15
        assert result[15]["count"] == 1
        # Other hours should be 0
        assert result[0]["count"] == 0

    def test_get_event_velocity(self, analytics: EventAnalytics, mock_repo: Mock) -> None:
        """Test event velocity calculation."""
        mock_repo.count.return_value = 24  # 24 events in 24 hours

        result = analytics.get_event_velocity(hours=24)

        assert result["event_count"] == 24
        assert result["hours"] == 24
        assert result["events_per_hour"] == 1.0

    def test_get_dashboard_summary(self, analytics: EventAnalytics, mock_repo: Mock) -> None:
        """Test dashboard summary generation."""
        now = datetime.now()
        start_date = now - timedelta(days=30)

        mock_repo.get_stats.return_value = {
            "total_events": 100,
            "events_by_type": {"InvoiceCreated": 60, "ClientCreated": 40},
            "events_by_entity": {"invoice": 60, "client": 40},
            "most_recent_event": {"event_type": "InvoiceCreated", "occurred_at": now},
            "oldest_event": {"event_type": "ClientCreated", "occurred_at": start_date},
        }

        # Mock count calls: trends (2 calls), velocity (1 call)
        mock_repo.count.side_effect = [20, 15, 24]  # recent, previous for trends, velocity

        result = analytics.get_dashboard_summary(days=30)

        assert result["period_days"] == 30
        assert result["total_events"] == 100
        assert result["event_types_count"] == 2
        assert len(result["top_event_types"]) == 2
        assert "trends" in result
        assert "entity_activity" in result
        assert "velocity_24h" in result

    def test_close(self, analytics: EventAnalytics, mock_repo: Mock) -> None:
        """Test closing the analytics service."""
        analytics.close()
        mock_repo.close.assert_called_once()
