# AI Invoice Assistant – Usage Guide

The **Invoice Assistant** agent transforms short prompts into polished invoice line descriptions, including deliverables, skills, duration, and optional risks or upsell suggestions. It leverages past invoices (via RAG) and template prompts to maintain consistent tone and detail.

---

## Quick Start (CLI)

```bash
# Minimal usage
uv run openfatture ai describe "Backend API development – 5h"

# With additional context
uv run openfatture ai describe "Security audit" \
  --hours 8 \
  --rate 90 \
  --tech "Python,FastAPI,PostgreSQL" \
  --project "E-commerce platform" \
  --language en

# JSON output for automation
uv run openfatture ai describe "GDPR consulting" --json
```

Sample response (JSON mode):

```json
{
  "descrizione": "Technical consulting for GDPR compliance",
  "attivita": [
    "Reviewed data processing registers",
    "Assessed DPIA requirements",
    "Produced remediation plan and timeline"
  ],
  "deliverables": [
    "Audit report",
    "Risk analysis table",
    "Remediation backlog"
  ],
  "ore": 6.0,
  "tariffa": 95,
  "totale": 570.0,
  "skills": ["Privacy", "RegTech", "Risk management"],
  "suggestioni": ["Propose quarterly compliance review"]
}
```

---

## Programmatic Usage

```python
from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.domain.agent import AgentConfig
from openfatture.ai.domain.context import InvoiceContext
from openfatture.ai.providers import create_provider

provider = create_provider()

agent = InvoiceAssistantAgent(
    config=AgentConfig(
        name="invoice_assistant",
        description="Generate invoice descriptions",
        model="gpt-4-turbo-preview",
        temperature=0.4,
        max_tokens=550,
    ),
    provider=provider,
)

context = InvoiceContext(
    user_input="Backend maintenance retainer",
    servizio_base="Software maintenance",
    ore_lavorate=12.0,
    tariffa_oraria=80,
    tecnologie=["Python", "FastAPI", "PostgreSQL"],
    richieste_cliente=["Stabilise performance", "Reduce API latency"],
)

response = await agent.execute(context)
print(response.parsed_output.dict())
```

---

## Output Structure

- `descrizione`: main paragraph for the invoice line.
- `attivita`: list of key activities performed.
- `deliverables`: tangible outputs delivered to the client.
- `ore` / `tariffa` / `totale`: numeric values (hours, rate, total) when provided.
- `skills`: technologies or competencies highlighted.
- `suggestioni`: optional follow-up or upsell suggestions.
- `note_rischi`: optional risks or caveats when applicable.

Names remain in Italian to mirror the OpenFatture data model.

---

## Knowledge Base Integration

When `openfatture ai rag index` has been run, the agent automatically:

- Retrieves similar past invoices to align tone and structure.
- Reuses domain-specific terminology.
- Highlights missing information (e.g. hours or deliverables not provided).
- Adds invoice notes consistent with company guidelines.

---

## Tips & Best Practices

1. Provide hours and hourly rate for accurate totals.
2. Add technologies and client requests to tailor the narrative.
3. Use `--language it` to produce Italian descriptions when required.
4. Review the output before sending to clients; adjust wording as needed.
5. Store responses (JSON) to populate ERP systems or re-use in templates.

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `"servizio_base" is required` | Missing base service name | Provide `--service` or set `servizio_base` in the context. |
| Generic descriptions | Not enough context | Add activities, technologies, customer goals. |
| Provider timeout | Model too slow or unavailable | Lower `max_tokens` / `temperature`, or switch provider. |

---

## References

- `docs/AI_ARCHITECTURE.md` – detailed architecture
- `docs/KB_INTEGRATION_BLUEPRINT.md` – knowledge base plan
- `docs/CLI_REFERENCE.md` – complete command reference
