# CLI Command Reference

Complete catalogue of the `openfatture` CLI commands and the tasks you can run from the terminal.

> **🎥 Demo videos**
> - [Setup & Configuration](../media/output/scenario_a_onboarding.mp4) (2:30)
> - [Invoice Creation](../media/output/scenario_b_invoice.mp4) (3:30)
> - [AI Assistant](../media/output/scenario_c_ai.mp4) (2:45)
> - [Batch Operations](../media/output/scenario_d_batch.mp4) (2:15)
> - [PEC & SDI](../media/output/scenario_e_pec.mp4) (3:00)

---

## General Structure

- Show global help: `openfatture --help`
- Install shell completion (recommended): `openfatture --install-completion zsh` / `bash`
- Launch the interactive TUI: `openfatture --interactive` or `openfatture interactive`
- Control output format globally: `openfatture --format json ai describe "text"`

Every command group ships with its own `--help`, e.g. `openfatture fattura --help`.

---

## Output Formats

OpenFatture supports multiple output formats for AI commands, making it easy to integrate with scripts, CI/CD pipelines, or other tools.

### Available Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| `rich` (default) | Rich terminal UI with colors, panels, and formatting | Interactive CLI usage |
| `json` | Structured JSON with full metadata | Scripting, API integration, programmatic parsing |
| `markdown` | Formatted Markdown with headers and sections | Documentation, reports, human-readable exports |
| `stream-json` | JSON Lines format for streaming responses | Real-time processing, log ingestion |
| `html` | Styled HTML document with embedded CSS | Email, web display, archival |

### Usage

**Global format flag** (applies to all AI commands):
```bash
openfatture --format json ai describe "consulting"
openfatture --format markdown ai suggest-vat "training"
openfatture --format html ai forecast --months 6
```

**Per-command format** (overrides global):
```bash
openfatture ai describe "consulting" --format json
```

**Backward compatibility** (existing `--json` flag still works):
```bash
openfatture ai describe "consulting" --json  # Same as --format json
```

### Format Priority

When multiple format options are specified, the priority order is:
1. Explicit `--format` on the command itself
2. Legacy `--json` flag on the command
3. Global `--format` flag
4. Default (`rich`)

### Examples

**JSON output** for scripting:
```bash
# Get structured data for parsing
result=$(openfatture --format json ai describe "Backend development" --hours 8)
echo "$result" | jq '.content'
```

**Markdown output** for documentation:
```bash
# Generate invoice description for docs
openfatture --format markdown ai describe "Cloud migration consulting" > docs/services.md
```

**HTML output** for email/reports:
```bash
# Create formatted report
openfatture --format html ai forecast --months 6 > reports/forecast.html
```

**StreamJSON output** for real-time processing:
```bash
# Process streaming responses line-by-line
openfatture --format stream-json ai chat "Analyze my invoices" | while read -r line; do
  echo "$line" | jq '.content'
done
```

### Format Details

**JSON format** includes:
- `content`: AI response text
- `status`: Response status (success/error)
- `provider`: LLM provider used
- `model`: Model name
- `tokens_used`: Total tokens consumed
- `cost_usd`: Estimated cost in USD
- `latency_ms`: Response time

**Markdown format** includes:
- Formatted headers and sections
- Response content
- Metadata table (provider, model, tokens, cost, latency)

**HTML format** includes:
- Complete HTML document with DOCTYPE
- Embedded CSS styling (light/dark mode support)
- Responsive design
- Metadata section (optional)

**StreamJSON format** includes:
- Each chunk as a separate JSON object
- `type`: "chunk", "metadata", "complete", or "error"
- `index`: Chunk sequence number
- `content`: Chunk text
- Final `complete` message with total chunks and status

---

## 1. Initial Setup

| Command | Description | Handy options |
|---------|-------------|---------------|
| `openfatture init` | Creates data folders, initialises the database, and (in interactive mode) prepares `.env`. | `--no-interactive` skips the wizard and uses existing `.env` values. |
| `openfatture config show` | Displays the current configuration (derived from `.env`). | `--json` for structured output. |
| `openfatture config edit` | Opens `.env` in `$EDITOR`, then reloads settings. |  |
| `openfatture config set KEY VALUE` | Updates one or more config values and reloads `.env`. | Accepts `KEY VALUE` and `KEY=VALUE` formats. |
| `openfatture config reload` | Forces a reload of settings from `.env`. |  |

---

## 2. Customer Management

| Command | Purpose | Example |
|---------|---------|---------|
| `openfatture cliente add` | Adds a customer (`--interactive` launches a guided wizard). | `openfatture cliente add "ACME SRL" --piva 12345678901 --sdi ABC1234 --pec acme@pec.it` |
| `openfatture cliente list` | Lists customers (default limit 50). | `openfatture cliente list --limit 20` |
| `openfatture cliente show ID` | Shows full details (addresses, contacts). | `openfatture cliente show 3` |
| `openfatture cliente delete ID` | Removes a customer (blocked if invoices exist). | `openfatture cliente delete 7 --force` |

Tip: run `cliente list` to retrieve IDs before invoicing or batch imports.

---

## 3. Invoice Management

### Creation and updates
- `openfatture fattura crea [--cliente ID] [--pdf]`: interactive wizard to build invoices, add lines, calculate VAT/withholding/stamp duty. Use `--pdf` to render the PDF immediately.
- `openfatture fattura delete ID [--force]`: deletes drafts or unsent invoices.

### Review
- `openfatture fattura list [--stato inviata] [--anno 2025]`: list with filters.
- `openfatture fattura show ID`: detailed breakdown with lines and totals.

### Export
- `openfatture fattura pdf ID [--template professional] [--output path.pdf]`: renders PDF (templates: `minimalist`, `professional`, `branded`).
- `openfatture fattura xml ID [--output path.xml] [--no-validate]`: generates the FatturaPA XML (XSD validation on by default).

### Delivery
- `openfatture fattura invia ID [--pec/--no-pec]`: generates XML and sends it via PEC using the professional HTML template. Ensure PEC and `NOTIFICATION_EMAIL` are set in `.env`.

---

## 4. PEC & Email

| Command | Purpose |
|---------|---------|
| `openfatture pec test` | Verifies PEC credentials and SMTP server by sending a test message. |
| `openfatture email test` | Sends a test email using the professional template to the notification address. |
| `openfatture email preview --template sdi/invio_fattura` | Renders HTML to `/tmp/email_preview.html` with demo data. |
| `openfatture email info` | Displays branding, colours, and available templates. |

If the test fails, double-check `PEC_ADDRESS`, `PEC_PASSWORD`, and `PEC_SMTP_*` in `.env`.

---

## 5. SDI Notifications

| Command | Description | Notes |
|---------|-------------|-------|
| `openfatture notifiche process FILE.xml` | Parses SDI notifications (AT/RC/NS/MC/NE), updates invoice status, and optionally sends an email. | `--no-email` skips automatic alerts. |
| `openfatture notifiche list [--tipo RC]` | Lists processed notifications. | Data comes from the `log_sdi` table. |
| `openfatture notifiche show ID` | Shows the details of a specific notification. | Useful to understand why an invoice was rejected. |

When you download PEC notifications manually, feed them to `notifiche process` to keep the database in sync.

---

## 6. Batch Operations

- `openfatture batch import file.csv [--dry-run] [--no-summary]`: bulk-import invoices. Use `--dry-run` to validate without saving; optionally emails a summary afterwards.
- `openfatture batch export output.csv [--anno 2025] [--stato inviata]`: exports invoices for reporting or migrations.
- `openfatture batch history`: placeholder (currently shows an example). Historical tracking will be finalised in future releases.

See [docs/BATCH_OPERATIONS.md](BATCH_OPERATIONS.md) for CSV formats and best practices.

---

## 7. Reporting

| Command | Output |
|---------|--------|
| `openfatture report iva [--anno 2025] [--trimestre Q1]` | VAT breakdown by rate. |
| `openfatture report clienti [--anno 2025]` | Top clients by revenue. |
| `openfatture report scadenze` | Overdue, due, and upcoming payments with remaining balance and payment status. |

---

## 8. Payment Tracking

| Command | Purpose | Example |
|---------|---------|---------|
| `openfatture payment create-account NAME` | Creates a bank account for transaction import. | `openfatture payment create-account "BCC" --iban IT123...` |
| `openfatture payment list-accounts` | Lists configured bank accounts. |  |
| `openfatture payment import FILE.ofx` | Imports bank transactions from OFX/QFX files. | `openfatture payment import statement.ofx --account 1` |
| `openfatture payment list-transactions` | Shows imported transactions with match status. | `openfatture payment list-transactions --status unmatched` |
| `openfatture payment reconcile` | Runs automatic reconciliation against unpaid invoices. | `openfatture payment reconcile --account 1` |
| `openfatture payment match-transaction TX_ID PAYMENT_ID` | Manually matches a transaction to a payment. | `openfatture payment match-transaction 123 456` |
| `openfatture payment audit [--limit 50]` | Shows payment allocation audit trail. | `openfatture payment audit --payment 123` |
| `openfatture payment stats [--account ID]` | Payment tracking statistics (matched/unmatched). | `openfatture payment stats` |

---

## 9. Events & Audit Log

View and analyze event history and audit logs. All domain events are automatically persisted for compliance and analytics.

### List Events
```bash
# List recent events
openfatture events list

# Filter by event type
openfatture events list --type InvoiceCreatedEvent

# Filter by entity (invoice, client, etc.)
openfatture events list --entity invoice --entity-id 123

# Last 7 days
openfatture events list --last-days 7

# Limit results
openfatture events list --limit 100
```

### Show Event Details
```bash
# View full event details with JSON data
openfatture events show <event-id>
```

### Statistics
```bash
# All-time statistics
openfatture events stats

# Last 30 days
openfatture events stats --last-days 30
```

### Entity Timeline
```bash
# View all events for an invoice
openfatture events timeline invoice 123

# View all events for a client
openfatture events timeline client 5
```

### Search Events
```bash
# Full-text search in event data
openfatture events search "Client A"
openfatture events search "001/2025"
openfatture events search "invoice" --limit 50
```

### List Event Types
```bash
# View all available event types with counts
openfatture events types
```

### Analytics Dashboard
```bash
# Comprehensive analytics dashboard (last 30 days by default)
openfatture events dashboard

# Custom period (last 7 days)
openfatture events dashboard --days 7

# Dashboard includes:
# - Total events, event types, velocity (events/hour)
# - Activity trends (comparing periods)
# - Top event types with ASCII bar charts
# - Entity activity distribution
# - Trend indicators (📈 increasing, 📉 decreasing, ➡️ stable)
```

### Trends Analysis
```bash
# Activity trends for last 30 days
openfatture events trends

# Filter by event type
openfatture events trends --type InvoiceCreatedEvent

# Custom period (last 90 days)
openfatture events trends --days 90
```

**Available Event Types:**
- `InvoiceCreatedEvent` - Invoice creation
- `InvoiceValidatedEvent` - XML validation
- `InvoiceSentEvent` - Sent via PEC to SDI
- `InvoiceDeletedEvent` - Invoice deletion
- `ClientCreatedEvent` - Client creation
- `ClientDeletedEvent` - Client deletion
- `AICommandStartedEvent` - AI command execution
- `AICommandCompletedEvent` - AI command completion
- `BatchImportStartedEvent` - Batch import start
- `BatchImportCompletedEvent` - Batch import completion
- `SDINotificationReceivedEvent` - SDI notification received

---

## 10. AI & Automation

Configure `AI_PROVIDER`, `AI_MODEL`, and `AI_API_KEY` (or Ollama) first. Validate with `openfatture config show`.

### AI Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `openfatture ai describe "text"` | Generates polished invoice line descriptions, reusing relevant examples and operational notes. | `openfatture ai describe "Backend consulting" --hours 8 --rate 75 --tech "Python,FastAPI"` |
| `openfatture ai suggest-vat "service"` | Suggests VAT rate, nature code, and fiscal notes with references to DPR 633/72. | `openfatture ai suggest-vat "Online training" --pa` |
| `openfatture ai forecast [--months 6]` | Cash-flow forecast using Prophet + XGBoost; stores models/metrics; supports `--retrain`. | `openfatture ai forecast --client 12 --retrain` |
| `openfatture ai check ID [--level advanced]` | Analyses the invoice using rules + AI to catch issues before submission. | `openfatture ai check 45 --level standard --verbose` |
| `openfatture ai create-invoice "desc"` | Creates complete invoices using AI workflow orchestration. | `openfatture ai create-invoice "consulenza web" --client 123 --amount 300` |
| `openfatture ai chat ["message"]` | Interactive AI chat assistant for invoice/tax questions. | `openfatture ai chat --stream` (or interactive mode) |
| `openfatture ai rag status` | Displays knowledge-base sources, document counts, and ChromaDB directory. |  |
| `openfatture ai rag index [--source id]` | Indexes or re-indexes the RAG sources defined in the manifest. | `openfatture ai rag index --source tax_guides` |
| `openfatture ai rag search "query"` | Semantic search inside the knowledge base (great for debugging or audits). | `openfatture ai rag search "reverse charge edilizia" --source tax_guides` |

### Output Format Examples

All AI commands support output formatting. Use `--format` to control the output:

```bash
# JSON output for scripting
openfatture --format json ai describe "3 hours consulting"
openfatture ai suggest-vat "training course" --format json

# Markdown output for documentation
openfatture --format markdown ai forecast --months 12 > forecast.md
openfatture ai check 45 --format markdown > compliance_report.md

# HTML output for reports
openfatture --format html ai describe "Migration project" > description.html

# Backward compatibility (--json flag)
openfatture ai describe "consulting" --json
```

**Example JSON output:**
```json
{
  "content": "Consulenza tecnica backend per sviluppo API RESTful...",
  "status": "success",
  "provider": "openai",
  "model": "gpt-4",
  "tokens_used": 450,
  "cost_usd": 0.0045,
  "latency_ms": 850
}
```

**Example Markdown output:**
```markdown
# AI Response

## Response

Consulenza tecnica backend per sviluppo API RESTful...

---

## Metadata

**Provider:** openai
**Model:** gpt-4
**Tokens Used:** 450
**Cost:** $0.0045
**Latency:** 850ms
```

### Notes

`ai forecast` reads models from `MLConfig.model_path` (default `.models/`). If missing, it performs the initial training and generates `cash_flow_*` files. Use `--retrain` to rebuild models after updating your data.

Compliance analysis (`ai check`) remains in beta; when it fails, use `--format json` for easier diagnostics.

> ℹ️ **Tip:** After setting `OPENAI_API_KEY` (or a local embedding provider), run `openfatture ai rag index` to populate the knowledge base. Agents will automatically cite normative sources such as `[1] DPR 633/72 art...`.

---

## 11. Interactive Mode

`openfatture interactive` (or `openfatture --interactive`) launches the Rich-powered TUI with menu navigation:

- Quick access to customers, invoices, and reports
- AI chat with persistent history (`~/.openfatture/ai/sessions`)
- Guided VAT suggestions directly from the menu
- Shortcuts for the most common operations without memorising CLI syntax

---

## 10. Lightning Network Payments

⚡ **Lightning Network integration for instant Bitcoin payments.**

### Prerequisites
- LND (Lightning Network Daemon) running and accessible
- TLS certificate and macaroon authentication configured
- `lightning_enabled=true` in `.env`

### Configuration
```bash
# Enable Lightning
openfatture config set lightning_enabled true

# Configure LND connection
openfatture config set lightning_host "localhost:10009"
openfatture config set lightning_cert_path "/path/to/tls.cert"
openfatture config set lightning_macaroon_path "/path/to/admin.macaroon"

# BTC/EUR conversion (choose one)
openfatture config set lightning_coingecko_enabled true
openfatture config set lightning_cmc_enabled false
```

### Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `openfatture lightning status` | Show Lightning status and configuration | `openfatture lightning status` |
| `openfatture lightning invoice create --fattura-id ID` | Create Lightning invoice from existing invoice | `openfatture lightning invoice create --fattura-id 123` |
| `openfatture lightning channels status` | List Lightning channels and capacity | `openfatture lightning channels status` |
| `openfatture lightning liquidity report` | Generate liquidity analysis report | `openfatture lightning liquidity report` |

### Invoice Creation
```bash
# Create invoice from existing fattura
openfatture lightning invoice create --fattura-id 123

# Create zero-amount invoice (donation)
openfatture lightning invoice create --amount 0 --description "Donazione libera"

# Create with custom expiry (hours)
openfatture lightning invoice create --fattura-id 123 --expiry-hours 48
```

### Channel Management
```bash
# View channel status
openfatture lightning channels status

# Monitor liquidity automatically
openfatture lightning liquidity monitor --start

# Generate detailed liquidity report
openfatture lightning liquidity report
```

### Webhook Integration
Lightning supports real-time webhook notifications for payment events. Configure in your LND node to point to:
```
POST https://your-domain.com/webhook/lightning
```

### Troubleshooting
- **Connection failed**: Check LND host/port and TLS certificate path
- **Authentication error**: Verify macaroon file and permissions
- **No channels**: Ensure LND has active channels with sufficient capacity
- **Rate conversion failed**: Check CoinGecko/CoinMarketCap API keys

---

## Final Tips

- Run `uv run openfatture ...` if you rely on `uv` (recommended). With classic virtual environments, activate the venv and call `openfatture` directly.
- For debugging, add `--verbose` to commands that support it or inspect logs under `~/.openfatture/data`.
- Keep `.env` up to date and back up the database (`openfatture.db` or your PostgreSQL instance) regularly.
