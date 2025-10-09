"""Central registry for AI tools and function calling."""

from typing import Any, Optional

from openfatture.ai.tools.models import Tool, ToolResult
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """
    Central registry for managing AI tools.

    Provides:
    - Tool registration and discovery
    - Schema generation for LLM providers
    - Safe tool execution with validation
    - Category-based filtering
    """

    def __init__(self) -> None:
        """Initialize empty tool registry."""
        self._tools: dict[str, Tool] = {}
        self._categories: dict[str, list[str]] = {}

        logger.info("tool_registry_initialized")

    def register(self, tool: Tool) -> None:
        """
        Register a tool.

        Args:
            tool: Tool to register
        """
        if tool.name in self._tools:
            logger.warning("tool_already_registered", name=tool.name)

        self._tools[tool.name] = tool

        # Add to category index
        if tool.category not in self._categories:
            self._categories[tool.category] = []
        if tool.name not in self._categories[tool.category]:
            self._categories[tool.category].append(tool.name)

        logger.info(
            "tool_registered",
            name=tool.name,
            category=tool.category,
            parameters_count=len(tool.parameters),
        )

    def unregister(self, tool_name: str) -> bool:
        """
        Unregister a tool.

        Args:
            tool_name: Name of tool to remove

        Returns:
            True if removed, False if not found
        """
        if tool_name in self._tools:
            tool = self._tools[tool_name]

            # Remove from category index
            if tool.category in self._categories:
                self._categories[tool.category].remove(tool_name)

            del self._tools[tool_name]
            logger.info("tool_unregistered", name=tool_name)
            return True

        return False

    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool if found, None otherwise
        """
        return self._tools.get(name)

    def list_tools(
        self,
        category: Optional[str] = None,
        enabled_only: bool = True,
    ) -> list[Tool]:
        """
        List all tools.

        Args:
            category: Filter by category
            enabled_only: Only return enabled tools

        Returns:
            List of tools
        """
        tools = list(self._tools.values())

        if category:
            tools = [t for t in tools if t.category == category]

        if enabled_only:
            tools = [t for t in tools if t.enabled]

        return tools

    def get_categories(self) -> list[str]:
        """Get all tool categories."""
        return list(self._categories.keys())

    def get_openai_functions(
        self,
        category: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Get tools in OpenAI function calling format.

        Args:
            category: Filter by category

        Returns:
            List of function schemas for OpenAI API
        """
        tools = self.list_tools(category=category, enabled_only=True)
        return [tool.to_openai_function() for tool in tools]

    def get_anthropic_tools(
        self,
        category: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Get tools in Anthropic tool calling format.

        Args:
            category: Filter by category

        Returns:
            List of tool schemas for Anthropic API
        """
        tools = self.list_tools(category=category, enabled_only=True)
        return [tool.to_anthropic_tool() for tool in tools]

    async def execute_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        confirm: bool = True,
    ) -> ToolResult:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters
            confirm: Skip confirmation if False

        Returns:
            ToolResult with execution outcome
        """
        # Get tool
        tool = self.get_tool(tool_name)

        if not tool:
            logger.error("tool_not_found", name=tool_name)
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found",
                tool_name=tool_name,
            )

        if not tool.enabled:
            logger.error("tool_disabled", name=tool_name)
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' is disabled",
                tool_name=tool_name,
            )

        # Check confirmation requirement
        if tool.requires_confirmation and confirm:
            # In a real implementation, this would ask the user
            # For now, we'll just log it
            logger.info(
                "tool_requires_confirmation",
                name=tool_name,
                parameters=parameters,
            )

        # Execute
        logger.info(
            "tool_executing",
            name=tool_name,
            parameters=parameters,
        )

        result = await tool.execute(**parameters)

        logger.info(
            "tool_executed",
            name=tool_name,
            success=result.success,
            error=result.error if not result.success else None,
        )

        return result

    def get_stats(self) -> dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "total_tools": len(self._tools),
            "enabled_tools": len([t for t in self._tools.values() if t.enabled]),
            "categories": len(self._categories),
            "tools_by_category": {
                cat: len(tools) for cat, tools in self._categories.items()
            },
        }


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.

    Returns:
        Global ToolRegistry
    """
    global _global_registry

    if _global_registry is None:
        _global_registry = ToolRegistry()

        # Register default tools
        _register_default_tools(_global_registry)

    return _global_registry


def _register_default_tools(registry: ToolRegistry) -> None:
    """
    Register default tools on first use.

    Args:
        registry: Registry to populate
    """
    # Import and register tools
    try:
        from openfatture.ai.tools import client_tools, invoice_tools

        # Register invoice tools
        for tool in invoice_tools.get_invoice_tools():
            registry.register(tool)

        # Register client tools
        for tool in client_tools.get_client_tools():
            registry.register(tool)

        logger.info("default_tools_registered")

    except ImportError as e:
        logger.warning(
            "could_not_register_default_tools",
            error=str(e),
            message="Tools will be registered on demand",
        )
