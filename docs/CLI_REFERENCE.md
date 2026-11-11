# CLI Reference

OpenFatture exposes a deliberately small public command surface. Business
operations (clients, invoices, lines, PDFs, collections, reports) are requests
to the assistant; the CLI does not duplicate them. Besides setup and
diagnostics, it keeps only the operations the assistant does not perform:
writing the FatturaPA XML file, the SDI journal and its human-evidence
resolutions, and the collection ledger migration.

## Global options

| Option | Purpose |
| --- | --- |
| `--version`, `-v` | Print the version and exit |
| `--debug` | Show diagnostic logs and tracebacks |
| `--format`, `-f` | Output format for commands: `rich` (default), `json`, `markdown`, `stream-json`, `html` |

## `openfatture`

Starts the interactive assistant directly, using the same session handling and
runtime as `openfatture assistant` without a message. Use `openfatture --help`
to display the command reference. Structured output requires an explicit
`assistant` request, for example `openfatture --format json assistant "List unpaid invoices"`.

## `openfatture init`

Creates the local data directories and optional company configuration, and
creates or **upgrades the database schema** (packaged Alembic migrations; SQLite
files are backed up next to the database first). Run it after upgrading
OpenFatture when `status` asks for it.

```bash
openfatture init
openfatture init --no-interactive   # only directories and database schema
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

## `openfatture config`

Reads or updates the user configuration (`config.toml`) and secrets (OS
keychain). See [configuration sources](CONFIGURATION.md#sources-and-precedence).

```bash
openfatture config show                       # values and their source
openfatture config set ai_provider openai     # validated, writes only this key
openfatture config set ai_api_key sk-...      # secret: stored in the keychain
openfatture config unset ai_base_url          # back to the default
openfatture config migrate [--env-file .env]  # move plaintext secrets / import a .env
openfatture config reload
```

## `openfatture status`

Reports version, storage paths, optional extras, **readiness**
(`core_ready` / `assistant_ready` plus `next_steps`) and **configuration**
(`config_file`, `secret_backend`, `plaintext_secrets`, `ignored_dotenv`)
without changing local state. Use `--json` for machine-readable output.

```bash
openfatture status
openfatture status --json
```

## `openfatture fattura`

| Command | Purpose |
| --- | --- |
| `generate-xml ID [--output PATH] [--dry-run]` | Build FatturaPA XML (no XSD validation, no transmission) |
| `sdi-journal` | Read-only list of PEC attempts and imported receipts |
| `associate-receipt RECEIPT INVOICE --evidence TEXT` | Associate an unresolved receipt (asks for confirmation) |
| `resolve-submission ID --sent/--not-sent --evidence TEXT` | Resolve an uncertain PEC attempt (asks for confirmation) |

Receipt association and submission resolution record a person's verification of
external evidence, so they are not assistant tools.

## `openfatture pagamento`

| Command | Purpose |
| --- | --- |
| `migrate` | Upgrade pre-ledger collection data without changing balances |

Interactive assistant slash commands (when no one-shot message is given):

- `/help` — list commands
- `/exit` — end the session
- `/session` — show session id
- `/clear` — clear persisted messages for the current session

Use `openfatture --help` and command-specific `--help` output as the
canonical option reference.


### Pending assistant turns

`openfatture assistant --session ID` resumes a pending turn before processing
another message. In the interactive assistant, `/resume` continues that turn;
`/pending` lists tool calls whose outcomes require verification. `/reconcile`
accepts a JSON object containing `call_id`, a verified ToolResult in `result`,
and nonempty `evidence`. It records the outcome without rerunning the operation.
See [reconciliation instructions](AI_ARCHITECTURE.md#reconciling-an-uncertain-operation).
A pending turn must be resolved before clearing history or starting another
request. Existing sessions without pending-turn metadata continue normally.
