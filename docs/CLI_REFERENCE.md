# CLI Reference

OpenFatture exposes a deliberately small public command surface. Business
operations are expressed as requests to the assistant; setup and diagnostics
remain deterministic commands.

## `openfatture init`

Creates the local data directories, database, and optional company
configuration.

```bash
openfatture init
openfatture init --no-interactive
```

## `openfatture assistant`

Sends a natural-language request to the business assistant. The assistant can
inspect local business data and use registered domain tools when the request
requires an action.

```bash
openfatture assistant "Create an invoice for 3 hours of consulting at 90 euros"
openfatture assistant --no-stream "List unpaid invoices"
openfatture assistant --json "Summarize this month's cash flow"
```

## `openfatture interactive start`

Starts a persistent conversational session in the terminal.

```bash
openfatture interactive start
```

## `openfatture config`

Reads or updates local configuration.

```bash
openfatture config show
openfatture config set ai_provider ollama
openfatture config reload
```

## `openfatture status`

Reports version, storage paths, and AI readiness without changing local state.

```bash
openfatture status
openfatture status --json
```

Use `openfatture --help` and command-specific `--help` output as the
canonical option reference.
