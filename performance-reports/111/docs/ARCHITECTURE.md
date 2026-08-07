# Architecture

OpenFatture is a CLI-first, agentic application for Italian electronic
invoicing. The public command surface stays small; domain work runs through
application services and assistant tools.

## Public surface

- `openfatture init`
- `openfatture assistant [MESSAGE]`
- `openfatture interactive start`
- `openfatture config ...`
- `openfatture status`

Business operations are not duplicated as top-level CLI groups. See
[CLI_REFERENCE.md](CLI_REFERENCE.md) and [AI_ARCHITECTURE.md](AI_ARCHITECTURE.md).

## Package layout (2.0)

```
openfatture/
  cli/           # public adapter only
  platform/      # config, logging, email, extras, async, metrics
  storage/       # SQLAlchemy models and sessions
  events/        # domain events bus and persistence
  hooks/         # hook registry and executor
  billing/       # clienti, fatture, preventivi, prodotti, batch, fiscale
  sdi/           # FatturaPA XML, PEC, notifications, signature
  payment/       # reconciliation and bank import (DDD layers)
  lightning/     # Lightning Network (optional / experimental)
  pdf/           # human-readable invoice PDFs
  ai/            # assistant, tools, providers, RAG, ML (feature extras)
  i18n/
```

Removed from the product: browser `web`, `web_scraper`, `ai.voice`, orphan
analytics agents, and the experimental in-process `plugins` package. See
[ARCHITECTURE_REDESIGN.md](ARCHITECTURE_REDESIGN.md) and
[CORE_VS_EXTENSIONS.md](CORE_VS_EXTENSIONS.md).

**Core vs extras vs extensions:** billing/SDI/payment/PDF are core; AI/RAG/ML/
Lightning are feature extras; user automation uses **hooks**.

### Import rules

1. `cli` may call application services and AI entrypoints only.
2. `ai` tools call application services; they are not a second domain layer.
3. Domain packages do not import `cli` or `ai`.
4. `platform` and `storage` do not depend on `ai` or `lightning`.
5. Optional features fail with an explicit install hint when extras are missing.

### Optional extras

| Extra | Purpose |
|-------|---------|
| *(core)* | Billing, SDI, payment, PDF, storage, platform, CLI, hooks engine |
| `ai` | LLM providers, assistant, tools, orchestration |
| `rag` | Vector store and embeddings |
| `ml` | Forecasting models (optional / frozen features) |
| `lightning` | Lightning Network stack (experimental) |
| `dev` | Tests and linters |
| `all` | Union of feature extras |

`payment` and `lightning` keep the DDD layout
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
 infrastructure (DB, PEC, files, bank importers, LND stubs)
```

Mutating tools keep their own confirmation and validation boundaries.
`status` is read-only and does not contact external services.
Startup is read-only; setup happens only through `init`.

## Related docs

- [Core vs extras vs extensions](CORE_VS_EXTENSIONS.md) — what is plugin vs core
- [AI-era redesign](ARCHITECTURE_REDESIGN.md) — unify under LangGraph; deprecate list
- [AI architecture](AI_ARCHITECTURE.md) — current assistant flow and tools
- [Configuration](CONFIGURATION.md)
- [Status](STATUS.md) — migration progress
- [Technical debt](TECHNICAL_DEBT.md)
- [Architecture diagrams](ARCHITECTURE_DIAGRAMS.md) — historical visuals
