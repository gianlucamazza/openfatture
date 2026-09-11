"""Unit tests for AI domain message models."""

from openfatture.ai.domain.message import ConversationHistory, Message, Role


class TestRole:
    """Tests for Role enum."""

    def test_role_values(self):
        """Test role enum values."""
        assert Role.SYSTEM.value == "system"
        assert Role.USER.value == "user"
        assert Role.ASSISTANT.value == "assistant"
        assert Role.TOOL.value == "tool"


class TestMessage:
    """Tests for Message model."""

    def test_message_basic(self):
        """Test basic message creation."""
        msg = Message(role=Role.USER, content="Hello")

        assert msg.role == Role.USER
        assert msg.content == "Hello"
        assert msg.name is None
        assert msg.tool_call_id is None
        assert msg.tool_calls is None
        assert msg.metadata == {}

    def test_message_with_name(self):
        """Test message with name (for tool messages)."""
        msg = Message(role=Role.TOOL, content="Result", name="search_tool")

        assert msg.role == Role.TOOL
        assert msg.name == "search_tool"

    def test_message_with_tool_call_id(self):
        """Test message with tool_call_id (for tool responses)."""
        msg = Message(role=Role.TOOL, content="Result", name="search", tool_call_id="call_123")

        assert msg.tool_call_id == "call_123"

    def test_message_with_tool_calls(self):
        """Test assistant message with tool calls."""
        tool_calls = [
            {
                "id": "call_123",
                "type": "function",
                "function": {"name": "search", "arguments": '{"query": "test"}'},
            }
        ]
        msg = Message(role=Role.ASSISTANT, content="", tool_calls=tool_calls)

        assert msg.tool_calls == tool_calls
        assert len(msg.tool_calls) == 1

    def test_message_str_short(self):
        """Test __str__ with short content."""
        msg = Message(role=Role.USER, content="Hello World")

        result = str(msg)

        assert result == "user: Hello World"
        assert "..." not in result

    def test_message_str_long(self):
        """Test __str__ truncates long content."""
        long_content = "A" * 100  # 100 characters
        msg = Message(role=Role.ASSISTANT, content=long_content)

        result = str(msg)

        assert result.startswith("assistant: ")
        assert result.endswith("...")
        assert len(result) < len(long_content) + 20  # Truncated

    def test_message_to_dict_basic(self):
        """Test to_dict with basic message."""
        msg = Message(role=Role.USER, content="Hello")

        result = msg.to_dict()

        assert result == {"role": "user", "content": "Hello"}
        assert "name" not in result
        assert "tool_call_id" not in result
        assert "tool_calls" not in result

    def test_message_to_dict_with_name(self):
        """Test to_dict includes name when present."""
        msg = Message(role=Role.TOOL, content="Result", name="search_tool")

        result = msg.to_dict()

        assert result["name"] == "search_tool"

    def test_message_to_dict_with_tool_call_id(self):
        """Test to_dict includes tool_call_id when present."""
        msg = Message(role=Role.TOOL, content="Result", name="search", tool_call_id="call_123")

        result = msg.to_dict()

        assert result["tool_call_id"] == "call_123"

    def test_message_to_dict_with_tool_calls(self):
        """Test to_dict includes tool_calls when present."""
        tool_calls = [{"id": "call_123", "type": "function"}]
        msg = Message(role=Role.ASSISTANT, content="", tool_calls=tool_calls)

        result = msg.to_dict()

        assert result["tool_calls"] == tool_calls

    def test_message_to_dict_complete(self):
        """Test to_dict with all optional fields."""
        tool_calls = [{"id": "call_123"}]
        msg = Message(
            role=Role.TOOL,
            content="Result",
            name="search",
            tool_call_id="call_456",
            tool_calls=tool_calls,
        )

        result = msg.to_dict()

        assert result["role"] == "tool"
        assert result["content"] == "Result"
        assert result["name"] == "search"
        assert result["tool_call_id"] == "call_456"
        assert result["tool_calls"] == tool_calls


class TestConversationHistory:
    """Tests for ConversationHistory model."""

    def test_conversation_history_empty(self):
        """Test empty conversation history."""
        history = ConversationHistory()

        assert len(history.messages) == 0
        assert history.max_messages == 20
        assert history.max_tokens == 4000

    def test_conversation_history_custom_limits(self):
        """Test conversation history with custom limits."""
        history = ConversationHistory(max_messages=10, max_tokens=2000)

        assert history.max_messages == 10
        assert history.max_tokens == 2000

    def test_add_message(self):
        """Test adding a message."""
        history = ConversationHistory()
        msg = Message(role=Role.USER, content="Hello")

        history.add_message(msg)

        assert len(history.messages) == 1
        assert history.messages[0] == msg

    def test_add_user_message(self):
        """Test add_user_message convenience method."""
        history = ConversationHistory()

        history.add_user_message("Hello")

        assert len(history.messages) == 1
        assert history.messages[0].role == Role.USER
        assert history.messages[0].content == "Hello"

    def test_add_assistant_message(self):
        """Test add_assistant_message convenience method."""
        history = ConversationHistory()

        history.add_assistant_message("Hi there")

        assert len(history.messages) == 1
        assert history.messages[0].role == Role.ASSISTANT
        assert history.messages[0].content == "Hi there"

    def test_add_system_message(self):
        """Test add_system_message convenience method."""
        history = ConversationHistory()

        history.add_system_message("System prompt")

        assert len(history.messages) == 1
        assert history.messages[0].role == Role.SYSTEM
        assert history.messages[0].content == "System prompt"

    def test_get_messages_all(self):
        """Test get_messages returns all messages."""
        history = ConversationHistory()
        history.add_system_message("System")
        history.add_user_message("User")
        history.add_assistant_message("Assistant")

        messages = history.get_messages(include_system=True)

        assert len(messages) == 3
        assert messages[0].role == Role.SYSTEM
        assert messages[1].role == Role.USER
        assert messages[2].role == Role.ASSISTANT

    def test_get_messages_without_system(self):
        """Test get_messages excludes system messages."""
        history = ConversationHistory()
        history.add_system_message("System")
        history.add_user_message("User")
        history.add_assistant_message("Assistant")

        messages = history.get_messages(include_system=False)

        assert len(messages) == 2
        assert all(m.role != Role.SYSTEM for m in messages)

    def test_get_messages_returns_copy(self):
        """Test get_messages returns a copy, not reference."""
        history = ConversationHistory()
        history.add_user_message("Original")

        messages = history.get_messages()
        messages.append(Message(role=Role.USER, content="Modified"))

        # Original should be unchanged
        assert len(history.messages) == 1

    def test_get_last_n_messages(self):
        """Test get_last_n_messages returns recent messages."""
        history = ConversationHistory()
        history.add_user_message("Message 1")
        history.add_assistant_message("Message 2")
        history.add_user_message("Message 3")
        history.add_assistant_message("Message 4")

        last_2 = history.get_last_n_messages(2)

        assert len(last_2) == 2
        assert last_2[0].content == "Message 3"
        assert last_2[1].content == "Message 4"

    def test_get_last_n_messages_more_than_available(self):
        """Test get_last_n_messages when n > message count."""
        history = ConversationHistory()
        history.add_user_message("Message 1")
        history.add_assistant_message("Message 2")

        last_10 = history.get_last_n_messages(10)

        # Should return all available messages (copy)
        assert len(last_10) == 2
        assert last_10[0].content == "Message 1"
        assert last_10[1].content == "Message 2"

    def test_clear(self):
        """Test clear removes all messages."""
        history = ConversationHistory()
        history.add_user_message("Message 1")
        history.add_assistant_message("Message 2")

        assert len(history.messages) == 2

        history.clear()

        assert len(history.messages) == 0

    def test_to_list(self):
        """Test to_list converts messages to dict list."""
        history = ConversationHistory()
        history.add_user_message("Hello")
        history.add_assistant_message("Hi")

        result = history.to_list()

        assert len(result) == 2
        assert result[0] == {"role": "user", "content": "Hello"}
        assert result[1] == {"role": "assistant", "content": "Hi"}

    def test_truncate_exceeds_max_messages_no_system(self):
        """Test truncation when exceeding max_messages without system messages."""
        history = ConversationHistory(max_messages=5)

        # Add 10 messages
        for i in range(10):
            history.add_user_message(f"Message {i}")

        # Should keep only last 5
        assert len(history.messages) == 5
        assert history.messages[0].content == "Message 5"
        assert history.messages[-1].content == "Message 9"

    def test_truncate_exceeds_max_messages_with_system(self):
        """Test truncation preserves system messages."""
        history = ConversationHistory(max_messages=6)

        # Add 2 system messages
        history.add_system_message("System 1")
        history.add_system_message("System 2")

        # Add 10 user/assistant messages
        for i in range(10):
            history.add_user_message(f"Message {i}")

        # Should keep 2 system + 4 recent others (total 6)
        assert len(history.messages) == 6

        system_messages = [m for m in history.messages if m.role == Role.SYSTEM]
        other_messages = [m for m in history.messages if m.role != Role.SYSTEM]

        assert len(system_messages) == 2
        assert len(other_messages) == 4

        # Check system messages are first
        assert history.messages[0].role == Role.SYSTEM
        assert history.messages[1].role == Role.SYSTEM

        # Check we kept the most recent user messages
        assert other_messages[-1].content == "Message 9"

    def test_truncate_multiple_times(self):
        """Test truncation works correctly on multiple additions."""
        history = ConversationHistory(max_messages=3)

        history.add_system_message("System")  # 1 message

        # Add messages one by one
        history.add_user_message("Message 1")  # 2 messages
        history.add_user_message("Message 2")  # 3 messages
        history.add_user_message("Message 3")  # 3 messages (truncated)
        history.add_user_message("Message 4")  # 3 messages (truncated)

        assert len(history.messages) == 3

        # System message should be preserved
        assert history.messages[0].role == Role.SYSTEM
        assert history.messages[0].content == "System"

        # Should have last 2 user messages
        assert history.messages[1].content == "Message 3"
        assert history.messages[2].content == "Message 4"

    def test_no_truncation_under_limit(self):
        """Test no truncation when under max_messages."""
        history = ConversationHistory(max_messages=10)

        history.add_user_message("Message 1")
        history.add_assistant_message("Message 2")
        history.add_user_message("Message 3")

        # Should keep all messages
        assert len(history.messages) == 3
        assert history.messages[0].content == "Message 1"
        assert history.messages[1].content == "Message 2"
        assert history.messages[2].content == "Message 3"
