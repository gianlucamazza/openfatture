"""Tests for cliente CLI commands."""

from typer.testing import CliRunner

from openfatture.cli.main import app

runner = CliRunner()


def test_cliente_list_empty(db_session):
    """Test cliente list with no clients."""
    result = runner.invoke(app, ["cliente", "list"])
    assert result.exit_code == 0
    assert "No clients found" in result.stdout


def test_cliente_create(db_session):
    """Test creating a new client."""
    result = runner.invoke(
        app,
        [
            "cliente",
            "create",
            "--name",
            "Test Client SRL",
            "--piva",
            "12345678901",
            "--email",
            "test@example.com",
        ],
    )
    assert result.exit_code == 0
    assert "created successfully" in result.stdout
    assert "Client ID:" in result.stdout


def test_cliente_list_with_results(db_session, sample_cliente):
    """Test cliente list with existing clients."""
    result = runner.invoke(app, ["cliente", "list"])
    assert result.exit_code == 0
    assert "Clients" in result.stdout
    assert sample_cliente.denominazione in result.stdout


def test_cliente_show(db_session, sample_cliente):
    """Test showing client details."""
    result = runner.invoke(app, ["cliente", "show", str(sample_cliente.id)])
    assert result.exit_code == 0
    assert sample_cliente.denominazione in result.stdout
    assert sample_cliente.partita_iva in result.stdout


def test_cliente_show_not_found(db_session):
    """Test showing non-existent client."""
    result = runner.invoke(app, ["cliente", "show", "99999"])
    assert result.exit_code == 1
    assert "Error" in result.stdout


def test_cliente_list_with_query(db_session, sample_cliente):
    """Test cliente list with search query."""
    result = runner.invoke(app, ["cliente", "list", "--query", sample_cliente.denominazione[:5]])
    assert result.exit_code == 0
    assert sample_cliente.denominazione in result.stdout


def test_cliente_create_missing_required(db_session):
    """Test creating client without required fields."""
    result = runner.invoke(app, ["cliente", "create"])
    assert result.exit_code != 0
