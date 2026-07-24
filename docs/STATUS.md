# OpenFatture project status

**Current version:** 1.3.1
**Product posture:** CLI-first, with an interactive terminal mode for guided workflows
**Runtime:** Python 3.12+ and `uv`

## Supported product surface

- FatturaPA XML generation and validation
- PEC/SDI delivery and notification processing
- Client, invoice, quote, payment, and batch workflows
- Event audit trail, reports, hooks, and Lightning integrations
- Optional AI assistance, RAG, voice, and forecasting workflows
- Regulatory web scraping as an independent automation module

## Quality expectations

Every release should validate the full deterministic test gate, formatting,
linting, type checking, package build, CLI help/version output, and current
documentation links. Historical reports under `docs/history/` and
`docs/reports/` are context, not current quality claims.

## Current focus

The active polishing lane is onboarding and feedback quality in the CLI/TUI,
single-source version reporting, accurate capability documentation, and
production hardening.

## Explicit non-goals

There is no maintained browser frontend or alternate web application surface.
Future UI/API work requires a separate product decision and release plan.
