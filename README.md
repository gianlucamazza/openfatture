# OpenFatture 🧾

**Open-source electronic invoicing for Italian freelancers** — built around a CLI-first workflow, AI automation, and payment reconciliation.

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](CHANGELOG.md)
[![CI Tests](https://github.com/gianlucamazza/openfatture/actions/workflows/test.yml/badge.svg)](https://github.com/gianlucamazza/openfatture/actions/workflows/test.yml)
[![Release](https://github.com/gianlucamazza/openfatture/actions/workflows/release.yml/badge.svg)](https://github.com/gianlucamazza/openfatture/actions/workflows/release.yml)
[![Media Generation](https://github.com/gianlucamazza/openfatture/actions/workflows/media-generation.yml/badge.svg)](https://github.com/gianlucamazza/openfatture/actions/workflows/media-generation.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> 📘 For the consolidated v1.1.0 documentation, visit the docs hub at `docs/README.md` and the release notes in `docs/releases/`.

---

## Quick Links
- `docs/README.md` – Documentation hub and navigation index
- `docs/QUICKSTART.md` – Extended quickstart (15-minute setup walkthrough)
- `QUICKSTART.md` – Quickstart (5-minute CLI tour)
- `docs/releases/v1.1.0.md` – Latest release notes
- `docs/releases/v1.0.1.md` – Upcoming AI cash flow upgrade (in progress)
- `CHANGELOG.md` – Full change log
- `docs/history/ROADMAP.md` – Roadmap and phase breakdown
- `docs/reports/TEST_RESULTS_SUMMARY.md` – Test and coverage report
- `CONTRIBUTING.md` – Contribution guidelines

---

## Highlights
- **Core invoicing** – Generates FatturaPA XML v1.9, handles PEC delivery to SDI, supports digital signatures, and validates automatically.
- **Quote management** – Create and manage preventivi (quotes/estimates) with automatic PDF generation and client tracking.
- **Payment & reconciliation** – Multi-bank imports, intelligent reconciliation, and configurable reminders (`docs/PAYMENT_TRACKING.md`).
- **Lightning Network payments** – Instant Bitcoin payments via LND integration with automatic EUR conversion, channel liquidity monitoring, and real-time webhook notifications.
- **AI workflows** – Chat assistant, VAT guidance, description generation, **voice interaction** with speech-to-text and text-to-speech, custom slash commands, RAG knowledge base, ReAct tool calling, and ML model retraining powered by OpenAI, Anthropic, or Ollama (`examples/AI_CHAT_ASSISTANT.md`).
- **Web UI** – Modern Streamlit interface with real-time dashboard, invoice management, AI assistant, and Lightning payments (`docs/WEB_UI_GUIDE.md`).
- **Custom AI commands** – User-defined slash commands for repetitive workflows (invoicing, tax, reporting) with Jinja2 templating.
- **Automation hooks** – Lifecycle hooks for custom automation on invoice creation, sending, and other events.
- **Event audit trail** – Complete event system with analytics, timelines, and compliance reporting.
- **Regulatory monitoring** – Automatic web scraping for tax law updates and compliance alerts.
- **Developer experience** – Modern Python toolchain (uv, Typer, Pydantic), 170+ automated tests with CI coverage gate at 50% (targeting 60%), plus Docker and Makefile automation.
- **Compliance & operations** – GDPR-ready logging, professional email templates, and turnkey PEC workflows.

---

## Advanced Features

- **Lightning Network Integration** – Production-ready LND client with circuit breaker, multi-provider BTC/EUR conversion, automated liquidity management, and real-time payment notifications
- **RAG Knowledge Base** – Semantic search and automatic citation of tax regulations with ChromaDB vector storage
- **ReAct Orchestration** – Tool calling for Ollama models with 80%+ success rate using qwen3:8b
- **ML Model Retraining** – Automatic cash flow model updates based on user feedback and prediction accuracy
- **Event-Driven Architecture** – Complete audit trail with entity tracking, timeline generation, and analytics dashboard
- **Lifecycle Hooks** – Extensible automation system for business processes (invoice creation, sending, etc.)
- **Regulatory Monitoring** – Automated web scraping for tax law updates and compliance alerts
- **Feedback Analytics** – User feedback collection and ML prediction quality analysis
- **Batch Operations** – CSV import/export with validation, dry-run mode, and summary reporting

---

## Demo Library
- Scenario A — Setup & configuration: https://github.com/user-attachments/assets/scenario_a_onboarding.mp4
- Scenario B — Professional invoicing: https://github.com/user-attachments/assets/scenario_b_invoice.mp4
- Scenario C — AI Assistant with local Ollama: https://github.com/user-attachments/assets/scenario_c_ai.mp4
- Scenario D — Batch operations & analytics: https://github.com/user-attachments/assets/scenario_d_batch.mp4
- Scenario E — PEC integration & SDI notifications: https://github.com/user-attachments/assets/scenario_e_pec.mp4
- Scenario F — Quote management & preventivo workflow: https://github.com/user-attachments/assets/scenario_f_preventivo.mp4
- Scenario G — Custom AI commands & automation: https://github.com/user-attachments/assets/scenario_g_custom_commands.mp4
- Additional assets live in `media/output/` (videos) and `media/screenshots/` (images)

---

## Getting Started

### Prerequisites
- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/) package manager
- PEC mailbox credentials (for SDI delivery)
- Optional: digital signature certificate (PKCS#12)

### Installation & Setup

```bash
git clone https://github.com/gianlucamazza/openfatture.git
cd openfatture
uv sync
cp .env.example .env
```

Populate `.env` with company data, PEC credentials, and notification settings (see `docs/CONFIGURATION.md`), then initialise the database:

```bash
uv run python -c "from openfatture.storage.database.session import init_db; init_db()"
```

### Next Steps
- Follow the extended quickstart in `docs/QUICKSTART.md` or the slim walkthrough in `QUICKSTART.md`.
- Review the complete CLI catalogue in `docs/CLI_REFERENCE.md`.
- Explore `docs/PAYMENT_TRACKING.md` to master reconciliation and reminders.

---

## Usage

### CLI Examples

```bash
# Setup & initialization
uv run openfatture init  # Interactive setup wizard
uv run openfatture config show  # View current configuration

# Core invoicing
uv run openfatture fattura crea
uv run openfatture preventivo crea --cliente 123
uv run openfatture fattura invia 456  # Send invoice via PEC

# Payment & reconciliation
uv run openfatture payment reconcile
uv run openfatture payment import statement.ofx
uv run openfatture payment audit --payment 123

# Lightning Network payments
uv run openfatture lightning status
uv run openfatture lightning invoice create --fattura-id 123
uv run openfatture lightning channels status
uv run openfatture lightning liquidity report

# SDI notifications & compliance
uv run openfatture notifiche process notification.xml
uv run openfatture notifiche list --tipo RC

# Batch operations
uv run openfatture batch import invoices.csv --dry-run
uv run openfatture batch export report.csv --anno 2025

# Reporting & analytics
uv run openfatture report iva --anno 2025 --trimestre Q1
uv run openfatture report clienti --anno 2025
uv run openfatture report scadenze

# AI workflows
uv run openfatture ai describe "3 hours consulting"
uv run openfatture ai suggest-vat "web development service"
uv run openfatture ai forecast --months 6 --retrain
uv run openfatture ai check 456 --level advanced  # Compliance check
uv run openfatture ai rag status  # Knowledge base status
uv run openfatture ai rag search "reverse charge"  # Semantic search
uv run openfatture ai feedback stats  # User feedback analytics
uv run openfatture ai retrain status  # ML model retraining status
uv run openfatture ai chat  # Interactive with custom commands
uv run openfatture ai voice-chat  # Voice interaction (STT + TTS)
uv run openfatture ai voice-chat --interactive  # Continuous voice conversation

# Event analytics & audit
uv run openfatture events dashboard
uv run openfatture events timeline invoice 456
uv run openfatture events search "cliente Rossi"

# Automation & hooks
uv run openfatture hooks list --enabled
uv run openfatture hooks create on-invoice-created
uv run openfatture web-scraper status

# Interactive mode
uv run openfatture --interactive
```

### Python API

```python
from openfatture.storage.database.models import Fattura, Preventivo, Cliente
from openfatture.core.xml.generator import FatturaXMLGenerator
from openfatture.core.preventivi.service import PreventivoService
from openfatture.core.events import InvoiceCreatedEvent, event_bus
from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.domain.context import InvoiceContext
from openfatture.utils.email.sender import TemplatePECSender
from openfatture.utils.config import get_settings

# Invoice creation with event tracking
invoice = Fattura(...)  # See QUICKSTART for complete examples
xml_tree = FatturaXMLGenerator(invoice).generate()

# Publish event for audit trail
event = InvoiceCreatedEvent(invoice_id=invoice.id, user_id="system")
event_bus.publish(event)

TemplatePECSender(settings=get_settings()).send_invoice_to_sdi(
    invoice,
    xml_path="invoice.xml",
    signed=False,
)

# Quote management workflow
quote_service = PreventivoService()
quote = Preventivo(...)  # Create quote with client, lines, validity
quote_service.save(quote)

# Convert to invoice when approved
if quote.stato == "approvato":
    invoice_from_quote = quote_service.convert_to_invoice(quote.id)

# AI-powered invoice description
agent = InvoiceAssistantAgent()
context = InvoiceContext(user_input="3 hours backend development")
response = await agent.execute(context)
description = response.content

# Event analytics
from openfatture.core.events.analytics import EventAnalyticsService
analytics = EventAnalyticsService()
stats = analytics.get_dashboard_summary(days=30)
print(f"Total events: {stats.total_events}")
```

More examples live in the `examples/` directory.

---

## Documentation
- `docs/README.md` – Navigation index for guides, diagrams, and releases
- `docs/QUICKSTART.md` – Extended quickstart (15-minute setup walkthrough)
- `docs/CONFIGURATION.md` – Complete `.env` and settings reference
- `docs/AI_ARCHITECTURE.md` – AI agent architecture, RAG, and ReAct orchestration
- `docs/PAYMENT_TRACKING.md` – Reconciliation workflows and reminders
- `docs/examples/custom-commands/README.md` – Custom AI commands guide
- `docs/HOOKS.md` – Lifecycle hooks documentation
- `docs/ARCHITECTURE_DIAGRAMS.md` – Mermaid diagrams of the platform
- `docs/BATCH_OPERATIONS.md` – CSV import/export and bulk operations
- `docs/CLI_REFERENCE.md` – Complete command reference with examples

---

## Development
- Install dev extras and pre-commit hooks: `uv sync --all-extras` and `uv run pre-commit install`
- Run the tests: `uv run python -m pytest` (coverage: `uv run python -m pytest --cov=openfatture`)
- CI/CD, automation, and media workflows are documented in `docs/DEVELOPMENT.md`, `docs/operations/SETUP_CI_CD.md`, and related guides

---

## Project Status
- Latest stable release: `docs/releases/v1.1.0.md` (Event System & Audit Trail)
- Current features: 170+ automated tests, RAG knowledge base, ReAct tool calling, ML retraining, event analytics
- Upcoming features: Enhanced regulatory AI, advanced compliance automation, multi-language support
- Detailed roadmap and phase summaries: `docs/history/ROADMAP.md` and `docs/history/PHASE_*_SUMMARY.md`
- Current focus: AI orchestration (Phase 4) and production hardening (Phase 6)
- Test coverage: 50%+ (targeting 60%), 170+ tests passing

---

## Contributing & License
Contributions are welcome! Read `CONTRIBUTING.md` and open an issue for substantial proposals. OpenFatture ships under the MIT License (see `LICENSE`).

---

## Support
- Documentation: `docs/README.md`, quickstart guides, and the `examples/` directory
- Community: [GitHub Discussions](https://github.com/gianlucamazza/openfatture/discussions)
- Bugs & feature requests: [GitHub Issues](https://github.com/gianlucamazza/openfatture/issues)
- Email: info@gianlucamazza.it

---

## Troubleshooting

### Common Issues

**PEC Connection Problems:**
```bash
# Test PEC credentials
uv run openfatture pec test

# Check SMTP settings in .env
uv run openfatture config show | grep PEC
```

**AI Model Issues:**
```bash
# Check AI configuration
uv run openfatture config show | grep AI

# Test AI connectivity
uv run openfatture ai describe "test" --format json
```

**Database Issues:**
```bash
# Reinitialize database (WARNING: destroys data)
uv run python -c "from openfatture.storage.database.session import init_db; init_db()"

# Check database path
uv run openfatture config show | grep database_url
```

**SDI Validation Errors:**
```bash
# Validate XML before sending
uv run openfatture fattura xml 123 --validate

# Check compliance
uv run openfatture ai check 123 --level advanced --verbose
```

**RAG Knowledge Base Issues:**
```bash
# Check RAG status
uv run openfatture ai rag status

# Reindex knowledge base
uv run openfatture ai rag index --force
```

**Event System Issues:**
```bash
# Check event persistence
uv run openfatture events stats

# View recent errors
uv run openfatture events list --type ErrorEvent --limit 10
```

**Voice Features Issues:**
```bash
# Check voice configuration
uv run openfatture config show | grep VOICE

# Test voice interaction
uv run openfatture ai voice-chat --duration 5 --no-playback

# Verify OpenAI API key (required for voice)
uv run openfatture config show | grep OPENAI_API_KEY

# Test microphone access
uv run openfatture ai voice-chat --save-audio --duration 3
```

### Getting Help

- **Logs**: Check `~/.openfatture/logs/` for detailed error information
- **Debug Mode**: Add `--verbose` to most commands for additional output
- **Configuration**: Run `openfatture config show` to verify settings
- **Tests**: Run `uv run python -m pytest tests/` to check system health

---

## Disclaimer
The software is provided “as-is” for educational and production use. Ensure compliance with Italian tax regulations and consult a certified accountant when in doubt.

---

Made with ❤️ by freelancers, for freelancers.
