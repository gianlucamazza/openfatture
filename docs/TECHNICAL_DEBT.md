# Technical Debt Inventory

Honest inventory of **open** and **closed** debt after modernization **2.0**,
the **2.1.0** LangGraph default flip, post-2.1 hygiene (#31–#34), the
**2.6.0–2.8.0** architecture review and the **2.9.0** burn-down of all open debt.

**Last updated:** 2026-11-10  
**Version baseline:** 2.9.0 (`v2.9.0`) · analysis: [docs/reports/technical-debt-analysis-2026-11.md](reports/technical-debt-analysis-2026-11.md)

Related: [STATUS.md](STATUS.md), [CORE_VS_EXTENSIONS.md](CORE_VS_EXTENSIONS.md),
[ARCHITECTURE.md](ARCHITECTURE.md), [releases/v2.1.0.md](releases/v2.1.0.md).

### GitHub tracking

| Role | Link |
|------|------|
| Umbrella | [#36 tracker](https://github.com/gianlucamazza/openfatture/issues/36) |
| Milestone | [Post-2.1 backlog (on-demand)](https://github.com/gianlucamazza/openfatture/milestone/1) |
| Labels | `technical-debt`, `product-decision`, `on-demand`, `priority:p1`–`p3` |

| ID | Issue | State |
|----|-------|-------|
| D-SIZE | [#37](https://github.com/gianlucamazza/openfatture/issues/37) | Closed in 2.9.0 |
| D-OBS | [#40](https://github.com/gianlucamazza/openfatture/issues/40) | Closed in 2.9.0 |
| D-PDF-PAGOPA | [#41](https://github.com/gianlucamazza/openfatture/issues/41) | Closed in 2.9.0 (removed: not applicable) |
| D-TYPES-TESTS | [#42](https://github.com/gianlucamazza/openfatture/issues/42) | Closed in 2.9.0 |
| D-ASYNC | [#43](https://github.com/gianlucamazza/openfatture/issues/43) | Closed in 2.9.0 |
| Product surfaces (TUI/MCP/web) | [#44](https://github.com/gianlucamazza/openfatture/issues/44) | Product decision, not debt |

Close the matching issue and move the row to the closed ledger when debt is burned.

---

## Verdict

| Signal | State |
|--------|--------|
| Open code debt | **None** (2.9.0) |
| Module size | No product module above ~520 LOC; no function above radon rank C |
| Types | mypy on `openfatture/` and `tests/`, zero suppressions |
| Amount consistency | Stored totals, XML and PDF share `billing.application.totals` |
| Blocking release debt | **None** |

New debt is recorded here with an ID, impact and trigger when it is found;
it is not left in code comments.

---

## Debt level by area

| Area | Level | Notes |
|------|-------|--------|
| Public CLI surface | Low | Assistant (`openfatture`, `assistant`), `init`, `config`, `status`, plus documented `cliente` / `fattura` / `pagamento` adapters |
| Core billing / SDI / payment | Low | Tools → application services; payment suite floor 75% |
| Package layout | Low | Bounded packages; no empty placeholders; extras explicit |
| Config / SSOT | Low | Version, backends, AI credentials hydrated consistently (#32) |
| AI runtime (product path) | Low | Default `langgraph_tool_loop`; single tool-loop; ChatAgent slim rollback |
| Module size / cohesion | Low | Split by cohesion in 2.9.0; radon rank ≤ C everywhere |
| Lightning | **Removed** | Incomplete LND gRPC; archive under `docs/history/lightning/` |
| RAG auto-update | Low | Real `reindex_callback` required; default auto-update off |
| Tooling / types | Low | Zero in-code `noqa` / `type: ignore` / `pragma: no cover`; tests type-checked |
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
| Contributions missing from DatiRiepilogo/totals; PDF riepilogo and totals diverging from XML | 2.9.0 | One summary for totals, XML and PDF; amount due on PDF and QR |
| 0% lines without natura; quotes losing natura | 2.9.0 | Rule enforced at creation and XML build; regime defaults |
| Stamp duty never computed; meaningless `bollo_assolto_virtuale` | 2.9.0 | Automatic `importo_bollo`; flag dropped (migration) |
| PDF sections running under the footer / off the page | 2.9.0 | Measured page flow, real page count |
| D-XML-TOTAL `ImportoTotaleDocumento` not emitted | 2.9.0 | Emitted from the stored total |
| D-SIZE oversized modules and complexity hotspots (#37) | 2.9.0 | Models package, command/query modules, registry/PDF/provider splits; no rank D+ |
| D-OBS approximate bulkhead queue (#40) | 2.9.0 | `Bulkhead` counts waiters explicitly |
| D-PDF-PAGOPA (#41) | 2.9.0 | Removed: pagoPA notices are issued by public creditors |
| D-TYPES-TESTS (#42) | 2.9.0 | `check_untyped_defs` on tests; CI runs `mypy openfatture/ tests/` |
| D-ASYNC nested-loop bridge (#43) | 2.9.0 | One strategy, no `nest_asyncio` |
| D-CLI-I18N hard-coded CLI text | 2.9.0 | All command output in `cli.ftl`, five locales |
| D-ERRORS application refusals reported as tool success | 2.9.0 | `{"error"}` → failed `ToolResult`, not cached, breaker-neutral |
| Awaitable matcher list shim | 2.9.0 | Synchronous matcher contract |
| Duplicate line tools, `ReActOrchestrator`, unused feedback tables | 2.9.0 | Removed |

---

## Open debt

None. Record new items here with an **ID**, **impact** and **trigger**.

### Error contract (reference)

Layers keep one contract each, translated at the boundary:

1. Domain and infrastructure code raises exceptions (`OpenFattureError`,
   `XMLValidationError`, library errors).
2. Application services return `{"success": True, ...}` or
   `{"error": <message>, "error_code"?: <code>}`; exception text goes through
   `platform.errors.describe_error` (no SQL).
3. Tools turn an error dict into `ToolResult(success=False, data=<dict>)`;
   such refusals are not cached and do not open the circuit breaker.

Broad `except Exception` remains only where it isolates peripheral work
(post-commit events and notifications, hooks, optional caches) and logs it.

### D-COV — Coverage floors are baselines

| Suite | Floor | Source |
|-------|-------|--------|
| Full package | 78% | `[tool.coverage.report] fail_under` + `test.yml` |
| Payment | 75% | `payment-tests.yml` |

Raise floors only when a suite sustainably exceeds them. This is a policy,
not debt.

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

## How to keep this document honest

- Update **Last updated** and the closed ledger when debt is removed or accepted.  
- Prefer **IDs** (`D-SIZE`, `D-WF`, …) in PR descriptions when intentionally
  burning debt.  
- Do not list “nice to have” refactors without a trigger.  
- Historical investigation reports live under `docs/history/` and
  `docs/reports/` — they are **not** current claims.  
- In-code suppressions remain **forbidden**; fix the root cause instead.
