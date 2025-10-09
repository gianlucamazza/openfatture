"""
Batch operations for invoices.

Provides high-level batch operations for import, export, validation, and sending.
"""

import csv
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from openfatture.core.batch.processor import BatchProcessor, BatchResult
from openfatture.sdi.validator.xsd_validator import FatturaPAValidator
from openfatture.storage.database.models import Cliente, Fattura, StatoFattura


def export_invoices_csv(
    invoices: list[Fattura],
    output_path: Path,
    include_lines: bool = False,
) -> tuple[bool, str | None]:
    """
    Export invoices to CSV file.

    Args:
        invoices: List of invoices to export
        output_path: Path to output CSV file
        include_lines: Whether to include invoice lines (separate rows)

    Returns:
        Tuple[bool, Optional[str]]: (success, error_message)
    """
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            if include_lines:
                # Export with invoice lines
                fieldnames = [
                    "numero",
                    "anno",
                    "data_emissione",
                    "cliente",
                    "stato",
                    "imponibile",
                    "iva",
                    "totale",
                    "riga_descrizione",
                    "riga_quantita",
                    "riga_prezzo_unitario",
                    "riga_aliquota_iva",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for fattura in invoices:
                    if fattura.righe:
                        for riga in fattura.righe:
                            writer.writerow(
                                {
                                    "numero": fattura.numero,
                                    "anno": fattura.anno,
                                    "data_emissione": fattura.data_emissione.isoformat(),
                                    "cliente": fattura.cliente.denominazione,
                                    "stato": fattura.stato.value,
                                    "imponibile": float(fattura.imponibile),
                                    "iva": float(fattura.iva),
                                    "totale": float(fattura.totale),
                                    "riga_descrizione": riga.descrizione,
                                    "riga_quantita": float(riga.quantita),
                                    "riga_prezzo_unitario": float(riga.prezzo_unitario),
                                    "riga_aliquota_iva": float(riga.aliquota_iva),
                                }
                            )
                    else:
                        # Invoice without lines
                        writer.writerow(
                            {
                                "numero": fattura.numero,
                                "anno": fattura.anno,
                                "data_emissione": fattura.data_emissione.isoformat(),
                                "cliente": fattura.cliente.denominazione,
                                "stato": fattura.stato.value,
                                "imponibile": float(fattura.imponibile),
                                "iva": float(fattura.iva),
                                "totale": float(fattura.totale),
                            }
                        )
            else:
                # Export summary only
                fieldnames = [
                    "numero",
                    "anno",
                    "data_emissione",
                    "cliente",
                    "stato",
                    "imponibile",
                    "iva",
                    "totale",
                    "note",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for fattura in invoices:
                    writer.writerow(
                        {
                            "numero": fattura.numero,
                            "anno": fattura.anno,
                            "data_emissione": fattura.data_emissione.isoformat(),
                            "cliente": fattura.cliente.denominazione,
                            "stato": fattura.stato.value,
                            "imponibile": float(fattura.imponibile),
                            "iva": float(fattura.iva),
                            "totale": float(fattura.totale),
                            "note": fattura.note or "",
                        }
                    )

        return True, None

    except Exception as e:
        return False, f"Export failed: {e}"


def import_invoices_csv(
    csv_path: Path,
    db_session: Session,
    default_cliente_id: int | None = None,
) -> BatchResult:
    """
    Import invoices from CSV file.

    CSV Format:
    numero,anno,data_emissione,cliente_id,imponibile,iva,totale,note

    Args:
        csv_path: Path to CSV file
        db_session: Database session
        default_cliente_id: Default client ID if not specified in CSV

    Returns:
        BatchResult with import summary
    """
    result = BatchResult(start_time=datetime.now())

    try:
        with open(csv_path, encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                result.total += 1

                try:
                    # Parse row
                    numero = row["numero"]
                    anno = int(row["anno"])
                    data_emissione = date.fromisoformat(row["data_emissione"])
                    cliente_id = int(row.get("cliente_id", default_cliente_id or 0))
                    imponibile = Decimal(row["imponibile"])
                    iva = Decimal(row["iva"])
                    totale = Decimal(row["totale"])
                    note = row.get("note", "")

                    # Validate client exists
                    cliente = db_session.query(Cliente).filter(Cliente.id == cliente_id).first()
                    if not cliente:
                        raise ValueError(f"Client {cliente_id} not found")

                    # Create invoice
                    fattura = Fattura(
                        numero=numero,
                        anno=anno,
                        data_emissione=data_emissione,
                        cliente_id=cliente_id,
                        imponibile=imponibile,
                        iva=iva,
                        totale=totale,
                        note=note,
                        stato=StatoFattura.BOZZA,
                    )

                    db_session.add(fattura)
                    db_session.flush()

                    result.add_success(fattura.id)

                except Exception as e:
                    result.add_failure(f"Row {result.total}: {str(e)}")

        # Commit all changes
        if result.succeeded > 0:
            db_session.commit()
        else:
            db_session.rollback()

    except Exception as e:
        result.add_failure(f"Import failed: {e}")
        db_session.rollback()

    result.end_time = datetime.now()
    return result


def validate_batch(
    invoices: list[Fattura],
    xml_generator: Callable | None = None,
    validator: FatturaPAValidator | None = None,
) -> BatchResult:
    """
    Validate multiple invoices.

    Args:
        invoices: List of invoices to validate
        xml_generator: Function to generate XML from invoice
        validator: XSD validator (uses default if None)

    Returns:
        BatchResult with validation summary
    """
    if validator is None:
        validator = FatturaPAValidator()
        try:
            validator.load_schema()
        except FileNotFoundError:
            # Schema not available - skip XSD validation
            validator = None

    def validate_invoice(fattura: Fattura) -> bool:
        """Validate single invoice."""
        # Basic validation
        if not fattura.cliente:
            raise ValueError("Invoice has no client")

        if fattura.totale <= 0:
            raise ValueError("Invoice total must be positive")

        if not fattura.righe or len(fattura.righe) == 0:
            raise ValueError("Invoice has no lines")

        # XSD validation (if XML generator provided)
        if xml_generator and validator:
            xml_content = xml_generator(fattura)
            is_valid, error = validator.validate(xml_content)
            if not is_valid:
                raise ValueError(f"XSD validation failed: {error}")

        return True

    processor = BatchProcessor(
        process_func=validate_invoice,
        fail_fast=False,
    )

    return processor.process(invoices)


def send_batch(
    invoices: list[Fattura],
    pec_sender,
    xml_paths: list[Path],
    max_concurrent: int = 5,
) -> BatchResult:
    """
    Send multiple invoices via PEC.

    Args:
        invoices: List of invoices to send
        pec_sender: PECSender instance
        xml_paths: List of XML file paths (must match invoices order)
        max_concurrent: Maximum concurrent sends (respects rate limiting)

    Returns:
        BatchResult with send summary
    """
    if len(invoices) != len(xml_paths):
        result = BatchResult(
            total=len(invoices), start_time=datetime.now(), end_time=datetime.now()
        )
        result.add_failure("Mismatch between invoices and XML paths")
        return result

    def send_invoice(data: tuple[Fattura, Path]) -> bool:
        """Send single invoice."""
        fattura, xml_path = data
        success, error = pec_sender.send_invoice(fattura, xml_path)
        if not success:
            raise Exception(error)
        return True

    processor = BatchProcessor(
        process_func=send_invoice,
        fail_fast=False,
    )

    # Zip invoices with paths
    items = list(zip(invoices, xml_paths, strict=False))

    return processor.process(items)


def bulk_update_status(
    invoices: list[Fattura],
    new_status: StatoFattura,
    db_session: Session,
) -> BatchResult:
    """
    Bulk update invoice status.

    Args:
        invoices: List of invoices
        new_status: New status to set
        db_session: Database session

    Returns:
        BatchResult
    """
    result = BatchResult(total=len(invoices), start_time=datetime.now())

    try:
        for fattura in invoices:
            try:
                fattura.stato = new_status
                result.add_success()
            except Exception as e:
                result.add_failure(f"Invoice {fattura.numero}/{fattura.anno}: {e}")

        db_session.commit()

    except Exception as e:
        db_session.rollback()
        result.add_failure(f"Bulk update failed: {e}")

    result.end_time = datetime.now()
    return result
