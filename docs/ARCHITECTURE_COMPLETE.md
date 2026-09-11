# Architecture Complete

**Status:** OpenFatture 2.3.0 (TD04 credit notes + real CLI XML generation)  
**Last updated:** 2026-09-11  
**Purpose:** Comprehensive honest picture of layers, public surface, phased delivery, and remaining product decisions.

Related: [ARCHITECTURE.md](ARCHITECTURE.md), [STATUS.md](STATUS.md), [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md), [CORE_VS_EXTENSIONS.md](CORE_VS_EXTENSIONS.md).

---

## 1. Current layers

OpenFatture is a CLI-first, agentic application for Italian electronic invoicing. Domain operations run through application services; the assistant and CLI are thin adapters.

```
┌─────────────────────────────────────────┐
│   CLI commands + AI assistant tools     │  ← Public surface adapters
├─────────────────────────────────────────┤
│   Application services                  │  ← billing, payment, sdi use-cases
│   (billing, payment, sdi, pdf, …)      │
├─────────────────────────────────────────┤
│   Domain rules + events                 │  ← Models, enums, validation
├─────────────────────────────────────────┤
│   Infrastructure                        │  ← DB, PEC, files, bank importers
│   (storage, email, hooks, platform)    │
└─────────────────────────────────────────┘
```

### Package structure (post-2.0 modernization)

```
openfatture/
  cli/               # Public adapter only; wires to application services
    commands/
      init.py
      config.py
      status.py
      assistant.py
      interactive.py
      fattura.py      # Invoice management CLI (list/show/create/add-line/generate-pdf/xml/set-status)
      cliente.py      # Client management CLI (list/show/create)
  
  platform/          # Config, logging, email, validators, metrics, extras helpers
  storage/           # SQLAlchemy models and sessions
  events/            # Domain events bus and persistence
  hooks/             # Hook registry and executor
  
  billing/           # CORE: clienti, fatture, preventivi, prodotti, batch, fiscale
    application/     # Commands (write) and queries (read)
    clienti/
    fatture/
    preventivi/
    prodotti/
    batch/
    fiscale/
  
  sdi/               # CORE: FatturaPA XML, PEC, notifications, signature
    xml_builder/
    notifications/
    pec/
    signature/
  
  payment/           # CORE: reconciliation and bank import (DDD layers)
    application/
    domain/
    infrastructure/
  
  pdf/               # CORE: human-readable invoice PDFs
  
  ai/                # FEATURE EXTRA [ai]: assistant, tools, providers, RAG, ML
    runtime.py
    tools/
      registry/
      invoice_tools/
      client_tools/
      analytics_tools/
    providers/
    orchestration/
    agents/
    ml/
    rag/
  
  i18n/              # Locale strings (fluent-runtime)
```

### Import rules

1. `cli` may call application services and AI entrypoints only.
2. `ai` tools call application services; they are **not** a second domain layer.
3. Domain packages do not import `cli` or `ai`.
4. `platform` and `storage` do not depend on `ai`.
5. Optional features fail with an explicit install hint when extras are missing.

---

## 2. Real public surface

**Documented in [CLAUDE.md](../CLAUDE.md) and [CLI_REFERENCE.md](CLI_REFERENCE.md):**

### 2.1 Primary agentic surface

- `openfatture init` — First-time setup (config, directories, database)
- `openfatture assistant [MESSAGE]` — Natural language assistant with tool calling
- `openfatture interactive start` — Guided terminal mode with menus
- `openfatture config ...` — Configuration management (show/set/validate)
- `openfatture status` — Read-only migration and system status (supports `--json`)

### 2.2 Direct domain commands (also exist in product)

**These commands provide direct CLI access to domain operations, complementing the assistant-first approach.**

#### `openfatture fattura` — Invoice management

- `list` — Search and list invoices with filters (query/year/status/client)
- `show INVOICE_ID` — Display detailed invoice information
- `create` — Create new draft invoice
- `add-line` — Add line item to invoice
- `generate-pdf` — Generate PDF for invoice (multiple templates)
- `generate-xml` — Generate FatturaPA XML (wired to real XML builder in 2.3.0)
- `create-credit-note` — Create nota di credito (TD04) from existing invoice
- `set-status` — Update invoice status (BOZZA → DA_INVIARE)

#### `openfatture cliente` — Client management

- `list` — Search and list clients
- `show CLIENT_ID` — Display detailed client information
- `create` — Create new client record

**Design rationale:** These commands exist because:
1. They provide deterministic CRUD paths for scripting and automation
2. They complement (not duplicate) assistant workflows for power users
3. They remain thin adapters over application services
4. Complex workflows (SDI transmission, reconciliation, compliance) stay on the assistant

**CLAUDE.md constraint:** Domain operations belong in application services. Do not add another public command for workflows the assistant can express through tools.

### 2.3 Assistant requires `[ai]` extra

When `uv sync --extra ai` (or `--all-extras`) is not performed, `assistant` and `interactive` commands fail with:

```
Error: AI features require the 'ai' extra.
Install with: uv sync --extra ai
```

---

## 3. Core vs extras vs hooks vs extensions

| Layer | Meaning | Install | Examples |
|-------|---------|---------|----------|
| **Core** | Required for Italian e-invoicing | `uv sync` (default) | billing, SDI, payment, PDF, storage, events, hooks engine, platform, CLI |
| **Feature extras** | In-tree, optional deps | `--extra ai/rag/ml/all` | Assistant, RAG, cash-flow forecasting |
| **Hooks** | User automation scripts | Drop files in `~/.openfatture/hooks/` | Slack notify, backup triggers |
| **Extensions** | Future out-of-tree packages | Not yet designed | MCP servers, third-party tool plugins |

**Feature extras details:**

```toml
[project.optional-dependencies]
ai = ["langgraph>=0.6", "openai>=2.4.0", "anthropic>=0.71.0", "tiktoken>=0.8.0"]
rag = ["openfatture[ai]", "chromadb>=0.4.22", "sentence-transformers>=2.6.0", ...]
ml = ["prophet>=1.1.5", "xgboost>=2.1.0", "pandas>=2.3.3", "plotly>=6.3.1", ...]
all = ["openfatture[ai,rag,ml]"]
```

**No in-process plugin API.** The experimental `openfatture.plugins` package was removed in 2.0. User extensions use **hooks** (see [CORE_VS_EXTENSIONS.md](CORE_VS_EXTENSIONS.md)).

---

## 4. Phased roadmap: what is done, what to ship, what is product-decision

### 4.1 Done (2.0 modernization — shipped)

**Release:** 2.0.0–2.0.2 (2026-06/07)  
**Scope:** Architectural reset for AI-first product.

✅ Repo hygiene and living documentation  
✅ Ruff-only tooling (no flake8/black/isort dual stack)  
✅ Optional dependency extras (`ai`, `rag`, `ml`, `all`)  
✅ D0 non-core cut: removed voice, web scraper, orphan analytics agents  
✅ D1 package reorg: `billing`, `events`, `hooks`, `platform`, `pdf` bounded packages  
✅ Core vs extras vs extensions design (hooks supported; plugins removed)  
✅ Honesty gates: Lightning removed (incomplete); RAG auto-update requires explicit callback  
✅ D3 unified `ai.runtime` entry for assistant  
✅ D2: AI tools are thin adapters over application services (not a second domain layer)  
✅ Zero in-code suppressions (`noqa`, `type: ignore`, `pragma: no cover`)  

**See:** [releases/v2.0.0.md](releases/v2.0.0.md), [ARCHITECTURE_REDESIGN.md](ARCHITECTURE_REDESIGN.md).

### 4.2 Done (2.1 LangGraph default — shipped)

**Release:** 2.1.0 (2026-08)  
**Scope:** Flip to LangGraph as default assistant backend; slim ChatAgent to rollback option.

✅ `langgraph_tool_loop` default backend  
✅ ChatAgent slim + `ASSISTANT_BACKEND=chat` rollback path  
✅ Lightning Network module removed entirely (docs archived under `docs/history/lightning/`)  
✅ Dead Lightning i18n keys GC'd from all locales  
✅ Config SSOT: version, backends, AI credentials hydrated consistently (#32)  

**See:** [releases/v2.1.0.md](releases/v2.1.0.md), [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) closed ledger.

### 4.3 Done (2.2 forfettario PDF — shipped)

**Release:** 2.2.0 (2026-08/09, latest on `main`)  
**Scope:** Real Italian forfettario invoice PDF with RF19, natura, cassa, bollo MEF-compliant rendering.

✅ Professional PDF template upgraded to production quality  
✅ RF19 (regime forfettario) as first-class regime with correct natura/IVA rendering  
✅ Natura codes (N2.1, N2.2, N3.1, ...) rendered with labels and totals  
✅ DatiCassaPrevidenziale support in XML builder and PDF  
✅ Bollo virtuale (€2 stamp duty) rendering for invoices >€77.47 without IVA  
✅ CLI commands for invoice/client management (`fattura`, `cliente`) fully wired  
✅ Fix: premature page break for single-row invoices with payment info (#55)  

**See:** [releases/v2.2.0.md](releases/v2.2.0.md), PR #56 (forfettario PDF), PR #53 (FatturaPA natura/cassa).

### 4.4 Done (2.3 nota di credito TD04 — shipped)

**Release:** 2.3.0 (2026-09)  
**Scope:** Real TD04 (nota di credito) support with FatturaPA linkage + real CLI XML generation.

✅ Application service `create_nota_credito_from_fattura(fattura_id, ...)` — loads source invoice, creates TD04 with copied lines (negated amounts), sets FatturaPA linkage  
✅ Fattura model extended with optional linkage fields (`fattura_originale_id`, `fattura_originale_numero`, `fattura_originale_data`)  
✅ XML builder (`_build_dati_generali`) emits `DatiFattureCollegate` when linkage present  
✅ AI invoice tools wired to credit note creation  
✅ CLI command `openfatture fattura create-credit-note --from-invoice INVOICE_ID`  
✅ Integration tests for TD04 XML generation and workflow  
✅ PDF renders TD04 document type label (via `tipo_documento.value`)  
✅ `openfatture fattura generate-xml` now actually generates FatturaPA XML (no longer a stub; wired to `InvoiceService.generate_xml()` and real builder)  
✅ CLI generate-xml honors `--output` and `--dry-run` flags  
✅ Comprehensive test coverage for XML generation (normal, custom output, dry-run, error handling)  

**See:** [releases/v2.3.0.md](releases/v2.3.0.md), PR #57 (TD04), PR #58 (Alembic migration 8cf82bd24752).

### 4.5 Experimental (not on public CLI by design)

**Location:** `openfatture/ai/orchestration/workflows/`

- `invoice_creation.py` — Multi-agent invoice creation workflow
- `compliance_check.py` — Compliance orchestration
- `cash_flow_analysis.py` — Cash flow workflow

**Current state:**
- ✅ Implemented under GraphAssistantBackend
- ✅ Config flag: `enable multi-agent orchestration (experimental)` in AI settings
- ⚠️ **Not** exposed on public CLI (intentional)
- ⚠️ No invented human decisions; honest awaiting-approval gates only

**Product path:** Remains experimental until explicit product decision to ship multi-agent UX. See [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) D-WF #38.

### 4.6 Product decisions (blocked / not code yet)

**These require explicit product and release plan; do not implement until decided:**

| Decision | GitHub | Default stance |
|----------|--------|----------------|
| Multi-agent workflows on public path | [#38](https://github.com/gianlucamazza/openfatture/issues/38) | Off / experimental only |
| Textual TUI or other rich TUI | [#44](https://github.com/gianlucamazza/openfatture/issues/44) | Non-goal; interactive terminal exists |
| MCP server / external tool bus | [#44](https://github.com/gianlucamazza/openfatture/issues/44) | Non-goal until designed; hooks + tool contracts today |
| Browser / web app surface | [#44](https://github.com/gianlucamazza/openfatture/issues/44) | Explicit non-goal (see STATUS.md) |
| Domain CLI command tree growth | N/A | **Forbidden** per CLAUDE.md; domain ops stay on assistant + app layer |

**See:** [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) § Product decisions, [STATUS.md](STATUS.md) § Explicit non-goals.

### 4.7 On-demand technical debt (not blocking releases)

All debt has explicit **trigger** conditions (when to act) and GitHub issues. Do not drive standalone "code cleanup" PRs; burn debt when editing the affected module.

**Summary of open debt:**

- **D-SIZE** (#37, P1–P3): Oversized modules (700–1091 LOC); split **when editing them**
- **D-WF** (#38): Experimental workflows; act only with product decision
- **D-ML-DRIFT** (#39): Accuracy-drift signal not implemented; trigger: when production ML monitoring required
- **D-OBS** (#40): Bulkhead queue length approximate; trigger: if dashboards need accurate depth
- **D-PDF-PAGOPA** (#41): pagoPA QR not implemented; trigger: customer need for QR on PDFs
- **D-TYPES-TESTS** (#42): mypy does not type-check `tests.*`; trigger: optional incremental enable
- **D-ASYNC** (#43): Nested event-loop bridge; trigger: only if interactive hosts hit real nested failures

**See:** [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) for full inventory, triggers, and non-goals.

---

## 5. First-class PDF + XML concerns

**Current product supports (as of 2.2.0):**

### 5.1 Regime fiscale

All Italian tax regimes (`RegimeFiscale` enum):

- **RF01** — Ordinario
- **RF19** — Regime forfettario (full PDF rendering support added in 2.2.0)
- RF02–RF18, RF19+ — All other regimes supported in XML builder; PDF renders correctly

### 5.2 Natura codes (zero-rated / exempt / out-of-scope VAT)

Supported in `RigaFattura` model and FatturaPA XML builder:

- **N2.1** — Non soggette ad IVA ex art. 15
- **N2.2** — Non soggette – altri casi
- **N3.1** — Non imponibili – esportazioni
- **N3.2** — Non imponibili – cessioni intracomunitarie
- **N3.3** — Non imponibili – cessioni verso San Marino
- **N3.4** — Non imponibili – operazioni assimilate
- **N3.5** — Non imponibili – seguito di dichiarazioni d'intento
- **N3.6** — Non imponibili – altre operazioni
- **N4** — Esenti
- **N5** — Regime del margine / IVA non esposta
- **N6** — Inversione contabile (reverse charge)
- **N7** — IVA assolta in altro Stato UE

**Implementation:** `_build_dati_beni_servizi` in `sdi/xml_builder/fatturapa.py`; PDF natura labels in `pdf/generator.py`.

### 5.3 DatiCassaPrevidenziale (social security contributions)

**Model:** `DatiCassaPrevidenziale` (relationship to `Fattura`)  
**Fields:** `tipo_cassa`, `al_cassa`, `importo_contributo_cassa`, `imponibile_cassa`, `aliquota_iva`, `ritenuta`, `natura`, `riferimento_amministrazione`

**XML builder support:** `_build_dati_generali` in `fatturapa.py` (added in 2.2.0 / PR #53)  
**PDF support:** Cassa line items rendered in professional template (2.2.0)

**Common cassa types:**
- **TC01** — Cassa Nazionale Previdenza e Assistenza Avvocati (CNPA)
- **TC02** — Cassa Previdenza Dottori Commercialisti (CNPADC)
- **TC03** — Cassa Previdenza e Assistenza Geometri (CIPAG)
- **TC04** — Cassa Nazionale Previdenza e Assistenza Ingegneri e Architetti (INARCASSA)
- **TC05** — Cassa Nazionale del Notariato (CNN)
- **TC06** — Cassa Nazionale Previdenza e Assistenza Ragionieri e Periti Commerciali (CNPR)
- **TC07** — ENPACL (Consulenti del Lavoro)
- ... (22 total)

### 5.4 Ritenuta d'acconto (withholding tax)

**Model fields:** `Fattura.ritenuta_acconto`, `Fattura.aliquota_ritenuta`  
**XML builder:** `DatiRitenuta` section in `_build_dati_generali`  
**PDF:** Rendered as deduction from total in payment section

**Common rates:**
- **20%** — Prestazioni lavoro autonomo (most freelancers)
- **23%** — Provvigioni

### 5.5 Bollo virtuale (stamp duty)

**Model field:** `Fattura.importo_bollo`  
**XML builder:** `DatiBollo` section with `BolloVirtuale=SI`  
**PDF:** Rendered as separate line in totals section (2.2.0)

**MEF requirement:** €2.00 stamp duty for invoices >€77.47 without IVA.

### 5.6 TipoDocumento support

**Currently supported in product:**

- ✅ **TD01** — Fattura (ordinary invoice) — full support
- ✅ **TD04** — Nota di credito (credit note) — full support with `DatiFattureCollegate` linkage (shipped in 2.3.0)
- ✅ **TD06** — Parcella (professional fee invoice) — full support
- ⚠️ TD02, TD03, TD05, TD16–TD27 — Enum values exist; XML builder may work; **not tested in production**

---

## 6. SDI / PEC transport readiness

**Status:** PEC integration and SDI notification parsing are production-ready.

**Covered in dedicated doc:** [SDI_TRANSPORT_READINESS.md](SDI_TRANSPORT_READINESS.md)

**Summary:**

- ✅ FatturaPA XML v1.9 generation with validation
- ✅ Digital signature (PKCS#12, CAdES/P7M) with certificate checks
- ✅ PEC integration (rate limiting, retries, templated emails, attachments)
- ✅ SDI notification parser (AT, RC, NS, MC, NE) with automatic status updates
- ⚠️ Batch operations functional; performance optimization on-demand (D-SIZE triggers)
- ⚠️ Real SDI testing requires production PEC credentials (see STATUS.md)

---

## 7. Coverage and quality gates

**CI gates (defined in `pyproject.toml` + `.github/workflows/test.yml`):**

```toml
[tool.coverage.report]
fail_under = 49  # Package-wide floor (prevents large regressions)
```

**Payment module floor:** 75% (measured ~78% in dedicated job)

**Local default:** `pytest` runs **without** coverage (faster). Use `--cov=openfatture` for reports.

**Mypy:** Type-checks `openfatture/` (production code). `tests/` excluded (D-TYPES-TESTS #42 — optional incremental enable).

**Linters:** Ruff only (no flake8/black/isort). Zero in-code suppressions.

**See:** [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) D-COV, [STATUS.md](STATUS.md) § Quality expectations.

---

## 8. Versioning and release cadence

**Current version:** 2.2.0 (2026-09-11)

**Version scheme:** `MAJOR.MINOR.PATCH`

- **MAJOR** — Breaking changes to public CLI or core models (rare)
- **MINOR** — New features, non-breaking API additions, dependency updates
- **PATCH** — Bug fixes, documentation updates, performance improvements

**Release tags:** `v2.0.0`, `v2.1.0`, `v2.2.0`, ...

**Changelog:** [CHANGELOG.md](../CHANGELOG.md) with user-facing release notes

**Release process:**
1. Update version in `openfatture/__about__.py` (single source of truth)
2. Update [CHANGELOG.md](../CHANGELOG.md) with release notes
3. Create release notes doc under `docs/releases/vX.Y.Z.md`
4. Tag release: `git tag vX.Y.Z && git push origin vX.Y.Z`
5. PyPI publish (manual or CI automation — not yet automated)

**See:** [releases/](releases/) directory for historical release notes.

---

## 9. Summary: what you get in 2.2.0

✅ **Core invoicing:** CRUD for clients/invoices, line items, batch operations  
✅ **FatturaPA XML:** v1.9 compliant, all regimes, natura codes, cassa, ritenuta, bollo  
✅ **PDF generation:** Professional/minimalist/branded templates with forfettario support  
✅ **SDI/PEC:** Ready for production with real credentials  
✅ **Payment reconciliation:** Bank import (CSV/OFX), matching engine, ledger  
✅ **AI assistant** (`[ai]` extra): Natural language tools, LangGraph orchestration, RAG optional  
✅ **Hooks:** User automation scripts via event bus  
✅ **CLI + interactive mode:** Deterministic commands + guided TUI  

⚠️ **Experimental:** Multi-agent workflows (off public path)  
⚠️ **On-demand:** Oversized module splits, pagoPA QR, accuracy-drift monitoring  
❌ **Explicit non-goals:** Web app, in-process plugins, duplicate CLI command trees  

**Next likely feature (this branch):** Real nota di credito with FatturaPA linkage.

---

## 10. Contributing and design constraints

**Read first:**

- [CLAUDE.md](../CLAUDE.md) — Contributor guide with design rules
- [CONTRIBUTING.md](../CONTRIBUTING.md) — Workflow and PR guidelines
- [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) — Honest debt inventory with triggers

**Key constraints from CLAUDE.md:**

1. Do not add another public command for workflows the assistant can express through tools.
2. Prefer explicit, typed interfaces and small modules.
3. Keep startup read-only; setup happens only through `init`.
4. Keep `status` read-only and machine-readable with `--json`.
5. Route business actions through the assistant and domain tools.
6. Do not add aliases, deprecated command paths, compatibility shims, or duplicate implementations.
7. Update CLI reference and tests when public surface changes.

**Historical material:** Anything under `docs/history/` is **not** current CLI behavior.

---

**Questions or additions:** See [docs/README.md](README.md) for documentation index or file GitHub issues.
