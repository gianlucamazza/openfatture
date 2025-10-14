"""Tests for ReAct orchestration and tool call parsing."""

import pytest

from openfatture.ai.orchestration.parsers import ParsedResponse, ToolCallParser


class TestToolCallParser:
    """Test ToolCallParser for extracting tool calls from LLM responses."""

    def test_parse_final_answer(self):
        """Test parsing a final answer response."""
        parser = ToolCallParser()
        response_text = """
Thought: I have all the information needed
Final Answer: Ecco le tue fatture:
- Fattura 001/2025 - €1.200
- Fattura 002/2025 - €850
"""

        parsed = parser.parse(response_text)

        assert parsed.is_final is True
        assert "Ecco le tue fatture" in parsed.content
        assert parsed.tool_call is None

    def test_parse_tool_call_with_json_input(self):
        """Test parsing a tool call with JSON parameters."""
        parser = ToolCallParser()
        response_text = """
Thought: I need to search for invoices with specific status
Action: search_invoices
Action Input: {"stato": "da_inviare", "limit": 5}
"""

        parsed = parser.parse(response_text)

        assert parsed.is_final is False
        assert parsed.tool_call is not None
        assert parsed.tool_call.tool_name == "search_invoices"
        assert parsed.tool_call.parameters == {"stato": "da_inviare", "limit": 5}
        assert parsed.tool_call.thought is not None
        assert "search for invoices" in parsed.tool_call.thought

    def test_parse_tool_call_without_thought(self):
        """Test parsing tool call without thought section."""
        parser = ToolCallParser()
        response_text = """
Action: get_client_details
Action Input: {"client_id": 123}
"""

        parsed = parser.parse(response_text)

        assert parsed.is_final is False
        assert parsed.tool_call is not None
        assert parsed.tool_call.tool_name == "get_client_details"
        assert parsed.tool_call.parameters == {"client_id": 123}
        assert parsed.tool_call.thought is None

    def test_parse_tool_call_with_malformed_json(self):
        """Test parsing with malformed JSON (should attempt fix)."""
        parser = ToolCallParser()
        response_text = """
Action: search_invoices
Action Input: {'stato': 'da_inviare'}
"""

        parsed = parser.parse(response_text)

        # Parser should fix single quotes to double quotes
        assert parsed.is_final is False
        assert parsed.tool_call is not None
        assert parsed.tool_call.parameters == {"stato": "da_inviare"}

    def test_parse_case_insensitive(self):
        """Test case-insensitive parsing."""
        parser = ToolCallParser()
        response_text = """
THOUGHT: Need to check something
ACTION: get_invoice_stats
ACTION INPUT: {"year": 2025}
"""

        parsed = parser.parse(response_text)

        assert parsed.is_final is False
        assert parsed.tool_call is not None
        assert parsed.tool_call.tool_name == "get_invoice_stats"

    def test_parse_italian_keywords(self):
        """Test parsing with Italian keywords."""
        parser = ToolCallParser()
        response_text = """
Ragionamento: Devo cercare le fatture
Action: search_invoices
Action Input: {"limit": 10}
"""

        parsed = parser.parse(response_text)

        assert parsed.is_final is False
        assert parsed.tool_call is not None
        assert "Devo cercare" in parsed.tool_call.thought

    def test_parse_no_tool_or_final_treats_as_final(self):
        """Test that responses without tool calls or final answer are treated as final."""
        parser = ToolCallParser()
        response_text = "This is just a regular response without any special format"

        parsed = parser.parse(response_text)

        assert parsed.is_final is True
        assert parsed.content == response_text

    def test_parser_stats_tracking(self):
        """Test that parser tracks statistics."""
        parser = ToolCallParser()

        # Parse some responses
        parser.parse("Final Answer: Test")
        parser.parse("Action: test_tool\nAction Input: {}")
        parser.parse("Invalid format will fail parsing")

        stats = parser.get_stats()

        assert stats["total_parses"] == 3
        assert stats["parse_errors"] >= 0
        assert "error_rate" in stats


class TestXMLToolCallParser:
    """Test XML-based tool call parsing (2025 format)."""

    def test_parse_xml_tool_call_valid(self):
        """Test parsing valid XML tool call."""
        parser = ToolCallParser()
        response_text = """
<thought>Devo ottenere le statistiche delle fatture per l'anno corrente</thought>
<action>get_invoice_stats</action>
<action_input>{"year": 2025}</action_input>
"""

        parsed = parser.parse(response_text)

        assert parsed.is_final is False
        assert parsed.tool_call is not None
        assert parsed.tool_call.tool_name == "get_invoice_stats"
        assert parsed.tool_call.parameters == {"year": 2025}
        assert parsed.tool_call.thought is not None
        assert "statistiche" in parsed.tool_call.thought.lower()

    def test_parse_xml_final_answer(self):
        """Test parsing XML final answer."""
        parser = ToolCallParser()
        response_text = """
<thought>Ho tutti i dati necessari per rispondere</thought>
<final_answer>Hai emesso **42 fatture** nel 2025 per un totale di **€15.000,00**.</final_answer>
"""

        parsed = parser.parse(response_text)

        assert parsed.is_final is True
        assert "42 fatture" in parsed.content
        assert parsed.tool_call is None

    def test_parse_xml_without_thought(self):
        """Test parsing XML tool call without thought tag."""
        parser = ToolCallParser()
        response_text = """
<action>search_invoices</action>
<action_input>{"limit": 3}</action_input>
"""

        parsed = parser.parse(response_text)

        assert parsed.is_final is False
        assert parsed.tool_call is not None
        assert parsed.tool_call.tool_name == "search_invoices"
        assert parsed.tool_call.parameters == {"limit": 3}
        assert parsed.tool_call.thought is None

    def test_parse_xml_malformed_json(self):
        """Test parsing XML with malformed JSON in action_input."""
        parser = ToolCallParser()
        response_text = """
<thought>Need to search</thought>
<action>search_invoices</action>
<action_input>{'limit': 5, 'stato': 'INVIATA'}</action_input>
"""

        parsed = parser.parse(response_text)

        # Parser should fix single quotes
        assert parsed.is_final is False
        assert parsed.tool_call is not None
        assert parsed.tool_call.parameters == {"limit": 5, "stato": "INVIATA"}

    def test_parse_xml_case_insensitive(self):
        """Test XML parsing is case-insensitive."""
        parser = ToolCallParser()
        response_text = """
<THOUGHT>Using uppercase tags</THOUGHT>
<ACTION>test_tool</ACTION>
<ACTION_INPUT>{"key": "value"}</ACTION_INPUT>
"""

        parsed = parser.parse(response_text)

        assert parsed.is_final is False
        assert parsed.tool_call is not None
        assert parsed.tool_call.tool_name == "test_tool"

    def test_parse_xml_empty_action_input(self):
        """Test XML parsing with empty action_input."""
        parser = ToolCallParser()
        response_text = """
<thought>Calling tool without parameters</thought>
<action>get_current_stats</action>
<action_input>{}</action_input>
"""

        parsed = parser.parse(response_text)

        assert parsed.is_final is False
        assert parsed.tool_call is not None
        assert parsed.tool_call.parameters == {}

    def test_parse_xml_metrics_tracking(self):
        """Test that XML parsing is tracked separately."""
        parser = ToolCallParser()

        # Parse XML format
        xml_response = """
<thought>Test</thought>
<action>tool1</action>
<action_input>{}</action_input>
"""
        parser.parse(xml_response)

        # Parse legacy format
        legacy_response = "Thought: Test\nAction: tool2\nAction Input: {}"
        parser.parse(legacy_response)

        stats = parser.get_stats()

        assert stats["xml_parse_count"] == 1
        assert stats["legacy_parse_count"] == 1
        assert stats["xml_parse_rate"] == 0.5  # 1 out of 2

    def test_fallback_to_legacy_when_xml_missing(self):
        """Test fallback to legacy parsing when XML tags not found."""
        parser = ToolCallParser()
        response_text = """
I'll use the legacy format.
Thought: Need to check something
Action: get_data
Action Input: {"id": 123}
"""

        parsed = parser.parse(response_text)

        assert parsed.is_final is False
        assert parsed.tool_call is not None
        assert parsed.tool_call.tool_name == "get_data"

        # Verify legacy parsing was used
        stats = parser.get_stats()
        assert stats["legacy_parse_count"] == 1
        assert stats["xml_parse_count"] == 0

    def test_xml_priority_over_legacy(self):
        """Test that XML parsing takes priority when both formats present."""
        parser = ToolCallParser()
        response_text = """
<thought>XML format</thought>
<action>xml_tool</action>
<action_input>{"xml": true}</action_input>

Thought: Legacy format
Action: legacy_tool
Action Input: {"legacy": true}
"""

        parsed = parser.parse(response_text)

        # Should parse XML first
        assert parsed.is_final is False
        assert parsed.tool_call.tool_name == "xml_tool"
        assert parsed.tool_call.parameters == {"xml": True}

        stats = parser.get_stats()
        assert stats["xml_parse_count"] == 1
        assert stats["legacy_parse_count"] == 0

    def test_xml_with_multiline_thought(self):
        """Test XML parsing with multiline thought content."""
        parser = ToolCallParser()
        response_text = """
<thought>
This is a multiline thought.
It spans multiple lines
and should be preserved.
</thought>
<action>test_tool</action>
<action_input>{"test": true}</action_input>
"""

        parsed = parser.parse(response_text)

        assert parsed.is_final is False
        assert parsed.tool_call is not None
        assert "multiline thought" in parsed.tool_call.thought
        assert "spans multiple lines" in parsed.tool_call.thought

    def test_xml_with_nested_json(self):
        """Test XML parsing with nested JSON in action_input."""
        parser = ToolCallParser()
        response_text = """
<thought>Complex nested data</thought>
<action>complex_tool</action>
<action_input>{"filters": {"status": "INVIATA", "year": 2025}, "limit": 10}</action_input>
"""

        parsed = parser.parse(response_text)

        assert parsed.is_final is False
        assert parsed.tool_call.parameters["filters"]["status"] == "INVIATA"
        assert parsed.tool_call.parameters["filters"]["year"] == 2025
        assert parsed.tool_call.parameters["limit"] == 10


@pytest.mark.asyncio
class TestReActOrchestrator:
    """Test ReActOrchestrator for managing tool calling loop."""

    async def test_orchestrator_initialization(self):
        """Test that orchestrator initializes correctly."""
        from unittest.mock import MagicMock

        from openfatture.ai.orchestration.react import ReActOrchestrator
        from openfatture.ai.tools.registry import ToolRegistry

        provider = MagicMock()
        provider.provider_name = "test_provider"
        provider.model = "test_model"

        registry = ToolRegistry()

        orchestrator = ReActOrchestrator(
            provider=provider,
            tool_registry=registry,
            max_iterations=5,
        )

        assert orchestrator.provider == provider
        assert orchestrator.tool_registry == registry
        assert orchestrator.max_iterations == 5
        assert orchestrator.parser is not None

    async def test_orchestrator_format_observation_dict(self):
        """Test formatting observation from dict."""
        from unittest.mock import MagicMock

        from openfatture.ai.orchestration.react import ReActOrchestrator

        provider = MagicMock()
        registry = MagicMock()

        orchestrator = ReActOrchestrator(provider, registry)

        result = orchestrator._format_observation({"key1": "value1", "key2": 123})

        assert "key1: value1" in result
        assert "key2: 123" in result

    async def test_orchestrator_format_observation_list(self):
        """Test formatting observation from list."""
        from unittest.mock import MagicMock

        from openfatture.ai.orchestration.react import ReActOrchestrator

        provider = MagicMock()
        registry = MagicMock()

        orchestrator = ReActOrchestrator(provider, registry)

        data = [{"id": 1, "name": "Item1"}, {"id": 2, "name": "Item2"}]
        result = orchestrator._format_observation(data)

        assert "id=1" in result
        assert "name=Item1" in result
        assert "id=2" in result
        assert "name=Item2" in result

    async def test_orchestrator_stats(self):
        """Test orchestrator statistics."""
        from unittest.mock import MagicMock

        from openfatture.ai.orchestration.react import ReActOrchestrator

        provider = MagicMock()
        provider.provider_name = "test"
        provider.model = "test-model"

        registry = MagicMock()

        orchestrator = ReActOrchestrator(provider, registry, max_iterations=3)

        stats = orchestrator.get_stats()

        assert stats["provider"] == "test"
        assert stats["model"] == "test-model"
        assert stats["max_iterations"] == 3
        assert "parser_stats" in stats


@pytest.mark.asyncio
@pytest.mark.integration
class TestReActIntegration:
    """Integration tests for ReAct orchestration with real components."""

    async def test_react_system_prompt_includes_tools(self):
        """Test that ReAct system prompt includes tool descriptions."""
        from unittest.mock import AsyncMock, MagicMock

        from openfatture.ai.domain.context import ChatContext
        from openfatture.ai.orchestration.react import ReActOrchestrator
        from openfatture.ai.tools.registry import ToolRegistry

        provider = MagicMock()
        provider.provider_name = "test"

        # Get real tool registry with tools
        registry = ToolRegistry()
        from openfatture.ai.tools import invoice_tools

        for tool in invoice_tools.get_invoice_tools():
            registry.register(tool)

        orchestrator = ReActOrchestrator(provider, registry)

        # Build context
        context = ChatContext(
            user_input="Test query",
            enable_tools=True,
        )

        # Get system prompt
        messages = orchestrator._build_react_messages(context)

        system_prompt = messages[0].content

        # Verify ReAct format instructions are present (check for XML tags - language-agnostic)
        assert "<thought>" in system_prompt or "Thought:" in system_prompt
        assert "<action>" in system_prompt or "Action:" in system_prompt
        assert "<action_input>" in system_prompt or "Action Input:" in system_prompt
        assert "<final_answer>" in system_prompt or "Final Answer:" in system_prompt

        # Verify tools are listed
        assert "search_invoices" in system_prompt
        assert "get_invoice_details" in system_prompt

    async def test_parser_handles_multiple_formats(self):
        """Test parser robustness with various response formats."""
        parser = ToolCallParser()

        formats = [
            # Standard format
            """Thought: Test\nAction: tool1\nAction Input: {"key": "value"}""",
            # With extra whitespace
            """  Thought:   Test  \n  Action:  tool1  \n  Action Input:  {"key": "value"}  """,
            # Uppercase keywords
            """THOUGHT: Test\nACTION: tool1\nACTION INPUT: {"key": "value"}""",
            # Mixed case
            """ThOuGhT: Test\nActiOn: tool1\nAction InPut: {"key": "value"}""",
        ]

        for response_text in formats:
            parsed = parser.parse(response_text)
            assert parsed.is_final is False
            assert parsed.tool_call is not None
            assert parsed.tool_call.tool_name == "tool1"
            assert parsed.tool_call.parameters == {"key": "value"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
