# Configuration

OpenFatture reads settings from the environment and the local configuration
file. Use the CLI for inspection and simple updates:

```bash
openfatture config show
openfatture config set ai_provider ollama
openfatture config reload
```

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
| `AI_PROVIDER` | Configured assistant provider |
| `AI_MODEL` | Provider model name |
| `AI_API_KEY` | Provider credential |
| `AI_BASE_URL` | Local provider endpoint, such as Ollama |

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
