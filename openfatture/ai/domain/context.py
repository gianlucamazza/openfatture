"""Context models for AI agent execution."""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from openfatture.ai.domain.message import ConversationHistory
from openfatture.storage.database.models import Cliente, Fattura


class AgentContext(BaseModel):
    """
    Base context passed to agents for execution.

    Contains all information needed for the agent to make decisions:
    - User input
    - Historical data
    - Business rules
    - Preferences
    - Execution metadata
    """

    # User input
    user_input: str
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Domain entities (optional)
    cliente: Optional[Cliente] = None
    fattura: Optional[Fattura] = None
    fatture_recenti: list[Fattura] = Field(default_factory=list)

    # Conversation management
    conversation_history: ConversationHistory = Field(default_factory=ConversationHistory)

    # Business context
    regime_fiscale: Optional[str] = None
    settore_attivita: Optional[str] = None
    lingua_preferita: str = "it"

    # Execution metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Feature flags
    enable_streaming: bool = False
    enable_tools: bool = False
    enable_rag: bool = False

    # Limits
    max_tokens: int = 2000
    timeout_seconds: int = 30

    # Additional data
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def add_user_message(self, content: str) -> None:
        """Add a user message to conversation history."""
        self.conversation_history.add_user_message(content)

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to conversation history."""
        self.conversation_history.add_assistant_message(content)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "user_input": self.user_input[:100],  # Truncate for logging
            "correlation_id": self.correlation_id,
            "has_cliente": self.cliente is not None,
            "has_fattura": self.fattura is not None,
            "regime_fiscale": self.regime_fiscale,
            "settore_attivita": self.settore_attivita,
            "lingua": self.lingua_preferita,
            "message_count": len(self.conversation_history.messages),
            "timestamp": self.timestamp.isoformat(),
        }


class InvoiceContext(AgentContext):
    """
    Specialized context for invoice-related agents.

    Used by Invoice Assistant to generate descriptions.
    """

    # Service details
    servizio_base: Optional[str] = None
    ore_lavorate: Optional[float] = None
    tariffa_oraria: Optional[float] = None
    giorni_lavoro: Optional[int] = None

    # Project details
    progetto: Optional[str] = None
    deliverables: list[str] = Field(default_factory=list)
    tecnologie: list[str] = Field(default_factory=list)

    # Context from history
    descrizioni_simili: list[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


class TaxContext(AgentContext):
    """
    Specialized context for tax advisor agent.

    Used to determine correct VAT treatment and tax codes.
    """

    # Service details
    tipo_servizio: str
    categoria_servizio: Optional[str] = None
    importo: float = 0.0

    # Client details
    cliente_pa: bool = False  # Public administration
    cliente_estero: bool = False
    paese_cliente: str = "IT"

    # Special cases
    reverse_charge: bool = False
    split_payment: bool = False
    regime_speciale: Optional[str] = None

    # Supporting evidence
    codice_ateco: Optional[str] = None
    contratto_tipo: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class CashFlowContext(AgentContext):
    """
    Specialized context for cash flow prediction.

    Used to forecast payment timing based on historical data.
    """

    # Invoice details
    importo_fattura: float
    data_emissione: datetime
    giorni_pagamento_contratto: Optional[int] = None

    # Client history
    pagamenti_cliente: list[dict[str, Any]] = Field(default_factory=list)
    media_giorni_pagamento_cliente: Optional[float] = None

    # Sector data
    media_giorni_settore: Optional[float] = None
    stagionalita: Optional[str] = None  # Month/quarter

    # Risk factors
    importo_insolito: bool = False
    cliente_nuovo: bool = False

    class Config:
        arbitrary_types_allowed = True


class ComplianceContext(AgentContext):
    """
    Specialized context for compliance checking.

    Used to validate invoices before SDI submission.
    """

    # Invoice to check
    fattura: Fattura  # Required

    # Validation rules
    check_xsd: bool = True
    check_business_rules: bool = True
    check_best_practices: bool = True

    # Historical data for learning
    rejection_history: list[dict[str, Any]] = Field(default_factory=list)

    # Severity threshold
    min_severity_to_report: str = "WARNING"

    class Config:
        arbitrary_types_allowed = True


class AgentResult(BaseModel):
    """
    Result of agent execution with structured output.

    Generic wrapper for different agent outputs.
    """

    success: bool
    data: dict[str, Any]
    error: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "confidence": self.confidence,
        }


class ChatContext(AgentContext):
    """
    Specialized context for general chat assistant.

    Used for multi-turn conversational AI with tool calling capabilities.
    Enriched with business data and history.
    """

    # Tool calling
    available_tools: list[str] = Field(default_factory=list)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)

    # Business data enrichment
    recent_invoices_summary: Optional[str] = None
    recent_clients_summary: Optional[str] = None
    current_year_stats: Optional[dict[str, Any]] = None

    # User preferences
    preferred_response_style: str = "professional"  # professional, casual, technical
    language: str = "it"

    # RAG context (if enabled)
    similar_conversations: list[str] = Field(default_factory=list)
    relevant_documents: list[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True
