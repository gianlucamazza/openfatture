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
        _global_registry = ToolRegistry(apply_ai_settings=True)

        # Register default tools
        _register_default_tools(_global_registry)

    return _global_registry


def _register_default_tools(registry: ToolRegistry) -> None:
    """Register every built-in tool module.

    Import errors propagate: a broken tool module must fail loudly instead of
    starting the assistant with a partial or empty tool set. Optional extras
    (RAG) are loaded lazily inside the tools themselves.
    """
    from openfatture.ai.tools import (
        batch_tools,
        client_tools,
        collection_tools,
        document_tools,
        invoice_tools,
        knowledge_tools,
        memory_tools,
        payment_tools,
        pdf_tools,
        preventivo_tools,
        prodotto_tools,
        report_tools,
        sdi_tools,
        signature_tools,
        vat_tools,
    )

    providers = (
        invoice_tools.get_invoice_tools,
        client_tools.get_client_tools,
        knowledge_tools.get_knowledge_tools,
        collection_tools.get_collection_tools,
        payment_tools.get_payment_tools,
        report_tools.get_report_tools,
        batch_tools.get_batch_tools,
        preventivo_tools.get_preventivo_tools,
        prodotto_tools.get_prodotto_tools,
        pdf_tools.get_pdf_tools,
        document_tools.get_document_tools,
        memory_tools.get_memory_tools,
        sdi_tools.get_sdi_tools,
        signature_tools.get_signature_tools,
        vat_tools.get_vat_tools,
    )
    for provider in providers:
        for tool in provider():
            registry.register(tool)

    logger.info("default_tools_registered", count=len(registry.list_tools(enabled_only=False)))
