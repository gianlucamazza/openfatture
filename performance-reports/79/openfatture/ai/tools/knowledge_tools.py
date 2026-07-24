"""Tools for knowledge base retrieval and inspection."""

import os
from typing import Any

from pydantic import validate_call

from openfatture.ai.rag import KnowledgeIndexer, get_rag_config
from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.utils.logging import get_logger
from openfatture.utils.security import sanitize_string_input, validate_integer_input

logger = get_logger(__name__)


@validate_call
async def search_knowledge_base(
    query: str,
    source: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    # Sanitize and validate inputs
    query = sanitize_string_input(query, max_length=500)

    if source is not None:
        source = sanitize_string_input(source, max_length=100)

    top_k = validate_integer_input(top_k, min_value=1, max_value=20)
    """
    Perform semantic search over the knowledge base.

    Args:
        query: Natural language query
        source: Optional source filter (id defined in manifest)
        top_k: Maximum number of results

    Returns:
        Dictionary with formatted results
    """
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
            description="Esegue una ricerca semantica nella knowledge base normativa e operativa",
            category="knowledge",
            func=search_knowledge_base,
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolParameterType.STRING,
                    description="Domanda o tema da cercare",
                    required=True,
                ),
                ToolParameter(
                    name="source",
                    type=ToolParameterType.STRING,
                    description="Filtra per ID sorgente definito nel manifest (opzionale)",
                    required=False,
                ),
                ToolParameter(
                    name="top_k",
                    type=ToolParameterType.INTEGER,
                    description="Numero massimo di risultati (default 5)",
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
