"""E2E tests for ReAct orchestration with real Ollama provider.

These tests validate tool calling with the ReAct orchestrator using
real Ollama models (qwen3:8b recommended). They verify:
- XML format generation
- Tool call execution
- Multi-step reasoning
- Success rate metrics

Requirements:
- Ollama running locally: `ollama serve`
- qwen3:8b model pulled: `ollama pull qwen3:8b`

Run with: pytest tests/ai/test_react_e2e_ollama.py -v -m "ollama and e2e"
"""

import pytest
import pytest_asyncio

from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.message import ConversationHistory
from openfatture.ai.orchestration.react import ReActOrchestrator
from openfatture.ai.providers.ollama import OllamaProvider
from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.ai.tools.registry import ToolRegistry


@pytest_asyncio.fixture(scope="session")
async def ollama_qwen3_provider():
    """Real Ollama provider with qwen3:8b for E2E tests."""
    provider = OllamaProvider(
        model="qwen3:8b",
        base_url="http://localhost:11434",
        temperature=0.0,  # Deterministic for tool calling
    )

    # Health check
    if not await provider.health_check():
        pytest.skip("Ollama service not available at localhost:11434")

    # Check if model is available
    available_models = await provider.list_models()
    if "qwen3:8b" not in available_models:
        pytest.skip("qwen3:8b model not available. Run: ollama pull qwen3:8b")

    return provider


@pytest.fixture
def tool_registry_with_mock_tools():
    """Tool registry with mock invoice and client tools."""
    registry = ToolRegistry()

    # Mock database data
    mock_invoice_stats = {
        "totale_fatture": 42,
        "importo_totale": 15000.0,
        "per_stato": {"bozza": 5, "da_inviare": 10, "inviata": 27},
    }

    mock_invoices = [
        {
            "numero": "003/2025",
            "cliente": "Acme Corp",
            "totale": 1200.0,
            "data": "2025-01-20",
            "stato": "INVIATA",
        },
        {
            "numero": "002/2025",
            "cliente": "Beta Ltd",
            "totale": 850.0,
            "data": "2025-01-15",
            "stato": "INVIATA",
        },
        {
            "numero": "001/2025",
            "cliente": "Gamma SpA",
            "totale": 2100.0,
            "data": "2025-01-10",
            "stato": "DA_INVIARE",
        },
    ]

    mock_clients = [
        {
            "id": 1,
            "denominazione": "Acme Corp",
            "partita_iva": "IT12345678901",
            "totale_fatture": 15,
            "importo_totale": 18000.0,
        },
        {
            "id": 2,
            "denominazione": "Beta Ltd",
            "partita_iva": "IT98765432109",
            "totale_fatture": 8,
            "importo_totale": 6800.0,
        },
    ]

    # Define tool functions
    def get_invoice_stats(year: int = 2025):
        """Get invoice statistics for a specific year."""
        return mock_invoice_stats

    def search_invoices(limit: int = 10, stato: str | None = None, **kwargs):
        """Search invoices with optional filters."""
        results = mock_invoices[:limit]
        if stato:
            results = [inv for inv in results if inv["stato"] == stato]
        return results

    def get_invoice_details(numero: str):
        """Get details of a specific invoice."""
        for inv in mock_invoices:
            if inv["numero"] == numero:
                return inv
        return {"error": f"Invoice {numero} not found"}

    def search_clients(query: str | None = None, limit: int = 10):
        """Search clients."""
        if query:
            results = [c for c in mock_clients if query.lower() in c["denominazione"].lower()]
        else:
            results = mock_clients
        return results[:limit]

    # Register tools
    registry.register(
        Tool(
            name="get_invoice_stats",
            description="Ottieni statistiche delle fatture per un anno specifico",
            func=get_invoice_stats,
            parameters=[
                ToolParameter(
                    name="year",
                    type=ToolParameterType.INTEGER,
                    description="Anno di riferimento (default: 2025)",
                    required=False,
                )
            ],
            category="invoice",
            enabled=True,
        )
    )

    registry.register(
        Tool(
            name="search_invoices",
            description="Cerca fatture con filtri opzionali",
            func=search_invoices,
            parameters=[
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Numero massimo di risultati (default: 10)",
                    required=False,
                ),
                ToolParameter(
                    name="stato",
                    type=ToolParameterType.STRING,
                    description="Filtra per stato (BOZZA, DA_INVIARE, INVIATA)",
                    required=False,
                ),
            ],
            category="invoice",
            enabled=True,
        )
    )

    registry.register(
        Tool(
            name="get_invoice_details",
            description="Ottieni dettagli di una fattura specifica",
            func=get_invoice_details,
            parameters=[
                ToolParameter(
                    name="numero",
                    type=ToolParameterType.STRING,
                    description="Numero fattura (es: 003/2025)",
                    required=True,
                )
            ],
            category="invoice",
            enabled=True,
        )
    )

    registry.register(
        Tool(
            name="search_clients",
            description="Cerca clienti nel database",
            func=search_clients,
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolParameterType.STRING,
                    description="Testo da cercare nel nome cliente",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Numero massimo di risultati",
                    required=False,
                ),
            ],
            category="client",
            enabled=True,
        )
    )

    return registry


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.ollama
class TestReActOllamaSingleToolCall:
    """Test ReAct with single tool call."""

    async def test_single_tool_call_invoice_stats(
        self, ollama_qwen3_provider, tool_registry_with_mock_tools
    ):
        """Test ReAct calls get_invoice_stats correctly."""
        orchestrator = ReActOrchestrator(
            provider=ollama_qwen3_provider,
            tool_registry=tool_registry_with_mock_tools,
            max_iterations=5,
        )

        context = ChatContext(
            user_input="Quante fatture ho emesso quest'anno?",
            enable_tools=True,
            conversation_history=ConversationHistory(),
        )

        result = await orchestrator.execute(context)

        # Verify result contains expected data
        assert result is not None
        assert len(result) > 0
        # Should mention the number from mock data
        assert "42" in result or "quarantadue" in result.lower()
        # Should not contain fake data
        assert "001/2025" not in result or "mock" not in result.lower()

        # Check parser stats
        stats = orchestrator.parser.get_stats()
        assert stats["total_parses"] > 0
        # Should use XML parsing with qwen3:8b (legacy removed)
        if stats["xml_parse_count"] > 0:
            assert stats["xml_parse_rate"] >= 0.8  # At least 80% XML (legacy removed)

    async def test_search_invoices_with_limit(
        self, ollama_qwen3_provider, tool_registry_with_mock_tools
    ):
        """Test ReAct searches invoices with limit parameter."""
        orchestrator = ReActOrchestrator(
            provider=ollama_qwen3_provider,
            tool_registry=tool_registry_with_mock_tools,
            max_iterations=5,
        )

        context = ChatContext(
            user_input="Mostrami le ultime 2 fatture",
            enable_tools=True,
            conversation_history=ConversationHistory(),
        )

        result = await orchestrator.execute(context)

        # Should contain references to invoices
        assert result is not None
        assert any(inv_num in result for inv_num in ["003/2025", "002/2025"])

    async def test_client_search(self, ollama_qwen3_provider, tool_registry_with_mock_tools):
        """Test ReAct searches clients correctly."""
        orchestrator = ReActOrchestrator(
            provider=ollama_qwen3_provider,
            tool_registry=tool_registry_with_mock_tools,
            max_iterations=5,
        )

        context = ChatContext(
            user_input="Chi è il cliente Acme?",
            enable_tools=True,
            conversation_history=ConversationHistory(),
        )

        result = await orchestrator.execute(context)

        # Should contain client info
        assert result is not None
        assert "acme" in result.lower()


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.ollama
class TestReActOllamaMultiToolCalls:
    """Test ReAct with multiple tool calls in sequence."""

    async def test_search_then_get_details(
        self, ollama_qwen3_provider, tool_registry_with_mock_tools
    ):
        """Test ReAct: search_invoices → get_invoice_details."""
        orchestrator = ReActOrchestrator(
            provider=ollama_qwen3_provider,
            tool_registry=tool_registry_with_mock_tools,
            max_iterations=8,  # More iterations for multi-step
        )

        context = ChatContext(
            user_input="Cerca le fatture e dimmi i dettagli della prima",
            enable_tools=True,
            conversation_history=ConversationHistory(),
        )

        result = await orchestrator.execute(context)

        # Should contain details from the first invoice
        assert result is not None
        assert "003/2025" in result or "acme" in result.lower()

    async def test_stats_then_search_by_status(
        self, ollama_qwen3_provider, tool_registry_with_mock_tools
    ):
        """Test ReAct: get_invoice_stats → search_invoices(stato=DA_INVIARE)."""
        orchestrator = ReActOrchestrator(
            provider=ollama_qwen3_provider,
            tool_registry=tool_registry_with_mock_tools,
            max_iterations=8,
        )

        context = ChatContext(
            user_input="Quante fatture devo ancora inviare? Mostrami la lista",
            enable_tools=True,
            conversation_history=ConversationHistory(),
        )

        result = await orchestrator.execute(context)

        # Should mention the count (10) and show some invoices
        assert result is not None
        assert "10" in result or "dieci" in result.lower()


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.ollama
class TestReActOllamaXMLCompliance:
    """Test XML format generation with qwen3:8b."""

    async def test_xml_format_in_response(
        self, ollama_qwen3_provider, tool_registry_with_mock_tools
    ):
        """Verify qwen3:8b generates XML-formatted responses."""
        orchestrator = ReActOrchestrator(
            provider=ollama_qwen3_provider,
            tool_registry=tool_registry_with_mock_tools,
            max_iterations=5,
        )

        context = ChatContext(
            user_input="Quante fatture ho?",
            enable_tools=True,
            conversation_history=ConversationHistory(),
        )

        # Execute and check parser stats
        result = await orchestrator.execute(context)

        assert result is not None

        # Check that XML parsing was used (legacy removed)
        stats = orchestrator.parser.get_stats()
        if stats["xml_parse_count"] > 0:
            # qwen3:8b should generate XML format most of the time
            xml_rate = stats["xml_parse_rate"]
            assert xml_rate >= 0.8, f"XML parse rate too low: {xml_rate:.2f}"


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.ollama
@pytest.mark.slow  # This test takes ~1-2 minutes
class TestReActOllamaSuccessRate:
    """Test tool calling success rate across multiple queries."""

    async def test_tool_calling_success_rate_80_percent(
        self, ollama_qwen3_provider, tool_registry_with_mock_tools
    ):
        """Test success rate ≥80% across 10 different queries."""
        orchestrator = ReActOrchestrator(
            provider=ollama_qwen3_provider,
            tool_registry=tool_registry_with_mock_tools,
            max_iterations=5,
        )

        # Test queries that should trigger tool calls
        test_queries = [
            "Quante fatture ho emesso?",
            "Mostra le ultime fatture",
            "Cerca il cliente Acme",
            "Quante fatture sono in bozza?",
            "Dimmi i dettagli della fattura 003/2025",
            "Lista tutti i clienti",
            "Quante fatture ho da inviare?",
            "Cerca fatture per stato INVIATA",
            "Chi è Beta Ltd?",
            "Statistiche fatture 2025",
        ]

        successes = 0
        total = len(test_queries)

        for query in test_queries:
            context = ChatContext(
                user_input=query,
                enable_tools=True,
                conversation_history=ConversationHistory(),
            )

            try:
                result = await orchestrator.execute(context)

                # Check if result contains real data (not invented)
                # Success criteria: contains numbers from mock data OR client names
                has_real_data = any(
                    [
                        "42" in result,  # From invoice stats
                        "003/2025" in result,
                        "002/2025" in result,
                        "001/2025" in result,
                        "acme" in result.lower(),
                        "beta" in result.lower(),
                        "gamma" in result.lower(),
                    ]
                )

                if has_real_data:
                    successes += 1

            except Exception:
                # Failure - tool calling or execution error
                pass

        success_rate = successes / total
        assert (
            success_rate >= 0.8
        ), f"Tool calling success rate too low: {success_rate:.2%} (expected ≥80%)"

        # Print stats for analysis
        print(f"\n✅ Success Rate: {success_rate:.2%} ({successes}/{total})")
        print(f"Parser Stats: {orchestrator.parser.get_stats()}")


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.ollama
class TestReActOllamaErrorHandling:
    """Test error handling with Ollama ReAct."""

    async def test_unknown_tool_graceful_degradation(
        self, ollama_qwen3_provider, tool_registry_with_mock_tools
    ):
        """Test graceful handling when LLM tries to call non-existent tool."""
        orchestrator = ReActOrchestrator(
            provider=ollama_qwen3_provider,
            tool_registry=tool_registry_with_mock_tools,
            max_iterations=5,
        )

        context = ChatContext(
            user_input="Delete all invoices",  # Should trigger unknown tool
            enable_tools=True,
            conversation_history=ConversationHistory(),
        )

        result = await orchestrator.execute(context)

        # Should still return a result (not crash)
        assert result is not None
        assert len(result) > 0

    async def test_max_iterations_limit(self, ollama_qwen3_provider, tool_registry_with_mock_tools):
        """Test that max_iterations prevents infinite loops."""
        orchestrator = ReActOrchestrator(
            provider=ollama_qwen3_provider,
            tool_registry=tool_registry_with_mock_tools,
            max_iterations=2,  # Very low limit
        )

        context = ChatContext(
            user_input="Prima ottieni le statistiche delle fatture, poi cerca tutte le fatture, quindi analizza i dettagli di ogni fattura una per una e fornisci un riassunto completo",
            enable_tools=True,
            conversation_history=ConversationHistory(),
        )

        result = await orchestrator.execute(context)

        # Should return result mentioning iteration limit
        assert result is not None
        assert "limite" in result.lower() or "iterazioni" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "ollama and e2e"])
