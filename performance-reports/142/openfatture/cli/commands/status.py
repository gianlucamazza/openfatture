"""Read-only application status command."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from openfatture import __version__
from openfatture.platform.config import Settings, get_settings
from openfatture.platform.extras import available_extras

app = typer.Typer(no_args_is_help=True)
console = Console()


def _hooks_dir() -> Path:
    """Default hooks directory used by the hooks engine."""
    return Path.home() / ".openfatture" / "hooks"


def _readiness(settings: Settings, extras: dict[str, bool]) -> dict[str, Any]:
    """Compute honest setup readiness (core invoicing vs assistant)."""
    company_ok = bool(
        (settings.cedente_partita_iva or "").strip()
        and (settings.cedente_denominazione or "").strip()
    )
    data_dir_ok = settings.data_dir.exists()
    archive_ok = settings.archivio_dir.exists()
    ai_extra = bool(extras.get("ai"))
    provider = (settings.ai_provider or "").lower()
    # Ollama needs no cloud key; cloud providers need a key for real calls.
    ai_credentials_ok = provider == "ollama" or bool(settings.ai_api_key)
    assistant_ready = ai_extra and ai_credentials_ok
    core_ready = company_ok and data_dir_ok

    next_steps: list[str] = []
    if not data_dir_ok or not company_ok:
        next_steps.append("Run: openfatture init")
    if not ai_extra:
        next_steps.append("For the assistant: uv sync --extra ai")
    elif not ai_credentials_ok:
        next_steps.append("Set AI_API_KEY (or use AI_PROVIDER=ollama)")
    if core_ready and assistant_ready:
        next_steps.append('Try: openfatture assistant "Elenca le fatture aperte"')
    elif core_ready and not ai_extra:
        # Only when the ai extra itself is missing — not when credentials alone fail.
        next_steps.append("Core is ready; enable the ai extra to use the assistant")
    if not next_steps:
        next_steps.append("openfatture --help")

    return {
        "core_ready": core_ready,
        "assistant_ready": assistant_ready,
        "checks": {
            "company_profile": company_ok,
            "data_dir": data_dir_ok,
            "archive_dir": archive_ok,
            "ai_extra": ai_extra,
            "ai_credentials": ai_credentials_ok,
        },
        "next_steps": next_steps,
    }


def _build_status() -> dict[str, Any]:
    settings = get_settings()
    extras = available_extras()
    hooks_dir = _hooks_dir()
    hook_scripts = []
    if hooks_dir.is_dir():
        hook_scripts = sorted(
            p.name for p in hooks_dir.iterdir() if p.is_file() and not p.name.startswith(".")
        )
    readiness = _readiness(settings, extras)
    # Backend ids SSOT: platform.assistant_backends (no AI package import).
    from openfatture.platform.assistant_backends import (
        DEFAULT_ASSISTANT_BACKEND,
        resolve_backend_id,
    )

    assistant_backend = str(
        getattr(settings, "assistant_backend", DEFAULT_ASSISTANT_BACKEND)
        or DEFAULT_ASSISTANT_BACKEND
    )
    try:
        assistant_backend_id = resolve_backend_id(assistant_backend)
    except ValueError:
        assistant_backend_id = resolve_backend_id(DEFAULT_ASSISTANT_BACKEND)

    return {
        "version": __version__,
        "database": str(settings.database_url),
        "data_dir": str(settings.data_dir),
        "archive_dir": str(settings.archivio_dir),
        "ai_provider": settings.ai_provider,
        "ai_model": settings.ai_model,
        "ai_api_key_configured": bool(settings.ai_api_key),
        "assistant_backend": assistant_backend,
        "assistant_backend_id": assistant_backend_id,
        "readiness": readiness,
        "extras": extras,
        "extensions": {
            # Supported extension mechanism: user hook scripts (see docs/CORE_VS_EXTENSIONS.md)
            "hooks_dir": str(hooks_dir),
            "hooks_present": hooks_dir.is_dir(),
            "hooks_scripts": hook_scripts,
            # In-process plugins are not a product API (package removed / unsupported)
            "in_process_plugins": "unsupported",
        },
        "feature_flags": {
            "assistant_available": bool(extras.get("ai")),
            "assistant_backend": assistant_backend,
            "rag_auto_update_default": False,  # OPENFATTURE_RAG_AUTO_UPDATE_ENABLED default
        },
        "limitations": {
            "rag_auto_update": (
                "requires reindex_callback (AutoIndexingService); no silent simulation"
            ),
        },
    }


@app.command()
def status(json_output: bool = typer.Option(False, "--json", help="Emit status as JSON.")) -> None:
    """Show local configuration and storage readiness without changing state."""
    data = _build_status()
    if json_output:
        # Pure stdout for machine consumers; diagnostics use stderr via logging.
        print(json.dumps(data, indent=2, default=str))
        return

    ready = data["readiness"]
    core_label = "ready" if ready["core_ready"] else "not ready"
    asst_label = "ready" if ready["assistant_ready"] else "not ready"
    console.print(
        f"[bold]Readiness[/bold]  core: [cyan]{core_label}[/cyan]  "
        f"assistant: [cyan]{asst_label}[/cyan]\n"
    )

    table = Table(title="OpenFatture status")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")
    for key in (
        "version",
        "database",
        "data_dir",
        "archive_dir",
        "ai_provider",
        "ai_model",
        "ai_api_key_configured",
        "assistant_backend",
        "assistant_backend_id",
    ):
        table.add_row(key.replace("_", " ").title(), str(data[key]))
    console.print(table)

    checks = Table(title="Readiness checks")
    checks.add_column("Check", style="cyan")
    checks.add_column("OK")
    for name, ok in ready["checks"].items():
        checks.add_row(name.replace("_", " "), "yes" if ok else "no")
    console.print(checks)

    if ready["next_steps"]:
        console.print("\n[bold]Next steps[/bold]")
        for step in ready["next_steps"]:
            console.print(f"  • {step}")
        console.print()

    extras_table = Table(title="Optional extras (feature modules)")
    extras_table.add_column("Extra", style="cyan")
    extras_table.add_column("Installed")
    for name, installed in sorted(data["extras"].items()):
        extras_table.add_row(name, "yes" if installed else "no")
    console.print(extras_table)

    ext = data["extensions"]
    ext_table = Table(title="Extensions")
    ext_table.add_column("Mechanism", style="cyan")
    ext_table.add_column("Detail")
    ext_table.add_row(
        "hooks (supported)", f"{ext['hooks_dir']} ({len(ext['hooks_scripts'])} scripts)"
    )
    ext_table.add_row("in-process plugins", str(ext["in_process_plugins"]))
    console.print(ext_table)
