"""Default tool registration and global registry factory."""

from __future__ import annotations

from openfatture.ai.tools.registry.core import ToolRegistry
from openfatture.platform.logging import get_logger

logger = get_logger(__name__)

# Global registry instance
_global_registry: ToolRegistry | None = None


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
        from openfatture.ai.tools import (
            batch_tools,
            client_tools,
            invoice_tools,
            knowledge_tools,
            payment_tools,
            pdf_tools,
            preventivo_tools,
            prodotto_tools,
            report_tools,
            sdi_tools,
            signature_tools,
        )

        # Register invoice tools
        for tool in invoice_tools.get_invoice_tools():
            registry.register(tool)

        # Register client tools
        for tool in client_tools.get_client_tools():
            registry.register(tool)

        # Register knowledge tools
        for tool in knowledge_tools.get_knowledge_tools():
            registry.register(tool)

        # Register payment tools
        for tool in payment_tools.get_payment_tools():
            registry.register(tool)

        # Register report tools
        for tool in report_tools.get_report_tools():
            registry.register(tool)

        # Register batch tools
        for tool in batch_tools.get_batch_tools():
            registry.register(tool)

        # Register preventivo tools
        for tool in preventivo_tools.get_preventivo_tools():
            registry.register(tool)

        # Register prodotto tools (Phase 6 - TIER 1)
        for tool in prodotto_tools.get_prodotto_tools():
            registry.register(tool)

        # Register PDF tools (Phase 6 - TIER 1)
        for tool in pdf_tools.get_pdf_tools():
            registry.register(tool)

        # Register SDI tools (Phase 6 - TIER 1)
        for tool in sdi_tools.get_sdi_tools():
            registry.register(tool)

        # Register signature tools (Phase 6 - TIER 1)
        for tool in signature_tools.get_signature_tools():
            registry.register(tool)

        logger.info("default_tools_registered")

    except ImportError as e:
        logger.warning(
            "could_not_register_default_tools",
            error=str(e),
            message="Tools will be registered on demand",
        )
