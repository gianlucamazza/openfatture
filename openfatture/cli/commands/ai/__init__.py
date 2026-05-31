"""AI-powered assistance commands."""

# Import command modules to register their decorators on the Typer apps.
from . import (  # noqa: F401, E402
    auto_update,
    chat,
    compliance,
    create_invoice,
    describe,
    feedback,
    forecast,
    rag,
    retrain,
    self_learning,
    vat,
    voice,
)
from ._app import app, auto_update_app, feedback_app, rag_app, retrain_app

# Mount sub-typers with the same names as the original monolith.
app.add_typer(feedback_app, name="feedback")
app.add_typer(retrain_app, name="retrain")
app.add_typer(auto_update_app, name="auto-update")
app.add_typer(rag_app, name="rag")

__all__ = ["app"]
