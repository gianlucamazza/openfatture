# Architecture

OpenFatture is a CLI-first, agentic application for Italian electronic
invoicing. The public command surface stays small; domain work runs through
application services and assistant tools.

## Public surface

- `openfatture init`
- `openfatture` (interactive assistant) and `openfatture assistant [MESSAGE]`
- `openfatture config ...`
- `openfatture status`
- `openfatture cliente|fattura|pagamento ...` — deterministic data commands,
  thin adapters over the same application services the assistant tools use

No other business workflow gets its own top-level CLI group. See
[CLI_REFERENCE.md](CLI_REFERENCE.md) and [AI_ARCHITECTURE.md](AI_ARCHITECTURE.md).

## Package layout (2.0)

```
openfatture/
  cli/           # public adapter only
  platform/      # config, logging, email, extras, async, metrics
  storage/       # SQLAlchemy models and sessions
  events/        # domain events bus and persistence
  hooks/         # hook registry and executor
  billing/       # fatture, preventivi, batch, application services
  sdi/           # FatturaPA XML, PEC + email templates, notifications, signature
  payment/       # reconciliation and bank import (DDD layers)
  pdf/           # human-readable invoice PDFs
  ai/            # assistant runtime, tools, providers, RAG (feature extras)
  i18n/
```

Removed from the product: browser `web`, `web_scraper`, `ai.voice`, orphan
analytics agents, the experimental in-process `plugins` package and (2.8.0)
the ML forecasting stack and the multi-agent workflows. See
[ARCHITECTURE_REDESIGN.md](history/ARCHITECTURE_REDESIGN.md) and
[CORE_VS_EXTENSIONS.md](CORE_VS_EXTENSIONS.md).

**Core vs extras vs extensions:** billing/SDI/payment/PDF are core; AI/RAG
are feature extras; user automation uses **hooks**.

### Import rules

1. `cli` may call application services and AI entrypoints only.
2. `ai` tools call application services; they are not a second domain layer.
3. Domain packages (`billing`, `payment`, `sdi`, `pdf`) and `storage`,
   `events`, `hooks`, `platform` do not import `cli` or `ai`; `ai` does not
   import `cli`. Application services publish through
   `events.get_global_event_bus()`.
4. Optional features fail with an explicit install hint when extras are missing.

Rule 3 is enforced by `tests/test_import_rules.py`, which also forbids
`platform` from importing `billing`, `payment`, `sdi` or `pdf`. Known remaining
coupling: `storage` models reference payment ORM models lazily.

### Persistence

- Application services open sessions with `storage.session.db_session()` or
  `session_scope(session)`; nothing manages `close()` by hand.
- The schema is owned by the migrations in `storage/migrations` (shipped in the
  wheel) through `storage.schema`; see
  [CONFIGURATION.md](CONFIGURATION.md#database-schema).

### Optional extras

| Extra | Purpose |
|-------|---------|
| *(core)* | Billing, SDI, payment, PDF, storage, platform, CLI, hooks engine |
| `ai` | LLM providers, assistant, tools, orchestration |
| `rag` | Vector store and embeddings |
| `dev` | Tests and linters |
| `all` | Union of feature extras |

`payment` keeps the DDD layout
(`application` / `domain` / `infrastructure`).

## Layers

```
CLI / assistant tools
        |
        v
 application services  (billing, payment, sdi, ...)
        |
        v
 domain rules + events
        |
        v
 infrastructure (DB, PEC, files, bank importers)
```

Mutating tools keep their own confirmation and validation boundaries.
`status` is read-only and does not contact external services.
Startup is read-only; setup happens only through `init`.

## Related docs

- [Architecture complete](history/ARCHITECTURE_COMPLETE.md) — comprehensive roadmap, public surface, and phased delivery
- [Core vs extras vs extensions](CORE_VS_EXTENSIONS.md) — what is plugin vs core
- [AI-era redesign](history/ARCHITECTURE_REDESIGN.md) — unify under LangGraph; deprecate list
- [AI architecture](AI_ARCHITECTURE.md) — current assistant flow and tools
- [Configuration](CONFIGURATION.md)
- [Status](STATUS.md) — migration progress
- [Technical debt](TECHNICAL_DEBT.md)
- [Architecture diagrams](history/ARCHITECTURE_DIAGRAMS.md) — historical visuals
