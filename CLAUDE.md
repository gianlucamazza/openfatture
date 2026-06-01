# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenFatture is an open-source electronic invoicing system for Italian freelancers, built around FatturaPA XML generation, SDI (Sistema di Interscambio) integration, AI-powered workflows, and payment reconciliation. The project uses modern Python tooling (Python 3.12+, uv package manager, SQLAlchemy ORM, Typer CLI).

**Core Features:**
- FatturaPA XML v1.9 generation and validation
- PEC email integration for SDI submission
- Digital signature support (PKCS#12)
- AI agents for invoice description, VAT guidance, and chat assistance
- Payment reconciliation with multi-bank imports
- Batch operations (CSV import/export)
- PDF generation

## Architecture

OpenFatture follows a layered architecture:

```
openfatture/
├── ai/              # AI agents, LLM providers, tools, sessions, RAG
├── cli/             # Typer CLI commands and Rich UI
├── core/            # Business logic (fatture, clienti, prodotti, batch, events, hooks)
├── payment/         # Payment reconciliation (DDD structure)
├── sdi/             # FatturaPA XML, PEC sender, digital signatures, SDI notifications
├── services/        # PDF generation and other services
├── storage/         # SQLAlchemy models, database session, archivio
├── utils/           # Email templates, config, logging
├── web_scraper/     # Automated data extraction and business intelligence
└── tests/           # Comprehensive test suite with 170+ tests
```

**Key Architectural Patterns:**
- **AI Module**: Provider abstraction (OpenAI/Anthropic/Ollama), agent protocol, tool registry, session management
- **Payment Module**: Domain-Driven Design with matchers (exact, fuzzy, date window)
- **Event System**: Observer pattern for audit trail, repository pattern for queries, analytics service for insights
- **SDI Integration**: XML generation validation PEC sending notification processing
- **Database**: SQLAlchemy ORM with models: Fattura, Riga, Cliente, Prodotto, NotificaSDI, PaymentAllocation, EventLog

## Modern Utilities (2025)

OpenFatture uses unified, modern utilities following best practices to replace legacy patterns:

### Retry Logic (`openfatture/utils/retry.py`)

**Purpose**: Centralized retry logic with exponential backoff, replacing 9+ scattered implementations.

**Usage**:
```python
from openfatture.utils.retry import retry_async, retry_sync, RetryConfig, NETWORK_RETRY

# Async function with custom config
result = await retry_async(
    lambda: api_call(),
    config=RetryConfig(max_retries=5, base_delay=2.0),
)

# Sync function with pre-configured strategy
result = retry_sync(
    lambda: risky_operation(),
    config=NETWORK_RETRY,  # Fast retries for transient network errors
)

# With retry callback for logging
async def on_retry(error: Exception, attempt: int):
    logger.warning(f"Retry attempt {attempt}: {error}")

result = await retry_async(func, on_retry=on_retry)
```

**Pre-configured Strategies**:
- `NETWORK_RETRY`: Fast retries (5 attempts, 0.5s base, 5s max) for transient network errors
- `RATE_LIMIT_RETRY`: Slow retries (10 attempts, 5s base, 120s max) for API rate limiting
- `DATABASE_RETRY`: Database retries (3 attempts, 1s base, 10s max)
- `AI_PROVIDER_RETRY`: AI provider retries (5 attempts, 2s base, 60s max, backoff 2.5x)

**Features**:
- Exponential backoff with configurable factor (default 2.0x)
- Jitter (±10%) to prevent thundering herd
- Selective exception retry (configure `retryable_exceptions` tuple)
- Automatic logging at info/warning/error levels
- Custom retry callbacks for metrics/observability

**Migration from legacy**:
```python
# OLD (scattered across codebase)
for attempt in range(max_retries):
    try:
        return await func()
    except Exception as e:
        if attempt == max_retries - 1:
            raise
        await asyncio.sleep(2 ** attempt)

# NEW (unified)
return await retry_async(func, config=RetryConfig(max_retries=max_retries))
```

### Async/Sync Bridge (`openfatture/utils/async_bridge.py`)

**Purpose**: Unified async/sync interop, replacing 19+ `asyncio.run()` calls with proper event loop handling.

**Usage**:
```python
from openfatture.utils.async_bridge import run_async, run_with_lifespan, AsyncRunner, async_context

# Basic async->sync bridge (CLI commands, scripts)
result = run_async(async_function())

# With lifespan management (CLI commands needing DB/HTTP clients)
result = run_with_lifespan(async_command())

# Reusable runner for multiple operations
with AsyncRunner() as runner:
    result1 = runner.run(async_func1())
    result2 = runner.run(async_func2())
    # Automatic cleanup

# Context manager for batch async operations
with async_context() as execute:
    result1 = execute(async_func1())
    result2 = execute(async_func2())

# Safe execution with default on error
result = run_async_safe(risky_async_op(), default=[])

# With timeout
result = run_async_timeout(slow_async_op(), timeout=5.0, default="timed out")
```

**Features**:
- Handles nested event loops (Streamlit, Jupyter) automatically
- Thread-safe execution with proper cleanup
- Context variable propagation
- Debug mode for development
- Lifespan management for CLI commands (database connections, HTTP clients)

**Migration from legacy**:
```python
# OLD (inconsistent)
asyncio.run(coro)                    # Various places
loop.run_until_complete(coro)        # Legacy
nest_asyncio.apply()                 # Streamlit-specific

# NEW (unified)
run_async(coro)                      # Everywhere
```

### Database Session Management (`openfatture/storage/session.py`)

**Purpose**: Context managers for database sessions, replacing 26+ direct `SessionLocal()` instantiations.

**Usage**:
```python
from openfatture.storage.session import db_session, async_db_session, get_db_session

# Sync context manager (recommended)
with db_session() as db:
    fattura = db.query(Fattura).filter_by(numero="001").first()
    db.commit()
    # Automatic cleanup, rollback on exception

# Async context manager (for async CLI commands)
async with async_db_session() as db:
    fattura = Fattura(numero="001", ...)
    db.add(fattura)
    db.commit()

# Direct session (manual cleanup required, use only when necessary)
db = get_db_session()
try:
    fattura = db.query(Fattura).first()
    db.commit()
finally:
    db.close()
```

**Features**:
- Automatic session cleanup (no memory leaks)
- Automatic rollback on exceptions
- Proper connection pool management
- Structured logging for debugging
- Thread-safe

**Migration from legacy**:
```python
# OLD (manual cleanup, error-prone)
from openfatture.storage.database.base import SessionLocal
db = SessionLocal()
try:
    # Use db
    db.commit()
finally:
    db.close()

# NEW (automatic cleanup, safe)
from openfatture.storage.session import db_session
with db_session() as db:
    # Use db
    db.commit()
```

**Testing**:
- Retry logic: 28/28 tests passing (`tests/utils/test_retry.py`)
- Async bridge: 30/31 tests passing (`tests/utils/test_async_bridge.py`)
- Session management: 19/19 tests passing (`tests/storage/test_session.py`)

## Development Commands

### Setup
```bash
# Install dependencies
uv sync --all-extras

# Initialize database
uv run python -c "from openfatture.storage.database.session import init_db; init_db()"

# Install pre-commit hooks
uv run pre-commit install
```

### Testing
```bash
# Run all tests with coverage
uv run python -m pytest

# Run specific test modules
uv run python -m pytest tests/ai/ -v                    # AI tests
uv run python -m pytest tests/payment/ -v               # Payment tests
uv run python -m pytest tests/unit/test_xml_builder.py  # XML generation

# E2E tests (require Ollama running)
uv run python -m pytest -m "ollama and e2e" -v          # Ollama E2E tests
uv run python -m pytest tests/ai/test_ollama_integration.py -v

# Single test function
uv run python -m pytest tests/ai/test_streaming.py::test_streaming_basic -v

# Coverage report
uv run python -m pytest --cov=openfatture --cov-report=html
```

### Makefile Commands
```bash
# Testing
make test            # Run all tests with coverage
make test-fast       # Run tests without coverage
make test-ai         # AI module tests only
make test-payment    # Payment module tests (≥80% coverage required)
make coverage        # Generate coverage reports

# Code quality
make lint            # Run ruff linter
make format          # Run black formatter
make typecheck       # Run mypy type checker

# Development
make dev-install     # Install dev dependencies
make clean           # Clean temporary files
```

## AI Module

The AI module (`openfatture/ai/`) implements a provider-agnostic architecture for LLM integration:

**Structure:**
- `providers/`: OpenAI, Anthropic, Ollama implementations (BaseLLMProvider interface)
- `agents/`: InvoiceAssistantAgent, TaxAdvisorAgent, ChatAgent, CashFlowPredictor
- `tools/`: Function calling tools (search_invoices, get_client_details, etc.)
- `session/`: ChatSession persistence with token/cost tracking
- `context/`: Automatic business data enrichment
- `prompts/`: YAML prompt templates with Jinja2 rendering
- `ml/`: Prophet + XGBoost ensemble for cash flow prediction

**Key Classes:**
- `BaseLLMProvider`: Abstract provider with `generate()`, `stream()`, `count_tokens()`, `health_check()`
- `AgentProtocol`: Agent interface with `execute(context)`, `validate_input()`, `cleanup()`
- `AgentContext`: Execution context (user_input, conversation_history, business context)
- `ToolRegistry`: Centralized tool management with async execution

**AI Commands:**
```bash
uv run openfatture ai describe "3 hours consulting"      # Generate invoice description
uv run openfatture ai suggest-vat "IT consulting"        # VAT rate suggestion
uv run openfatture ai chat                               # Interactive chat assistant
uv run openfatture ai voice-chat --interactive           # Voice-based chat assistant
uv run openfatture ai forecast --retrain                 # Train ML models for cash flow
```

### Voice Features (NEW!)

The voice module (`openfatture/ai/voice/`) adds text-to-speech (TTS) and speech-to-text (STT) capabilities for natural voice interactions with the AI assistant.

**Purpose**: Enable hands-free voice interaction for invoice creation, tax queries, and business questions using OpenAI Whisper (STT) and OpenAI TTS API.

**Architecture:**
- **Provider Abstraction**: `BaseVoiceProvider` abstract class for future extensibility (Google, Azure, etc.)
- **OpenAI Implementation**: Full Whisper STT (100+ languages) + TTS (6 voices) integration
- **Factory Pattern**: `create_voice_provider()` with environment-based configuration
- **Orchestration Layer**: `VoiceAssistant` coordinates STT ChatAgent TTS pipeline
- **Audio Handling**: Microphone recording via `sounddevice`, multi-format support (mp3, opus, aac, flac, wav)

**Key Components:**
```
openfatture/ai/voice/
├── __init__.py           # Public API exports
├── base.py               # BaseVoiceProvider abstract interface
├── models.py             # VoiceConfig, TranscriptionResult, SynthesisResult, VoiceResponse
├── openai_voice.py       # OpenAI Whisper + TTS implementation
├── factory.py            # create_voice_provider(), get_default_voice_config()
└── assistant.py          # VoiceAssistant orchestration layer
```

**Configuration (`.env`):**
```bash
# Enable voice features
OPENFATTURE_VOICE_ENABLED=true
OPENFATTURE_VOICE_PROVIDER=openai

# Speech-to-Text (Whisper)
OPENFATTURE_VOICE_STT_MODEL=whisper-1
OPENFATTURE_VOICE_STT_LANGUAGE=it  # or auto-detect (leave empty)

# Text-to-Speech
OPENFATTURE_VOICE_TTS_MODEL=tts-1-hd  # or tts-1 for lower cost
OPENFATTURE_VOICE_TTS_VOICE=nova      # alloy, echo, fable, onyx, nova, shimmer
OPENFATTURE_VOICE_TTS_SPEED=1.0       # 0.25 - 4.0
OPENFATTURE_VOICE_TTS_FORMAT=mp3      # mp3, opus, aac, flac
OPENFATTURE_VOICE_STREAMING=true      # Enable streaming TTS
```

**Voice Selection Guide:**
- `alloy`: Neutral, professional (best for English)
- `echo`: Clear, articulate
- `fable`: Expressive, storytelling
- `onyx`: Deep, authoritative
- `nova`: Warm, conversational (best for Italian)
- `shimmer`: Soft, gentle (best for French)

**CLI Commands:**
```bash
# Single voice interaction (5-second recording)
uv run openfatture ai voice-chat --duration 5

# Interactive mode (press Enter to record each time)
uv run openfatture ai voice-chat --interactive --duration 10

# Save audio files for debugging
uv run openfatture ai voice-chat -i -d 8 --save-audio

# Disable audio playback (text output only)
uv run openfatture ai voice-chat --no-playback

# Custom audio settings
uv run openfatture ai voice-chat --sample-rate 16000 --channels 1
```

**Usage Example:**
```python
from openfatture.ai.voice import create_voice_provider, VoiceAssistant
from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.providers.factory import create_provider

# Create voice provider
voice_provider = create_voice_provider(api_key="your-openai-key")

# Create voice assistant
chat_provider = create_provider()
chat_agent = ChatAgent(provider=chat_provider)
assistant = VoiceAssistant(
    voice_provider=voice_provider,
    chat_agent=chat_agent,
    enable_tts=True,
)

# Process voice input
audio_bytes = Path("recording.mp3").read_bytes()
response = await assistant.process_voice_input(audio_bytes)

print(f"You said: {response.transcription.text}")
print(f"Language: {response.transcription.language}")
print(f"Assistant: {response.llm_response}")

# Save response audio
if response.synthesis:
    Path("response.mp3").write_bytes(response.synthesis.audio_data)
```

**Voice Orchestration Flow:**
```
1. Audio Recording (sounddevice)

2. Speech-to-Text (Whisper API)
   transcription.text + language
3. LLM Processing (ChatAgent with context)
   llm_response
4. Text-to-Speech (OpenAI TTS)
   audio_data (MP3/OPUS/etc)
5. Audio Playback (sounddevice) or Save
```

**Features:**
- **Multi-language Support**: Auto-detect from 100+ languages (Whisper)
- **Language-Voice Mapping**: Automatic voice selection based on detected language
- **Streaming TTS**: Chunked audio streaming for reduced perceived latency
- **Conversation Context**: Full conversation history support in voice mode
- **Metrics Tracking**: STT, LLM, and TTS latency tracking with cost estimation
- **Error Handling**: Comprehensive exception hierarchy (VoiceProviderError, AuthError, RateLimitError, TimeoutError)

**Audio Specifications:**
- **Recording**: 16kHz sample rate, mono (configurable), 16-bit PCM WAV
- **STT Input**: Supports WAV, MP3, M4A, WEBM, MP4 (Whisper API)
- **TTS Output**: MP3 (default), OPUS, AAC, FLAC, PCM at 24kHz
- **Latency**: ~1-3s STT + LLM time + ~0.5-1s TTS = 2-5s total typical

**Cost Estimation:**
- **Whisper STT**: ~$0.006 per minute of audio
- **TTS**: ~$0.015 per 1,000 characters (tts-1) or ~$0.030 (tts-1-hd)
- **LLM**: Standard ChatGPT pricing (varies by model)

**Testing:**
```bash
# Unit tests (28 tests, 85%+ coverage)
uv run python -m pytest tests/ai/voice/ -v

# Test models
uv run python -m pytest tests/ai/voice/test_models.py -v

# Test factory
uv run python -m pytest tests/ai/voice/test_factory.py -v
```

**Limitations & Future Enhancements:**
- Currently OpenAI-only (future: Google TTS/STT, Azure, ElevenLabs)
- MP3 playback requires decoding (currently saves to temp file)
- No real-time streaming in interactive mode yet
- Push-to-talk only (no voice activity detection)

**Dependencies:**
```bash
sounddevice>=0.4.6  # Audio recording and playback
numpy>=1.26.0       # Required by sounddevice
```

**See also:**
- `openfatture/ai/voice/models.py` - Data models and enums
- `openfatture/ai/voice/assistant.py` - Orchestration layer
- `.env.example` - Complete voice configuration reference

### Custom Slash Commands (NEW!)

**Purpose**: User-defined slash commands for the interactive AI chat, inspired by Gemini CLI's extensibility

**Location**: `openfatture/cli/commands/custom_commands.py`

**Key Components:**
- `CustomCommand`: Dataclass with Jinja2 template expansion
- `CustomCommandRegistry`: Loads commands from `~/.openfatture/commands/*.yaml`
- Integration in `InteractiveChatUI`: `/custom`, `/reload` built-in commands

**Command File Structure** (`~/.openfatture/commands/mycommand.yaml`):
```yaml
name: mycommand
description: Command description
category: invoicing  # invoicing, tax, clients, reporting, compliance, general
aliases: [mc, my-cmd]
template: |
  Your prompt template here.
  Use {{ arg1 }}, {{ arg2 }} for positional arguments.
  Use {% if arg2 %}conditional{% endif %} for logic.
  Full Jinja2 syntax supported.

examples:
  - "/mycommand arg1 arg2"
```

**Usage in Chat:**
```bash
openfatture ai chat
> /help           # Show all built-in commands
> /custom         # List custom commands
> /reload         # Reload commands from disk
> /mycommand "arg1" "arg2"  # Execute custom command
```

**Example Commands** (in `docs/examples/custom-commands/`):
1. `/fattura-rapida` - Quick invoice creation workflow (description + VAT + compliance + create)
2. `/iva` - VAT rate suggestion shortcut with legal references
3. `/cliente-info` - Client lookup with statistics and payment status
4. `/report-mensile` - Monthly business report with insights
5. `/compliance-check` - Pre-submission compliance verification

**Template Variables:**
- `{{ arg1 }}`, `{{ arg2 }}`, ... - Positional arguments
- `{{ args }}` - List of all arguments
- `{{ argN | default('value') }}` - Default values
- `{{ argN | upper }}` - Jinja2 filters (upper, lower, title, etc.)
- Conditionals: `{% if arg2 %}...{% endif %}`
- Loops: `{% for item in args %}...{% endfor %}`

**Installation:**
```bash
# Copy example commands
mkdir -p ~/.openfatture/commands/
cp docs/examples/custom-commands/*.yaml ~/.openfatture/commands/

# Use in chat
openfatture ai chat
> /custom          # See 5 example commands
> /fattura-rapida "Acme Corp" "Web consulting" "500"
```

**Testing:**
```bash
# Run custom commands tests (28 tests, 79% coverage)
uv run python -m pytest tests/cli/test_custom_commands.py -v
```

**Benefits:**
- **Productivity**: Reusable workflows eliminate repetitive prompts
- **Customization**: Tailor commands to your specific business needs
- **Consistency**: Standardized prompts ensure reliable AI outputs
- **Shareability**: YAML files can be shared across team/community
- **Hot Reload**: `/reload` command picks up changes without restart

**See also:**
- `docs/examples/custom-commands/README.md` - Complete usage guide
- Example commands in `docs/examples/custom-commands/*.yaml`

**E2E Testing with Ollama:**
```bash
# Run end-to-end tests with real Ollama (requires Ollama running)
uv run python -m pytest tests/ai/test_ollama_integration.py -v

# Test specific agent with Ollama
uv run python -m pytest tests/ai/test_ollama_integration.py::TestOllamaTaxAdvisor -v
```

**ML Models:**
- Models stored in `.models/` directory with versioning
- Files: `cash_flow_prophet.json`, `cash_flow_xgboost.json`, `cash_flow_pipeline.pkl`, `cash_flow_metrics.json`
- Requires ≥25 invoices/payments for training
- Test with: `uv run pytest tests/ai/test_cash_flow_predictor_training.py`

**ReAct Orchestration (NEW!):**

ReAct (Reasoning + Acting) enables tool calling for Ollama models without native function calling:

- **Purpose**: Local LLMs (Ollama) can use the same tools as OpenAI/Anthropic
- **Method**: XML-based prompt engineering + multi-strategy parser
- **Location**: `openfatture/ai/orchestration/react.py`, `openfatture/ai/orchestration/parsers.py`

**Key Components:**
- `ToolCallParser`: Parses LLM responses (XML-first, legacy text fallback)
- `ReActOrchestrator`: Manages tool calling loop (max iterations, metrics tracking)

**Configuration:**
```bash
# .env settings for Ollama with ReAct
OPENFATTURE_AI_PROVIDER=ollama
OPENFATTURE_AI_OLLAMA_MODEL=qwen3:8b  # Recommended for tool calling
OPENFATTURE_AI_TEMPERATURE=0.0        # CRITICAL: Deterministic for tool calling
```

**Best Practices (2025):**
1. **Always use temperature=0.0** for tool calling with Ollama
2. **Use qwen3:8b model** (5.2 GB) - optimized for tool calling, 80%+ success rate
3. **Monitor metrics**: Track `tool_call_success_rate` and `xml_parse_rate`
4. **Set appropriate max_iterations**: 5 for simple queries, 8+ for multi-step reasoning
5. **XML format is standard**: LLM should generate `<thought>`, `<action>`, `<action_input>`, `<final_answer>` tags

**Testing:**
```bash
# Unit tests (parsers, orchestrator)
uv run pytest tests/ai/test_react_orchestration.py -v

# Integration tests (with mock tools)
uv run pytest tests/ai/test_react_orchestration_integration.py -v

# E2E tests (requires Ollama running with qwen3:8b)
uv run pytest tests/ai/test_react_e2e_ollama.py -v -m "ollama and e2e"

# Success rate test (10 diverse queries, requires ≥80% success)
uv run pytest tests/ai/test_react_e2e_ollama.py::TestReActOllamaSuccessRate -v
```

**Performance Benchmarks:**
- **Success Rate**: ≥80% across diverse queries (validated with real Ollama)
- **XML Format Adoption**: 60%+ with qwen3:8b (fallback to legacy if needed)
- **Average Iterations**: 2-3 per successful completion
- **Latency**: ~2-5s per iteration (local inference)

**Common Issues:**
- **Low success rate**: Check temperature=0.0, verify model is qwen3:8b, monitor metrics
- **Infinite loops**: Tool not providing expected data validate tool outputs
- **Max iterations reached**: Query too complex increase max_iterations or split query
- **Failed tool calls**: Invalid parameters improve tool parameter descriptions

**See also:**
- `docs/AI_ARCHITECTURE.md` - Complete ReAct architecture documentation
- `docs/guidelines/REACT_BEST_PRACTICES.md` - Detailed best practices guide

## Event System & Audit Trail

The event system (`openfatture/core/events/`) provides comprehensive audit trails and analytics:

**Structure:**
- `event_bus.py`: Observer pattern implementation with async event publishing
- `event_log.py`: EventLog model with UUID, timestamps, entity tracking, metadata
- `event_repository.py`: Advanced queries with filtering, search, pagination, statistics
- `event_analytics.py`: Time-based aggregations, trends, velocity metrics
- `event_persistence.py`: Automatic event logging with error isolation

**Key Features:**
- **Event Types**: Invoice creation/deletion, client updates, payment reconciliation, SDI notifications
- **Entity Tracking**: Link events to specific business entities (fattura, cliente, etc.)
- **Metadata Support**: JSON storage for additional context and structured data
- **Timeline Generation**: Human-readable event summaries with chronological ordering
- **Full-text Search**: SQLite LIKE queries across event data and metadata

**CLI Commands (`openfatture events`):**
```bash
uv run openfatture events list --type invoice_created --limit 10    # List events
uv run openfatture events show <event-id>                           # Detailed view
uv run openfatture events stats --last-days 7                      # Statistics
uv run openfatture events timeline fattura INV-001                 # Entity timeline
uv run openfatture events search "payment received"                # Full-text search
uv run openfatture events dashboard --days 30                      # Analytics dashboard
uv run openfatture events trends --type payment_reconciled         # Trend analysis
```

**Analytics Features:**
- **Time Aggregations**: Daily, weekly, monthly activity patterns
- **Event Distribution**: Type percentages and entity activity rankings
- **Trend Analysis**: Recent vs previous period comparisons with indicators
- **Velocity Metrics**: Events per hour with peak activity detection
- **Hourly Patterns**: 24-hour distribution analysis

**Visualizations:**
- ASCII bar charts with Rich library (█ blocks scaled to data)
- Tree-style timeline views with connectors (┌ ├ └)
- Color-coded trend indicators ()
- Formatted tables with proper alignment

**Testing Coverage:**
- **Event Persistence**: 100% coverage (13 tests)
- **Event Repository**: 91% coverage (27 tests for queries, search, stats, pagination)
- **Event Base**: 88% coverage (event bus, serialization)
- **Event Analytics**: 15% coverage (new module, expanding)
- **Integration Tests**: 5 tests for fattura events (creation, validation, sending, timeline)

## Hooks & Automation

The hooks system (`openfatture/core/hooks/`) enables custom automation workflows:

**Structure:**
- `hook_registry.py`: Centralized hook management and execution
- `hook_types.py`: Pre/post operation hook definitions
- `built_in_hooks/`: Standard hooks for common operations
- `custom_hooks/`: User-defined YAML-based hooks

**Built-in Hooks:**
- **Post-Invoice-Send**: Send notifications, update external systems, trigger backups
- **Post-Payment-Reconcile**: Update accounting software, generate reports
- **Post-Client-Create**: Setup default configurations, send welcome emails

**Custom Hook Development:**
```yaml
# ~/.openfatture/hooks/post_invoice_send.yaml
name: sync-to-accounting
description: Sync invoice to external accounting system
trigger: post_invoice_send
script: |
  #!/bin/bash
  curl -X POST https://api.accounting.com/invoices \
    -H "Authorization: Bearer $API_KEY" \
    -d "{\"invoice_id\": \"$INVOICE_ID\", \"amount\": \"$AMOUNT\"}"
```

**Error Handling:**
- Hook failures don't block main operations
- Isolated execution with timeout controls
- Comprehensive logging and retry mechanisms

## Preventivi System

The preventivi (quotations) system (`openfatture/core/preventivi/`) manages estimates and proposals:

**Structure:**
- `preventivo.py`: Preventivo model with line items and status tracking
- `preventivo_service.py`: Business logic for creation, updates, conversion
- `preventivo_cli.py`: CLI commands for preventivo management

**Status Workflow:**
- `BOZZA`: Draft, editable
- `INVIATA`: Sent to client, awaiting response
- `ACCETTATA`: Approved, ready for conversion
- `RIFIUTATA`: Rejected by client
- `SCADUTA`: Expired without response

**Conversion to Invoice:**
```bash
uv run openfatture preventivo convert PREV-001 --numero-fattura INV-2024-042
```

**Business Logic:**
- Validity periods with automatic expiration
- Version control for revisions
- Client approval workflow
- Tax calculation and validation

## Web UI Module

Modern Streamlit-based interface following 2025 Best Practices. Provides dashboard, invoice management, AI assistant, and Lightning payments with 77% test coverage.

**Quick Start:**
```bash
uv sync --extra web
uv run streamlit run openfatture/web/app.py
```

**Key Features:**
- Real-time dashboard with KPI and interactive charts
- AI assistant with chat, VAT suggestions, and description generation
- Invoice management with XML generation and SDI integration
- Lightning payments with QR codes and monitoring
- Security: File validation, input sanitization, rate limiting
- Health monitoring and structured logging

**Architecture Highlights:**
- Service layer with async/sync bridging
- React-style component library (cards, tables, alerts)
- Intelligent caching with TTL and category invalidation
- Production-ready configuration (.streamlit/config.toml)

**See also:**
- `docs/WEB_UI_GUIDE.md` - Complete user guide
- `docs/WEB_UI_MODERNIZATION_COMPLETE.md` - Technical implementation
- `docs/WEB_UI_BEST_PRACTICES_2025.md` - Best practices compliance
- `openfatture/web/README.md` - Module documentation

## Web Scraper Module

The web scraper (`openfatture/web_scraper/`) enables automated business intelligence:

**Structure:**
- `agent.py`: Agent-based scraping with configurable strategies
- `scrapers/`: Specialized scrapers for different data sources
- `data_processor.py`: Extraction and normalization logic
- `rate_limiter.py`: Politeness controls and throttling

**Key Features:**
- **Company Data Enrichment**: VAT validation, address verification, contact information
- **Market Research**: Competitor analysis, industry benchmarks
- **Data Validation**: Automated verification of business information

**Usage:**
```bash
uv run openfatture scrape company "Tech Solutions SRL" --vat IT12345678901
uv run openfatture scrape market-research "software development" --region lombardy
```

**Architecture:**
- Agent-based design with pluggable strategies
- Rate limiting and politeness controls
- Structured data extraction with validation
- Results storage and reporting

## Payment Reconciliation

The payment module (`openfatture/payment/`) uses Domain-Driven Design:

**Structure:**
- `domain/`: Core models (BankTransaction, PaymentAllocation)
- `matchers/`: Reconciliation strategies (exact, fuzzy, date window)
- `infrastructure/`: Bank parsers (OFX/QFX)
- `application/services/`: Orchestration logic

**Matchers:**
- `ExactMatcher`: Exact amount + invoice number matching
- `FuzzyDescriptionMatcher`: Fuzzy string matching with `rapidfuzz` (threshold: 80)
- `IBANMatcher`: IBAN matching with SEPA multi-country support (30 countries: 27 EU + 3 EEA)
- `DateWindowMatcher`: Matches within ±N days of invoice date
- `CompositeMatcher`: Weighted combination of all strategies (parallel execution, 3.87x speedup)

**Commands:**
```bash
uv run openfatture payment import bank_statement.ofx    # Import bank transactions
uv run openfatture payment reconcile                    # Run reconciliation
uv run openfatture payment status                       # View payment status
```

## FatturaPA & SDI Integration

**XML Generation Flow:**
1. Create `Fattura` model with `Riga` (invoice lines)
2. `FatturaPABuilder` (`openfatture/sdi/xml_builder/fatturapa.py`) generates FatturaPA XML v1.9
3. `XSDValidator` validates against official schema
4. Optional: `DigitalSigner` signs XML with PKCS#12 certificate
5. `TemplatePECSender` sends to `sdi01@pec.fatturapa.it`
6. `NotificheProcessor` handles SDI responses (RC/NS/MC/DT)

**Invoice States:**
- `BOZZA`: Draft, editable
- `DA_INVIARE`: Ready to send
- `INVIATA`: Sent to SDI, awaiting response
- `CONSEGNATA`: Delivered successfully

**Commands:**
```bash
uv run openfatture fattura crea                         # Create invoice (interactive)
uv run openfatture fattura lista                        # List invoices
uv run openfatture fattura valida <numero>              # Validate XML
uv run openfatture pec invia <numero>                   # Send to SDI via PEC
```

## Configuration

Configuration uses Pydantic Settings with `.env` file (see `.env.example`):

**Required:**
- `CEDENTE_*`: Your company data (P.IVA, codice fiscale, regime fiscale)
- `PEC_*`: PEC email credentials for SDI submission
- `DATABASE_URL`: SQLite (dev) or PostgreSQL (production)

**Optional:**
- `AI_PROVIDER`, `AI_MODEL`, `AI_API_KEY`: AI configuration
- `SIGNATURE_CERTIFICATE_*`: Digital signature
- `EMAIL_LOGO_URL`, `EMAIL_PRIMARY_COLOR`: Email branding

See `docs/CONFIGURATION.md` for complete reference.

## Database Models

**Core Models:**
- `Fattura`: Invoice (numero, data, tipo_documento, stato, totale_*)
- `Riga`: Invoice line items (descrizione, quantita, prezzo_unitario, aliquota_iva)
- `Cliente`: Client (denominazione, partita_iva, regime_fiscale, codice_destinatario)
- `Prodotto`: Product catalog (codice, descrizione, prezzo_unitario)
- `NotificaSDI`: SDI notifications (tipo: RC/NS/MC/DT, messaggio, xml_notifica)
- `PaymentAllocation`: Payment reconciliation linkage

**Relationships:**
- Fattura Cliente (many-to-one)
- Fattura Riga (one-to-many)
- Riga Prodotto (many-to-one, optional)
- Fattura NotificaSDI (one-to-many)

## Italian Tax Codes

**Regime Fiscale (RF):**
- `RF01`: Ordinario
- `RF19`: Regime forfettario
- (See full list in FatturaPA specs)

**Natura IVA (when aliquota_iva = 0):**
- `N1`: Escluse ex art. 15
- `N2`: Non soggette
- `N3`: Non imponibili
- `N4`: Esenti
- `N6`: Inversione contabile (reverse charge)
- `N7`: IVA assolta in altro stato UE

**Tipo Documento:**
- `TD01`: Fattura (most common)
- `TD04`: Nota di credito
- `TD06`: Parcella
- (See `TipoDocumento` enum for full list)

## Testing Conventions

- **Unit tests**: `tests/unit/test_*.py` - Mock external dependencies
- **Integration tests**: `tests/integration/test_*.py` - Test real integrations
- **AI tests**: `tests/ai/test_*.py` - AI module specific
- **Payment tests**: `tests/payment/` - Domain, matchers, services (≥80% coverage required)
- Use `conftest.py` fixtures for database session, sample data, mock providers

**Database fixtures (testing architecture):**
- `db_session` / `sample_*` (root `conftest.py`): an in-memory session for direct
  ORM assertions. Does NOT wire the global session factory — use it when the test
  itself owns the queries.
- `runtime_db` / `runtime_session` / `seed_cliente` / `seed_fattura`: point an
  isolated, file-backed SQLite DB at the GLOBAL session factory AND at
  `get_settings()` (cedente/PEC/`database_url` via env). Use these whenever the
  code under test opens its own session — CLI commands (`with db_session() as db:`
  / `init_db(settings.database_url)`), web services (`db_session_scope`), or agents
  — so production code and the test share one real database. Prefer seeding real
  rows over mocking SQLAlchemy query chains. Mock only true external boundaries
  (LLM providers, PEC/SMTP, LND/gRPC). The `tests/ai` package has an autouse
  in-memory DB; opt a node test out of session mocking with `@pytest.mark.real_db`.
- CLI output is i18n (default locale Italian). Tests that assert on rendered text
  pin the locale with a module-level autouse `_english_locale` fixture and assert
  the English strings; Rich tables truncate at 80 cols, so use a `_WideCliRunner`
  (COLUMNS=220) when asserting wide table cells. Typer/Click route usage/argument
  errors to `result.stderr` (streams are split), not `result.stdout`.

**Test Markers:**
```python
@pytest.mark.streaming     # Streaming-capable components
@pytest.mark.e2e          # End-to-end tests requiring external services
@pytest.mark.ollama       # Tests requiring Ollama LLM service
@pytest.mark.performance  # Wall-clock/benchmark tests
@pytest.mark.real_db      # Opt out of session mocking, use the real in-memory DB
```
The default `pytest` gate deselects `performance`/`benchmark`/`slow`/`e2e`/`ollama`
(see `addopts`) so it stays fast and deterministic; run those tiers explicitly,
e.g. `uv run pytest -m performance` or `uv run pytest -m "ollama and e2e"`.

## Code Style

- **Formatter**: Black (line length 100)
- **Linter**: Ruff (pycodestyle, pyflakes, isort, flake8-bugbear, pyupgrade); PEP 695 generics (`def f[T]`)
- **Type checking**: MyPy (strict mode, but tests are ignored)
- **Pre-commit hooks**: Automatically run black, ruff, mypy, bandit before commit
- **No emojis**: plain text only — no emoji/pictographic characters in code, CLI help,
  Rich/Streamlit UI, i18n bundles, email templates, docs, or filenames.

### Structural conventions (2026 refactor)
- **CLI command groups are packages, not single files**: `cli/commands/ai/` and
  `payment/cli/` split by responsibility, each with an `_app.py` (Typer app + shared
  helpers) and per-group modules; the `__init__` imports the modules to register commands.
  AI tools live in the `ai/tools/invoice_tools/` package.
- **Heavy ML deps are lazy**: `sentence-transformers`, the AI providers/agents and the
  `openfatture.ai` stack are imported inside functions (e.g. `ai/rag/embeddings.py`'s
  `_sentence_transformer()` seam, `payment/cli/_app.py`), not at module top level, so the
  CLI starts fast. Tests patch the local seam, not the third-party global.
- **Streamlit pages**: `web/pages/N_Name.py` (no emoji prefix); navigation/`st.switch_page`
  paths and `AppTest.from_file` must match these names.

## Key Implementation Notes

1. **Async by default**: All AI providers and agents use `async/await`
2. **Type safety**: Full type hints with Pydantic models everywhere
3. **Structured logging**: Use `structlog` for observability
4. **Cost tracking**: AI agents track tokens/cost in AgentResponse and ChatSession
5. **Immutable invoices**: Once `CONSEGNATA`, invoices cannot be edited (clone instead)
6. **Decimal precision**: Use `Decimal` for all currency/amounts (never float)
7. **Date handling**: Use `datetime.date` for invoice dates, `datetime.datetime` for timestamps
8. **XML namespaces**: FatturaPA uses specific namespaces (see `openfatture/sdi/xml_builder/`)

## Common Workflows

**Create and send invoice:**
```python
from openfatture.storage.database.models import Fattura, Riga, Cliente
from openfatture.sdi.xml_builder.fatturapa import FatturaPABuilder
from openfatture.sdi.validator.xsd_validator import XSDValidator
from openfatture.utils.email.sender import TemplatePECSender

# Create invoice (CLI: uv run openfatture fattura crea)
fattura = Fattura(numero="001", data=date.today(), ...)
riga = Riga(descrizione="Consulting", prezzo_unitario=1000, ...)

# Generate XML (FatturaPABuilder(settings).build(fattura) -> XML string)
xml_str = FatturaPABuilder(get_settings()).build(fattura)

# Validate
validator = XSDValidator()
validator.validate(xml_tree)

# Send to SDI
sender = TemplatePECSender(settings=get_settings())
sender.send_invoice_to_sdi(fattura, xml_path="invoice.xml", signed=False)
```

**AI-assisted description:**
```python
from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.domain.context import InvoiceContext

agent = InvoiceAssistantAgent(...)
context = InvoiceContext(user_input="3 hours GDPR consulting")
response = await agent.execute(context)
print(response.content)  # Detailed professional description
```

## Documentation

- `docs/README.md`: Documentation hub and navigation
- `docs/QUICKSTART.md`: 15-minute setup guide
- `docs/CONFIGURATION.md`: Complete `.env` reference
- `docs/AI_ARCHITECTURE.md`: AI module deep dive
- `docs/PAYMENT_TRACKING.md`: Payment reconciliation guide
- `docs/ARCHITECTURE_DIAGRAMS.md`: Mermaid diagrams of system architecture
- `docs/DEVELOPMENT.md`: Development environment setup, testing, CI/CD
- `docs/CLI_REFERENCE.md`: Complete CLI command catalogue

## Release Process

```bash
# Update CHANGELOG.md with changes
# Bump version (patch/minor/major)
uv run bump-my-version bump minor

# Push with tags (triggers GitHub Actions release workflow)
git push --follow-tags
```

## CI/CD

GitHub Actions workflows:
- `.github/workflows/test.yml`: Runs on push/PR (lint, test, coverage gate ≥60%)
- `.github/workflows/release.yml`: Runs on version tags (build, GitHub release)
- `.github/workflows/media-generation.yml`: Demo video generation

Test workflows locally with `act`:
```bash
./scripts/validate-actions.sh           # Validate workflow syntax
act push -j lint                        # Run lint job
act push -W .github/workflows/test.yml  # Run full test workflow
```

## Project Status

- **Version**: 1.1.0 (see `docs/releases/v1.1.0.md`)
- **Current Phase**: Event System & Automation (Phase 5), production hardening (Phase 6)
- **Test Coverage**: 55%+ (targeting 60-85% with event system completion)
- **Python**: 3.12+
- **License**: MIT
