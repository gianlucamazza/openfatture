# Technical Debt Inventory

Honest inventory of **open** and **closed** debt after modernization **2.0**,
the **2.1.0** LangGraph default flip, and post-2.1 hygiene (#31–#34).

**Last updated:** 2026-08-08  
**Version baseline:** 2.1.0 (`v2.1.0`)

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
| D-WF | [#38](https://github.com/gianlucamazza/openfatture/issues/38) | P2 + product |
| D-ML-DRIFT | [#39](https://github.com/gianlucamazza/openfatture/issues/39) | P2 |
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
| Real remaining debt | **Oversized modules** + **experimental workflows** (not on CLI) |
| Blocking release debt | **None** |

Remaining work is **maintenance when touched** or **product decisions**, not
firefighting. Do not invent new public domain CLI commands to “finish” debt.

---

## Debt level by area

| Area | Level | Notes |
|------|-------|--------|
| Public CLI surface | Low | Agentic surface only: `init`, `assistant`, `interactive`, `config`, `status` |
| Core billing / SDI / payment | Low | Tools → application services; payment suite floor 75% |
| Package layout | Low | Bounded packages; no empty placeholders; extras explicit |
| Config / SSOT | Low | Version, backends, AI credentials hydrated consistently (#32) |
| AI runtime (product path) | Low | Default `langgraph_tool_loop`; single tool-loop; ChatAgent slim rollback |
| Multi-agent workflows | Medium | Present under `ai.orchestration.workflows.*`; **not** on public CLI |
| Module size / cohesion | Medium | A few files >700 LOC; split only when editing them |
| Lightning | **Removed** | Incomplete LND gRPC; archive under `docs/history/lightning/` |
| RAG auto-update | Low | Real `reindex_callback` required; default auto-update off |
| Tooling / types | Low | Zero in-code `noqa` / `type: ignore` / `pragma: no cover` |
| Tests | Low | Skips are for extras, external services, or intentional env limits |
| Coverage floors | Acceptable | Package 49%; payment 75% (measured ~78%) |

---

## Closed (do not re-open)

Keep this ledger so old debt is not rediscovered as open.

| Item | Resolved in | Notes |
|------|-------------|--------|
| Repo hygiene + living docs | 2.0 | Canonical docs; history under `docs/history/` |
| Ruff-only tooling | 2.0 | No flake8/black/isort dual stack |
| Optional dependency extras | 2.0 | `ai` / `rag` / `ml` / `all` |
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
| `ai/agents/cash_flow_predictor.py` | ~1091 | Predictor vs features vs report/IO | P1 |
| `ai/orchestration/workflows/invoice_creation.py` | ~921 | Nodes / gates / IO (only if productized) | P2* |
| `ai/providers/openai.py` | ~855 | Client vs streaming vs tool-call mapping | P2 |
| `ai/tools/registry/core.py` | ~718 | Already a package; further extract bulkhead/metrics if grows | P3 |
| `billing/application/invoice_commands.py` | ~714 | Commands vs validation vs side-effects | P2 |
| `storage/database/models.py` | ~672 | Models by bounded context (billing / payment / events) | P2 |
| `ai/orchestration/react.py` | ~633 | Keep unless ReAct path expands | P3 |
| `ai/domain/agent.py` | ~623 | Base agent vs helpers | P3 |
| `ai/orchestration/workflows/cash_flow_analysis.py` | ~615 | Experimental workflow | P2* |
| `ai/orchestration/workflows/compliance_check.py` | ~592 | Experimental workflow | P2* |
| `payment/application/services/reconciliation_service.py` | ~579 | Matching strategies vs orchestration | P3 |
| `ai/ml/features.py` | ~565 | Feature groups by domain | P3 |
| `billing/application/preventivo_ops.py` | ~550 | Ops vs PDF/email side paths | P2 |
| `payment/application/payment_commands.py` | ~541 | Commands vs importers glue | P3 |

\*P2 only if workflows move toward product; otherwise leave experimental.

**Done nearby:** `chat_agent.py` slimmed (structured + graph delegation);
`ai.tools.registry` is already a package.

### D-WF — Experimental multi-agent workflows

**GitHub:** [#38](https://github.com/gianlucamazza/openfatture/issues/38)  
**Location:** `openfatture/ai/orchestration/workflows/`  
(`invoice_creation`, `compliance_check`, `cash_flow_analysis`)

| Aspect | Status |
|--------|--------|
| Public CLI exposure | **No** — intentional |
| Config flag | `enable multi-agent orchestration (experimental)` in AI settings |
| Human interrupt | Confidence auto-gates or honest `awaiting_approval`; **no** invented human decisions |
| Product path | Tool-loop via `GraphAssistantBackend` only |

**Impact:** Code weight and maintenance cost if left half-productized.  
**Trigger:** Explicit product decision to ship multi-agent UX (still assistant-first).  
**Non-goal:** Do not add Typer subcommands for each workflow.

### D-ML-DRIFT — Accuracy-drift signal not implemented

**GitHub:** [#39](https://github.com/gianlucamazza/openfatture/issues/39)  
**Location:** `ai/ml/retraining/triggers.py` (`_check_accuracy_drift`)  
**Behavior:** Logs `status: not_implemented`; does **not** claim success.  
**Impact:** Retraining will not fire on accuracy drift until implemented.  
**Trigger:** When production ML monitoring is required.  
**Honesty rule:** Keep the explicit unavailable signal; never fake a metric.

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
| Full package | 49% | `[tool.coverage.report] fail_under` + `test.yml` |
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
| Multi-agent workflows on product path | Off / experimental | [D-WF #38](https://github.com/gianlucamazza/openfatture/issues/38) |
| Textual (or other) TUI | Non-goal | [#44](https://github.com/gianlucamazza/openfatture/issues/44); interactive terminal exists |
| MCP server / external tool bus | Non-goal until designed | [#44](https://github.com/gianlucamazza/openfatture/issues/44); hooks + tool contracts today |
| Browser / web app surface | Explicit non-goal | [#44](https://github.com/gianlucamazza/openfatture/issues/44); see STATUS |
| Domain CLI command tree growth | Forbidden | Domain ops stay on assistant + application layer |
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

1. **D-SIZE P1** — split `cash_flow_predictor` when forecasting is next touched  
2. **D-SIZE P2** — `invoice_commands` / `models.py` / `preventivo_ops` when billing storage changes  
3. **D-WF** — productize or delete experimental workflows after an explicit decision  
4. **D-ML-DRIFT** — only with real monitoring requirements  
5. **D-OBS / D-PDF-PAGOPA / D-TYPES-TESTS** — opportunistic  
6. **Product decisions** (TUI / MCP / web) — separate design + release, not drive-by PRs  

---

## How to keep this document honest

- Update **Last updated** and the closed ledger when debt is removed or accepted.  
- Prefer **IDs** (`D-SIZE`, `D-WF`, …) in PR descriptions when intentionally
  burning debt.  
- Do not list “nice to have” refactors without a trigger.  
- Historical investigation reports live under `docs/history/` and
  `docs/reports/` — they are **not** current claims.  
- In-code suppressions remain **forbidden**; fix the root cause instead.
