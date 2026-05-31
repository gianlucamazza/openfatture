"""Shared Typer apps and utilities for AI commands."""

import typer
from rich.console import Console

from openfatture.ai.domain.message import ConversationHistory, Message, Role
from openfatture.utils.logging import get_logger

app = typer.Typer(no_args_is_help=True)
console = Console()
logger = get_logger(__name__)

rag_app = typer.Typer(help="Manage RAG knowledge base", no_args_is_help=True)
feedback_app = typer.Typer(help="Manage user feedback and ML predictions", no_args_is_help=True)
retrain_app = typer.Typer(help="Manage automatic ML model retraining", no_args_is_help=True)
auto_update_app = typer.Typer(help="Manage RAG auto-update on data changes", no_args_is_help=True)


def _convert_history(history: list[dict[str, str]]) -> ConversationHistory:
    """Convert list of dicts to ConversationHistory."""
    conv_history = ConversationHistory()
    for msg_dict in history:
        role_str = msg_dict.get("role", "user")
        content = msg_dict.get("content", "")
        try:
            role = Role(role_str)
        except ValueError:
            role = Role.USER  # Default to user if invalid
        message = Message(role=role, content=content)
        conv_history.add_message(message)
    return conv_history
