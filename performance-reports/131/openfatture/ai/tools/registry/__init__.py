"""Tool registry package — public API for AI function calling.

Import from here (or ``openfatture.ai.tools``):

    from openfatture.ai.tools.registry import ToolRegistry, get_tool_registry
"""

from openfatture.ai.tools.registry.core import ToolRegistry
from openfatture.ai.tools.registry.defaults import get_tool_registry

__all__ = ["ToolRegistry", "get_tool_registry"]
