# CLI Reference

OpenFatture exposes a deliberately small public command surface. Business
operations (clients, invoices, lines, PDFs, the FatturaPA XML file,
collections, reports) are requests to the assistant; the CLI does not
duplicate them. Besides setup and diagnostics, it keeps only the SDI journal
and its human-evidence resolutions, which the assistant must not perform.

Help, messages and errors follow the configured locale (`locale` in
`config.toml`, or `OPENFATTURE_LOCALE`): Italian by default, also English,
German, Spanish and French.

## Global options

| Option | Purpose |
| --- | --- |
| `--version`, `-v` | Print the version and exit |
| `--debug` | Show diagnostic logs and tracebacks |
| `--format`, `-f` | Output format for commands: `rich` (default), `json`, `markdown`, `stream-json`, `html` |
| `--message`, `-m` | One request for the assistant instead of the chat |
| `--session` | Resume a saved assistant session by its ID (enables persistence) |
| `--continue`, `-c` | Resume the latest saved conversation (cannot be combined with `--session`) |
| `--stream/--no-stream` | Show the assistant response while it is generated (default `--stream`) |

`--message` and `--session` apply only when no command is given.

## `openfatture`

Starts the business assistant. The assistant can inspect local business data
and use registered domain tools when the request requires an action. Requires
the `ai` extra (`uv sync --extra ai`).

```bash
openfatture                                                  # interactive chat
openfatture -m "Create an invoice for 3 hours of consulting at 90 euros"
openfatture --no-stream -m "List unpaid invoices"
openfatture --format json -m "Summarize this month's cash flow"
openfatture --session <session-id>                           # resume a stored session
openfatture --continue                                       # resume the latest conversation
```

The chat persists turns to the file session store and prints the session ID.
A `-m` request does not create a session unless `--session` is set (resume /
continue that session). Structured output (`--format json` and the others)
needs a `-m` request; without one the command exits with code 2 and the error
code `interactive_format`.

### Memory

- **Within a conversation** the assistant sees the previous messages. The whole
  transcript is saved (up to 100 messages); the model receives the most recent
  part that fits about 12,000 tokens, starting at one of your messages, with a
  note when earlier messages were left out. Data shown by tools in earlier
  turns is read again from the tools, not from the transcript.
- **Across conversations** it keeps *notes*: preferences or stable facts you ask
  it to remember ("ricorda che…"). Saving a note asks for your confirmation and
  shows its text; notes containing credentials are refused; at most 50 notes of
  300 characters. `/memory` lists them and `/forget N` deletes one. The model
  receives them as information about your preferences, never as instructions
  over its rules, and the tools' data wins over a note.

### Missing setup

Before the assistant starts, OpenFatture checks the setup without changing it:

| Missing | In a terminal | Otherwise (pipe, script, structured format) |
| --- | --- | --- |
| Company profile (`cedente_partita_iva`, `cedente_denominazione`) | runs `openfatture init` with the wizard | refuses, error code `setup_required` |
| Database (absent, outdated or pre-2.8) or archive directory | runs `openfatture init` without the wizard (SQLite backup first) | refuses, error code `setup_required` |
| Database from a newer OpenFatture | refuses, error code `newer_database` | refuses, error code `newer_database` |
| AI API key (any provider except Ollama) | refuses with the `config set` command to run | refuses, error code `ai_key_missing` |

A refusal prints what to run and exits with code **3**; nothing is created.

## `openfatture init`

Creates the local data directories and optional company configuration, and
creates or **upgrades the database schema** (packaged Alembic migrations; SQLite
files are backed up next to the database first). Run it after upgrading
OpenFatture when `status` asks for it.

```bash
openfatture init
openfatture init --no-interactive   # only directories and database schema
```

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
| `sdi-journal` | Read-only list of PEC attempts and imported receipts |
| `associate-receipt RECEIPT INVOICE --evidence TEXT` | Associate an unresolved receipt (asks for confirmation) |
| `resolve-submission ID --sent/--not-sent --evidence TEXT` | Resolve an uncertain PEC attempt (asks for confirmation) |

Receipt association and submission resolution record a person's verification of
external evidence, so they are not assistant tools.

Interactive assistant slash commands (when no one-shot message is given):

- `/help` — list commands
- `/open [N]` — open the N-th most recent document the chat generated (default
  the latest) with the default application; see [Opening documents](#opening-documents)
- `/exit` — end the session
- `/session` — show session id
- `/clear` — clear persisted messages for the current session
- `/memory` — list the notes kept across conversations
- `/forget N` — delete note N

Use `openfatture --help` and command-specific `--help` output as the
canonical option reference.

### Opening documents

When a tool writes a document (PDF, FatturaPA XML, signed `.p7m`, CSV export), the chat prints
its path under the tool line as a terminal link: Ctrl+click (Cmd+click on
macOS) opens it in terminals that support OSC 8 hyperlinks. `/open` opens the
latest document, `/open 2` the one before. Asking the assistant to open a
document ("aprilo") uses the `open_document` tool, enabled from
`ai_tool_access = "standard"` up (the default is `full`).

Only `.pdf`, `.xml`, `.p7m` and `.csv` files, or folders ("apri la cartella
delle esportazioni"), inside the exports or the archive directory can be
opened, after resolving symbolic links. The default application (`xdg-open` on
Linux, `open` on macOS, the file association on Windows) starts detached from
the chat; when the launcher reports within two seconds that no application
handles the file type, the chat says so. A `.p7m` needs a signature viewer
installed (for example the one your signing device came with). Without a person at the terminal or a
graphical session (SSH, scripts) nothing is opened and the path is shown
instead.


### Pending assistant turns

`openfatture --session ID` resumes a pending turn before processing
another message. In the interactive assistant, `/resume` continues that turn;
`/pending` lists tool calls whose outcomes require verification. `/reconcile`
accepts a JSON object containing `call_id`, a verified ToolResult in `result`,
and nonempty `evidence`. It records the outcome without rerunning the operation.
See [reconciliation instructions](AI_ARCHITECTURE.md#reconciling-an-uncertain-operation).
A pending turn must be resolved before clearing history or starting another
request. Existing sessions without pending-turn metadata continue normally.
