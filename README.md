# OpenFatture 🧾

**Open-source electronic invoicing system for Italian freelancers** – CLI-first with AI-powered workflows and bank reconciliation.

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![CI Tests](https://github.com/gianlucamazza/openfatture/actions/workflows/test.yml/badge.svg)](https://github.com/gianlucamazza/openfatture/actions/workflows/test.yml)
[![Release](https://github.com/gianlucamazza/openfatture/actions/workflows/release.yml/badge.svg)](https://github.com/gianlucamazza/openfatture/actions/workflows/release.yml)
[![Media Generation](https://github.com/gianlucamazza/openfatture/actions/workflows/media-generation.yml/badge.svg)](https://github.com/gianlucamazza/openfatture/actions/workflows/media-generation.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> 📘 Per la documentazione consolidata v1.0.0 consulta l'hub principale in `docs/README.md` e le note di rilascio in `docs/releases/`.

---

## Quick Links
- `docs/README.md` – Hub di documentazione e navigazione
- `docs/QUICKSTART.md` – Guida rapida in italiano
- `QUICKSTART.md` – Guida rapida in inglese (CLI in 5 minuti)
- `docs/releases/v1.0.1.md` – Aggiornamento più recente
- `CHANGELOG.md` – Storico completo delle modifiche
- `docs/history/ROADMAP.md` – Roadmap e fasi di progetto
- `docs/reports/TEST_RESULTS_SUMMARY.md` – Report test e copertura
- `CONTRIBUTING.md` – Regole per contribuire

---

## Highlights
- **Core invoicing** – Generazione FatturaPA XML v1.9, invio SDI via PEC, firme digitali e validazione automatica.
- **Payment & reconciliation** – Import multi-banca, riconciliazione intelligente e reminder configurabili (`docs/PAYMENT_TRACKING.md`).
- **AI workflows** – Chat assistant, suggerimenti IVA e descrizioni automatiche con provider OpenAI/Anthropic/Ollama (`examples/AI_CHAT_ASSISTANT.md`).
- **Developer experience** – Stack Python moderno (uv, Typer, Pydantic), 117 test automatizzati con copertura media ~56% e gate CI al 50% (roadmap → 60%), Docker e script pronti.
- **Compliance & operations** – Gestione GDPR, log di audit, template email professionali e flussi PEC pronti all’uso.

---

## Demo
- Scenario A — Setup & configurazione: https://github.com/user-attachments/assets/scenario_a_onboarding.mp4
- Scenario B — Emissione fatture professionali: https://github.com/user-attachments/assets/scenario_b_invoice.mp4
- Scenario C — Assistant AI con Ollama locale: https://github.com/user-attachments/assets/scenario_c_ai.mp4
- Scenario D — Operazioni batch & analytics: https://github.com/user-attachments/assets/scenario_d_batch.mp4
- Scenario E — Integrazione PEC & notifiche SDI: https://github.com/user-attachments/assets/scenario_e_pec.mp4
- Libreria media completa in `media/output/` (video) e `media/screenshots/` (immagini)

---

## Getting Started

### Prerequisiti
- Python 3.12 o superiore
- [uv](https://docs.astral.sh/uv/)
- Account PEC e credenziali
- Facoltativo: certificato di firma digitale (PKCS#12)

### Installazione e configurazione

```bash
git clone https://github.com/gianlucamazza/openfatture.git
cd openfatture
uv sync
cp .env.example .env
```

Compila `.env` con i dati aziendali, PEC e notifiche (riferimento: `docs/CONFIGURATION.md`), poi inizializza il database:

```bash
uv run python -c "from openfatture.storage.database.session import init_db; init_db()"
```

### Prossimi passi
- Segui la guida italiana in `docs/QUICKSTART.md` o la walkthrough inglese in `QUICKSTART.md`.
- Consulta `docs/CLI_REFERENCE.md` per il catalogo completo dei comandi.
- Esplora `docs/PAYMENT_TRACKING.md` per il modulo pagamenti e riconciliazione.

---

## Usage

### CLI

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

fattura = Fattura(...)  # Vedi QUICKSTART per esempi completi
xml_tree = FatturaXMLGenerator(fattura).generate()
TemplatePECSender(settings=get_settings()).send_invoice_to_sdi(
    fattura,
    xml_path="fattura.xml",
    signed=False,
)
```

Altri esempi sono disponibili nella cartella `examples/`.

---

## Documentation
- `docs/README.md` – Indice di navigazione per guide, diagrammi e release
- `docs/CONFIGURATION.md` – Riferimento completo per `.env` e impostazioni
- `docs/AI_ARCHITECTURE.md` – Struttura agenti e integrazioni AI
- `docs/PAYMENT_TRACKING.md` – Flussi di riconciliazione e reminder
- `docs/ARCHITECTURE_DIAGRAMS.md` – Diagrammi Mermaid di sistema

---

## Development
- Installa gli extra di sviluppo e i pre-commit: `uv sync --all-extras` e `uv run pre-commit install`
- Esegui i test: `uv run python -m pytest` (copertura: `uv run python -m pytest --cov=openfatture`)
- Automazioni, CI/CD e media workflow sono descritti in `docs/DEVELOPMENT.md`, `docs/operations/SETUP_CI_CD.md` e nella documentazione correlata

---

## Project Status
- Ultimo rilascio stabile: `docs/releases/v1.0.1.md` (AI Cash Flow Upgrade)
- Roadmap dettagliata e fasi progettuali in `docs/history/ROADMAP.md` e file `docs/history/PHASE_*_SUMMARY.md`
- Focus attuale: orchestrazione AI (Phase 4) e hardening per produzione (Phase 6)

---

## Contributing & License
Contribuzioni benvenute! Leggi `CONTRIBUTING.md` e apri una issue per proposte sostanziali. OpenFatture è distribuito sotto licenza MIT (vedi `LICENSE`).

---

## Support
- Documentazione: `docs/README.md`, guide QUICKSTART e directory `examples/`
- Community: [GitHub Discussions](https://github.com/gianlucamazza/openfatture/discussions)
- Bug & feature request: [GitHub Issues](https://github.com/gianlucamazza/openfatture/issues)
- Email: info@gianlucamazza.it

---

## Disclaimer
Il software è fornito “as-is” per scopi didattici e produttivi. Assicurati la conformità con la normativa fiscale italiana e consulta un commercialista in caso di dubbi.

---

Made with ❤️ by freelancers, for freelancers.
