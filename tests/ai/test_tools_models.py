"""Tests for AI tools models."""

import pytest

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolResult


class TestToolParameter:
    """Test ToolParameter model."""

    def test_tool_parameter_creation(self):
        """Test creating a ToolParameter."""
        param = ToolParameter(
            name="query",
            type=ToolParameterType.STRING,
            description="Search query",
            required=True,
        )
        assert param.name == "query"
        assert param.type == ToolParameterType.STRING
        assert param.description == "Search query"
        assert param.required is True

    def test_tool_parameter_to_openai_schema(self):
        """Test converting to OpenAI schema."""
        param = ToolParameter(
            name="limit",
            type=ToolParameterType.INTEGER,
            description="Maximum results",
            required=False,
            default=10,
        )
        schema = param.to_openai_schema()
        assert schema["type"] == "integer"
        assert schema["description"] == "Maximum results"
        assert "enum" not in schema

    def test_tool_parameter_with_enum(self):
        """Test parameter with enum values."""
        param = ToolParameter(
            name="sort_order",
            type=ToolParameterType.STRING,
            description="Sort order",
            enum=["asc", "desc"],
        )
        schema = param.to_openai_schema()
        assert schema["enum"] == ["asc", "desc"]


class TestTool:
    """Test Tool model."""

    def test_tool_creation(self):
        """Test creating a Tool."""

        def dummy_func(x: int) -> int:
            return x * 2

        tool = Tool(
            name="multiply",
            description="Multiply by 2",
            func=dummy_func,
            parameters=[
                ToolParameter(
                    name="value",
                    type=ToolParameterType.INTEGER,
                    description="Value to multiply",
                )
            ],
        )
        assert tool.name == "multiply"
        assert tool.description == "Multiply by 2"
        assert tool.category == "general"
        assert len(tool.parameters) == 1

    def test_tool_to_openai_function(self):
        """Test converting to OpenAI function format."""

        def search_func(query: str) -> str:
            return f"Searching for {query}"

        tool = Tool(
            name="search",
            description="Search for information",
            func=search_func,
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolParameterType.STRING,
                    description="Search query",
                    required=True,
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Max results",
                    required=False,
                    default=10,
                ),
            ],
        )

        openai_func = tool.to_openai_function()
        assert openai_func["name"] == "search"
        assert openai_func["description"] == "Search for information"
        assert "parameters" in openai_func
        assert openai_func["parameters"]["type"] == "object"
        assert "query" in openai_func["parameters"]["properties"]
        assert "limit" in openai_func["parameters"]["properties"]
        assert openai_func["parameters"]["required"] == ["query"]

    def test_tool_to_anthropic_tool(self):
        """Test converting to Anthropic tool format."""

        def add_func(a: int, b: int) -> int:
            return a + b

        tool = Tool(
            name="add",
            description="Add two numbers",
            func=add_func,
            parameters=[
                ToolParameter(
                    name="a",
                    type=ToolParameterType.INTEGER,
                    description="First number",
                ),
                ToolParameter(
                    name="b",
                    type=ToolParameterType.INTEGER,
                    description="Second number",
                ),
            ],
        )

        anthropic_tool = tool.to_anthropic_tool()
        assert anthropic_tool["name"] == "add"
        assert anthropic_tool["description"] == "Add two numbers"
        assert "input_schema" in anthropic_tool
        assert anthropic_tool["input_schema"]["type"] == "object"

    @pytest.mark.asyncio
    async def test_tool_execute_success(self):
        """Test successful tool execution."""

        def multiply(x: int) -> int:
            return x * 2

        tool = Tool(
            name="multiply",
            description="Multiply by 2",
            func=multiply,
            parameters=[
                ToolParameter(
                    name="x",
                    type=ToolParameterType.INTEGER,
                    description="Number to multiply",
                    required=True,
                ),
            ],
        )

        result = await tool.execute(x=5)
        assert result.success is True
        assert result.data == 10
        assert result.tool_name == "multiply"
        assert result.execution_time is not None
        assert result.retries == 0

    @pytest.mark.asyncio
    async def test_tool_execute_missing_required_param(self):
        """Test execution with missing required parameter."""

        def multiply(x: int) -> int:
            return x * 2

        tool = Tool(
            name="multiply",
            description="Multiply by 2",
            func=multiply,
            parameters=[
                ToolParameter(
                    name="x",
                    type=ToolParameterType.INTEGER,
                    description="Number to multiply",
                    required=True,
                ),
            ],
        )

        result = await tool.execute()  # Missing x
        assert result.success is False
        assert result.error is not None
        assert "Required parameter 'x' missing" in result.error
        assert result.tool_name == "multiply"

    @pytest.mark.asyncio
    async def test_tool_execute_with_exception(self):
        """Test execution that raises an exception."""

        def failing_func():
            raise ValueError("Something went wrong")

        tool = Tool(
            name="failing",
            description="Always fails",
            func=failing_func,
        )

        result = await tool.execute()
        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.error_type == "ValueError"
        assert result.tool_name == "failing"


class TestToolResult:
    """Test ToolResult model."""

    def test_tool_result_success(self):
        """Test successful tool result."""
        result = ToolResult(
            success=True,
            data="some data",
            tool_name="test_tool",
            execution_time=1.5,
        )
        assert result.success is True
        assert result.data == "some data"
        assert result.tool_name == "test_tool"
        assert result.execution_time == 1.5

    def test_tool_result_failure(self):
        """Test failed tool result."""
        result = ToolResult(
            success=False,
            error="Something failed",
            error_type="ValueError",
            tool_name="test_tool",
        )
        assert result.success is False
        assert result.error == "Something failed"
        assert result.error_type == "ValueError"

    def test_tool_result_to_dict(self):
        """Test converting to dictionary."""
        result = ToolResult(
            success=True,
            data=42,
            tool_name="calculator",
            execution_time=0.5,
            retries=1,
        )
        data = result.to_dict()
        assert data["success"] is True
        assert data["data"] == 42
        assert data["tool_name"] == "calculator"
        assert data["execution_time"] == 0.5
        assert data["retries"] == 1

    def test_tool_result_to_string_success(self):
        """Test converting successful result to string."""
        result = ToolResult(
            success=True,
            data="Hello World",
            tool_name="greeter",
        )
        assert result.to_string() == "✓ greeter: Hello World"

    def test_tool_result_to_string_failure(self):
        """Test converting failed result to string."""
        result = ToolResult(
            success=False,
            error="Network error",
            tool_name="fetcher",
        )
        assert result.to_string() == "✗ fetcher: Network error"
