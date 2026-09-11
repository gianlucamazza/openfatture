"""Tests for fattura CLI commands."""

from typer.testing import CliRunner

from openfatture.cli.main import app

runner = CliRunner()


def test_fattura_list_empty(db_session):
    """Test fattura list with no invoices."""
    result = runner.invoke(app, ["fattura", "list"])
    assert result.exit_code == 0
    assert "No invoices found" in result.stdout


def test_fattura_create(db_session, sample_cliente):
    """Test creating a new invoice."""
    result = runner.invoke(
        app,
        [
            "fattura",
            "create",
            "--client",
            str(sample_cliente.id),
            "--note",
            "Test invoice",
        ],
    )
    assert result.exit_code == 0
    assert "created successfully" in result.stdout
    assert "Invoice ID:" in result.stdout


def test_fattura_list_with_results(db_session, sample_fattura):
    """Test fattura list with existing invoices."""
    result = runner.invoke(app, ["fattura", "list"])
    assert result.exit_code == 0
    assert "Invoices" in result.stdout
    assert sample_fattura.numero in result.stdout


def test_fattura_show(db_session, sample_fattura):
    """Test showing invoice details."""
    result = runner.invoke(app, ["fattura", "show", str(sample_fattura.id)])
    assert result.exit_code == 0
    assert f"{sample_fattura.numero}/{sample_fattura.anno}" in result.stdout
    assert sample_fattura.cliente.denominazione in result.stdout


def test_fattura_show_not_found(db_session):
    """Test showing non-existent invoice."""
    result = runner.invoke(app, ["fattura", "show", "99999"])
    assert result.exit_code == 1
    assert "Error" in result.stdout


def test_fattura_add_line(db_session, sample_fattura):
    """Test adding line item to invoice."""
    result = runner.invoke(
        app,
        [
            "fattura",
            "add-line",
            "--invoice",
            str(sample_fattura.id),
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


def test_fattura_generate_pdf(db_session, sample_fattura_with_righe, tmp_path):
    """Test generating PDF for invoice."""
    output_file = tmp_path / "test_invoice.pdf"
    result = runner.invoke(
        app,
        [
            "fattura",
            "generate-pdf",
            str(sample_fattura_with_righe.id),
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert "PDF generated successfully" in result.stdout
    assert output_file.exists()


def test_fattura_list_with_filters(db_session, sample_fattura):
    """Test fattura list with filters."""
    result = runner.invoke(app, ["fattura", "list", "--year", str(sample_fattura.anno)])
    assert result.exit_code == 0
    assert sample_fattura.numero in result.stdout


def test_fattura_create_invalid_client(db_session):
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
