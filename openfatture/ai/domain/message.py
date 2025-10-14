"""Message and role definitions for AI agents."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Role(str, Enum):
    """Message role in conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """
    A single message in a conversation.

    Used to represent messages exchanged between user and AI,
    including system prompts and tool responses.
    """

    role: Role
    content: str
    name: str | None = None  # For tool messages
    tool_call_id: str | None = None  # For tool responses
    tool_calls: list[dict[str, Any]] | None = None  # For assistant messages with tool calls
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __str__(self) -> str:
        """String representation for logging."""
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.role.value}: {preview}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for LLM APIs."""
        data: dict[str, Any] = {
            "role": self.role.value,
            "content": self.content,
        }

        if self.name:
            data["name"] = self.name

        if self.tool_call_id:
            data["tool_call_id"] = self.tool_call_id

        if self.tool_calls:
            data["tool_calls"] = self.tool_calls

        return data


class ConversationHistory(BaseModel):
    """
    Manages conversation history with context window limits.

    Handles message storage, retrieval, and truncation to stay
    within token limits.
    """

    messages: list[Message] = Field(default_factory=list)
    max_messages: int = 20
    max_tokens: int = 4000

    def add_message(self, message: Message) -> None:
        """Add a message to history."""
        self.messages.append(message)
        self._truncate_if_needed()

    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self.add_message(Message(role=Role.USER, content=content))

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message."""
        self.add_message(Message(role=Role.ASSISTANT, content=content))

    def add_system_message(self, content: str) -> None:
        """Add a system message."""
        self.add_message(Message(role=Role.SYSTEM, content=content))

    def get_messages(self, include_system: bool = True) -> list[Message]:
        """
        Get all messages.

        Args:
            include_system: Whether to include system messages

        Returns:
            List of messages
        """
        if include_system:
            return self.messages.copy()
        return [m for m in self.messages if m.role != Role.SYSTEM]

    def get_last_n_messages(self, n: int) -> list[Message]:
        """Get the last N messages."""
        return self.messages[-n:] if n < len(self.messages) else self.messages.copy()

    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()

    def _truncate_if_needed(self) -> None:
        """Truncate messages if exceeding limits."""
        # Keep system messages (first ones) and truncate middle
        if len(self.messages) > self.max_messages:
            system_messages = [m for m in self.messages if m.role == Role.SYSTEM]
            other_messages = [m for m in self.messages if m.role != Role.SYSTEM]

            # Keep most recent messages
            recent = other_messages[-(self.max_messages - len(system_messages)) :]

            self.messages = system_messages + recent

    def to_list(self) -> list[dict[str, Any]]:
        """Convert to list of dicts for LLM APIs."""
        return [m.to_dict() for m in self.messages]
