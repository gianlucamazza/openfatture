"""Tests for cliente CLI commands."""

from typer.testing import CliRunner

from openfatture.cli.main import app

runner = CliRunner()


def test_cliente_list_empty(runtime_db):
    """Test cliente list with no clients."""
    result = runner.invoke(app, ["cliente", "list"])
    assert result.exit_code == 0
    assert "No clients found" in result.stdout


def test_cliente_create(runtime_db):
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


def test_cliente_list_with_results(runtime_db, seed_cliente):
    """Test cliente list with existing clients."""
    result = runner.invoke(app, ["cliente", "list"])
    assert result.exit_code == 0
    assert "Clients" in result.stdout
    # Check ID is in output (safer than full name due to Rich table rendering)
    assert str(seed_cliente.id) in result.stdout


def test_cliente_show(runtime_db, seed_cliente):
    """Test showing client details."""
    result = runner.invoke(app, ["cliente", "show", str(seed_cliente.id)])
    assert result.exit_code == 0
    assert seed_cliente.denominazione in result.stdout
    assert seed_cliente.partita_iva in result.stdout


def test_cliente_show_not_found(runtime_db):
    """Test showing non-existent client."""
    result = runner.invoke(app, ["cliente", "show", "99999"])
    assert result.exit_code == 1
    assert "Error" in result.stdout


def test_cliente_list_with_query(runtime_db, seed_cliente):
    """Test cliente list with search query."""
    result = runner.invoke(app, ["cliente", "list", "--query", seed_cliente.denominazione[:5]])
    assert result.exit_code == 0
    # Check that search returned results
    assert "Clients" in result.stdout
    assert str(seed_cliente.id) in result.stdout


def test_cliente_create_missing_required(runtime_db):
    """Test creating client without required fields."""
    result = runner.invoke(app, ["cliente", "create"])
    assert result.exit_code != 0
