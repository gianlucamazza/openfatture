# Technical Debt Inventory

Honest inventory of **open** and **closed** debt after modernization **2.0**,
the **2.1.0** LangGraph default flip, post-2.1 hygiene (#31–#34) and the
**2.6.0–2.8.0** architecture review.

**Last updated:** 2026-11-10  
**Version baseline:** 2.8.2 (`v2.8.2`) · analysis: [docs/reports/technical-debt-analysis-2026-11.md](reports/technical-debt-analysis-2026-11.md)

Related: [STATUS.md](STATUS.md), [CORE_VS_EXTENSIONS.md](CORE_VS_EXTENSIONS.md),
[ARCHITECTURE.md](ARCHITECTURE.md), [releases/v2.1.0.md](releases/v2.1.0.md).

### GitHub tracking

| Role | Link |
|------|------|
| Umbrella | [#36 tracker](https://github.com/gianlucamazza/openfatture/issues/36) |
| Milestone | [Post-2.1 backlog (on-demand)](https://github.com/gianlucamazza/openfatture/milestone/1) |
| Labels | `technical-debt`, `product-decision`, `on-demand`, `priority:p1`–`p3` |

| ID | Issue | Priority |
|----|-------|----------|
| D-SIZE | [#37](https://github.com/gianlucamazza/openfatture/issues/37) | P1 |
| D-OBS | [#40](https://github.com/gianlucamazza/openfatture/issues/40) | P3 |
| D-PDF-PAGOPA | [#41](https://github.com/gianlucamazza/openfatture/issues/41) | P2 |
| D-TYPES-TESTS | [#42](https://github.com/gianlucamazza/openfatture/issues/42) | P3 |
| D-ASYNC | [#43](https://github.com/gianlucamazza/openfatture/issues/43) | P3 |
| D-COV | *(acceptable — no issue; baseline floors only)* | — |
| Product surfaces (TUI/MCP/web) | [#44](https://github.com/gianlucamazza/openfatture/issues/44) | decision |

Close the matching issue and move the row to the closed ledger when debt is burned.

---

## Verdict

| Signal | State |
|--------|--------|
| Structural modernization (2.0) | **Done** |
| AI product backend (LangGraph default) | **Done** (2.1.0) |
| Packaging / CLI surface / suppressions | **Clean** |
| Real remaining debt | **Oversized modules** (split when touched) |
| Blocking release debt | **None** |

Remaining work is **maintenance when touched** or **product decisions**, not
firefighting. Do not invent new public domain CLI commands to “finish” debt.

---

## Debt level by area

| Area | Level | Notes |
|------|-------|--------|
| Public CLI surface | Low | Assistant (`openfatture`, `assistant`), `init`, `config`, `status`, plus documented `cliente` / `fattura` / `pagamento` adapters |
| Core billing / SDI / payment | Low | Tools → application services; payment suite floor 75% |
| Package layout | Low | Bounded packages; no empty placeholders; extras explicit |
| Config / SSOT | Low | Version, backends, AI credentials hydrated consistently (#32) |
| AI runtime (product path) | Low | Default `langgraph_tool_loop`; single tool-loop; ChatAgent slim rollback |
| Module size / cohesion | Medium | A few files >700 LOC; split only when editing them |
| Lightning | **Removed** | Incomplete LND gRPC; archive under `docs/history/lightning/` |
| RAG auto-update | Low | Real `reindex_callback` required; default auto-update off |
| Tooling / types | Low | Zero in-code `noqa` / `type: ignore` / `pragma: no cover` |
| Tests | Low | Skips are for extras, external services, or intentional env limits |
| Coverage floors | Acceptable | Package 78% (measured 81%); payment 75% |

---

## Closed (do not re-open)

Keep this ledger so old debt is not rediscovered as open.

| Item | Resolved in | Notes |
|------|-------------|--------|
| Repo hygiene + living docs | 2.0 | Canonical docs; history under `docs/history/` |
| Ruff-only tooling | 2.0 | No flake8/black/isort dual stack |
| Optional dependency extras | 2.0 | `ai` / `rag` / `all` (`ml` removed in 2.8.0) |
| D0 non-core cut | 2.0 | Voice, scraper, orphan agents out of product path |
| D1 package reorg | 2.0 | `billing` / `events` / `hooks` / `platform` / `pdf` |
| Experimental `plugins` package | 2.0 | Removed; hooks + future MCP contracts |
| AI tools → application adapters | 2.0 | Thin tools over use-cases |
| Unified `ai.runtime` entry | 2.0 | Assistant entry is runtime-owned |
| RAG queue honesty | 2.0 | No silent no-op reindex |
| LangGraph product opt-in | 2.0.x (#29) | Backend available behind config |
| LangGraph **default** + ChatAgent slim | **2.1.0** (#30) | One tool-loop; chat is rollback |
| Dependabot / Ruff 0.16 readiness | #28 | CI dependency batch |
| Project config hygiene | #31 | Post-2.1 config cleanup |
| SSOT: version, backends, AI credentials | #32 | Single sources; hydrate rules tested |
| Lightning Network module | #33 | Removed from tree; docs archived |
| Dead Lightning i18n keys | #34 | GC’d from all `cli.ftl` locales |
| Redundant payment-only lint job | #34 | Package-wide `lint` in `test.yml` covers it |
| Lexicographic invoice numbering | 2.6.0 | Single `next_numero`; unique `(numero, anno)` index |
| Two Alembic heads | 2.6.0 | `20261110_merge` reunites `dda5c6e9a600` |
| Payment events never delivered | 2.6.0 | `PaymentEvent` extends `BaseEvent`; parallel bus removed |
| Application layer importing `cli` / payment importing `ai` | 2.6.0 | Enforced by `tests/test_import_rules.py` |
| Tool registration swallowing ImportError | 2.6.0 | Broken tool modules fail loudly |
| Model-chosen export paths | 2.6.0 | Confined to `data_dir/exports` |
| CLI data commands querying ORM | 2.6.0 | Routed through application services |
| Unused payment AI insight chain, `ai.context`, `InvoiceBatchProcessor` | 2.6.0 | Removed |
| D-WF experimental multi-agent workflows (#38), incl. direct DB writes | 2.8.0 | Removed with their agents and states |
| D-ML-DRIFT / ML stack (#39) | 2.8.0 | `ai.ml`, cash-flow predictor, feedback and the `ml` extra removed |
| D-SCHEMA Alembic not shipped, `create_all` drift | 2.8.0 | Packaged migrations; `storage.schema` creates, refuses, upgrades, adopts |
| D-PEC two PEC senders | 2.8.0 | Only `sdi.email.TemplatePECSender`; `platform` no longer imports domains |
| D-SESSION hand-managed sessions | 2.8.0 | `db_session()` / `session_scope()` everywhere |
| D-I18N orphan keys, incomplete locales | 2.8.0 | Only referenced ids; all locales complete; enforced by tests |
| Knowledge base never indexed, CWD-relative paths | 2.8.0 | Packaged KB, indexed on first use; vector store in data_dir |
| Correlation IDs never set | 2.8.0 | One per CLI invocation |
| Unrounded VAT and drifting totals | 2.8.2 | `billing.application.totals`, half-up, per-rate VAT |
| Unvalidated/stale XML on send; signed send attached unsigned XML | 2.8.2 | Always validated; `.p7m` stored and checked against current data |
| CSV import lost all rows after one failure | 2.8.2 | Savepoint per row |
| Unsafe XML parsing of SDI notifications | 2.8.2 | `sdi.safe_xml` |
| Raw exceptions returned to the assistant | 2.8.2 | `platform.errors.describe_error` |
| Unused deps, advisory-only security CI, 49% coverage floor | 2.8.2 | deptry/pip-audit/bandit blocking; floor 78% |

---

## Open debt

Each item has an **ID**, **impact**, **trigger** (when to act), and **non-goal**
if relevant. Prefer fixing debt in the same PR that touches the module.

### D-SIZE — Oversized modules

**GitHub:** [#37](https://github.com/gianlucamazza/openfatture/issues/37)  
**Impact:** Harder review, higher merge conflict risk, mixed concerns.  
**Risk to users:** Low until bugs land in these files.  
**Trigger:** Split **when you edit** them for a real feature/bug; do not drive
standalone “LOC reduction” PRs.

| Module | ~LOC | Suggested split direction | Priority |
|--------|------|---------------------------|----------|
| `storage/database/models.py` | ~840 | Models by bounded context (billing / payment / events / SDI) | P2 |
| `ai/tools/registry/core.py` | ~810 | Extract bulkhead/circuit-breaker and metrics | P3 |
| `pdf/templates/base.py` | ~770 | Summary/table drawing helpers | P3 |
| `billing/application/invoice_commands.py` | ~680 | Invoice vs line commands | P2 |
| `ai/tools/invoice_tools/__init__.py` | ~660 | One module per tool group | P3 |
| `ai/orchestration/react.py` | ~630 | Keep unless ReAct path expands | P3 |
| `ai/providers/openai.py` | ~630 | Client vs streaming vs tool-call mapping | P3 |
| `billing/application/preventivo_ops.py` | ~540 | Ops vs PDF/email side paths | P2 |

**Done nearby:** `chat_agent.py` slimmed (structured + graph delegation);
`ai.tools.registry` is already a package.

### D-CLI-I18N — Hard-coded CLI strings

**Location:** `cli/commands/fattura.py` (69), `init.py` (26), `cliente.py` (19).  
**Impact:** Mixed Italian/English output; non-Italian locales see untranslated text.  
**Trigger:** Next change to these commands; move strings to `cli.ftl` (the i18n
test then enforces every locale).

### D-ERRORS — Three error contracts

**Behavior:** Application services return `{"error": ...}`, the XML path raises
`XMLValidationError`, tools wrap results in `ToolResult`. 54 broad `except`
blocks only log; the reviewed ones isolate post-commit side effects
(events, notification emails).  
**Trigger:** A new caller that needs typed errors; unify at the tool boundary.

### D-XML-TOTAL — `ImportoTotaleDocumento` not emitted

Optional in FatturaPA; some customer tools expect it. Add when the bollo and
cassa contributions are folded into the document total rules.

### D-OBS — Bulkhead queue length is approximate

**GitHub:** [#40](https://github.com/gianlucamazza/openfatture/issues/40)  
**Location:** `ai/tools/registry/core.py` (+ `ToolResult.bulkhead_queue_length`)  
**Behavior:** Derived from semaphore `_value` / max concurrent, not a real wait-queue depth.  
**Impact:** Observability only; concurrency limiting still works.  
**Trigger:** If tool-resilience dashboards need accurate queue depth.

### D-PDF-PAGOPA — pagoPA QR not implemented

**GitHub:** [#41](https://github.com/gianlucamazza/openfatture/issues/41)  
**Location:** `pdf/generator.py` (`pagopa_qr_not_implemented` warning)  
**Impact:** PDF generation continues without QR when that path is requested.  
**Trigger:** Customer need for pagoPA QR on generated PDFs.

### D-TYPES-TESTS — mypy does not type-check `tests.*`

**GitHub:** [#42](https://github.com/gianlucamazza/openfatture/issues/42)  
**Location:** `pyproject.toml` mypy config  
**Impact:** Test-only type bugs slip until runtime.  
**Trigger:** Optional incremental enable for critical test packages.  
**Not debt:** third-party `ignore_missing_imports` for packages without stubs.

### D-COV — Global coverage floor is a baseline, not a goal

| Suite | Floor | Source |
|-------|-------|--------|
| Full package | 78% | `[tool.coverage.report] fail_under` + `test.yml` |
| Payment | 75% | `payment-tests.yml` (~78% measured) |

**Impact:** Prevents large regressions; does not drive quality by itself.  
**Trigger:** Raise floors only when a suite sustainably exceeds them.  
**Local default:** pytest without coverage (speed); use CI flags for reports.

### D-ASYNC — Nested event-loop bridge

**GitHub:** [#43](https://github.com/gianlucamazza/openfatture/issues/43)  
**Location:** platform async bridge (`nest_asyncio` optional, else worker thread;
primary path `asyncio.run`).  
**Impact:** Edge cases in nested loops / notebook-like hosts.  
**Trigger:** Only if interactive/assistant hosts hit real nested-loop failures.

---

## Product decisions (not code debt yet)

These need a **product decision and release plan** before implementation.
Documenting them here prevents them from being treated as silent backlog bugs.

| Decision | Default stance | Notes |
|----------|----------------|--------|
| Textual (or other) TUI | Non-goal | [#44](https://github.com/gianlucamazza/openfatture/issues/44); interactive terminal exists |
| MCP server / external tool bus | Non-goal until designed | [#44](https://github.com/gianlucamazza/openfatture/issues/44); hooks + tool contracts today |
| Browser / web app surface | Explicit non-goal | [#44](https://github.com/gianlucamazza/openfatture/issues/44); see STATUS |
| Domain CLI command tree growth | Forbidden | Only `cliente` / `fattura` / `pagamento` exist, as adapters over application services |
| Lightning / LND payments | Removed | Archive only; reintroduce only as greenfield design |

---

## Acceptable / intentional (not debt)

| Item | Why acceptable |
|------|----------------|
| `except Exception` in hooks / events / email | Isolation of untrusted or peripheral code |
| Test skips for missing extras / external services | Correct for CI and optional installs |
| Ruff global ignore `E501` | Line length owned by `ruff format` |
| `tests/**` E402 per-file ignore | Path setup before SUT import |
| `__init__.py` F401 per-file ignore | Public re-export barrels |
| Interactive / TTY-only test skips | Cannot assert full UX headlessly |
| SQLite in-memory concurrency skips | Known engine limit, not app bug |

---

## Recommended burn-down order

Act only with a real trigger. Order is **cost/benefit**, not a sprint backlog.

1. **D-SIZE P2** — `models.py` / `invoice_commands` / `preventivo_ops` when billing storage changes  
2. **D-OBS / D-PDF-PAGOPA / D-TYPES-TESTS / D-ASYNC** — opportunistic  
3. **Product decisions** (TUI / MCP / web) — separate design + release, not drive-by PRs  

---

## How to keep this document honest

- Update **Last updated** and the closed ledger when debt is removed or accepted.  
- Prefer **IDs** (`D-SIZE`, `D-WF`, …) in PR descriptions when intentionally
  burning debt.  
- Do not list “nice to have” refactors without a trigger.  
- Historical investigation reports live under `docs/history/` and
  `docs/reports/` — they are **not** current claims.  
- In-code suppressions remain **forbidden**; fix the root cause instead.
