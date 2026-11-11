"""Tools for knowledge base retrieval and inspection."""

import os
from typing import Any

from pydantic import validate_call

from openfatture.ai.rag import KnowledgeIndexer, get_rag_config
from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.platform.logging import get_logger
from openfatture.platform.security import sanitize_string_input, validate_integer_input

logger = get_logger(__name__)


@validate_call
async def search_knowledge_base(
    query: str,
    source: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Perform semantic search over the knowledge base.

    The packaged knowledge sources are indexed on first use, so the search never
    runs against an empty collection.

    Args:
        query: Natural language query
        source: Optional source filter (id defined in manifest)
        top_k: Maximum number of results

    Returns:
        Dictionary with formatted results
    """
    query = sanitize_string_input(query, max_length=500)
    if source is not None:
        source = sanitize_string_input(source, max_length=100)
    top_k = validate_integer_input(top_k, min_value=1, max_value=20)

    config = get_rag_config()

    if not config.enabled:
        logger.info("knowledge_tool_rag_disabled")
        return {"results": [], "count": 0, "message": "RAG disabled"}

    api_key = os.getenv("OPENAI_API_KEY")
    if config.embedding_provider == "openai" and not api_key:
        logger.warning("knowledge_tool_missing_api_key")
        return {
            "results": [],
            "count": 0,
            "error": "OPENAI_API_KEY non impostata",
        }

    indexer = await KnowledgeIndexer.create(
        config=config,
        api_key=api_key,
    )

    if indexer.vector_store.count() == 0:
        indexed = await indexer.index_sources()
        logger.info("knowledge_base_indexed_on_first_use", chunks=indexed)

    filters = {"type": "knowledge"}
    if source:
        filters["knowledge_source"] = source

    results = await indexer.vector_store.search(
        query=query,
        top_k=top_k,
        filters=filters,
    )

    formatted = []
    for item in results:
        metadata = item.get("metadata", {}) or {}
        excerpt = (item.get("document") or "").strip().replace("\n", " ")
        formatted.append(
            {
                "source": metadata.get("knowledge_source"),
                "section": metadata.get("section_title"),
                "citation": metadata.get("law_reference")
                or metadata.get("section_title")
                or metadata.get("knowledge_source"),
                "source_path": metadata.get("source_path"),
                "similarity": round(item.get("similarity", 0.0), 4),
                "excerpt": excerpt[:400] + ("…" if len(excerpt) > 400 else ""),
            }
        )

    logger.info(
        "knowledge_tool_search_completed",
        query_length=len(query),
        count=len(formatted),
        source=source,
    )

    return {"count": len(formatted), "results": formatted}


def get_knowledge_tools() -> list[Tool]:
    """Return knowledge-related tools."""
    return [
        Tool(
            name="search_knowledge_base",
            risk=ToolRisk.READ,
            description=(
                "Semantic search over the packaged knowledge base on Italian VAT and "
                "FatturaPA rules (VAT rates, natura codes, reverse charge, split payment, "
                "regime forfettario). Returns count and results, each with source, section, "
                "citation (law reference when available), source_path, similarity (0-1) and "
                "an excerpt of up to 400 characters, best match first. The knowledge base is "
                "indexed on first use, which can take a while. When retrieval is disabled it "
                "returns no results with message 'RAG disabled'; with OpenAI embeddings and "
                "no OPENAI_API_KEY it returns an error. It does not read invoices or clients. "
                "Cite the returned citation when answering a regulatory question."
            ),
            category="knowledge",
            func=search_knowledge_base,
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolParameterType.STRING,
                    description="Question or topic in natural language, Italian or English, up to 500 characters",
                    required=True,
                ),
                ToolParameter(
                    name="source",
                    type=ToolParameterType.STRING,
                    description=(
                        "Restrict to one knowledge source by its manifest ID (currently "
                        "'iva_fatturapa'); an unknown ID returns no results. All sources "
                        "when omitted"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="top_k",
                    type=ToolParameterType.INTEGER,
                    description="Maximum number of excerpts, 1-20 (default 5)",
                    required=False,
                    default=5,
                ),
            ],
            examples=[
                "search_knowledge_base(query='reverse charge edilizia')",
                "search_knowledge_base(query='split payment PA', source='tax_guides')",
            ],
        )
    ]
