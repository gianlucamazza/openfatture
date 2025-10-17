"""Client service adapter for Streamlit web interface.

Provides caching and simplified API for client operations.
"""

from typing import Any

import streamlit as st

from openfatture.core.events.client_events import ClientCreatedEvent
from openfatture.storage.database.models import Cliente
from openfatture.utils.config import Settings, get_settings
from openfatture.web.utils.cache import get_db_session
from openfatture.web.utils.lifespan import get_event_bus


class StreamlitClientService:
    """Adapter service for client operations in Streamlit."""

    def __init__(self) -> None:
        """Initialize service with settings."""
        self.settings: Settings = get_settings()

    @st.cache_data(ttl=60, show_spinner=False)  # Longer TTL for clients (less volatile)
    def get_clients(
        _self,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get list of clients with optional filters and search.

        Args:
            filters: Optional filters (e.g., {"regime_fiscale": "RF01"})
            limit: Maximum number of results
            search: Search term for denominazione or P.IVA

        Returns:
            List of client dictionaries with basic info
        """
        db = get_db_session()
        query = db.query(Cliente).order_by(Cliente.denominazione)

        # Apply filters
        if filters:
            # Add filters here as needed
            pass

        # Apply search
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Cliente.denominazione.ilike(search_term))
                | (Cliente.partita_iva.ilike(search_term))
                | (Cliente.codice_fiscale.ilike(search_term))
            )

        if limit:
            query = query.limit(limit)

        clients = query.all()

        # Convert to dictionaries for serialization
        return [
            {
                "id": c.id,
                "denominazione": c.denominazione,
                "partita_iva": c.partita_iva,
                "codice_fiscale": c.codice_fiscale,
                "codice_destinatario": c.codice_destinatario,
                "pec": c.pec,
                "indirizzo": c.indirizzo,
                "cap": c.cap,
                "comune": c.comune,
                "provincia": c.provincia,
                "telefono": c.telefono,
                "email": c.email,
                "created_at": c.created_at,
            }
            for c in clients
        ]

    def get_client_detail(self, client_id: int) -> Cliente | None:
        """
        Get detailed client by ID.

        Args:
            client_id: Client ID

        Returns:
            Cliente object or None if not found
        """
        db = get_db_session()
        return db.query(Cliente).filter(Cliente.id == client_id).first()

    def create_client(self, client_data: dict[str, Any]) -> Cliente:
        """
        Create a new client.

        Args:
            client_data: Client data dictionary

        Returns:
            Created Cliente object
        """
        db = get_db_session()

        # Create client object
        client = Cliente(
            denominazione=client_data["denominazione"],
            partita_iva=client_data.get("partita_iva"),
            codice_fiscale=client_data.get("codice_fiscale"),
            codice_destinatario=client_data.get("codice_destinatario"),
            pec=client_data.get("pec"),
            indirizzo=client_data.get("indirizzo"),
            numero_civico=client_data.get("numero_civico"),
            cap=client_data.get("cap"),
            comune=client_data.get("comune"),
            provincia=client_data.get("provincia"),
            nazione=client_data.get("nazione", "IT"),
            telefono=client_data.get("telefono"),
            email=client_data.get("email"),
            note=client_data.get("note"),
        )

        db.add(client)
        db.commit()
        db.refresh(client)

        # Publish ClientCreatedEvent
        event_bus = get_event_bus()
        if event_bus:
            event_bus.publish(
                ClientCreatedEvent(
                    client_id=client.id,
                    client_name=client.denominazione,
                    partita_iva=client.partita_iva,
                    codice_fiscale=client.codice_fiscale,
                    codice_destinatario=client.codice_destinatario,
                    pec=client.pec,
                )
            )

        # Clear cache after creation
        self._clear_clients_cache()

        return client

    def update_client(self, client_id: int, client_data: dict[str, Any]) -> Cliente | None:
        """
        Update an existing client.

        Args:
            client_id: Client ID to update
            client_data: Updated client data

        Returns:
            Updated Cliente object or None if not found
        """
        db = get_db_session()
        client = db.query(Cliente).filter(Cliente.id == client_id).first()

        if not client:
            return None

        # Update fields
        for key, value in client_data.items():
            if hasattr(client, key):
                setattr(client, key, value)

        db.commit()
        db.refresh(client)

        # Clear cache after update
        self._clear_clients_cache()

        return client

    def delete_client(self, client_id: int) -> bool:
        """
        Delete a client by ID.

        Args:
            client_id: Client ID to delete

        Returns:
            True if deleted, False if not found
        """
        db = get_db_session()
        client = db.query(Cliente).filter(Cliente.id == client_id).first()

        if not client:
            return False

        db.delete(client)
        db.commit()

        # Clear cache after deletion
        self._clear_clients_cache()

        return True

    def _clear_clients_cache(self) -> None:
        """Clear the clients cache to force refresh."""
        # This will be called by Streamlit's cache invalidation
        pass

    @st.cache_data(ttl=300, show_spinner=False)  # 5 minutes cache for stats
    def get_client_stats(_self) -> dict[str, Any]:
        """
        Get client statistics.

        Returns:
            Dictionary with client statistics
        """
        db = get_db_session()

        total_clients = db.query(Cliente).count()

        # Count with PEC configured
        pec_count = db.query(Cliente).filter(Cliente.pec.isnot(None)).count()

        # Count with SDI code
        sdi_count = db.query(Cliente).filter(Cliente.codice_destinatario.isnot(None)).count()

        # Count with partita IVA
        piva_count = db.query(Cliente).filter(Cliente.partita_iva.isnot(None)).count()

        return {
            "total_clients": total_clients,
            "clients_with_pec": pec_count,
            "clients_with_sdi": sdi_count,
            "clients_with_piva": piva_count,
        }
