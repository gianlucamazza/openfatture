"""Auto-Indexing Service for RAG Updates.

Orchestrates automatic reindexing when invoice/client data changes.
Integrates ChangeTracker, ReindexQueue, and InvoiceIndexer.

Example:
    >>> from openfatture.ai.rag.auto_update import get_auto_indexing_service
    >>> service = get_auto_indexing_service()
    >>> await service.start()
    >>>
    >>> # Service automatically reindexes on data changes
    >>> # Check status
    >>> status = service.get_status()
    >>>
    >>> await service.stop()
"""

from typing import Any

from openfatture.ai.rag.auto_update.config import get_auto_update_config
from openfatture.ai.rag.auto_update.queue import ReindexQueue
from openfatture.ai.rag.auto_update.tracker import ChangeType, EntityChange, get_change_tracker
from openfatture.ai.rag.indexing import InvoiceIndexer
from openfatture.ai.rag.vector_store import VectorStore
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class AutoIndexingService:
    """Auto-indexing service for RAG system.

    Orchestrates automatic reindexing when data changes.
    Integrates all auto-update components:
    - ChangeTracker: Tracks entity changes
    - ReindexQueue: Batches and processes changes
    - InvoiceIndexer: Performs actual indexing

    Example:
        >>> service = AutoIndexingService(vector_store)
        >>> await service.start()
        >>> # Service runs in background
        >>> await service.stop()
    """

    def __init__(self, vector_store: VectorStore | None = None):
        """Initialize auto-indexing service.

        Args:
            vector_store: VectorStore instance (optional, creates if None)
        """
        self.config = get_auto_update_config()
        self.tracker = get_change_tracker()

        # Create or use provided vector store
        if vector_store is None:
            from openfatture.ai.rag.config import get_rag_config
            from openfatture.ai.rag.embeddings import create_embeddings

            rag_config = get_rag_config()
            embedding_strategy = create_embeddings(rag_config)
            vector_store = VectorStore(
                config=rag_config,
                embedding_strategy=embedding_strategy,
            )

        self.vector_store = vector_store
        self.invoice_indexer = InvoiceIndexer(vector_store)

        # Create queue with callback
        self.queue = ReindexQueue(reindex_callback=self._reindex_callback)

        logger.info("auto_indexing_service_initialized", enabled=self.config.enabled)

    async def start(self) -> None:
        """Start the auto-indexing service."""
        if not self.config.enabled:
            logger.warning(
                "auto_indexing_disabled",
                message="Set OPENFATTURE_RAG_AUTO_UPDATE_ENABLED=true to enable",
            )
            return

        # Start the processing queue
        await self.queue.start()

        logger.info("auto_indexing_service_started")

    async def stop(self) -> None:
        """Stop the auto-indexing service."""
        # Stop the queue
        await self.queue.stop()

        logger.info("auto_indexing_service_stopped")

    async def _reindex_callback(self, changes: list[EntityChange]) -> None:
        """Callback for reindex queue to process changes.

        Args:
            changes: List of entity changes to process
        """
        for change in changes:
            try:
                if change.entity_type == "invoice":
                    await self._process_invoice_change(change)
                elif change.entity_type == "client":
                    await self._process_client_change(change)
                else:
                    logger.warning(
                        "unsupported_entity_type",
                        entity_type=change.entity_type,
                    )

            except Exception as e:
                logger.error(
                    "change_processing_failed",
                    entity_type=change.entity_type,
                    entity_id=change.entity_id,
                    change_type=change.change_type.value,
                    error=str(e),
                    exc_info=True,
                )
                # Continue processing other changes

    async def _process_invoice_change(self, change: EntityChange) -> None:
        """Process invoice change.

        Args:
            change: Invoice change to process
        """
        if change.change_type == ChangeType.DELETE:
            # Delete from vector store
            await self.invoice_indexer.delete_invoice(change.entity_id)
            logger.info("invoice_removed_from_index", invoice_id=change.entity_id)

        else:  # CREATE or UPDATE
            # Index/reindex invoice
            doc_id = await self.invoice_indexer.index_invoice(change.entity_id)
            logger.info(
                "invoice_indexed",
                invoice_id=change.entity_id,
                change_type=change.change_type.value,
                doc_id=doc_id,
            )

    async def _process_client_change(self, change: EntityChange) -> None:
        """Process client change.

        When a client changes, we need to reindex all their invoices
        since client info is embedded in invoice documents.

        Args:
            change: Client change to process
        """
        from openfatture.storage.database.base import SessionLocal
        from openfatture.storage.database.models import Fattura

        if change.change_type == ChangeType.DELETE:
            # Client deleted - their invoices should already be deleted
            # (cascading delete or handled separately)
            logger.info("client_deleted", client_id=change.entity_id)
            return

        # Check if database is initialized
        if SessionLocal is None:
            logger.warning("database_not_initialized_skipping_client_reindex")
            return

        # For CREATE/UPDATE, reindex all client's invoices
        db = SessionLocal()
        try:
            # Get all invoices for this client
            invoices = db.query(Fattura).filter(Fattura.cliente_id == change.entity_id).all()

            if not invoices:
                logger.debug("no_invoices_for_client", client_id=change.entity_id)
                return

            # Reindex each invoice
            for invoice in invoices:
                try:
                    await self.invoice_indexer.index_invoice(invoice.id)
                except Exception as e:
                    logger.error(
                        "client_invoice_reindex_failed",
                        client_id=change.entity_id,
                        invoice_id=invoice.id,
                        error=str(e),
                    )

            logger.info(
                "client_invoices_reindexed",
                client_id=change.entity_id,
                invoice_count=len(invoices),
            )

        finally:
            db.close()

    def get_status(self) -> dict[str, Any]:
        """Get service status.

        Returns:
            Dictionary with service status
        """
        # Safe check for queue running status
        queue_running = False
        if self.queue and hasattr(self.queue, "_running"):
            queue_running = bool(self.queue._running)

        return {
            "enabled": self.config.enabled,
            "running": queue_running,
            "queue_stats": self.queue.get_stats() if self.queue else {},
            "tracker_stats": self.tracker.get_queue_stats(),
            "config": {
                "batch_size": self.config.batch_size,
                "debounce_seconds": self.config.debounce_seconds,
                "incremental_updates": self.config.incremental_updates,
                "tracked_entities": self.config.get_tracked_entities(),
            },
        }

    async def manual_reindex(
        self,
        entity_type: str,
        entity_ids: list[int],
    ) -> dict[str, Any]:
        """Manually trigger reindexing for specific entities.

        Args:
            entity_type: Type of entity (invoice, client)
            entity_ids: List of entity IDs to reindex

        Returns:
            Dictionary with reindex results
        """
        # Explicit type annotations for mypy
        successful: list[int] = []
        failed: list[dict[str, Any]] = []

        results: dict[str, Any] = {
            "entity_type": entity_type,
            "requested_count": len(entity_ids),
            "successful": successful,
            "failed": failed,
        }

        for entity_id in entity_ids:
            try:
                if entity_type == "invoice":
                    await self.invoice_indexer.index_invoice(entity_id)
                elif entity_type == "client":
                    # Create change for queue processing
                    change = EntityChange(
                        entity_type="client",
                        entity_id=entity_id,
                        change_type=ChangeType.UPDATE,
                        timestamp=__import__("datetime").datetime.now(__import__("datetime").UTC),
                    )
                    await self._process_client_change(change)
                else:
                    raise ValueError(f"Unsupported entity type: {entity_type}")

                successful.append(entity_id)

            except Exception as e:
                logger.error(
                    "manual_reindex_failed",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    error=str(e),
                )
                failed.append({"entity_id": entity_id, "error": str(e)})

        # Update final counts in results dict
        results["successful"] = successful
        results["failed"] = failed

        logger.info(
            "manual_reindex_completed",
            entity_type=entity_type,
            successful=len(successful),
            failed=len(failed),
        )

        return results


# Global service instance (singleton pattern)
_service: AutoIndexingService | None = None


def get_auto_indexing_service() -> AutoIndexingService:
    """Get or create global auto-indexing service instance.

    Returns:
        AutoIndexingService singleton
    """
    global _service

    if _service is None:
        _service = AutoIndexingService()

    return _service
