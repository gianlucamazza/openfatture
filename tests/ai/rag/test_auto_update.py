"""Tests for RAG auto-update system."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openfatture.ai.rag.auto_update import (
    AutoIndexingService,
    AutoUpdateConfig,
    ChangeTracker,
    ChangeType,
    EntityChange,
    ReindexQueue,
    get_auto_indexing_service,
    get_auto_update_config,
    get_change_tracker,
    get_reindex_queue,
    setup_event_listeners,
    teardown_event_listeners,
)


class TestAutoUpdateConfig:
    """Test AutoUpdateConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AutoUpdateConfig()

        assert config.enabled is False
        assert config.batch_size == 50
        assert config.debounce_seconds == 5
        assert config.max_queue_size == 1000
        assert config.track_invoices is True
        assert config.track_clients is True
        assert config.incremental_updates is True
        assert config.async_processing is True

    def test_get_tracked_entities(self):
        """Test get_tracked_entities method."""
        config = AutoUpdateConfig(track_invoices=True, track_clients=True)
        entities = config.get_tracked_entities()

        assert "invoice" in entities
        assert "client" in entities
        assert len(entities) == 2

    def test_get_tracked_entities_selective(self):
        """Test get_tracked_entities with selective tracking."""
        config = AutoUpdateConfig(track_invoices=True, track_clients=False)
        entities = config.get_tracked_entities()

        assert "invoice" in entities
        assert "client" not in entities
        assert len(entities) == 1

    def test_get_auto_update_config_singleton(self):
        """Test get_auto_update_config returns singleton."""
        config1 = get_auto_update_config()
        config2 = get_auto_update_config()

        assert config1 is config2


class TestEntityChange:
    """Test EntityChange dataclass."""

    def test_entity_change_creation(self):
        """Test creating EntityChange."""
        change = EntityChange(
            entity_type="invoice",
            entity_id=123,
            change_type=ChangeType.CREATE,
            timestamp=datetime.now(),
        )

        assert change.entity_type == "invoice"
        assert change.entity_id == 123
        assert change.change_type == ChangeType.CREATE
        assert change.metadata is None

    def test_entity_change_with_metadata(self):
        """Test EntityChange with metadata."""
        metadata = {"numero": "001", "anno": 2025}
        change = EntityChange(
            entity_type="invoice",
            entity_id=123,
            change_type=ChangeType.UPDATE,
            timestamp=datetime.now(),
            metadata=metadata,
        )

        assert change.metadata == metadata
        assert change.metadata["numero"] == "001"


class TestChangeTracker:
    """Test ChangeTracker."""

    @pytest.fixture
    def enabled_config(self):
        """Create enabled config for testing."""
        return AutoUpdateConfig(enabled=True)

    @pytest.fixture
    def tracker(self, enabled_config):
        """Create test tracker with enabled config."""
        with patch(
            "openfatture.ai.rag.auto_update.tracker.get_auto_update_config",
            return_value=enabled_config,
        ):
            tracker = ChangeTracker()
            tracker.clear_all()  # Clear any existing changes
            return tracker

    def test_tracker_initialization(self, tracker):
        """Test tracker initialization."""
        assert len(tracker._pending) == 0

    def test_track_change(self, tracker):
        """Test tracking a change."""
        tracker.track_change(
            entity_type="invoice",
            entity_id=123,
            change_type=ChangeType.CREATE,
            metadata={"numero": "001"},
        )

        stats = tracker.get_queue_stats()
        assert stats["by_entity_type"]["invoice"] == 1

    def test_track_multiple_changes(self, tracker):
        """Test tracking multiple changes."""
        for i in range(5):
            tracker.track_change(
                entity_type="invoice",
                entity_id=i,
                change_type=ChangeType.CREATE,
            )

        stats = tracker.get_queue_stats()
        assert stats["by_entity_type"]["invoice"] == 5

    def test_get_pending_changes(self, tracker):
        """Test getting pending changes."""
        # Add changes
        for i in range(3):
            tracker.track_change(
                entity_type="invoice",
                entity_id=i,
                change_type=ChangeType.CREATE,
            )

        # Get pending
        pending = tracker.get_pending_changes(entity_type="invoice")

        assert len(pending) == 3
        assert all(c.entity_type == "invoice" for c in pending)

    def test_get_pending_changes_with_limit(self, tracker):
        """Test getting pending changes with batch size limit."""
        # Add 10 changes
        for i in range(10):
            tracker.track_change(
                entity_type="invoice",
                entity_id=i,
                change_type=ChangeType.CREATE,
            )

        # Get only 5
        pending = tracker.get_pending_changes(entity_type="invoice", batch_size=5)

        assert len(pending) == 5

    def test_mark_processed(self, tracker):
        """Test marking changes as processed."""
        # Add changes
        for i in range(3):
            tracker.track_change(
                entity_type="invoice",
                entity_id=i,
                change_type=ChangeType.CREATE,
            )

        # Mark processed
        tracker.mark_processed("invoice", [0, 1, 2])

        # Should be empty now
        pending = tracker.get_pending_changes(entity_type="invoice")
        assert len(pending) == 0

    def test_clear_all(self, tracker):
        """Test clearing all changes."""
        tracker.track_change("invoice", 1, ChangeType.CREATE)
        tracker.track_change("client", 2, ChangeType.UPDATE)

        tracker.clear_all()

        stats = tracker.get_queue_stats()
        assert stats["total_pending"] == 0

    def test_max_queue_size(self, enabled_config):
        """Test max queue size enforcement."""
        config = AutoUpdateConfig(enabled=True, max_queue_size=10)
        with patch(
            "openfatture.ai.rag.auto_update.tracker.get_auto_update_config", return_value=config
        ):
            tracker = ChangeTracker()

            # Try to add 20 changes (should only keep last 10)
            for i in range(20):
                tracker.track_change("invoice", i, ChangeType.CREATE)

            pending = tracker.get_pending_changes("invoice")
            assert len(pending) == 10
            # Should have kept the most recent ones (10-19)
            ids = [c.entity_id for c in pending]
            assert 19 in ids

    def test_get_change_tracker_singleton(self):
        """Test get_change_tracker returns singleton."""
        tracker1 = get_change_tracker()
        tracker2 = get_change_tracker()

        assert tracker1 is tracker2


class TestReindexQueue:
    """Test ReindexQueue."""

    @pytest.fixture
    def mock_callback(self):
        """Create mock callback."""
        return AsyncMock()

    @pytest.fixture
    def queue(self, mock_callback):
        """Create test queue."""
        return ReindexQueue(reindex_callback=mock_callback)

    def test_queue_initialization(self, queue):
        """Test queue initialization."""
        assert queue._running is False
        assert queue._total_processed == 0
        assert queue._total_batches == 0

    @pytest.mark.asyncio
    async def test_start_queue(self, queue):
        """Test starting queue."""
        # Mock config to enable
        with patch.object(queue.config, "enabled", True):
            await queue.start()

            assert queue._running is True
            assert queue._task is not None

            # Stop queue
            await queue.stop()

    @pytest.mark.asyncio
    async def test_stop_queue(self, queue):
        """Test stopping queue."""
        with patch.object(queue.config, "enabled", True):
            await queue.start()
            await queue.stop()

            assert queue._running is False

    @pytest.mark.asyncio
    async def test_process_batch(self, queue, mock_callback):
        """Test processing a batch."""
        changes = [
            EntityChange(
                entity_type="invoice",
                entity_id=i,
                change_type=ChangeType.CREATE,
                timestamp=datetime.now(),
            )
            for i in range(3)
        ]

        await queue._process_batch(changes)

        # Callback should have been called
        mock_callback.assert_called_once()
        assert len(mock_callback.call_args[0][0]) == 3

    @pytest.mark.asyncio
    async def test_process_entity_type(self, queue, mock_callback):
        """Test processing specific entity type."""
        changes = [
            EntityChange(
                entity_type="invoice",
                entity_id=1,
                change_type=ChangeType.CREATE,
                timestamp=datetime.now(),
            ),
            EntityChange(
                entity_type="invoice",
                entity_id=2,
                change_type=ChangeType.UPDATE,
                timestamp=datetime.now(),
            ),
        ]

        await queue._process_entity_type("invoice", changes)

        # Callback should have been called
        mock_callback.assert_called_once()

    def test_get_stats(self, queue):
        """Test getting queue statistics."""
        stats = queue.get_stats()

        assert "running" in stats
        assert "total_processed" in stats
        assert "total_batches" in stats
        assert "queue_stats" in stats
        assert "config" in stats

    def test_get_reindex_queue_singleton(self):
        """Test get_reindex_queue returns singleton."""
        queue1 = get_reindex_queue()
        queue2 = get_reindex_queue()

        assert queue1 is queue2


class TestAutoIndexingService:
    """Test AutoIndexingService."""

    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store."""
        store = MagicMock()
        store.delete = AsyncMock()
        return store

    @pytest.fixture
    def mock_invoice_indexer(self):
        """Create mock invoice indexer."""
        indexer = MagicMock()
        indexer.index_invoice = AsyncMock(return_value="doc_123")
        indexer.delete_invoice = AsyncMock()
        return indexer

    @pytest.fixture
    def service(self, mock_vector_store):
        """Create test service."""
        return AutoIndexingService(vector_store=mock_vector_store)

    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initialization."""
        assert service.config is not None
        assert service.tracker is not None
        assert service.queue is not None
        assert service.invoice_indexer is not None

    @pytest.mark.asyncio
    async def test_start_service(self, service):
        """Test starting service."""
        with patch.object(service.config, "enabled", True):
            with patch.object(service.queue, "start", new_callable=AsyncMock):
                await service.start()

    @pytest.mark.asyncio
    async def test_stop_service(self, service):
        """Test stopping service."""
        with patch.object(service.queue, "stop", new_callable=AsyncMock):
            await service.stop()

    @pytest.mark.asyncio
    async def test_process_invoice_create(self, service):
        """Test processing invoice creation."""
        change = EntityChange(
            entity_type="invoice",
            entity_id=123,
            change_type=ChangeType.CREATE,
            timestamp=datetime.now(),
        )

        with patch.object(
            service.invoice_indexer, "index_invoice", new_callable=AsyncMock
        ) as mock_index:
            mock_index.return_value = "doc_123"
            await service._process_invoice_change(change)

            mock_index.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_process_invoice_update(self, service):
        """Test processing invoice update."""
        change = EntityChange(
            entity_type="invoice",
            entity_id=123,
            change_type=ChangeType.UPDATE,
            timestamp=datetime.now(),
        )

        with patch.object(
            service.invoice_indexer, "index_invoice", new_callable=AsyncMock
        ) as mock_index:
            mock_index.return_value = "doc_123"
            await service._process_invoice_change(change)

            mock_index.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_process_invoice_delete(self, service):
        """Test processing invoice deletion."""
        change = EntityChange(
            entity_type="invoice",
            entity_id=123,
            change_type=ChangeType.DELETE,
            timestamp=datetime.now(),
        )

        with patch.object(
            service.invoice_indexer, "delete_invoice", new_callable=AsyncMock
        ) as mock_delete:
            await service._process_invoice_change(change)

            mock_delete.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_process_client_change(self, service):
        """Test processing client change."""
        change = EntityChange(
            entity_type="client",
            entity_id=456,
            change_type=ChangeType.UPDATE,
            timestamp=datetime.now(),
        )

        # Mock database session and query
        with patch("openfatture.storage.database.base.SessionLocal") as mock_session_local:
            mock_db = MagicMock()
            mock_session_local.return_value = mock_db

            # Mock invoice query result
            mock_invoice = MagicMock()
            mock_invoice.id = 789
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_invoice]

            with patch.object(
                service.invoice_indexer, "index_invoice", new_callable=AsyncMock
            ) as mock_index:
                await service._process_client_change(change)

                # Should have reindexed the client's invoice
                mock_index.assert_called_once_with(789)

    @pytest.mark.asyncio
    async def test_manual_reindex_invoices(self, service):
        """Test manual invoice reindexing."""
        with patch.object(
            service.invoice_indexer, "index_invoice", new_callable=AsyncMock
        ) as mock_index:
            mock_index.return_value = "doc_123"

            result = await service.manual_reindex("invoice", [1, 2, 3])

            assert result["entity_type"] == "invoice"
            assert result["requested_count"] == 3
            assert len(result["successful"]) == 3
            assert len(result["failed"]) == 0
            assert mock_index.call_count == 3

    @pytest.mark.asyncio
    async def test_manual_reindex_with_failure(self, service):
        """Test manual reindexing with some failures."""
        with patch.object(
            service.invoice_indexer, "index_invoice", new_callable=AsyncMock
        ) as mock_index:
            # First call succeeds, second fails, third succeeds
            mock_index.side_effect = [
                "doc_1",
                Exception("Indexing failed"),
                "doc_3",
            ]

            result = await service.manual_reindex("invoice", [1, 2, 3])

            assert result["requested_count"] == 3
            assert len(result["successful"]) == 2
            assert len(result["failed"]) == 1
            assert result["failed"][0]["entity_id"] == 2

    def test_get_status(self, service):
        """Test getting service status."""
        status = service.get_status()

        assert "enabled" in status
        assert "running" in status
        assert "queue_stats" in status
        assert "tracker_stats" in status
        assert "config" in status

    @pytest.mark.skip(reason="Singleton test conflicts with module-level imports")
    def test_get_auto_indexing_service_singleton(self):
        """Test get_auto_indexing_service returns singleton."""
        service1 = get_auto_indexing_service()
        service2 = get_auto_indexing_service()

        assert service1 is service2


class TestEventListeners:
    """Test SQLAlchemy event listeners."""

    @pytest.fixture
    def mock_fattura(self):
        """Create mock Fattura."""
        fattura = MagicMock()
        fattura.id = 123
        fattura.numero = "001"
        fattura.anno = 2025
        fattura.cliente_id = 456
        return fattura

    @pytest.fixture
    def mock_cliente(self):
        """Create mock Cliente."""
        cliente = MagicMock()
        cliente.id = 456
        cliente.denominazione = "Test Client"
        return cliente

    def test_setup_event_listeners(self):
        """Test setting up event listeners."""
        config = AutoUpdateConfig(enabled=True, track_invoices=True, track_clients=True)

        with patch("openfatture.ai.rag.auto_update.listeners.event") as mock_event:
            with patch(
                "openfatture.ai.rag.auto_update.listeners.get_auto_update_config",
                return_value=config,
            ):
                setup_event_listeners()

                # Should have registered 6 listeners (3 for invoices, 3 for clients)
                assert mock_event.listen.call_count == 6

    def test_teardown_event_listeners(self):
        """Test tearing down event listeners."""
        with patch("openfatture.ai.rag.auto_update.listeners.event") as mock_event:
            teardown_event_listeners()

            # Should have removed 6 listeners
            assert mock_event.remove.call_count == 6

    def test_invoice_insert_listener(self, mock_fattura):
        """Test invoice insert event listener."""
        from openfatture.ai.rag.auto_update.listeners import _on_invoice_insert

        # Create enabled config and tracker
        config = AutoUpdateConfig(enabled=True)
        with patch(
            "openfatture.ai.rag.auto_update.tracker.get_auto_update_config", return_value=config
        ):
            tracker = ChangeTracker()
            tracker.clear_all()

            with patch(
                "openfatture.ai.rag.auto_update.listeners.get_change_tracker", return_value=tracker
            ):
                _on_invoice_insert(None, None, mock_fattura)

                stats = tracker.get_queue_stats()
                assert stats["by_entity_type"].get("invoice", 0) == 1

    def test_invoice_update_listener(self, mock_fattura):
        """Test invoice update event listener."""
        from openfatture.ai.rag.auto_update.listeners import _on_invoice_update

        config = AutoUpdateConfig(enabled=True)
        with patch(
            "openfatture.ai.rag.auto_update.tracker.get_auto_update_config", return_value=config
        ):
            tracker = ChangeTracker()
            tracker.clear_all()

            with patch(
                "openfatture.ai.rag.auto_update.listeners.get_change_tracker", return_value=tracker
            ):
                _on_invoice_update(None, None, mock_fattura)

                stats = tracker.get_queue_stats()
                assert stats["by_entity_type"].get("invoice", 0) == 1

    def test_invoice_delete_listener(self, mock_fattura):
        """Test invoice delete event listener."""
        from openfatture.ai.rag.auto_update.listeners import _on_invoice_delete

        config = AutoUpdateConfig(enabled=True)
        with patch(
            "openfatture.ai.rag.auto_update.tracker.get_auto_update_config", return_value=config
        ):
            tracker = ChangeTracker()
            tracker.clear_all()

            with patch(
                "openfatture.ai.rag.auto_update.listeners.get_change_tracker", return_value=tracker
            ):
                _on_invoice_delete(None, None, mock_fattura)

                stats = tracker.get_queue_stats()
                assert stats["by_entity_type"].get("invoice", 0) == 1

    def test_client_insert_listener(self, mock_cliente):
        """Test client insert event listener."""
        from openfatture.ai.rag.auto_update.listeners import _on_client_insert

        config = AutoUpdateConfig(enabled=True)
        with patch(
            "openfatture.ai.rag.auto_update.tracker.get_auto_update_config", return_value=config
        ):
            tracker = ChangeTracker()
            tracker.clear_all()

            with patch(
                "openfatture.ai.rag.auto_update.listeners.get_change_tracker", return_value=tracker
            ):
                _on_client_insert(None, None, mock_cliente)

                stats = tracker.get_queue_stats()
                assert stats["by_entity_type"].get("client", 0) == 1

    def test_client_update_listener(self, mock_cliente):
        """Test client update event listener."""
        from openfatture.ai.rag.auto_update.listeners import _on_client_update

        config = AutoUpdateConfig(enabled=True)
        with patch(
            "openfatture.ai.rag.auto_update.tracker.get_auto_update_config", return_value=config
        ):
            tracker = ChangeTracker()
            tracker.clear_all()

            with patch(
                "openfatture.ai.rag.auto_update.listeners.get_change_tracker", return_value=tracker
            ):
                _on_client_update(None, None, mock_cliente)

                stats = tracker.get_queue_stats()
                assert stats["by_entity_type"].get("client", 0) == 1

    def test_client_delete_listener(self, mock_cliente):
        """Test client delete event listener."""
        from openfatture.ai.rag.auto_update.listeners import _on_client_delete

        config = AutoUpdateConfig(enabled=True)
        with patch(
            "openfatture.ai.rag.auto_update.tracker.get_auto_update_config", return_value=config
        ):
            tracker = ChangeTracker()
            tracker.clear_all()

            with patch(
                "openfatture.ai.rag.auto_update.listeners.get_change_tracker", return_value=tracker
            ):
                _on_client_delete(None, None, mock_cliente)

                stats = tracker.get_queue_stats()
                assert stats["by_entity_type"].get("client", 0) == 1
