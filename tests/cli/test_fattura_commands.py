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
    assert "Errore: Fattura non trovata." in result.stdout


def test_fattura_generate_xml_issued_elsewhere_is_localized(
    runtime_db, runtime_session, seed_fattura
):
    seed_fattura.issued_elsewhere = True
    runtime_session.commit()

    result = runner.invoke(app, ["fattura", "generate-xml", str(seed_fattura.id), "--dry-run"])

    assert result.exit_code == 1
    assert "emessa altrove" in result.stdout
    assert "Cannot generate" not in result.stdout


def test_resolve_unknown_submission_is_localized(runtime_db):
    result = runner.invoke(
        app,
        ["fattura", "resolve-submission", "424242", "--sent", "--evidence", "PEC ref"],
        input="y\n",
    )

    assert result.exit_code == 1
    assert "Tentativo di invio non trovato." in result.stdout
    assert "Traceback" not in result.output


def test_json_keeps_the_service_error_and_code(runtime_db):
    import json

    result = runner.invoke(app, ["--format", "json", "fattura", "generate-xml", "99999"])

    error = json.loads(result.stdout)["error"]
    assert error == {"code": "invoice_not_found", "message": "Invoice 99999 not found"}
