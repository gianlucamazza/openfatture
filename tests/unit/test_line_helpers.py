"""Course line helper: formatted description, cedente VAT defaults."""

from decimal import Decimal

from openfatture.ai.tools.invoice_tools.line_helpers import (
    create_course_line,
    format_course_description,
)
from openfatture.billing.application import invoice_commands
from openfatture.storage.database.models import RigaFattura


def test_course_line_uses_one_service_and_forfettario_natura(runtime_session, seed_cliente):
    # The test cedente is in the forfettario regime (RF19).
    invoice_id = invoice_commands.create_invoice(cliente_id=seed_cliente.id, anno=2026)[
        "invoice_id"
    ]
    result = create_course_line(
        fattura_id=invoice_id,
        course_title="Python",
        imponibile=960,
        start_date="14.09.2026",
    )
    assert result.get("success"), result
    riga = runtime_session.get(RigaFattura, result["riga_id"])
    assert (riga.quantita, riga.unita_misura) == (Decimal("1.00"), "servizio")
    assert (riga.aliquota_iva, riga.natura) == (Decimal("0.00"), "N2.2")
    assert riga.descrizione.startswith('Corso di formazione: "Python"')


class TestCourseDescription:
    def test_format_course_description(self):
        """Test formatting course descriptions."""
        # Single-day course
        desc = format_course_description(
            course_title="Python avanzato per data science",
            start_date="14.09.2026",
            end_date="14.09.2026",
            location="Sede del cliente, Milano",
        )

        assert "Corso di formazione:" in desc
        assert '"Python avanzato per data science"' in desc
        assert "eseguito il 14.09.2026" in desc  # Single day: "il" not "dal...al"
        assert "presso Sede del cliente, Milano" in desc

        # Multi-day course
        desc2 = format_course_description(
            course_title="Workshop Django",
            start_date="2026-09-14",
            end_date="2026-09-16",
            location="Online",
        )

        assert "eseguito dal 2026-09-14 al 2026-09-16" in desc2

        # Course without end_date (defaults to start_date)
        desc3 = format_course_description(
            course_title="Webinar",
            start_date="14.09.2026",
            location="Zoom",
        )

        assert "eseguito il 14.09.2026" in desc3

        # Course with additional notes
        desc4 = format_course_description(
            course_title="Advanced Course",
            start_date="14.09.2026",
            additional_notes="Include materiale didattico e certificato",
        )

        assert "Include materiale didattico e certificato" in desc4
