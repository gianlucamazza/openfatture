# Data that leaves the computer

OpenFatture keeps invoices, clients, receipts and conversations on your
computer. Four flows can carry data elsewhere. `openfatture status` lists them
under "Dati che lasciano il computer", and `status --json` reports them in
`data_destinations`.

| Flow | What it carries | When | How to keep it local or off |
| --- | --- | --- | --- |
| AI model | The system prompt, the conversation, your saved notes and the results of the tools the assistant uses (client names, VAT numbers, amounts, invoice lines) | Every request to the assistant | `ai_provider = "ollama"` runs the model on your computer |
| Knowledge-base embeddings | The bundled regulatory guides, not your data | When `search_knowledge_base` first indexes them | `OPENFATTURE_RAG_EMBEDDING_PROVIDER=sentence-transformers` (automatic with Ollama) |
| VAT checks (VIES) | The VAT number checked and your own partita IVA as requester | When the assistant runs `check_vat_vies` | `ai_offline = true` |
| SDI (PEC) | The FatturaPA XML of an invoice | Only if `send_invoice_to_sdi` is in `ai_enabled_tools`, and after your confirmation | Off by default |

With Ollama, local embeddings and `ai_offline = true`, nothing leaves the
computer.

## Choosing a model provider

The model provider receives business and possibly personal data (for example
a private client's codice fiscale). Under the GDPR it acts as a processor for
you. Before using a cloud provider for real data, check:

- **A data processing agreement (DPA).** Your provider's terms must include one.
- **Transfers.** For a provider outside the EU, check that it participates in
  the EU-US Data Privacy Framework or uses Standard Contractual Clauses.
- **Retention and training.** API data should not be used to train models,
  and retention should be limited.
- **Region.** Prefer EU processing where the provider offers it.

These are pointers, not legal advice.

## Why the assistant cannot browse the web

An assistant that holds private data, reads untrusted text and can send data
out can be steered by text it reads into sending your data elsewhere. This is
the "lethal trifecta" of prompt injection
([OWASP LLM01](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)).
OpenFatture already reads untrusted text: invoice notes, imported files and SDI
receipts. A generic web search or URL fetch tool would add both untrusted web
content and an outbound channel, because the URL itself can carry data out.
So there is none.

Online capabilities are narrow lookups instead. Each one has a fixed endpoint,
takes a validated identifier and returns typed fields. It has its own risk
class (`lookup`) and is turned off by `ai_offline`. The text a lookup returns
is shown to the model as data, never as instructions.
