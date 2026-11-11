"""Tests for the fattura CLI commands without an assistant equivalent."""

from typer.testing import CliRunner

from openfatture.cli.main import app

runner = CliRunner()


def test_fattura_generate_xml(runtime_db, seed_fattura):
    """Test generating FatturaPA XML for invoice."""
    result = runner.invoke(app, ["fattura", "generate-xml", str(seed_fattura.id)])
    assert result.exit_code == 0
    assert "XML generato correttamente" in result.stdout
    assert "File:" in result.stdout


def test_fattura_generate_xml_with_output(runtime_db, seed_fattura, tmp_path):
    """Test generating XML with custom output path."""
    output_file = tmp_path / "custom_invoice.xml"
    result = runner.invoke(
        app,
        [
            "fattura",
            "generate-xml",
            str(seed_fattura.id),
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert "XML generato correttamente" in result.stdout
    assert output_file.exists()
    xml_content = output_file.read_text()
    assert "FatturaElettronica" in xml_content
    assert seed_fattura.numero in xml_content


def test_fattura_generate_xml_dry_run(runtime_db, seed_fattura):
    """Test generating XML in dry-run mode (no file written)."""
    result = runner.invoke(app, ["fattura", "generate-xml", str(seed_fattura.id), "--dry-run"])
    assert result.exit_code == 0
    assert "XML generato correttamente (simulazione" in result.stdout
    assert "FatturaElettronica" in result.stdout
    assert seed_fattura.numero in result.stdout


def test_fattura_generate_xml_not_found(runtime_db):
    """Test generating XML for non-existent invoice."""
    result = runner.invoke(app, ["fattura", "generate-xml", "99999"])
    assert result.exit_code == 1
    assert "Errore" in result.stdout
    assert "not found" in result.stdout
