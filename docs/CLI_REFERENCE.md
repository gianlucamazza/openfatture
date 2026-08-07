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
requires an action. Requires the `ai` extra (`uv sync --extra ai`).

```bash
openfatture assistant "Create an invoice for 3 hours of consulting at 90 euros"
openfatture assistant --no-stream "List unpaid invoices"
openfatture assistant --json "Summarize this month's cash flow"
openfatture assistant --session <session-id>   # resume a stored session
```

Without a message argument, starts an interactive multi-turn session. Interactive
mode persists turns to the file session store and prints the session ID.
One-shot messages do not create a session unless `--session` is set (resume /
continue that session).

## `openfatture interactive start`

Starts a persistent conversational session in the terminal (same assistant
runtime; sessions stored under the configured data directory).

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

Reports version, storage paths, optional extras, and **readiness**
(`core_ready` / `assistant_ready` plus `next_steps`) without changing local
state. Use `--json` for machine-readable output.

```bash
openfatture status
openfatture status --json
```

Interactive assistant slash commands (when no one-shot message is given):

- `/help` — list commands
- `/exit` — end the session
- `/session` — show session id
- `/clear` — clear persisted messages for the current session

Use `openfatture --help` and command-specific `--help` output as the
canonical option reference.
