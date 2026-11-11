"""Long-term notes the assistant keeps across conversations.

Short-term memory is the conversation itself (``ai.session`` plus the history
budget in ``ai.runtime.history``). Long-term memory is this small set of notes:
preferences and stable facts the user asked the assistant to remember. Every
note is written only after the user confirms it, can be listed with
``/memory`` and removed with ``/forget``, and reaches the model as data, never
as instructions that override the system prompt.
"""

from openfatture.ai.memory.store import MemoryNote, MemoryStore, NoteError, get_memory_store

__all__ = ["NoteError", "MemoryNote", "MemoryStore", "get_memory_store"]
