"""Invoice-specific batch processor with CSV import/export support.

Extends generic BatchProcessor for FatturaPA invoice operations.
"""

import csv
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from openfatture.core.batch.processor import BatchProcessor, BatchResult
from openfatture.storage.database.models import Cliente, Fattura, RigaFattura


class InvoiceBatchProcessor:
    """Specialized batch processor for invoice operations with CSV support.

    Wraps generic BatchProcessor and adds invoice-specific:
    - CSV import/export
    - Database session management
    - FatturaPA validation

    Example:
        >>> processor = InvoiceBatchProcessor(db_session=session)
        >>> result = processor.import_from_csv(Path("invoices.csv"))
        >>> print(f"Imported: {result.succeeded}/{result.total}")
    """

    def __init__(self, db_session: Session) -> None:
        """Initialize with database session for persistence.

        Args:
            db_session: SQLAlchemy session for database operations
        """
        self.db_session = db_session

    def import_from_csv(self, csv_path: Path, dry_run: bool = False) -> BatchResult:
        """Import invoices from CSV file.

        CSV Format:
            numero,anno,cliente_id,descrizione,quantita,prezzo,aliquota_iva

        Args:
            csv_path: Path to CSV file
            dry_run: If True, validate only (no DB writes)

        Returns:
            BatchResult with import statistics

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid

        Example:
            >>> result = processor.import_from_csv(Path("invoices.csv"))
            >>> if result.failed > 0:
            ...     for error in result.errors:
            ...         print(error)
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Read CSV rows
        rows = []
        try:
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception as e:
            raise ValueError(f"Failed to read CSV: {e}") from e

        # Process each row
        def process_row(row: dict[str, str]) -> Fattura:
            """Process single CSV row into Fattura."""
            # Validate required fields
            required_fields = ["numero", "anno", "cliente_id", "descrizione", "quantita", "prezzo"]
            missing_fields = [f for f in required_fields if f not in row or not row[f]]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")

            # Validate cliente exists
            cliente_id = int(row["cliente_id"])
            cliente = self.db_session.query(Cliente).filter(Cliente.id == cliente_id).first()
            if not cliente:
                raise ValueError(f"Cliente {cliente_id} not found")

            # Parse values
            numero = row["numero"]
            anno = int(row["anno"])
            descrizione = row["descrizione"]
            quantita = Decimal(row["quantita"])
            prezzo = Decimal(row["prezzo"])
            aliquota_iva = Decimal(row.get("aliquota_iva", "22.00"))

            # Calculate totals
            imponibile = quantita * prezzo
            iva = imponibile * (aliquota_iva / Decimal("100"))
            totale = imponibile + iva

            # Create invoice
            fattura = Fattura(
                numero=numero,
                anno=anno,
                cliente_id=cliente_id,
                imponibile=imponibile,
                iva=iva,
                totale=totale,
            )

            # Create line item
            riga = RigaFattura(
                numero_riga=1,
                descrizione=descrizione,
                quantita=quantita,
                prezzo_unitario=prezzo,
                aliquota_iva=aliquota_iva,
                imponibile=imponibile,
                iva=iva,
                totale=totale,
            )

            fattura.righe.append(riga)

            # Persist if not dry_run
            if not dry_run:
                self.db_session.add(fattura)
                self.db_session.flush()

            return fattura

        # Use BatchProcessor for processing with error handling
        processor: BatchProcessor[dict[str, str], Fattura] = BatchProcessor(
            process_func=process_row,
            fail_fast=False,
        )

        result = processor.process(rows)

        # Commit if successful and not dry_run
        if not dry_run and result.succeeded > 0:
            try:
                self.db_session.commit()
            except Exception as e:
                self.db_session.rollback()
                result.add_failure(f"Database commit failed: {e}")

        return result

    def export_to_csv(self, fatture: list[Fattura], output_path: Path) -> BatchResult:
        """Export invoices to CSV file.

        Args:
            fatture: List of Fattura objects to export
            output_path: Output CSV file path

        Returns:
            BatchResult with export statistics

        Raises:
            ValueError: If fatture list is empty
            IOError: If file cannot be written

        Example:
            >>> fatture = session.query(Fattura).filter(Fattura.anno == 2025).all()
            >>> result = processor.export_to_csv(fatture, Path("export.csv"))
            >>> print(f"Exported {result.succeeded} invoices")
        """
        if not fatture:
            raise ValueError("No invoices to export")

        # Prepare rows
        def prepare_row(fattura: Fattura) -> dict[str, str]:
            """Convert Fattura to CSV row."""
            # Get first line item (simplified)
            riga = fattura.righe[0] if fattura.righe else None

            return {
                "numero": fattura.numero,
                "anno": str(fattura.anno),
                "cliente_id": str(fattura.cliente_id),
                "cliente_nome": fattura.cliente.denominazione if fattura.cliente else "",
                "descrizione": riga.descrizione if riga else "",
                "quantita": str(riga.quantita) if riga else "0",
                "prezzo": str(riga.prezzo_unitario) if riga else "0",
                "aliquota_iva": str(riga.aliquota_iva) if riga else "22.00",
                "imponibile": str(fattura.imponibile),
                "iva": str(fattura.iva),
                "totale": str(fattura.totale),
                "stato": fattura.stato.value,
            }

        # Process with BatchProcessor
        rows: list[dict[str, str]] = []

        def process_fattura(fattura: Fattura) -> dict[str, str]:
            """Process single fattura."""
            row = prepare_row(fattura)
            rows.append(row)
            return row

        processor: BatchProcessor[Fattura, dict[str, str]] = BatchProcessor(
            process_func=process_fattura,
            fail_fast=False,
        )

        result = processor.process(fatture)

        # Write to CSV
        if rows:
            try:
                with open(output_path, "w", encoding="utf-8", newline="") as f:
                    fieldnames = [
                        "numero",
                        "anno",
                        "cliente_id",
                        "cliente_nome",
                        "descrizione",
                        "quantita",
                        "prezzo",
                        "aliquota_iva",
                        "imponibile",
                        "iva",
                        "totale",
                        "stato",
                    ]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
            except Exception as e:
                result.add_failure(f"Failed to write CSV: {e}")

        return result
