# OpenFatture Quick Start

OpenFatture is a CLI-first, agentic invoicing workspace for Italian
freelancers.

## Install

```bash
git clone https://github.com/venerelabs/openfatture.git
cd openfatture
# Full stack (recommended for development and AI). Core-only: uv sync
uv sync --all-extras
```

Feature extras (`ai`, `rag`, `ml`, `lightning`) are documented in
[CONFIGURATION.md](docs/CONFIGURATION.md).

## Initialize

```bash
uv run openfatture init
```

The command creates the database, local directories, and optional company,
PEC, notification, and AI configuration.

## Check readiness

```bash
uv run openfatture status
uv run openfatture status --json
```

## Work with the assistant

Use natural language for business operations:

```bash
uv run openfatture assistant "Create an invoice for 3 hours of consulting at 90 euros"
uv run openfatture assistant "List unpaid invoices"
uv run openfatture interactive start
```

The assistant is the public business interface. Deterministic commands are
limited to setup, configuration, diagnostics, and output control.

## Configuration

```bash
uv run openfatture config show
uv run openfatture config set ai_provider ollama
uv run openfatture config reload
```

See [CLI_REFERENCE.md](docs/CLI_REFERENCE.md) for the complete public surface
and [CONFIGURATION.md](docs/CONFIGURATION.md) for settings.
