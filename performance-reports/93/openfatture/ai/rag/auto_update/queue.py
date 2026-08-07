"""Async Reindex Queue for Batch Processing.

Manages asynchronous reindexing operations with debouncing and batching.
Processes changes in background without blocking main application.

Example:
    >>> from openfatture.ai.rag.auto_update import ReindexQueue
    >>> queue = ReindexQueue()
    >>> await queue.start()
    >>>
    >>> # Queue gets populated by ChangeTracker
    >>> # Processing happens automatically in background
    >>>
    >>> await queue.stop()
"""

import asyncio
from collections.abc import Callable
from typing import Any

from openfatture.ai.rag.auto_update.config import get_auto_update_config
from openfatture.ai.rag.auto_update.tracker import ChangeType, EntityChange, get_change_tracker
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class ReindexQueue:
    """Async queue for batch reindexing operations.

    Features:
    - Debouncing: Waits for changes to settle before processing
    - Batching: Processes multiple changes in single operation
    - Concurrency control: Limits concurrent reindex operations
    - Background processing: Runs in asyncio task

    Example:
        >>> queue = ReindexQueue()
        >>> await queue.start()
        >>> # Queue processes changes automatically
        >>> stats = queue.get_stats()
        >>> await queue.stop()
    """

    def __init__(self, reindex_callback: Callable[[list[EntityChange]], Any] | None = None):
        """Initialize reindex queue.

        Args:
            reindex_callback: Async function to call with batch of changes
        """
        self.config = get_auto_update_config()
        self.tracker = get_change_tracker()
        self.reindex_callback = reindex_callback

        # Processing state
        self._running = False
        self._task: asyncio.Task | None = None
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_updates)

        # Metrics
        self._total_processed = 0
        self._total_batches = 0
        self._last_process_time: float | None = None

        logger.info(
            "reindex_queue_initialized",
            batch_size=self.config.batch_size,
            debounce_seconds=self.config.debounce_seconds,
        )

    async def start(self) -> None:
        """Start the background processing task."""
        if not self.config.enabled:
            logger.warning(
                "reindex_queue_disabled",
                message="Set OPENFATTURE_RAG_AUTO_UPDATE_ENABLED=true to enable",
            )
            return

        if self._running:
            logger.warning("reindex_queue_already_running")
            return

        self._running = True
        self._task = asyncio.create_task(self._processing_loop())

        logger.info("reindex_queue_started")

    async def stop(self) -> None:
        """Stop the background processing task."""
        if not self._running:
            logger.warning("reindex_queue_not_running")
            return

        self._running = False

        # Wait for task to complete
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=30.0)
            except TimeoutError:
                logger.warning("reindex_queue_stop_timeout")
                self._task.cancel()

        # Persist queue on shutdown
        if self.config.persist_queue_on_shutdown:
            self.tracker.persist_to_disk()

        logger.info("reindex_queue_stopped")

    async def _processing_loop(self) -> None:
        """Main processing loop that runs in background."""
        logger.info("reindex_queue_processing_loop_started")

        while self._running:
            try:
                # Wait for debounce period
                await asyncio.sleep(self.config.debounce_seconds)

                # Get pending changes
                changes = self.tracker.get_pending_changes(batch_size=self.config.batch_size)

                if not changes:
                    # No changes to process
                    continue

                # Process batch
                await self._process_batch(changes)

            except Exception as e:
                logger.error(
                    "reindex_queue_processing_error",
                    error=str(e),
                    exc_info=True,
                )
                # Continue processing despite errors
                await asyncio.sleep(5)  # Brief pause before retry

        logger.info("reindex_queue_processing_loop_stopped")

    async def _process_batch(self, changes: list[EntityChange]) -> None:
        """Process a batch of changes.

        Args:
            changes: List of entity changes to process
        """
        if not changes:
            return

        # Acquire semaphore to limit concurrency
        async with self._semaphore:
            logger.info(
                "reindex_batch_processing_started",
                count=len(changes),
                batch_number=self._total_batches + 1,
            )

            try:
                import time

                start_time = time.time()

                # Group changes by entity type for efficient processing
                changes_by_type: dict[str, list[EntityChange]] = {}
                for change in changes:
                    if change.entity_type not in changes_by_type:
                        changes_by_type[change.entity_type] = []
                    changes_by_type[change.entity_type].append(change)

                # Process each entity type
                for entity_type, type_changes in changes_by_type.items():
                    await self._process_entity_type(entity_type, type_changes)

                # Update metrics
                self._total_processed += len(changes)
                self._total_batches += 1
                self._last_process_time = time.time() - start_time

                logger.info(
                    "reindex_batch_completed",
                    count=len(changes),
                    duration_ms=self._last_process_time * 1000,
                    total_processed=self._total_processed,
                )

            except Exception as e:
                logger.error(
                    "reindex_batch_failed",
                    count=len(changes),
                    error=str(e),
                    exc_info=True,
                )
                # Don't mark as processed on error - will retry later
                raise

    async def _process_entity_type(self, entity_type: str, changes: list[EntityChange]) -> None:
        """Process changes for a specific entity type.

        Args:
            entity_type: Type of entity (invoice, client, product)
            changes: Changes for this entity type
        """
        # Separate by change type
        creates = [c for c in changes if c.change_type == ChangeType.CREATE]
        updates = [c for c in changes if c.change_type == ChangeType.UPDATE]
        deletes = [c for c in changes if c.change_type == ChangeType.DELETE]

        # Call reindex callback if provided
        if self.reindex_callback:
            try:
                await self.reindex_callback(changes)
            except Exception as e:
                logger.error(
                    "reindex_callback_failed",
                    entity_type=entity_type,
                    error=str(e),
                )
                raise

        # Process creates/updates (add/update in vector store)
        if creates or updates:
            entity_ids = [c.entity_id for c in creates + updates]
            logger.debug(
                "reindexing_entities",
                entity_type=entity_type,
                operation="upsert",
                count=len(entity_ids),
                ids=entity_ids[:10],  # Log first 10 IDs
            )

            # TODO: Call actual reindexing service
            # This will be implemented in auto_indexing_service.py
            # For now, just simulate
            await asyncio.sleep(0.1)  # Simulate processing time

        # Process deletes (remove from vector store)
        if deletes and self.config.delete_on_removal:
            entity_ids = [c.entity_id for c in deletes]
            logger.debug(
                "removing_from_vector_store",
                entity_type=entity_type,
                count=len(entity_ids),
                ids=entity_ids[:10],
            )

            # TODO: Call actual deletion service
            await asyncio.sleep(0.05)  # Simulate processing time

        # Mark all changes as processed
        all_entity_ids = [c.entity_id for c in changes]
        self.tracker.mark_processed(entity_type, all_entity_ids)

    def get_stats(self) -> dict[str, Any]:
        """Get queue statistics.

        Returns:
            Dictionary with queue statistics
        """
        return {
            "running": self._running,
            "total_processed": self._total_processed,
            "total_batches": self._total_batches,
            "last_process_time_ms": (
                self._last_process_time * 1000 if self._last_process_time else None
            ),
            "queue_stats": self.tracker.get_queue_stats(),
            "config": {
                "batch_size": self.config.batch_size,
                "debounce_seconds": self.config.debounce_seconds,
                "max_concurrent": self.config.max_concurrent_updates,
            },
        }


# Global queue instance (singleton pattern)
_queue: ReindexQueue | None = None


def get_reindex_queue() -> ReindexQueue:
    """Get or create global reindex queue instance.

    Returns:
        ReindexQueue singleton
    """
    global _queue

    if _queue is None:
        _queue = ReindexQueue()

    return _queue
