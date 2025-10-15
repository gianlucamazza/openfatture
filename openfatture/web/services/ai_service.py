"""AI service adapter for Streamlit web interface.

Provides async/sync bridge and simplified API for AI operations.
"""

from collections.abc import AsyncGenerator
from typing import Any

import streamlit as st

from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.agents.tax_advisor import TaxAdvisorAgent
from openfatture.ai.domain.context import ChatContext, InvoiceContext, TaxContext
from openfatture.ai.domain.message import ConversationHistory, Message, Role
from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.providers.factory import create_provider
from openfatture.utils.config import DebugConfig, get_settings
from openfatture.web.utils.async_helpers import run_async


class StreamlitAIService:
    """Adapter service for AI operations in Streamlit."""

    def __init__(self, debug_config: DebugConfig | None = None) -> None:
        """Initialize service with AI provider."""
        self._provider: Any = None
        self._chat_agent: ChatAgent | None = None
        self._invoice_agent: InvoiceAssistantAgent | None = None
        self._tax_agent: TaxAdvisorAgent | None = None
        self.debug_config = debug_config or get_settings().debug_config

    def _convert_history(self, history: list[dict[str, str]]) -> ConversationHistory:
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

    @property
    def provider(self) -> Any:
        """Get or create AI provider (cached)."""
        if self._provider is None:
            self._provider = create_provider()
        return self._provider

    @property
    def chat_agent(self) -> ChatAgent:
        """Get or create chat agent (cached)."""
        if self._chat_agent is None:
            self._chat_agent = ChatAgent(
                provider=self.provider, enable_streaming=True, debug_config=self.debug_config
            )
        return self._chat_agent

    @property
    def invoice_agent(self) -> InvoiceAssistantAgent:
        """Get or create invoice assistant agent (cached)."""
        if self._invoice_agent is None:
            self._invoice_agent = InvoiceAssistantAgent(provider=self.provider)
        return self._invoice_agent

    @property
    def tax_agent(self) -> TaxAdvisorAgent:
        """Get or create tax advisor agent (cached)."""
        if self._tax_agent is None:
            self._tax_agent = TaxAdvisorAgent(provider=self.provider)
        return self._tax_agent

    def chat(self, message: str, conversation_history: list[dict[str, str]]) -> AgentResponse:
        """
        Send a chat message and get response.

        Args:
            message: User message
            conversation_history: Previous conversation

        Returns:
            Agent response with content and metadata
        """
        context = ChatContext(
            user_input=message, conversation_history=self._convert_history(conversation_history)
        )

        return run_async(self.chat_agent.execute(context))

    async def chat_stream(
        self, message: str, conversation_history: list[dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """
        Send a chat message and stream response chunks.

        Args:
            message: User message
            conversation_history: Previous conversation

        Yields:
            Response text chunks
        """
        context = ChatContext(
            user_input=message, conversation_history=self._convert_history(conversation_history)
        )

        async for chunk in self.chat_agent.execute_stream(context):
            yield chunk

    def generate_invoice_description(
        self,
        servizio: str,
        ore: float | None = None,
        tariffa: float | None = None,
        progetto: str | None = None,
        tecnologie: list[str] | None = None,
    ) -> AgentResponse:
        """
        Generate detailed invoice description using AI.

        Args:
            servizio: Service description
            ore: Hours worked
            tariffa: Hourly rate
            progetto: Project name
            tecnologie: Technologies used

        Returns:
            Agent response with generated description
        """
        context = InvoiceContext(
            user_input=servizio,
            servizio_base=servizio,
            ore_lavorate=ore,
            tariffa_oraria=tariffa,
            progetto=progetto,
            tecnologie=tecnologie or [],
        )

        return run_async(self.invoice_agent.execute(context))

    def suggest_vat(
        self,
        description: str,
        cliente_pa: bool = False,
        cliente_estero: bool = False,
        paese_cliente: str = "IT",
        importo: float = 0.0,
        categoria: str | None = None,
    ) -> AgentResponse:
        """
        Get VAT rate suggestion using AI tax advisor.

        Args:
            description: Service/product description
            cliente_pa: Whether client is Public Administration
            cliente_estero: Whether client is foreign
            paese_cliente: Client country code
            importo: Amount in EUR
            categoria: Service category

        Returns:
            Agent response with VAT suggestion
        """
        context = TaxContext(
            user_input=description,
            tipo_servizio=description,
            categoria_servizio=categoria,
            importo=importo,
            cliente_pa=cliente_pa,
            cliente_estero=cliente_estero,
            paese_cliente=paese_cliente,
        )

        return run_async(self.tax_agent.execute(context))

    def is_available(self) -> bool:
        """
        Check if AI services are available.

        Returns:
            True if AI is configured and working
        """
        try:
            _ = self.provider
            return True
        except Exception:
            return False


@st.cache_resource
def get_ai_service() -> StreamlitAIService:
    """
    Get cached AI service instance.

    Returns:
        Singleton AI service
    """
    return StreamlitAIService()
