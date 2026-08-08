# OpenFatture project status

**Current version:** 2.1.0  
**Product posture:** CLI-first, with an interactive terminal mode for guided workflows  
**Runtime:** Python 3.12+ and `uv`

## Supported product surface

- FatturaPA XML generation and validation
- PEC/SDI delivery and notification processing
- Client, invoice, quote, payment, and batch workflows
- Event audit trail, reports, hooks
- Optional AI assistance, RAG, and forecasting workflows (feature extras)

## Quality expectations

Every release should validate the full deterministic test gate, formatting,
linting, type checking, package build, CLI help/version output, and current
documentation links. Historical reports under `docs/history/` and
`docs/reports/` are context, not current quality claims.

In-code suppressions (`noqa`, `type: ignore`, `pragma: no cover`) are not used;
fix the root cause instead.

## 2.0 modernization (complete)

1. ~~Repo hygiene and living documentation~~
2. ~~Ruff-only tooling~~
3. ~~Optional dependency extras~~
4. ~~D0 non-core cut (voice, scraper, orphan agents)~~
5. ~~D1 package reorg (`billing` / `events` / `hooks` / `platform` / `pdf`)~~
6. ~~Core vs extras vs extensions; experimental plugins package removed~~
7. ~~Honesty gates: Lightning no silent mock; RAG queue no simulation~~
8. ~~D3 unified `ai.runtime` entry for assistant~~
9. ~~D2: AI tools are adapters over application services~~
10. ~~2.0.0 release notes and version bump~~

## Current focus (post-2.1)

1. **LangGraph is the default product backend** (`langgraph_tool_loop`);
   `ASSISTANT_BACKEND=chat` remains a supported rollback. Multi-agent workflows
   stay non-CLI.
2. Continue splitting oversized modules (`cash_flow_predictor`, ops facades;
   `ai.tools.registry` is already a package)
3. Onboarding polish continues (readiness in `status`, slash commands in assistant)

**Removed from product:** experimental Lightning Network module (incomplete LND
gRPC; archived under `docs/history/lightning/`).

See [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md), [releases/v2.1.0.md](releases/v2.1.0.md),
[releases/v2.0.2.md](releases/v2.0.2.md), and [releases/v2.0.1.md](releases/v2.0.1.md).

## Coverage floors (CI)

| Suite | Floor | Source of truth |
|-------|-------|-----------------|
| Full package | 49% | `[tool.coverage.report] fail_under` in `pyproject.toml` (+ `test.yml`) |
| Payment module | 75% | `payment-tests.yml` (measured ~78%) |

Local default pytest runs **without** coverage (faster). Pass `--cov=openfatture`
(or use CI flags) when you need a report.

## Explicit non-goals

There is no maintained browser frontend or alternate web application surface.
Future UI/API work requires a separate product decision and release plan.
Public domain workflows stay on the assistant; do not reintroduce large CLI
command trees for business operations.
