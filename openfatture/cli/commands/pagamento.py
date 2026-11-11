"""Collection ledger maintenance without an assistant equivalent.

Recording, allocating and inspecting collections go through the assistant.
"""

import json

import typer
from rich.console import Console

from openfatture.cli.database import ensure_database
from openfatture.cli.output import remember_result
from openfatture.i18n import _

app = typer.Typer(name="pagamento")
console = Console()


@app.command("migrate", help=_("cli-help-collections-migrate"))
def migrate_collections() -> None:
    """Upgrade pre-ledger collection data."""
    ensure_database()
    from openfatture.payment.application.collection_migration import upgrade_collection_database
    from openfatture.storage.database import base

    assert base.engine is not None
    upgrade_collection_database(base.engine)
    result = {"success": True, "message": "Collection migration complete"}
    remember_result(result)
    console.print(json.dumps(result, ensure_ascii=False, indent=2), markup=False)
