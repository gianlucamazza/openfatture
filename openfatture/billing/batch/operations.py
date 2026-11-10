"""
Batch operations for invoices.

Provides high-level batch operations for import, export, validation, and sending.
"""

import csv
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from openfatture.billing.batch.processor import BatchResult
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
                    duplicate = (
                        db_session.query(Fattura.id)
                        .filter(Fattura.numero == numero, Fattura.anno == anno)
                        .first()
                    )
                    if duplicate:
                        raise ValueError(f"Invoice {numero}/{anno} already exists")

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

                    # A savepoint per row: a failing row never poisons the batch.
                    with db_session.begin_nested():
                        db_session.add(fattura)
                        db_session.flush()

                    result.add_success(fattura.id)

                except IntegrityError as e:
                    result.add_failure(f"Row {result.total}: rejected by the database ({e.orig})")
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

    from openfatture.billing.application.invoice_status import (
        change_status,
        validate_manual_transition,
    )

    try:
        issues = []
        for fattura in invoices:
            try:
                validate_manual_transition(fattura, new_status)
            except ValueError as exc:
                issues.append(f"Invoice {getattr(fattura, 'id', '?')}: {exc}")
        if issues:
            raise ValueError("; ".join(issues))
        for fattura in invoices:
            if fattura.stato != new_status:
                change_status(db_session, fattura, new_status)
        db_session.commit()
        for _ in invoices:
            result.add_success()
    except Exception as e:
        db_session.rollback()
        for _fattura in invoices:
            result.add_failure(f"Batch not applied: {e}")

    result.end_time = datetime.now()
    return result
