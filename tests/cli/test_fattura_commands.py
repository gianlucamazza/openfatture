"""Tests for fattura CLI commands."""

from typer.testing import CliRunner

from openfatture.cli.main import app

runner = CliRunner()


def test_fattura_list_empty(runtime_db):
    """Test fattura list with no invoices."""
    result = runner.invoke(app, ["fattura", "list"])
    assert result.exit_code == 0
    assert "No invoices found" in result.stdout


def test_fattura_create(runtime_db, seed_cliente):
    """Test creating a new invoice."""
    result = runner.invoke(
        app,
        [
            "fattura",
            "create",
            "--client",
            str(seed_cliente.id),
            "--note",
            "Test invoice",
        ],
    )
    assert result.exit_code == 0
    assert "created successfully" in result.stdout
    assert "Invoice ID:" in result.stdout


def test_fattura_list_with_results(runtime_db, seed_fattura):
    """Test fattura list with existing invoices."""
    result = runner.invoke(app, ["fattura", "list"])
    assert result.exit_code == 0
    assert "Invoices" in result.stdout
    assert seed_fattura.numero in result.stdout


def test_fattura_show(runtime_db, seed_fattura):
    """Test showing invoice details."""
    result = runner.invoke(app, ["fattura", "show", str(seed_fattura.id)])
    assert result.exit_code == 0
    assert f"{seed_fattura.numero}/{seed_fattura.anno}" in result.stdout
    assert seed_fattura.cliente.denominazione in result.stdout


def test_fattura_show_not_found(runtime_db):
    """Test showing non-existent invoice."""
    result = runner.invoke(app, ["fattura", "show", "99999"])
    assert result.exit_code == 1
    assert "Error" in result.stdout


def test_fattura_add_line(runtime_db, seed_fattura):
    """Test adding line item to invoice."""
    result = runner.invoke(
        app,
        [
            "fattura",
            "add-line",
            "--invoice",
            str(seed_fattura.id),
            "--desc",
            "Test service",
            "--qty",
            "10",
            "--price",
            "50.00",
        ],
    )
    assert result.exit_code == 0
    assert "added" in result.stdout or "created" in result.stdout.lower()


def test_fattura_generate_pdf(runtime_db, seed_fattura, tmp_path):
    """Test generating PDF for invoice."""
    output_file = tmp_path / "test_invoice.pdf"
    result = runner.invoke(
        app,
        [
            "fattura",
            "generate-pdf",
            str(seed_fattura.id),
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert "PDF generated successfully" in result.stdout
    assert output_file.exists()


def test_fattura_list_with_filters(runtime_db, seed_fattura):
    """Test fattura list with filters."""
    result = runner.invoke(app, ["fattura", "list", "--year", str(seed_fattura.anno)])
    assert result.exit_code == 0
    assert seed_fattura.numero in result.stdout


def test_fattura_create_invalid_client(runtime_db):
    """Test creating invoice with non-existent client."""
    result = runner.invoke(
        app,
        [
            "fattura",
            "create",
            "--client",
            "99999",
        ],
    )
    assert result.exit_code == 1
    assert "Error" in result.stdout


def test_fattura_generate_xml(runtime_db, seed_fattura):
    """Test generating FatturaPA XML for invoice."""
    result = runner.invoke(app, ["fattura", "generate-xml", str(seed_fattura.id)])
    assert result.exit_code == 0
    assert "XML generated successfully" in result.stdout
    assert "Output:" in result.stdout


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
    assert "XML generated successfully" in result.stdout
    assert output_file.exists()
    xml_content = output_file.read_text()
    assert "FatturaElettronica" in xml_content
    assert seed_fattura.numero in xml_content


def test_fattura_generate_xml_dry_run(runtime_db, seed_fattura):
    """Test generating XML in dry-run mode (no file written)."""
    result = runner.invoke(app, ["fattura", "generate-xml", str(seed_fattura.id), "--dry-run"])
    assert result.exit_code == 0
    assert "XML generated successfully (dry-run mode)" in result.stdout
    assert "FatturaElettronica" in result.stdout
    assert seed_fattura.numero in result.stdout


def test_fattura_generate_xml_not_found(runtime_db):
    """Test generating XML for non-existent invoice."""
    result = runner.invoke(app, ["fattura", "generate-xml", "99999"])
    assert result.exit_code == 1
    assert "Error" in result.stdout
    assert "not found" in result.stdout
