# OpenFatture AI Architecture

**Phase 4 Implementation**
**Date:** October 2025
**Status:** Partially Implemented (60% Complete)
**Last Updated:** October 10, 2025

---

## Implementation Status

### ✅ Completed (Phase 4.1 & 4.2)

**Core Infrastructure:**
- ✅ LLM provider abstraction (`openfatture/ai/providers/`)
  - OpenAI provider with GPT-4, GPT-4o support
  - Anthropic provider with Claude 3.5 Sonnet support
  - Ollama provider for local models
  - Factory pattern for provider creation
- ✅ Base agent protocol (`openfatture/ai/domain/agent.py`)
  - AgentProtocol interface
  - BaseAgent implementation with common functionality
- ✅ Domain models (`openfatture/ai/domain/`)
  - Message, Role, ConversationHistory
  - AgentContext, InvoiceContext, TaxContext, **ChatContext**
  - AgentResponse with structured outputs
- ✅ Configuration management (`openfatture/ai/config/settings.py`)

**AI Agents:**
- ✅ Invoice Assistant Agent (`openfatture/ai/agents/invoice_assistant.py`)
- ✅ Tax Advisor Agent (`openfatture/ai/agents/tax_advisor.py`)
- ✅ **Chat Agent** (`openfatture/ai/agents/chat_agent.py`) - NEW!
  - Conversational AI with multi-turn context
  - Tool calling integration
  - Context enrichment

**Tool System:** (NEW!)
- ✅ Tool models (`openfatture/ai/tools/models.py`)
  - Tool, ToolParameter, ToolResult
  - OpenAI and Anthropic format conversion
- ✅ Tool registry (`openfatture/ai/tools/registry.py`)
  - Centralized tool management
  - Async tool execution
- ✅ **6 Built-in Tools:**
  - `search_invoices` - Search invoices by criteria
  - `get_invoice_details` - Get invoice details
  - `get_invoice_stats` - Invoice statistics
  - `search_clients` - Search clients
  - `get_client_details` - Get client details
  - `get_client_stats` - Client statistics

**Session Management:** (NEW!)
- ✅ Session models (`openfatture/ai/session/models.py`)
  - ChatSession, ChatMessage, SessionMetadata
  - Token and cost tracking
- ✅ Session manager (`openfatture/ai/session/manager.py`)
  - CRUD operations with atomic persistence
  - JSON-based storage
  - Session export (JSON/Markdown)

**Context & Prompts:**
- ✅ Context enrichment (`openfatture/ai/context/enrichment.py`)
  - Automatic business data injection
  - Current year statistics
  - Recent invoices/clients summaries
- ✅ YAML prompt templates (`openfatture/ai/prompts/`)
  - invoice_assistant.yaml
  - tax_advisor.yaml
  - **chat_assistant.yaml** - NEW!

**UI Integration:**
- ✅ Interactive chat UI (`openfatture/cli/ui/chat.py`)
  - Rich terminal interface with markdown
  - Command system (/help, /save, /tools, etc.)
  - Real-time token/cost tracking
- ✅ CLI commands (`openfatture/cli/commands/ai.py`)
  - `ai describe` - Functional
  - `ai suggest-vat` - Functional
- `ai forecast` - Functional (Prophet + XGBoost ensemble con modelli/versioni salvati)
  - `ai check` - Stub

### 🚧 Partially Implemented

- 🔄 RAG / Vector Store
  - ChromaDB persistence for invoices + knowledge base (`openfatture/ai/rag/**`)
  - Async enrichment pipeline (`enrich_with_rag`) for chat, invoice, and tax advisor agents
  - CLI management commands (`openfatture ai rag status|index|search`)
  - Knowledge base manifest (`openfatture/ai/rag/sources.json`) with dedicated indexer
  - Legal citations surfaced within Chat/Tax/Invoice agents

### ⏳ Planned (Phase 4.3 & 4.4)

- [ ] Compliance Checker agent
- [ ] LangGraph orchestration for multi-agent workflows
- [x] Complete RAG implementation with ChromaDB (invoice + knowledge collections)
- [ ] Streaming response support
- [ ] Advanced caching strategies
- [ ] Metrics and observability dashboards

### ✅ Cash Flow Predictor (v1.0.1)

- Prophet + XGBoost ensemble with tunable weights (`openfatture/ai/ml/models/ensemble.py`)
- Persistent feature engineering pipeline (`FeaturePipeline`) with versioned schema
- Chronological dataset loader with metadata and caching (`InvoiceDataLoader`)
- Training metrics (`mae`, `rmse`, interval coverage) and provenance saved to `<model_prefix>_metrics.json`
- Artefacts stored in `MLConfig.model_path` (default `.models/`):
  - `_prophet.json` + `_xgboost.json`
  - `_pipeline.pkl` (pipeline/scaler/schema)
  - `_metrics.json`
- CLI `openfatture ai forecast --retrain` forces retraining; default reuses existing models
- Optional AI insights when a provider is configured (deterministic fallback otherwise)

---

## Overview

This document outlines the architecture for OpenFatture's AI-powered features, following 2025 best practices for production-ready LLM applications.

### Design Principles

1. **Provider Agnostic** - Support multiple LLM providers (OpenAI, Anthropic, Ollama)
2. **Type Safe** - Full type hints with Pydantic models
3. **Testable** - Mockable interfaces, dependency injection
4. **Observable** - Structured logging, metrics, tracing
5. **Secure** - API key management, input validation
6. **Cost Aware** - Token tracking, caching, fallbacks
7. **Resilient** - Retry logic, circuit breakers, graceful degradation

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│                  (CLI Commands - Existing)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Application Layer                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐ │
│  │  Invoice   │ │    Tax     │ │ Cash Flow  │ │Compliance│ │
│  │ Assistant  │ │  Advisor   │ │ Predictor  │ │ Checker  │ │
│  │   Agent    │ │   Agent    │ │   Agent    │ │  Agent   │ │
│  └────────────┘ └────────────┘ └────────────┘ └──────────┘ │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │      Multi-Agent Orchestrator (LangGraph)             │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                     Domain Layer                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │   Agent    │ │   Prompt   │ │   Memory   │              │
│  │  Protocol  │ │  Template  │ │  Manager   │              │
│  └────────────┘ └────────────┘ └────────────┘              │
│                                                               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │  Response  │ │   Tool     │ │  Context   │              │
│  │   Models   │ │ Definition │ │   Models   │              │
│  └────────────┘ └────────────┘ └────────────┘              │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 Infrastructure Layer                         │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │  OpenAI    │ │ Anthropic  │ │   Ollama   │              │
│  │  Provider  │ │  Provider  │ │  Provider  │              │
│  └────────────┘ └────────────┘ └────────────┘              │
│                                                               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │  ChromaDB  │ │   Cache    │ │   Metrics  │              │
│  │  Vectors   │ │   Layer    │ │  Tracker   │              │
│  └────────────┘ └────────────┘ └────────────┘              │
└───────────────────────────────────────────────────────────────┘
```

---

## Module Structure

```
openfatture/ai/
├── __init__.py                    # Public API exports
│
├── config/                        # ✅ Configuration management
│   ├── __init__.py
│   └── settings.py               # AISettings (Pydantic)
│
├── domain/                        # ✅ Core domain models
│   ├── __init__.py
│   ├── agent.py                  # AgentProtocol, BaseAgent
│   ├── message.py                # Message, Role enums
│   ├── prompt.py                 # PromptTemplate, PromptManager
│   ├── context.py                # AgentContext, InvoiceContext, TaxContext, ChatContext
│   └── response.py               # AgentResponse, structured outputs
│
├── providers/                     # ✅ LLM provider implementations
│   ├── __init__.py
│   ├── base.py                   # BaseLLMProvider (ABC)
│   ├── openai.py                 # OpenAIProvider
│   ├── anthropic.py              # AnthropicProvider
│   ├── ollama.py                 # OllamaProvider
│   └── factory.py                # create_provider() factory
│
├── agents/                        # ✅ Agent implementations (3/4 complete)
│   ├── __init__.py
│   ├── invoice_assistant.py      # ✅ InvoiceAssistantAgent
│   ├── tax_advisor.py            # ✅ TaxAdvisorAgent
│   ├── chat_agent.py             # ✅ ChatAgent (NEW!)
│   ├── cash_flow_predictor.py    # ⏳ Planned
│   └── compliance_checker.py     # ⏳ Planned
│
├── session/                       # ✅ Session management (NEW!)
│   ├── __init__.py
│   ├── models.py                 # ChatSession, ChatMessage, SessionMetadata
│   └── manager.py                # SessionManager with CRUD operations
│
├── tools/                         # ✅ Function calling tools (NEW!)
│   ├── __init__.py
│   ├── models.py                 # Tool, ToolParameter, ToolResult
│   ├── registry.py               # ToolRegistry for centralized management
│   ├── invoice_tools.py          # Invoice search/details/stats tools
│   └── client_tools.py           # Client search/details/stats tools
│
├── context/                       # ✅ Context enrichment (NEW!)
│   ├── __init__.py
│   └── enrichment.py             # Automatic business data injection
│
├── prompts/                       # ✅ Prompt templates
│   ├── __init__.py
│   ├── invoice_assistant.yaml    # Invoice assistant prompts
│   ├── tax_advisor.yaml          # Tax advisor prompts
│   └── chat_assistant.yaml       # ✅ Chat assistant prompts (NEW!)
│
├── orchestration/                 # ⏳ Multi-agent workflows (Planned)
│   └── (LangGraph integration planned for Phase 4.4)
│
└── memory/                        # 🔄 Memory & vector store (Partial)
    └── (ChromaDB integration planned)
```

---

## Core Components

### 1. LLM Provider Abstraction

**File:** `openfatture/ai/providers/base.py`

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional

from openfatture.ai.domain.message import Message
from openfatture.ai.domain.response import AgentResponse


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Provides a unified interface for different LLM services
    (OpenAI, Anthropic, Ollama, etc.).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        **kwargs,
    ) -> AgentResponse:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream response tokens from the LLM."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text for this provider."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is available."""
        pass
```

**Design Rationale:**
- Strategy pattern for swappable providers
- Async by default for performance
- Streaming support for UX
- Health checks for resilience
- Token counting for cost control

---

### 2. Agent Protocol

**File:** `openfatture/ai/domain/agent.py`

```python
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel

from openfatture.ai.domain.context import AgentContext
from openfatture.ai.domain.response import AgentResponse


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    name: str
    description: str
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    system_prompt: Optional[str] = None
    tools_enabled: bool = False
    memory_enabled: bool = False


class AgentProtocol(ABC):
    """
    Protocol that all agents must implement.

    Defines the interface for agent execution with
    context management and structured responses.
    """

    @property
    @abstractmethod
    def config(self) -> AgentConfig:
        """Get agent configuration."""
        pass

    @abstractmethod
    async def execute(
        self,
        context: AgentContext,
        **kwargs: Any,
    ) -> AgentResponse:
        """
        Execute the agent with given context.

        Args:
            context: Agent execution context
            **kwargs: Additional arguments

        Returns:
            AgentResponse with structured output
        """
        pass

    @abstractmethod
    async def validate_input(self, context: AgentContext) -> bool:
        """Validate input before execution."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources after execution."""
        pass


class BaseAgent(AgentProtocol):
    """
    Base implementation of AgentProtocol.

    Provides common functionality for all agents:
    - Provider management
    - Logging
    - Metrics
    - Error handling
    """

    def __init__(
        self,
        config: AgentConfig,
        provider: BaseLLMProvider,
        logger: Optional[Any] = None,
    ) -> None:
        self._config = config
        self.provider = provider
        self.logger = logger or get_logger(__name__)

    @property
    def config(self) -> AgentConfig:
        return self._config

    async def execute(
        self,
        context: AgentContext,
        **kwargs: Any,
    ) -> AgentResponse:
        # Common execution logic with:
        # - Input validation
        # - Logging
        # - Metrics tracking
        # - Error handling
        # - Response parsing
        pass

    async def validate_input(self, context: AgentContext) -> bool:
        """Default validation - can be overridden."""
        return True

    async def cleanup(self) -> None:
        """Default cleanup - can be overridden."""
        pass
```

**Design Rationale:**
- Protocol pattern for type safety
- Template method pattern in BaseAgent
- Dependency injection for provider
- Structured logging and metrics
- Async-first design

---

### 3. Agent Context

**File:** `openfatture/ai/domain/context.py`

```python
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from openfatture.storage.database.models import Cliente, Fattura


class AgentContext(BaseModel):
    """
    Context passed to agents for execution.

    Contains all information needed for agent to make decisions:
    - User input
    - Historical data
    - Business rules
    - Preferences
    """

    # User input
    user_input: str
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Domain entities (optional)
    cliente: Optional[Cliente] = None
    fattura: Optional[Fattura] = None
    fatture_recenti: list[Fattura] = Field(default_factory=list)

    # Historical context
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    previous_interactions: int = 0

    # Business context
    regime_fiscale: Optional[str] = None
    settore_attivita: Optional[str] = None
    lingua_preferita: str = "it"

    # Execution metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Additional data
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class InvoiceContext(AgentContext):
    """Specialized context for invoice-related agents."""

    servizio_base: Optional[str] = None
    ore_lavorate: Optional[float] = None
    tariffa_oraria: Optional[float] = None


class TaxContext(AgentContext):
    """Specialized context for tax advisor agent."""

    tipo_servizio: Optional[str] = None
    importo: Optional[float] = None
    cliente_pa: bool = False
    reverse_charge: bool = False
```

**Design Rationale:**
- Pydantic for validation
- Specialized contexts per agent type
- Historical tracking for learning
- Correlation IDs for tracing
- Metadata for extensibility

---

### 4. Prompt Management

**File:** `openfatture/ai/domain/prompt.py`

```python
from pathlib import Path
from typing import Any, Optional

import yaml
from jinja2 import Environment, FileSystemLoader, Template

from pydantic import BaseModel


class PromptTemplate(BaseModel):
    """Structured prompt template."""

    name: str
    description: str
    system_prompt: str
    user_template: str
    few_shot_examples: list[dict[str, str]] = []
    variables: list[str] = []

    class Config:
        arbitrary_types_allowed = True


class PromptManager:
    """
    Manages prompt templates with Jinja2 rendering.

    Loads prompts from YAML files and renders them
    with context variables.
    """

    def __init__(self, templates_dir: Path) -> None:
        self.templates_dir = templates_dir
        self.env = Environment(loader=FileSystemLoader(str(templates_dir)))
        self._cache: dict[str, PromptTemplate] = {}

    def load_template(self, name: str) -> PromptTemplate:
        """Load prompt template from YAML file."""
        if name in self._cache:
            return self._cache[name]

        yaml_path = self.templates_dir / f"{name}.yaml"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        template = PromptTemplate(**data)
        self._cache[name] = template
        return template

    def render(
        self,
        template_name: str,
        variables: dict[str, Any],
    ) -> tuple[str, str]:
        """
        Render prompt template with variables.

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        template = self.load_template(template_name)

        # Render system prompt
        system_tmpl = Template(template.system_prompt)
        system_prompt = system_tmpl.render(**variables)

        # Render user prompt
        user_tmpl = Template(template.user_template)
        user_prompt = user_tmpl.render(**variables)

        return system_prompt, user_prompt
```

**Design Rationale:**
- YAML for easy prompt editing
- Jinja2 for variable interpolation
- Caching for performance
- Version control friendly
- Non-technical users can edit

---

### 5. ReAct Orchestration

**File:** `openfatture/ai/orchestration/react.py`

**Purpose:** Enable tool calling for LLM providers without native function calling support (Ollama)

**Background:**
Local LLMs via Ollama lack native function calling APIs like OpenAI and Anthropic. ReAct (Reasoning + Acting) orchestration implements tool calling through prompt engineering, allowing Ollama models to use the same tools as cloud providers.

**Architecture Components:**

**ReAct Pattern:**
```
Thought: [Reasoning about what to do]
Action: [Tool name]
Action Input: [JSON parameters]
Observation: [Tool execution result]
... (repeat until final answer)
Final Answer: [Response to user]
```

**XML Format (2025 Standard):**
```xml
<thought>Reasoning about what to do</thought>
<action>tool_name</action>
<action_input>{"param": "value"}</action_input>

<!-- After tool execution -->
<thought>Analysis of result</thought>
<final_answer>Response to user</final_answer>
```

**Key Classes:**

```python
class ToolCallParser:
    """
    Multi-strategy parser for LLM tool call responses.

    Supports:
    - XML format (primary, 2025 standard)
    - Legacy text format (fallback)
    - Malformed JSON correction
    - Case-insensitive keywords
    """

    def parse(self, response_text: str) -> ParsedResponse:
        """Parse LLM response into structured tool call or final answer."""
        # Try XML parsing first (priority)
        if xml_result := self._try_parse_xml(response_text):
            self.metrics["xml_parse_count"] += 1
            return xml_result

        # Fallback to legacy text format
        if legacy_result := self._try_parse_legacy(response_text):
            self.metrics["legacy_parse_count"] += 1
            return legacy_result

        # Treat as final answer if no format detected
        return ParsedResponse(is_final=True, content=response_text)

    def get_stats(self) -> dict:
        """Get parser statistics including XML adoption rate."""
        return {
            "total_parses": self.metrics["total_parses"],
            "xml_parse_count": self.metrics["xml_parse_count"],
            "legacy_parse_count": self.metrics["legacy_parse_count"],
            "xml_parse_rate": self.metrics["xml_parse_count"] / max(1, self.metrics["total_parses"]),
            "parse_errors": self.metrics["parse_errors"],
        }


class ReActOrchestrator:
    """
    Orchestrates ReAct loop for tool calling with Ollama.

    Flow:
    1. Build ReAct prompt with tool descriptions
    2. Send to LLM (with conversation history)
    3. Parse response (XML or legacy format)
    4. If tool call: execute tool → add observation → loop
    5. If final answer: return to user
    6. Enforce max_iterations to prevent infinite loops
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        tool_registry: ToolRegistry,
        max_iterations: int = 5,
        parser: ToolCallParser | None = None,
    ) -> None:
        self.provider = provider
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.parser = parser or ToolCallParser()

        # Metrics tracking
        self.metrics = {
            "total_executions": 0,
            "tool_calls_attempted": 0,
            "tool_calls_succeeded": 0,
            "tool_calls_failed": 0,
            "max_iterations_reached": 0,
            "total_iterations": 0,
        }

    async def execute(self, context: ChatContext) -> str:
        """Execute ReAct loop until final answer or max iterations."""
        conversation_messages = self._build_react_messages(context)

        for iteration in range(1, self.max_iterations + 1):
            # Generate LLM response
            response = await self.provider.generate(conversation_messages)

            # Parse response
            parsed = self.parser.parse(response.content)

            if parsed.is_final:
                # Final answer reached
                return parsed.content

            if parsed.tool_call:
                # Execute tool
                self.metrics["tool_calls_attempted"] += 1

                try:
                    result = await self.tool_registry.execute_tool(
                        parsed.tool_call.tool_name,
                        parsed.tool_call.parameters,
                    )

                    if result.success:
                        observation = self._format_observation(result.data)
                        self.metrics["tool_calls_succeeded"] += 1
                    else:
                        observation = f"Error: {result.error}"
                        self.metrics["tool_calls_failed"] += 1

                except Exception as e:
                    observation = f"Tool execution error: {str(e)}"
                    self.metrics["tool_calls_failed"] += 1

                # Add observation to conversation
                conversation_messages.append(
                    Message(role="user", content=f"Observation: {observation}")
                )

        # Max iterations reached
        self.metrics["max_iterations_reached"] += 1
        return "Unable to complete request within iteration limit."

    def get_metrics(self) -> dict:
        """Get comprehensive orchestrator metrics."""
        success_rate = 0.0
        if self.metrics["tool_calls_attempted"] > 0:
            success_rate = (
                self.metrics["tool_calls_succeeded"]
                / self.metrics["tool_calls_attempted"]
            )

        return {
            **self.metrics,
            "tool_call_success_rate": success_rate,
            "parser_stats": self.parser.get_stats(),
            "provider": self.provider.provider_name,
            "model": self.provider.model,
        }
```

**Design Rationale:**
- **XML-First Parsing**: XML tags are more robust than text parsing (qwen3:8b generates XML 60%+ of time)
- **Deterministic Execution**: Temperature=0.0 for reliable tool calling
- **Metrics Tracking**: Monitor tool call success rate, XML adoption, iteration counts
- **Graceful Degradation**: Fallback to legacy format if XML parsing fails
- **Safety**: Max iterations prevents infinite loops
- **Observability**: Comprehensive metrics for production monitoring

**Recommended Models:**
- **qwen3:8b** (Recommended) - 5.2 GB, optimized for tool calling, 80%+ success rate
- **mistral-small3.1** - 15 GB, more powerful but slower
- **llama3.2** - 7 GB, good general performance

**Configuration:**
```python
# AI Settings for ReAct with Ollama
OPENFATTURE_AI_PROVIDER=ollama
OPENFATTURE_AI_OLLAMA_MODEL=qwen3:8b
OPENFATTURE_AI_OLLAMA_BASE_URL=http://localhost:11434
OPENFATTURE_AI_TEMPERATURE=0.0  # Deterministic for tool calling
```

**Performance Benchmarks:**
- **Success Rate**: ≥80% across diverse queries (validated in E2E tests)
- **Average Iterations**: 2-3 per successful completion
- **XML Format Adoption**: 60%+ with qwen3:8b
- **Latency**: ~2-5s per iteration (local inference)

**Testing:**
```python
# E2E tests with real Ollama (tests/ai/test_react_e2e_ollama.py)
@pytest.mark.e2e
@pytest.mark.ollama
async def test_single_tool_call_invoice_stats(
    ollama_qwen3_provider, tool_registry_with_mock_tools
):
    """Test ReAct calls get_invoice_stats correctly."""
    orchestrator = ReActOrchestrator(
        provider=ollama_qwen3_provider,
        tool_registry=tool_registry_with_mock_tools,
        max_iterations=5,
    )

    context = ChatContext(
        user_input="Quante fatture ho emesso quest'anno?",
        enable_tools=True,
    )

    result = await orchestrator.execute(context)

    # Verify result contains expected data from tools
    assert result is not None
    assert "42" in result  # From mock invoice stats

    # Check metrics
    metrics = orchestrator.get_metrics()
    assert metrics["tool_call_success_rate"] >= 0.8
```

**Best Practices:**
1. **Always use temperature=0.0** for tool calling (deterministic output)
2. **Monitor XML parse rate** - should be 60%+ with qwen3:8b
3. **Set appropriate max_iterations** (5 for simple queries, 8+ for multi-step)
4. **Track tool call success rate** - alert if drops below 70%
5. **Use structured tool schemas** - clear descriptions and parameter types
6. **Provide few-shot examples** in system prompt for better parsing
7. **Implement retry logic** for transient failures
8. **Log all iterations** for debugging and optimization

**Common Issues:**
- **Low XML parse rate**: Model not generating XML → update prompt with more examples
- **Infinite loops**: Tool not providing expected data → validate tool outputs
- **Failed tool calls**: Invalid parameters → improve parameter descriptions
- **Max iterations reached**: Query too complex → increase max_iterations or split query

**Integration with Chat Agent:**
The Chat Agent automatically uses ReActOrchestrator when:
- Provider is Ollama
- `enable_tools=True` in ChatContext
- Tool registry has available tools

For OpenAI/Anthropic, native function calling is used instead.

---

## Agent Implementations

### Invoice Assistant Agent

**Purpose:** Generate detailed invoice descriptions from brief inputs

**Input:** "3 hours web consulting"

**Output:**
```
Professional consulting for web development and software architecture

Activities delivered:
- Analysed functional and non-functional requirements
- Designed the application architecture
- Developed front-end components with React
- Implemented authenticated REST APIs
- Performed testing and debugging
- Produced technical documentation

Duration: 3 hours
Skills: React, TypeScript, Node.js, API design
```

**Implementation Strategy:**
- RAG with previous invoice descriptions
- Few-shot examples from user's history
- Sector-specific templates
- Multilingual support (IT/EN)

---

### Tax Advisor Agent

**Purpose:** Suggest correct VAT rates and tax treatments

**Input:** "IT consulting services for a construction company"

**Output:**
```json
{
  "aliquota_iva": 22,
  "natura_iva": null,
  "reverse_charge": true,
  "split_payment": false,
  "regime_speciale": "REVERSE_CHARGE_COSTRUZIONI",
  "spiegazione": "Reverse charge applies to services rendered to the construction sector under art. 17, paragraph 6, letter a-ter of DPR 633/72.",
  "codice_iva": "N6.2",
  "note_fattura": "Reverse charge - art. 17 c. 6 lett. a-ter DPR 633/72"
}
```

**Implementation Strategy:**
- Knowledge base of Italian tax rules
- Decision tree for regime detection
- Citation of legal references
- Confidence scores
- Human review recommendation

---

### Cash Flow Predictor

**Purpose:** Forecast payment timing based on historical data

**Input:** Invoice data + client history

**Output:**
```json
{
  "predicted_payment_date": "2025-11-15",
  "confidence": 0.85,
  "expected_days": 30,
  "risk_level": "LOW",
  "factors": [
    "Client historical average: 28 days",
    "Sector average: 32 days",
    "Invoice amount: normal range",
    "Month: November (slower)"
  ],
  "recommendation": "Set reminder for day 35 (2025-11-20)",
  "probability_distribution": {
    "on_time": 0.75,
    "late_1_week": 0.15,
    "late_2_weeks": 0.08,
    "very_late": 0.02
  }
}
```

**Implementation Strategy:**
- Time series analysis with historical data
- Feature engineering (client, amount, month, sector)
- Ensemble model (XGBoost + Prophet)
- Confidence intervals
- Explainable predictions

---

### Compliance Checker

**Purpose:** Pre-validate invoices before SDI submission

**Input:** `Fattura` object

**Output:**
```json
{
  "is_compliant": false,
  "severity": "ERROR",
  "issues": [
    {
      "field": "cliente.codice_destinatario",
      "message": "Missing SDI recipient code for Public Administration customer",
      "severity": "ERROR",
      "fix": "Request the IPA recipient code from the customer"
    },
    {
      "field": "riga[0].descrizione",
      "message": "Description too generic (< 20 characters)",
      "severity": "WARNING",
      "fix": "Add details such as hours, specific activities, deliverables"
    }
  ],
  "suggestions": [
    "Consider adding the CIG for public tenders",
    "Verify whether withholding tax applies to this service"
  ],
  "estimated_sdi_approval": 0.95
}
```

**Implementation Strategy:**
- Rule-based validation (must-have)
- LLM for heuristic checks
- Learning from past rejections
- Actionable fix suggestions
- Severity classification

---

## Multi-Agent Orchestration

**File:** `openfatture/ai/orchestration/graph.py`

```python
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode


class InvoiceCreationState(TypedDict):
    """State for invoice creation workflow."""

    user_input: str
    generated_description: Annotated[str, "Invoice description"]
    tax_suggestion: Annotated[dict, "Tax treatment"]
    compliance_check: Annotated[dict, "Compliance results"]
    approved: bool
    fattura: Optional[Fattura]


async def create_invoice_workflow() -> StateGraph:
    """
    LangGraph workflow for AI-assisted invoice creation.

    Flow:
    1. User inputs brief description
    2. Invoice Assistant generates detailed description
    3. Tax Advisor suggests VAT treatment
    4. Compliance Checker validates
    5. Human approval
    6. Create invoice
    """

    workflow = StateGraph(InvoiceCreationState)

    # Add nodes
    workflow.add_node("generate_description", generate_description_node)
    workflow.add_node("suggest_tax", suggest_tax_node)
    workflow.add_node("check_compliance", check_compliance_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("create_invoice", create_invoice_node)

    # Define edges
    workflow.set_entry_point("generate_description")
    workflow.add_edge("generate_description", "suggest_tax")
    workflow.add_edge("suggest_tax", "check_compliance")
    workflow.add_edge("check_compliance", "human_approval")

    # Conditional edge based on approval
    workflow.add_conditional_edges(
        "human_approval",
        lambda state: "create" if state["approved"] else END,
        {
            "create": "create_invoice",
            END: END,
        },
    )

    workflow.add_edge("create_invoice", END)

    return workflow.compile()
```

**Design Rationale:**
- LangGraph for stateful workflows
- Type-safe state management
- Human-in-the-loop checkpoints
- Conditional branching
- Error recovery paths

---

## Configuration

**File:** `openfatture/ai/config/settings.py`

```python
from typing import Literal, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class AISettings(BaseSettings):
    """AI module configuration."""

    # Provider selection
    ai_provider: Literal["openai", "anthropic", "ollama"] = "openai"

    # API credentials
    openai_api_key: Optional[SecretStr] = None
    anthropic_api_key: Optional[SecretStr] = None
    ollama_base_url: str = "http://localhost:11434"

    # Model selection
    ai_model: str = "gpt-4-turbo-preview"
    ai_temperature: float = 0.7
    ai_max_tokens: int = 2000

    # Features
    ai_streaming: bool = True
    ai_caching_enabled: bool = True
    ai_metrics_enabled: bool = True

    # Vector store
    chromadb_host: str = "localhost"
    chromadb_port: int = 8000
    chromadb_persist_directory: str = ".chromadb"

    # Cost controls
    ai_max_cost_per_request: float = 0.50  # USD
    ai_daily_budget: float = 10.0  # USD

    # Prompts
    ai_prompts_dir: str = "openfatture/ai/prompts"

    class Config:
        env_prefix = "OPENFATTURE_"
        env_file = ".env"
```

**Design Rationale:**
- Pydantic Settings for validation
- SecretStr for API keys
- Cost controls to prevent runaway bills
- Environment variable support
- Sensible defaults

---

## Testing Strategy

### Unit Tests

```python
# tests/ai/test_invoice_assistant.py

@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider for testing."""
    provider = Mock(spec=BaseLLMProvider)
    provider.generate = AsyncMock(return_value=AgentResponse(
        content="Generated description...",
        tokens_used=150,
        cost=0.003,
    ))
    return provider


@pytest.mark.asyncio
async def test_invoice_assistant_generates_description(mock_llm_provider):
    """Test invoice assistant generates valid description."""
    agent = InvoiceAssistantAgent(
        config=AgentConfig(name="test", description="test"),
        provider=mock_llm_provider,
    )

    context = InvoiceContext(
        user_input="3 hours web consulting",
        servizio_base="consulting",
        ore_lavorate=3.0,
    )

    response = await agent.execute(context)

    assert response.success
    assert len(response.content) > 100
    assert "consulting" in response.content.lower()
    mock_llm_provider.generate.assert_called_once()
```

### Integration Tests

```python
# tests/ai/integration/test_ollama_provider.py

@pytest.mark.integration
@pytest.mark.ai
async def test_ollama_provider_real_request():
    """Test real request to local Ollama."""
    # Requires: ollama run llama3
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3",
    )

    if not await provider.health_check():
        pytest.skip("Ollama not available")

    messages = [
        Message(role="user", content="Say 'test' in Italian")
    ]

    response = await provider.generate(messages)

    assert response.content
    assert "test" in response.content.lower()
```

### Property-Based Tests

```python
# tests/ai/test_properties.py

from hypothesis import given, strategies as st


@given(st.text(min_size=5, max_size=200))
def test_prompt_rendering_never_fails(user_input: str):
    """Prompt rendering should handle any input."""
    manager = PromptManager(prompts_dir=Path("openfatture/ai/prompts"))

    # Should not raise
    system, user = manager.render(
        "invoice_assistant",
        {"user_input": user_input}
    )

    assert isinstance(system, str)
    assert isinstance(user, str)
    assert len(system) > 0
```

---

## Observability

### Logging

```python
# Structured logging for AI operations

logger.info(
    "agent_execution_started",
    agent=agent.config.name,
    correlation_id=context.correlation_id,
    user_input_length=len(context.user_input),
)

logger.info(
    "llm_request",
    provider=provider.__class__.__name__,
    model=provider.model,
    messages_count=len(messages),
    estimated_tokens=estimated_tokens,
)

logger.info(
    "agent_execution_completed",
    agent=agent.config.name,
    correlation_id=context.correlation_id,
    tokens_used=response.tokens_used,
    cost_usd=response.cost,
    duration_ms=duration,
    success=response.success,
)
```

## Security Considerations

1. **API Key Management**
   - Never log API keys
   - Use SecretStr in Pydantic
   - Support multiple secret backends
   - Rotate keys regularly

2. **Input Validation**
   - Sanitize all user inputs
   - Limit input length
   - Validate against injection attacks
   - Rate limiting per user

3. **Output Validation**
   - Parse LLM outputs safely
   - Validate structured data
   - Sanitize before database storage
   - Never execute code from LLM

4. **Cost Protection**
   - Per-request cost limits
   - Daily budget caps
   - Alert on unusual usage
   - Token counting before requests

---

## Performance Optimizations

1. **Caching**
   - Cache identical requests (24h TTL)
   - Semantic similarity caching
   - Prompt template caching
   - Vector store results caching

2. **Batching**
   - Batch similar requests
   - Parallel agent execution
   - Async/await throughout
   - Connection pooling

3. **Token Optimization**
   - Truncate long contexts
   - Use function calling when possible
   - Optimize prompt templates
   - Track token usage

---

## Implementation Phases

### ✅ Phase 4.1: Foundation (COMPLETED)
- [x] Set up module structure
- [x] Implement provider abstraction (OpenAI, Anthropic, Ollama)
- [x] Create base agent classes (AgentProtocol, BaseAgent)
- [x] Configuration management (AISettings with Pydantic)
- [x] Domain models (Message, Context, Response)
- [x] Basic tests

### ✅ Phase 4.2: Agents & Tools (COMPLETED)
- [x] Invoice Assistant agent
- [x] Tax Advisor agent
- [x] **Chat Agent** (conversational AI)
- [x] **Tool system implementation**
  - [x] Tool models and registry
  - [x] 6 built-in tools (invoice and client operations)
  - [x] Tool calling integration
- [x] **Session management**
  - [x] Session models and persistence
  - [x] Token/cost tracking
  - [x] Export functionality
- [x] **Context enrichment**
  - [x] Automatic business data injection
  - [x] Current statistics
- [x] Prompt templates (YAML)
- [x] **Interactive UI integration**
  - [x] Rich terminal chat interface
  - [x] Command system (/help, /save, /tools, etc.)
- [x] CLI integration (`ai describe`, `ai suggest-vat`)
- [x] Agent tests

### 🚧 Phase 4.3: Advanced Features (IN PROGRESS)
- [ ] Cash Flow Predictor (ML-based)
- [ ] Compliance Checker agent
- [x] Complete RAG implementation
  - [ ] Vector store integration (ChromaDB)
  - [ ] Embeddings generation
  - [ ] Semantic search
- [ ] Streaming response support
- [ ] Advanced caching strategies
- [ ] Performance optimization

### ⏳ Phase 4.4: Orchestration (PLANNED)
- [ ] LangGraph workflows
- [ ] Multi-agent coordination
- [ ] State management for complex workflows
- [ ] Human-in-the-loop checkpoints
- [ ] Advanced cost tracking and budgets
- [ ] Production observability
  - [ ] Metrics dashboards
  - [ ] Tracing integration
  - [ ] Alert systems

---

## Success Metrics

- **Accuracy:** >90% for tax suggestions
- **Adoption:** >60% of users try AI features
- **Performance:** <3s average latency
- **Cost:** <€0.10 per AI-assisted invoice
- **Errors:** <5% failure rate
- **Coverage:** 100% test coverage for critical paths

---

**Document Status:** Implementation In Progress (60% Complete)
**Current Phase:** 4.2 Complete, 4.3 In Progress
**Next Steps:**
- Complete remaining Phase 4.3 features (RAG, streaming)
- Begin Phase 4.4 (LangGraph orchestration)
**Owner:** Development Team
**Last Updated:** October 10, 2025

## Quick Links

- [Chat Assistant Guide](../examples/AI_CHAT_ASSISTANT.md)
- [Invoice Assistant Guide](../examples/AI_INVOICE_ASSISTANT.md)
- [Tax Advisor Guide](../examples/AI_TAX_ADVISOR.md)
- [Main README](../README.md)
- [Project Roadmap](history/ROADMAP.md)
