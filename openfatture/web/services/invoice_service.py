"""Invoice service adapter for Streamlit web interface.

Provides caching and simplified API for invoice operations.
"""

import streamlit as st
from datetime import date
from decimal import Decimal
from typing import Any

from openfatture.core.fatture.service import InvoiceService as CoreInvoiceService
from openfatture.storage.database.models import Cliente, Fattura, RigaFattura, StatoFattura
from openfatture.utils.config import Settings, get_settings
from openfatture.web.utils.cache import get_db_session


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
        db = get_db_session()
        query = db.query(Fattura).order_by(Fattura.anno.desc(), Fattura.numero.desc())

        # Apply filters
        if filters:
            if "stato" in filters:
                query = query.filter(Fattura.stato == StatoFattura(filters["stato"]))
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
    ) -> Fattura:
        """
        Create a new invoice with line items.

        Args:
            cliente_id: Client ID
            numero: Invoice number
            anno: Year
            data_emissione: Issue date
            righe_data: List of line item data dicts

        Returns:
            Created Fattura object

        Raises:
            ValueError: If validation fails
        """
        db = get_db_session()

        # Validate cliente
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            raise ValueError(f"Cliente {cliente_id} non trovato")

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
            quantita = Decimal(str(riga_data["quantita"]))
            prezzo = Decimal(str(riga_data["prezzo_unitario"]))
            aliquota_iva = Decimal(str(riga_data["aliquota_iva"]))

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

        # Update invoice totals
        fattura.imponibile = totale_imponibile
        fattura.iva = totale_iva
        fattura.totale = totale_imponibile + totale_iva

        db.commit()
        db.refresh(fattura)

        # Clear cache
        st.cache_data.clear()

        return fattura

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
        from sqlalchemy import func, extract
        from datetime import datetime

        now = datetime.now()

        total_revenue = db.query(func.sum(Fattura.totale)).scalar() or Decimal("0")
        year_revenue = (
            db.query(func.sum(Fattura.totale))
            .filter(extract("year", Fattura.data_emissione) == now.year)
            .scalar()
            or Decimal("0")
        )
        month_revenue = (
            db.query(func.sum(Fattura.totale))
            .filter(
                extract("year", Fattura.data_emissione) == now.year,
                extract("month", Fattura.data_emissione) == now.month,
            )
            .scalar()
            or Decimal("0")
        )

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
