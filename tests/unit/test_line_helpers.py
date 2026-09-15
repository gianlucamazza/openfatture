"""Tests for line helper tools (Issue #69).

Tests that line items can be created in different styles:
- "lump" style: 1 × imponibile
- "rate" style: qty × unit_price
- "course" style: formatted descriptions for training courses
"""

import inspect

from openfatture.ai.tools.invoice_tools.line_helpers import (
    create_course_line,
    create_lump_line,
    create_rate_line,
    format_course_description,
)


class TestLineHelpers:
    """Test line creation helper tools."""

    def test_create_lump_line_signature(self):
        """Test that create_lump_line has the expected signature."""
        sig = inspect.signature(create_lump_line)
        params = list(sig.parameters.keys())

        assert "fattura_id" in params
        assert "descrizione" in params
        assert "imponibile" in params
        assert "aliquota_iva" in params
        assert "unita_misura" in params

        # Check defaults
        assert sig.parameters["aliquota_iva"].default == 22.0
        assert sig.parameters["unita_misura"].default == "servizio"

    def test_create_rate_line_signature(self):
        """Test that create_rate_line has the expected signature."""
        sig = inspect.signature(create_rate_line)
        params = list(sig.parameters.keys())

        assert "fattura_id" in params
        assert "descrizione" in params
        assert "quantita" in params
        assert "prezzo_unitario" in params
        assert "aliquota_iva" in params
        assert "unita_misura" in params

        # Check defaults
        assert sig.parameters["aliquota_iva"].default == 22.0
        assert sig.parameters["unita_misura"].default == "ore"

    def test_create_course_line_signature(self):
        """Test that create_course_line has the expected signature."""
        sig = inspect.signature(create_course_line)
        params = list(sig.parameters.keys())

        assert "fattura_id" in params
        assert "course_title" in params
        assert "imponibile" in params
        assert "start_date" in params
        assert "end_date" in params
        assert "location" in params
        assert "additional_notes" in params
        assert "aliquota_iva" in params

        # Check defaults
        assert sig.parameters["aliquota_iva"].default == 0.0

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
