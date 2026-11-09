# Configuration

OpenFatture reads settings from the environment and the local configuration
file. Use the CLI for inspection and simple updates:

```bash
openfatture config show
openfatture config set ai_provider ollama
openfatture config reload
```

## Optional extras

Core install covers billing, SDI, payment reconciliation, PDF, and the
public CLI (`init`, `config`, `status`). Feature stacks are opt-in:

| Extra | Install | Provides |
| --- | --- | --- |
| `ai` | `uv sync --extra ai` | LLM providers, assistant, agents, LangGraph workflows |
| `rag` | `uv sync --extra rag` | ChromaDB + embeddings (includes `ai`) |
| `ml` | `uv sync --extra ml` | Cash-flow forecasting (Prophet / XGBoost; optional) |
| `all` | `uv sync --extra all` | Union of feature extras |
| `dev` | `uv sync --extra dev` | Tests and linters |

Voice STT/TTS and the regulatory web scraper were removed from the product
(see [ARCHITECTURE_REDESIGN.md](ARCHITECTURE_REDESIGN.md)).

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
| `AI_ENABLED_TOOLS` | Comma-separated allowlist of tools the chat/AI agent may use. Default is read-only invoice/client lookups. Transmit tools such as `send_invoice_to_sdi` stay off unless you name them here. The value `all` enables every non-transmit tool; it does **not** enable SDI/PEC send. |
| `AI_TOOLS_REQUIRE_CONFIRMATION` | Default `true`. When true, tools that require confirmation (including every SDI/PEC send) refuse unless a human says yes. An interactive TTY may prompt (default no). `source="human"` with `confirmed=True` is an API for human-facing callers; no built-in UI uses that path yet (there is no TUI). The model cannot self-confirm. Non-interactive sessions refuse and do not transmit. Setting this to `false` skips the prompt but still requires an `AI_ENABLED_TOOLS` opt-in for transmit tools. |

Product credentials written by `openfatture init` use the `AI_*` names above.
The provider factory hydrates `AISettings` from those values (see
`hydrate_ai_settings_from_platform`). Advanced AI-only knobs may use the
`OPENFATTURE_AI_*` prefix; when both are set, `OPENFATTURE_AI_*` wins for that
field.

Sensitive values should be provided through the environment or a protected
local secrets file. Do not commit credentials.

## Provider examples

Cloud provider:

```bash
export AI_PROVIDER=openai
export AI_MODEL=gpt-4-turbo-preview
export AI_API_KEY=...
```

Local provider:

```bash
export AI_PROVIDER=ollama
export AI_MODEL=llama3.2
export AI_BASE_URL=http://localhost:11434
```

After changing environment variables, run:

```bash
openfatture config reload
openfatture status
```

## User profile and assistant confirmations

The setup wizard and `config set` save the user profile to the platform
configuration directory (`~/.config/openfatture/config.toml` on Linux).
Explicit settings, environment variables and the working-directory `.env`
override this profile, in that order. New databases default to the user data
directory; existing configured database URLs are preserved.

Tools marked as requiring confirmation cannot execute without approval from
the calling interface. Noninteractive callers receive `confirmation_required`.
The legacy `confirm=False` argument does not bypass this requirement.

`status --json` reports missing invoice fields separately from delivery
configuration. Readiness describes local configuration, not successful
provider authentication or SDI delivery.

Unknown model prices are marked with `cost_known=false`; their numeric cost
placeholder is not a billing estimate. Use `openfatture --debug assistant`
for diagnostic logs.

## Terminal assistant behavior

`assistant` and `interactive start` share a terminal presentation layer.
Live previews are temporary; the complete Markdown response is printed once
into scrollback. Slash commands support help, session ID, clearing messages
and exit. Input history stays in memory. `NO_COLOR` is respected.

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

Direct `fattura` and `cliente` commands initialize database access on each new
CLI process. No prior assistant or setup process is needed for an existing
database. Running `openfatture` alone displays help and exits successfully.
