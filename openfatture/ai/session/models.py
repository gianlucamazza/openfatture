"""Data models for chat sessions."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from openfatture.ai.domain.message import Role


class SessionStatus(str, Enum):
    """Status of a chat session."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ChatMessage(BaseModel):
    """
    A single message in a chat session.

    Extends the basic Message model with session-specific metadata.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Role
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

    # Token usage for this message
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # Cost tracking
    estimated_cost_usd: float = 0.0

    # Provider info
    provider: str | None = None
    model: str | None = None

    # Tool calls (for function calling)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    tool_call_id: str | None = None

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "provider": self.provider,
            "model": self.model,
            "tool_calls": self.tool_calls,
            "tool_call_id": self.tool_call_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatMessage":
        """Create from dictionary."""
        # Convert timestamp string to datetime
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        # Convert role string to enum
        if isinstance(data.get("role"), str):
            data["role"] = Role(data["role"])

        return cls(**data)


class SessionMetadata(BaseModel):
    """Metadata about a chat session."""

    # Session info
    title: str = "New Chat"
    description: str | None = None
    tags: list[str] = Field(default_factory=list)

    # User context
    user_id: str | None = None
    regime_fiscale: str | None = None
    settore_attivita: str | None = None

    # Session stats
    message_count: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_response_time_ms: float = 0.0

    # Tools usage
    tools_enabled: bool = False
    tools_used: list[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_message_at: datetime | None = None

    # Provider info
    primary_provider: str | None = None
    primary_model: str | None = None

    def update_stats(self, message: ChatMessage) -> None:
        """Update metadata stats with new message."""
        self.message_count += 1
        self.total_tokens += message.total_tokens
        self.total_cost_usd += message.estimated_cost_usd
        self.updated_at = datetime.now()
        self.last_message_at = message.timestamp

        if message.provider:
            self.primary_provider = message.provider
        if message.model:
            self.primary_model = message.model

        # Track tool usage
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.get("function", {}).get("name")
                if tool_name and tool_name not in self.tools_used:
                    self.tools_used.append(tool_name)


class ChatSession(BaseModel):
    """
    A complete chat session with conversation history and metadata.

    Manages the full lifecycle of a chat conversation, including
    persistence, export, and statistics tracking.
    """

    # Identity
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: SessionStatus = SessionStatus.ACTIVE

    # Messages
    messages: list[ChatMessage] = Field(default_factory=list)

    # Metadata
    metadata: SessionMetadata = Field(default_factory=SessionMetadata)

    # Configuration
    max_messages: int = 100
    max_tokens: int = 8000
    auto_save: bool = True

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_message(
        self,
        role: Role,
        content: str,
        **kwargs: Any,
    ) -> ChatMessage:
        """
        Add a message to the session.

        Args:
            role: Message role
            content: Message content
            **kwargs: Additional message fields

        Returns:
            Created ChatMessage
        """
        message = ChatMessage(
            role=role,
            content=content,
            **kwargs,
        )

        self.messages.append(message)
        self.metadata.update_stats(message)
        self._truncate_if_needed()

        return message

    def add_user_message(self, content: str) -> ChatMessage:
        """Add a user message."""
        return self.add_message(Role.USER, content)

    def add_assistant_message(
        self,
        content: str,
        provider: str | None = None,
        model: str | None = None,
        tokens: int = 0,
        cost: float = 0.0,
        **kwargs: Any,
    ) -> ChatMessage:
        """Add an assistant message with tracking."""
        return self.add_message(
            Role.ASSISTANT,
            content,
            provider=provider,
            model=model,
            total_tokens=tokens,
            estimated_cost_usd=cost,
            **kwargs,
        )

    def add_system_message(self, content: str) -> ChatMessage:
        """Add a system message."""
        return self.add_message(Role.SYSTEM, content)

    def get_messages(
        self,
        include_system: bool = False,
        limit: int | None = None,
    ) -> list[ChatMessage]:
        """
        Get messages from the session.

        Args:
            include_system: Include system messages
            limit: Maximum number of messages to return (most recent)

        Returns:
            List of messages
        """
        messages = self.messages

        if not include_system:
            messages = [m for m in messages if m.role != Role.SYSTEM]

        if limit:
            messages = messages[-limit:]

        return messages

    def get_conversation_history(self) -> list[dict[str, Any]]:
        """
        Get conversation history in LLM API format.

        Returns:
            List of message dicts compatible with OpenAI/Anthropic APIs
        """
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in self.messages
            if msg.role != Role.SYSTEM
        ]

    def clear_messages(self, keep_system: bool = True) -> None:
        """
        Clear all messages from the session.

        Args:
            keep_system: Keep system messages
        """
        if keep_system:
            self.messages = [m for m in self.messages if m.role == Role.SYSTEM]
        else:
            self.messages = []

        # Reset some stats
        self.metadata.message_count = len(self.messages)

    def archive(self) -> None:
        """Archive this session."""
        self.status = SessionStatus.ARCHIVED
        self.metadata.updated_at = datetime.now()

    def delete(self) -> None:
        """Mark session as deleted."""
        self.status = SessionStatus.DELETED
        self.metadata.updated_at = datetime.now()

    def export_markdown(self) -> str:
        """
        Export session as Markdown.

        Returns:
            Markdown formatted conversation
        """
        lines = [
            f"# {self.metadata.title}",
            f"\n**Session ID:** `{self.id}`",
            f"**Created:** {self.metadata.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Messages:** {self.metadata.message_count}",
            f"**Tokens:** {self.metadata.total_tokens}",
            f"**Cost:** ${self.metadata.total_cost_usd:.4f}",
            "\n---\n",
        ]

        for msg in self.messages:
            if msg.role == Role.SYSTEM:
                continue

            role_emoji = "👤" if msg.role == Role.USER else "🤖"
            timestamp = msg.timestamp.strftime("%H:%M:%S")

            lines.append(f"\n### {role_emoji} {msg.role.value.title()} ({timestamp})\n")
            lines.append(msg.content)
            lines.append("\n")

            if msg.tool_calls:
                lines.append("**Tools Called:**\n")
                for tool in msg.tool_calls:
                    lines.append(f"- {tool.get('function', {}).get('name')}")
                lines.append("\n")

        return "\n".join(lines)

    def export_json(self) -> dict[str, Any]:
        """
        Export session as JSON-compatible dict.

        Returns:
            Dictionary with full session data
        """
        return {
            "id": self.id,
            "status": self.status.value,
            "metadata": {
                "title": self.metadata.title,
                "description": self.metadata.description,
                "tags": self.metadata.tags,
                "created_at": self.metadata.created_at.isoformat(),
                "updated_at": self.metadata.updated_at.isoformat(),
                "message_count": self.metadata.message_count,
                "total_tokens": self.metadata.total_tokens,
                "total_cost_usd": self.metadata.total_cost_usd,
                "primary_provider": self.metadata.primary_provider,
                "primary_model": self.metadata.primary_model,
                "tools_used": self.metadata.tools_used,
            },
            "messages": [msg.to_dict() for msg in self.messages],
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "ChatSession":
        """
        Create session from JSON data.

        Args:
            data: Dictionary with session data

        Returns:
            ChatSession instance
        """
        # Parse messages
        messages = [ChatMessage.from_dict(msg) for msg in data.get("messages", [])]

        # Parse metadata
        metadata_data = data.get("metadata", {})
        if isinstance(metadata_data.get("created_at"), str):
            metadata_data["created_at"] = datetime.fromisoformat(metadata_data["created_at"])
        if isinstance(metadata_data.get("updated_at"), str):
            metadata_data["updated_at"] = datetime.fromisoformat(metadata_data["updated_at"])

        metadata = SessionMetadata(**metadata_data)

        # Create session
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            status=SessionStatus(data.get("status", "active")),
            messages=messages,
            metadata=metadata,
        )

    def get_summary(self) -> str:
        """
        Get a short summary of the session.

        Returns:
            Summary string
        """
        return (
            f"{self.metadata.title} | "
            f"{self.metadata.message_count} msgs | "
            f"{self.metadata.total_tokens} tokens | "
            f"${self.metadata.total_cost_usd:.4f}"
        )

    def _truncate_if_needed(self) -> None:
        """Truncate messages if exceeding limits."""
        # Keep system messages and truncate conversation
        if len(self.messages) > self.max_messages:
            system_messages = [m for m in self.messages if m.role == Role.SYSTEM]
            other_messages = [m for m in self.messages if m.role != Role.SYSTEM]

            # Keep most recent messages
            recent = other_messages[-(self.max_messages - len(system_messages)) :]

            self.messages = system_messages + recent

        # Token-based truncation (simplified)
        # In production, use tiktoken for accurate counting
        if self.metadata.total_tokens > self.max_tokens:
            # Keep last N messages that fit within token limit
            cumulative_tokens = 0
            keep_messages: list[ChatMessage] = []

            for msg in reversed(self.messages):
                if msg.role == Role.SYSTEM:
                    keep_messages.insert(0, msg)
                    continue

                cumulative_tokens += msg.total_tokens
                if cumulative_tokens <= self.max_tokens:
                    keep_messages.insert(0, msg)
                else:
                    break

            self.messages = keep_messages
