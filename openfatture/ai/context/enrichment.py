"""Context enrichment utilities for AI agents."""

from datetime import datetime

from openfatture.ai.domain.context import AgentContext, ChatContext
from openfatture.storage.database.base import SessionLocal
from openfatture.storage.database.models import Cliente, Fattura, StatoFattura
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


def enrich_chat_context(context: ChatContext) -> ChatContext:
    """
    Enrich chat context with relevant business data.

    Adds:
    - Current year statistics
    - Recent invoices summary
    - Recent clients summary
    - Available tools list

    Args:
        context: Chat context to enrich

    Returns:
        Enriched context
    """
    try:
        logger.debug(
            "enriching_chat_context",
            session_id=getattr(context, "session_id", None),
        )

        # Add current year stats
        context.current_year_stats = _get_current_year_stats()

        # Add recent invoices summary
        context.recent_invoices_summary = _get_recent_invoices_summary()

        # Add recent clients summary
        context.recent_clients_summary = _get_recent_clients_summary()

        # Add available tools (will be set by agent)
        # context.available_tools = []  # Set by ChatAgent

        logger.info(
            "chat_context_enriched",
            session_id=getattr(context, "session_id", None),
            has_stats=context.current_year_stats is not None,
        )

    except Exception as e:
        logger.warning(
            "context_enrichment_failed",
            error=str(e),
            message="Continuing with unenriched context",
        )

    return context


def _get_current_year_stats() -> dict:
    """
    Get statistics for current year.

    Returns:
        Dictionary with year stats
    """
    db = SessionLocal()
    try:
        current_year = datetime.now().year

        stats = {
            "anno": current_year,
            "totale_fatture": 0,
            "per_stato": {},
            "importo_totale": 0.0,
        }

        # Count by status
        for stato in StatoFattura:
            count = (
                db.query(Fattura)
                .filter(Fattura.anno == current_year, Fattura.stato == stato)
                .count()
            )
            stats["per_stato"][stato.value] = count
            stats["totale_fatture"] += count

        # Total amount
        fatture = db.query(Fattura).filter(Fattura.anno == current_year).all()
        stats["importo_totale"] = float(sum(f.totale for f in fatture))

        return stats

    except Exception as e:
        logger.error("get_current_year_stats_failed", error=str(e))
        return {}

    finally:
        db.close()


def _get_recent_invoices_summary(limit: int = 5) -> str:
    """
    Get summary of recent invoices.

    Args:
        limit: Number of invoices to include

    Returns:
        Formatted summary string
    """
    db = SessionLocal()
    try:
        fatture = db.query(Fattura).order_by(Fattura.data_emissione.desc()).limit(limit).all()

        if not fatture:
            return "Nessuna fattura trovata"

        lines = [f"Ultime {len(fatture)} fatture:"]
        for f in fatture:
            lines.append(
                f"- {f.numero}/{f.anno}: {f.cliente.denominazione} - "
                f"€{f.totale:.2f} ({f.stato.value})"
            )

        return "\n".join(lines)

    except Exception as e:
        logger.error("get_recent_invoices_summary_failed", error=str(e))
        return "Errore nel recupero delle fatture recenti"

    finally:
        db.close()


def _get_recent_clients_summary(limit: int = 5) -> str:
    """
    Get summary of recent clients.

    Args:
        limit: Number of clients to include

    Returns:
        Formatted summary string
    """
    db = SessionLocal()
    try:
        # Get clients with most recent invoices
        clienti = db.query(Cliente).limit(limit).all()

        if not clienti:
            return "Nessun cliente trovato"

        lines = [f"Ultimi {len(clienti)} clienti:"]
        for c in clienti:
            fatture_count = len(c.fatture)
            lines.append(
                f"- {c.denominazione} ({c.partita_iva or 'N/A'}): " f"{fatture_count} fatture"
            )

        return "\n".join(lines)

    except Exception as e:
        logger.error("get_recent_clients_summary_failed", error=str(e))
        return "Errore nel recupero dei clienti recenti"

    finally:
        db.close()


async def enrich_with_rag(context: AgentContext, query: str) -> AgentContext:
    """
    Enrich context with RAG (Retrieval-Augmented Generation).

    Uses semantic search to find relevant invoices and historical data
    to provide better context for the AI assistant.

    Args:
        context: Chat context to enrich
        query: User query for similarity search

    Returns:
        Enriched context with relevant documents
    """
    try:
        import os

        from openfatture.ai.rag import KnowledgeIndexer, RAGSystem
        from openfatture.ai.rag.config import get_rag_config

        # Check if RAG is enabled
        config = get_rag_config()
        if not config.enabled:
            logger.debug("rag_enrichment_disabled")
            return context

        # Get API key for embeddings
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key and config.embedding_provider == "openai":
            logger.warning("openai_api_key_missing_for_rag")
            return context

        # Reset previous RAG fields
        context.relevant_documents = []
        context.knowledge_snippets = []

        # --- Invoice retrieval -------------------------------------------------
        rag = await RAGSystem.create(config, api_key=api_key)

        invoice_results = await rag.search(
            query=query,
            top_k=config.top_k,
            min_similarity=config.similarity_threshold,
        )

        if invoice_results:
            context.relevant_documents = [
                _format_invoice_result(result) for result in invoice_results
            ]

            logger.info(
                "rag_invoices_enriched",
                results_count=len(invoice_results),
                query_length=len(query),
            )
        else:
            logger.debug("rag_no_invoice_results", query=query[:50])

        # --- Knowledge base retrieval -----------------------------------------
        try:
            knowledge_indexer = await KnowledgeIndexer.create(
                config=config,
                api_key=api_key,
            )

            knowledge_results = await knowledge_indexer.vector_store.search(
                query=query,
                top_k=config.top_k,
                filters={"type": "knowledge"},
            )

            if knowledge_results:
                context.knowledge_snippets = [
                    _format_knowledge_result(result) for result in knowledge_results
                ][: config.top_k]

                logger.info(
                    "rag_knowledge_enriched",
                    results_count=len(context.knowledge_snippets),
                    query_length=len(query),
                )
            else:
                logger.debug("rag_no_knowledge_results", query=query[:50])

        except FileNotFoundError:
            logger.warning(
                "knowledge_manifest_missing",
                manifest=str(config.knowledge_manifest_path),
            )

    except ImportError as e:
        logger.warning(
            "rag_import_failed",
            error=str(e),
            message="RAG system not available",
        )

    except Exception as e:
        logger.warning(
            "rag_enrichment_failed",
            error=str(e),
            message="Continuing without RAG enrichment",
        )

    return context


def _format_invoice_result(result) -> str:
    """Create human-readable summary for invoice retrieval result."""
    client_name = result.client_name or "Cliente sconosciuto"
    snippet = result.document.replace("\n", " ")[:200]
    return f"{client_name} — {snippet}..."


def _format_knowledge_result(result: dict) -> dict[str, str | float | None]:
    """Normalize knowledge result with citation metadata."""
    metadata = result.get("metadata", {}) or {}
    snippet = (result.get("document") or "").strip().replace("\n", " ")
    excerpt = snippet[:200] + ("…" if len(snippet) > 200 else "")

    citation = (
        metadata.get("law_reference")
        or metadata.get("section_title")
        or metadata.get("knowledge_source")
    )

    return {
        "source": metadata.get("knowledge_source", "unknown"),
        "section": metadata.get("section_title", "N/A"),
        "citation": citation,
        "excerpt": excerpt,
        "similarity": round(result.get("similarity", 0.0), 4),
        "source_path": metadata.get("source_path"),
    }
