"""Tools that write the user's long-term notes (`openfatture.ai.memory`)."""

from typing import Any

from openfatture.ai.memory import NoteError, get_memory_store
from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk


def remember_note(text: str) -> dict[str, Any]:
    try:
        note = get_memory_store().add(text)
    except NoteError as exc:
        return {"error": str(exc)}
    return {"success": True, "note_id": note.id, "text": note.text}


def forget_note(note_id: int) -> dict[str, Any]:
    try:
        note = get_memory_store().remove(int(note_id))
    except NoteError as exc:
        return {"error": str(exc)}
    return {"success": True, "note_id": note.id, "text": note.text}


def get_memory_tools() -> list[Tool]:
    return [
        Tool(
            name="remember_note",
            risk=ToolRisk.MUTATE,
            description=(
                "Save a note the assistant will see in every future conversation: a "
                "preference or stable fact the user asked you to remember, such as how to "
                "allocate receipts or a usual payment term. One short sentence in the user's "
                "words, at most 300 characters. Refused for empty or duplicate notes, "
                "credentials, or when 50 notes are saved. Returns note_id and the saved text."
            ),
            category="memory",
            parameters=[
                ToolParameter(
                    name="text",
                    type=ToolParameterType.STRING,
                    description="The note, one sentence, at most 300 characters",
                    required=True,
                ),
            ],
            func=remember_note,
            requires_confirmation=True,
            tags=["memory", "write"],
        ),
        Tool(
            name="forget_note",
            risk=ToolRisk.MUTATE,
            description=(
                "Delete one saved note by its id (the number shown in the saved notes). "
                "Irreversible. Returns the removed text; an unknown id is an error."
            ),
            category="memory",
            parameters=[
                ToolParameter(
                    name="note_id",
                    type=ToolParameterType.INTEGER,
                    description="Id of the note to delete",
                    required=True,
                ),
            ],
            func=forget_note,
            requires_confirmation=True,
            tags=["memory", "write"],
        ),
    ]
