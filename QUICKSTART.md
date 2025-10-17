# OpenFatture - Quick Start Guide

Get started with OpenFatture in 5 minutes!

## Installation

### Prerequisites
- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) (recommended package manager)
- PEC account (for sending invoices)

### Install OpenFatture

```bash
# Clone the repository
git clone https://github.com/venerelabs/openfatture.git
cd openfatture

# Install dependencies with uv
uv sync --all-extras

# Or manage the virtual environment manually with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

## Initial Setup

Run the setup wizard:

```bash
uv run openfatture init
```

This will:
- Create the database
- Set up data directories
- Guide you through configuration (company data, PEC settings)

### Enable AI & Knowledge Base (Optional but Recommended)

If vuoi sfruttare gli agenti AI con citazioni normative:

```bash
# 1. Imposta le credenziali per il provider di embedding (es. OpenAI)
export OPENAI_API_KEY=sk-...

# 2. Popola la knowledge base con le fonti incluse nel manifest
uv run openfatture ai rag index

# 3. Verifica stato e documenti indicizzati
uv run openfatture ai rag status
```

Puoi esplorare rapidamente il contenuto indicizzato con `uv run openfatture ai rag search "reverse charge edilizia"`.

## Basic Workflow

### 1. Add Your First Client

```bash
# Interactive mode (recommended for first time)
uv run openfatture cliente add "Acme Corp" --interactive

# Or quick mode
uv run openfatture cliente add "Acme Corp" \
  --piva 12345678901 \
  --sdi ABC1234
```

### 2. Create an Invoice

```bash
# Interactive wizard
uv run openfatture fattura crea

# Follow the prompts:
# - Select client
# - Add line items (description, quantity, price, VAT rate)
# - Apply ritenuta d'acconto if needed
# - Add bollo if required
```

### 3. Generate XML

```bash
# Generate FatturaPA XML
uv run openfatture fattura xml 1

# Output will be saved to ~/.openfatture/archivio/xml/
```

### 4. Send to SDI

```bash
# Test PEC configuration first
uv run openfatture pec test

# Send invoice
uv run openfatture fattura invia 1
```

## Common Commands

### Client Management
```bash
# List all clients
openfatture cliente list

# View client details
openfatture cliente show 1

# Delete client
openfatture cliente delete 1
```

### Invoice Management
```bash
# List invoices
openfatture fattura list

# Filter by year
openfatture fattura list --anno 2025

# Filter by status
openfatture fattura list --stato inviata

# View invoice details
openfatture fattura show 1

# Delete draft invoice
openfatture fattura delete 1
```

### Reports
```bash
# VAT report for Q1
openfatture report iva --trimestre Q1

# Client revenue report
openfatture report clienti --anno 2025

# Upcoming due dates
openfatture report scadenze
```

### Configuration
```bash
# View current configuration
openfatture config show

# Set a value
openfatture config --set pec.address yourcompany@pec.it

# Reload from .env
openfatture config reload
```

## Tips & Tricks

### 1. Use Shell Completion

```bash
# For Bash
openfatture --install-completion bash

# For Zsh
openfatture --install-completion zsh
```

### 2. Edit .env Directly

For complex configuration, edit the `.env` file directly:

```bash
nano .env
```

### 3. Keep Backups

Your database is at `./openfatture.db` by default. Back it up regularly!

```bash
cp openfatture.db backups/openfatture-$(date +%Y%m%d).db
```

### 4. XSD Validation

For strict validation, download the official XSD schema:

```bash
mkdir -p ~/.openfatture/data/schemas
cd ~/.openfatture/data/schemas
wget https://www.fatturapa.gov.it/export/documenti/fatturapa/v1.2.2/Schema_del_file_xml_FatturaPA_v1.2.2.xsd
```

### 5. Test Mode

```bash
DATABASE_URL=sqlite:///./test.db openfatture init
```

### 6. Web UI Alternative

Preferisci un'interfaccia grafica? OpenFatture include una moderna Web UI basata su Streamlit:

```bash
# Installa dipendenze web
uv sync --extra web

# Avvia la Web UI
uv run streamlit run openfatture/web/app.py

# Si aprirà automaticamente nel browser su http://localhost:8501
```

La Web UI offre:
- 📊 Dashboard real-time con KPI e grafici
- 🧾 Gestione fatture visuale
- 🤖 AI Assistant integrato
- 💰 Monitoraggio pagamenti
- ⚙️ Configurazione sistema

**Nota:** CLI e Web UI condividono lo stesso database. Puoi usarle insieme!

Per la guida completa: `docs/WEB_UI_GUIDE.md`

## Troubleshooting

### "PEC authentication failed"
- Check your PEC credentials in `.env`
- Verify SMTP server and port
- Test with: `openfatture pec test`

### "Client not found"
- List clients: `openfatture cliente list`
- Use the correct client ID

### "XML validation failed"
- Download XSD schema (see Tips #4)
- Check for missing required fields
- Or skip validation: `openfatture fattura xml 1 --no-validate`

## Next Steps

1. 📖 Read the full [README](README.md)
2. 🤝 Check [CONTRIBUTING](CONTRIBUTING.md) to help improve OpenFatture
3. 💬 Join [GitHub Discussions](https://github.com/venerelabs/openfatture/discussions)
4. 🐛 Report issues at [GitHub Issues](https://github.com/venerelabs/openfatture/issues)

## Example: Complete Invoice Flow

```bash
# 1. Setup (one time)
openfatture init

# 2. Add client
openfatture cliente add "Acme Corp" \
  --piva 12345678901 \
  --sdi ABC1234 \
  --pec acme@pec.it

# 3. Create invoice
openfatture fattura crea
# Interactive wizard will guide you

# 4. Generate and send
openfatture fattura xml 1      # Generate XML
openfatture pec test          # Test PEC (optional)
openfatture fattura invia 1   # Send to SDI

# 5. Check status
openfatture fattura show 1

# 6. Generate report
openfatture report iva --trimestre Q1
```

Happy invoicing! 🧾
