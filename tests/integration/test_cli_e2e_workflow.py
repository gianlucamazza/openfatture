"""
Lightweight CLI smoke tests covering the primary command groups.

These focus on verifying that the modernised commands execute against a
temporary SQLite database with the plugin system disabled.
"""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import ExitStack, contextmanager
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

os.environ.setdefault("OPENFATTURE_PLUGINS_ENABLED", "0")

import openfatture.cli.main as cli_main
from openfatture.cli.main import app
from openfatture.storage.database.base import Base
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)

# Disable plugin auto-loading to keep tests deterministic
cli_main.settings.plugins_enabled = False
cli_main.settings.plugins_auto_discover = False


def _configure_cli_settings(
    settings: MagicMock, db_url: str, archivio_dir: Path | None = None
) -> None:
    """Apply shared overrides to the dynamic settings object returned by get_settings."""
    settings.database_url = db_url
    settings.archivio_dir = archivio_dir or Path("/tmp/openfatture-tests")
    settings.plugins_enabled = False
    settings.plugins_auto_discover = False
    settings.plugins_enabled_list = ""
    # Minimal AI configuration for commands that read these fields
    settings.ai_provider = "openai"
    settings.ai_model = "gpt-4o-mini"
    settings.archivio_dir.mkdir(parents=True, exist_ok=True)


@contextmanager
def patched_cli_environment(db_url: str, engine) -> None:
    """Patch CLI settings and command-level init_db hooks to reuse the shared SQLite engine."""
    init_targets = [
        "openfatture.storage.database.base.init_db",
        "openfatture.cli.commands.cliente.init_db",
        "openfatture.cli.commands.fattura.init_db",
        "openfatture.cli.commands.events.init_db",
        "openfatture.cli.commands.batch.init_db",
        "openfatture.cli.commands.report.init_db",
    ]

    with ExitStack() as stack:
        mock_settings = stack.enter_context(patch("openfatture.utils.config.get_settings"))
        init_mocks = [stack.enter_context(patch(target)) for target in init_targets]

        settings = mock_settings.return_value
        _configure_cli_settings(settings, db_url)

        def _init_db_override(_: str) -> None:
            from openfatture.storage.database import base

            base.engine = engine
            base.SessionLocal = sessionmaker(bind=engine)
            Base.metadata.create_all(bind=engine)

        for mock_init in init_mocks:
            mock_init.side_effect = _init_db_override

        # Ensure SessionLocal is primed for commands that don't call init_db explicitly
        _init_db_override(db_url)

        yield


@pytest.fixture
def app_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def db_engine(tmp_path: Path):
    db_path = tmp_path / "cli_tests.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def temp_config():
    """Provide an on-disk config file for commands that expect one."""
    config = {
        "cedente": {
            "denominazione": "Test Company S.r.l.",
            "partita_iva": "12345678901",
            "codice_fiscale": "TSTCMP80A01H501Y",
            "regime_fiscale": "RF01",
            "indirizzo": "Via Test 123",
            "numero_civico": "123",
            "cap": "20100",
            "comune": "Milano",
            "provincia": "MI",
            "nazione": "IT",
        }
    }

    with patch("tempfile.NamedTemporaryFile", wraps=tempfile.NamedTemporaryFile):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as handle:
            json.dump(config, handle)
            path = Path(handle.name)
    try:
        yield path
    finally:
        if path.exists():
            path.unlink()


def test_cliente_add_and_list(app_runner: CliRunner, db_engine) -> None:
    with patched_cli_environment(str(db_engine.url), db_engine):
        add_result = app_runner.invoke(
            app,
            [
                "cliente",
                "add",
                "Test Client SRL",
                "--piva",
                "12345678901",
                "--cf",
                "TSTCLT80A01H501Y",
                "--sdi",
                "ABC1234",
            ],
        )
        assert add_result.exit_code == 0
        assert "Client added successfully" in add_result.output

        list_result = app_runner.invoke(app, ["cliente", "list"])
        assert list_result.exit_code == 0
        assert "Test Client SRL" in list_result.output


def test_fattura_list_with_seed_data(app_runner: CliRunner, db_engine, db_session) -> None:
    cliente = Cliente(
        denominazione="List Test Client", partita_iva="12345678901", codice_destinatario="LIST01"
    )
    db_session.add(cliente)
    db_session.commit()

    fattura = Fattura(
        numero="001",
        anno=2025,
        data_emissione=date(2025, 1, 15),
        cliente_id=cliente.id,
        tipo_documento=TipoDocumento.TD01,
        stato=StatoFattura.BOZZA,
        imponibile=1000,
        iva=220,
        totale=1220,
    )
    db_session.add(fattura)
    db_session.commit()

    with patched_cli_environment(str(db_engine.url), db_engine):
        result = app_runner.invoke(app, ["fattura", "list"])
        assert result.exit_code == 0
        assert "Invoices" in result.output
        assert "001/2025" in result.output
        assert "€1220.00" in result.output


def test_fattura_show_renders_details(app_runner: CliRunner, db_engine, db_session) -> None:
    cliente = Cliente(
        denominazione="Show Client", partita_iva="12345678901", codice_destinatario="SHOW01"
    )
    db_session.add(cliente)
    db_session.commit()

    fattura = Fattura(
        numero="010",
        anno=2025,
        data_emissione=date(2025, 2, 1),
        cliente_id=cliente.id,
        tipo_documento=TipoDocumento.TD01,
        stato=StatoFattura.BOZZA,
        imponibile=500,
        iva=110,
        totale=610,
    )
    db_session.add(fattura)
    db_session.flush()

    riga = RigaFattura(
        fattura_id=fattura.id,
        numero_riga=1,
        descrizione="Consulenza",
        quantita=1,
        prezzo_unitario=500,
        aliquota_iva=22,
        imponibile=500,
        iva=110,
        totale=610,
    )
    db_session.add(riga)
    db_session.commit()

    with patched_cli_environment(str(db_engine.url), db_engine):
        result = app_runner.invoke(app, ["fattura", "show", str(fattura.id)])
        assert result.exit_code == 0
        assert "Invoice 010/2025" in result.output
        assert "Consulenza" in result.output
        assert "€610.00" in result.output


def test_ai_describe_command_mocked(app_runner: CliRunner, db_engine) -> None:
    fake_response = MagicMock()
    fake_response.status = MagicMock(value="success")
    fake_response.content = "Descrizione generata"
    fake_response.metadata = {"is_structured": False}
    fake_response.usage.total_tokens = 100
    fake_response.usage.estimated_cost_usd = 0.0
    fake_response.latency_ms = 50
    fake_response.provider = "mock"
    fake_response.model = "mock"

    agent_instance = AsyncMock()
    agent_instance.execute.return_value = fake_response

    with (
        patched_cli_environment(str(db_engine.url), db_engine),
        patch("openfatture.cli.commands.ai.InvoiceAssistantAgent", return_value=agent_instance),
        patch("openfatture.cli.commands.ai.create_provider") as mock_provider,
        patch(
            "openfatture.cli.commands.ai.enrich_with_rag",
            new=AsyncMock(side_effect=lambda ctx, *_: ctx),
        ),
    ):
        mock_provider.return_value = MagicMock()
        result = app_runner.invoke(app, ["ai", "describe", "3 ore sviluppo web"])
        assert result.exit_code == 0
        assert "Descrizione generata" in result.output


def test_payment_account_lifecycle(app_runner: CliRunner, db_engine) -> None:
    with patched_cli_environment(str(db_engine.url), db_engine):
        create_result = app_runner.invoke(app, ["payment", "create-account", "Main Account"])
        assert create_result.exit_code == 0
        assert "Account created" in create_result.output

        list_result = app_runner.invoke(app, ["payment", "list-accounts"])
        assert list_result.exit_code == 0
        assert "Main Account" in list_result.output
