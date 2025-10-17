"""Batch operations service adapter for Streamlit web interface.

Provides simplified API for batch import/export operations.
"""

import csv
import io
import tempfile
from pathlib import Path
from typing import Any

from openfatture.core.batch.operations import export_invoices_csv
from openfatture.storage.database.models import Cliente, Fattura
from openfatture.utils.config import Settings, get_settings
from openfatture.web.utils.cache import get_db_session


class StreamlitBatchService:
    """Adapter service for batch operations in Streamlit."""

    def __init__(self) -> None:
        """Initialize service with settings."""
        self.settings: Settings = get_settings()

    def import_clients_from_csv(self, csv_content: str) -> dict[str, Any]:
        """
        Import clients from CSV content.

        Args:
            csv_content: CSV file content as string

        Returns:
            Dictionary with import results
        """
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        processed = 0
        created = 0
        updated = 0
        errors = []

        db = get_db_session()

        for i, row in enumerate(rows, 1):
            try:
                processed += 1

                # Validate required fields
                denominazione = row.get("denominazione", "").strip()
                if not denominazione:
                    errors.append(f"Riga {i}: denominazione obbligatoria")
                    continue

                # Check if client exists
                existing = db.query(Cliente).filter(Cliente.denominazione == denominazione).first()

                if existing:
                    # Update existing
                    for key, value in row.items():
                        if hasattr(existing, key) and value.strip():
                            setattr(existing, key, value.strip())
                    updated += 1
                else:
                    # Create new
                    client = Cliente(
                        denominazione=denominazione,
                        partita_iva=row.get("partita_iva", "").strip() or None,
                        codice_fiscale=row.get("codice_fiscale", "").strip() or None,
                        codice_destinatario=row.get("codice_destinatario", "").strip() or None,
                        pec=row.get("pec", "").strip() or None,
                        indirizzo=row.get("indirizzo", "").strip() or None,
                        cap=row.get("cap", "").strip() or None,
                        comune=row.get("comune", "").strip() or None,
                        provincia=row.get("provincia", "").strip() or None,
                        telefono=row.get("telefono", "").strip() or None,
                        email=row.get("email", "").strip() or None,
                        note=row.get("note", "").strip() or None,
                    )
                    db.add(client)
                    created += 1

            except Exception as e:
                errors.append(f"Riga {i}: {str(e)}")

        if created > 0:
            db.commit()

        return {
            "success": len(errors) == 0,
            "processed": processed,
            "errors": errors,
            "warnings": [],
            "created": created,
            "updated": updated,
            "skipped": 0,
        }

    def import_invoices_from_csv(self, csv_content: str) -> dict[str, Any]:
        """
        Import invoices from CSV content.

        Note: This is a simplified implementation. Full batch import available via CLI.

        Args:
            csv_content: CSV file content as string

        Returns:
            Dictionary with import results
        """
        return {
            "success": False,
            "processed": 0,
            "errors": [
                "Import fatture disponibile via CLI: uv run openfatture batch import-invoices"
            ],
            "warnings": [],
            "created": 0,
            "updated": 0,
            "skipped": 0,
        }

    def export_invoices_to_csv(
        self, filters: dict[str, Any] | None = None, include_lines: bool = False
    ) -> tuple[bool, str, str | None]:
        """
        Export invoices to CSV string.

        Args:
            filters: Optional filters for invoice selection
            include_lines: Whether to include invoice lines

        Returns:
            Tuple of (success, csv_content, error_message)
        """
        try:
            db = get_db_session()

            # Build query
            query = db.query(Fattura).order_by(Fattura.anno.desc(), Fattura.numero.desc())

            if filters:
                if "anno" in filters:
                    query = query.filter(Fattura.anno == filters["anno"])
                if "stato" in filters:
                    from openfatture.storage.database.models import StatoFattura

                    query = query.filter(Fattura.stato == StatoFattura(filters["stato"]))

            invoices = query.all()

            # Create temporary file for export
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_file:
                temp_path = Path(temp_file.name)

            # Export to temp file
            success, error = export_invoices_csv(invoices, temp_path, include_lines)

            if success:
                # Read content back
                csv_content = temp_path.read_text(encoding="utf-8")
                temp_path.unlink(missing_ok=True)
                return True, csv_content, None
            else:
                temp_path.unlink(missing_ok=True)
                return False, "", error or "Export failed"

        except Exception as e:
            return False, "", str(e)

    def export_clients_to_csv(self) -> tuple[bool, str, str | None]:
        """
        Export clients to CSV string.

        Returns:
            Tuple of (success, csv_content, error_message)
        """
        try:
            import csv
            import io

            db = get_db_session()
            clients = db.query(Cliente).order_by(Cliente.denominazione).all()

            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow(
                [
                    "denominazione",
                    "partita_iva",
                    "codice_fiscale",
                    "codice_destinatario",
                    "pec",
                    "indirizzo",
                    "cap",
                    "comune",
                    "provincia",
                    "telefono",
                    "email",
                    "note",
                ]
            )

            # Data
            for client in clients:
                writer.writerow(
                    [
                        client.denominazione,
                        client.partita_iva or "",
                        client.codice_fiscale or "",
                        client.codice_destinatario or "",
                        client.pec or "",
                        client.indirizzo or "",
                        client.cap or "",
                        client.comune or "",
                        client.provincia or "",
                        client.telefono or "",
                        client.email or "",
                        client.note or "",
                    ]
                )

            return True, output.getvalue(), None

        except Exception as e:
            return False, "", str(e)

    def get_batch_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        Get batch operation history.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of batch operation records
        """
        # This would integrate with a batch history table
        # For now, return empty list
        return []

    def validate_csv_format(self, csv_content: str, data_type: str) -> dict[str, Any]:
        """
        Validate CSV format without importing.

        Args:
            csv_content: CSV content to validate
            data_type: Type of data ('clients' or 'invoices')

        Returns:
            Validation results
        """
        try:
            import csv
            import io

            reader = csv.DictReader(io.StringIO(csv_content))

            if data_type == "clients":
                required_fields = ["denominazione"]
                optional_fields = [
                    "partita_iva",
                    "codice_fiscale",
                    "codice_destinatario",
                    "pec",
                    "indirizzo",
                    "cap",
                    "comune",
                    "provincia",
                    "telefono",
                    "email",
                    "note",
                ]
            elif data_type == "invoices":
                required_fields = ["numero", "anno", "cliente", "data_emissione"]
                optional_fields = ["descrizione", "quantita", "prezzo_unitario", "aliquota_iva"]
            else:
                return {"valid": False, "errors": [f"Unknown data type: {data_type}"]}

            # Check headers
            headers = reader.fieldnames or []
            missing_required = [field for field in required_fields if field not in headers]

            if missing_required:
                return {
                    "valid": False,
                    "errors": [f"Missing required fields: {', '.join(missing_required)}"],
                }

            # Count rows
            row_count = sum(1 for row in reader)

            return {
                "valid": True,
                "row_count": row_count,
                "headers": headers,
                "required_fields": required_fields,
                "optional_fields": optional_fields,
            }

        except Exception as e:
            return {"valid": False, "errors": [str(e)]}
