"""Tests for OpenAI Chat Completions API tool format in ToolRegistry."""

import pytest

from openfatture.ai.tools import get_tool_registry
from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType


class TestToolRegistryOpenAIFormat:
    """Test ToolRegistry OpenAI function format for Chat Completions API."""

    @pytest.fixture
    def registry(self):
        """Get a fresh tool registry."""
        return get_tool_registry()

    def test_get_openai_functions_format(self, registry):
        """
        Test that get_openai_functions() returns the correct format for Chat Completions API.

        The Chat Completions API expects tools in the format:
        {"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}

        NOT the old Responses API format:
        {"type": "function", "name": ..., "description": ..., "parameters": ...}
        """
        # Get tools in OpenAI format
        tools = registry.get_openai_functions()

        # Should have tools registered
        assert len(tools) > 0, "Expected at least one tool to be registered"

        # Check first tool format
        tool = tools[0]

        # Must have these fields
        assert "type" in tool, "Missing 'type' field"
        assert "function" in tool, "Missing 'function' field"

        # Type must be "function"
        assert tool["type"] == "function", "Expected type='function'"

        # Must have nested "function" field (Chat Completions format)
        assert isinstance(tool["function"], dict), "Function field should be a dict"

        # Function field must contain the actual function schema
        func = tool["function"]
        assert "name" in func, "Function missing 'name' field"
        assert "description" in func, "Function missing 'description' field"
        assert "parameters" in func, "Function missing 'parameters' field"

        # Parameters must be an object with properties and required
        assert isinstance(func["parameters"], dict), "Parameters should be a dict"
        assert func["parameters"]["type"] == "object", "Parameters type should be 'object'"
        assert "properties" in func["parameters"], "Parameters should have 'properties'"

    def test_openai_format_for_all_tools(self, registry):
        """Test that ALL tools have correct format."""
        tools = registry.get_openai_functions()

        for tool in tools:
            # Check structure
            assert tool["type"] == "function"
            assert "function" in tool
            assert isinstance(tool["function"], dict)

            # Function field must contain the actual function schema
            func = tool["function"]
            assert isinstance(func["name"], str)
            assert isinstance(func["description"], str)
            assert isinstance(func["parameters"], dict)

    def test_openai_format_with_custom_tool(self):
        """Test format with a custom tool."""

        def test_func(query: str) -> str:
            return f"Result: {query}"

        tool = Tool(
            name="test_search",
            description="Test search function",
            func=test_func,
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolParameterType.STRING,
                    description="Search query",
                    required=True,
                )
            ],
        )

        # Get OpenAI function format
        func_dict = tool.to_openai_function()

        # Manually wrap like ToolRegistry does (Chat Completions format)
        wrapped = {"type": "function", "function": func_dict}

        # Verify correct format
        assert wrapped["type"] == "function"
        assert "function" in wrapped
        assert isinstance(wrapped["function"], dict)

        # Function field contains the actual schema
        func = wrapped["function"]
        assert func["name"] == "test_search"
        assert func["description"] == "Test search function"
        assert "parameters" in func
