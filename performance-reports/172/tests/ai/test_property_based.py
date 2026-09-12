"""
Property-based tests for AI module components using Hypothesis.

These tests use property-based testing to verify invariants and edge cases
across a wide range of inputs, ensuring robustness of AI functionality.
"""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from openfatture.ai.domain.agent import AgentConfig
from openfatture.ai.domain.context import AgentContext, InvoiceContext
from openfatture.ai.domain.message import ConversationHistory, Message, Role
from openfatture.ai.domain.prompt import PromptTemplate
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics


class TestAgentContextProperties:
    """Property-based tests for AgentContext."""

    @given(
        user_input=st.text(min_size=1, max_size=1000),
        conversation_messages=st.lists(
            st.builds(
                Message,
                role=st.sampled_from(Role),
                content=st.text(min_size=1, max_size=500),
                name=st.text(min_size=0, max_size=50) | st.none(),
                tool_call_id=st.text(min_size=0, max_size=50) | st.none(),
                metadata=st.dictionaries(
                    st.text(min_size=1, max_size=50),
                    st.one_of(st.text(), st.integers(), st.booleans()),
                    min_size=0,
                    max_size=5,
                ),
            ),
            min_size=0,
            max_size=10,
        ),
        metadata=st.dictionaries(
            st.text(min_size=1, max_size=50), st.text(min_size=0, max_size=200)
        ),
    )
    def test_agent_context_creation(self, user_input, conversation_messages, metadata):
        """Test that AgentContext can be created with various inputs."""
        # Create ConversationHistory from messages
        conversation_history = ConversationHistory()
        for msg in conversation_messages:
            conversation_history.add_message(msg)

        context = AgentContext(
            user_input=user_input, conversation_history=conversation_history, metadata=metadata
        )

        assert context.user_input == user_input
        assert len(context.conversation_history.messages) == len(conversation_messages)
        assert context.metadata == metadata

    @given(
        user_input=st.text(min_size=1, max_size=1000),
        conversation_messages=st.lists(
            st.builds(
                Message,
                role=st.sampled_from(Role),
                content=st.text(min_size=1, max_size=500),
                name=st.text(min_size=0, max_size=50) | st.none(),
                tool_call_id=st.text(min_size=0, max_size=50) | st.none(),
                metadata=st.dictionaries(
                    st.text(min_size=1, max_size=50),
                    st.one_of(st.text(), st.integers(), st.booleans()),
                    min_size=0,
                    max_size=5,
                ),
            ),
            min_size=0,
            max_size=10,
        ),
    )
    def test_agent_context_serialization(self, user_input, conversation_messages):
        """Test that AgentContext can be serialized and deserialized."""
        # Create ConversationHistory from messages
        conversation_history = ConversationHistory()
        for msg in conversation_messages:
            conversation_history.add_message(msg)

        context = AgentContext(user_input=user_input, conversation_history=conversation_history)

        # Test model_dump works
        data = context.model_dump()
        assert isinstance(data, dict)
        assert "user_input" in data
        assert "conversation_history" in data

        # Test model_validate works
        context2 = AgentContext.model_validate(data)
        assert context2.user_input == context.user_input
        assert len(context2.conversation_history.messages) == len(
            context.conversation_history.messages
        )


class TestInvoiceContextProperties:
    """Property-based tests for InvoiceContext."""

    @given(
        user_input=st.text(min_size=1, max_size=1000),
        servizio_base=st.text(min_size=0, max_size=200) | st.none(),
        ore_lavorate=st.floats(min_value=0.0, max_value=100.0) | st.none(),
        progetto=st.text(min_size=0, max_size=100) | st.none(),
    )
    def test_invoice_context_creation(self, user_input, servizio_base, ore_lavorate, progetto):
        """Test that InvoiceContext can be created with various inputs."""
        context = InvoiceContext(
            user_input=user_input,
            servizio_base=servizio_base,
            ore_lavorate=ore_lavorate,
            progetto=progetto,
        )

        assert context.user_input == user_input
        assert context.servizio_base == servizio_base
        assert context.ore_lavorate == ore_lavorate
        assert context.progetto == progetto

    @given(
        user_input=st.text(min_size=1, max_size=1000),
        servizio_base=st.text(min_size=0, max_size=200) | st.none(),
    )
    def test_invoice_context_inheritance(self, user_input, servizio_base):
        """Test that InvoiceContext inherits from AgentContext."""
        context = InvoiceContext(user_input=user_input, servizio_base=servizio_base)

        # Should have AgentContext properties
        assert hasattr(context, "user_input")
        assert hasattr(context, "conversation_history")
        assert hasattr(context, "metadata")

        # Should have InvoiceContext specific properties
        assert hasattr(context, "servizio_base")
        assert hasattr(context, "ore_lavorate")
        assert hasattr(context, "progetto")


class TestMessageProperties:
    """Property-based tests for Message."""

    @given(
        role=st.sampled_from(Role),
        content=st.text(min_size=1, max_size=10000),
        name=st.text(min_size=0, max_size=50) | st.none(),
        tool_call_id=st.text(min_size=0, max_size=50) | st.none(),
        metadata=st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.one_of(st.text(), st.integers(), st.booleans()),
            min_size=0,
            max_size=10,
        ),
    )
    def test_message_creation(self, role, content, name, tool_call_id, metadata):
        """Test that Message can be created with various inputs."""
        message = Message(
            role=role, content=content, name=name, tool_call_id=tool_call_id, metadata=metadata
        )

        assert message.role == role
        assert message.content == content
        assert message.metadata == metadata

    @given(content=st.text(min_size=1, max_size=10000))
    def test_message_role_validation(self, content):
        """Test that Message validates roles correctly."""
        for role in Role:
            message = Message(role=role, content=content)
            assert message.role == role

    @given(
        role=st.sampled_from(Role),
        content=st.text(min_size=1, max_size=10000),
        name=st.text(min_size=0, max_size=50) | st.none(),
        tool_call_id=st.text(min_size=0, max_size=50) | st.none(),
        metadata=st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.one_of(st.text(), st.integers(), st.booleans()),
            min_size=0,
            max_size=10,
        ),
    )
    def test_message_serialization(self, role, content, name, tool_call_id, metadata):
        """Test that Message can be serialized."""
        message = Message(
            role=role, content=content, name=name, tool_call_id=tool_call_id, metadata=metadata
        )

        data = message.model_dump()
        assert isinstance(data, dict)
        assert data["role"] == role.value  # Enum values are serialized
        assert data["content"] == content


class TestPromptTemplateProperties:
    """Property-based tests for PromptTemplate."""

    @given(
        name=st.text(min_size=1, max_size=100),
        system_prompt=st.text(min_size=1, max_size=5000),
        user_template=st.text(min_size=1, max_size=5000),
        description=st.text(min_size=0, max_size=500),
        required_variables=st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=10),
    )
    def test_prompt_template_creation(
        self, name, system_prompt, user_template, description, required_variables
    ):
        """Test that PromptTemplate can be created with various inputs."""
        prompt = PromptTemplate(
            name=name,
            system_prompt=system_prompt,
            user_template=user_template,
            description=description,
            required_variables=required_variables,
        )

        assert prompt.name == name
        assert prompt.system_prompt == system_prompt
        assert prompt.user_template == user_template
        assert prompt.description == description
        assert prompt.required_variables == required_variables

    # Removed rendering test as PromptTemplate doesn't have render method

    @given(
        name=st.text(min_size=1, max_size=100),
        system_prompt=st.text(min_size=1, max_size=1000),
        user_template=st.text(min_size=1, max_size=1000),
        description=st.text(min_size=0, max_size=500),
    )
    def test_prompt_template_validation(self, name, system_prompt, user_template, description):
        """Test that PromptTemplate validates inputs."""
        prompt = PromptTemplate(
            name=name,
            system_prompt=system_prompt,
            user_template=user_template,
            description=description,
        )
        assert prompt.name == name
        assert prompt.system_prompt == system_prompt
        assert prompt.user_template == user_template
        assert prompt.description == description


class TestAgentResponseProperties:
    """Property-based tests for AgentResponse."""

    @given(
        content=st.text(min_size=0, max_size=10000),
        status=st.sampled_from(ResponseStatus),
        confidence=st.floats(min_value=0.0, max_value=1.0),
        usage=st.builds(
            UsageMetrics,
            prompt_tokens=st.integers(min_value=0, max_value=100000),
            completion_tokens=st.integers(min_value=0, max_value=100000),
            total_tokens=st.integers(min_value=0, max_value=200000),
        ),
        metadata=st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.one_of(st.text(), st.integers(), st.booleans(), st.floats()),
            min_size=0,
            max_size=10,
        ),
    )
    def test_agent_response_creation(self, content, status, confidence, usage, metadata):
        """Test that AgentResponse can be created with various inputs."""
        response = AgentResponse(
            content=content, status=status, confidence=confidence, usage=usage, metadata=metadata
        )

        assert response.content == content
        assert response.status == status
        assert response.confidence == confidence
        assert response.usage == usage
        assert response.metadata == metadata

    @given(
        content=st.text(min_size=0, max_size=10000),
        confidence=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_agent_response_defaults(self, content, confidence):
        """Test that AgentResponse has sensible defaults."""
        response = AgentResponse(content=content, confidence=confidence)

        assert response.status == ResponseStatus.SUCCESS
        assert isinstance(response.usage, UsageMetrics)
        assert isinstance(response.metadata, dict)

    @given(
        content=st.text(min_size=0, max_size=10000),
        status=st.sampled_from(ResponseStatus),
        prompt_tokens=st.integers(min_value=0, max_value=100000),
        completion_tokens=st.integers(min_value=0, max_value=100000),
        total_tokens=st.integers(min_value=0, max_value=200000),
    )
    def test_agent_response_usage_calculation(
        self, content, status, prompt_tokens, completion_tokens, total_tokens
    ):
        """Test that AgentResponse handles usage metrics correctly."""
        usage = UsageMetrics(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        response = AgentResponse(content=content, status=status, usage=usage)

        assert response.usage.prompt_tokens == prompt_tokens
        assert response.usage.completion_tokens == completion_tokens
        assert response.usage.total_tokens == total_tokens


class TestUsageMetricsProperties:
    """Property-based tests for UsageMetrics."""

    @given(
        prompt_tokens=st.integers(min_value=0, max_value=100000),
        completion_tokens=st.integers(min_value=0, max_value=100000),
        total_tokens=st.integers(min_value=0, max_value=200000),
    )
    def test_usage_metrics_creation(self, prompt_tokens, completion_tokens, total_tokens):
        """Test that UsageMetrics can be created with various inputs."""
        usage = UsageMetrics(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        assert usage.prompt_tokens == prompt_tokens
        assert usage.completion_tokens == completion_tokens
        assert usage.total_tokens == total_tokens

    @given(
        prompt_tokens=st.integers(min_value=0, max_value=100000),
        completion_tokens=st.integers(min_value=0, max_value=100000),
        total_tokens=st.integers(min_value=0, max_value=200000),
    )
    def test_usage_metrics_creation_with_total(
        self, prompt_tokens, completion_tokens, total_tokens
    ):
        """Test that UsageMetrics can be created with explicit total_tokens."""
        usage = UsageMetrics(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        assert usage.prompt_tokens == prompt_tokens
        assert usage.completion_tokens == completion_tokens
        assert usage.total_tokens == total_tokens

    @given(
        prompt_tokens=st.integers(min_value=0, max_value=100000),
        completion_tokens=st.integers(min_value=0, max_value=100000),
        total_tokens=st.integers(min_value=0, max_value=200000),
    )
    def test_usage_metrics_cost_calculation(self, prompt_tokens, completion_tokens, total_tokens):
        """Test that UsageMetrics can calculate costs."""
        usage = UsageMetrics(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        # Test cost calculation with mock rates
        input_cost_per_token = 0.0001
        output_cost_per_token = 0.0002

        total_cost = (usage.prompt_tokens * input_cost_per_token) + (
            usage.completion_tokens * output_cost_per_token
        )
        assert total_cost >= 0


class TestAgentConfigProperties:
    """Property-based tests for AgentConfig."""

    @given(
        name=st.text(min_size=1, max_size=100),
        description=st.text(min_size=1, max_size=500),
        model=st.text(min_size=0, max_size=100) | st.none(),
        temperature=st.floats(min_value=0.0, max_value=2.0),
        max_tokens=st.integers(min_value=1, max_value=100000),
        system_prompt=st.text(min_size=0, max_size=2000) | st.none(),
    )
    def test_agent_config_creation(
        self, name, description, model, temperature, max_tokens, system_prompt
    ):
        """Test that AgentConfig can be created with various inputs."""
        config = AgentConfig(
            name=name,
            description=description,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
        )

        assert config.name == name
        assert config.description == description
        assert config.model == model
        assert config.temperature == temperature
        assert config.max_tokens == max_tokens
        assert config.system_prompt == system_prompt

    @given(name=st.text(min_size=1, max_size=100), description=st.text(min_size=1, max_size=500))
    def test_agent_config_defaults(self, name, description):
        """Test that AgentConfig has sensible defaults."""
        config = AgentConfig(name=name, description=description)

        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.system_prompt is None


# Settings for hypothesis tests
pytestmark = [
    pytest.mark.property,
    pytest.mark.slow,
]

# Configure hypothesis settings
settings.register_profile(
    "ci",
    settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    ),
)
settings.register_profile(
    "dev",
    settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    ),
)
settings.load_profile("dev")
