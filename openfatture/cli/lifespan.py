"""
Lifespan management for OpenFatture CLI application.

Provides graceful startup and shutdown handling for async resources,
preventing event loop race conditions during application termination.
"""

from __future__ import annotations

import asyncio
import signal
from collections.abc import AsyncGenerator, Coroutine
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

import httpx

# The AI/ML self-learning stack (retraining scheduler, RAG auto-update) is heavy
# and optional. Import it lazily inside the methods that use it so the core CLI
# (and a minimal, AI-free install such as the payment-only Docker image) can
# start without the AI extras; only type names are imported eagerly, guarded by
# TYPE_CHECKING.
if TYPE_CHECKING:
    from openfatture.ai.ml.retraining import RetrainingScheduler
    from openfatture.ai.rag.auto_update import AutoIndexingService

from openfatture.events import GlobalEventBus, initialize_event_system
from openfatture.hooks import HookEventBridge, initialize_hook_system
from openfatture.platform.async_bridge import run_async
from openfatture.platform.logging import get_logger

# Context variable to hold the shared HTTP client
_http_client_context: ContextVar[httpx.AsyncClient | None] = ContextVar(
    "_http_client_context", default=None
)

# Context variable to hold the global event bus
_event_bus_context: ContextVar[GlobalEventBus | None] = ContextVar(
    "_event_bus_context", default=None
)

logger = get_logger(__name__)


class LifespanManager:
    """Manages application lifecycle and async resource cleanup."""

    def __init__(self) -> None:
        self.http_client: httpx.AsyncClient | None = None
        self.event_bus: GlobalEventBus | None = None
        self.hook_bridge: HookEventBridge | None = None
        self.shutdown_event = asyncio.Event()
        self._shutdown_handlers: list[asyncio.Task[Any]] = []

        # Self-learning components
        self.auto_indexing_service: AutoIndexingService | None = None
        self.retraining_scheduler: RetrainingScheduler | None = None

    @asynccontextmanager
    async def lifespan(self) -> AsyncGenerator[dict[str, Any], None]:
        """Application lifespan context manager."""
        # Startup phase
        logger.info("Starting OpenFatture CLI application")

        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )
        _http_client_context.set(self.http_client)

        # Initialize global event system
        logger.debug("Initializing global event system")
        self.event_bus = initialize_event_system()
        _event_bus_context.set(self.event_bus)
        logger.info("Global event system initialized", **self.event_bus.get_stats())

        # Initialize hook system
        logger.debug("Initializing hook system")
        self.hook_bridge = initialize_hook_system(self.event_bus)
        logger.info("Hook system initialized and registered with event bus")

        # Optional feature extras (never required for core invoicing)
        await self._initialize_self_learning()

        try:
            yield {
                "http_client": self.http_client,
                "event_bus": self.event_bus,
                "hook_bridge": self.hook_bridge,
                "auto_indexing_service": self.auto_indexing_service,
                "retraining_scheduler": self.retraining_scheduler,
            }
        finally:
            # Shutdown phase
            logger.info("Shutting down OpenFatture CLI application")
            await self._graceful_shutdown()

    async def _initialize_self_learning(self) -> None:
        """Initialize RAG auto-update and ML retraining when those extras are installed.

        Skipped entirely on core-only installs (no ``rag`` / ``ml`` extras).
        """
        from openfatture.platform.extras import has_extra

        want_rag = has_extra("rag")
        want_ml = has_extra("ml")
        if not want_rag and not want_ml:
            logger.debug("Self-learning extras not installed; skipping RAG/ML startup")
            return

        if want_rag:
            try:
                from openfatture.ai.rag.auto_update import (
                    get_auto_indexing_service,
                    get_auto_update_config,
                    setup_event_listeners,
                )

                logger.debug("Setting up RAG auto-update event listeners")
                setup_event_listeners()

                auto_update_config = get_auto_update_config()
                if auto_update_config.enabled:
                    logger.info("RAG auto-update enabled, starting service")
                    self.auto_indexing_service = get_auto_indexing_service()
                    await self.auto_indexing_service.start()
                    logger.info(
                        "Auto-indexing service started",
                        tracked_entities=auto_update_config.get_tracked_entities(),
                    )
                else:
                    logger.debug("RAG auto-update disabled by config")
            except Exception as e:
                logger.warning(f"RAG auto-update not started: {e}")

        if want_ml:
            try:
                from openfatture.ai.ml.retraining import (
                    get_scheduler as get_retraining_scheduler,
                )

                self.retraining_scheduler = get_retraining_scheduler()
                retraining_status = self.retraining_scheduler.get_status()
                if retraining_status.get("enabled"):
                    logger.info("ML retraining enabled, starting scheduler")
                    self.retraining_scheduler.start()
                    logger.info(
                        "Retraining scheduler started",
                        interval_hours=retraining_status.get("interval_hours"),
                        dry_run=retraining_status.get("dry_run"),
                    )
                else:
                    logger.debug("ML retraining disabled by config")
            except Exception as e:
                logger.warning(f"ML retraining not started: {e}")

    async def _graceful_shutdown(self) -> None:
        """Perform graceful shutdown of all resources."""
        try:
            # Shutdown self-learning systems
            await self._shutdown_self_learning()

            # Close HTTP client
            if self.http_client:
                logger.debug("Closing HTTP client")
                await self.http_client.aclose()
                self.http_client = None

            # Wait for any pending shutdown handlers
            if self._shutdown_handlers:
                logger.debug(f"Waiting for {len(self._shutdown_handlers)} shutdown handlers")
                await asyncio.gather(*self._shutdown_handlers, return_exceptions=True)

            logger.info("Graceful shutdown completed")

        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")

    async def _shutdown_self_learning(self) -> None:
        """Shutdown optional RAG/ML systems gracefully."""
        try:
            if self.retraining_scheduler:
                logger.debug("Stopping retraining scheduler")
                self.retraining_scheduler.stop()
                self.retraining_scheduler = None

            if self.auto_indexing_service:
                logger.debug("Stopping auto-indexing service")
                await self.auto_indexing_service.stop()
                self.auto_indexing_service = None

            try:
                from openfatture.ai.rag.auto_update import teardown_event_listeners

                logger.debug("Tearing down RAG auto-update event listeners")
                teardown_event_listeners()
            except ImportError:
                pass

            logger.debug("Optional self-learning systems shutdown completed")

        except Exception as e:
            logger.error(f"Error shutting down self-learning systems: {e}", exc_info=True)

    def add_shutdown_handler(self, coro: Any) -> None:
        """Add a coroutine to run during shutdown."""
        task = asyncio.create_task(coro)
        self._shutdown_handlers.append(task)

    def signal_handler(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals (SIGTERM, SIGINT)."""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received signal {signal_name} ({signum}), initiating graceful shutdown")
        self.shutdown_event.set()


# Global lifespan manager instance
_lifespan_manager = LifespanManager()


def get_lifespan_manager() -> LifespanManager:
    """Get the global lifespan manager instance."""
    return _lifespan_manager


@asynccontextmanager
async def app_lifespan() -> AsyncGenerator[None, None]:
    """Application lifespan context manager for CLI commands."""
    async with _lifespan_manager.lifespan():
        yield


def setup_signal_handlers() -> None:
    """Setup signal handlers for graceful shutdown."""
    signal.signal(signal.SIGTERM, _lifespan_manager.signal_handler)
    signal.signal(signal.SIGINT, _lifespan_manager.signal_handler)


async def run_with_lifespan[T](main_coro: Coroutine[Any, Any, T]) -> T:
    """
    Run a coroutine with proper lifespan management.

    Args:
        main_coro: The main coroutine to execute

    Returns:
        The result of the main coroutine
    """
    setup_signal_handlers()

    try:
        async with app_lifespan():
            return await main_coro
    except asyncio.CancelledError:
        logger.info("Operation cancelled")
        raise
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        raise
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


def run_sync_with_lifespan[T](main_coro: Coroutine[Any, Any, T]) -> T | None:
    """
    Run an async coroutine synchronously with lifespan management.

    This is useful for CLI commands that need to run async code
    but are called from synchronous contexts.

    Args:
        main_coro: The main coroutine to execute

    Returns:
        The result of the main coroutine, or None on user interruption
    """
    try:
        return run_async(run_with_lifespan(main_coro))
    except KeyboardInterrupt:
        logger.info("Application shutdown requested by user")
        return None
    except Exception as e:
        logger.error(f"Application failed: {e}")
        raise


def get_event_bus() -> GlobalEventBus | None:
    """Get the global event bus from context.

    Returns:
        The global event bus instance if available, None otherwise

    Example:
        >>> from openfatture.cli.lifespan import get_event_bus
        >>> event_bus = get_event_bus()
        >>> if event_bus:
        >>>     event_bus.publish(InvoiceCreatedEvent(...))
    """
    return _event_bus_context.get()
