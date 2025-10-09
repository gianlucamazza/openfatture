# Invoice Assistant - Quick Start Guide

The **Invoice Assistant** is an AI-powered agent that automatically generates professional, detailed Italian invoice descriptions from brief service summaries. It's perfect for consultants, freelancers, and businesses who need to create FatturaPA-compliant electronic invoices.

## Features

- 🤖 **AI-Powered**: Uses GPT-5, Claude 4.5, or local Ollama models
- 📝 **Professional Output**: Generates detailed, structured descriptions in Italian
- ✅ **FatturaPA Compliant**: Respects 1000-character limit and Italian invoice standards
- 🎯 **Structured Data**: Returns JSON with deliverables, skills, and notes
- 💰 **Cost Tracking**: Monitors token usage and estimated costs
- 🔄 **Batch Processing**: Generate multiple descriptions efficiently

## Quick Start

### 1. Installation

The Invoice Assistant is included in the OpenFatture AI module:

```bash
# Already installed if you have openfatture
pip install openfatture
```

### 2. Configuration

Set your AI provider and API key as environment variables:

#### Option A: OpenAI (GPT-5)

```bash
export OPENFATTURE_AI_PROVIDER=openai
export OPENFATTURE_AI_OPENAI_API_KEY=sk-...
```

#### Option B: Anthropic (Claude 4.5)

```bash
export OPENFATTURE_AI_PROVIDER=anthropic
export OPENFATTURE_AI_ANTHROPIC_API_KEY=sk-ant-...
```

#### Option C: Ollama (Local, Free)

```bash
# Start Ollama server first
ollama serve

# Configure OpenFatture
export OPENFATTURE_AI_PROVIDER=ollama
export OPENFATTURE_AI_OLLAMA_MODEL=llama3.2
```

### 3. CLI Usage

The simplest way to use the Invoice Assistant is via CLI:

```bash
# Basic usage
openfatture ai describe "3 ore consulenza web"

# With hours and technologies
openfatture ai describe "sviluppo backend API" \
  --hours 8 \
  --tech "Python,FastAPI,PostgreSQL"

# With project context
openfatture ai describe "audit sicurezza" \
  --hours 16 \
  --rate 150 \
  --project "Portale Aziendale"

# JSON output for scripting
openfatture ai describe "migrazione database" \
  --hours 4 \
  --json
```

### 4. Programmatic Usage

Use the agent directly in your Python code:

```python
import asyncio
from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.domain.context import InvoiceContext
from openfatture.ai.providers.factory import create_provider

async def generate_description():
    # Create provider (uses env config)
    provider = create_provider()

    # Create agent
    agent = InvoiceAssistantAgent(provider=provider)

    # Create context
    context = InvoiceContext(
        user_input="sviluppo API REST",
        servizio_base="sviluppo API REST",
        ore_lavorate=8.0,
        tariffa_oraria=100.0,
        tecnologie=["Python", "FastAPI", "PostgreSQL"],
        deliverables=["API REST", "Documentazione", "Tests"]
    )

    # Execute
    response = await agent.execute(context)

    # Get structured output
    if response.metadata.get("is_structured"):
        model = response.metadata["parsed_model"]
        print(model["descrizione_completa"])
        print(f"Deliverables: {model['deliverables']}")
        print(f"Skills: {model['competenze']}")

asyncio.run(generate_description())
```

## Output Format

The agent returns structured JSON output with the following fields:

```json
{
  "descrizione_completa": "Detailed professional description in Italian (max 1000 chars)",
  "deliverables": ["List", "of", "deliverables"],
  "competenze": ["Technical", "skills", "used"],
  "durata_ore": 8.0,
  "note": "Additional notes or context"
}
```

## Examples

### Example 1: Web Consulting

**Input:**
```
3 ore consulenza web
```

**Output:**
```
Consulenza professionale per sviluppo web e architettura software

Attività svolte:
- Analisi dei requisiti funzionali e non funzionali del progetto
- Progettazione dell'architettura applicativa e definizione stack tecnologico
- Sviluppo di componenti front-end con framework moderni
- Implementazione API REST con autenticazione sicura
- Testing e debugging del codice sviluppato
- Documentazione tecnica delle scelte architetturali

Durata: 3 ore
```

### Example 2: Backend Development

**Input:**
```bash
openfatture ai describe "sviluppo backend API" \
  --hours 8 \
  --tech "Python,FastAPI,PostgreSQL,Docker"
```

**Output:**
```
Sviluppo backend e implementazione servizi API RESTful

Attività svolte:
- Design e implementazione endpoints API secondo specifiche REST
- Integrazione con database PostgreSQL tramite ORM
- Implementazione sistema di autenticazione con JWT
- Validazione input e gestione errori con middleware dedicati
- Containerizzazione applicazione con Docker
- Unit testing con coverage >80% del codice
- Generazione documentazione API OpenAPI/Swagger

Deliverables: Codice backend, API REST, Documentazione OpenAPI, Docker images
Competenze: Python, FastAPI, PostgreSQL, Docker, JWT
Durata: 8 ore
```

### Example 3: Security Audit

**Input:**
```bash
openfatture ai describe "audit sicurezza applicazione" \
  --hours 16 \
  --tech "OWASP,Penetration Testing,Security Analysis"
```

**Output:**
```
Audit di sicurezza applicativa e penetration testing

Attività svolte:
- Analisi statica del codice sorgente (SAST)
- Scansione vulnerabilità dipendenze e librerie
- Test di penetrazione manuale su autenticazione e autorizzazioni
- Verifica conformità OWASP Top 10
- Valutazione configurazione server e infrastruttura
- Redazione report dettagliato con classificazione rischi
- Raccomandazioni per remediation con priorità

Deliverables: Report audit, Lista vulnerabilità, Piano remediation, Best practices
Competenze: OWASP, Penetration Testing, Security Analysis
Durata: 16 ore
```

## Advanced Usage

### Batch Processing

Generate multiple descriptions efficiently:

```python
from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.domain.context import InvoiceContext
from openfatture.ai.providers.factory import create_provider

async def batch_generate():
    provider = create_provider()
    agent = InvoiceAssistantAgent(provider=provider)

    services = [
        {"servizio": "formazione team", "ore": 6.0},
        {"servizio": "code review", "ore": 4.0},
        {"servizio": "migrazione DB", "ore": 5.0}
    ]

    for service in services:
        context = InvoiceContext(
            user_input=service["servizio"],
            servizio_base=service["servizio"],
            ore_lavorate=service["ore"]
        )
        response = await agent.execute(context)
        # Process response...

    # Get aggregate metrics
    metrics = agent.get_metrics()
    print(f"Total cost: ${metrics['total_cost_usd']:.4f}")
```

### Custom Configuration

Override default settings per request:

```python
from openfatture.ai.config import AISettings
from openfatture.ai.providers.factory import create_provider

# Custom settings
settings = AISettings(
    provider="anthropic",
    anthropic_model="claude-4.5-haiku",  # Faster, cheaper
    temperature=0.5,  # More deterministic
    max_tokens=500
)

provider = create_provider(settings=settings)
agent = InvoiceAssistantAgent(provider=provider)
```

### Error Handling

The agent validates input and handles errors gracefully:

```python
response = await agent.execute(context)

if response.status.value == "error":
    print(f"Error: {response.error}")
    # Handle error...
else:
    # Process successful response
    model = response.metadata["parsed_model"]
```

## Cost Optimization

### Provider Comparison (per 1M tokens)

| Provider | Model | Input | Output | Best For |
|----------|-------|-------|--------|----------|
| OpenAI | GPT-5 | $5.00 | $15.00 | Highest quality |
| OpenAI | GPT-5-mini | $0.20 | $0.80 | Cost-effective |
| Anthropic | Claude 4.5 Sonnet | $2.50 | $12.50 | Balanced |
| Anthropic | Claude 4.5 Haiku | $0.20 | $1.00 | Fast & cheap |
| Ollama | Llama 3.2 | Free | Free | Local, private |

### Tips to Reduce Costs

1. **Use smaller models for simple descriptions**:
   ```bash
   export OPENFATTURE_AI_OPENAI_MODEL=gpt-5-mini
   ```

2. **Set budget limits** in configuration:
   ```bash
   export OPENFATTURE_AI_MAX_COST_PER_REQUEST_USD=0.10
   export OPENFATTURE_AI_DAILY_BUDGET_USD=5.00
   ```

3. **Use local Ollama** for development and testing (free)

4. **Batch similar requests** to share context and reduce tokens

## Configuration Options

All settings can be configured via environment variables:

```bash
# Provider selection
export OPENFATTURE_AI_PROVIDER=openai  # openai, anthropic, ollama

# Model selection (per provider)
export OPENFATTURE_AI_OPENAI_MODEL=gpt-5
export OPENFATTURE_AI_ANTHROPIC_MODEL=claude-4.5-sonnet
export OPENFATTURE_AI_OLLAMA_MODEL=llama3.2

# Generation parameters
export OPENFATTURE_AI_TEMPERATURE=0.7  # 0.0-2.0
export OPENFATTURE_AI_MAX_TOKENS=800

# Cost controls
export OPENFATTURE_AI_MAX_COST_PER_REQUEST_USD=0.50
export OPENFATTURE_AI_DAILY_BUDGET_USD=10.00

# Features
export OPENFATTURE_AI_STREAMING_ENABLED=true
export OPENFATTURE_AI_CACHING_ENABLED=true
export OPENFATTURE_AI_METRICS_ENABLED=true
```

## Troubleshooting

### Error: "API key not configured"

Make sure you've set the correct environment variable:
```bash
export OPENFATTURE_AI_OPENAI_API_KEY=sk-...
# or
export OPENFATTURE_AI_ANTHROPIC_API_KEY=sk-ant-...
```

### Error: "servizio_base è richiesto"

The service description cannot be empty:
```bash
# ❌ Wrong
openfatture ai describe ""

# ✅ Correct
openfatture ai describe "consulenza IT"
```

### Low Quality Descriptions

Try increasing temperature or using a better model:
```bash
export OPENFATTURE_AI_TEMPERATURE=0.8
export OPENFATTURE_AI_OPENAI_MODEL=gpt-5  # Instead of gpt-5-mini
```

### Ollama Connection Failed

Make sure Ollama server is running:
```bash
ollama serve
# In another terminal:
ollama run llama3.2
```

## Integration with OpenFatture

The Invoice Assistant integrates seamlessly with OpenFatture invoice creation:

```python
from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.domain.context import InvoiceContext
from openfatture.ai.providers.factory import create_provider
from openfatture.storage.database import get_db_session
from openfatture.core.fatture.service import FatturaService

async def create_invoice_with_ai():
    # Generate description with AI
    provider = create_provider()
    agent = InvoiceAssistantAgent(provider=provider)

    context = InvoiceContext(
        user_input="consulenza web",
        servizio_base="consulenza web",
        ore_lavorate=8.0,
        tariffa_oraria=100.0
    )

    response = await agent.execute(context)
    model = response.metadata["parsed_model"]

    # Create invoice
    session = get_db_session()
    service = FatturaService(session)

    fattura = service.crea_fattura(
        cliente_id=1,
        descrizione=model["descrizione_completa"],
        quantita=model["durata_ore"],
        prezzo_unitario=100.0,
        aliquota_iva=22.0
    )

    print(f"Invoice created: {fattura.numero}")
```

## Next Steps

- 📖 Read the [AI Architecture Documentation](../docs/AI_ARCHITECTURE.md)
- 🧪 Run the [examples](ai_invoice_assistant.py)
- 🔧 Explore other agents: Tax Advisor, Cash Flow Predictor, Compliance Checker
- 🤝 Contribute: [GitHub Repository](https://github.com/venerelabs/openfatture)

## Support

- 📚 Documentation: [docs/](../docs/)
- 💬 Issues: [GitHub Issues](https://github.com/venerelabs/openfatture/issues)
- 🐛 Bug Reports: Use the issue tracker
- 💡 Feature Requests: Open a discussion

---

**Last Updated**: October 2025
**OpenFatture Version**: 0.1.0
**AI Module**: Phase 4.2 - Invoice Assistant
