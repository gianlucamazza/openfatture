"""Tools for invoice operations (thin adapters).

Domain logic lives in application services:

- reads: ``billing.application.invoice_queries``
- writes: ``billing.application.invoice_commands``,
  ``billing.application.line_commands`` and ``billing.application.cassa_ops``
- SDI: ``sdi.application.invoice_sdi_ops``

Each adapter module defines its own ``tools()``; ``get_invoice_tools`` collects
them for the ToolRegistry.
"""

from openfatture.ai.tools.models import Tool

from . import cassa, invoices, line_helpers, nota_credito, queries, righe, sdi
from .cassa import set_cassa_previdenziale
from .invoices import (
    create_invoice,
    delete_invoice,
    update_invoice,
    update_invoice_status,
)
from .line_helpers import (
    create_course_line,
    format_course_description,
)
from .nota_credito import (
    create_nota_credito_from_fattura,
)
from .queries import (
    get_invoice_details,
    get_invoice_stats,
    search_invoices,
)
from .righe import (
    create_riga,
    delete_riga,
    update_riga,
)
from .sdi import (
    generate_invoice_xml,
    send_invoice_to_sdi,
)

__all__ = [
    "search_invoices",
    "get_invoice_details",
    "get_invoice_stats",
    "create_invoice",
    "create_nota_credito_from_fattura",
    "create_riga",
    "create_course_line",
    "format_course_description",
    "update_riga",
    "delete_riga",
    "generate_invoice_xml",
    "send_invoice_to_sdi",
    "update_invoice",
    "delete_invoice",
    "update_invoice_status",
    "set_cassa_previdenziale",
    "get_invoice_tools",
]


def get_invoice_tools() -> list[Tool]:
    """Get all invoice-related tools."""
    return [
        *queries.tools(),
        *invoices.tools(),
        *righe.tools(),
        *sdi.tools(),
        *nota_credito.tools(),
        *cassa.tools(),
        *line_helpers.tools(),
    ]
