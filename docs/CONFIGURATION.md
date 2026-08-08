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
