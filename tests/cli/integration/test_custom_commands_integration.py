"""Integration tests for custom commands with AI chat system.

Tests the full integration of custom commands with:
- ChatAgent execution
- Tool calling
- RAG enrichment
- Streaming responses
- Session persistence
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.message import Message, Role
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.ai.session import ChatSession
from openfatture.cli.commands.custom_commands import CustomCommandRegistry


class MockProvider(BaseLLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self):
        super().__init__()
        self._provider_name = "mock"
        self.model = "mock-model"
        self._supports_streaming = True
        self._supports_tools = True
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def supports_streaming(self) -> bool:
        return self._supports_streaming

    @property
    def supports_tools(self) -> bool:
        return self._supports_tools

    async def generate(self, messages, **kwargs):
        self.call_count += 1
        # Simulate AI response based on input
        last_message = messages[-1] if messages else Message(role=Role.USER, content="")

        # Check if this is a custom command expansion
        if "fattura completa" in last_message.content.lower():
            content = """Ho analizzato la richiesta per creare una fattura:

**Cliente:** Acme Corp
**Servizio:** Consulenza web
**Importo:** 500€

Ecco i dettagli generati:
1. ✓ Descrizione: Consulenza professionale per sviluppo applicazione web
2. ✓ IVA: 22% (servizi professionali standard)
3. ✓ Compliance: Verificata - pronta per SDI
"""
        elif "cliente" in last_message.content.lower():
            content = """Informazioni cliente trovate:
- Denominazione: Acme Corp
- P.IVA: 12345678901
- Fatture totali: 15
- Importo totale: €12,500
"""
        else:
            content = "Risposta AI generica basata su input."

        return AgentResponse(
            content=content,
            status=ResponseStatus.SUCCESS,
            provider=self.provider_name,
            model=self.model,
            usage=UsageMetrics(
                prompt_tokens=50,
                completion_tokens=100,
                total_tokens=150,
                estimated_cost_usd=0.0015,
            ),
            latency_ms=250,
        )

    async def stream(self, messages, **kwargs):
        response = await self.generate(messages, **kwargs)
        # Simulate streaming by yielding chunks
        for chunk in response.content.split():
            yield chunk + " "

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def estimate_cost(self, usage: UsageMetrics) -> float:
        """Estimate cost based on token usage."""
        return usage.total_tokens * 0.00001  # Mock pricing

    async def health_check(self) -> bool:
        return True


@pytest.fixture
def mock_provider():
    """Create mock provider for testing."""
    return MockProvider()


@pytest.fixture
def temp_commands_dir():
    """Create temporary directory for test commands."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def custom_registry_with_commands(temp_commands_dir):
    """Create registry with test commands."""
    # Create test command: fattura-test
    command_data = {
        "name": "fattura-test",
        "description": "Test invoice creation",
        "template": """Crea una fattura completa per:
Cliente: {{ arg1 }}
Servizio: {{ arg2 }}
Importo: {{ arg3 }}€

Genera descrizione, suggerisci IVA, e verifica compliance.""",
        "category": "invoicing",
    }

    file_path = temp_commands_dir / "fattura-test.yaml"
    with open(file_path, "w") as f:
        yaml.dump(command_data, f)

    # Create another test command: cliente-test
    command_data2 = {
        "name": "cliente-test",
        "description": "Test client lookup",
        "template": "Cerca cliente: {{ arg1 }}",
        "category": "clients",
    }

    file_path2 = temp_commands_dir / "cliente-test.yaml"
    with open(file_path2, "w") as f:
        yaml.dump(command_data2, f)

    return CustomCommandRegistry(commands_dir=temp_commands_dir)


@pytest.mark.asyncio
class TestCustomCommandsIntegration:
    """Integration tests for custom commands with AI system."""

    async def test_custom_command_with_chat_agent(
        self, mock_provider, custom_registry_with_commands
    ):
        """Test that custom command works with ChatAgent."""
        # Create ChatAgent
        agent = ChatAgent(provider=mock_provider, enable_tools=False, enable_streaming=False)

        # Expand custom command
        expanded = custom_registry_with_commands.execute(
            "fattura-test", args=["Acme Corp", "Consulenza web", "500"]
        )

        # Create context
        context = ChatContext(user_input=expanded)

        # Execute agent
        response = await agent.execute(context)

        # Verify response
        assert response.status == ResponseStatus.SUCCESS
        assert "Acme Corp" in response.content
        assert "500" in response.content or "500€" in response.content
        assert mock_provider.call_count == 1

    async def test_custom_command_with_session_persistence(
        self, mock_provider, custom_registry_with_commands
    ):
        """Test that custom command results are persisted in session."""
        # Create session
        session = ChatSession()

        # Expand command
        expanded = custom_registry_with_commands.execute("cliente-test", args=["Acme Corp"])

        # Add to session
        session.add_user_message(expanded)

        # Simulate agent response
        agent = ChatAgent(provider=mock_provider, enable_tools=False)
        context = ChatContext(user_input=expanded, session_id=session.id)
        response = await agent.execute(context)

        # Add response to session
        session.add_assistant_message(
            response.content,
            provider=response.provider,
            model=response.model,
            tokens=response.usage.total_tokens,
            cost=response.usage.estimated_cost_usd,
        )

        # Verify session
        assert session.metadata.message_count == 2  # user + assistant
        assert session.metadata.total_tokens > 0
        messages = session.get_messages()
        assert len(messages) == 2
        assert "Cerca cliente: Acme Corp" in messages[0].content
        assert "Acme Corp" in messages[1].content

    async def test_custom_command_with_streaming(
        self, mock_provider, custom_registry_with_commands
    ):
        """Test that custom command works with streaming responses."""
        # Create agent with streaming
        agent = ChatAgent(provider=mock_provider, enable_streaming=True)

        # Expand command
        expanded = custom_registry_with_commands.execute(
            "fattura-test", args=["Test Client", "Test Service", "100"]
        )

        # Create context
        context = ChatContext(user_input=expanded)

        # Collect streamed chunks
        chunks = []
        async for chunk in agent.execute_stream(context):
            chunks.append(chunk)

        # Verify streaming
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0
        assert mock_provider.call_count == 1

    async def test_custom_command_expansion_with_complex_template(
        self, custom_registry_with_commands
    ):
        """Test custom command with complex Jinja2 template."""
        # Create command with conditionals
        complex_command = {
            "name": "complex-test",
            "description": "Complex test",
            "template": """Analizza:
Cliente: {{ arg1 }}
{% if arg2 %}Servizio: {{ arg2 }}{% endif %}
{% if arg3 %}Importo: {{ arg3 }}€{% else %}Importo: da definire{% endif %}""",
        }

        # Manually add to registry
        from openfatture.cli.commands.custom_commands import CustomCommand

        cmd = CustomCommand(**complex_command)
        custom_registry_with_commands._commands["complex-test"] = cmd

        # Test with all args
        result1 = custom_registry_with_commands.execute(
            "complex-test", args=["Client A", "Service B", "200"]
        )
        assert "Client A" in result1
        assert "Service B" in result1
        assert "200€" in result1

        # Test with missing optional arg
        result2 = custom_registry_with_commands.execute("complex-test", args=["Client C"])
        assert "Client C" in result2
        assert "da definire" in result2

    async def test_multiple_custom_commands_in_sequence(
        self, mock_provider, custom_registry_with_commands
    ):
        """Test executing multiple custom commands in sequence."""
        agent = ChatAgent(provider=mock_provider, enable_tools=False)

        # Execute first command
        expanded1 = custom_registry_with_commands.execute("cliente-test", args=["Client A"])
        context1 = ChatContext(user_input=expanded1)
        response1 = await agent.execute(context1)

        assert response1.status == ResponseStatus.SUCCESS

        # Execute second command
        expanded2 = custom_registry_with_commands.execute(
            "fattura-test", args=["Client B", "Service X", "150"]
        )
        context2 = ChatContext(user_input=expanded2)
        response2 = await agent.execute(context2)

        assert response2.status == ResponseStatus.SUCCESS
        assert mock_provider.call_count == 2

    async def test_custom_command_error_handling(
        self, mock_provider, custom_registry_with_commands
    ):
        """Test error handling when custom command fails."""
        # Try to execute non-existent command
        with pytest.raises(ValueError, match="not found"):
            custom_registry_with_commands.execute("nonexistent-command")

        # Verify agent wasn't called
        assert mock_provider.call_count == 0

    async def test_custom_command_with_conversation_history(
        self, mock_provider, custom_registry_with_commands
    ):
        """Test custom command with existing conversation history."""
        # Create context with history
        from openfatture.ai.domain.message import ConversationHistory

        history = ConversationHistory()
        history.add_message(Message(role=Role.USER, content="Ciao"))
        history.add_message(Message(role=Role.ASSISTANT, content="Ciao! Come posso aiutarti?"))

        # Expand command
        expanded = custom_registry_with_commands.execute("cliente-test", args=["Previous Client"])

        # Create context with history
        context = ChatContext(user_input=expanded, conversation_history=history)

        # Execute agent
        agent = ChatAgent(provider=mock_provider)
        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        # Verify history was included in context
        assert len(context.conversation_history.messages) == 2


@pytest.mark.asyncio
class TestCustomCommandsWithTools:
    """Integration tests for custom commands with tool calling."""

    async def test_custom_command_triggers_tool_call(
        self, mock_provider, custom_registry_with_commands
    ):
        """Test that custom command can trigger tool calls."""
        # This test verifies that expanded commands work with tool-enabled agents
        # In a real scenario, tools would be invoked based on the expanded prompt

        agent = ChatAgent(provider=mock_provider, enable_tools=True)

        # Expand command that should trigger tools
        expanded = custom_registry_with_commands.execute("cliente-test", args=["Search Term"])

        context = ChatContext(user_input=expanded, enable_tools=True)

        # Execute (in real scenario, tools would be called)
        response = await agent.execute(context)

        assert response.status == ResponseStatus.SUCCESS
        # Tool registry should be available
        assert agent.tool_registry is not None


@pytest.mark.asyncio
class TestCustomCommandsPerformance:
    """Performance tests for custom commands."""

    async def test_command_expansion_latency(self, custom_registry_with_commands):
        """Test that command expansion is fast."""
        import time

        # Measure expansion time
        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            custom_registry_with_commands.execute("fattura-test", args=["Client", "Service", "100"])

        end = time.perf_counter()
        avg_latency_ms = ((end - start) / iterations) * 1000

        # Should be < 5ms per expansion
        assert avg_latency_ms < 5.0, f"Average latency {avg_latency_ms:.2f}ms exceeds 5ms target"

    async def test_registry_load_performance(self, temp_commands_dir):
        """Test registry loading performance with many commands."""
        import time

        # Create 50 test commands
        for i in range(50):
            command_data = {
                "name": f"test-cmd-{i}",
                "description": f"Test command {i}",
                "template": f"Execute test {i} for {{{{ arg1 }}}}",
            }
            file_path = temp_commands_dir / f"cmd{i}.yaml"
            with open(file_path, "w") as f:
                yaml.dump(command_data, f)

        # Measure load time
        start = time.perf_counter()
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)
        end = time.perf_counter()

        load_time_ms = (end - start) * 1000

        # Should load 50 commands in < 100ms
        assert (
            load_time_ms < 100.0
        ), f"Load time {load_time_ms:.2f}ms exceeds 100ms target for 50 commands"
        assert len(registry.list_commands()) == 50
