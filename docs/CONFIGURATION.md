# Configuration Reference

Comprehensive reference for every OpenFatture configuration option.

---

## Overview

OpenFatture relies on environment variables managed through `.env` files and loaded with **Pydantic Settings**.

**Key files**
- `.env` – Local configuration (never commit this file)
- `.env.example` – Template with sample values

**Precedence order**
1. System environment variables
2. Values defined in `.env`
3. Defaults defined in code

---

## Database

### `DATABASE_URL`

**Description:** Database connection string
**Type:** String
**Default:** `sqlite:///./openfatture.db`

```env
# SQLite (development)
DATABASE_URL=sqlite:///./openfatture.db

# PostgreSQL (production)
DATABASE_URL=postgresql://user:password@localhost:5432/openfatture

# PostgreSQL with SSL
DATABASE_URL=postgresql://user:password@host:5432/db?sslmode=require
```

**Notes**
- SQLite is fine for development and single-user installs
- PostgreSQL is recommended for production or multi-user scenarios
- The database is created automatically if it does not exist

**Troubleshooting**
```bash
uv run python -c "
from openfatture.storage.database.session import get_session
session = next(get_session())
print('✅ Database connection OK')
"
```

---

## Company Data (Cedente Prestatore)

These details appear on every invoice and in SDI submissions.

### `CEDENTE_DENOMINAZIONE`

**Description:** Company name or full name
**Type:** String
**Required:** ✅

```env
CEDENTE_DENOMINAZIONE=Mario Rossi
# or
CEDENTE_DENOMINAZIONE=Acme Consulting SRL
```

**Notes**
- Sole traders: full name
- Companies: registered business name
- Shown in XML files and outbound emails

---

### `CEDENTE_PARTITA_IVA`

**Description:** VAT number (11 digits)
**Type:** String (11 characters)
**Required:** ✅

```env
CEDENTE_PARTITA_IVA=12345678901
```

**Validation**
- Must contain exactly 11 digits
- Digits only
- Basic checksum not enforced (extend if needed)

**Notes**
- Primary identifier for SDI
- Required for electronic invoicing

---

### `CEDENTE_CODICE_FISCALE`

**Description:** Italian tax code
**Type:** String (16 alphanumeric characters)
**Required:** ✅

```env
# Individual
CEDENTE_CODICE_FISCALE=RSSMRA80A01H501U

# Company (usually same as VAT number)
CEDENTE_CODICE_FISCALE=12345678901
```

**Notes**
- Individuals: 16-character codice fiscale
- Companies: generally matches the VAT number
- Mandatory for FatturaPA

---

### `CEDENTE_REGIME_FISCALE`

**Description:** Tax regime code
**Type:** String
**Default:** `RF19`

```env
# Flat-tax regime (5–15%)
CEDENTE_REGIME_FISCALE=RF19

# Ordinary regime
CEDENTE_REGIME_FISCALE=RF01

# Simplified regime
CEDENTE_REGIME_FISCALE=RF02
```

| Code | Description |
|------|-------------|
| RF01 | Ordinary |
| RF02 | Minimum taxpayers |
| RF04 | Agriculture and related activities |
| RF05 | Salt and tobacco retail |
| RF06 | Match sales |
| RF07 | Publishing |
| RF08 | Public telephony services |
| RF09 | Transport document resale |
| RF10 | Entertainment and gaming |
| RF11 | Travel agencies |
| RF12 | Agritourism |
| RF13 | Door-to-door sales |
| RF14 | Second-hand goods / art objects |
| RF15 | Auction agencies |
| RF16 | Cash accounting – public administration |
| RF17 | Cash accounting – other |
| RF18 | Other |
| RF19 | **Forfait regime** (most common) |

---

### `CEDENTE_INDIRIZZO`

**Description:** Full street address
**Type:** String
**Required:** ✅

```env
CEDENTE_INDIRIZZO=Via Giuseppe Garibaldi 42
```

---

### `CEDENTE_CAP`

**Description:** Postal code (CAP)
**Type:** String (5 digits)
**Required:** ✅

```env
CEDENTE_CAP=00100
```

---

### `CEDENTE_COMUNE`

**Description:** Municipality name
**Type:** String
**Required:** ✅

```env
CEDENTE_COMUNE=Roma
```

**Notes**
- Use the official full name (e.g. `Reggio Emilia`, not `Reggio E.`)

---

### `CEDENTE_PROVINCIA`

**Description:** Province code (2 letters)
**Type:** String (2 characters)
**Required:** ✅

```env
CEDENTE_PROVINCIA=RM
```

**Common province codes**
- RM = Roma
- MI = Milano
- TO = Torino
- NA = Napoli
- FI = Firenze
- BO = Bologna

[Full province list](https://it.wikipedia.org/wiki/Province_d%27Italia)

---

### `CEDENTE_NAZIONE`

**Description:** ISO 3166-1 alpha-2 country code
**Type:** String (2 characters)
**Default:** `IT`

```env
CEDENTE_NAZIONE=IT
```

**Notes**
- Italian entities use `IT`
- Change only for foreign companies

---

### `CEDENTE_TELEFONO`

**Description:** Contact phone number (optional)
**Type:** String (optional)
**Default:** None

```env
CEDENTE_TELEFONO=+39 06 12345678
CEDENTE_TELEFONO=06 12345678
CEDENTE_TELEFONO=3331234567
```

**Notes**
- Accepts any readable format
- Recommended for client communications

---

### `CEDENTE_EMAIL`

**Description:** Company email (optional)
**Type:** String (optional)
**Default:** None

```env
CEDENTE_EMAIL=info@yourcompany.it
```

**Notes**
- Separate from the PEC mailbox
- Used for general communications
- May appear on invoice PDFs

---

## PEC Configuration

PEC (certified email) is required to deliver invoices to SDI.

### `PEC_ADDRESS`

**Description:** PEC mailbox
**Type:** String (email)
**Required:** ✅

```env
PEC_ADDRESS=yourcompany@pec.it
```

**Notes**
- Must be valid and active
- Used as the sender for SDI
- Verify periodically with your provider

---

### `PEC_PASSWORD`

**Description:** PEC mailbox password
**Type:** String
**Required:** ✅

```env
PEC_PASSWORD=your_secure_password
```

**Security checklist**
- ⚠️ Never commit `.env` to Git
- Use a strong password
- Rotate regularly
- Prefer environment variables or vaults in production

---

### `PEC_SMTP_SERVER`

**Description:** SMTP hostname for the PEC provider
**Type:** String (hostname)
**Default:** `smtp.pec.it`

```env
# Aruba
PEC_SMTP_SERVER=smtp.pec.aruba.it

# Register
PEC_SMTP_SERVER=smtps.pec.register.it

# Legalmail
PEC_SMTP_SERVER=smtp.legalmail.it

# PosteCert
PEC_SMTP_SERVER=smtp.postecert.it

# InfoCert
PEC_SMTP_SERVER=smtp.pec.infocert.it

# Actalis
PEC_SMTP_SERVER=smtp.pec.actalis.it
```

**Notes**
- Hostname depends on the provider
- Consult your provider’s documentation
- Typically uses SSL/TLS on port 465

---

### `PEC_SMTP_PORT`

**Description:** SMTP port
**Type:** Integer
**Default:** `465`

```env
# SSL/TLS (recommended)
PEC_SMTP_PORT=465

# STARTTLS (less common for PEC)
PEC_SMTP_PORT=587
```

**Notes**
- Port 465 is standard for PEC
- Always use encrypted connections

---

### `SDI_PEC_ADDRESS`

**Description:** SDI intake mailbox
**Type:** String (email)
**Default:** `sdi01@pec.fatturapa.it`

```env
SDI_PEC_ADDRESS=sdi01@pec.fatturapa.it
```

**Notes**
- Official SDI address
- Rarely changes
- Do not modify unless explicitly instructed by Agenzia delle Entrate

---

## Email Templates & Branding

Customise the automatic emails sent by OpenFatture.

### `EMAIL_LOGO_URL`

**Description:** Public URL for the company logo
**Type:** String (URL, optional)
**Default:** None

```env
EMAIL_LOGO_URL=https://cdn.yourcompany.it/logo.png
EMAIL_LOGO_URL=https://your-company.com/assets/logo.svg
```

**Notes**
- Must be reachable via HTTPS
- PNG or SVG recommended
- Displayed in the email header

---

### `EMAIL_PRIMARY_COLOR`

**Description:** Primary brand colour (hex)
**Type:** String (HEX, optional)
**Default:** `#1976D2`

```env
EMAIL_PRIMARY_COLOR=#1976D2  # Blue
EMAIL_PRIMARY_COLOR=#FF5722  # Orange
EMAIL_PRIMARY_COLOR=#0E1116  # Near black
```

**Notes**
- Include the `#`
- High-contrast colours work best
- Applied to headers and buttons

---

### `EMAIL_SECONDARY_COLOR`

**Description:** Secondary colour (hex)
**Type:** String (HEX, optional)
**Default:** `#424242`

```env
EMAIL_SECONDARY_COLOR=#424242  # Dark grey
EMAIL_SECONDARY_COLOR=#FFFFFF  # White
EMAIL_SECONDARY_COLOR=#1E1E1E  # Charcoal
```

**Notes**
- Used for footers and links
- Keep a readable contrast with the primary colour

---

### `EMAIL_FOOTER_TEXT`

**Description:** Custom footer text
**Type:** String (optional)
**Default:** None (falls back to company details)

```env
EMAIL_FOOTER_TEXT=© 2025 Acme SRL - VAT 12345678901 - All rights reserved
```

**Notes**
- Plain text only (no HTML)
- Appears on every email
- Defaults to cedente information when omitted

---

### `NOTIFICATION_EMAIL`

**Description:** Inbox for SDI and automation alerts
**Type:** String (email)
**Required:** ✅ (for email features)

```env
NOTIFICATION_EMAIL=admin@yourcompany.it
```

**Receives**
- SDI transmission receipts (AT)
- Delivery receipts (RC)
- Rejection notices (NS)
- Failed deliveries (MC)
- Customer outcomes (NE)
- Batch operation summaries
- PEC configuration tests

**Notes**
- May differ from the PEC mailbox
- Monitor daily (or route to a shared mailbox)
- Mailing lists are supported

---

### `NOTIFICATION_ENABLED`

**Description:** Toggle email notifications
**Type:** Boolean
**Default:** `true`

```env
NOTIFICATION_ENABLED=true   # Enable notifications
NOTIFICATION_ENABLED=false  # Disable temporarily
```

**Notes**
- Even when disabled, notifications are still processed (emails are just skipped)
- Keep enabled in production

---

### `LOCALE`

**Description:** Locale for emails and CLI labels
**Type:** String
**Default:** `it`

```env
LOCALE=it  # Italian
LOCALE=en  # English
```

**Notes**
- Switches the language of all email templates
- Fully translated for Italian and English
- Add more locales via `openfatture/utils/email/i18n/*.json`

---

## Digital Signature

Optional configuration to sign XML invoices digitally.

### `SIGNATURE_CERTIFICATE_PATH`

**Description:** Path to the digital certificate
**Type:** Path (optional)
**Default:** None

```env
SIGNATURE_CERTIFICATE_PATH=/path/to/certificate.p12
SIGNATURE_CERTIFICATE_PATH=/home/user/.openfatture/cert.pfx
```

**Supported formats**
- `.p12` / `.pfx` (PKCS#12)
- `.pem`

**Notes**
- Optional but strongly recommended
- Reduces SDI rejections
- Improves legal enforceability

---

### `SIGNATURE_CERTIFICATE_PASSWORD`

**Description:** Certificate password
**Type:** String (optional)
**Default:** None

```env
SIGNATURE_CERTIFICATE_PASSWORD=certificate_password
```

**Security**
- ⚠️ Never commit secrets to Git
- Use a strong password
- Prefer vault/secret managers in production

---

## AI Configuration

Enable LLM features for smart suggestions and assistants.

### `AI_PROVIDER`

**Description:** LLM provider
**Type:** String
**Default:** `openai`

```env
AI_PROVIDER=openai     # OpenAI (GPT-4, GPT-3.5)
AI_PROVIDER=anthropic  # Anthropic (Claude)
AI_PROVIDER=ollama     # Ollama (local models)
```

---

### `AI_MODEL`

**Description:** Model name
**Type:** String
**Default:** `gpt-4-turbo-preview`

```env
# OpenAI
AI_MODEL=gpt-4-turbo-preview
AI_MODEL=gpt-3.5-turbo

# Anthropic
AI_MODEL=claude-3-5-sonnet-20241022
AI_MODEL=claude-3-opus-20240229

# Ollama (local)
AI_MODEL=llama3
AI_MODEL=mistral
```

---

### `AI_API_KEY`

**Description:** Provider API key
**Type:** String (optional)
**Default:** None

```env
# OpenAI
AI_API_KEY=sk-proj-...

# Anthropic
AI_API_KEY=sk-ant-...
```

**Notes**
- Not required for local Ollama deployments
- ⚠️ Never commit the key to Git repositories

---

### `AI_BASE_URL`

**Description:** Custom API base URL
**Type:** String (URL, optional)
**Default:** None

```env
# Local Ollama
AI_BASE_URL=http://localhost:11434

# OpenAI proxy
AI_BASE_URL=https://api.openai-proxy.com/v1
```

---

### `AI_TEMPERATURE`

**Description:** LLM temperature (creativity)
**Type:** Float (0.0 – 2.0)
**Default:** `0.7`

```env
AI_TEMPERATURE=0.0  # Deterministic
AI_TEMPERATURE=0.7  # Balanced
AI_TEMPERATURE=1.5  # Creative
```

---

### `AI_MAX_TOKENS`

**Description:** Maximum response length (tokens)
**Type:** Integer
**Default:** `2000`

```env
AI_MAX_TOKENS=1000   # Short answers
AI_MAX_TOKENS=4000   # Long answers
```

---

### `AI_TIMEOUT`

**Description:** Request timeout (seconds)
**Type:** Integer
**Default:** `60`

```env
AI_TIMEOUT=30
AI_TIMEOUT=90
```

---

### `AI_CACHE_ENABLED`

**Description:** Enable in-memory cache for responses
**Type:** Boolean
**Default:** `true`

```env
AI_CACHE_ENABLED=true
AI_CACHE_ENABLED=false
```

**Notes**
- Speeds up repeated prompts
- Helps reduce API costs

---

### `AI_CACHE_TTL_SECONDS`

**Description:** Cache lifetime (seconds)
**Type:** Integer
**Default:** `900` (15 minutes)

```env
AI_CACHE_TTL_SECONDS=300   # 5 minutes
AI_CACHE_TTL_SECONDS=3600  # 1 hour
```

---

### `AI_COST_ALERT_THRESHOLD`

**Description:** Cost threshold (EUR) before warnings
**Type:** Float
**Default:** `25.0`

```env
AI_COST_ALERT_THRESHOLD=10.0
AI_COST_ALERT_THRESHOLD=50.0
```

---

### `AI_LOG_LEVEL`

**Description:** Logging level for AI modules
**Type:** String
**Default:** `INFO`

```env
AI_LOG_LEVEL=ERROR
AI_LOG_LEVEL=WARNING
AI_LOG_LEVEL=INFO
AI_LOG_LEVEL=DEBUG
```

---

### `AI_LOG_PROMPTS`

**Description:** Log prompts and responses (debug)
**Type:** Boolean
**Default:** `false`

```env
AI_LOG_PROMPTS=true   # Log prompts and completions
AI_LOG_PROMPTS=false  # (default) No prompt logging
```

**Notes**
- ⚠️ May expose sensitive data
- Enable only when debugging

---

### `AI_SESSION_DIR`

**Description:** Folder for chat history
**Type:** Path
**Default:** `~/.openfatture/ai/sessions`

```env
AI_SESSION_DIR=/var/lib/openfatture/ai/sessions
```

---

### `AI_MAX_SESSION_FILES`

**Description:** Maximum number of saved sessions
**Type:** Integer
**Default:** `100`

```env
AI_MAX_SESSION_FILES=50   # Keep the latest 50 sessions
AI_MAX_SESSION_FILES=200  # Keep the latest 200 sessions
```

**Notes**
- Old sessions are deleted when the limit is reached
- Set to 0 to disable automatic cleanup

---

### `AI_CHAT_MAX_MESSAGES`

**Description:** Max chat messages per session
**Type:** Integer
**Default:** `100`

```env
AI_CHAT_MAX_MESSAGES=50    # Short sessions
AI_CHAT_MAX_MESSAGES=200   # Longer sessions
```

**Notes**
- Controls conversation length to manage costs
- Oldest messages are pruned beyond the limit
- System messages are excluded from the count

---

### `AI_CHAT_MAX_TOKENS`

**Description:** Max accumulated tokens per session
**Type:** Integer
**Default:** `8000`

```env
AI_CHAT_MAX_TOKENS=4000    # Short sessions
AI_CHAT_MAX_TOKENS=16000   # Long sessions
```

**Notes**
- Includes both input and output tokens
- Old messages are removed automatically when the limit is reached

---

## AI Tools & Function Calling

Fine-tune the tool-calling behaviour for agents.

### `AI_TOOLS_ENABLED`

**Description:** Enable function calling
**Type:** Boolean
**Default:** `true`

```env
AI_TOOLS_ENABLED=true   # Enable tools
AI_TOOLS_ENABLED=false  # Conversation only
```

**Notes**
- Enables invoice/client search from the chat assistant
- Requires the database to be initialised

---

### `AI_ENABLED_TOOLS`

**Description:** Comma-separated list of enabled tools
**Type:** String
**Default:** All tools

```env
# Only invoice-related tools
AI_ENABLED_TOOLS=search_invoices,get_invoice_details,get_invoice_stats

# All tools
AI_ENABLED_TOOLS=search_invoices,get_invoice_details,get_invoice_stats,search_clients,get_client_details,get_client_stats
```

**Available tools**
- `search_invoices`
- `get_invoice_details`
- `get_invoice_stats`
- `search_clients`
- `get_client_details`
- `get_client_stats`

---

### `AI_TOOLS_REQUIRE_CONFIRMATION`

**Description:** Ask for confirmation before running tools
**Type:** Boolean
**Default:** `true`

```env
AI_TOOLS_REQUIRE_CONFIRMATION=true   # Ask before executing tools
AI_TOOLS_REQUIRE_CONFIRMATION=false  # Execute immediately
```

**Notes**
- Current tools are read-only, so confirmation is optional
- Keep enabled if you plan to add write operations later

---

## Paths & Directories

Override default storage locations when required.

### `DATA_DIR`

**Description:** Application data directory
**Type:** Path
**Default:** `~/.openfatture/data`

```env
DATA_DIR=/var/lib/openfatture/data
```

---

### `ARCHIVIO_DIR`

**Description:** Archive for invoices (XML/PDF)
**Type:** Path
**Default:** `~/.openfatture/archivio`

```env
ARCHIVIO_DIR=/mnt/storage/invoices
```

**Notes**
- Preserve invoices for 10 years (legal requirement)
- Back up regularly

---

### `CERTIFICATES_DIR`

**Description:** Certificate directory
**Type:** Path
**Default:** `~/.openfatture/certificates`

```env
CERTIFICATES_DIR=/etc/openfatture/certs
```

---

## Best Practices

### Security

1. **Never commit `.env` to Git**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Use environment variables in production**
   ```bash
   export PEC_PASSWORD=secret
   ```

3. **Rotate credentials regularly**

4. **Adopt digital signatures for invoices**

### Performance

1. **Prefer PostgreSQL in production**
   ```env
   DATABASE_URL=postgresql://...
   ```

2. **Plan for AI response caching** (coming soon)

### Backup

1. **Database snapshots**
   ```bash
   cp openfatture.db backup_$(date +%Y%m%d).db
   ```

2. **Invoice archive**
   - Mandatory 10-year retention
   - Store off-site whenever possible

---

## Troubleshooting

### Inspect Effective Configuration

```bash
uv run python -c "
from openfatture.utils.config import get_settings
s = get_settings()

print('=== CONFIGURATION ===')
print(f'Cedente: {s.cedente_denominazione}')
print(f'VAT: {s.cedente_partita_iva}')
print(f'PEC: {s.pec_address}')
print(f'SMTP: {s.pec_smtp_server}:{s.pec_smtp_port}')
print(f'Notifications: {s.notification_email}')
print(f'Database: {s.database_url}')
print(f'Locale: {s.locale}')
"
```

### Test PEC Delivery

```bash
uv run python -c "
from openfatture.utils.config import get_settings
from openfatture.utils.email.sender import TemplatePECSender

sender = TemplatePECSender(settings=get_settings())
success, error = sender.send_test_email()

if success:
    print('✅ PEC OK')
else:
    print(f'❌ ERROR: {error}')
"
```

---

## Payment Tracking

### `PAYMENT_EVENT_LISTENERS`

**Description:** Optional comma-separated list of dotted paths to callables that will receive `PaymentEvent` instances in addition to the built-in audit logger.
**Type:** String (comma-separated dotted paths)

```env
PAYMENT_EVENT_LISTENERS=analytics.events.track_payment,monitoring.alerts.on_payment_event
```

**Notes**
- Handlers are imported dynamically; ensure they are available on `PYTHONPATH`
- Every event is sent to the default audit logger plus the custom listeners
- Leave empty or unset to disable additional listeners

---

## References

- [FatturaPA Technical Specifications](https://www.fatturapa.gov.it/it/norme-e-regole/documentazione-fattura-elettronica/formato-fatturapa/)
- [SDI – Sistema di Interscambio](https://www.fatturapa.gov.it/it/sdi/)
- [Tax Regime Codes](https://www.agenziaentrate.gov.it/)
