"""Integration tests for fattura command event publishing."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from typer.testing import CliRunner

from openfatture.core.events import GlobalEventBus
from openfatture.core.events.listeners import register_default_listeners
from openfatture.core.events.repository import EventRepository
from openfatture.storage.database.base import get_session, init_db
from openfatture.storage.database.models import Cliente, Fattura, RigaFattura, StatoFattura


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def test_db(tmp_path):
    """Initialize test database with event system."""
    db_path = tmp_path / "test_fattura_events.db"
    init_db(f"sqlite:///{db_path}")

    # Create event bus and register listeners
    event_bus = GlobalEventBus()
    register_default_listeners(event_bus)

    # Monkey-patch get_event_bus for this test
    import openfatture.cli.lifespan as lifespan_module

    original_get_event_bus = lifespan_module.get_event_bus
    lifespan_module.get_event_bus = lambda: event_bus

    yield

    # Restore original
    lifespan_module.get_event_bus = original_get_event_bus


@pytest.fixture
def test_client(test_db):
    """Create a test client."""
    db = get_session()
    try:
        cliente = Cliente(
            denominazione="Test Client S.r.l.",
            partita_iva="12345678901",
            codice_fiscale="TSTCLT80A01H501U",
            codice_destinatario="ABCDEFG",
            indirizzo="Via Test 1",
            cap="00100",
            comune="Roma",
            provincia="RM",
            nazione="IT",
        )
        db.add(cliente)
        db.commit()
        db.refresh(cliente)
        return cliente.id
    finally:
        db.close()


def test_invoice_creation_publishes_event(runner, test_client, test_db):
    """Test that creating an invoice publishes InvoiceCreatedEvent."""
    # This test would need to be interactive, so we test programmatically
    db = get_session()
    try:
        # Create invoice directly (simulating what the CLI does)
        fattura = Fattura(
            numero="001",
            anno=date.today().year,
            data_emissione=date.today(),
            cliente_id=test_client,
            stato=StatoFattura.BOZZA,
        )
        db.add(fattura)
        db.flush()

        # Add line item
        riga = RigaFattura(
            fattura_id=fattura.id,
            numero_riga=1,
            descrizione="Test Service",
            quantita=Decimal("1.0"),
            prezzo_unitario=Decimal("100.00"),
            aliquota_iva=Decimal("22.00"),
            imponibile=Decimal("100.00"),
            iva=Decimal("22.00"),
            totale=Decimal("122.00"),
        )
        db.add(riga)

        fattura.imponibile = Decimal("100.00")
        fattura.iva = Decimal("22.00")
        fattura.totale = Decimal("122.00")

        db.commit()
        db.refresh(fattura)

        # Publish event (as the CLI does)
        from openfatture.cli.lifespan import get_event_bus
        from openfatture.core.events import InvoiceCreatedEvent

        event_bus = get_event_bus()
        if event_bus:
            event_bus.publish(
                InvoiceCreatedEvent(
                    invoice_id=fattura.id,
                    invoice_number=f"{fattura.numero}/{fattura.anno}",
                    client_id=fattura.cliente_id,
                    client_name="Test Client S.r.l.",
                    total_amount=fattura.totale,
                )
            )

        # Verify event was persisted
        repo = EventRepository()
        try:
            events = repo.get_by_event_type("InvoiceCreatedEvent")
            assert len(events) >= 1

            # Find our event
            our_event = next(
                (e for e in events if e.entity_id == fattura.id and e.entity_type == "invoice"),
                None,
            )
            assert our_event is not None
            assert our_event.event_type == "InvoiceCreatedEvent"
            assert our_event.entity_type == "invoice"
            assert our_event.entity_id == fattura.id

            # Verify event data
            import json

            event_data = json.loads(our_event.event_data)
            assert event_data["invoice_id"] == fattura.id
            assert event_data["invoice_number"] == f"{fattura.numero}/{fattura.anno}"
            assert event_data["client_id"] == test_client

        finally:
            repo.close()

    finally:
        db.close()


def test_invoice_validation_publishes_event(test_client, test_db):
    """Test that validating an invoice publishes InvoiceValidatedEvent."""
    db = get_session()
    try:
        # Create invoice
        fattura = Fattura(
            numero="002",
            anno=date.today().year,
            data_emissione=date.today(),
            cliente_id=test_client,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("100.00"),
            iva=Decimal("22.00"),
            totale=Decimal("122.00"),
        )
        db.add(fattura)
        db.flush()

        # Add line item
        riga = RigaFattura(
            fattura_id=fattura.id,
            numero_riga=1,
            descrizione="Test Service",
            quantita=Decimal("1.0"),
            prezzo_unitario=Decimal("100.00"),
            aliquota_iva=Decimal("22.00"),
            imponibile=Decimal("100.00"),
            iva=Decimal("22.00"),
            totale=Decimal("122.00"),
        )
        db.add(riga)
        db.commit()
        db.refresh(fattura)

        # Publish validation event (simulating XML generation success)
        from openfatture.cli.lifespan import get_event_bus
        from openfatture.core.events import InvoiceValidatedEvent

        event_bus = get_event_bus()
        if event_bus:
            event_bus.publish(
                InvoiceValidatedEvent(
                    invoice_id=fattura.id,
                    invoice_number=f"{fattura.numero}/{fattura.anno}",
                    validation_status="passed",
                    issues=[],
                    xml_path="/tmp/test.xml",
                )
            )

        # Verify event was persisted
        repo = EventRepository()
        try:
            events = repo.get_by_event_type("InvoiceValidatedEvent")
            assert len(events) >= 1

            our_event = next((e for e in events if e.entity_id == fattura.id), None)
            assert our_event is not None
            assert our_event.entity_type == "invoice"

            import json

            event_data = json.loads(our_event.event_data)
            assert event_data["validation_status"] == "passed"
            assert event_data["issues"] == []

        finally:
            repo.close()

    finally:
        db.close()


def test_invoice_deletion_publishes_event(test_client, test_db):
    """Test that deleting an invoice publishes InvoiceDeletedEvent."""
    db = get_session()
    try:
        # Create invoice
        fattura = Fattura(
            numero="003",
            anno=date.today().year,
            data_emissione=date.today(),
            cliente_id=test_client,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("100.00"),
            iva=Decimal("22.00"),
            totale=Decimal("122.00"),
        )
        db.add(fattura)
        db.commit()
        db.refresh(fattura)

        invoice_id = fattura.id
        invoice_number = f"{fattura.numero}/{fattura.anno}"

        # Delete invoice
        db.delete(fattura)
        db.commit()

        # Publish deletion event (as the CLI does)
        from openfatture.cli.lifespan import get_event_bus
        from openfatture.core.events import InvoiceDeletedEvent

        event_bus = get_event_bus()
        if event_bus:
            event_bus.publish(
                InvoiceDeletedEvent(
                    invoice_id=invoice_id,
                    invoice_number=invoice_number,
                    reason="Test deletion",
                )
            )

        # Verify event was persisted
        repo = EventRepository()
        try:
            events = repo.get_by_event_type("InvoiceDeletedEvent")
            assert len(events) >= 1

            our_event = next((e for e in events if e.entity_id == invoice_id), None)
            assert our_event is not None
            assert our_event.entity_type == "invoice"

            import json

            event_data = json.loads(our_event.event_data)
            assert event_data["invoice_id"] == invoice_id
            assert event_data["invoice_number"] == invoice_number
            assert "reason" in event_data

        finally:
            repo.close()

    finally:
        db.close()


def test_invoice_sent_publishes_event(test_client, test_db):
    """Test that sending an invoice publishes InvoiceSentEvent."""
    db = get_session()
    try:
        # Create invoice
        fattura = Fattura(
            numero="004",
            anno=date.today().year,
            data_emissione=date.today(),
            cliente_id=test_client,
            stato=StatoFattura.DA_INVIARE,
            imponibile=Decimal("100.00"),
            iva=Decimal("22.00"),
            totale=Decimal("122.00"),
        )
        db.add(fattura)
        db.commit()
        db.refresh(fattura)

        # Publish sent event (simulating successful PEC send)
        from openfatture.cli.lifespan import get_event_bus
        from openfatture.core.events import InvoiceSentEvent

        event_bus = get_event_bus()
        if event_bus:
            event_bus.publish(
                InvoiceSentEvent(
                    invoice_id=fattura.id,
                    invoice_number=f"{fattura.numero}/{fattura.anno}",
                    recipient="ABCDEFG",
                    pec_address="sdi01@pec.fatturapa.it",
                    xml_path="/tmp/test.xml",
                    signed=False,
                )
            )

        # Verify event was persisted
        repo = EventRepository()
        try:
            events = repo.get_by_event_type("InvoiceSentEvent")
            assert len(events) >= 1

            our_event = next((e for e in events if e.entity_id == fattura.id), None)
            assert our_event is not None
            assert our_event.entity_type == "invoice"

            import json

            event_data = json.loads(our_event.event_data)
            assert event_data["recipient"] == "ABCDEFG"
            assert event_data["pec_address"] == "sdi01@pec.fatturapa.it"
            assert event_data["signed"] is False

        finally:
            repo.close()

    finally:
        db.close()


def test_invoice_timeline_shows_all_events(test_client, test_db):
    """Test that invoice timeline shows creation, validation, and sending events."""
    db = get_session()
    try:
        # Create invoice
        fattura = Fattura(
            numero="005",
            anno=date.today().year,
            data_emissione=date.today(),
            cliente_id=test_client,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("100.00"),
            iva=Decimal("22.00"),
            totale=Decimal("122.00"),
        )
        db.add(fattura)
        db.flush()

        # Add line item
        riga = RigaFattura(
            fattura_id=fattura.id,
            numero_riga=1,
            descrizione="Test Service",
            quantita=Decimal("1.0"),
            prezzo_unitario=Decimal("100.00"),
            aliquota_iva=Decimal("22.00"),
            imponibile=Decimal("100.00"),
            iva=Decimal("22.00"),
            totale=Decimal("122.00"),
        )
        db.add(riga)
        db.commit()
        db.refresh(fattura)

        # Publish multiple events
        from openfatture.cli.lifespan import get_event_bus
        from openfatture.core.events import (
            InvoiceCreatedEvent,
            InvoiceSentEvent,
            InvoiceValidatedEvent,
        )

        event_bus = get_event_bus()
        if event_bus:
            # Creation
            event_bus.publish(
                InvoiceCreatedEvent(
                    invoice_id=fattura.id,
                    invoice_number=f"{fattura.numero}/{fattura.anno}",
                    client_id=test_client,
                    client_name="Test Client S.r.l.",
                    total_amount=fattura.totale,
                )
            )

            # Validation
            event_bus.publish(
                InvoiceValidatedEvent(
                    invoice_id=fattura.id,
                    invoice_number=f"{fattura.numero}/{fattura.anno}",
                    validation_status="passed",
                    issues=[],
                )
            )

            # Sent
            event_bus.publish(
                InvoiceSentEvent(
                    invoice_id=fattura.id,
                    invoice_number=f"{fattura.numero}/{fattura.anno}",
                    recipient="ABCDEFG",
                    pec_address="sdi01@pec.fatturapa.it",
                    xml_path="/tmp/test.xml",
                )
            )

        # Get timeline
        repo = EventRepository()
        try:
            timeline = repo.get_timeline("invoice", fattura.id)

            # Should have at least 3 events
            assert len(timeline) >= 3

            # Check event types are present
            event_types = [e["event_type"] for e in timeline]
            assert "InvoiceCreatedEvent" in event_types
            assert "InvoiceValidatedEvent" in event_types
            assert "InvoiceSentEvent" in event_types

            # Events should be in chronological order (most recent first)
            assert timeline[0]["timestamp"] >= timeline[-1]["timestamp"]

        finally:
            repo.close()

    finally:
        db.close()
