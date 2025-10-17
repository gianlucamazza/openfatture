"""Report service adapter for Streamlit web interface.

Provides simplified API for report generation and analytics.
"""

from datetime import date
from typing import Any

import streamlit as st

from openfatture.storage.database.models import Fattura, StatoFattura
from openfatture.utils.config import Settings, get_settings
from openfatture.web.utils.cache import get_db_session


class StreamlitReportService:
    """Adapter service for report operations in Streamlit."""

    def __init__(self) -> None:
        """Initialize service with settings."""
        self.settings: Settings = get_settings()

    @st.cache_data(ttl=300, show_spinner=False)  # 5 minutes cache for reports
    def get_revenue_report(self, year: int, quarter: str | None = None) -> dict[str, Any]:
        """
        Generate revenue report for year/quarter.

        Args:
            year: Year for the report
            quarter: Optional quarter (Q1, Q2, Q3, Q4)

        Returns:
            Revenue report data
        """
        db = get_db_session()

        # Build date filters
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        if quarter:
            quarter_map = {"Q1": (1, 3), "Q2": (4, 6), "Q3": (7, 9), "Q4": (10, 12)}
            if quarter in quarter_map:
                start_month, end_month = quarter_map[quarter]
                start_date = date(year, start_month, 1)
                end_date = date(year, end_month + 1, 1) if end_month < 12 else date(year + 1, 1, 1)
                end_date = end_date.replace(day=end_date.day - 1)

        # Query invoices
        query = db.query(Fattura).filter(
            Fattura.data_emissione >= start_date,
            Fattura.data_emissione <= end_date,
            Fattura.stato.in_([StatoFattura.CONSEGNATA, StatoFattura.ACCETTATA]),
        )

        invoices = query.all()

        # Calculate totals
        total_revenue = sum(float(f.totale) for f in invoices)
        total_vat = sum(float(f.iva) for f in invoices)
        total_invoices = len(invoices)

        # Monthly breakdown
        monthly_data = {}
        for month in range(1, 13):
            month_start = date(year, month, 1)
            month_end = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
            month_end = month_end.replace(day=month_end.day - 1)

            if quarter:
                if not (start_date <= month_start <= end_date):
                    continue

            month_invoices = [f for f in invoices if month_start <= f.data_emissione <= month_end]
            monthly_data[month] = {
                "revenue": sum(float(f.totale) for f in month_invoices),
                "invoices": len(month_invoices),
            }

        return {
            "period": f"{quarter} {year}" if quarter else str(year),
            "total_revenue": total_revenue,
            "total_vat": total_vat,
            "total_invoices": total_invoices,
            "monthly_breakdown": monthly_data,
            "avg_invoice_value": total_revenue / total_invoices if total_invoices > 0 else 0,
        }

    @st.cache_data(ttl=300, show_spinner=False)
    def get_vat_report(self, year: int, quarter: str | None = None) -> dict[str, Any]:
        """
        Generate VAT report for year/quarter.

        Args:
            year: Year for the report
            quarter: Optional quarter (Q1, Q2, Q3, Q4)

        Returns:
            VAT report data
        """
        db = get_db_session()

        # Build date filters (same as revenue report)
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        if quarter:
            quarter_map = {"Q1": (1, 3), "Q2": (4, 6), "Q3": (7, 9), "Q4": (10, 12)}
            if quarter in quarter_map:
                start_month, end_month = quarter_map[quarter]
                start_date = date(year, start_month, 1)
                end_date = date(year, end_month + 1, 1) if end_month < 12 else date(year + 1, 1, 1)
                end_date = end_date.replace(day=end_date.day - 1)

        # Query invoices
        query = db.query(Fattura).filter(
            Fattura.data_emissione >= start_date,
            Fattura.data_emissione <= end_date,
            Fattura.stato.in_([StatoFattura.CONSEGNATA, StatoFattura.ACCETTATA]),
        )

        invoices = query.all()

        # Group by VAT rate
        vat_rates = {}
        for invoice in invoices:
            for riga in invoice.righe:
                rate = float(riga.aliquota_iva)
                amount = float(riga.prezzo_unitario * riga.quantita)
                vat_amount = amount * rate / 100

                if rate not in vat_rates:
                    vat_rates[rate] = {"imponibile": 0.0, "iva": 0.0}

                vat_rates[rate]["imponibile"] += amount
                vat_rates[rate]["iva"] += vat_amount

        # Calculate totals
        total_imponibile = sum(data["imponibile"] for data in vat_rates.values())
        total_iva = sum(data["iva"] for data in vat_rates.values())

        return {
            "period": f"{quarter} {year}" if quarter else str(year),
            "vat_breakdown": vat_rates,
            "total_imponibile": total_imponibile,
            "total_iva": total_iva,
            "total_fatturato": total_imponibile + total_iva,
        }

    @st.cache_data(ttl=300, show_spinner=False)
    def get_client_report(self, year: int) -> dict[str, Any]:
        """
        Generate client activity report for year.

        Args:
            year: Year for the report

        Returns:
            Client report data
        """
        db = get_db_session()

        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        # Query invoices with client info
        query = db.query(Fattura).filter(
            Fattura.data_emissione >= start_date,
            Fattura.data_emissione <= end_date,
            Fattura.stato.in_([StatoFattura.CONSEGNATA, StatoFattura.ACCETTATA]),
        )

        invoices = query.all()

        # Group by client
        client_data = {}
        for invoice in invoices:
            if invoice.cliente:
                client_name = invoice.cliente.denominazione
                if client_name not in client_data:
                    client_data[client_name] = {"invoices": 0, "total": 0.0, "last_invoice": None}

                client_data[client_name]["invoices"] += 1
                client_data[client_name]["total"] += float(invoice.totale or 0)
                if (
                    not client_data[client_name]["last_invoice"]
                    or invoice.data_emissione > client_data[client_name]["last_invoice"]
                ):
                    client_data[client_name]["last_invoice"] = invoice.data_emissione

        # Sort by total descending
        sorted_clients = sorted(client_data.items(), key=lambda x: x[1]["total"], reverse=True)[
            :20
        ]  # Top 20 clients

        return {
            "year": year,
            "total_clients": len(client_data),
            "top_clients": dict(sorted_clients),
        }

    def get_available_years(self) -> list[int]:
        """
        Get list of years with invoice data.

        Returns:
            List of years
        """
        db = get_db_session()
        years = db.query(Fattura.anno).distinct().order_by(Fattura.anno.desc()).all()
        return [year[0] for year in years]
