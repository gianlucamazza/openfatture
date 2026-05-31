"""
Unit tests for fattura CLI command functions.

These exercise the command functions directly against a real, isolated database
(``runtime_db``) instead of mocking SQLAlchemy query chains: data is seeded
through the same database the command reads (via the real ``db_session()``
seam), and the locale is pinned to English so message assertions are
deterministic. Rich output is captured through a wide, recording ``Console`` so
table cells are not truncated.
"""

import io
from unittest.mock import patch

import pytest
import typer
from rich.console import Console

from openfatture.cli.commands.fattura import (
    crea_fattura,
    genera_xml,
    list_fatture,
)


@pytest.fixture(autouse=True)
def _english_locale():
    """Pin the locale to English so message assertions are deterministic."""
    from openfatture.i18n import get_locale, set_locale

    previous = get_locale()
    set_locale("en")
    try:
        yield
    finally:
        set_locale(previous)


def _recording_console() -> Console:
    """A wide Console that records output to a StringIO.

    The wide width stops Rich from truncating table cells, keeping rendered
    tokens intact for substring assertions.
    """
    return Console(file=io.StringIO(), width=220, force_terminal=False)


class TestListFattureFunction:
    """Test list_fatture function directly."""

    def test_list_fatture_empty(self, runtime_db):
        """Test listing when no invoices exist."""
        console = _recording_console()
        with patch("openfatture.cli.commands.fattura.console", console):
            list_fatture(stato=None, anno=None, limit=50)

        output = console.file.getvalue()
        assert "No invoices found" in output

    def test_list_fatture_with_data(self, runtime_db, seed_fattura):
        """Test listing invoices with data."""
        console = _recording_console()
        with patch("openfatture.cli.commands.fattura.console", console):
            list_fatture(stato=None, anno=None, limit=50)

        output = console.file.getvalue()
        # Table title and the seeded invoice row are rendered.
        assert "Invoices" in output
        assert "Acme Corporation" in output


class TestShowFatturaFunction:
    """Test genera_xml function directly."""

    def test_genera_xml_invoice_not_found(self, runtime_db):
        """Test XML generation for non-existent invoice."""
        console = _recording_console()
        with patch("openfatture.cli.commands.fattura.console", console):
            with pytest.raises(typer.Exit):
                genera_xml(999, output=None, no_validate=False)

        output = console.file.getvalue()
        assert "not found" in output


class TestCreaFatturaFunction:
    """Test crea_fattura function directly."""

    def test_crea_no_clients(self, runtime_db):
        """Test creating invoice when no clients exist."""
        console = _recording_console()
        with patch("openfatture.cli.commands.fattura.console", console):
            with pytest.raises(typer.Exit):
                crea_fattura(None)

        output = console.file.getvalue()
        assert "No clients found" in output

    def test_crea_client_not_found(self, runtime_db):
        """Test creating invoice with non-existent client ID."""
        console = _recording_console()
        with patch("openfatture.cli.commands.fattura.console", console):
            with pytest.raises(typer.Exit):
                crea_fattura(999)

        output = console.file.getvalue()
        assert "Invalid client selection" in output
