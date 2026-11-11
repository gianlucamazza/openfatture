"""Tests for the ReAct prompt and tool call parsing."""

import pytest

from openfatture.ai.orchestration.parsers import ToolCallParser


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
<thought>I need to search for invoices with specific status</thought>
<action>search_invoices</action>
<action_input>{"stato": "da_inviare", "limit": 5}</action_input>
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
<action>get_client_details</action>
<action_input>{"client_id": 123}</action_input>
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
<action>search_invoices</action>
<action_input>{'stato': 'da_inviare'}</action_input>
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
<THOUGHT>Need to check something</THOUGHT>
<ACTION>get_invoice_stats</ACTION>
<ACTION_INPUT>{"year": 2025}</ACTION_INPUT>
"""

        parsed = parser.parse(response_text)

        assert parsed.is_final is False
        assert parsed.tool_call is not None
        assert parsed.tool_call.tool_name == "get_invoice_stats"

    def test_parse_italian_keywords(self):
        """Test parsing with Italian keywords."""
        parser = ToolCallParser()
        response_text = """
<thought>Devo cercare le fatture</thought>
<action>search_invoices</action>
<action_input>{"limit": 10}</action_input>
"""

        parsed = parser.parse(response_text)

        assert parsed.is_final is False
        assert parsed.tool_call is not None
        assert parsed.tool_call.thought is not None
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
        """Test that XML parsing is tracked."""
        parser = ToolCallParser()

        # Parse XML format
        xml_response = """
<thought>Test</thought>
<action>tool1</action>
<action_input>{}</action_input>
"""
        parser.parse(xml_response)

        # Parse another XML format
        xml_response2 = """
<thought>Test2</thought>
<action>tool2</action>
<action_input>{"param": "value"}</action_input>
"""
        parser.parse(xml_response2)

        stats = parser.get_stats()

        assert stats["xml_parse_count"] == 2
        assert stats["xml_parse_rate"] == 1.0  # All parses are XML

    def test_legacy_format_no_longer_supported(self):
        """Test that legacy text format is no longer supported."""
        parser = ToolCallParser()
        legacy_response = """
Thought: Need to check something
Action: get_data
Action Input: {"id": 123}
"""

        parsed = parser.parse(legacy_response)

        # Should be treated as final answer since no XML tags found
        assert parsed.is_final is True
        assert parsed.tool_call is None

        # Verify no parsing occurred
        stats = parser.get_stats()
        assert stats["xml_parse_count"] == 0

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
        assert parsed.tool_call.thought is not None
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
        assert parsed.tool_call is not None
        assert parsed.tool_call.parameters["filters"]["status"] == "INVIATA"
        assert parsed.tool_call.parameters["filters"]["year"] == 2025
        assert parsed.tool_call.parameters["limit"] == 10


@pytest.mark.asyncio
@pytest.mark.integration
class TestReActIntegration:
    """Integration tests for ReAct orchestration with real components."""

    async def test_react_system_prompt_includes_tools(self):
        """The ReAct prompt carries the XML format and the enabled tools."""
        from openfatture.ai.domain.context import ChatContext
        from openfatture.ai.orchestration.react import build_react_messages
        from openfatture.ai.tools import invoice_tools

        context = ChatContext(user_input="Test query", enable_tools=True)
        messages = build_react_messages(context, invoice_tools.get_invoice_tools())

        system_prompt = messages[0].content
        assert messages[0].role.value == "system"
        assert messages[-1].role.value == "user"
        assert messages[-1].content == "Test query"
        for tag in ("<thought>", "<action>", "<action_input>", "<final_answer>"):
            assert tag in system_prompt
        assert "search_invoices" in system_prompt
        assert "get_invoice_details" in system_prompt

    async def test_react_system_prompt_keeps_the_product_rules(self):
        from openfatture.ai.domain.context import ChatContext
        from openfatture.ai.orchestration.react import build_react_system_prompt
        from openfatture.ai.runtime.prompt import build_chat_system_prompt

        context = ChatContext(user_input="Test query", available_tools=["search_invoices"])
        prompt = build_react_system_prompt(context, [])

        assert prompt.startswith(build_chat_system_prompt(context))
        assert "issued_elsewhere" in prompt
        assert "Nessuno strumento disponibile." in prompt
        # Neither invented business data nor shouted rules.
        for fossil in ("Gamma SpA", "CRITICAL", "SEMPRE"):
            assert fossil not in prompt

    async def test_parser_handles_multiple_formats(self):
        """Test parser robustness with various XML response formats."""
        parser = ToolCallParser()

        formats = [
            # Standard XML format
            """<thought>Test</thought><action>tool1</action><action_input>{"key": "value"}</action_input>""",
            # With extra whitespace
            """  <thought>   Test  </thought>  <action>  tool1  </action>  <action_input>  {"key": "value"}  </action_input>  """,
            # Uppercase XML tags
            """<THOUGHT>Test</THOUGHT><ACTION>tool1</ACTION><ACTION_INPUT>{"key": "value"}</ACTION_INPUT>""",
            # Mixed case XML tags
            """<ThOuGhT>Test</ThOuGhT><ActiOn>tool1</ActiOn><Action_InPut>{"key": "value"}</Action_InPut>""",
        ]

        for response_text in formats:
            parsed = parser.parse(response_text)
            assert parsed.is_final is False
            assert parsed.tool_call is not None
            assert parsed.tool_call.tool_name == "tool1"
            assert parsed.tool_call.parameters == {"key": "value"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
