# OpenFatture 🧾

**Open-source electronic invoicing system for Italian freelancers** - CLI-first with AI-powered workflows.

> A modern, compliant alternative to proprietary invoicing platforms, designed for tech-savvy freelancers who value transparency, automation, and control.

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![CI Tests](https://github.com/gianlucamazza/openfatture/actions/workflows/test.yml/badge.svg)](https://github.com/gianlucamazza/openfatture/actions/workflows/test.yml)
[![Release](https://github.com/gianlucamazza/openfatture/actions/workflows/release.yml/badge.svg)](https://github.com/gianlucamazza/openfatture/actions/workflows/release.yml)
[![Media Generation](https://github.com/gianlucamazza/openfatture/actions/workflows/media-generation.yml/badge.svg)](https://github.com/gianlucamazza/openfatture/actions/workflows/media-generation.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> 📘 Documentazione consolidata per v1.0.0: consulta l'[indice aggiornato](docs/README.md) e le [note di rilascio](docs/releases/v1.0.0.md).

---

## Demo

<div align="center">

### 🎥 See OpenFatture in Action

**Quick Start: Setup & Configuration**

https://github.com/user-attachments/assets/scenario_a_onboarding.mp4

**Creating Professional Invoices**

https://github.com/user-attachments/assets/scenario_b_invoice.mp4

**AI-Powered Assistant with Local Ollama**

https://github.com/user-attachments/assets/scenario_c_ai.mp4

**Batch Operations & Analytics**

https://github.com/user-attachments/assets/scenario_d_batch.mp4

**PEC Integration & SDI Notifications**

https://github.com/user-attachments/assets/scenario_e_pec.mp4

> **📹 All demo videos:** [media/output/](media/output/) • **📸 Screenshots:** [media/screenshots/](media/screenshots/)

</div>

---

## Features

### Core Invoicing
- 📄 **FatturaPA XML v1.9** - Full compliance with Italian e-invoicing standards (updated for 2025)
- 🏛️ **SDI Integration** - Direct submission via PEC (Certified Email)
- ✅ **Automatic Validation** - XSD schema validation before submission
- 🔐 **Digital Signatures** - Support for P7M and CAdES formats (PKCS#12)
- 📧 **Professional Email Templates** - HTML multipart emails for SDI notifications
- 📊 **Client & Product Management** - Complete CRM for freelancers
- 🔔 **Automatic Notifications** - Email alerts for SDI events (delivery, rejection, etc.)
- 📦 **Batch Operations** - Import/export multiple invoices with CSV

### 💰 Payment Tracking & Bank Reconciliation (v1.0.0 - NEW!)
- 🏦 **Multi-Bank Support** - Import statements from CSV, OFX, QIF formats
- 🔍 **Intelligent Matching** - Auto-reconcile payments using multiple algorithms:
  - Exact amount + date window matching
  - Fuzzy description matching with NLP (Levenshtein distance)
  - IBAN/BIC validation for wire transfers
  - Composite strategies with confidence scoring
- 📥 **Bank Presets** - Pre-configured importers for major Italian banks:
  - Intesa Sanpaolo, UniCredit, Revolut
  - Custom CSV mapping support
- 🎯 **Smart Reconciliation Workflow**:
  - Auto-apply high-confidence matches (>85%)
  - Review queue for medium-confidence matches (60-84%)
  - Manual reconciliation with interactive CLI
  - Transaction state management (UNMATCHED → MATCHED → IGNORED)
- 🔔 **Payment Reminders** - Automated reminder system with configurable strategies:
  - DEFAULT: Single reminder at due date
  - PROGRESSIVE: Escalating reminders (-7, -3, 0, +3, +7 days)
  - AGGRESSIVE: Frequent follow-ups for high-risk clients
  - CUSTOM: User-defined schedules
- 📧 **Multi-Channel Notifications** - Email, SMS, webhook support with Jinja2 templates
- 📊 **Rich CLI Interface** - `openfatture payment` commands for:
  - Transaction import and management
  - Interactive reconciliation with confidence scores
  - Batch operations with progress tracking
  - Payment reminder scheduling
- 🏗️ **Enterprise Architecture**:
  - Hexagonal Architecture (Ports & Adapters)
  - Domain-Driven Design with aggregates
  - SOLID principles, Strategy/Saga/Composite patterns
  - 74 comprehensive tests (100% pass rate)
  - 85%+ code coverage (enforced in CI)

### AI-Powered Workflows (Phase 4 - Partially Implemented)
- ✅ **Interactive Chat Assistant** - Conversational AI for invoicing questions and automation
- ✅ **Smart Descriptions** - Auto-generate invoice descriptions from natural language
- ✅ **Tax Suggestions** - AI recommends correct VAT rates and deductions
- ✅ **Tool Calling** - AI can search invoices, query clients, and retrieve statistics
- ✅ **Knowledge Retrieval** - RAG-powered normative snippets with citations (`openfatture ai rag`)
- ✅ **Session Management** - Persistent conversations with context tracking
- ✅ **Multi-Provider Support** - OpenAI, Anthropic, or local Ollama models
- 📈 **Cash Flow Forecasting** - ML-based payment predictions (CLI stub available)
- 🔍 **Compliance Checker** - AI validates invoices before SDI submission (CLI stub available)
- 🧠 **Multi-Agent System** - LangGraph orchestration for complex workflows (planned)

> **Status**: AI features are **now functional**! Access via interactive mode (`openfatture -i` → "AI Assistant" → "Chat") or CLI commands (`openfatture ai describe`, `openfatture ai suggest-vat`, `openfatture ai rag ...`). Full LangGraph orchestration and advanced agents planned for Phase 4.3-4.4.

### Developer Experience
- ⚡ **CLI-First** - Fast, keyboard-driven workflow
- 🐍 **Modern Python** - Type-safe with Pydantic, clean with Black/Ruff
- 🧪 **Fully Tested** - >80% coverage with pytest
- 🐳 **Docker Ready** - Containerized for easy deployment
- 📚 **Well Documented** - Comprehensive guides and examples

---

## Quick Start

### Prerequisites
- Python 3.12 or higher
- **uv** (fast Python package manager)
- PEC account (for SDI submission)
- Digital signature certificate (optional but recommended)

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/gianlucamazza/openfatture.git
cd openfatture

# Install dependencies
uv sync

# Initialize the database
uv run python -c "from openfatture.storage.database.session import init_db; init_db()"
```

### Configuration

```bash
# Copy configuration template
cp .env.example .env

# Edit with your data (REQUIRED)
nano .env
```

**Minimum required configuration:**
```env
# Your company data
CEDENTE_DENOMINAZIONE=Your Company Name
CEDENTE_PARTITA_IVA=12345678901
# ... (see .env.example for all fields)

# PEC credentials
PEC_ADDRESS=yourcompany@pec.it
PEC_PASSWORD=your_password
PEC_SMTP_SERVER=smtp.pec.aruba.it

# Email notifications
NOTIFICATION_EMAIL=admin@yourcompany.it
```

**📚 Full guides:**
- [Documentation Index](docs/README.md) - Navigazione completa per v1.0.0
- [Quick Start (IT)](docs/QUICKSTART.md) - Tutorial passo-passo
- [Quick Start (EN)](QUICKSTART.md) - CLI onboarding in 5 minuti
- [Configuration Reference](docs/CONFIGURATION.md) - Tutte le variabili `.env`

### First Invoice

```python
# See docs/QUICKSTART.md (IT) or QUICKSTART.md (EN) for complete examples
from openfatture.core.invoice.builder import InvoiceBuilder
from openfatture.utils.email.sender import TemplatePECSender

# Create invoice (see QUICKSTART.md)
# Send to SDI with professional email template
sender = TemplatePECSender(settings=get_settings())
success, error = sender.send_invoice_to_sdi(fattura, xml_path, signed=False)
```

---

## Architecture

> **📐 Visual Diagrams:** See [docs/ARCHITECTURE_DIAGRAMS.md](docs/ARCHITECTURE_DIAGRAMS.md) for Mermaid diagrams of system architecture, AI flows, SDI workflow, batch operations, and data model.

```
openfatture/
├── core/              # Business logic
│   ├── invoice/      # Invoice management
│   ├── batch/        # Batch operations (CSV import/export)
│   └── xml/          # FatturaPA XML generator
├── sdi/              # SDI integration
│   ├── validator/    # XSD validation
│   └── notifiche/    # SDI notification parser (AT, RC, NS, MC, NE)
├── payment/          # Payment tracking & bank reconciliation (v1.0.0)
│   ├── domain/       # Domain models (BankAccount, BankTransaction, PaymentReminder)
│   ├── application/  # Application services
│   │   ├── services/ # MatchingService, ReconciliationService, ReminderScheduler
│   │   └── notifications/ # EmailNotifier, ConsoleNotifier, CompositeNotifier
│   ├── matchers/     # Matching strategies (Exact, Fuzzy, IBAN, Composite)
│   ├── infrastructure/ # Infrastructure layer
│   │   ├── importers/ # CSV, OFX, QIF importers with bank presets
│   │   └── repository.py # Data access layer
│   ├── cli/          # CLI commands (import, reconcile, reminders)
│   └── templates/    # Email templates for payment reminders
├── ai/               # AI & LLM integration (Phase 4)
│   ├── agents/       # AI agents (InvoiceAssistant, TaxAdvisor, ChatAgent)
│   ├── providers/    # LLM providers (OpenAI, Anthropic, Ollama)
│   ├── domain/       # Core models (Message, Context, Response)
│   ├── session/      # Chat session management
│   ├── tools/        # Function calling tools (search, query, stats)
│   ├── context/      # Context enrichment utilities
│   └── prompts/      # YAML prompt templates
├── utils/            # Utilities
│   ├── email/        # Email templates & PEC sender
│   │   ├── templates/    # Jinja2 HTML/text templates
│   │   ├── i18n/         # Translations (IT/EN)
│   │   ├── models.py     # Pydantic context models
│   │   ├── renderer.py   # Template engine
│   │   ├── sender.py     # TemplatePECSender
│   │   └── styles.py     # Email CSS/branding
│   ├── signature/    # Digital signature (PKCS#12)
│   ├── rate_limiter.py   # Rate limiting for PEC
│   └── config.py     # Pydantic Settings
├── storage/          # Data persistence
│   └── database/     # SQLAlchemy models (Cliente, Fattura, Pagamento, NotificaSDI)
├── cli/              # Command-line interface (Typer)
│   └── ui/           # Interactive UI (menus, chat interface)
├── examples/         # Usage examples
├── docs/             # Documentation
└── tests/            # Test suite (pytest)
    ├── payment/      # Payment module tests (74 tests, 100% pass rate)
    ├── unit/         # Unit tests
    └── integration/  # Integration tests
```

---

## Compliance

OpenFatture implements the latest Italian e-invoicing standards:

| Requirement | Status | Notes |
|-------------|--------|-------|
| FatturaPA XML v1.9 | ✅ | Mandatory from April 1, 2025 |
| SDI Submission | ✅ | Via PEC (primary) or API |
| Simplified Invoices | ✅ | For amounts <400€ |
| Reverse Charge | ✅ | Construction, subcontracting |
| Digital Preservation | ✅ | 10-year storage |
| GDPR | ✅ | Encryption at rest, audit logs |

---

## Usage

OpenFatture può essere utilizzato sia tramite **CLI/TUI interattiva** sia come **libreria Python**. Per una panoramica completa consulta l'[indice della documentazione](docs/README.md).

### CLI

```bash
# wizard interattivo per emettere una fattura
uv run openfatture fattura crea

# invio PEC con template professionale
uv run openfatture fattura invia 42 --pec

# dashboard testuale con AI chat
uv run openfatture --interactive
```

### Python API

```python
# Create and send invoice
from openfatture.storage.database.models import Cliente, Fattura
from openfatture.core.xml.generator import FatturaXMLGenerator
from openfatture.utils.email.sender import TemplatePECSender

# Create invoice
fattura = Fattura(...)  # See docs/QUICKSTART.md (IT) or QUICKSTART.md (EN)

# Generate XML
generator = FatturaXMLGenerator(fattura)
xml_tree = generator.generate()

# Send to SDI with email template
sender = TemplatePECSender(settings=settings)
success, error = sender.send_invoice_to_sdi(fattura, xml_path, signed=False)
```

### Email Notifications

```python
# Automatic SDI notifications
from openfatture.sdi.notifiche.processor import NotificationProcessor

processor = NotificationProcessor(
    db_session=session,
    email_sender=sender  # Auto-send emails on SDI events
)

# Process notification file
success, error, notification = processor.process_file(Path("RC_IT12345678901_00001.xml"))
# → Automatically sends email to NOTIFICATION_EMAIL
```

### Batch Operations

```python
# Import invoices from CSV
from openfatture.core.batch.processor import BatchProcessor

processor = BatchProcessor(db_session=session)
result = processor.import_from_csv(Path("invoices.csv"))

# Send summary email
sender.send_batch_summary(result, operation_type="import", recipients=[...])
```

**📚 See [docs/QUICKSTART.md](docs/QUICKSTART.md) for complete examples**

---

## AI Integration (Phase 4 - Partially Implemented)

OpenFatture features an **AI-powered assistant** with LLM integration (OpenAI, Anthropic, Ollama).

### Implemented Features

**✅ Interactive Chat Assistant**
```bash
# Start interactive mode and select AI Assistant
openfatture -i
# Navigate to: 8. AI Assistant → 1. Chat

# Or use CLI commands directly
openfatture ai describe "sviluppo API REST" --hours 8 --tech "Python,FastAPI"
openfatture ai suggest-vat "consulenza IT per azienda edile"
```

**✅ Available AI Agents**
1. **Chat Assistant** - Conversational AI with tool calling for invoices/clients
2. **Invoice Assistant** - Generates detailed descriptions from brief inputs
3. **Tax Advisor** - Suggests correct VAT rates and fiscal treatments

**✅ AI Capabilities**
- 🔍 Search invoices and clients via natural language
- 📊 Get statistics and analytics on demand
- 💬 Multi-turn conversations with context
- 🛠️ Function calling with 6 built-in tools
- 💾 Session persistence and export (JSON/Markdown)
- 🎯 Structured outputs with Pydantic validation

**Example Chat Conversation:**
```
Tu: Quante fatture ho emesso quest'anno?
AI: Quest'anno hai emesso 42 fatture per un totale di €125,430.00...

Tu: Cerca fatture del cliente Rossi
AI: Ho trovato 5 fatture per Mario Rossi SRL...

Tu: Mostrami le ultime 5 fatture
AI: Ecco le ultime 5 fatture emesse: [...]
```

### Planned Features (Phase 4.3-4.4)

- [ ] **Cash Flow Predictor** - ML-based payment predictions (stub available)
- [ ] **Compliance Checker** - AI validates invoices before SDI submission (stub available)
- [ ] **LangGraph Orchestration** - Multi-agent workflows
- [ ] **RAG with ChromaDB** - Semantic search over invoice history

**📖 Full guide:** [examples/AI_CHAT_ASSISTANT.md](examples/AI_CHAT_ASSISTANT.md)

---

## Development

### Setup Development Environment

```bash
# Install all dependencies (including dev)
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install

# Run tests
uv run python -m pytest

# Run with coverage
uv run python -m pytest --cov=openfatture --cov-report=html

# Lint and format
uv run black .
uv run ruff check .
uv run mypy openfatture/
```

### Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/test_xml_builder.py

# With verbose output
pytest -v

# Watch mode (requires pytest-watch)
ptw
```

---

## Roadmap

### ✅ Phase 1 - Core Foundation (Completed)
- [x] Project setup with modern Python tooling (uv)
- [x] Core models (Cliente, Fattura, LineaFattura)
- [x] Database layer with SQLAlchemy
- [x] Configuration management with Pydantic Settings
- [x] Test infrastructure with pytest

### ✅ Phase 2 - SDI Integration (Completed)
- [x] FatturaPA XML v1.9 generator
- [x] XSD validation
- [x] Digital signature support (PKCS#12)
- [x] PEC email sender with rate limiting
- [x] SDI notification parser (AT, RC, NS, MC, NE)
- [x] **Professional email templates (HTML + text)**
- [x] **Automatic email notifications for SDI events**
- [x] **Batch operations with CSV import/export**
- [x] **Internationalization (IT/EN)**

### ✅ Phase 3 - CLI & User Experience (95% Complete)
- [x] Interactive CLI with Typer
- [x] Invoice creation wizard
- [x] Client management commands
- [x] Status monitoring dashboard (fatturato + scadenze pagamenti raggruppate)
- [x] Batch operation commands
- [x] Report generation (IVA, clienti, scadenze)
- [x] Email template management
- [x] SDI notification processing
- [x] PDF generation for human-readable invoices (PDF/A-3 templates disponibili)

### 📋 Phase 4 - AI Layer (In Progress - Partially Implemented)
- [x] LLM provider abstraction (OpenAI, Anthropic, Ollama)
- [x] Base agent protocol and implementations
- [x] **Interactive Chat Assistant with tool calling**
- [x] **Session management and persistence**
- [x] **Tool registry with 6 built-in tools**
- [x] Invoice description generator: `ai describe` (functional)
- [x] Tax suggestion agent: `ai suggest-vat` (functional)
- [x] Prompt template system (YAML-based)
- [x] Context enrichment for business data
- [x] Cash flow forecasting: `ai forecast` (Prophet + XGBoost ensemble con modelli salvati e metriche)
- [ ] Compliance checker agent: `ai check` (stub available)
- [ ] Multi-agent orchestration with LangGraph
- [ ] Vector embeddings with ChromaDB (RAG)

### ✅ Phase 5 - Payment Module (v1.0.0 - Completed!)
- [x] **Bank statement import** (CSV, OFX, QIF formats)
- [x] **Intelligent payment matching** (5 algorithms with confidence scoring)
- [x] **Bank reconciliation workflow** (auto-match, review queue, manual)
- [x] **Payment reminders** (4 strategies: DEFAULT, PROGRESSIVE, AGGRESSIVE, CUSTOM)
- [x] **Multi-channel notifications** (Email, SMS, webhook)
- [x] **CLI commands** (`openfatture payment` with 8 commands)
- [x] **74 comprehensive tests** (100% pass rate, 85%+ coverage)

### 🚀 Phase 6 - Production & Advanced (Future)
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Accountant export formats (CSV, Excel)
- [ ] Payment gateway integration
- [ ] Web GUI (optional)

**Current Status**: Phase 2 ✅ | Phase 3 95% ✅ | **Phase 5 (Payment Module v1.0.0) ✅** | Phase 4 (AI) 60% 🚧

---

## 📚 Documentation

Complete documentation is available in the `docs/` directory:

| Document | Description |
|----------|-------------|
| [docs/README.md](docs/README.md) | 📚 Documentation index, release hub and navigation |
| [docs/releases/v1.0.1.md](docs/releases/v1.0.1.md) | AI Cash Flow Upgrade (ensemble Prophet + XGBoost, metriche) |
| [docs/releases/v1.0.0.md](docs/releases/v1.0.0.md) | Detailed release notes for v1.0.0 |
| [QUICKSTART.md](QUICKSTART.md) | Quick CLI onboarding (EN, 5 minutes) |
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | Step-by-step guide in Italian (15 minutes) |
| [ARCHITECTURE_DIAGRAMS.md](docs/ARCHITECTURE_DIAGRAMS.md) | **NEW!** Visual Mermaid diagrams (system, AI, SDI, batch, data model) |
| [AI_ARCHITECTURE.md](docs/AI_ARCHITECTURE.md) | AI module architecture and agent implementation details |
| [CONFIGURATION.md](docs/CONFIGURATION.md) | Complete reference for all configuration options |
| [EMAIL_TEMPLATES.md](docs/EMAIL_TEMPLATES.md) | Email templates system documentation |
| [CLI_REFERENCE.md](docs/CLI_REFERENCE.md) | Full CLI command catalogue with examples |
| [BATCH_OPERATIONS.md](docs/BATCH_OPERATIONS.md) | CSV import/export workflow and best practices |
| [PAYMENT_TRACKING.md](docs/PAYMENT_TRACKING.md) | **NEW!** Payment tracking & bank reconciliation module (v1.0.0) |

### Examples

Practical code examples are in the `examples/` directory:

```bash
# Email templates examples
uv run python examples/email_templates_example.py

# Payment tracking examples (NEW!)
uv run python examples/payment_examples.py

# Basic usage
uv run python examples/basic_usage.py
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas We Need Help
- 🧪 Test coverage improvements
- 📖 Documentation (especially for non-technical users)
- 🌍 Internationalization (currently Italian-only)
- 🔌 Integration with accounting software
- 🎨 Web UI design (future phase)

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Disclaimer

This software is provided as-is for educational and productivity purposes. Users are responsible for ensuring compliance with Italian tax regulations. We recommend consulting with a certified accountant (*commercialista*) for tax-related questions.

---

## Support

- 📖 **Documentation**: See `docs/` directory ([QUICKSTART](docs/QUICKSTART.md), [CONFIGURATION](docs/CONFIGURATION.md), [EMAIL_TEMPLATES](docs/EMAIL_TEMPLATES.md))
- 💬 **Community**: [GitHub Discussions](https://github.com/gianlucamazza/openfatture/discussions)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/gianlucamazza/openfatture/issues)
- 📧 **Email**: info@gianlucamazza.it

### Getting Help

1. Check the [QUICKSTART.md](docs/QUICKSTART.md) guide
2. Review [CONFIGURATION.md](docs/CONFIGURATION.md) for configuration issues
3. See [examples/](examples/) directory for code examples
4. Search existing [GitHub Issues](https://github.com/gianlucamazza/openfatture/issues)
5. Ask on [GitHub Discussions](https://github.com/gianlucamazza/openfatture/discussions)

---

**Made with ❤️ by freelancers, for freelancers.**
