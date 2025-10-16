"""SQLAlchemy Event Listeners for RAG Auto-Update.

Listens to database changes (insert, update, delete) and tracks them
for automatic reindexing.

Example:
    >>> from openfatture.ai.rag.auto_update import setup_event_listeners
    >>> setup_event_listeners()
    >>> # Now all invoice/client changes are automatically tracked
"""

from sqlalchemy import event
from sqlalchemy.orm import Mapper

from openfatture.ai.rag.auto_update.config import get_auto_update_config
from openfatture.ai.rag.auto_update.tracker import ChangeType, get_change_tracker
from openfatture.storage.database.models import Cliente, Fattura
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


def _on_invoice_insert(mapper: Mapper, connection: any, target: Fattura) -> None:
    """Handle invoice insert events.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Fattura instance
    """
    tracker = get_change_tracker()
    tracker.track_change(
        entity_type="invoice",
        entity_id=target.id,
        change_type=ChangeType.CREATE,
        metadata={
            "numero": target.numero,
            "anno": target.anno,
            "cliente_id": target.cliente_id,
        },
    )

    logger.debug("invoice_insert_tracked", invoice_id=target.id)


def _on_invoice_update(mapper: Mapper, connection: any, target: Fattura) -> None:
    """Handle invoice update events.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Fattura instance
    """
    tracker = get_change_tracker()
    tracker.track_change(
        entity_type="invoice",
        entity_id=target.id,
        change_type=ChangeType.UPDATE,
        metadata={
            "numero": target.numero,
            "anno": target.anno,
            "cliente_id": target.cliente_id,
        },
    )

    logger.debug("invoice_update_tracked", invoice_id=target.id)


def _on_invoice_delete(mapper: Mapper, connection: any, target: Fattura) -> None:
    """Handle invoice delete events.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Fattura instance
    """
    tracker = get_change_tracker()
    tracker.track_change(
        entity_type="invoice",
        entity_id=target.id,
        change_type=ChangeType.DELETE,
        metadata={
            "numero": target.numero,
            "anno": target.anno,
        },
    )

    logger.debug("invoice_delete_tracked", invoice_id=target.id)


def _on_client_insert(mapper: Mapper, connection: any, target: Cliente) -> None:
    """Handle client insert events.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Cliente instance
    """
    tracker = get_change_tracker()
    tracker.track_change(
        entity_type="client",
        entity_id=target.id,
        change_type=ChangeType.CREATE,
        metadata={
            "denominazione": target.denominazione,
        },
    )

    logger.debug("client_insert_tracked", client_id=target.id)


def _on_client_update(mapper: Mapper, connection: any, target: Cliente) -> None:
    """Handle client update events.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Cliente instance
    """
    tracker = get_change_tracker()
    tracker.track_change(
        entity_type="client",
        entity_id=target.id,
        change_type=ChangeType.UPDATE,
        metadata={
            "denominazione": target.denominazione,
        },
    )

    logger.debug("client_update_tracked", client_id=target.id)


def _on_client_delete(mapper: Mapper, connection: any, target: Cliente) -> None:
    """Handle client delete events.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Cliente instance
    """
    tracker = get_change_tracker()
    tracker.track_change(
        entity_type="client",
        entity_id=target.id,
        change_type=ChangeType.DELETE,
        metadata={
            "denominazione": target.denominazione,
        },
    )

    logger.debug("client_delete_tracked", client_id=target.id)


def setup_event_listeners() -> None:
    """Setup SQLAlchemy event listeners for auto-update.

    Registers listeners on Fattura and Cliente models to track changes.
    Only registers if auto-update is enabled in config.
    """
    config = get_auto_update_config()

    if not config.enabled:
        logger.info("auto_update_listeners_disabled", message="Auto-update not enabled")
        return

    # Register invoice listeners if tracking enabled
    if config.track_invoices:
        event.listen(Fattura, "after_insert", _on_invoice_insert)
        event.listen(Fattura, "after_update", _on_invoice_update)
        event.listen(Fattura, "after_delete", _on_invoice_delete)

        logger.info("invoice_event_listeners_registered")

    # Register client listeners if tracking enabled
    if config.track_clients:
        event.listen(Cliente, "after_insert", _on_client_insert)
        event.listen(Cliente, "after_update", _on_client_update)
        event.listen(Cliente, "after_delete", _on_client_delete)

        logger.info("client_event_listeners_registered")

    logger.info(
        "event_listeners_setup_completed",
        track_invoices=config.track_invoices,
        track_clients=config.track_clients,
    )


def teardown_event_listeners() -> None:
    """Remove SQLAlchemy event listeners.

    Removes all registered listeners. Useful for testing or shutdown.
    """
    # Remove invoice listeners
    try:
        event.remove(Fattura, "after_insert", _on_invoice_insert)
        event.remove(Fattura, "after_update", _on_invoice_update)
        event.remove(Fattura, "after_delete", _on_invoice_delete)
        logger.info("invoice_event_listeners_removed")
    except Exception as e:
        logger.debug("invoice_listeners_removal_failed", error=str(e))

    # Remove client listeners
    try:
        event.remove(Cliente, "after_insert", _on_client_insert)
        event.remove(Cliente, "after_update", _on_client_update)
        event.remove(Cliente, "after_delete", _on_client_delete)
        logger.info("client_event_listeners_removed")
    except Exception as e:
        logger.debug("client_listeners_removal_failed", error=str(e))

    logger.info("event_listeners_teardown_completed")
