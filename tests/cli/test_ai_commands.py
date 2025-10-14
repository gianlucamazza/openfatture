"""
Tests for AI-powered CLI commands.

Tests Typer commands with mocking of AI providers, agents, and external dependencies.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from openfatture.cli.commands.ai import app

runner = CliRunner()
pytestmark = pytest.mark.unit


class TestRagStatusCommand:
    """Test 'ai rag status' command."""

    @patch("openfatture.cli.commands.ai._rag_status")
    def test_rag_status_success(self, mock_rag_status):
        """Test successful RAG status display."""
        mock_rag_status.return_value = None  # Async function returns None

        result = runner.invoke(app, ["rag", "status"])

        assert result.exit_code == 0
        mock_rag_status.assert_called_once()

    @patch("openfatture.cli.commands.ai._rag_status")
    def test_rag_status_error(self, mock_rag_status):
        """Test RAG status with initialization error."""
        mock_rag_status.side_effect = RuntimeError("API key missing")

        result = runner.invoke(app, ["rag", "status"])

        assert result.exit_code == 1  # CLI exits with error on exceptions


class TestRagIndexCommand:
    """Test 'ai rag index' command."""

    @patch("openfatture.cli.commands.ai._rag_index")
    def test_rag_index_all_sources(self, mock_rag_index):
        """Test indexing all sources."""
        mock_rag_index.return_value = None

        result = runner.invoke(app, ["rag", "index"])

        assert result.exit_code == 0
        mock_rag_index.assert_called_once_with(None)

    @patch("openfatture.cli.commands.ai._rag_index")
    def test_rag_index_specific_sources(self, mock_rag_index):
        """Test indexing specific sources."""
        mock_rag_index.return_value = None

        result = runner.invoke(app, ["rag", "index", "--source", "doc1", "--source", "doc2"])

        assert result.exit_code == 0
        mock_rag_index.assert_called_once_with(["doc1", "doc2"])

    @patch("openfatture.cli.commands.ai._rag_index")
    def test_rag_index_error(self, mock_rag_index):
        """Test indexing with error."""
        mock_rag_index.side_effect = Exception("Indexing failed")

        result = runner.invoke(app, ["rag", "index"])

        assert result.exit_code == 1  # CLI exits with error on exceptions


class TestRagSearchCommand:
    """Test 'ai rag search' command."""

    @patch("openfatture.cli.commands.ai._rag_search")
    def test_rag_search_success(self, mock_rag_search):
        """Test successful semantic search."""
        mock_rag_search.return_value = None

        result = runner.invoke(app, ["rag", "search", "test query"])

        assert result.exit_code == 0
        mock_rag_search.assert_called_once_with("test query", 5, None)

    @patch("openfatture.cli.commands.ai._rag_search")
    def test_rag_search_no_results(self, mock_rag_search):
        """Test search with no results."""
        mock_rag_search.return_value = None

        result = runner.invoke(app, ["rag", "search", "nonexistent query"])

        assert result.exit_code == 0
        mock_rag_search.assert_called_once_with("nonexistent query", 5, None)

    @patch("openfatture.cli.commands.ai._rag_search")
    def test_rag_search_with_filters(self, mock_rag_search):
        """Test search with source filter."""
        mock_rag_search.return_value = None

        result = runner.invoke(app, ["rag", "search", "query", "--source", "filtered_source"])

        assert result.exit_code == 0
        mock_rag_search.assert_called_once_with("query", 5, "filtered_source")


class TestDescribeCommand:
    """Test 'ai describe' command."""

    @patch("openfatture.cli.commands.ai._run_invoice_assistant")
    def test_describe_success_basic(self, mock_run_assistant):
        """Test successful description generation with basic input."""
        mock_run_assistant.return_value = None

        result = runner.invoke(app, ["describe", "3 hours consulting"])

        assert result.exit_code == 0
        mock_run_assistant.assert_called_once()


class TestSuggestVatCommand:
    """Test 'ai suggest-vat' command."""

    @patch("openfatture.cli.commands.ai._run_tax_advisor")
    def test_suggest_vat_basic(self, mock_run_advisor):
        """Test basic VAT suggestion."""
        mock_run_advisor.return_value = None

        result = runner.invoke(app, ["suggest-vat", "consulenza IT"])

        assert result.exit_code == 0

    @patch("openfatture.cli.commands.ai._run_tax_advisor")
    def test_suggest_vat_pa_client(self, mock_run_advisor):
        """Test VAT suggestion for public administration."""
        mock_run_advisor.return_value = None

        result = runner.invoke(app, ["suggest-vat", "servizi professionali", "--pa"])

        assert result.exit_code == 0

    @patch("openfatture.cli.commands.ai._run_tax_advisor")
    def test_suggest_vat_foreign_client(self, mock_run_advisor):
        """Test VAT suggestion for foreign client."""
        mock_run_advisor.return_value = None

        result = runner.invoke(app, ["suggest-vat", "consulenza", "--estero", "--paese", "DE"])

        assert result.exit_code == 0


class TestForecastCommand:
    """Test 'ai forecast' command."""

    @patch("openfatture.cli.commands.ai._run_cash_flow_forecast")
    def test_forecast_success(self, mock_run_forecast):
        """Test successful cash flow forecasting."""
        mock_run_forecast.return_value = None

        result = runner.invoke(app, ["forecast", "--months", "3"])

        assert result.exit_code == 0

    @patch("openfatture.cli.commands.ai._run_cash_flow_forecast")
    def test_forecast_with_client_filter(self, mock_run_forecast):
        """Test forecasting filtered by client."""
        mock_run_forecast.return_value = None

        result = runner.invoke(app, ["forecast", "--client", "123", "--months", "6"])

        assert result.exit_code == 0

    @patch("openfatture.cli.commands.ai._run_cash_flow_forecast")
    def test_forecast_with_retrain(self, mock_run_forecast):
        """Test forecasting with model retraining."""
        mock_run_forecast.return_value = None

        result = runner.invoke(app, ["forecast", "--retrain"])

        assert result.exit_code == 0

    @patch("openfatture.cli.commands.ai._run_cash_flow_forecast")
    def test_forecast_insufficient_data(self, mock_run_forecast):
        """Test forecasting with insufficient data."""
        mock_run_forecast.side_effect = ValueError("Insufficient invoice data for forecasting")

        result = runner.invoke(app, ["forecast"])

        assert result.exit_code == 1


class TestCheckCommand:
    """Test 'ai check' command."""

    @patch("openfatture.cli.commands.ai._run_compliance_check")
    def test_check_basic_level(self, mock_run_check):
        """Test compliance check with basic level."""
        mock_run_check.return_value = None

        result = runner.invoke(app, ["check", "123", "--level", "basic"])

        assert result.exit_code == 0

    @patch("openfatture.cli.commands.ai._run_compliance_check")
    def test_check_advanced_level_with_issues(self, mock_run_check):
        """Test advanced compliance check with issues."""
        mock_run_check.return_value = None

        result = runner.invoke(app, ["check", "456", "--level", "advanced", "--verbose"])

        assert result.exit_code == 0

    @patch("openfatture.cli.commands.ai._run_compliance_check")
    def test_check_invalid_level(self, mock_run_check):
        """Test check with invalid compliance level."""
        mock_run_check.side_effect = SystemExit(1)

        result = runner.invoke(app, ["check", "123", "--level", "invalid"])

        assert result.exit_code == 1

    @patch("openfatture.cli.commands.ai._run_compliance_check")
    def test_check_json_output(self, mock_run_check):
        """Test compliance check with JSON output."""
        mock_run_check.return_value = None

        result = runner.invoke(app, ["check", "123", "--json"])

        assert result.exit_code == 0


class TestCreateInvoiceCommand:
    """Test 'ai create-invoice' command."""

    @patch("openfatture.cli.commands.ai._run_invoice_workflow")
    def test_create_invoice_success(self, mock_run_workflow):
        """Test successful invoice creation via workflow."""
        mock_run_workflow.return_value = None

        result = runner.invoke(
            app,
            ["create-invoice", "web development services", "--client", "456", "--amount", "1500"],
        )

        assert result.exit_code == 0

    @patch("openfatture.cli.commands.ai._run_invoice_workflow")
    def test_create_invoice_with_options(self, mock_run_workflow):
        """Test invoice creation with all options."""
        mock_run_workflow.return_value = None

        result = runner.invoke(
            app,
            [
                "create-invoice",
                "consulting work",
                "--client",
                "789",
                "--amount",
                "2000",
                "--hours",
                "40",
                "--rate",
                "50",
                "--project",
                "ERP System",
                "--tech",
                "Python,Django",
                "--require-approvals",
                "--confidence",
                "0.9",
            ],
        )

        assert result.exit_code == 0

    @patch("openfatture.cli.commands.ai._run_invoice_workflow")
    def test_create_invoice_workflow_error(self, mock_run_workflow):
        """Test invoice creation with workflow error."""
        mock_run_workflow.side_effect = Exception("Workflow failed")

        result = runner.invoke(
            app, ["create-invoice", "test service", "--client", "999", "--amount", "100"]
        )

        assert result.exit_code == 1

    @patch("openfatture.cli.commands.ai._run_invoice_workflow")
    def test_create_invoice_json_output(self, mock_run_workflow):
        """Test invoice creation with JSON output."""
        mock_run_workflow.return_value = None

        result = runner.invoke(
            app, ["create-invoice", "service", "--client", "1", "--amount", "500", "--json"]
        )

        assert result.exit_code == 0


class TestChatCommand:
    """Test 'ai chat' command."""

    @patch("openfatture.cli.commands.ai._run_chat")
    def test_chat_single_message(self, mock_run_chat):
        """Test single message chat."""
        mock_run_chat.return_value = None

        result = runner.invoke(app, ["chat", "Hello AI"])

        assert result.exit_code == 0

    @patch("openfatture.cli.commands.ai._run_chat")
    def test_chat_single_message_streaming(self, mock_run_chat):
        """Test single message chat with streaming."""
        mock_run_chat.return_value = None

        result = runner.invoke(app, ["chat", "Hello", "--stream"])

        assert result.exit_code == 0

    @patch("openfatture.cli.commands.ai._run_chat")
    def test_chat_json_output(self, mock_run_chat):
        """Test chat with JSON output."""
        mock_run_chat.return_value = None

        result = runner.invoke(app, ["chat", "test message", "--json"])

        assert result.exit_code == 0

    @patch("openfatture.cli.commands.ai._run_chat")
    def test_chat_interactive_mode(self, mock_run_chat):
        """Test interactive chat mode."""
        mock_run_chat.return_value = None

        result = runner.invoke(app, ["chat"])

        assert result.exit_code == 0

    @patch("openfatture.cli.commands.ai._run_chat")
    def test_chat_provider_error(self, mock_run_chat):
        """Test chat with provider error."""
        mock_run_chat.side_effect = Exception("Provider unavailable")

        result = runner.invoke(app, ["chat", "test"])

        assert result.exit_code == 1
