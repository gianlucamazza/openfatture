# AI Chat Assistant - Complete Guide

The **AI Chat Assistant** is an interactive conversational AI for OpenFatture that helps you manage invoices, query clients, and get business insights through natural language conversations.

## Features

- 💬 **Natural Language Conversations** - Ask questions in plain Italian or English
- 🛠️ **Function Calling** - AI can search invoices, query clients, and retrieve statistics
- 💾 **Session Persistence** - Resume conversations where you left off
- 📊 **Real-time Statistics** - Track tokens, costs, and conversation metrics
- 🎨 **Rich UI** - Beautiful markdown rendering in the terminal
- ⌨️ **Command System** - Powerful slash commands for session management
- 🔄 **Multi-Provider Support** - Works with OpenAI, Anthropic, or local Ollama

---

## Quick Start

### 1. Configuration

Set your AI provider and API key in `.env`:

```bash
# For Anthropic Claude (recommended)
AI_PROVIDER=anthropic
AI_MODEL=claude-3-5-sonnet-20241022
AI_API_KEY=sk-ant-your-api-key-here

# For OpenAI GPT
# AI_PROVIDER=openai
# AI_MODEL=gpt-4o
# AI_API_KEY=sk-your-openai-key-here

# For local Ollama (FREE)
# AI_PROVIDER=ollama
# AI_MODEL=llama3.2
# AI_BASE_URL=http://localhost:11434
```

### 2. Start the Chat

**Interactive Mode** (Recommended):
```bash
openfatture -i
# Navigate to: 8. AI Assistant → 1. Chat
```

**Direct Access** (if configured):
```bash
# Not yet available as standalone command
# Use interactive mode for now
```

---

## Using the Chat Assistant

### Example Conversations

**1. Query Invoice Statistics**
```
Tu: Quante fatture ho emesso quest'anno?

AI: Lasciami controllare le statistiche dell'anno corrente...

[Tool call: get_invoice_stats]

Quest'anno hai emesso 42 fatture per un totale di €125,430.00.

Ecco la ripartizione per stato:
- Da inviare: 3 fatture
- Inviate: 35 fatture
- Accettate: 4 fatture

Vuoi maggiori dettagli su qualche categoria specifica?
```

**2. Search Invoices**
```
Tu: Cerca fatture del cliente Rossi

AI: Cerco le fatture per il cliente Rossi...

[Tool call: search_clients(query="Rossi")]
[Tool call: search_invoices(cliente_id=5)]

Ho trovato 5 fatture per Mario Rossi SRL:

1. Fattura 001/2025 - €1,500.00 (Inviata)
2. Fattura 045/2024 - €2,200.00 (Accettata)
3. Fattura 038/2024 - €1,800.00 (Accettata)
4. Fattura 022/2024 - €2,500.00 (Accettata)
5. Fattura 015/2024 - €1,200.00 (Accettata)

Vuoi vedere i dettagli di una fattura specifica?
```

**3. Get Recent Invoices**
```
Tu: Mostrami le ultime 5 fatture

AI: Ecco le ultime 5 fatture emesse:

[Tool call: search_invoices(limit=5)]

1. **Fattura 003/2025** - Rossi SRL - €1,500.00 (Da inviare)
   Data: 15/01/2025

2. **Fattura 002/2025** - Bianchi & C. - €3,200.00 (Inviata)
   Data: 10/01/2025

3. **Fattura 001/2025** - Verdi SpA - €2,800.00 (Accettata)
   Data: 05/01/2025

4. **Fattura 125/2024** - Neri SAS - €1,900.00 (Accettata)
   Data: 28/12/2024

5. **Fattura 124/2024** - Ferrari Ltd - €4,500.00 (Accettata)
   Data: 20/12/2024

Vuoi vedere i dettagli di una specifica fattura?
```

**4. Client Information**
```
Tu: Dammi informazioni sul cliente Bianchi

AI: Cerco i dati del cliente Bianchi...

[Tool call: search_clients(query="Bianchi")]
[Tool call: get_client_details(cliente_id=3)]

**Bianchi & C. SNC**
- P.IVA: 12345678901
- Codice Fiscale: 12345678901
- Indirizzo: Via Roma 123, 20100 Milano (MI)
- Email: info@bianchiec.it
- PEC: bianchiec@pec.it

**Statistiche:**
- Totale fatture: 12
- Importo totale fatturato: €38,400.00
- Media per fattura: €3,200.00
- Ultima fattura: 002/2025 (€3,200.00)

Vuoi vedere l'elenco completo delle fatture per questo cliente?
```

---

## Available Tools

The Chat Assistant has access to 6 built-in tools:

### Invoice Tools

**1. search_invoices**
- Search invoices by number, year, status, or client
- Supports filtering and pagination

**2. get_invoice_details**
- Get complete details of a specific invoice
- Includes lines, amounts, and client info

**3. get_invoice_stats**
- Get statistics about invoices
- Breakdown by status, year totals

### Client Tools

**4. search_clients**
- Search clients by name, P.IVA, or Codice Fiscale
- Fuzzy matching support

**5. get_client_details**
- Get complete client information
- Includes contact details and invoice history

**6. get_client_stats**
- Get statistics about all clients
- Total count, top clients, activity breakdown

---

## Command System

The Chat Assistant supports powerful slash commands:

### Session Commands

**`/help`** - Show help message with command list
```
Tu: /help
AI: [Shows complete help with examples]
```

**`/stats`** - Show session statistics
```
Tu: /stats
AI: [Shows session ID, messages, tokens, cost, tools used]
```

**`/tools`** - Show available tools
```
Tu: /tools
AI: [Lists all 6 available tools with descriptions]
```

### Save & Export

**`/save`** - Save current session
```
Tu: /save
AI: ✓ Sessione salvata: cb851a65...
```

**`/export`** - Export conversation to file
```
Tu: /export
AI: Formato di export:
    1. Markdown
    2. JSON
Tu: 1
AI: ✓ Esportato in: ~/.openfatture/ai/sessions/cb851a65-export.md
```

### Utility Commands

**`/clear`** - Clear chat messages (keeps session)
```
Tu: /clear
AI: Vuoi davvero cancellare tutti i messaggi? (y/n)
Tu: y
AI: ✓ Chat pulita
```

**`/exit`** or **`/quit`** - Exit chat
```
Tu: /exit
AI: [Shows session summary and goodbye message]
```

---

## Session Management

### Auto-Save

Sessions are automatically saved after each message when `AI_CHAT_AUTO_SAVE=true` (default).

### Resume Sessions

Sessions are stored in `~/.openfatture/ai/sessions/` and can be resumed:

```bash
# Sessions are automatically listed in interactive mode
# Select "Resume Previous Session" to continue
```

### Export Formats

**Markdown:**
```markdown
# Chat Session: cb851a65-3af8-4598-9f84-6d5e8b9c7a2f

**Date:** 2025-10-10
**Messages:** 12
**Tokens:** 3,456
**Cost:** $0.0234

## Conversation

### User
Quante fatture ho emesso quest'anno?

### AI
Quest'anno hai emesso 42 fatture...
```

**JSON:**
```json
{
  "session_id": "cb851a65-3af8-4598-9f84-6d5e8b9c7a2f",
  "created_at": "2025-10-10T14:23:45Z",
  "messages": [
    {
      "role": "user",
      "content": "Quante fatture ho emesso quest'anno?",
      "timestamp": "2025-10-10T14:23:45Z"
    },
    {
      "role": "assistant",
      "content": "Quest'anno hai emesso 42 fatture...",
      "timestamp": "2025-10-10T14:23:52Z",
      "provider": "anthropic",
      "model": "claude-3-5-sonnet-20241022",
      "tokens": 234,
      "cost": 0.00156
    }
  ],
  "metadata": {
    "total_tokens": 3456,
    "total_cost_usd": 0.0234
  }
}
```

---

## Tips & Best Practices

### 1. Be Specific

❌ **Vague:** "Dimmi qualcosa sulle fatture"
✅ **Specific:** "Mostrami le fatture da inviare di questo mese"

### 2. Use Follow-Up Questions

The Chat Assistant remembers context:
```
Tu: Cerca fatture del 2024
AI: [Shows results]
Tu: Filtra solo quelle da inviare
AI: [Filters previous results]
```

### 3. Save Important Sessions

Use `/save` for conversations you might want to reference later:
```
Tu: /save
AI: ✓ Sessione salvata
```

### 4. Check Your Usage

Monitor tokens and costs with `/stats`:
```
Tu: /stats
AI: Tokens: 1,234 | Cost: $0.0123
```

### 5. Use Natural Language

The AI understands Italian business terminology:
- "fatture scadute" → overdue invoices
- "clienti attivi" → active clients
- "fatturato anno corrente" → current year revenue

---

## Configuration Options

All settings can be configured via environment variables:

```bash
# Provider selection
AI_PROVIDER=anthropic  # openai, anthropic, ollama
AI_MODEL=claude-3-5-sonnet-20241022
AI_API_KEY=sk-ant-your-key

# Generation parameters
AI_TEMPERATURE=0.7  # 0.0 (deterministic) to 2.0 (creative)
AI_MAX_TOKENS=2000

# Chat features
AI_CHAT_ENABLED=true
AI_CHAT_AUTO_SAVE=true
AI_CHAT_MAX_MESSAGES=100
AI_CHAT_MAX_TOKENS=8000

# Tools
AI_TOOLS_ENABLED=true
AI_ENABLED_TOOLS=search_invoices,get_invoice_details,get_invoice_stats,search_clients,get_client_details,get_client_stats
AI_TOOLS_REQUIRE_CONFIRMATION=true
```

---

## Cost Optimization

### Provider Comparison

| Provider | Model | Cost (per 1M tokens) | Best For |
|----------|-------|----------------------|----------|
| **Anthropic** | Claude 3.5 Sonnet | $3.00 input / $15.00 output | Best quality/price |
| **Anthropic** | Claude 3.5 Haiku | $0.25 input / $1.25 output | Fast & cheap |
| **OpenAI** | GPT-4o | $2.50 input / $10.00 output | Excellent quality |
| **OpenAI** | GPT-4o-mini | $0.15 input / $0.60 output | Cost-effective |
| **Ollama** | Llama 3.2 | **FREE** (local) | Privacy, development |

### Tips to Reduce Costs

1. **Use Haiku for simple queries**
   ```bash
   AI_MODEL=claude-3-5-haiku-20241022
   ```

2. **Use Ollama for development**
   ```bash
   ollama serve
   AI_PROVIDER=ollama
   AI_MODEL=llama3.2
   ```

3. **Clear context when switching topics**
   ```
   Tu: /clear
   ```

4. **Limit session length**
   ```bash
   AI_CHAT_MAX_MESSAGES=50  # Default 100
   ```

---

## Troubleshooting

### Chat Not Appearing in Menu

**Problem:** "AI Assistant" menu item missing

**Solution:**
```bash
# Check if AI is configured
grep AI_PROVIDER .env

# If not configured, add:
AI_PROVIDER=anthropic
AI_API_KEY=sk-ant-your-key
```

### Error: "Provider not configured"

**Problem:** API key not set

**Solution:**
```bash
# Set your API key
export AI_API_KEY=sk-ant-your-api-key-here

# Or add to .env:
echo "AI_API_KEY=sk-ant-your-key" >> .env
```

### Error: "Tool execution failed"

**Problem:** Database connection or tool error

**Solution:**
1. Check database is initialized: `openfatture init`
2. Verify data exists: `openfatture cliente list`
3. Check logs for details

### Slow Responses

**Problem:** Chat takes too long to respond

**Solutions:**
1. Use faster model:
   ```bash
   AI_MODEL=claude-3-5-haiku-20241022  # Anthropic
   # or
   AI_MODEL=gpt-4o-mini  # OpenAI
   ```

2. Use local Ollama:
   ```bash
   ollama serve
   AI_PROVIDER=ollama
   AI_MODEL=llama3.2
   ```

3. Reduce max tokens:
   ```bash
   AI_MAX_TOKENS=1000  # Default 2000
   ```

### Session Not Saving

**Problem:** Sessions not persisting

**Solution:**
```bash
# Enable auto-save
AI_CHAT_AUTO_SAVE=true

# Check sessions directory exists
mkdir -p ~/.openfatture/ai/sessions

# Or set custom directory:
AI_CHAT_SESSIONS_DIR=/path/to/sessions
```

---

## Advanced Usage

### Programmatic Access

Use the Chat Assistant programmatically in your Python code:

```python
import asyncio
from openfatture.cli.ui.chat import start_interactive_chat

# Start chat programmatically
asyncio.run(start_interactive_chat())

# Or with specific session
asyncio.run(start_interactive_chat(session_id="cb851a65-..."))
```

### Custom Tools

Add your own tools to the Chat Assistant:

```python
from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.ai.tools.registry import ToolRegistry

# Define custom tool
def my_custom_tool(param: str) -> dict:
    return {"result": f"Processed: {param}"}

# Create tool definition
custom_tool = Tool(
    name="my_custom_tool",
    description="Does something custom",
    category="custom",
    parameters=[
        ToolParameter(
            name="param",
            type=ToolParameterType.STRING,
            description="Input parameter",
            required=True
        )
    ],
    func=my_custom_tool
)

# Register tool
registry = ToolRegistry()
registry.register(custom_tool)
```

### Context Enrichment

Customize the data injected into conversations:

```python
from openfatture.ai.context.enrichment import enrich_chat_context
from openfatture.ai.domain.context import ChatContext

context = ChatContext(user_input="Hello")
enriched_context = enrich_chat_context(context)

# Now includes:
# - current_year_stats
# - recent_invoices_summary
# - recent_clients_summary
```

---

## Next Steps

- 📖 Read the [AI Architecture Documentation](../docs/AI_ARCHITECTURE.md)
- 🤖 Try the [Invoice Assistant](AI_INVOICE_ASSISTANT.md)
- 💡 Try the [Tax Advisor](AI_TAX_ADVISOR.md)
- 🔧 Explore [Configuration Options](../docs/CONFIGURATION.md)
- 🤝 Contribute: [GitHub Repository](https://github.com/venerelabs/openfatture)

---

## Support

- 📚 Documentation: [docs/](../docs/)
- 💬 Community: [GitHub Discussions](https://github.com/venerelabs/openfatture/discussions)
- 🐛 Bug Reports: [GitHub Issues](https://github.com/venerelabs/openfatture/issues)
- 📧 Email: info@gianlucamazza.it

---

**Last Updated:** October 10, 2025
**OpenFatture Version:** 0.1.0
**AI Module:** Phase 4.2 - Chat Assistant
