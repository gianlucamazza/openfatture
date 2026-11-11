# Configuration

OpenFatture keeps one configuration per user, secrets in the operating-system
keychain, and uses environment variables only as explicit overrides. Use the
CLI for inspection and updates:

```bash
openfatture config show                 # effective values and where each comes from
openfatture config set ai_provider openai
openfatture config set ai_api_key       # value goes to the keychain, never to config.toml
openfatture config unset ai_base_url
openfatture config migrate              # move plaintext secrets out of config.toml
```

## Sources and precedence

Highest precedence first:

| Source | Location | Written by |
| --- | --- | --- |
| Environment variables | process environment (`AI_MODEL`, `PEC_PASSWORD`, …) | you, CI, containers |
| Secrets | OS keychain (Secret Service, macOS Keychain, Windows Credential Locker), or `credentials.toml` (0600) when no keychain is available | `init`, `config set`, `config migrate` |
| User configuration | `config.toml` in the user config directory (`~/.config/openfatture/` on Linux) | `init`, `config set` |
| Defaults | built in | — |

OpenFatture **never reads a `.env` file by itself**, so a command behaves the
same in every working directory. `openfatture status` warns when a `./.env` is
present but ignored.

- `OPENFATTURE_CONFIG_DIR` points to another configuration directory (for
  example a second profile or tests).
- `OPENFATTURE_SECRET_BACKEND=keyring|file` forces the secret backend; `file`
  keeps secrets in `credentials.toml` next to `config.toml`.

Secret settings are `ai_api_key`, `pec_password` and
`signature_certificate_password`. `config set` validates every value against
its type, writes only the given key (comments and other keys in `config.toml`
are preserved) and reports when an environment variable overrides it.

## Database schema

The schema is owned by the Alembic migrations shipped inside the package
(`openfatture/storage/migrations`).

- A new database is created at the current schema on first use.
- A database behind the current release is refused until `openfatture init`
  upgrades it; SQLite files are copied to `<name>.bak-<timestamp>` first.
- Databases created before 2.8.0 have no migration history: they keep working,
  and `openfatture init` verifies their columns and adopts them.
- `openfatture status --json` reports `database_schema`
  (`empty`, `current`, `outdated`, `unversioned` or `ahead`).

The migration chain starts from the 1.x schema, so new databases are created
from the models and stamped at head (`openfatture init` or first use); run
`uv run alembic upgrade head` from the repository only against an existing,
versioned database.

## Development and containers

Load an env file explicitly when you need one:

```bash
uv run --env-file .env openfatture status
docker run --env-file .env openfatture:latest
```

`docker-compose.yml` passes `.env` through `env_file:` and sets
`OPENFATTURE_SECRET_BACKEND=file`, because containers have no keychain.

## Migrating from `.env`

Earlier versions read `./.env` implicitly. Import it once:

```bash
openfatture config migrate --env-file .env
openfatture config show
```

Secrets go to the keychain; other values are added to `config.toml` only when
not already set, and conflicting keys are listed instead of overwritten. The
source file is left untouched: delete it once `config show` looks right.

## Optional extras

Core install covers billing, SDI, payment reconciliation, PDF, and the
public CLI (`init`, `config`, `status`). Feature stacks are opt-in:

| Extra | Install | Provides |
| --- | --- | --- |
| `ai` | `uv sync --extra ai` | LLM providers, assistant runtime and tools |
| `rag` | `uv sync --extra rag` | ChromaDB + embeddings (includes `ai`) |
| `all` | `uv sync --extra all` | Union of feature extras |
| `dev` | `uv sync --extra dev` | Tests and linters |

Voice STT/TTS and the regulatory web scraper were removed from the product
(see [ARCHITECTURE_REDESIGN.md](history/ARCHITECTURE_REDESIGN.md)).

### Extensions (not plugins)

- **Hooks** (supported): scripts under `~/.openfatture/hooks/`; see
  `examples/hooks/` and [CORE_VS_EXTENSIONS.md](CORE_VS_EXTENSIONS.md).
- **In-process plugins**: not supported (experimental package removed).

For what belongs in core vs an extra vs a hook, see
[CORE_VS_EXTENSIONS.md](CORE_VS_EXTENSIONS.md).

Development full stack:

```bash
uv sync --all-extras
```

`openfatture status` / `status --json` reports which extras are installed.

## Core settings

| Setting | Purpose |
| --- | --- |
| `DATABASE_URL` | Local database connection |
| `DATA_DIR` | Application data directory |
| `ARCHIVIO_DIR` | Generated and archived documents |
| `CEDENTE_DENOMINAZIONE` | Company or freelancer name |
| `CEDENTE_PARTITA_IVA` | VAT number |
| `CEDENTE_CODICE_FISCALE` | Tax code |
| `PEC_ADDRESS` | Certified email address |
| `PEC_PASSWORD` | Certified email credential |
| `AI_PROVIDER` | **Product SSOT** assistant provider (`openai` / `anthropic` / `ollama`) |
| `AI_MODEL` | **Product SSOT** model name for the selected provider |
| `AI_API_KEY` | **Product SSOT** provider credential |
| `AI_BASE_URL` | **Product SSOT** local provider endpoint (Ollama) |
| `ASSISTANT_BACKEND` | Product assistant orchestration: `langgraph` (default) or `chat` (rollback) |
| `AI_TOOL_ACCESS` | Which tools the assistant may use, by risk class. `read`: lookups only. `standard`: lookups plus local documents (PDF, FatturaPA XML, CSV) in the exports and archive directories. `full` (default): also creates, changes and deletes records; each of those calls shows its parameters and asks for a human confirmation, and is refused without a person at the terminal. No level enables SDI/PEC send. |
| `AI_ENABLED_TOOLS` | Comma-separated tool names enabled on top of `AI_TOOL_ACCESS` (default empty). It is the only way to enable a transmit tool such as `send_invoice_to_sdi`. Unknown names are ignored; `all` is not a special value. |
| `AI_TOOLS_REQUIRE_CONFIRMATION` | Default `true`. When true, tools that require confirmation (including every SDI/PEC send) refuse unless a human says yes. An interactive TTY may prompt (default no). `source="human"` with `confirmed=True` is an API for human-facing callers; no built-in UI uses that path yet (there is no TUI). The model cannot self-confirm. Non-interactive sessions refuse and do not transmit. Setting this to `false` skips the prompt but still requires an `AI_ENABLED_TOOLS` opt-in for transmit tools. |

Product credentials written by `openfatture init` use the `AI_*` names above.
The provider factory hydrates `AISettings` from those values (see
`hydrate_ai_settings_from_platform`). Advanced AI-only knobs may use the
`OPENFATTURE_AI_*` prefix; when both are set, `OPENFATTURE_AI_*` wins for that
field.

Credentials belong in the keychain (`openfatture config set ai_api_key …`) or
in the environment. Do not commit credentials.

## Provider examples

Cloud provider (any OpenAI-compatible endpoint, e.g. DeepSeek, via `ai_base_url`):

```bash
openfatture config set ai_provider openai
openfatture config set ai_model gpt-5
openfatture config set ai_api_key sk-...
```

Local provider:

```bash
openfatture config set ai_provider ollama
openfatture config set ai_model qwen3:8b
openfatture config set ai_base_url http://localhost:11434
```

For a one-off override use the environment, e.g. `AI_MODEL=qwen3:14b openfatture`.
Check the result with `openfatture config show` or `openfatture status`.

## User profile and assistant confirmations

The setup wizard and `config set` save the user profile to `config.toml` and
secrets to the keychain (see [Sources and precedence](#sources-and-precedence)).
New databases default to the user data directory; existing configured database
URLs are preserved.

With `ai_tools_require_confirmation=true` (the default), tools marked as
requiring confirmation cannot execute without approval from a human-facing path. Noninteractive callers receive `confirmation_required`.
The legacy `confirm=False` argument does not bypass this requirement.

`status --json` reports missing invoice fields separately from delivery
configuration. Readiness describes local configuration, not successful
provider authentication or SDI delivery.

Unknown model prices are marked with `cost_known=false`; their numeric cost
placeholder is not a billing estimate. Use `openfatture --debug assistant`
for diagnostic logs.

## Terminal assistant behavior

The chat (`openfatture`) and single requests (`openfatture -m`) share a terminal presentation layer.
Live previews are temporary; the complete Markdown response is printed once
into scrollback. Paths of generated documents are printed as terminal links.
Slash commands support help, opening the latest document (`/open`), session
ID, clearing messages and exit. Input history stays in memory. `NO_COLOR` is respected.

Confirmations pause the live display. Denied operations are recorded as denied,
not executed. Ctrl+C cancels an active asynchronous turn and waits for cleanup;
an operation already started may have taken effect, so inspect its outcome
before retrying. EOF exits at the input prompt.

Runtime interactions use the `AssistantInteraction` protocol, passed at
construction, rather than callbacks attached by the UI after construction.
`last_response` holds the final or partial turn outcome; `total_usage` aggregates
all completed provider requests, including requests before a later interruption.
Session metadata and `AITurnCompletedEvent` preserve status, tool outcomes and
`usage_complete`. Unknown usage is never estimated from text.

Tools default to one attempt. `retry_safe=True` is an explicit declaration
for operations safe to repeat, limited to ConnectionError and TimeoutError.
Do not enable it for writes without an independently verified idempotency
guarantee. Permission and validation errors are not retried.

Credentials are masked recursively in diagnostic dictionaries, and configured
credentials are also removed from textual diagnostics. `config set` confirms
saving a credential without echoing its value. Debug traceback output omits
local variables.

`status` checks the configured company fields using bundled domain validators;
it does not authenticate providers or certify fiscal correctness. Missing or
invalid fiscal fields must be corrected before issuing documents. The setup
wizard no longer assumes RF19.

The `fattura` commands initialize database
access on each new CLI process. No prior assistant or setup process is needed
for an existing database. Running `openfatture` alone starts the interactive
assistant; `openfatture --help` lists the commands.

### Assistant file exports

Without an output path, PDFs are written to `data_dir/exports/fatture/` (invoices)
`data_dir/exports/preventivi/` (quotes) and `data_dir/exports/riepiloghi/`
(yearly summaries), never to the current directory.
When the assistant chooses an output path for PDF or CSV exports, the path is
resolved inside `data_dir/exports`. Absolute paths or `..` segments that would
leave that directory are refused before the tool runs.

An invoice PDF is a courtesy copy: its footer says it has no fiscal value and
that the original is the FatturaPA XML sent through SDI.

### Event listeners

`EVENT_LISTENERS` (comma-separated dotted paths) registers custom listeners on
the global event bus. Payment reconciliation events (`TransactionMatchedEvent`,
`TransactionUnmatchedEvent`) are global events; subscribe to
`openfatture.payment.application.events.PaymentEvent` to receive only those.
The former `PAYMENT_EVENT_LISTENERS` setting was removed.


### Assistant execution timeouts

- `AI_MODEL_TIMEOUT_SECONDS`: positive seconds per model attempt (default `120`).
- `AI_TOOL_TIMEOUT_SECONDS`: positive seconds per tool execution, excluding
  human approval (default `60`). Synchronous domain calls finish cooperatively.

Persistent LangGraph sessions keep per-turn checkpoints and tool receipts in
`data_dir/ai/runtime/`. Conversations are saved in `AI_CHAT_SESSIONS_DIR`, and
the notes the assistant keeps across conversations in `data_dir/ai/memory.json`
(owner-only permissions; manage them with `/memory` and `/forget`). See [AI architecture](AI_ARCHITECTURE.md#durable-local-execution)
for restart, approval and reconciliation behavior.
