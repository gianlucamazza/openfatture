"""Behaviour scenarios run against the configured model: an eval, not a unit test.

They call the real provider with the user's configured key and model, so they
cost money and their outcome can vary. They are deselected by default and run
only on request, against an isolated database and data directory:

    OPENFATTURE_EVAL=1 uv run python -m pytest -m llm_eval tests/evals

Run them before and after a change to the system prompt or to tool
descriptions, and compare the results.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.orm import Session

pytestmark = [
    pytest.mark.llm_eval,
    pytest.mark.skipif(
        os.environ.get("OPENFATTURE_EVAL") != "1",
        reason="calls the configured model: set OPENFATTURE_EVAL=1 to run",
    ),
]


@pytest.fixture
def workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
    provider_env: dict[str, str],
) -> Iterator[Session]:
    """Isolated database and data directories; the provider is the user's."""
    for name, value in provider_env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("ARCHIVIO_DIR", str(tmp_path / "data" / "archivio"))
    monkeypatch.setenv("AI_TOOL_ACCESS", "standard")
    session_factory = request.getfixturevalue("runtime_db")
    session = session_factory()
    _seed(session)
    try:
        yield session
    finally:
        session.close()


def _seed(session: Session) -> None:
    from openfatture.storage.database.models import (
        Cliente,
        Fattura,
        RigaFattura,
        StatoFattura,
        TipoDocumento,
    )

    client = Cliente(
        denominazione="Studio Esempio SRL",
        partita_iva="12345678901",
        codice_destinatario="ABC1234",
        indirizzo="Via Roma 1",
        cap="20100",
        comune="Milano",
        provincia="MI",
        nazione="IT",
    )
    session.add(client)
    session.flush()
    for numero, issued_elsewhere in (("1", True), ("2", False)):
        invoice = Fattura(
            numero=numero,
            anno=2026,
            data_emissione=date(2026, 3, int(numero)),
            cliente_id=client.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("1000.00"),
            iva=Decimal("220.00"),
            totale=Decimal("1220.00"),
            issued_elsewhere=issued_elsewhere,
        )
        session.add(invoice)
        session.flush()
        session.add(
            RigaFattura(
                fattura_id=invoice.id,
                numero_riga=1,
                descrizione="Consulenza",
                quantita=Decimal("10"),
                prezzo_unitario=Decimal("100.00"),
                aliquota_iva=Decimal("22.00"),
                imponibile=Decimal("1000.00"),
                iva=Decimal("220.00"),
                totale=Decimal("1220.00"),
            )
        )
    session.commit()


async def _ask(message: str) -> tuple[str, list[str]]:
    """The answer and the names of the tools it called."""
    from openfatture.ai.runtime import create_assistant_runtime
    from openfatture.platform.config import get_settings

    settings = get_settings()
    if (settings.ai_provider or "").lower() != "ollama" and not settings.ai_api_key:
        pytest.skip("no AI key configured")
    runtime = create_assistant_runtime(enable_streaming=False, persist_session=False)
    response = await runtime.run(message)
    assert response.success, response.error
    outcomes: list[dict[str, Any]] = response.metadata.get("tool_outcomes", [])
    return response.content, [outcome["tool"] for outcome in outcomes]


@pytest.mark.asyncio
async def test_a_greeting_gets_a_short_answer(workspace: Session) -> None:
    answer, tools = await _ask("ciao")
    assert tools == []
    assert len(answer) < 400, answer


@pytest.mark.asyncio
async def test_an_invoice_issued_elsewhere_is_not_called_unsent(workspace: Session) -> None:
    answer, tools = await _ask("mostrami lo stato delle fatture del 2026")
    assert tools, "the answer must come from the tools"
    lowered = answer.lower()
    assert "non verificat" in lowered, answer
    for claim in ("non è stata inviata", "non è stata emessa", "non inviata"):
        assert claim not in lowered, answer


@pytest.mark.asyncio
async def test_a_summary_pdf_is_computed_by_the_tool(workspace: Session) -> None:
    answer, tools = await _ask("genera il riepilogo pdf delle fatture 2026")
    assert "generate_invoice_summary_pdf" in tools
    assert "riepilogo_fatture_2026.pdf" in answer, answer


@pytest.mark.asyncio
async def test_a_disabled_capability_points_at_the_setting(
    workspace: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AI_TOOL_ACCESS", "read")
    from openfatture.platform.config import reload_settings

    reload_settings()
    answer, tools = await _ask("genera il pdf della fattura 2/2026")
    assert "generate_invoice_pdf" not in tools
    assert "ai_tool_access standard" in answer, answer
    assert "non supporta" not in answer.lower(), answer
