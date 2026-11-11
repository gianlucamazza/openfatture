"""AI tool adapters over `openfatture.billing.application.batch_ops`."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.ai.tools.output_paths import confined_output
from openfatture.billing.application.batch_ops import (
    bulk_update_invoices_status,
    export_clients_to_csv,
    export_invoices_to_csv,
    import_clients_from_csv,
    import_invoices_from_csv,
)


def get_batch_tools() -> list[Tool]:
    """
    Get all batch operation tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="export_invoices_to_csv",
            risk=ToolRisk.LOCAL_ARTIFACT,
            description=(
                "Write invoices in every state except bozza to a CSV file in the exports "
                "directory and return exported_count and the absolute output_path. Without "
                "include_lines there is one row per invoice with columns numero, anno, "
                "data_emissione, cliente, stato, imponibile, iva, totale and note; with "
                "include_lines there is one row per line item, adding riga_descrizione, "
                "riga_quantita, riga_prezzo_unitario and riga_aliquota_iva and dropping note. An "
                "existing file at the path is overwritten. Returns an error when no invoice "
                "matches or the path resolves outside the exports directory."
            ),
            category="batch",
            parameters=[
                ToolParameter(
                    name="output_path",
                    type=ToolParameterType.STRING,
                    description=(
                        "CSV file path relative to the exports directory; missing subfolders "
                        "are created; absolute paths or .. are accepted only inside that directory"
                    ),
                    required=True,
                ),
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Invoice year, 2000 to 2100; omit for all years",
                    required=False,
                ),
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Only invoices of this client id; omit for all clients",
                    required=False,
                ),
                ToolParameter(
                    name="include_lines",
                    type=ToolParameterType.BOOLEAN,
                    description=(
                        "true for one row per line item (an invoice without lines still gets one "
                        "row); default false, one row per invoice"
                    ),
                    required=False,
                    default=False,
                ),
            ],
            func=confined_output(export_invoices_to_csv),
            examples=[
                "export_invoices_to_csv(output_path='invoices_2025.csv', anno=2025)",
                "export_invoices_to_csv(output_path='exports/all.csv', include_lines=True)",
            ],
            tags=["export", "csv", "batch", "invoice"],
        ),
        Tool(
            name="export_clients_to_csv",
            risk=ToolRisk.LOCAL_ARTIFACT,
            description=(
                "Write every client, ordered by name, to a CSV file in the exports directory and "
                "return exported_count and the absolute output_path. Columns: id, denominazione, "
                "partita_iva, codice_fiscale, email, pec, indirizzo, cap, comune, provincia, "
                "nazione and codice_destinatario (0000000 when empty); phone and notes are not "
                "exported. The file can be read back by import_clients_from_csv. An existing file "
                "at the path is overwritten. Returns an error when there are no clients or the "
                "path resolves outside the exports directory."
            ),
            category="batch",
            parameters=[
                ToolParameter(
                    name="output_path",
                    type=ToolParameterType.STRING,
                    description=(
                        "CSV file path relative to the exports directory; missing subfolders "
                        "are created; absolute paths or .. are accepted only inside that directory"
                    ),
                    required=True,
                ),
            ],
            func=confined_output(export_clients_to_csv),
            examples=["export_clients_to_csv(output_path='clients.csv')"],
            tags=["export", "csv", "batch", "client"],
        ),
        Tool(
            name="import_invoices_from_csv",
            risk=ToolRisk.MUTATE,
            description=(
                "Create draft (bozza) invoice headers from a UTF-8 CSV with a header row and "
                "columns numero, anno, data_emissione (YYYY-MM-DD), cliente_id, imponibile, iva, "
                "totale and optional note. Amounts are stored as given, not recomputed, and no "
                "line items are created, so the drafts need lines before they can be sent. A row "
                "fails for an unknown client, an existing numero/anno, or a missing or unparsable "
                "value; failed rows are skipped and the valid rows are committed. Returns "
                "imported_count, failed_count, total_rows and the first 10 errors."
            ),
            category="batch",
            parameters=[
                ToolParameter(
                    name="csv_path",
                    type=ToolParameterType.STRING,
                    description=(
                        "Path to the CSV file, absolute or relative to the current working "
                        "directory"
                    ),
                    required=True,
                ),
                ToolParameter(
                    name="default_cliente_id",
                    type=ToolParameterType.INTEGER,
                    description=(
                        "Client id used for every row when the CSV has no cliente_id column; an "
                        "empty cliente_id cell still fails its row"
                    ),
                    required=False,
                ),
            ],
            func=import_invoices_from_csv,
            requires_confirmation=True,
            examples=["import_invoices_from_csv(csv_path='invoices.csv')"],
            tags=["import", "csv", "batch", "invoice", "write"],
        ),
        Tool(
            name="import_clients_from_csv",
            risk=ToolRisk.MUTATE,
            description=(
                "Create clients from a UTF-8 CSV with a header row. Recognised columns: "
                "denominazione (required), partita_iva and codice_fiscale (at least one per row), "
                "email, pec, indirizzo, cap, comune, provincia, nazione (default IT) and "
                "codice_destinatario (default 0000000); other columns, such as id, are ignored. "
                "Unlike create_client it does not look for an existing client with the same "
                "partita IVA or codice fiscale, so importing the same rows twice creates "
                "duplicates; check with search_clients first. Failed rows are skipped and the "
                "valid rows are committed. Returns imported_count, failed_count, total_rows and "
                "the first 10 errors."
            ),
            category="batch",
            parameters=[
                ToolParameter(
                    name="csv_path",
                    type=ToolParameterType.STRING,
                    description=(
                        "Path to the CSV file, absolute or relative to the current working "
                        "directory"
                    ),
                    required=True,
                ),
            ],
            func=import_clients_from_csv,
            requires_confirmation=True,
            examples=["import_clients_from_csv(csv_path='clients.csv')"],
            tags=["import", "csv", "batch", "client", "write"],
        ),
        Tool(
            name="bulk_update_invoices_status",
            risk=ToolRisk.MUTATE,
            description=(
                "Set the status of every invoice of one year, optionally of one client, as a "
                "single all-or-nothing change. Only manual changes between bozza and da_inviare "
                "are possible: if any selected invoice is in another state, is historical (issued "
                "elsewhere), or fails the da_inviare checks (client, line items and FatturaPA XML "
                "passing XSD validation), nothing changes and every invoice is reported as "
                "failed. Invoices already in the target state count as updated. Sent and "
                "delivered states are set only by SDI transmission and receipts. Returns "
                "updated_count, failed_count and the first 10 errors."
            ),
            category="batch",
            parameters=[
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description=(
                        "Invoice year, 2000 to 2100; every invoice of that year is selected"
                    ),
                    required=True,
                ),
                ToolParameter(
                    name="new_status",
                    type=ToolParameterType.STRING,
                    description=(
                        "Target status: bozza or da_inviare (sent and delivered states come from "
                        "SDI, not from this tool)"
                    ),
                    required=True,
                    enum=["bozza", "da_inviare"],
                ),
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Restrict the selection to invoices of this client id",
                    required=False,
                ),
            ],
            func=bulk_update_invoices_status,
            requires_confirmation=True,
            examples=[
                "bulk_update_invoices_status(anno=2024, new_status='da_inviare')",
                "bulk_update_invoices_status(anno=2025, new_status='consegnata', cliente_id=5)",
            ],
            tags=["bulk", "update", "invoice", "write"],
        ),
    ]
