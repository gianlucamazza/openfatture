"""RAG Auto-Update System.

Automatic knowledge base updates when invoice/client data changes.
Uses SQLAlchemy event listeners and async queue for batch processing.

Key Components:
- AutoUpdateConfig: Configuration for auto-update behavior
- ChangeTracker: Tracks changes to entities for reindexing
- ReindexQueue: Async queue for batch reindexing
- AutoIndexingService: Orchestrates automatic reindexing
- Event listeners: SQLAlchemy hooks for data changes

Example:
    >>> from openfatture.ai.rag.auto_update import get_auto_indexing_service, setup_event_listeners
    >>>
    >>> # Setup event listeners (do once at startup)
    >>> setup_event_listeners()
    >>>
    >>> # Start auto-indexing service
    >>> service = get_auto_indexing_service()
    >>> await service.start()
    >>>
    >>> # Now all invoice/client changes trigger automatic reindexing
"""

from openfatture.ai.rag.auto_update.config import (
    AUTO_UPDATE_CONFIG,
    AutoUpdateConfig,
    get_auto_update_config,
)
from openfatture.ai.rag.auto_update.listeners import setup_event_listeners, teardown_event_listeners
from openfatture.ai.rag.auto_update.queue import ReindexQueue, get_reindex_queue
from openfatture.ai.rag.auto_update.service import AutoIndexingService, get_auto_indexing_service
from openfatture.ai.rag.auto_update.tracker import (
    ChangeTracker,
    ChangeType,
    EntityChange,
    get_change_tracker,
)

__all__ = [
    # Config
    "AutoUpdateConfig",
    "get_auto_update_config",
    "AUTO_UPDATE_CONFIG",
    # Tracker
    "ChangeTracker",
    "ChangeType",
    "EntityChange",
    "get_change_tracker",
    # Queue
    "ReindexQueue",
    "get_reindex_queue",
    # Service
    "AutoIndexingService",
    "get_auto_indexing_service",
    # Listeners
    "setup_event_listeners",
    "teardown_event_listeners",
]
