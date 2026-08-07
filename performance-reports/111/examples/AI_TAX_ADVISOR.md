# AI Tax Advisor – Usage Guide

The **Tax Advisor** agent suggests the correct VAT treatment for Italian electronic invoices. It analyses the service description, client type, and optional context (ATECO code, amount, PA flag) and returns a structured recommendation with regulatory references.

---

## Prerequisites

```bash
uv sync --all-extras
export OPENFATTURE_AI_PROVIDER=anthropic   # or openai / ollama
export OPENFATTURE_AI_MODEL=claude-3-5-sonnet-20241022
export OPENFATTURE_AI_ANTHROPIC_API_KEY=sk-ant-...
uv run openfatture ai rag index --source tax_guides   # optional but recommended
```

---

## CLI Examples

```bash
# Basic suggestion
uv run openfatture ai suggest-vat "IT consulting services"

# Public Administration
uv run openfatture ai suggest-vat "Professional training" --pa

# Foreign customer (extra-EU)
uv run openfatture ai suggest-vat "Software licensing" --estero --paese US

# Complete context
uv run openfatture ai suggest-vat "Construction site cleaning" \
  --categoria "Construction" \
  --importo 5000 \
  --ateco 81.21.00 \
  --json
```

The response contains:

```json
{
  "aliquota_iva": 22,
  "codice_natura": null,
  "reverse_charge": false,
  "split_payment": false,
  "regime_speciale": null,
  "riferimento_normativo": "Art. 17 DPR 633/72",
  "note_fattura": "Standard VAT treatment",
  "confidence": 0.92
}
```

---

## Knowledge Base Coverage

| Topic | Details |
|-------|---------|
| VAT rates | 22% (standard), 10% (reduced), 5% (super-reduced), 4% (minimum), 0% (exempt) |
| VAT nature codes | N1–N7 with sub-codes (reverse charge, exports, exemptions) |
| Special regimes | Reverse charge (art. 17), split payment (art. 17-ter), flat-tax regime (L. 190/2014) |
| Inputs | service description, customer type (B2B/PA/foreign), amount, ATECO, additional notes |
| Outputs | VAT rate, nature code, reverse charge flag, split payment flag, recommended invoice note, citations |

---

## Programmatic Usage

```python
from openfatture.ai.agents.tax_advisor import TaxAdvisorAgent
from openfatture.ai.domain.agent import AgentConfig
from openfatture.ai.domain.context import TaxAdvisorContext
from openfatture.ai.providers import create_provider

provider = create_provider()

agent = TaxAdvisorAgent(
    config=AgentConfig(
        name="tax_advisor",
        description="Suggest Italian VAT treatments",
        model="claude-3-5-sonnet-20241022",
        temperature=0.1,
        max_tokens=600,
        tools_enabled=False,
    ),
    provider=provider,
)

context = TaxAdvisorContext(
    tipo_servizio="IT consulting",
    importo=1500,
    categoria="Professional services",
    cliente_pa=False,
    cliente_estero=True,
    paese_cliente="US",
)

result = await agent.execute(context)
print(result.parsed_output.dict())
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `"tipo_servizio" is required` | Missing service description | Provide a meaningful description (`--categoria` and `--ateco` improve accuracy). |
| Low confidence (<0.6) | Ambiguous input | Add more context (category, PA foreign flags, amount). |
| `Provider error: API key not set` | Missing credentials | Export `OPENFATTURE_AI_<PROVIDER>_API_KEY`. |

---

## Best Practices

1. Keep the knowledge base indexed (`openfatture ai rag index`).
2. Provide the ATECO code whenever possible.
3. For Public Administration customers add `--pa` to enable split payment checks.
4. Review suggested invoice notes before sending to SDI.
5. Monitor confidence scores; low values should be reviewed manually.

---

## References

- DPR 633/1972 (Italian VAT law)
- Agenzia delle Entrate – VAT nature codes and rates
- OpenFatture documentation (`docs/PAYMENT_TRACKING.md`, `docs/KB_INTEGRATION_BLUEPRINT.md`)
