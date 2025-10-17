"""Invoice service adapter for Streamlit web interface.

Provides caching and simplified API for invoice operations.
"""

from datetime import date
from decimal import Decimal
from typing import Any

import streamlit as st

from openfatture.core.events.invoice_events import InvoiceCreatedEvent
from openfatture.core.fatture.service import InvoiceService as CoreInvoiceService
from openfatture.storage.database.models import Cliente, Fattura, RigaFattura, StatoFattura
from openfatture.utils.config import Settings, get_settings
from openfatture.web.utils.cache import db_session_scope, get_db_session
from openfatture.web.utils.lifespan import get_event_bus


class StreamlitInvoiceService:
    """Adapter service for invoice operations in Streamlit."""

    def __init__(self) -> None:
        """Initialize service with settings and core service."""
        self.settings: Settings = get_settings()
        self.core_service: CoreInvoiceService = CoreInvoiceService(self.settings)

    @st.cache_data(ttl=30, show_spinner=False)
    def get_invoices(
        _self,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get list of invoices with optional filters.

        Args:
            filters: Optional filters (e.g., {"stato": "bozza", "anno": 2024})
            limit: Maximum number of results

        Returns:
            List of invoice dictionaries with basic info
        """
        try:
            db = get_db_session()
            query = db.query(Fattura).order_by(Fattura.anno.desc(), Fattura.numero.desc())

            # Apply filters
            if filters:
                if "stato" in filters:
                    try:
                        query = query.filter(Fattura.stato == StatoFattura(filters["stato"]))
                    except ValueError as e:
                        from openfatture.web.utils.logging_config import log_error

                        log_error(e, "get_invoices", {"invalid_stato": filters["stato"]})
                        # Continue without filter
                if "anno" in filters:
                    query = query.filter(Fattura.anno == filters["anno"])
                if "cliente_id" in filters:
                    query = query.filter(Fattura.cliente_id == filters["cliente_id"])

            if limit:
                query = query.limit(limit)

            invoices = query.all()

            # Convert to dictionaries for serialization
            return [
                {
                    "id": f.id,
                    "numero": f.numero,
                    "anno": f.anno,
                    "data_emissione": f.data_emissione,
                    "cliente_denominazione": f.cliente.denominazione if f.cliente else "N/A",
                    "totale": float(f.totale),
                    "stato": f.stato.value,
                    "num_righe": len(f.righe),
                }
                for f in invoices
            ]
        except Exception as e:
            from openfatture.web.utils.logging_config import log_error

            log_error(e, "get_invoices", {"filters": filters, "limit": limit})
            # Return empty list on error
            return []

    def get_invoice_detail(self, invoice_id: int) -> Fattura | None:
        """
        Get detailed invoice by ID.

        Args:
            invoice_id: Invoice ID

        Returns:
            Fattura object or None if not found
        """
        db = get_db_session()
        return db.query(Fattura).filter(Fattura.id == invoice_id).first()

    def create_invoice(
        self,
        cliente_id: int,
        numero: str,
        anno: int,
        data_emissione: date,
        righe_data: list[dict[str, Any]],
    ) -> Fattura | None:
        """
        Create a new invoice with line items.

        Uses explicit session management with automatic commit/rollback.

        Args:
            cliente_id: Client ID
            numero: Invoice number
            anno: Year
            data_emissione: Issue date
            righe_data: List of line item data dicts

        Returns:
            Created Fattura object or None on error

        Raises:
            ValueError: If validation fails
        """
        try:
            # Use context manager for write operations (Best Practice 2025)
            with db_session_scope() as db:
                # Validate cliente
                cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
                if not cliente:
                    raise ValueError(f"Cliente {cliente_id} non trovato")

                # Validate righe_data
                if not righe_data:
                    raise ValueError("Almeno una riga è richiesta")

                # Create invoice
                fattura = Fattura(
                    numero=numero,
                    anno=anno,
                    data_emissione=data_emissione,
                    cliente_id=cliente_id,
                    stato=StatoFattura.BOZZA,
                )

                db.add(fattura)
                db.flush()  # Get ID

                # Add line items
                totale_imponibile = Decimal("0")
                totale_iva = Decimal("0")

                for i, riga_data in enumerate(righe_data, start=1):
                    try:
                        quantita = Decimal(str(riga_data["quantita"]))
                        prezzo = Decimal(str(riga_data["prezzo_unitario"]))
                        aliquota_iva = Decimal(str(riga_data["aliquota_iva"]))

                        if quantita <= 0 or prezzo <= 0:
                            raise ValueError(f"Riga {i}: quantità e prezzo devono essere positivi")

                        imponibile = quantita * prezzo
                        iva = imponibile * aliquota_iva / Decimal("100")
                        totale = imponibile + iva

                        riga = RigaFattura(
                            fattura_id=fattura.id,
                            numero_riga=i,
                            descrizione=riga_data["descrizione"],
                            quantita=quantita,
                            prezzo_unitario=prezzo,
                            aliquota_iva=aliquota_iva,
                            imponibile=imponibile,
                            iva=iva,
                            totale=totale,
                        )

                        db.add(riga)
                        totale_imponibile += imponibile
                        totale_iva += iva

                    except (KeyError, ValueError, TypeError) as e:
                        raise ValueError(f"Errore nella riga {i}: {str(e)}")

                # Update invoice totals
                fattura.imponibile = totale_imponibile
                fattura.iva = totale_iva
                fattura.totale = totale_imponibile + totale_iva

                # Commit happens automatically via context manager
                # Get fresh instance for return (detached from session)
                fattura_id = fattura.id

            # Re-fetch with read session to return detached object
            db_read = get_db_session()
            result = db_read.query(Fattura).filter(Fattura.id == fattura_id).first()

            # Publish InvoiceCreatedEvent
            event_bus = get_event_bus()
            if event_bus and result:
                event_bus.publish(
                    InvoiceCreatedEvent(
                        invoice_id=result.id,
                        invoice_number=f"{result.numero}/{result.anno}",
                        client_id=result.cliente_id,
                        client_name=cliente.denominazione,
                        total_amount=result.totale,
                    )
                )

            # Clear cache
            st.cache_data.clear()

            return result

        except Exception as e:
            from openfatture.web.utils.logging_config import log_error

            log_error(
                e,
                "create_invoice",
                {
                    "cliente_id": cliente_id,
                    "numero": numero,
                    "anno": anno,
                    "righe_count": len(righe_data) if righe_data else 0,
                },
            )
            # Re-raise validation errors, return None for other errors
            if isinstance(e, ValueError):
                raise
            return None

    def generate_xml(self, fattura: Fattura, validate: bool = True) -> tuple[str, str | None]:
        """
        Generate FatturaPA XML for invoice.

        Args:
            fattura: Invoice object
            validate: Whether to validate against XSD

        Returns:
            Tuple of (xml_content, error_message)
        """
        return self.core_service.generate_xml(fattura, validate=validate)

    @st.cache_data(ttl=60, show_spinner=False)
    def get_invoice_stats(_self) -> dict[str, Any]:
        """
        Get invoice statistics.

        Returns:
            Dictionary with stats (total, by_status, revenue, etc.)
        """
        db = get_db_session()

        # Total invoices
        total = db.query(Fattura).count()

        # By status
        by_status: dict[str, int] = {}
        for stato in StatoFattura:
            count = db.query(Fattura).filter(Fattura.stato == stato).count()
            if count > 0:
                by_status[stato.value] = count

        # Revenue
        from datetime import datetime

        from sqlalchemy import extract, func

        now = datetime.now()

        total_revenue = db.query(func.sum(Fattura.totale)).scalar() or Decimal("0")
        year_revenue = db.query(func.sum(Fattura.totale)).filter(
            extract("year", Fattura.data_emissione) == now.year
        ).scalar() or Decimal("0")
        month_revenue = db.query(func.sum(Fattura.totale)).filter(
            extract("year", Fattura.data_emissione) == now.year,
            extract("month", Fattura.data_emissione) == now.month,
        ).scalar() or Decimal("0")

        return {
            "total": total,
            "by_status": by_status,
            "total_revenue": float(total_revenue),
            "year_revenue": float(year_revenue),
            "month_revenue": float(month_revenue),
        }

    @st.cache_data(ttl=300, show_spinner=False)
    def get_available_years(_self) -> list[int]:
        """
        Get list of years with invoices.

        Returns:
            Sorted list of years (descending)
        """
        db = get_db_session()
        years = db.query(Fattura.anno).distinct().order_by(Fattura.anno.desc()).all()
        return [year[0] for year in years]

    @st.cache_data(ttl=30, show_spinner=False)
    def get_next_invoice_number(_self, year: int) -> int:
        """
        Get the next available invoice number for the given year.

        Args:
            year: The year for which to get the next invoice number

        Returns:
            The next available invoice number
        """
        db = get_db_session()
        try:
            # Find the highest invoice number for the given year
            from sqlalchemy import func

            result = db.query(func.max(Fattura.numero)).filter(Fattura.anno == year).scalar()

            if result is None:
                return 1

            # Try to parse as integer, if it fails, increment by 1
            try:
                return int(result) + 1
            except (ValueError, TypeError):
                return 1

        finally:
            db.close()
