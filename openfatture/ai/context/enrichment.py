"""Context enrichment utilities for AI agents."""

from datetime import datetime
from typing import Any, cast

from openfatture.ai.domain.context import AgentContext, ChatContext
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Cliente, Fattura, StatoFattura
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class ContextManager:
    """
    Manages context enrichment for AI agents.
    
    Handles:
    - Business data injection (stats, recent items)
    - RAG enrichment (documents, knowledge)
    - Error handling and graceful degradation
    """

    def __init__(self) -> None:
        """Initialize context manager."""
        self._db_warning_shown = False

    async def enrich_context(self, context: ChatContext) -> ChatContext:
        """
        Enrich chat context with relevant business data.

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
            context.current_year_stats = self._get_current_year_stats()

            # Add recent invoices summary
            context.recent_invoices_summary = self._get_recent_invoices_summary()

            # Add recent clients summary
            context.recent_clients_summary = self._get_recent_clients_summary()

            logger.info(
                "chat_context_enriched",
                session_id=getattr(context, "session_id", None),
                has_stats=context.current_year_stats is not None,
            )

        except Exception as e:
            self._handle_enrichment_error(e)

        return context

    async def enrich_with_rag(self, context: AgentContext, query: str) -> AgentContext:
        """
        Enrich context with RAG (Retrieval-Augmented Generation).

        Args:
            context: Chat context to enrich
            query: User query for similarity search

        Returns:
            Enriched context with relevant documents
        """
        try:
            from openfatture.ai.config.settings import get_ai_settings
            from openfatture.ai.rag import KnowledgeIndexer, RAGSystem
            from openfatture.ai.rag.config import get_rag_config

            # Check if RAG is enabled
            config = get_rag_config()
            if not config.enabled:
                logger.debug("rag_enrichment_disabled")
                return context

            # Get API key for embeddings
            api_key = self._get_embedding_api_key(config)
            if config.embedding_provider == "openai" and not api_key:
                return context

            # Reset previous RAG fields
            context.relevant_documents = []
            context.knowledge_snippets = []

            # --- Invoice retrieval ---
            await self._enrich_invoices(context, query, config, api_key)

            # --- Knowledge base retrieval ---
            await self._enrich_knowledge(context, query, config, api_key)

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

    def _get_embedding_api_key(self, config: Any) -> str | None:
        """Get API key for embeddings if needed."""
        if config.embedding_provider == "openai":
            from openfatture.ai.config.settings import get_ai_settings
            ai_settings = get_ai_settings()
            if ai_settings.openai_api_key:
                return ai_settings.openai_api_key.get_secret_value()
            
            logger.warning(
                "openai_api_key_missing_for_rag",
                message="RAG enabled but OPENAI_API_KEY missing.",
                current_provider=config.embedding_provider,
            )
            return None
        return None

    async def _enrich_invoices(
        self, 
        context: AgentContext, 
        query: str, 
        config: Any, 
        api_key: str | None
    ) -> None:
        """Enrich context with invoice data."""
        from openfatture.ai.rag import RAGSystem
        
        rag = await RAGSystem.create(config, api_key=api_key)
        invoice_results = await rag.search(
            query=query,
            top_k=config.top_k,
            min_similarity=config.similarity_threshold,
        )

        if invoice_results:
            context.relevant_documents = [
                self._format_invoice_result(result) for result in invoice_results
            ]
            logger.info(
                "rag_invoices_enriched",
                results_count=len(invoice_results),
            )

    async def _enrich_knowledge(
        self, 
        context: AgentContext, 
        query: str, 
        config: Any, 
        api_key: str | None
    ) -> None:
        """Enrich context with knowledge base data."""
        from openfatture.ai.rag import KnowledgeIndexer
        
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
                    self._format_knowledge_result(result) for result in knowledge_results
                ][: config.top_k]
                logger.info(
                    "rag_knowledge_enriched",
                    results_count=len(context.knowledge_snippets),
                )
        except FileNotFoundError:
            logger.warning(
                "knowledge_manifest_missing",
                manifest=str(config.knowledge_manifest_path),
            )

    def _handle_enrichment_error(self, error: Exception) -> None:
        """Handle context enrichment errors."""
        error_str = str(error)
        is_db_init_error = "Database not initialized" in error_str

        if is_db_init_error and not self._db_warning_shown:
            logger.warning(
                "context_enrichment_db_not_initialized",
                message="Database not initialized. Context enrichment disabled until DB is ready.",
            )
            self._db_warning_shown = True
        elif not is_db_init_error:
            logger.warning(
                "context_enrichment_failed",
                error=error_str,
                message="Continuing with unenriched context",
            )

    def _get_current_year_stats(self) -> dict[str, Any]:
        """Get statistics for current year."""
        db = get_session()
        try:
            current_year = datetime.now().year
            stats: dict[str, Any] = {
                "anno": current_year,
                "totale_fatture": 0,
                "per_stato": {},
                "importo_totale": 0.0,
            }

            for stato in StatoFattura:
                count = (
                    db.query(Fattura)
                    .filter(Fattura.anno == current_year, Fattura.stato == stato)
                    .count()
                )
                stats["per_stato"][stato.value] = count
                stats["totale_fatture"] += count

            fatture = db.query(Fattura).filter(Fattura.anno == current_year).all()
            stats["importo_totale"] = float(sum(f.totale for f in fatture))

            return stats
        except Exception as e:
            logger.error("get_current_year_stats_failed", error=str(e))
            return {}
        finally:
            db.close()

    def _get_recent_invoices_summary(self, limit: int = 5) -> str:
        """Get summary of recent invoices."""
        db = get_session()
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

    def _get_recent_clients_summary(self, limit: int = 5) -> str:
        """Get summary of recent clients."""
        db = get_session()
        try:
            clienti = db.query(Cliente).limit(limit).all()
            if not clienti:
                return "Nessun cliente trovato"

            lines = [f"Ultimi {len(clienti)} clienti:"]
            for c in clienti:
                fatture_count = len(c.fatture)
                lines.append(
                    f"- {c.denominazione} ({c.partita_iva or 'N/A'}): {fatture_count} fatture"
                )
            return "\n".join(lines)
        except Exception as e:
            logger.error("get_recent_clients_summary_failed", error=str(e))
            return "Errore nel recupero dei clienti recenti"
        finally:
            db.close()

    @staticmethod
    def _format_invoice_result(result: Any) -> str:
        """Create human-readable summary for invoice retrieval result."""
        client_name = result.client_name or "Cliente sconosciuto"
        snippet = result.document.replace("\n", " ")[:200]
        return f"{client_name} — {snippet}..."

    @staticmethod
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


# Global instance for backward compatibility if needed, 
# though dependency injection is preferred.
default_context_manager = ContextManager()

# Backward compatibility functions
async def enrich_chat_context(context: ChatContext) -> ChatContext:
    return await default_context_manager.enrich_context(context)

async def enrich_with_rag(context: AgentContext, query: str) -> AgentContext:
    return await default_context_manager.enrich_with_rag(context, query)
