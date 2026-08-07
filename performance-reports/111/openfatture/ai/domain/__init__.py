"""Domain models for AI agents."""

from openfatture.ai.domain.agent import AgentConfig, AgentProtocol, BaseAgent
from openfatture.ai.domain.context import (
    AgentContext,
    AgentResult,
    CashFlowContext,
    ComplianceContext,
    InvoiceContext,
    PaymentInsightContext,
    TaxContext,
)
from openfatture.ai.domain.message import ConversationHistory, Message, Role
from openfatture.ai.domain.prompt import PromptManager, PromptTemplate, create_prompt_manager
from openfatture.ai.domain.response import (
    AgentResponse,
    ResponseStatus,
    StreamChunk,
    ToolCall,
    UsageMetrics,
)

__all__ = [
    # Agent
    "AgentConfig",
    "AgentProtocol",
    "BaseAgent",
    # Context
    "AgentContext",
    "AgentResult",
    "InvoiceContext",
    "TaxContext",
    "CashFlowContext",
    "ComplianceContext",
    "PaymentInsightContext",
    # Message
    "Message",
    "Role",
    "ConversationHistory",
    # Prompt
    "PromptTemplate",
    "PromptManager",
    "create_prompt_manager",
    # Response
    "AgentResponse",
    "ResponseStatus",
    "StreamChunk",
    "ToolCall",
    "UsageMetrics",
]
