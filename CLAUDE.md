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
├── core/            # Business logic (fatture, clienti, prodotti, batch)
├── payment/         # Payment reconciliation (DDD structure)
├── sdi/             # FatturaPA XML, PEC sender, digital signatures, SDI notifications
├── services/        # PDF generation and other services
├── storage/         # SQLAlchemy models, database session, archivio
└── utils/           # Email templates, config, logging
```

**Key Architectural Patterns:**
- **AI Module**: Provider abstraction (OpenAI/Anthropic/Ollama), agent protocol, tool registry, session management
- **Payment Module**: Domain-Driven Design with matchers (exact, fuzzy, date window)
- **SDI Integration**: XML generation → validation → PEC sending → notification processing
- **Database**: SQLAlchemy ORM with models: Fattura, Riga, Cliente, Prodotto, NotificaSDI, PaymentAllocation

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
uv run openfatture ai forecast --retrain                 # Train ML models for cash flow
```

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
- ⚡ **Productivity**: Reusable workflows eliminate repetitive prompts
- 🔧 **Customization**: Tailor commands to your specific business needs
- 🎯 **Consistency**: Standardized prompts ensure reliable AI outputs
- 📚 **Shareability**: YAML files can be shared across team/community
- 🔄 **Hot Reload**: `/reload` command picks up changes without restart

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
- **Infinite loops**: Tool not providing expected data → validate tool outputs
- **Max iterations reached**: Query too complex → increase max_iterations or split query
- **Failed tool calls**: Invalid parameters → improve tool parameter descriptions

**See also:**
- `docs/AI_ARCHITECTURE.md` - Complete ReAct architecture documentation
- `docs/guidelines/REACT_BEST_PRACTICES.md` - Detailed best practices guide

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
- `DateWindowMatcher`: Matches within ±N days of invoice date

**Commands:**
```bash
uv run openfatture payment import bank_statement.ofx    # Import bank transactions
uv run openfatture payment reconcile                    # Run reconciliation
uv run openfatture payment status                       # View payment status
```

## FatturaPA & SDI Integration

**XML Generation Flow:**
1. Create `Fattura` model with `Riga` (invoice lines)
2. `FatturaXMLGenerator` generates FatturaPA XML v1.9
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
- Fattura → Cliente (many-to-one)
- Fattura → Riga (one-to-many)
- Riga → Prodotto (many-to-one, optional)
- Fattura → NotificaSDI (one-to-many)

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

**Test Markers:**
```python
@pytest.mark.streaming     # Streaming-capable components
@pytest.mark.e2e          # End-to-end tests requiring external services
@pytest.mark.ollama       # Tests requiring Ollama LLM service
```

## Code Style

- **Formatter**: Black (line length 100)
- **Linter**: Ruff (pycodestyle, pyflakes, isort, flake8-bugbear)
- **Type checking**: MyPy (strict mode, but tests are ignored)
- **Pre-commit hooks**: Automatically run black, ruff, mypy before commit

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
from openfatture.core.xml.generator import FatturaXMLGenerator
from openfatture.sdi.validator.xsd_validator import XSDValidator
from openfatture.utils.email.sender import TemplatePECSender

# Create invoice (CLI: uv run openfatture fattura crea)
fattura = Fattura(numero="001", data=date.today(), ...)
riga = Riga(descrizione="Consulting", prezzo_unitario=1000, ...)

# Generate XML
xml_tree = FatturaXMLGenerator(fattura).generate()

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
- **Current Phase**: AI orchestration (Phase 4) and production hardening (Phase 6)
- **Test Coverage**: 50%+ (targeting 60%)
- **Python**: 3.12+
- **License**: MIT
