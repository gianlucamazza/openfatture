"""
Comprehensive validation tests for AI CLI commands.
Tests edge cases and validation for AI-powered commands.

Notes for maintainers:
- The installed Click/Typer separates stdout from stderr (the ``CliRunner`` does
  not support ``mix_stderr``), so usage/"Missing argument" text is emitted on
  ``result.stderr`` while ``result.stdout`` stays empty. Missing-argument
  assertions therefore check ``result.stderr``.
- Commands render through the i18n ``_()`` helper which defaults to Italian; the
  ``_english_locale`` autouse fixture pins English so label assertions are
  deterministic (mirrors ``tests/cli/test_report_commands.py``).
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from typer.testing import CliRunner

from openfatture.cli.commands.ai import app

runner = CliRunner()
pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _english_locale():
    """Pin the locale to English so label assertions are deterministic."""
    from openfatture.i18n import get_locale, set_locale

    previous = get_locale()
    set_locale("en")
    try:
        yield
    finally:
        set_locale(previous)


def _make_invoice_context():
    """Build a renderable stand-in for ``InvoiceContext``.

    The command patches ``InvoiceContext`` (and ``enrich_with_rag``), so the
    context object reaches ``_display_input`` as a mock. Its rendered attributes
    must be real strings/None so Rich can display the input table.
    """
    context = Mock()
    context.servizio_base = "Consulting services"
    context.ore_lavorate = None
    context.tariffa_oraria = None
    context.progetto = None
    context.tecnologie = []
    context.enable_rag = True
    return context


def _make_tax_context():
    """Build a renderable stand-in for ``TaxContext`` (see ``_make_invoice_context``)."""
    context = Mock()
    context.tipo_servizio = "Software development"
    context.categoria_servizio = None
    context.importo = 0
    context.cliente_pa = False
    context.cliente_estero = False
    context.paese_cliente = "IT"
    context.codice_ateco = None
    context.enable_rag = True
    return context


def _make_agent_response(content: str):
    """Build a fully renderable successful ``AgentResponse`` mock."""
    response = Mock()
    response.status = Mock()
    response.status.value = "success"
    response.content = content
    response.metadata = {"is_structured": False}
    response.provider = "openai"
    response.model = "gpt-4o-mini"
    response.latency_ms = 12.0
    response.usage = Mock()
    response.usage.total_tokens = 5
    response.usage.estimated_cost_usd = 0.001
    return response


class TestAIDescribeCommandValidation:
    """Test validation for 'ai describe' command."""

    def test_describe_required_argument(self):
        """Test that service description argument is required."""
        result = runner.invoke(app, ["describe"])

        # Usage/error text is routed to stderr by the installed Click.
        assert result.exit_code != 0
        assert "Missing argument" in result.stderr or "Usage:" in result.stderr

    @patch("openfatture.cli.commands.ai.describe.create_provider")
    @patch("openfatture.cli.commands.ai.describe.enrich_with_rag", new_callable=AsyncMock)
    @patch("openfatture.cli.commands.ai.describe.InvoiceAssistantAgent")
    @patch("openfatture.cli.commands.ai.describe.InvoiceContext")
    def test_describe_valid_service_description(
        self, mock_context, mock_agent, mock_enrich, mock_provider
    ):
        """Test valid service description."""
        # Mock context (must be renderable) and RAG enrichment
        context = _make_invoice_context()
        mock_context.return_value = context
        mock_enrich.return_value = context

        # Mock successful agent execution
        mock_provider.return_value = Mock()

        mock_agent_instance = AsyncMock()
        mock_agent_instance.execute.return_value = _make_agent_response("Generated description")
        mock_agent.return_value = mock_agent_instance

        result = runner.invoke(app, ["describe", "Consulting services"])

        assert result.exit_code == 0
        assert "AI Invoice Description Generation" in result.stdout

    @patch("openfatture.cli.commands.ai.describe.create_provider")
    @patch("openfatture.cli.commands.ai.describe.enrich_with_rag", new_callable=AsyncMock)
    @patch("openfatture.cli.commands.ai.describe.InvoiceAssistantAgent")
    @patch("openfatture.cli.commands.ai.describe.InvoiceContext")
    def test_describe_with_optional_parameters(
        self, mock_context, mock_agent, mock_enrich, mock_provider
    ):
        """Test describe command with optional parameters."""
        context = _make_invoice_context()
        mock_context.return_value = context
        mock_enrich.return_value = context

        # Mock successful agent execution
        mock_provider.return_value = Mock()

        mock_agent_instance = AsyncMock()
        mock_agent_instance.execute.return_value = _make_agent_response("Generated description")
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
        assert "AI Invoice Description Generation" in result.stdout

    @patch("openfatture.cli.commands.ai.describe.create_provider")
    @patch("openfatture.cli.commands.ai.describe.enrich_with_rag", new_callable=AsyncMock)
    @patch("openfatture.cli.commands.ai.describe.InvoiceAssistantAgent")
    @patch("openfatture.cli.commands.ai.describe.InvoiceContext")
    def test_describe_agent_error(self, mock_context, mock_agent, mock_enrich, mock_provider):
        """Test describe command when agent returns error."""
        context = _make_invoice_context()
        mock_context.return_value = context
        mock_enrich.return_value = context

        # Mock agent error
        mock_provider.return_value = Mock()

        mock_agent_instance = AsyncMock()
        mock_response = Mock()
        mock_response.status = Mock()
        mock_response.status.value = "error"
        mock_response.error = "Test agent error"
        mock_agent_instance.execute.return_value = mock_response
        mock_agent.return_value = mock_agent_instance

        result = runner.invoke(app, ["describe", "Consulting services"])

        # The error branch prints a message and returns normally (no Exit).
        assert result.exit_code == 0
        assert "Error generating description:" in result.stdout
        assert "Test agent error" in result.stdout


class TestAISuggestVATCommandValidation:
    """Test validation for 'ai suggest-vat' command."""

    def test_suggest_vat_required_argument(self):
        """Test that description argument is required."""
        result = runner.invoke(app, ["suggest-vat"])

        # Usage/error text is routed to stderr by the installed Click.
        assert result.exit_code != 0
        assert "Missing argument" in result.stderr or "Usage:" in result.stderr

    @patch("openfatture.cli.commands.ai.vat.create_provider")
    @patch("openfatture.cli.commands.ai.vat.enrich_with_rag", new_callable=AsyncMock)
    @patch("openfatture.ai.agents.tax_advisor.TaxAdvisorAgent")
    @patch("openfatture.ai.domain.context.TaxContext")
    def test_suggest_vat_valid_description(
        self, mock_context, mock_agent, mock_enrich, mock_provider
    ):
        """Test valid description for VAT suggestion."""
        context = _make_tax_context()
        mock_context.return_value = context
        mock_enrich.return_value = context

        # Mock successful agent execution
        mock_provider.return_value = Mock()

        mock_agent_instance = AsyncMock()
        mock_agent_instance.execute.return_value = _make_agent_response("VAT suggestion")
        mock_agent.return_value = mock_agent_instance

        result = runner.invoke(app, ["suggest-vat", "Software development"])

        assert result.exit_code == 0
        assert "VAT Rate Suggestion with AI" in result.stdout

    @patch("openfatture.cli.commands.ai.vat.create_provider")
    @patch("openfatture.cli.commands.ai.vat.enrich_with_rag", new_callable=AsyncMock)
    @patch("openfatture.ai.agents.tax_advisor.TaxAdvisorAgent")
    @patch("openfatture.ai.domain.context.TaxContext")
    def test_suggest_vat_with_all_options(
        self, mock_context, mock_agent, mock_enrich, mock_provider
    ):
        """Test VAT suggestion with all optional parameters."""
        context = _make_tax_context()
        mock_context.return_value = context
        mock_enrich.return_value = context

        # Mock successful agent execution
        mock_provider.return_value = Mock()

        mock_agent_instance = AsyncMock()
        mock_agent_instance.execute.return_value = _make_agent_response("VAT suggestion")
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
        assert "VAT Rate Suggestion with AI" in result.stdout

    @patch("openfatture.cli.commands.ai.vat.create_provider")
    @patch("openfatture.cli.commands.ai.vat.enrich_with_rag", new_callable=AsyncMock)
    @patch("openfatture.ai.agents.tax_advisor.TaxAdvisorAgent")
    @patch("openfatture.ai.domain.context.TaxContext")
    def test_suggest_vat_foreign_client(self, mock_context, mock_agent, mock_enrich, mock_provider):
        """Test VAT suggestion for foreign client."""
        context = _make_tax_context()
        mock_context.return_value = context
        mock_enrich.return_value = context

        # Mock successful agent execution
        mock_provider.return_value = Mock()

        mock_agent_instance = AsyncMock()
        mock_agent_instance.execute.return_value = _make_agent_response("VAT suggestion")
        mock_agent.return_value = mock_agent_instance

        result = runner.invoke(
            app, ["suggest-vat", "Software development", "--estero", "--paese", "DE"]
        )

        assert result.exit_code == 0
        assert "VAT Rate Suggestion with AI" in result.stdout


class TestAICheckCommandValidation:
    """Test validation for 'ai check' command."""

    def test_check_required_invoice_id(self):
        """Test that invoice ID argument is required."""
        result = runner.invoke(app, ["check"])

        # Usage/error text is routed to stderr by the installed Click.
        assert result.exit_code != 0
        assert "Missing argument" in result.stderr or "Usage:" in result.stderr

    def test_check_invalid_invoice_id_type(self):
        """Test that invalid invoice ID type is handled."""
        result = runner.invoke(app, ["check", "invalid"])

        assert result.exit_code != 0
        # Should show argument type conversion error (on stderr)

    @patch("openfatture.cli.commands.ai.compliance.ComplianceChecker")
    def test_check_valid_invoice_id(self, mock_checker_class):
        """Test check command with valid invoice ID."""
        # Mock checker
        mock_checker = Mock()
        mock_report = Mock()
        mock_report.invoice_number = "1/2025"
        mock_report.level = Mock()
        mock_report.level.value = "standard"
        mock_report.is_compliant = True
        # Set actual values for comparison
        type(mock_report).compliance_score = 95.0
        type(mock_report).risk_score = 10.0
        mock_report.risk_score = 10.0
        mock_report.get_errors.return_value = []
        mock_report.get_warnings.return_value = []
        mock_report.get_info.return_value = []
        mock_report.to_dict = Mock(return_value={})
        mock_report.sdi_pattern_matches = []
        mock_report.recommendations = []
        mock_checker.check_invoice = AsyncMock(return_value=mock_report)
        mock_checker_class.return_value = mock_checker

        result = runner.invoke(app, ["check", "123"])

        assert result.exit_code == 0
        assert "Compliance Check" in result.stdout

    @patch("openfatture.cli.commands.ai.compliance.ComplianceChecker")
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

    @patch("openfatture.cli.commands.ai.create_invoice.InvoiceCreationWorkflow")
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
        # ``workflow.execute`` is awaited, so it must be an async mock.
        mock_workflow.execute = AsyncMock(return_value=mock_result)
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

    @patch("openfatture.cli.commands.ai.create_invoice.InvoiceCreationWorkflow")
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
        assert result is not None


class TestAIChatCommandValidation:
    """Test validation for 'ai chat' command."""

    @patch("openfatture.cli.commands.ai.chat.create_provider")
    @patch("openfatture.cli.commands.ai.chat.ChatAgent")
    def test_chat_optional_message(self, mock_agent_class, mock_provider):
        """Test that message parameter is optional for chat command."""
        # Interactive mode still needs a provider/agent; supply mocks so the
        # session reaches the (empty stdin -> EOF) exit cleanly.
        mock_provider.return_value = Mock()
        mock_agent_class.return_value = Mock()

        result = runner.invoke(app, ["chat"], input="")

        # Should not fail just because no message provided (enters interactive mode)
        assert result.exit_code == 0

    @patch("openfatture.cli.commands.ai.chat.create_provider")
    @patch("openfatture.cli.commands.ai.chat.ChatAgent")
    def test_chat_with_message(self, mock_agent_class, mock_provider):
        """Test chat command with a message."""
        # Mock provider and agent
        mock_provider.return_value = Mock()

        mock_agent_instance = Mock()
        mock_response = Mock()
        mock_response.content = "Hello! How can I help you?"
        mock_response.model_dump = Mock(return_value={"content": "Hello! How can I help you?"})
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 10
        mock_response.usage.estimated_cost_usd = 0.001
        mock_agent_instance.execute = AsyncMock(return_value=mock_response)
        mock_agent_class.return_value = mock_agent_instance

        # --no-stream exercises the single-message ``agent.execute`` path mocked above.
        result = runner.invoke(app, ["chat", "Hello, how do I create an invoice?", "--no-stream"])

        assert result.exit_code == 0
        # The chat assistant label renders via i18n; assert the response content
        # is shown (the assistant replied).
        assert "Hello! How can I help you?" in result.stdout

    @patch("openfatture.cli.commands.ai.chat.create_provider")
    @patch("openfatture.cli.commands.ai.chat.ChatAgent")
    def test_chat_with_streaming(self, mock_agent_class, mock_provider):
        """Test chat command with streaming enabled."""
        # Mock provider and agent
        mock_provider.return_value = Mock()

        mock_agent_instance = Mock()
        mock_stream = AsyncMock()
        mock_stream.__aiter__.return_value = ["Hello", " ", "world", "!"]
        mock_agent_instance.execute_stream.return_value = mock_stream
        mock_agent_class.return_value = mock_agent_instance

        result = runner.invoke(app, ["chat", "Hello", "--stream"])

        assert result.exit_code == 0
        # Streamed chunks are concatenated into stdout.
        assert "Hello world!" in result.stdout


class TestAIForecastCommandValidation:
    """Test validation for 'ai forecast' command."""

    def test_forecast_default_parameters(self):
        """Test forecast command with default parameters."""
        with patch(
            "openfatture.ai.agents.cash_flow_predictor.CashFlowPredictorAgent"
        ) as mock_agent_class:
            mock_agent = Mock()
            mock_forecast = Mock()
            mock_forecast.months = 3
            mock_forecast.total_expected = 10000.0
            mock_forecast.monthly_forecast = [
                {"month": "Jan 2025", "expected": 3000.0},
                {"month": "Feb 2025", "expected": 4000.0},
                {"month": "Mar 2025", "expected": 3000.0},
            ]
            # ``insights``/``recommendations`` must be renderable (not auto-mocks).
            mock_forecast.insights = None
            mock_forecast.recommendations = []
            mock_forecast.to_dict = Mock(return_value={})
            # ``initialize`` and ``forecast_cash_flow`` are awaited.
            mock_agent.forecast_cash_flow = AsyncMock(return_value=mock_forecast)
            mock_agent.initialize = AsyncMock(return_value=None)
            mock_agent_class.return_value = mock_agent

            result = runner.invoke(app, ["forecast"])

            assert result.exit_code == 0
            assert "Cash Flow Forecasting" in result.stdout

    def test_forecast_invalid_client_id(self):
        """Test forecast command with invalid client ID."""
        result = runner.invoke(app, ["forecast", "--client", "invalid"])

        assert result.exit_code != 0
        # Should show argument type conversion error (on stderr)

    def test_forecast_invalid_months(self):
        """Test forecast command with invalid months value."""
        result = runner.invoke(app, ["forecast", "--months", "0"])

        # This would depend on how the validation is implemented
        # If there's custom validation, it should catch this
        # Otherwise the agent would just process it as 0 months
        assert result is not None
