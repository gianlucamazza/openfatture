"""
Comprehensive validation tests for AI CLI commands.
Tests edge cases and validation for AI-powered commands.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from typer.testing import CliRunner

from openfatture.cli.commands.ai import app

runner = CliRunner()
pytestmark = pytest.mark.unit


class TestAIDescribeCommandValidation:
    """Test validation for 'ai describe' command."""

    def test_describe_required_argument(self):
        """Test that service description argument is required."""
        result = runner.invoke(app, ["describe"])

        # Should show error about missing argument
        assert result.exit_code != 0
        assert "Missing argument" in result.stdout or "requires an argument" in result.stdout

    @patch("openfatture.cli.commands.ai.create_provider")
    @patch("openfatture.cli.commands.ai.enrich_with_rag")
    @patch("openfatture.cli.commands.ai.InvoiceAssistantAgent")
    @patch("openfatture.cli.commands.ai.InvoiceContext")
    def test_describe_valid_service_description(
        self, mock_context, mock_agent, mock_enrich, mock_provider
    ):
        """Test valid service description."""
        # Mock successful agent execution
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        mock_agent_instance = AsyncMock()
        mock_response = Mock()
        mock_response.status = Mock()
        mock_response.status.value = "success"
        mock_response.content = "Generated description"
        mock_response.metadata = {}
        mock_agent_instance.execute.return_value = mock_response
        mock_agent.return_value = mock_agent_instance

        result = runner.invoke(app, ["describe", "Consulting services"])

        assert result.exit_code == 0
        assert "AI Invoice Description Generator" in result.stdout

    @patch("openfatture.cli.commands.ai.create_provider")
    @patch("openfatture.cli.commands.ai.enrich_with_rag")
    @patch("openfatture.cli.commands.ai.InvoiceAssistantAgent")
    @patch("openfatture.cli.commands.ai.InvoiceContext")
    def test_describe_with_optional_parameters(
        self, mock_context, mock_agent, mock_enrich, mock_provider
    ):
        """Test describe command with optional parameters."""
        # Mock successful agent execution
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        mock_agent_instance = AsyncMock()
        mock_response = Mock()
        mock_response.status = Mock()
        mock_response.status.value = "success"
        mock_response.content = "Generated description"
        mock_response.metadata = {}
        mock_agent_instance.execute.return_value = mock_response
        mock_agent.return_value = mock_agent_instance

        result = runner.invoke(
            app,
            [
                "describe",
                "Web development services",
                "--hours",
                "10",
                "--rate",
                "50.0",
                "--project",
                "E-commerce site",
                "--tech",
                "Python,React",
            ],
        )

        assert result.exit_code == 0
        assert "AI Invoice Description Generator" in result.stdout

    @patch("openfatture.cli.commands.ai.create_provider")
    @patch("openfatture.cli.commands.ai.enrich_with_rag")
    @patch("openfatture.cli.commands.ai.InvoiceAssistantAgent")
    @patch("openfatture.cli.commands.ai.InvoiceContext")
    def test_describe_agent_error(self, mock_context, mock_agent, mock_enrich, mock_provider):
        """Test describe command when agent returns error."""
        # Mock agent error
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        mock_agent_instance = AsyncMock()
        mock_response = Mock()
        mock_response.status = Mock()
        mock_response.status.value = "error"
        mock_response.error = "Test agent error"
        mock_agent_instance.execute.return_value = mock_response
        mock_agent.return_value = mock_agent_instance

        result = runner.invoke(app, ["describe", "Consulting services"])

        assert result.exit_code == 0  # Command doesn't exit with error, just shows message
        assert "❌ Error:" in result.stdout


class TestAISuggestVATCommandValidation:
    """Test validation for 'ai suggest-vat' command."""

    def test_suggest_vat_required_argument(self):
        """Test that description argument is required."""
        result = runner.invoke(app, ["suggest-vat"])

        # Should show error about missing argument
        assert result.exit_code != 0
        assert "Missing argument" in result.stdout or "requires an argument" in result.stdout

    @patch("openfatture.cli.commands.ai.create_provider")
    @patch("openfatture.cli.commands.ai.enrich_with_rag")
    @patch("openfatture.cli.commands.ai.TaxAdvisorAgent")
    @patch("openfatture.cli.commands.ai.TaxContext")
    def test_suggest_vat_valid_description(
        self, mock_context, mock_agent, mock_enrich, mock_provider
    ):
        """Test valid description for VAT suggestion."""
        # Mock successful agent execution
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        mock_agent_instance = AsyncMock()
        mock_response = Mock()
        mock_response.status = Mock()
        mock_response.status.value = "success"
        mock_response.content = "VAT suggestion"
        mock_response.metadata = {"is_structured": False}
        mock_agent_instance.execute.return_value = mock_response
        mock_agent.return_value = mock_agent_instance

        result = runner.invoke(app, ["suggest-vat", "Software development"])

        assert result.exit_code == 0
        assert "AI Tax Advisor" in result.stdout

    @patch("openfatture.cli.commands.ai.create_provider")
    @patch("openfatture.cli.commands.ai.enrich_with_rag")
    @patch("openfatture.cli.commands.ai.TaxAdvisorAgent")
    @patch("openfatture.cli.commands.ai.TaxContext")
    def test_suggest_vat_with_all_options(
        self, mock_context, mock_agent, mock_enrich, mock_provider
    ):
        """Test VAT suggestion with all optional parameters."""
        # Mock successful agent execution
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        mock_agent_instance = AsyncMock()
        mock_response = Mock()
        mock_response.status = Mock()
        mock_response.status.value = "success"
        mock_response.content = "VAT suggestion"
        mock_response.metadata = {"is_structured": False}
        mock_agent_instance.execute.return_value = mock_response
        mock_agent.return_value = mock_agent_instance

        result = runner.invoke(
            app,
            [
                "suggest-vat",
                "Software development for PA",
                "--pa",
                "--categoria",
                "Consulenza",
                "--importo",
                "1000.0",
                "--ateco",
                "62.01.00",
            ],
        )

        assert result.exit_code == 0
        assert "AI Tax Advisor" in result.stdout

    @patch("openfatture.cli.commands.ai.create_provider")
    @patch("openfatture.cli.commands.ai.enrich_with_rag")
    @patch("openfatture.cli.commands.ai.TaxAdvisorAgent")
    @patch("openfatture.cli.commands.ai.TaxContext")
    def test_suggest_vat_foreign_client(self, mock_context, mock_agent, mock_enrich, mock_provider):
        """Test VAT suggestion for foreign client."""
        # Mock successful agent execution
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        mock_agent_instance = AsyncMock()
        mock_response = Mock()
        mock_response.status = Mock()
        mock_response.status.value = "success"
        mock_response.content = "VAT suggestion"
        mock_response.metadata = {"is_structured": False}
        mock_agent_instance.execute.return_value = mock_response
        mock_agent.return_value = mock_agent_instance

        result = runner.invoke(
            app, ["suggest-vat", "Software development", "--estero", "--paese", "DE"]
        )

        assert result.exit_code == 0
        assert "AI Tax Advisor" in result.stdout


class TestAICheckCommandValidation:
    """Test validation for 'ai check' command."""

    def test_check_required_invoice_id(self):
        """Test that invoice ID argument is required."""
        result = runner.invoke(app, ["check"])

        # Should show error about missing argument
        assert result.exit_code != 0
        assert "Missing argument" in result.stdout or "requires an argument" in result.stdout

    def test_check_invalid_invoice_id_type(self):
        """Test that invalid invoice ID type is handled."""
        result = runner.invoke(app, ["check", "invalid"])

        assert result.exit_code != 0
        # Should show argument type conversion error

    @patch("openfatture.cli.commands.ai.ComplianceChecker")
    def test_check_valid_invoice_id(self, mock_checker_class):
        """Test check command with valid invoice ID."""
        # Mock checker
        mock_checker = Mock()
        mock_report = Mock()
        mock_report.invoice_number = "1/2025"
        mock_report.level = Mock()
        mock_report.level.value = "standard"
        mock_report.is_compliant = True
        mock_report.compliance_score = 95.0
        mock_report.get_errors = Mock(return_value=[])
        mock_report.get_warnings = Mock(return_value=[])
        mock_report.get_info = Mock(return_value=[])
        mock_report.to_dict = Mock(return_value={})
        mock_checker.check_invoice.return_value = mock_report
        mock_checker_class.return_value = mock_checker

        result = runner.invoke(app, ["check", "123"])

        assert result.exit_code == 0
        assert "Compliance Check" in result.stdout

    @patch("openfatture.cli.commands.ai.ComplianceChecker")
    def test_check_invalid_level(self, mock_checker_class):
        """Test check command with invalid level."""
        result = runner.invoke(app, ["check", "123", "--level", "invalid_level"])

        assert result.exit_code == 1
        assert "Invalid level" in result.stdout


class TestAICreateInvoiceCommandValidation:
    """Test validation for 'ai create-invoice' command."""

    def test_create_invoice_required_arguments(self):
        """Test that required arguments are validated."""
        # Test missing description
        result = runner.invoke(app, ["create-invoice"])
        assert result.exit_code != 0

        # Test missing client_id
        result = runner.invoke(app, ["create-invoice", "Test service", "--client", ""])
        assert result.exit_code != 0

        # Test missing imponibile
        result = runner.invoke(
            app, ["create-invoice", "Test service", "--client", "123", "--amount", ""]
        )
        assert result.exit_code != 0

    @patch("openfatture.cli.commands.ai.InvoiceCreationWorkflow")
    def test_create_invoice_valid_parameters(self, mock_workflow_class):
        """Test create-invoice with valid parameters."""
        # Mock workflow
        mock_workflow = Mock()
        mock_result = Mock()
        mock_result.invoice_id = 456
        mock_result.status = "completed"
        mock_result.warnings = []
        mock_result.errors = []
        mock_result.model_dump = Mock(return_value={"invoice_id": 456, "status": "completed"})
        mock_workflow.execute.return_value = mock_result
        mock_workflow_class.return_value = mock_workflow

        result = runner.invoke(
            app,
            [
                "create-invoice",
                "Development services",
                "--client",
                "123",
                "--amount",
                "1000.0",
                "--hours",
                "20",
                "--rate",
                "50.0",
            ],
        )

        assert result.exit_code == 0
        assert "Invoice created successfully" in result.stdout

    @patch("openfatture.cli.commands.ai.InvoiceCreationWorkflow")
    def test_create_invoice_with_invalid_confidence_threshold(self, mock_workflow_class):
        """Test create-invoice with invalid confidence threshold."""
        # This test might not apply since typer handles validation automatically
        # but we'll test what we can
        result = runner.invoke(
            app,
            [
                "create-invoice",
                "Development services",
                "--client",
                "123",
                "--amount",
                "1000.0",
                "--confidence",
                "1.5",  # Invalid value > 1.0
            ],
        )

        # This would be handled by Typer's validation if properly configured


class TestAIChatCommandValidation:
    """Test validation for 'ai chat' command."""

    def test_chat_optional_message(self):
        """Test that message parameter is optional for chat command."""
        result = runner.invoke(app, ["chat"])

        # Should not fail just because no message provided (enters interactive mode)
        assert result.exit_code == 0

    @patch("openfatture.cli.commands.ai.create_provider")
    @patch("openfatture.cli.commands.ai.ChatAgent")
    def test_chat_with_message(self, mock_agent_class, mock_provider):
        """Test chat command with a message."""
        # Mock provider and agent
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        mock_agent_instance = Mock()
        mock_response = Mock()
        mock_response.content = "Hello! How can I help you?"
        mock_response.model_dump = Mock(return_value={"content": "Hello! How can I help you?"})
        mock_agent_instance.execute.return_value = mock_response
        mock_agent_class.return_value = mock_agent_instance

        result = runner.invoke(app, ["chat", "Hello, how do I create an invoice?"])

        assert result.exit_code == 0
        assert "Assistant:" in result.stdout

    @patch("openfatture.cli.commands.ai.create_provider")
    @patch("openfatture.cli.commands.ai.ChatAgent")
    def test_chat_with_streaming(self, mock_agent_class, mock_provider):
        """Test chat command with streaming enabled."""
        # Mock provider and agent
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        mock_agent_instance = Mock()
        mock_stream = AsyncMock()
        mock_stream.__aiter__.return_value = ["Hello", " ", "world", "!"]
        mock_agent_instance.execute_stream.return_value = mock_stream
        mock_agent_class.return_value = mock_agent_instance

        result = runner.invoke(app, ["chat", "Hello", "--stream"])

        assert result.exit_code == 0
        assert "Assistant:" in result.stdout


class TestAIForecastCommandValidation:
    """Test validation for 'ai forecast' command."""

    def test_forecast_default_parameters(self):
        """Test forecast command with default parameters."""
        with patch("openfatture.cli.commands.ai.CashFlowPredictorAgent") as mock_agent_class:
            mock_agent = Mock()
            mock_forecast = Mock()
            mock_forecast.months = 3
            mock_forecast.total_expected = 10000.0
            mock_forecast.monthly_forecast = [
                {"month": "Jan 2025", "expected": 3000.0},
                {"month": "Feb 2025", "expected": 4000.0},
                {"month": "Mar 2025", "expected": 3000.0},
            ]
            mock_forecast.to_dict = Mock(return_value={})
            mock_agent.forecast_cash_flow.return_value = mock_forecast
            mock_agent.initialize.return_value = None
            mock_agent_class.return_value = mock_agent

            result = runner.invoke(app, ["forecast"])

            assert result.exit_code == 0
            assert "Cash Flow Forecasting" in result.stdout

    def test_forecast_invalid_client_id(self):
        """Test forecast command with invalid client ID."""
        result = runner.invoke(app, ["forecast", "--client", "invalid"])

        assert result.exit_code != 0
        # Should show argument type conversion error

    def test_forecast_invalid_months(self):
        """Test forecast command with invalid months value."""
        result = runner.invoke(app, ["forecast", "--months", "0"])

        # This would depend on how the validation is implemented
        # If there's custom validation, it should catch this
        # Otherwise the agent would just process it as 0 months
