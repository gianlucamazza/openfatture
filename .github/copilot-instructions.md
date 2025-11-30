# GitHub Copilot Instructions for OpenFatture

This file provides guidance to GitHub Copilot coding agent when working on this repository.

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
- Web UI with Streamlit
- Lightning Network payment integration

## Repository Structure

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
├── web/             # Streamlit web UI
└── tests/           # Comprehensive test suite with 170+ tests
```

## Development Setup

### Prerequisites
- Python 3.12+
- uv package manager
- SQLite (dev) or PostgreSQL (production)

### Installation

```bash
# Install dependencies
uv sync --all-extras

# Initialize database
uv run python -c "from openfatture.storage.database.session import init_db; init_db()"

# Install pre-commit hooks
uv run pre-commit install
```

## Testing

### Running Tests

**Important:** Always run tests before making changes to understand existing failures, and after changes to verify they work correctly.

```bash
# Run all tests with coverage
uv run python -m pytest

# Run specific test modules
uv run python -m pytest tests/ai/ -v                    # AI tests
uv run python -m pytest tests/payment/ -v               # Payment tests
uv run python -m pytest tests/unit/test_xml_builder.py  # XML generation

# Run tests without coverage (faster)
make test-fast

# Generate coverage report
uv run python -m pytest --cov=openfatture --cov-report=html
```

### Test Markers

```python
@pytest.mark.streaming     # Streaming-capable components
@pytest.mark.e2e          # End-to-end tests requiring external services
@pytest.mark.ollama       # Tests requiring Ollama LLM service
```

### Test Organization

- **Unit tests**: `tests/unit/test_*.py` - Mock external dependencies
- **Integration tests**: `tests/integration/test_*.py` - Test real integrations
- **AI tests**: `tests/ai/test_*.py` - AI module specific
- **Payment tests**: `tests/payment/` - Domain, matchers, services (≥80% coverage required)
- Use `conftest.py` fixtures for database session, sample data, mock providers

## Code Quality

### Linting and Formatting

**Important:** Always run linters before committing changes.

```bash
# Run linter
make lint              # or: uv run ruff check .

# Run formatter
make format            # or: uv run black .

# Run type checker
make typecheck         # or: uv run mypy openfatture
```

### Code Style Rules

- **Formatter**: Black (line length 100)
- **Linter**: Ruff (pycodestyle, pyflakes, isort, flake8-bugbear)
- **Type checking**: MyPy (strict mode, but tests are ignored)
- **Pre-commit hooks**: Automatically run black, ruff, mypy before commit

### Type Hints

- Use full type hints with Pydantic models everywhere
- All AI providers and agents use `async/await`
- Decimal precision: Use `Decimal` for all currency/amounts (never float)
- Date handling: Use `datetime.date` for invoice dates, `datetime.datetime` for timestamps

## Key Architectural Patterns

### AI Module (`openfatture/ai/`)

Provider-agnostic architecture for LLM integration:
- `providers/`: OpenAI, Anthropic, Ollama implementations (BaseLLMProvider interface)
- `agents/`: InvoiceAssistantAgent, TaxAdvisorAgent, ChatAgent, CashFlowPredictor
- `tools/`: Function calling tools (search_invoices, get_client_details, etc.)
- `session/`: ChatSession persistence with token/cost tracking
- `orchestration/`: ReAct orchestration for tool calling with local LLMs

### Payment Module (`openfatture/payment/`)

Domain-Driven Design structure:
- `domain/`: Core models (BankTransaction, PaymentAllocation)
- `matchers/`: Reconciliation strategies (exact, fuzzy, date window)
- `infrastructure/`: Bank parsers (OFX/QFX)
- `application/services/`: Orchestration logic

### Event System (`openfatture/core/events/`)

Observer pattern for audit trail:
- `event_bus.py`: Event publishing and subscription
- `event_log.py`: EventLog model with UUID, timestamps, entity tracking
- `event_repository.py`: Advanced queries with filtering, search, pagination
- `event_analytics.py`: Time-based aggregations, trends, velocity metrics

### SDI Integration

XML generation flow:
1. Create `Fattura` model with `Riga` (invoice lines)
2. `FatturaXMLGenerator` generates FatturaPA XML v1.9
3. `XSDValidator` validates against official schema
4. Optional: `DigitalSigner` signs XML with PKCS#12 certificate
5. `TemplatePECSender` sends to `sdi01@pec.fatturapa.it`
6. `NotificheProcessor` handles SDI responses (RC/NS/MC/DT)

## Database Models

**Core Models:**
- `Fattura`: Invoice (numero, data, tipo_documento, stato, totale_*)
- `Riga`: Invoice line items (descrizione, quantita, prezzo_unitario, aliquota_iva)
- `Cliente`: Client (denominazione, partita_iva, regime_fiscale, codice_destinatario)
- `Prodotto`: Product catalog (codice, descrizione, prezzo_unitario)
- `NotificaSDI`: SDI notifications (tipo: RC/NS/MC/DT, messaggio, xml_notifica)
- `PaymentAllocation`: Payment reconciliation linkage
- `EventLog`: Audit trail with UUID, timestamps, entity tracking

**Relationships:**
- Fattura → Cliente (many-to-one)
- Fattura → Riga (one-to-many)
- Riga → Prodotto (many-to-one, optional)
- Fattura → NotificaSDI (one-to-many)

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

## Important Implementation Notes

When making changes, keep these principles in mind:

1. **Immutable invoices**: Once `CONSEGNATA`, invoices cannot be edited (clone instead)
2. **Decimal precision**: Use `Decimal` for all currency/amounts (never float)
3. **Async by default**: All AI providers and agents use `async/await`
4. **Type safety**: Full type hints with Pydantic models everywhere
5. **Structured logging**: Use `structlog` for observability
6. **Cost tracking**: AI agents track tokens/cost in AgentResponse and ChatSession
7. **XML namespaces**: FatturaPA uses specific namespaces (see `openfatture/sdi/xml_builder/`)
8. **Test coverage**: Target ≥60% overall, ≥80% for payment module

## Making Changes

### Before Making Changes

1. Run existing tests to understand baseline: `make test-fast`
2. Run linter to check for existing issues: `make lint`
3. Review relevant documentation in `docs/` directory
4. Check `CHANGELOG.md` for recent changes

### While Making Changes

1. Follow existing code patterns and conventions
2. Add type hints to all new code
3. Use Pydantic models for data validation
4. Add tests for new functionality
5. Update documentation if changing behavior
6. Run tests frequently: `make test-fast`

### After Making Changes

1. Run full test suite: `make test`
2. Run linter: `make lint`
3. Run formatter: `make format`
4. Run type checker: `make typecheck`
5. Update `CHANGELOG.md` if needed
6. Ensure coverage doesn't decrease

## Common Commands

```bash
# Development
make dev-install     # Install dev dependencies
make clean           # Clean temporary files

# Testing
make test            # Run all tests with coverage
make test-fast       # Run tests without coverage
make test-ai         # AI module tests only
make test-payment    # Payment module tests
make coverage        # Generate coverage reports

# Code quality
make lint            # Run ruff linter
make format          # Run black formatter
make typecheck       # Run mypy type checker

# CLI (examples)
uv run openfatture fattura crea              # Create invoice (interactive)
uv run openfatture fattura lista             # List invoices
uv run openfatture ai describe "text"        # AI invoice description
uv run openfatture payment reconcile         # Run payment reconciliation
uv run openfatture events list               # List audit events

# Web UI
uv sync --extra web
uv run streamlit run openfatture/web/app.py
```

## Italian Tax Codes Reference

**Regime Fiscale (RF):**
- `RF01`: Ordinario
- `RF19`: Regime forfettario

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

## Documentation

- `docs/README.md`: Documentation hub and navigation
- `docs/QUICKSTART.md`: 15-minute setup guide
- `docs/CONFIGURATION.md`: Complete `.env` reference
- `docs/AI_ARCHITECTURE.md`: AI module deep dive
- `docs/PAYMENT_TRACKING.md`: Payment reconciliation guide
- `docs/ARCHITECTURE_DIAGRAMS.md`: Mermaid diagrams of system architecture
- `docs/DEVELOPMENT.md`: Development environment setup, testing, CI/CD
- `docs/CLI_REFERENCE.md`: Complete CLI command catalogue

## CI/CD

GitHub Actions workflows:
- `.github/workflows/test.yml`: Runs on push/PR (lint, test, coverage gate ≥60%)
- `.github/workflows/release.yml`: Runs on version tags (build, GitHub release)
- `.github/workflows/media-generation.yml`: Demo video generation

## Project Status

- **Version**: 1.1.0
- **Python**: 3.12+
- **License**: MIT
- **Test Coverage**: 55%+ (targeting 60-85%)

## Getting Help

When you encounter issues:
1. Check `docs/DEVELOPMENT.md` for troubleshooting
2. Review `CONTRIBUTING.md` for contribution guidelines
3. Check existing tests for usage examples
4. Review `docs/` directory for specific module documentation
