"""Domain models for AI agents."""

from openfatture.ai.domain.agent import BaseAgent
from openfatture.ai.domain.agent_contract import AgentConfig, AgentProtocol
from openfatture.ai.domain.context import (
    AgentContext,
    AgentResult,
    CashFlowContext,
    ComplianceContext,
    InvoiceContext,
    TaxContext,
)
from openfatture.ai.domain.message import ConversationHistory, Message, Role
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
    # Message
    "Message",
    "Role",
    "ConversationHistory",
    # Response
    "AgentResponse",
    "ResponseStatus",
    "StreamChunk",
    "ToolCall",
    "UsageMetrics",
]
