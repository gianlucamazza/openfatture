"""Tools for generating business reports."""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import validate_call
from sqlalchemy import extract, func

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.payment.application.services.payment_overview import collect_payment_due_summary
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Cliente, Fattura, StatoFattura
from openfatture.utils.logging import get_logger
from openfatture.utils.security import validate_integer_input

logger = get_logger(__name__)


# =============================================================================
# Report Tools
# =============================================================================


@validate_call
def generate_vat_report(
    anno: int | None = None,
    trimestre: str | None = None,
) -> dict[str, Any]:
    """
    Generate VAT (IVA) report for a year or quarter.

    Args:
        anno: Year (current year if None)
        trimestre: Quarter (Q1, Q2, Q3, Q4) - full year if None

    Returns:
        Dictionary with VAT report data
    """
    # Validate inputs
    if anno is not None:
        anno = validate_integer_input(anno, min_value=2000, max_value=2100)
    else:
        anno = datetime.now().year

    db = get_session()
    try:
        # Determine quarter range
        if trimestre:
            quarter_months = {
                "Q1": (1, 3),
                "Q2": (4, 6),
                "Q3": (7, 9),
                "Q4": (10, 12),
            }

            trimestre_upper = trimestre.upper()
            if trimestre_upper not in quarter_months:
                return {"error": f"Invalid quarter: {trimestre}. Valid options: Q1, Q2, Q3, Q4"}

            mese_inizio, mese_fine = quarter_months[trimestre_upper]
            period = f"{trimestre_upper} ({mese_inizio}-{mese_fine})"
        else:
            mese_inizio, mese_fine = 1, 12
            period = "Full year"

        # Query invoices (exclude BOZZA)
        query = (
            db.query(Fattura)
            .filter(Fattura.anno == anno)
            .filter(Fattura.stato != StatoFattura.BOZZA)
        )

        # Filter by quarter if specified
        if trimestre:
            query = query.filter(
                extract("month", Fattura.data_emissione) >= mese_inizio,
                extract("month", Fattura.data_emissione) <= mese_fine,
            )

        fatture = query.all()

        if not fatture:
            return {
                "year": anno,
                "period": period,
                "invoices_count": 0,
                "total_imponibile": 0.0,
                "total_iva": 0.0,
                "total_revenue": 0.0,
                "by_vat_rate": [],
                "message": "No invoices found for the selected period",
            }

        # Calculate totals
        totale_imponibile = sum(f.imponibile for f in fatture)
        totale_iva = sum(f.iva for f in fatture)
        totale_fatturato = sum(f.totale for f in fatture)

        # Breakdown by VAT rate
        by_aliquota: dict[Decimal, dict[str, Decimal]] = defaultdict(
            lambda: {"imponibile": Decimal("0"), "iva": Decimal("0")}
        )

        for f in fatture:
            for riga in f.righe:
                aliquota = riga.aliquota_iva
                by_aliquota[aliquota]["imponibile"] += riga.imponibile
                by_aliquota[aliquota]["iva"] += riga.iva

        # Format breakdown
        vat_breakdown = []
        for aliquota in sorted(by_aliquota.keys()):
            data = by_aliquota[aliquota]
            vat_breakdown.append(
                {
                    "vat_rate": float(aliquota),
                    "imponibile": float(data["imponibile"]),
                    "iva": float(data["iva"]),
                }
            )

        logger.info(
            "vat_report_generated",
            year=anno,
            period=period,
            invoices_count=len(fatture),
        )

        return {
            "year": anno,
            "period": period,
            "invoices_count": len(fatture),
            "total_imponibile": float(totale_imponibile),
            "total_iva": float(totale_iva),
            "total_revenue": float(totale_fatturato),
            "by_vat_rate": vat_breakdown,
        }

    except Exception as e:
        logger.error("generate_vat_report_failed", error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


@validate_call
def generate_client_report(anno: int | None = None, limit: int = 20) -> dict[str, Any]:
    """
    Generate client revenue report (top clients by revenue).

    Args:
        anno: Year (current year if None)
        limit: Maximum number of clients to return

    Returns:
        Dictionary with client revenue data
    """
    # Validate inputs
    if anno is not None:
        anno = validate_integer_input(anno, min_value=2000, max_value=2100)
    else:
        anno = datetime.now().year

    limit = validate_integer_input(limit, min_value=1, max_value=100)

    db = get_session()
    try:
        # Query with aggregation
        results = (
            db.query(
                Fattura.cliente_id,
                func.count(Fattura.id).label("num_fatture"),
                func.sum(Fattura.totale).label("totale_fatturato"),
            )
            .filter(Fattura.anno == anno)
            .filter(Fattura.stato != StatoFattura.BOZZA)
            .group_by(Fattura.cliente_id)
            .order_by(func.sum(Fattura.totale).desc())
            .limit(limit)
            .all()
        )

        if not results:
            return {
                "year": anno,
                "clients_count": 0,
                "total_revenue": 0.0,
                "clients": [],
                "message": "No invoices found for the selected year",
            }

        # Format results
        clients = []
        for rank, (cliente_id, num_fatture, totale) in enumerate(results, 1):
            cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
            if cliente is None:
                # Skip if client was deleted
                continue

            clients.append(
                {
                    "rank": rank,
                    "client_id": cliente_id,
                    "client_name": cliente.denominazione,
                    "invoices_count": num_fatture,
                    "total_revenue": float(totale),
                }
            )

        # Calculate total
        totale_generale = sum(float(r[2]) for r in results)

        logger.info(
            "client_report_generated",
            year=anno,
            clients_count=len(clients),
        )

        return {
            "year": anno,
            "clients_count": len(clients),
            "total_revenue": totale_generale,
            "clients": clients,
        }

    except Exception as e:
        logger.error("generate_client_report_failed", error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


@validate_call
def get_due_dates(window_days: int = 14, max_results: int = 20) -> dict[str, Any]:
    """
    Get overdue and upcoming payment due dates.

    Args:
        window_days: Number of days to consider "due soon" (default: 14)
        max_results: Maximum number of upcoming payments to return

    Returns:
        Dictionary with payment due dates
    """
    # Validate inputs
    window_days = validate_integer_input(window_days, min_value=1, max_value=365)
    max_results = validate_integer_input(max_results, min_value=1, max_value=100)

    db = get_session()
    try:
        summary = collect_payment_due_summary(
            db,
            window_days=window_days,
            max_upcoming=max_results,
        )

        has_entries = any(summary.overdue or summary.due_soon or summary.upcoming)

        if not has_entries:
            return {
                "has_outstanding": False,
                "total_outstanding": 0.0,
                "overdue": [],
                "due_soon": [],
                "upcoming": [],
                "message": "No outstanding payments. All invoices are settled!",
            }

        # Format entries
        def format_entry(entry) -> dict[str, Any]:
            return {
                "invoice_ref": entry.invoice_ref,
                "client_name": entry.client_name,
                "due_date": entry.due_date.isoformat(),
                "days_delta": entry.days_delta,
                "residual": float(entry.residual),
                "paid": float(entry.paid),
                "total": float(entry.total),
                "status": entry.status.value,
            }

        result = {
            "has_outstanding": True,
            "total_outstanding": float(summary.total_outstanding),
            "window_days": window_days,
            "overdue": [format_entry(e) for e in summary.overdue],
            "due_soon": [format_entry(e) for e in summary.due_soon],
            "upcoming": [format_entry(e) for e in summary.upcoming],
            "hidden_upcoming": summary.hidden_upcoming,
        }

        # Add totals by category
        result["overdue_total"] = sum(float(e.residual) for e in summary.overdue)
        result["due_soon_total"] = sum(float(e.residual) for e in summary.due_soon)
        result["upcoming_total"] = sum(float(e.residual) for e in summary.upcoming)

        logger.info(
            "due_dates_report_generated",
            overdue_count=len(summary.overdue),
            due_soon_count=len(summary.due_soon),
            upcoming_count=len(summary.upcoming),
        )

        return result

    except Exception as e:
        logger.error("get_due_dates_failed", error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


# =============================================================================
# Tool Definitions
# =============================================================================


def get_report_tools() -> list[Tool]:
    """
    Get all report-related tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="generate_vat_report",
            description="Generate VAT (IVA) report for a year or quarter. Returns imponibile, IVA, revenue totals and breakdown by VAT rate.",
            category="reports",
            parameters=[
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Year (current year if not specified)",
                    required=False,
                ),
                ToolParameter(
                    name="trimestre",
                    type=ToolParameterType.STRING,
                    description="Quarter (Q1, Q2, Q3, Q4) - full year if not specified",
                    required=False,
                    enum=["Q1", "Q2", "Q3", "Q4"],
                ),
            ],
            func=generate_vat_report,
            examples=[
                "generate_vat_report()",
                "generate_vat_report(anno=2025)",
                "generate_vat_report(anno=2025, trimestre='Q1')",
            ],
            tags=["report", "vat", "iva", "tax"],
        ),
        Tool(
            name="generate_client_report",
            description="Generate client revenue report (top clients by revenue for a year)",
            category="reports",
            parameters=[
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Year (current year if not specified)",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum number of clients to return (default 20)",
                    required=False,
                    default=20,
                ),
            ],
            func=generate_client_report,
            examples=[
                "generate_client_report()",
                "generate_client_report(anno=2025)",
                "generate_client_report(anno=2024, limit=10)",
            ],
            tags=["report", "clients", "revenue"],
        ),
        Tool(
            name="get_due_dates",
            description="Get overdue and upcoming payment due dates. Returns overdue, due soon (within window), and upcoming payments.",
            category="reports",
            parameters=[
                ToolParameter(
                    name="window_days",
                    type=ToolParameterType.INTEGER,
                    description='Number of days to consider "due soon" (default 14)',
                    required=False,
                    default=14,
                ),
                ToolParameter(
                    name="max_results",
                    type=ToolParameterType.INTEGER,
                    description="Maximum number of upcoming payments to return (default 20)",
                    required=False,
                    default=20,
                ),
            ],
            func=get_due_dates,
            examples=[
                "get_due_dates()",
                "get_due_dates(window_days=21)",
                "get_due_dates(window_days=7, max_results=10)",
            ],
            tags=["report", "payment", "due", "overdue"],
        ),
    ]
