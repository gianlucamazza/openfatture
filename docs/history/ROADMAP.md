# OpenFatture Development Roadmap

**Last Updated:** October 10, 2025
**Current Version:** 1.0.0
**Project Status:** Phases 1-5 complete (v1.0.0). Phase 4 advanced items still in progress, Phase 6 planning underway.

---

## Project Vision

Build a modern, open-source invoicing platform for Italian freelancers that combines:
- Full compliance with FatturaPA and SDI guidelines.
- CLI-first workflows with an interactive TUI.
- AI-assisted automation for day-to-day accounting tasks.
- Production-ready, extensible architecture.

---

## Development Phases

### ✅ Phase 1 – Core Foundation (Completed)

**Status:** 100% complete • **Completion:** October 2025 • **Coverage:** 81%

Key achievements:
- Modern tooling (Python 3.12+, uv, pre-commit).
- Domain models for Cliente, Fattura, LineaFattura and related services.
- SQLAlchemy ORM with initial migrations and fixtures.
- Pydantic-based configuration system with `.env` support.
- pytest infrastructure, structured logging, correlation IDs.

📄 Approfondimenti: `PHASE_1_SUMMARY.md`

---

### ✅ Phase 2 – SDI Integration (Completed)

**Status:** 100% complete • **Completion:** October 2025 • **Coverage:** 80%

Key achievements:
- FatturaPA XML v1.9 generator with validation against official schemas.
- Digital signature pipeline (PKCS#12, CAdES/P7M) with certificate checks.
- PEC integration (rate limiting, retries, templated emails, attachments).
- SDI notification parser for AT, RC, NS, MC, NE with automatic status updates.
- Batch operations (CSV import/export, bulk PEC sending) with progress tracking.
- Full email templating system (Jinja2, IT/EN internationalisation).

📄 Approfondimenti: `PHASE_2_SUMMARY.md`

---

### ✅ Phase 3 – CLI & User Experience (Completed)

**Status:** 100% complete
CLI-first experience now available both as scripted commands and interactive TUI.

Highlights:
- Typer command tree (init, config, cliente, fattura, pec, email, notifiche, batch, report, ai, payment, interactive).
- Questionary/Rich-powered menus with fuzzy search, shortcuts, progress bars.
- Autocomplete helpers for provinces, codici SDI, nature VAT, service descriptions.
- `openfatture --install-completion` for bash/zsh/fish shell completions.
- PDF generation for human-readable invoices (`openfatture fattura pdf`) with three templates (Minimalist, Professional, Branded) conforming to PDF/A-3.
- Enhanced dashboard in interactive mode with AI chat integration.

✅ Remaining UX improvements (filtering widgets, live metrics) are tracked as backlog items for Phase 6.

---

### 🚧 Phase 4 – AI Layer (In Progress ~70%)

**Goal:** Transform AI stubs into production-grade agents.

✅ Delivered:
- Provider abstraction (OpenAI, Anthropic, Ollama) with streaming, token counting, cost tracking and configurable caching.
- Functional agents: InvoiceAssistant (`ai describe`), TaxAdvisor (`ai suggest-vat`), ChatAssistant (interactive chat with tool calling).
- Tool registry with six production tools for invoices/client search and analytics.
- Session persistence with export (JSON/Markdown) and cost telemetry.
- RAG subsystem (ChromaDB backing store) with CLI management (`ai rag status/index/search`) and automated snippet injection in Chat/Tax flows.
- PaymentInsightAgent for causale analysis during reconciliation.
- Cash Flow Predictor (`ai forecast`) – Prophet + XGBoost ensemble con artefatti persistenti, metriche salvate e comando `--retrain`.

🚧 Pending for Phase 4.3-4.4:
- Compliance Checker (`ai check`) – SDI preflight checks with severity/mitigation hints.
- LangGraph-powered multi-agent workflows (invoice → tax → compliance orchestration).
- Provider-level rate limiting, semantic caching fallback, advanced cost analytics.
- Full integration tests against local Ollama (CI) and property-based tests for prompts.

---

### ✅ Phase 5 – Payment Module & Bank Reconciliation (Completed)

**Released with v1.0.0**

Highlights:
- `openfatture.payment` module with DDD/hexagonal architecture (domain aggregates, services, repositories).
- Multi-format bank importers (CSV presets, OFX, QIF) with deduplication and preset management.
- Matching engine with composite strategies (exact, fuzzy, IBAN, date window) and confidence scoring.
- Ledger for partial allocations plus transaction lifecycle management (UNMATCHED → MATCHED → IGNORED).
- Payment reminders with configurable strategies (DEFAULT, PROGRESSIVE, AGGRESSIVE, CUSTOM) and multi-channel notifications (email/SMS/webhook).
- CLI toolset (`openfatture payment ...`) for import, review, reconciliation, reminders.
- Unified payment due insights across CLI (`report scadenze`) and TUI dashboard.

📈 Quality: 74 dedicated tests for the payment module, bringing overall coverage above 85%.

---

### 🚀 Phase 6 – Production & Advanced Capabilities (Planned)

**Focus areas for 2026:**
- **Production deployment:** hardened Docker images, health checks, observability stack, backup/disaster recovery automation.
- **CI/CD:** release automation, PyPI publishing, staging smoke tests, rollback workflows.
- **Accounting integrations:** accountant-friendly exports (CSV/XLSX/XML), connectors to third-party software, payment gateway integrations.
- **Web experience:** optional FastAPI backend + SPA frontend with realtime updates.
- **Performance & scale:** query optimisation, caching (Redis), load testing, multi-tenant support.
- **Compliance:** GDPR audit, long-term preservation strategy, security hardening.

---

## Known Placeholders & Follow-Ups

| Area | File | Status | Notes |
|------|------|--------|-------|
| Cash flow forecasting CLI | `openfatture/cli/commands/ai.py` | ⏳ Stub | `openfatture ai forecast` prints placeholder; awaiting Phase 4.3 model. |
| Compliance checker CLI | `openfatture/cli/commands/ai.py` | ⏳ Stub | `openfatture ai check` returns placeholder response; agent under development. |
| LangGraph orchestration | `openfatture/ai/orchestration/*` | ⏳ Scaffold | Workflow states defined, execution still to be wired into UI/CLI. |

---

## Dependency Outlook

- ✅ **ChromaDB** – in production for RAG indexing/search.
- ✅ **ReportLab** – used for PDF invoice generation.
- ⏳ **LangGraph** – installed, to be activated with multi-agent workflows in Phase 4.4.

---

## Release Schedule

| Version | Status | Focus |
|---------|--------|-------|
| **v1.0.0** (Oct 2025) | ✅ Released | Payment module, documentation consolidation, AI refresh. |
| **v1.0.1** (Q4 2025) | Planned | Bug fixes, due-date reporting, documentation polish. |
| **v1.1.0** (Q1 2026) | Planned | AI cash flow & compliance agents, LangGraph orchestration. |
| **v1.2.0** (2026) | Planned | Production deployments, accountant exports, performance tuning. |

---

## 🗺️ Next Release (v1.0.2 Preview)
- **Payment CLI parity** – implementare i comandi mancanti (account, reconcile, reminder management). Dettagli in `docs/history/NEXT_RELEASE_PLAN.md`.
- **Coverage uplift** – alzare la soglia CI a ≥60% e stimare roadmap verso l'85%.
- **Doc & UX alignment** – aggiornare `docs/CLI_REFERENCE.md`, completare esempi CLI e sincronizzare la dashboard interattiva con i nuovi comandi.

---

## Success Criteria & Metrics

- **Compliance:** Keep FatturaPA/SDI compatibility up to date (audited each release).
- **Quality:** Incrementare la copertura (gate CI ≥60% in v1.0.2, obiettivo 85% a medio termine); ampliare i test quando arrivano nuovi moduli.
- **AI adoption:** ≥60% of active users leverage AI features; monitor cost per AI-assisted invoice (<€0.10 target).
- **Payments:** ≥95% reconciliation accuracy per banca supportata con reminder affidabili.
- **Documentation:** Update `docs/README.md`, release notes, and roadmap at every tagged release.

---

## Contributing to the Roadmap

1. Upvote or propose features in GitHub Discussions.
2. File issues with concrete use cases, especially for production deployments and AI enhancements.
3. Join roadmap milestones in the issue tracker; see `CONTRIBUTING.md` for workflow guidelines.

### High-Impact Contribution Areas
- AI agent evolution (cash flow, compliance).
- Payment analytics and reporting (due dates, cash flow dashboards).
- Internationalisation and localisation (beyond IT/EN).
- Accountant tooling and third-party integrations.
- Web/TUI experience polish and accessibility.

---

## Maintenance & Risk Management

- **Active Work:** AI Phase 4 enhancements, payment reporting bridges, documentation polish.
- **Maintenance Mode:** Phases 1-3 – focus on bug fixes and compliance updates.
- **Risks:** Provider API changes, SDI specification updates, AI cost volatility. Mitigations: multi-provider support, schema auto-downloads, local models, proactive monitoring.

---

**Next review:** align with each minor release or when a phase completes. For historical context, consult `PHASE_*_SUMMARY.md` documents.
