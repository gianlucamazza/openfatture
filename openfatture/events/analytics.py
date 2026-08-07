"""Event analytics service for metrics and insights."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from .repository import EventRepository


class EventAnalytics:
    """Provides analytics and metrics for event data.

    Aggregates event data to provide insights like:
    - Time-based trends (events per day/week/month)
    - Entity-based metrics (most active entities)
    - Event type distributions
    - Activity patterns
    """

    def __init__(self, repository: EventRepository | None = None):
        """Initialize analytics service.

        Args:
            repository: EventRepository instance. If None, creates new instance.
        """
        self.repo = repository or EventRepository()

    def get_daily_activity(
        self, days: int = 30, event_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Get event activity grouped by day.

        Args:
            days: Number of days to include (default 30)
            event_type: Optional filter by event type

        Returns:
            List of dictionaries with date and event count
        """
        start_date = datetime.now() - timedelta(days=days)
        events = self.repo.get_all(
            event_type=event_type,
            start_date=start_date,
            limit=10000,
        )

        # Group by date
        daily_counts: dict[str, int] = defaultdict(int)
        for event in events:
            # Handle both naive and timezone-aware datetime
            occurred_at = event.occurred_at
            if occurred_at.tzinfo is not None:
                occurred_at = occurred_at.replace(tzinfo=None)

            date_key = occurred_at.strftime("%Y-%m-%d")
            daily_counts[date_key] += 1

        # Sort by date
        result = [{"date": date, "count": count} for date, count in sorted(daily_counts.items())]

        return result

    def get_weekly_activity(
        self, weeks: int = 12, event_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Get event activity grouped by week.

        Args:
            weeks: Number of weeks to include (default 12)
            event_type: Optional filter by event type

        Returns:
            List of dictionaries with week start date and event count
        """
        start_date = datetime.now() - timedelta(weeks=weeks)
        events = self.repo.get_all(
            event_type=event_type,
            start_date=start_date,
            limit=10000,
        )

        # Group by week (ISO week)
        weekly_counts: dict[str, int] = defaultdict(int)
        for event in events:
            occurred_at = event.occurred_at
            if occurred_at.tzinfo is not None:
                occurred_at = occurred_at.replace(tzinfo=None)

            # Get ISO week
            year, week, _ = occurred_at.isocalendar()
            week_key = f"{year}-W{week:02d}"
            weekly_counts[week_key] += 1

        # Sort by week
        result = [{"week": week, "count": count} for week, count in sorted(weekly_counts.items())]

        return result

    def get_monthly_activity(
        self, months: int = 6, event_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Get event activity grouped by month.

        Args:
            months: Number of months to include (default 6)
            event_type: Optional filter by event type

        Returns:
            List of dictionaries with month and event count
        """
        start_date = datetime.now() - timedelta(days=months * 30)  # Approximate
        events = self.repo.get_all(
            event_type=event_type,
            start_date=start_date,
            limit=10000,
        )

        # Group by month
        monthly_counts: dict[str, int] = defaultdict(int)
        for event in events:
            occurred_at = event.occurred_at
            if occurred_at.tzinfo is not None:
                occurred_at = occurred_at.replace(tzinfo=None)

            month_key = occurred_at.strftime("%Y-%m")
            monthly_counts[month_key] += 1

        # Sort by month
        result = [
            {"month": month, "count": count} for month, count in sorted(monthly_counts.items())
        ]

        return result

    def get_event_type_distribution(self, days: int | None = None) -> list[dict[str, Any]]:
        """Get distribution of events by type.

        Args:
            days: Optional number of days to limit (None = all time)

        Returns:
            List of dictionaries with event_type, count, and percentage
        """
        start_date = None
        if days:
            start_date = datetime.now() - timedelta(days=days)

        stats = self.repo.get_stats(start_date=start_date)

        total = stats["total_events"]
        if total == 0:
            return []

        result = []
        for event_type, count in sorted(
            stats["events_by_type"].items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / total * 100) if total > 0 else 0
            result.append(
                {
                    "event_type": event_type,
                    "count": count,
                    "percentage": percentage,
                }
            )

        return result

    def get_entity_activity(self, days: int | None = None) -> list[dict[str, Any]]:
        """Get activity distribution by entity type.

        Args:
            days: Optional number of days to limit (None = all time)

        Returns:
            List of dictionaries with entity_type and count
        """
        start_date = None
        if days:
            start_date = datetime.now() - timedelta(days=days)

        stats = self.repo.get_stats(start_date=start_date)

        result = [
            {"entity_type": entity_type, "count": count}
            for entity_type, count in sorted(
                stats["events_by_entity"].items(), key=lambda x: x[1], reverse=True
            )
        ]

        return result

    def get_top_entities(
        self, entity_type: str, limit: int = 10, days: int | None = None
    ) -> list[dict[str, Any]]:
        """Get most active entities of a specific type.

        Args:
            entity_type: Entity type to filter (e.g., "invoice", "client")
            limit: Maximum number of entities to return
            days: Optional number of days to limit (None = all time)

        Returns:
            List of dictionaries with entity_id and event_count
        """
        start_date = None
        if days:
            start_date = datetime.now() - timedelta(days=days)

        events = self.repo.get_all(
            entity_type=entity_type,
            start_date=start_date,
            limit=10000,
        )

        # Count events per entity
        entity_counts: dict[int, int] = defaultdict(int)
        for event in events:
            if event.entity_id is not None:
                entity_counts[event.entity_id] += 1

        # Sort by count and limit
        result = [
            {"entity_id": entity_id, "event_count": count}
            for entity_id, count in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[
                :limit
            ]
        ]

        return result

    def get_activity_trends(self, days: int = 30) -> dict[str, Any]:
        """Get activity trends comparing recent period to previous period.

        Args:
            days: Number of days for recent period

        Returns:
            Dictionary with trend metrics
        """
        now = datetime.now()
        recent_start = now - timedelta(days=days)
        previous_start = now - timedelta(days=days * 2)

        # Recent period
        recent_count = self.repo.count(start_date=recent_start, end_date=now)

        # Previous period
        previous_count = self.repo.count(start_date=previous_start, end_date=recent_start)

        # Calculate change
        change = recent_count - previous_count
        change_percent = (change / previous_count * 100) if previous_count > 0 else 0

        # Determine trend
        if change > 0:
            trend = "increasing"
        elif change < 0:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "recent_count": recent_count,
            "previous_count": previous_count,
            "change": change,
            "change_percent": change_percent,
            "trend": trend,
            "period_days": days,
        }

    def get_hourly_distribution(self, days: int = 7) -> list[dict[str, Any]]:
        """Get event distribution by hour of day.

        Args:
            days: Number of days to analyze (default 7)

        Returns:
            List of dictionaries with hour (0-23) and count
        """
        start_date = datetime.now() - timedelta(days=days)
        events = self.repo.get_all(start_date=start_date, limit=10000)

        # Count by hour
        hourly_counts: dict[int, int] = defaultdict(int)
        for event in events:
            occurred_at = event.occurred_at
            if occurred_at.tzinfo is not None:
                occurred_at = occurred_at.replace(tzinfo=None)

            hourly_counts[occurred_at.hour] += 1

        # Create result with all 24 hours
        result = [{"hour": hour, "count": hourly_counts.get(hour, 0)} for hour in range(24)]

        return result

    def get_event_velocity(self, hours: int = 24) -> dict[str, Any]:
        """Get event velocity (events per hour).

        Args:
            hours: Number of hours to analyze

        Returns:
            Dictionary with velocity metrics
        """
        start_date = datetime.now() - timedelta(hours=hours)
        event_count = self.repo.count(start_date=start_date)

        velocity = event_count / hours if hours > 0 else 0

        return {
            "event_count": event_count,
            "hours": hours,
            "events_per_hour": velocity,
        }

    def get_dashboard_summary(self, days: int = 30) -> dict[str, Any]:
        """Get comprehensive dashboard summary.

        Args:
            days: Number of days for metrics

        Returns:
            Dictionary with all key metrics
        """
        now = datetime.now()
        start_date = now - timedelta(days=days)

        # Basic stats
        stats = self.repo.get_stats(start_date=start_date)

        # Activity trends
        trends = self.get_activity_trends(days=days)

        # Top event types
        event_distribution = self.get_event_type_distribution(days=days)
        top_event_types = event_distribution[:5]

        # Entity activity
        entity_activity = self.get_entity_activity(days=days)

        # Recent velocity
        velocity = self.get_event_velocity(hours=24)

        return {
            "period_days": days,
            "total_events": stats["total_events"],
            "event_types_count": len(stats["events_by_type"]),
            "trends": trends,
            "top_event_types": top_event_types,
            "entity_activity": entity_activity,
            "velocity_24h": velocity,
            "most_recent_event": stats["most_recent_event"],
            "oldest_event": stats["oldest_event"],
        }

    def close(self) -> None:
        """Close repository connection if owned."""
        self.repo.close()
