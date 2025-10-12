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

Every command group ships with its own `--help`, e.g. `openfatture fattura --help`.

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

## 8. AI & Automation

Configure `AI_PROVIDER`, `AI_MODEL`, and `AI_API_KEY` (or Ollama) first. Validate with `openfatture config show`.

| Command | Purpose | Example |
|---------|---------|---------|
| `openfatture ai describe "text"` | Generates polished invoice line descriptions, reusing relevant examples and operational notes. | `openfatture ai describe "Backend consulting" --hours 8 --rate 75 --tech "Python,FastAPI"` |
| `openfatture ai suggest-vat "service"` | Suggests VAT rate, nature code, and fiscal notes with references to DPR 633/72. | `openfatture ai suggest-vat "Online training" --pa` |
| `openfatture ai forecast [--months 6]` | Cash-flow forecast using Prophet + XGBoost; stores models/metrics; supports `--retrain`. | `openfatture ai forecast --client 12 --retrain` |
| `openfatture ai check ID [--level advanced]` | Analyses the invoice using rules + AI to catch issues before submission. | `openfatture ai check 45 --level standard --verbose` |
| `openfatture ai rag status` | Displays knowledge-base sources, document counts, and ChromaDB directory. |  |
| `openfatture ai rag index [--source id]` | Indexes or re-indexes the RAG sources defined in the manifest. | `openfatture ai rag index --source tax_guides` |
| `openfatture ai rag search "query"` | Semantic search inside the knowledge base (great for debugging or audits). | `openfatture ai rag search "reverse charge edilizia" --source tax_guides` |

`ai forecast` reads models from `MLConfig.model_path` (default `.models/`). If missing, it performs the initial training and generates `cash_flow_*` files. Use `--retrain` to rebuild models after updating your data.

Compliance analysis (`ai check`) remains in beta; when it fails, use `--json` for easier diagnostics.

> ℹ️ **Tip:** After setting `OPENAI_API_KEY` (or a local embedding provider), run `openfatture ai rag index` to populate the knowledge base. Agents will automatically cite normative sources such as `[1] DPR 633/72 art...`.

---

## 9. Interactive Mode

`openfatture interactive` (or `openfatture --interactive`) launches the Rich-powered TUI with menu navigation:

- Quick access to customers, invoices, and reports
- AI chat with persistent history (`~/.openfatture/ai/sessions`)
- Guided VAT suggestions directly from the menu
- Shortcuts for the most common operations without memorising CLI syntax

---

## Final Tips

- Run `uv run openfatture ...` if you rely on `uv` (recommended). With classic virtual environments, activate the venv and call `openfatture` directly.
- For debugging, add `--verbose` to commands that support it or inspect logs under `~/.openfatture/data`.
- Keep `.env` up to date and back up the database (`openfatture.db` or your PostgreSQL instance) regularly.
