"""Tools for batch operations on invoices and clients."""

from pathlib import Path
from typing import Any

from pydantic import validate_call

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.core.batch.operations import (
    bulk_update_status,
    export_invoices_csv,
    import_invoices_csv,
)
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Cliente, Fattura, StatoFattura
from openfatture.utils.logging import get_logger
from openfatture.utils.security import validate_integer_input

logger = get_logger(__name__)


# =============================================================================
# Export Tools
# =============================================================================


@validate_call
def export_invoices_to_csv(
    output_path: str,
    anno: int | None = None,
    cliente_id: int | None = None,
    include_lines: bool = False,
) -> dict[str, Any]:
    """
    Export invoices to CSV file.

    Args:
        output_path: Path to output CSV file (absolute or relative)
        anno: Filter by year (optional)
        cliente_id: Filter by client ID (optional)
        include_lines: Include invoice line items in separate rows

    Returns:
        Dictionary with export result
    """
    # Validate inputs
    if anno is not None:
        anno = validate_integer_input(anno, min_value=2000, max_value=2100)
    if cliente_id is not None:
        cliente_id = validate_integer_input(cliente_id, min_value=1)

    db = get_session()
    try:
        # Build query
        query = db.query(Fattura).filter(Fattura.stato != StatoFattura.BOZZA)

        if anno:
            query = query.filter(Fattura.anno == anno)
        if cliente_id:
            query = query.filter(Fattura.cliente_id == cliente_id)

        fatture = query.all()

        if not fatture:
            return {
                "success": False,
                "error": "No invoices found matching criteria",
                "exported_count": 0,
            }

        # Export to CSV
        output_file = Path(output_path)
        success, error = export_invoices_csv(
            invoices=fatture,
            output_path=output_file,
            include_lines=include_lines,
        )

        if success:
            logger.info(
                "invoices_exported_to_csv",
                count=len(fatture),
                output_path=str(output_file),
            )

            return {
                "success": True,
                "exported_count": len(fatture),
                "output_path": str(output_file.absolute()),
                "include_lines": include_lines,
            }
        else:
            return {
                "success": False,
                "error": error,
                "exported_count": 0,
            }

    except Exception as e:
        logger.error("export_invoices_to_csv_failed", error=str(e))
        return {"success": False, "error": str(e), "exported_count": 0}
    finally:
        db.close()


@validate_call
def export_clients_to_csv(
    output_path: str,
) -> dict[str, Any]:
    """
    Export all clients to CSV file.

    Args:
        output_path: Path to output CSV file

    Returns:
        Dictionary with export result
    """
    import csv

    db = get_session()
    try:
        # Get all clients
        clienti = db.query(Cliente).order_by(Cliente.denominazione).all()

        if not clienti:
            return {
                "success": False,
                "error": "No clients found",
                "exported_count": 0,
            }

        # Write CSV
        output_file = Path(output_path)
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "id",
                "denominazione",
                "partita_iva",
                "codice_fiscale",
                "email",
                "pec",
                "indirizzo",
                "cap",
                "comune",
                "provincia",
                "nazione",
                "codice_destinatario",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for cliente in clienti:
                writer.writerow(
                    {
                        "id": cliente.id,
                        "denominazione": cliente.denominazione,
                        "partita_iva": cliente.partita_iva or "",
                        "codice_fiscale": cliente.codice_fiscale or "",
                        "email": cliente.email or "",
                        "pec": cliente.pec or "",
                        "indirizzo": cliente.indirizzo or "",
                        "cap": cliente.cap or "",
                        "comune": cliente.comune or "",
                        "provincia": cliente.provincia or "",
                        "nazione": cliente.nazione or "IT",
                        "codice_destinatario": cliente.codice_destinatario or "0000000",
                    }
                )

        logger.info(
            "clients_exported_to_csv",
            count=len(clienti),
            output_path=str(output_file),
        )

        return {
            "success": True,
            "exported_count": len(clienti),
            "output_path": str(output_file.absolute()),
        }

    except Exception as e:
        logger.error("export_clients_to_csv_failed", error=str(e))
        return {"success": False, "error": str(e), "exported_count": 0}
    finally:
        db.close()


# =============================================================================
# Import Tools (WRITE operations)
# =============================================================================


@validate_call
def import_invoices_from_csv(
    csv_path: str,
    default_cliente_id: int | None = None,
) -> dict[str, Any]:
    """
    Import invoices from CSV file.

    CSV Format:
    numero,anno,data_emissione,cliente_id,imponibile,iva,totale,note

    Args:
        csv_path: Path to CSV file to import
        default_cliente_id: Default client ID if not in CSV (optional)

    Returns:
        Dictionary with import result
    """
    # Validate inputs
    if default_cliente_id is not None:
        default_cliente_id = validate_integer_input(default_cliente_id, min_value=1)

    db = get_session()
    try:
        csv_file = Path(csv_path)
        if not csv_file.exists():
            return {
                "success": False,
                "error": f"CSV file not found: {csv_path}",
                "imported_count": 0,
                "failed_count": 0,
            }

        # Import using batch operations
        result = import_invoices_csv(
            csv_path=csv_file,
            db_session=db,
            default_cliente_id=default_cliente_id,
        )

        logger.info(
            "invoices_imported_from_csv",
            succeeded=result.succeeded,
            failed=result.failed,
            csv_path=str(csv_file),
        )

        return {
            "success": result.succeeded > 0,
            "imported_count": result.succeeded,
            "failed_count": result.failed,
            "total_rows": result.total,
            "errors": result.errors[:10],  # Limit errors to first 10
            "message": f"Imported {result.succeeded}/{result.total} invoices",
        }

    except Exception as e:
        logger.error("import_invoices_from_csv_failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "imported_count": 0,
            "failed_count": 0,
        }
    finally:
        db.close()


@validate_call
def import_clients_from_csv(
    csv_path: str,
) -> dict[str, Any]:
    """
    Import clients from CSV file.

    CSV Format:
    denominazione,partita_iva,codice_fiscale,email,pec,indirizzo,cap,comune,provincia,nazione,codice_destinatario

    Args:
        csv_path: Path to CSV file to import

    Returns:
        Dictionary with import result
    """
    import csv

    db = get_session()
    try:
        csv_file = Path(csv_path)
        if not csv_file.exists():
            return {
                "success": False,
                "error": f"CSV file not found: {csv_path}",
                "imported_count": 0,
                "failed_count": 0,
            }

        imported = 0
        failed = 0
        errors = []

        with open(csv_file, encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, 1):
                try:
                    # Validate required fields
                    denominazione = row.get("denominazione")
                    if not denominazione:
                        raise ValueError("denominazione is required")

                    # At least one of partita_iva or codice_fiscale required
                    partita_iva = row.get("partita_iva") or None
                    codice_fiscale = row.get("codice_fiscale") or None

                    if not partita_iva and not codice_fiscale:
                        raise ValueError(
                            "At least one of partita_iva or codice_fiscale is required"
                        )

                    # Create client
                    cliente = Cliente(
                        denominazione=denominazione,
                        partita_iva=partita_iva,
                        codice_fiscale=codice_fiscale,
                        email=row.get("email") or None,
                        pec=row.get("pec") or None,
                        indirizzo=row.get("indirizzo") or None,
                        cap=row.get("cap") or None,
                        comune=row.get("comune") or None,
                        provincia=row.get("provincia") or None,
                        nazione=row.get("nazione") or "IT",
                        codice_destinatario=row.get("codice_destinatario") or "0000000",
                    )

                    db.add(cliente)
                    db.flush()
                    imported += 1

                except Exception as e:
                    failed += 1
                    errors.append(f"Row {row_num}: {str(e)}")
                    logger.warning("client_import_row_failed", row=row_num, error=str(e))

        # Commit if any succeeded
        if imported > 0:
            db.commit()

            logger.info(
                "clients_imported_from_csv",
                succeeded=imported,
                failed=failed,
                csv_path=str(csv_file),
            )

            return {
                "success": True,
                "imported_count": imported,
                "failed_count": failed,
                "total_rows": imported + failed,
                "errors": errors[:10],  # Limit errors
                "message": f"Imported {imported}/{imported + failed} clients",
            }
        else:
            db.rollback()
            return {
                "success": False,
                "error": "No clients imported successfully",
                "imported_count": 0,
                "failed_count": failed,
                "errors": errors[:10],
            }

    except Exception as e:
        db.rollback()
        logger.error("import_clients_from_csv_failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "imported_count": 0,
            "failed_count": 0,
        }
    finally:
        db.close()


# =============================================================================
# Bulk Update Tools (WRITE operations)
# =============================================================================


@validate_call
def bulk_update_invoices_status(
    anno: int,
    new_status: str,
    cliente_id: int | None = None,
) -> dict[str, Any]:
    """
    Bulk update invoice status for a year.

    Args:
        anno: Year to filter invoices
        new_status: New status (bozza, da_inviare, inviata, consegnata)
        cliente_id: Optional client filter

    Returns:
        Dictionary with update result
    """
    # Validate inputs
    anno = validate_integer_input(anno, min_value=2000, max_value=2100)
    if cliente_id is not None:
        cliente_id = validate_integer_input(cliente_id, min_value=1)

    # Validate status
    try:
        status_enum = StatoFattura(new_status.lower())
    except ValueError:
        return {
            "success": False,
            "error": f"Invalid status: {new_status}. Valid: bozza, da_inviare, inviata, consegnata",
            "updated_count": 0,
        }

    db = get_session()
    try:
        # Get invoices
        query = db.query(Fattura).filter(Fattura.anno == anno)

        if cliente_id:
            query = query.filter(Fattura.cliente_id == cliente_id)

        fatture = query.all()

        if not fatture:
            return {
                "success": False,
                "error": "No invoices found matching criteria",
                "updated_count": 0,
            }

        # Bulk update
        result = bulk_update_status(
            invoices=fatture,
            new_status=status_enum,
            db_session=db,
        )

        logger.info(
            "invoices_status_bulk_updated",
            anno=anno,
            new_status=new_status,
            updated=result.succeeded,
            failed=result.failed,
        )

        return {
            "success": result.succeeded > 0,
            "updated_count": result.succeeded,
            "failed_count": result.failed,
            "new_status": new_status,
            "errors": result.errors[:10],
            "message": f"Updated {result.succeeded}/{result.total} invoices to {new_status}",
        }

    except Exception as e:
        logger.error("bulk_update_invoices_status_failed", error=str(e))
        return {"success": False, "error": str(e), "updated_count": 0}
    finally:
        db.close()


# =============================================================================
# Tool Definitions
# =============================================================================


def get_batch_tools() -> list[Tool]:
    """
    Get all batch operation tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="export_invoices_to_csv",
            description="Export invoices to CSV file with optional filters (year, client)",
            category="batch",
            parameters=[
                ToolParameter(
                    name="output_path",
                    type=ToolParameterType.STRING,
                    description="Path to output CSV file",
                    required=True,
                ),
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Filter by year (optional)",
                    required=False,
                ),
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Filter by client ID (optional)",
                    required=False,
                ),
                ToolParameter(
                    name="include_lines",
                    type=ToolParameterType.BOOLEAN,
                    description="Include invoice line items in separate rows",
                    required=False,
                    default=False,
                ),
            ],
            func=export_invoices_to_csv,
            examples=[
                "export_invoices_to_csv(output_path='invoices_2025.csv', anno=2025)",
                "export_invoices_to_csv(output_path='exports/all.csv', include_lines=True)",
            ],
            tags=["export", "csv", "batch", "invoice"],
        ),
        Tool(
            name="export_clients_to_csv",
            description="Export all clients to CSV file",
            category="batch",
            parameters=[
                ToolParameter(
                    name="output_path",
                    type=ToolParameterType.STRING,
                    description="Path to output CSV file",
                    required=True,
                ),
            ],
            func=export_clients_to_csv,
            examples=["export_clients_to_csv(output_path='clients.csv')"],
            tags=["export", "csv", "batch", "client"],
        ),
        Tool(
            name="import_invoices_from_csv",
            description="Import invoices from CSV file (creates new invoices as drafts)",
            category="batch",
            parameters=[
                ToolParameter(
                    name="csv_path",
                    type=ToolParameterType.STRING,
                    description="Path to CSV file to import",
                    required=True,
                ),
                ToolParameter(
                    name="default_cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Default client ID if not in CSV (optional)",
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
            description="Import clients from CSV file (creates new clients)",
            category="batch",
            parameters=[
                ToolParameter(
                    name="csv_path",
                    type=ToolParameterType.STRING,
                    description="Path to CSV file to import",
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
            description="Bulk update invoice status for multiple invoices at once",
            category="batch",
            parameters=[
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Year to filter invoices",
                    required=True,
                ),
                ToolParameter(
                    name="new_status",
                    type=ToolParameterType.STRING,
                    description="New status to set",
                    required=True,
                    enum=["bozza", "da_inviare", "inviata", "consegnata"],
                ),
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Optional client filter",
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
