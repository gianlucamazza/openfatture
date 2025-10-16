"""Regulatory Update Service - High-level orchestration for regulatory updates."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog

from ..ai.providers import BaseLLMProvider
from ..storage.database import SessionLocal
from .agent import RegulatoryUpdateAgent
from .config import WebScraperConfig, get_web_scraper_config
from .extractor import ContentExtractor
from .models import RegulatoryDocument, RegulatorySource, ScrapingSession, UpdateStatus
from .scraper import RegulatoryWebScraper

logger = structlog.get_logger(__name__)


class RegulatoryUpdateService:
    """High-level service for orchestrating regulatory updates.

    This service coordinates the entire regulatory update workflow:
    - Scheduled checking of regulatory sources
    - Content scraping and extraction
    - Change detection and validation
    - Knowledge base updates
    - Notification and reporting

    Features:
    - Configurable scheduling (hourly/daily/weekly)
    - Batch processing with concurrency control
    - Comprehensive error handling and recovery
    - Audit trails and compliance reporting
    - Integration with existing RAG system
    """

    def __init__(
        self,
        config: WebScraperConfig | None = None,
        scraper: RegulatoryWebScraper | None = None,
        extractor: ContentExtractor | None = None,
        agent: RegulatoryUpdateAgent | None = None,
    ):
        """Initialize regulatory update service.

        Args:
            config: Service configuration (uses defaults if None)
            scraper: Web scraper instance (created if None)
            extractor: Content extractor (created if None)
            agent: Update agent (created if None)
        """
        self.config = config or get_web_scraper_config()

        # Initialize components (lazy loading for testability)
        self._scraper = scraper
        self._extractor = extractor
        self._agent = agent
        self._llm_provider: BaseLLMProvider | None = None

        # Scheduling state
        self._last_check_time: datetime | None = None
        self._is_running = False

        logger.info(
            "regulatory_update_service_initialized",
            check_interval_hours=self.config.check_interval_hours,
            require_human_review=self.config.require_human_review,
        )

    @property
    def scraper(self) -> RegulatoryWebScraper:
        """Get or create web scraper instance."""
        if self._scraper is None:
            self._scraper = RegulatoryWebScraper(self.config)
        return self._scraper

    @property
    def extractor(self) -> ContentExtractor:
        """Get or create content extractor instance."""
        if self._extractor is None:
            if self._llm_provider is None:
                raise RuntimeError("LLM provider not set. Call set_llm_provider() first.")
            self._extractor = ContentExtractor(self.config, self._llm_provider)
        return self._extractor

    @property
    def agent(self) -> RegulatoryUpdateAgent:
        """Get or create update agent instance."""
        if self._agent is None:
            if self._llm_provider is None:
                raise RuntimeError("LLM provider not set. Call set_llm_provider() first.")
            self._agent = RegulatoryUpdateAgent(
                self.config, self.scraper, self.extractor, self._llm_provider
            )
        return self._agent

    def set_llm_provider(self, provider: BaseLLMProvider) -> None:
        """Set the LLM provider for AI operations.

        Args:
            provider: Configured LLM provider instance
        """
        self._llm_provider = provider
        # Reset dependent components to use new provider
        self._extractor = None
        self._agent = None

        logger.info("llm_provider_set", provider_type=type(provider).__name__)

    async def check_for_updates(self) -> dict[str, Any]:
        """Check all configured regulatory sources for updates.

        This is the main entry point for regulatory monitoring.
        Performs change detection across all sources and returns summary.

        Returns:
            Summary of update check results
        """
        if self._is_running:
            logger.warning("update_check_already_running")
            return {"status": "already_running"}

        self._is_running = True

        try:
            logger.info("regulatory_update_check_started")

            # Load sources configuration
            sources = self._load_sources_config()
            if not sources:
                logger.warning("no_regulatory_sources_configured")
                return {"status": "no_sources"}

            # Create scraping session for tracking
            session = await self._create_scraping_session(sources)

            results = {
                "session_id": session.session_id,
                "status": "completed",
                "sources_checked": len(sources),
                "documents_processed": 0,
                "changes_detected": 0,
                "errors": 0,
                "source_results": [],
            }

            # Process sources concurrently with controlled parallelism
            semaphore = asyncio.Semaphore(3)  # Max 3 concurrent sources

            async def process_source(source: RegulatorySource) -> dict[str, Any]:
                async with semaphore:
                    return await self._process_source(source, session)

            # Process all sources
            tasks = [process_source(source) for source in sources]
            source_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Aggregate results
            for result in source_results:
                if isinstance(result, Exception):
                    results["errors"] += 1
                    results["source_results"].append({"error": str(result), "status": "failed"})
                elif isinstance(result, dict):
                    results["source_results"].append(result)
                    results["documents_processed"] += result.get("documents_processed", 0)
                    results["changes_detected"] += result.get("changes_detected", 0)
                    if result.get("status") == "error":
                        results["errors"] += 1
                else:
                    # Handle unexpected result types
                    results["errors"] += 1
                    results["source_results"].append(
                        {"error": f"Unexpected result type: {type(result)}", "status": "failed"}
                    )

            # Update session with final results
            await self._complete_scraping_session(session, results)

            # Update last check time
            self._last_check_time = datetime.now(UTC)

            logger.info(
                "regulatory_update_check_completed",
                sources_checked=results["sources_checked"],
                documents_processed=results["documents_processed"],
                changes_detected=results["changes_detected"],
                errors=results["errors"],
            )

            return results

        finally:
            self._is_running = False

    async def _process_source(
        self, source: RegulatorySource, session: ScrapingSession
    ) -> dict[str, Any]:
        """Process a single regulatory source.

        Args:
            source: Source to process
            session: Current scraping session

        Returns:
            Processing results for this source
        """
        logger.info(
            "processing_source", source_id=source.id, url=source.url, session_id=session.session_id
        )

        try:
            # Use agent for orchestrated processing
            agent_results = await self.agent.process_source_updates(source)

            # Extract documents if changes detected
            documents = []
            if agent_results.get("changes_detected", 0) > 0:
                # In a full implementation, we'd get documents from agent results
                # For now, simulate document processing
                documents = await self._extract_documents_from_source(source)

                # Process and validate documents
                if documents:
                    validation_results = await self.agent.validate_regulatory_changes(documents)

                    # Apply approved updates to knowledge base
                    await self._apply_approved_updates(documents, validation_results)

            return {
                "source_id": source.id,
                "status": "completed",
                "documents_processed": len(documents),
                "changes_detected": agent_results.get("changes_detected", 0),
                "agent_results": agent_results,
            }

        except Exception as e:
            logger.error("source_processing_failed", source_id=source.id, error=str(e))
            return {
                "source_id": source.id,
                "status": "error",
                "error": str(e),
                "documents_processed": 0,
                "changes_detected": 0,
            }

    async def _extract_documents_from_source(
        self, source: RegulatorySource
    ) -> list[RegulatoryDocument]:
        """Extract documents from a regulatory source.

        Args:
            source: Source to extract from

        Returns:
            List of extracted documents
        """
        logger.info("extracting_documents_from_source", source_id=source.id)

        try:
            # Use the scraper to extract documents
            async with self.scraper:
                documents = await self.scraper.scrape_source(source)

                # Process documents with extractor if available
                if documents and self._llm_provider:
                    processed_documents = []
                    for doc in documents:
                        try:
                            processed_doc = await self.extractor.extract_content(doc, source)
                            processed_documents.append(processed_doc)
                        except Exception as e:
                            logger.warning(
                                "document_processing_failed", document_id=doc.id, error=str(e)
                            )
                            processed_documents.append(doc)  # Keep original if processing fails
                    documents = processed_documents

                logger.info(
                    "documents_extracted_from_source",
                    source_id=source.id,
                    document_count=len(documents),
                )

                return documents

        except Exception as e:
            logger.error("source_extraction_failed", source_id=source.id, error=str(e))
            return []

    async def _apply_approved_updates(
        self, documents: list[RegulatoryDocument], validation_results: dict[str, Any]
    ) -> None:
        """Apply approved regulatory updates to the knowledge base.

        Args:
            documents: Documents to potentially update
            validation_results: Validation results from agent
        """
        logger.info(
            "applying_approved_updates",
            total_documents=len(documents),
            approved=validation_results.get("approved", 0),
        )

        if SessionLocal is None:
            logger.warning("database_not_initialized_skipping_kb_updates")
            return

        # Get approved documents
        approved_docs = []
        for doc in documents:
            if doc.status == UpdateStatus.APPROVED:
                approved_docs.append(doc)

        if not approved_docs:
            logger.info("no_approved_documents_to_apply")
            return

        try:
            # Import RAG components
            from ..ai.rag.config import get_rag_config
            from ..ai.rag.embeddings import create_embeddings
            from ..ai.rag.vector_store import VectorStore
            from .models import RegulatoryUpdate

            # Initialize vector store
            rag_config = get_rag_config()
            if not rag_config.enabled:
                logger.warning("rag_disabled_skipping_kb_updates")
                return

            # Create embeddings strategy
            embeddings = create_embeddings(rag_config)
            vector_store = VectorStore(rag_config, embeddings)

            # Prepare documents for indexing
            doc_texts = []
            doc_metadatas = []
            doc_ids = []

            for doc in approved_docs:
                # Create comprehensive document text
                full_text = f"""
Titolo: {doc.title}
Fonte: {doc.source_name}
Categoria: {doc.category}
Giurisdizione: {doc.jurisdiction}
Data: {doc.scraped_at.date().isoformat()}

Contenuto:
{doc.content}

Entità estratte:
{doc.extracted_entities or {}}

Valutazione impatto:
{doc.impact_assessment or "Non disponibile"}

Riepilogo:
{doc.summary or "Non disponibile"}
""".strip()

                # Create metadata
                metadata = {
                    "source": "regulatory_scraper",
                    "source_id": doc.source_id,
                    "document_type": "regulatory_update",
                    "category": doc.category,
                    "jurisdiction": doc.jurisdiction,
                    "scraped_at": doc.scraped_at.isoformat(),
                    "tags": doc.tags,
                    "content_hash": doc.content_hash,
                    "change_confidence": doc.change_confidence,
                }

                doc_texts.append(full_text)
                doc_metadatas.append(metadata)
                doc_ids.append(f"regulatory_{doc.id}")

            # Add to knowledge base
            added_ids = await vector_store.add_documents(
                documents=doc_texts, metadatas=doc_metadatas, ids=doc_ids
            )

            # Create RegulatoryUpdate records
            db = SessionLocal()
            try:
                for doc, added_id in zip(approved_docs, added_ids, strict=False):
                    update_record = RegulatoryUpdate(
                        document_id=doc.id,
                        kb_collection=rag_config.collection_name,
                        kb_document_ids=[added_id],
                        update_type="add",
                        change_summary=f"Aggiornamento normativo approvato: {doc.title}",
                        applied_by="regulatory_scraper",
                    )
                    db.add(update_record)

                    # Update document status
                    doc.applied_at = datetime.now(UTC)
                    doc.status = UpdateStatus.APPLIED
                    db.merge(doc)

                db.commit()

                logger.info(
                    "regulatory_updates_applied_to_kb",
                    documents_added=len(added_ids),
                    kb_collection=rag_config.collection_name,
                )

            finally:
                db.close()

        except Exception as e:
            logger.error("failed_to_apply_kb_updates", error=str(e))
            # Mark documents as failed
            db = SessionLocal()
            try:
                for doc in approved_docs:
                    doc.error_message = f"KB update failed: {str(e)}"
                    doc.status = UpdateStatus.FAILED
                    db.merge(doc)
                db.commit()
            finally:
                db.close()

    def should_check_for_updates(self) -> bool:
        """Check if it's time to perform regulatory update check.

        Returns:
            True if update check should be performed
        """
        if self._last_check_time is None:
            return True

        time_since_last_check = datetime.now(UTC) - self._last_check_time
        required_interval = timedelta(hours=self.config.check_interval_hours)

        return time_since_last_check >= required_interval

    def _load_sources_config(self) -> list[RegulatorySource]:
        """Load regulatory sources configuration.

        Returns:
            List of configured regulatory sources
        """
        config_path = self.config.sources_config_path

        if not config_path.exists():
            logger.warning("sources_config_not_found", path=str(config_path))
            return []

        try:
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)

            sources = []
            for source_data in data.get("sources", []):
                source = RegulatorySource(**source_data)
                sources.append(source)

            logger.info("sources_config_loaded", sources_count=len(sources))
            return sources

        except Exception as e:
            logger.error("failed_to_load_sources_config", error=str(e))
            return []

    async def _create_scraping_session(self, sources: list[RegulatorySource]) -> ScrapingSession:
        """Create a new scraping session for tracking.

        Args:
            sources: Sources being processed

        Returns:
            New scraping session
        """
        session = ScrapingSession(
            session_id=f"scrape_{int(datetime.now(UTC).timestamp())}",
            config_snapshot=self.config.model_dump(),
            sources_processed=len(sources),
            documents_scraped=0,
            documents_changed=0,
            errors_count=0,
            started_at=datetime.now(UTC),
        )

        # Save to database
        if SessionLocal is None:
            logger.warning("database_not_initialized_skipping_session_save")
            return session

        db = SessionLocal()
        try:
            db.add(session)
            db.commit()
            db.refresh(session)
        finally:
            db.close()

        logger.info("scraping_session_created", session_id=session.session_id)

        return session

    async def _complete_scraping_session(
        self, session: ScrapingSession, results: dict[str, Any]
    ) -> None:
        """Complete a scraping session with final results.

        Args:
            session: Session to complete
            results: Final results
        """
        session.completed_at = datetime.now(UTC)
        session.results = results

        # Update session statistics
        session.sources_processed = results.get("sources_checked", 0)
        session.documents_scraped = results.get("documents_processed", 0)
        session.documents_changed = results.get("changes_detected", 0)
        session.errors_count = results.get("errors", 0)

        # Update database
        if SessionLocal is None:
            logger.warning("database_not_initialized_skipping_session_update")
            return

        db = SessionLocal()
        try:
            db.merge(session)  # Use merge in case session was modified elsewhere
            db.commit()
        finally:
            db.close()

        logger.info(
            "scraping_session_completed",
            session_id=session.session_id,
            duration=(session.completed_at - session.started_at).total_seconds(),
        )

    async def get_status(self) -> dict[str, Any]:
        """Get current service status and statistics.

        Returns:
            Status information
        """
        return {
            "is_running": self._is_running,
            "last_check_time": self._last_check_time.isoformat() if self._last_check_time else None,
            "check_interval_hours": self.config.check_interval_hours,
            "should_check": self.should_check_for_updates(),
            "config": {
                "enabled": self.config.enabled,
                "require_human_review": self.config.require_human_review,
                "auto_update_threshold": self.config.auto_update_threshold,
            },
        }
