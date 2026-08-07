# OpenFatture

OpenFatture is an agentic, CLI-first workspace for Italian electronic
invoicing. Describe the work you need; the assistant coordinates the domain
tools and returns an auditable result.

## Why

Italian freelancers must issue invoices as FatturaPA XML and deliver them
through SDI. The usual answer is a SaaS subscription that owns your client
list, your invoices, and your archive. OpenFatture keeps all of it local:
your data stays in a database on your machine, the XML is generated and
validated offline, and every action is recorded in an event audit trail you
can inspect. AI assistance is optional — the domain tools work without it.

Built for one-person businesses and small studios comfortable in a terminal.

## Start

```bash
# Full stack (AI + RAG + ML + …). Core-only: uv sync
uv sync --all-extras
uv run openfatture init
uv run openfatture status
uv run openfatture assistant "Help me prepare an invoice for a software project"
```

Optional feature extras: `ai`, `rag`, `ml`, `lightning`, `all`.
See [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

For a terminal conversation:

```bash
uv run openfatture interactive start
```

## Public CLI

The supported surface is intentionally small:

- `init` creates local state and guides setup.
- `assistant` handles business requests in natural language.
- `interactive start` opens a conversational session.
- `config` reads or updates configuration.
- `status` reports local readiness without mutation.

See [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md).

## What it covers

- FatturaPA XML generation and validation
- PEC/SDI delivery and notification processing
- Client, invoice, quote, payment, and batch workflows
- Event audit trail, reports, and hooks
- Optional AI assistance (assistant + domain tools), RAG, and forecasting extras
- Optional Lightning Network integration (experimental)

## Status

Version **2.0.1**, Python 3.12+ and `uv`. Packaging, extras, honesty gates, and
the unified assistant runtime shipped in 2.0 — see
[docs/STATUS.md](docs/STATUS.md), [docs/releases/v2.0.1.md](docs/releases/v2.0.1.md),
and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

Explicit non-goal: there is no browser frontend or web application surface,
and adding one would be a separate product decision.

## Documentation

- [Quick start](QUICKSTART.md)
- [Configuration](docs/CONFIGURATION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [AI architecture](docs/AI_ARCHITECTURE.md)
- [AI-era redesign](docs/ARCHITECTURE_REDESIGN.md)
- [Current status](docs/STATUS.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Development

```bash
uv sync --all-extras
uv run python -m pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy openfatture/
```

OpenFatture is released under the MIT License.
