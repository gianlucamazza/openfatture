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
- **Payment & reconciliation** – Multi-bank imports, intelligent reconciliation, and configurable reminders (`docs/PAYMENT_TRACKING.md`).
- **AI workflows** – Chat assistant, VAT guidance, and description generation powered by OpenAI, Anthropic, or Ollama (`examples/AI_CHAT_ASSISTANT.md`).
- **Developer experience** – Modern Python toolchain (uv, Typer, Pydantic), 117 automated tests with CI coverage gate at 50% (targeting 60%), plus Docker and Makefile automation.
- **Compliance & operations** – GDPR-ready logging, professional email templates, and turnkey PEC workflows.

---

## Demo Library
- Scenario A — Setup & configuration: https://github.com/user-attachments/assets/scenario_a_onboarding.mp4
- Scenario B — Professional invoicing: https://github.com/user-attachments/assets/scenario_b_invoice.mp4
- Scenario C — AI Assistant with local Ollama: https://github.com/user-attachments/assets/scenario_c_ai.mp4
- Scenario D — Batch operations & analytics: https://github.com/user-attachments/assets/scenario_d_batch.mp4
- Scenario E — PEC integration & SDI notifications: https://github.com/user-attachments/assets/scenario_e_pec.mp4
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
uv run openfatture fattura crea
uv run openfatture payment reconcile
uv run openfatture --interactive
```

### Python API

```python
from openfatture.storage.database.models import Fattura
from openfatture.core.xml.generator import FatturaXMLGenerator
from openfatture.utils.email.sender import TemplatePECSender
from openfatture.utils.config import get_settings

invoice = Fattura(...)  # See QUICKSTART for complete examples
xml_tree = FatturaXMLGenerator(invoice).generate()
TemplatePECSender(settings=get_settings()).send_invoice_to_sdi(
    invoice,
    xml_path="invoice.xml",
    signed=False,
)
```

More examples live in the `examples/` directory.

---

## Documentation
- `docs/README.md` – Navigation index for guides, diagrams, and releases
- `docs/CONFIGURATION.md` – Complete `.env` and settings reference
- `docs/AI_ARCHITECTURE.md` – AI agent architecture and integrations
- `docs/PAYMENT_TRACKING.md` – Reconciliation workflows and reminders
- `docs/ARCHITECTURE_DIAGRAMS.md` – Mermaid diagrams of the platform

---

## Development
- Install dev extras and pre-commit hooks: `uv sync --all-extras` and `uv run pre-commit install`
- Run the tests: `uv run python -m pytest` (coverage: `uv run python -m pytest --cov=openfatture`)
- CI/CD, automation, and media workflows are documented in `docs/DEVELOPMENT.md`, `docs/operations/SETUP_CI_CD.md`, and related guides

---

## Project Status
- Latest stable release: `docs/releases/v1.0.1.md` (AI Cash Flow Upgrade)
- Detailed roadmap and phase summaries: `docs/history/ROADMAP.md` and `docs/history/PHASE_*_SUMMARY.md`
- Current focus: AI orchestration (Phase 4) and production hardening (Phase 6)

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

## Disclaimer
The software is provided “as-is” for educational and production use. Ensure compliance with Italian tax regulations and consult a certified accountant when in doubt.

---

Made with ❤️ by freelancers, for freelancers.
