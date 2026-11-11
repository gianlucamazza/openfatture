"""Collection ledger maintenance without an assistant equivalent.

Recording, allocating and inspecting collections go through the assistant.
"""

import json

import typer
from rich.console import Console

from openfatture.cli.database import ensure_database
from openfatture.cli.output import remember_result

app = typer.Typer(name="pagamento")
console = Console()


@app.callback()
def prepare() -> None:
    ensure_database()


@app.command("migrate")
def migrate_collections() -> None:
    """Aggiorna i dati storici degli incassi senza cambiare gli importi."""
    from openfatture.payment.application.collection_migration import upgrade_collection_database
    from openfatture.storage.database import base

    assert base.engine is not None
    upgrade_collection_database(base.engine)
    result = {"success": True, "message": "Collection migration complete"}
    remember_result(result)
    console.print(json.dumps(result, ensure_ascii=False, indent=2), markup=False)
