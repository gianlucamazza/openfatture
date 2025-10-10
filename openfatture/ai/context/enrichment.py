"""Context enrichment utilities for AI agents."""

from datetime import datetime

from openfatture.ai.domain.context import ChatContext
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
        logger.debug("enriching_chat_context", session_id=context.session_id)

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
            session_id=context.session_id,
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
        fatture = (
            db.query(Fattura)
            .order_by(Fattura.data_emissione.desc())
            .limit(limit)
            .all()
        )

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
                f"- {c.denominazione} ({c.partita_iva or 'N/A'}): "
                f"{fatture_count} fatture"
            )

        return "\n".join(lines)

    except Exception as e:
        logger.error("get_recent_clients_summary_failed", error=str(e))
        return "Errore nel recupero dei clienti recenti"

    finally:
        db.close()


async def enrich_with_rag(context: ChatContext, query: str) -> ChatContext:
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
        from openfatture.ai.rag import RAGSystem
        from openfatture.ai.rag.config import get_rag_config
        import os

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

        # Initialize RAG system
        rag = await RAGSystem.create(config, api_key=api_key)

        # Search for relevant invoices
        results = await rag.search(
            query=query,
            top_k=config.top_k,
            min_similarity=config.similarity_threshold,
        )

        # Add to context
        if results:
            context.relevant_documents = [
                f"{r.client_name} - {r.document[:200]}..." for r in results
            ]

            logger.info(
                "rag_enrichment_completed",
                results_count=len(results),
                query_length=len(query),
            )
        else:
            logger.debug("no_rag_results_found", query=query[:50])

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
