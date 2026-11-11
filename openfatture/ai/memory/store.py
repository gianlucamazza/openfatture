"""File-backed store of the user's long-term notes (``data_dir/ai/memory.json``)."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from openfatture.platform.logging import redact_sensitive

MAX_NOTES = 50
MAX_NOTE_CHARS = 300

# Credentials never belong in a note: they would be sent to the model provider
# on every turn. Registered secrets are caught by redact_sensitive.
_SECRET_HINTS = re.compile(
    r"(?i)\b(password|passw|api[ _-]?key|token|segreto|pin)\b|\bsk-[A-Za-z0-9_-]{8,}"
)


class NoteError(ValueError):
    """A note that cannot be stored or removed."""


@dataclass(frozen=True)
class MemoryNote:
    id: int
    text: str
    created_at: str


class MemoryStore:
    """Notes in one JSON file, written atomically with owner-only permissions."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def entries(self) -> list[MemoryNote]:
        if not self.path.is_file():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        notes = raw.get("notes", []) if isinstance(raw, dict) else []
        return [
            MemoryNote(id=int(n["id"]), text=str(n["text"]), created_at=str(n["created_at"]))
            for n in notes
            if isinstance(n, dict) and {"id", "text", "created_at"} <= n.keys()
        ]

    def add(self, text: str) -> MemoryNote:
        """Store ``text`` as a new note, or raise :class:`NoteError`."""
        text = " ".join(text.split())
        if not text:
            raise NoteError("The note is empty")
        if len(text) > MAX_NOTE_CHARS:
            raise NoteError(f"A note is at most {MAX_NOTE_CHARS} characters")
        if redact_sensitive(text) != text or _SECRET_HINTS.search(text):
            raise NoteError("Notes cannot contain passwords, keys or other credentials")
        notes = self.entries()
        if any(note.text.casefold() == text.casefold() for note in notes):
            raise NoteError("This note is already saved")
        if len(notes) >= MAX_NOTES:
            raise NoteError(f"At most {MAX_NOTES} notes: forget one first")
        note = MemoryNote(
            id=max((n.id for n in notes), default=0) + 1,
            text=text,
            created_at=datetime.now().isoformat(timespec="seconds"),
        )
        self._write([*notes, note])
        return note

    def remove(self, note_id: int) -> MemoryNote:
        notes = self.entries()
        for note in notes:
            if note.id == note_id:
                self._write([n for n in notes if n.id != note_id])
                return note
        raise NoteError(f"No note with id {note_id}")

    def _write(self, notes: list[MemoryNote]) -> None:
        from openfatture.platform.secrets import write_private_text

        payload = {"version": 1, "notes": [asdict(note) for note in notes]}
        write_private_text(self.path, json.dumps(payload, ensure_ascii=False, indent=2))


def get_memory_store() -> MemoryStore:
    from openfatture.platform.config import get_settings

    return MemoryStore(get_settings().data_dir / "ai" / "memory.json")
