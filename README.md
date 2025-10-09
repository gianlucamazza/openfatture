# OpenFatture 🧾

**Open-source electronic invoicing system for Italian freelancers** - CLI-first with AI-powered workflows.

> A modern, compliant alternative to proprietary invoicing platforms, designed for tech-savvy freelancers who value transparency, automation, and control.

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](CHANGELOG.md)
[![CI Tests](https://github.com/gianlucamazza/openfatture/actions/workflows/test.yml/badge.svg)](https://github.com/gianlucamazza/openfatture/actions/workflows/test.yml)
[![Release](https://github.com/gianlucamazza/openfatture/actions/workflows/release.yml/badge.svg)](https://github.com/gianlucamazza/openfatture/actions/workflows/release.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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
- 💰 **Payment Tracking** - Monitor due dates and overdue invoices

### AI-Powered Workflows (2025 Best Practices)
- 🤖 **Smart Descriptions** - Auto-generate invoice descriptions from natural language
- 💡 **Tax Suggestions** - AI recommends correct VAT rates and deductions
- 📈 **Cash Flow Forecasting** - ML-based payment predictions
- 🔍 **Compliance Checker** - AI validates invoices before SDI submission
- 🧠 **Multi-Agent System** - LangGraph orchestration for complex workflows

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
- [Quick Start Guide](docs/QUICKSTART.md) - Step-by-step tutorial
- [Configuration Reference](docs/CONFIGURATION.md) - All config options

### First Invoice

```python
# See docs/QUICKSTART.md for complete examples
from openfatture.core.invoice.builder import InvoiceBuilder
from openfatture.utils.email.sender import TemplatePECSender

# Create invoice (see QUICKSTART.md)
# Send to SDI with professional email template
sender = TemplatePECSender(settings=get_settings())
success, error = sender.send_invoice_to_sdi(fattura, xml_path, signed=False)
```

---

## Architecture

```
openfatture/
├── core/              # Business logic
│   ├── invoice/      # Invoice management
│   ├── batch/        # Batch operations (CSV import/export)
│   └── xml/          # FatturaPA XML generator
├── sdi/              # SDI integration
│   ├── validator/    # XSD validation
│   └── notifiche/    # SDI notification parser (AT, RC, NS, MC, NE)
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
│   └── database/     # SQLAlchemy models (Cliente, Fattura, NotificaSDI)
├── cli/              # Command-line interface (Typer)
├── examples/         # Usage examples
├── docs/             # Documentation
└── tests/            # Test suite (pytest)
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

OpenFatture is primarily used as a **Python library**. CLI commands are planned for future releases.

### Python API

```python
# Create and send invoice
from openfatture.storage.database.models import Cliente, Fattura
from openfatture.core.xml.generator import FatturaXMLGenerator
from openfatture.utils.email.sender import TemplatePECSender

# Create invoice
fattura = Fattura(...)  # See docs/QUICKSTART.md

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

## AI Integration

OpenFatture uses **LangChain + LangGraph** for intelligent automation:

### Available Agents

1. **Invoice Assistant** - Generates detailed descriptions from brief inputs
2. **Tax Advisor** - Suggests correct VAT rates and deductions
3. **Cash Flow Predictor** - Forecasts payment timing based on historical data
4. **Compliance Checker** - Pre-validates invoices with AI reasoning

### Configuration

```bash
# Set your LLM provider (supports OpenAI, Anthropic, local models)
openfatture config --set ai.provider anthropic
openfatture config --set ai.api_key sk-ant-...

# Or use local models with Ollama (privacy-first)
openfatture config --set ai.provider ollama
openfatture config --set ai.model llama3
```

---

## Development

### Setup Development Environment

```bash
# Install all dependencies (including dev)
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=openfatture --cov-report=html

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

### 🚧 Phase 3 - CLI & User Experience (In Progress)
- [ ] Interactive CLI with Typer
- [ ] Invoice creation wizard
- [ ] Client management commands
- [ ] Status monitoring dashboard
- [ ] PDF generation for human-readable invoices

### 📋 Phase 4 - AI Layer (Planned)
- [ ] LangChain integration
- [ ] Invoice description generator
- [ ] Tax suggestion agent
- [ ] Cash flow forecasting
- [ ] Multi-agent orchestration

### 🚀 Phase 5 - Production & Advanced (Future)
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Bank statement import
- [ ] Accountant export formats (CSV, Excel)
- [ ] Payment gateway integration
- [ ] Web GUI (optional)

**Current Status**: Phase 2 completed ✅ | Phase 3 in progress 🚧

---

## 📚 Documentation

Complete documentation is available in the `docs/` directory:

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](docs/QUICKSTART.md) | Step-by-step guide to get started in 15 minutes |
| [CONFIGURATION.md](docs/CONFIGURATION.md) | Complete reference for all configuration options |
| [EMAIL_TEMPLATES.md](docs/EMAIL_TEMPLATES.md) | Email templates system documentation |

### Examples

Practical code examples are in the `examples/` directory:

```bash
# Email templates examples
uv run python examples/email_templates_example.py

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
