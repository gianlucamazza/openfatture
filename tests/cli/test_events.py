"""Tests for CLI events commands."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from openfatture.cli.commands.events import app
from openfatture.core.events.analytics import EventAnalytics
from openfatture.core.events.repository import EventRepository


class TestEventsCLI:
    """Test CLI events commands."""

    @pytest.fixture
    def mock_repo(self) -> Mock:
        """Create a mock EventRepository."""
        return Mock(spec=EventRepository)

    @pytest.fixture
    def mock_analytics(self, mock_repo: Mock) -> Mock:
        """Create a mock EventAnalytics."""
        analytics = Mock(spec=EventAnalytics)
        analytics.repo = mock_repo
        return analytics

    @patch("openfatture.cli.commands.events.get_settings")
    @patch("openfatture.cli.commands.events.init_db")
    @patch("openfatture.cli.commands.events.EventRepository")
    @patch("openfatture.cli.commands.events.console")
    def test_list_events_basic(
        self, mock_console, mock_repo_class, mock_init_db, mock_get_settings, mock_repo
    ):
        """Test basic event listing."""
        mock_repo_class.return_value = mock_repo
        mock_repo.get_all.return_value = []

        # Mock typer context and run command
        with patch("typer.Context") as mock_ctx:
            mock_ctx.__enter__ = Mock(return_value=Mock())
            mock_ctx.__exit__ = Mock(return_value=None)

            from typer.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(app, ["list"])

            assert result.exit_code == 0
            mock_repo.get_all.assert_called_once()

    @patch("openfatture.cli.commands.events.get_settings")
    @patch("openfatture.cli.commands.events.init_db")
    @patch("openfatture.cli.commands.events.EventRepository")
    @patch("openfatture.cli.commands.events.console")
    def test_list_events_with_filters(
        self, mock_console, mock_repo_class, mock_init_db, mock_get_settings, mock_repo
    ):
        """Test event listing with filters."""
        mock_repo_class.return_value = mock_repo
        mock_repo.get_all.return_value = []

        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "list",
                "--type",
                "InvoiceCreated",
                "--entity",
                "invoice",
                "--entity-id",
                "1",
                "--last-hours",
                "24",
                "--limit",
                "10",
            ],
        )

        assert result.exit_code == 0
        mock_repo.get_all.assert_called_once()
        call_args = mock_repo.get_all.call_args
        assert call_args[1]["event_type"] == "InvoiceCreated"
        assert call_args[1]["entity_type"] == "invoice"
        assert call_args[1]["entity_id"] == 1
        assert call_args[1]["limit"] == 10

    @patch("openfatture.cli.commands.events.get_settings")
    @patch("openfatture.cli.commands.events.init_db")
    @patch("openfatture.cli.commands.events.EventRepository")
    @patch("openfatture.cli.commands.events.console")
    def test_list_events_with_days(
        self, mock_console, mock_repo_class, mock_init_db, mock_get_settings, mock_repo
    ):
        """Test event listing with days filter."""
        mock_repo_class.return_value = mock_repo
        mock_repo.get_all.return_value = []

        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["list", "--last-days", "7"])

        assert result.exit_code == 0
        mock_repo.get_all.assert_called_once()
        call_args = mock_repo.get_all.call_args
        # Should have start_date set
        assert "start_date" in call_args[1]
        assert call_args[1]["start_date"] is not None

    @patch("openfatture.cli.commands.events.get_settings")
    @patch("openfatture.cli.commands.events.init_db")
    @patch("openfatture.cli.commands.events.EventAnalytics")
    @patch("openfatture.cli.commands.events.console")
    def test_stats_command(
        self, mock_console, mock_analytics_class, mock_init_db, mock_get_settings, mock_analytics
    ):
        """Test stats command."""
        mock_analytics_class.return_value = mock_analytics
        mock_analytics.get_dashboard_summary.return_value = {
            "total_events": 100,
            "event_types_count": 5,
            "trends": {"trend": "increasing"},
        }

        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["stats"])

        assert result.exit_code == 0
        mock_analytics.get_dashboard_summary.assert_called_once_with(days=30)

    @patch("openfatture.cli.commands.events.get_settings")
    @patch("openfatture.cli.commands.events.init_db")
    @patch("openfatture.cli.commands.events.EventAnalytics")
    @patch("openfatture.cli.commands.events.console")
    def test_stats_command_with_days(
        self, mock_console, mock_analytics_class, mock_init_db, mock_get_settings, mock_analytics
    ):
        """Test stats command with custom days."""
        mock_analytics_class.return_value = mock_analytics
        mock_analytics.get_dashboard_summary.return_value = {}

        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["stats", "--days", "7"])

        assert result.exit_code == 0
        mock_analytics.get_dashboard_summary.assert_called_once_with(days=7)

    @patch("openfatture.cli.commands.events.get_settings")
    @patch("openfatture.cli.commands.events.init_db")
    @patch("openfatture.cli.commands.events.EventRepository")
    @patch("openfatture.cli.commands.events.console")
    def test_show_event(
        self, mock_console, mock_repo_class, mock_init_db, mock_get_settings, mock_repo
    ):
        """Test showing a specific event."""
        from openfatture.storage.database.models import EventLog

        mock_event = EventLog(
            event_id="test-id",
            event_type="TestEvent",
            event_data='{"key": "value"}',
            occurred_at=datetime.now(),
            entity_type="invoice",
            entity_id=1,
        )
        mock_repo.get_by_id.return_value = mock_event

        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["show", "test-id"])

        assert result.exit_code == 0
        mock_repo.get_by_id.assert_called_once_with("test-id")

    @patch("openfatture.cli.commands.events.get_settings")
    @patch("openfatture.cli.commands.events.init_db")
    @patch("openfatture.cli.commands.events.EventRepository")
    @patch("openfatture.cli.commands.events.console")
    def test_show_event_not_found(
        self, mock_console, mock_repo_class, mock_init_db, mock_get_settings, mock_repo
    ):
        """Test showing a non-existent event."""
        mock_repo.get_by_id.return_value = None

        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["show", "nonexistent-id"])

        assert result.exit_code == 1
        mock_console.print.assert_called_with("[red]Event not found: nonexistent-id[/red]")

    @patch("openfatture.cli.commands.events.get_settings")
    @patch("openfatture.cli.commands.events.init_db")
    @patch("openfatture.cli.commands.events.EventRepository")
    @patch("openfatture.cli.commands.events.console")
    def test_timeline_command(
        self, mock_console, mock_repo_class, mock_init_db, mock_get_settings, mock_repo
    ):
        """Test timeline command."""
        mock_repo.get_timeline.return_value = [
            {
                "timestamp": datetime.now(),
                "event_type": "InvoiceCreated",
                "summary": "Invoice created",
            }
        ]

        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["timeline", "invoice", "1"])

        assert result.exit_code == 0
        mock_repo.get_timeline.assert_called_once_with("invoice", 1)

    @patch("openfatture.cli.commands.events.get_settings")
    @patch("openfatture.cli.commands.events.init_db")
    @patch("openfatture.cli.commands.events.EventRepository")
    @patch("openfatture.cli.commands.events.console")
    def test_search_command(
        self, mock_console, mock_repo_class, mock_init_db, mock_get_settings, mock_repo
    ):
        """Test search command."""
        mock_repo.search.return_value = []

        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["search", "invoice"])

        assert result.exit_code == 0
        mock_repo.search.assert_called_once_with("invoice", limit=100)

    @patch("openfatture.cli.commands.events.get_settings")
    @patch("openfatture.cli.commands.events.init_db")
    @patch("openfatture.cli.commands.events.EventRepository")
    @patch("openfatture.cli.commands.events.console")
    def test_trends_command(
        self, mock_console, mock_repo_class, mock_init_db, mock_get_settings, mock_analytics
    ):
        """Test trends command."""
        with patch("openfatture.cli.commands.events.EventAnalytics", return_value=mock_analytics):
            mock_analytics.get_activity_trends.return_value = {
                "trend": "increasing",
                "change_percent": 25.0,
            }

            from typer.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(app, ["trends"])

            assert result.exit_code == 0
            mock_analytics.get_activity_trends.assert_called_once_with(days=30)
