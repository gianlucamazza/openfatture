# 🚀 Quick Start Guide - OpenFatture

Hands-on walkthrough to get OpenFatture running in 15 minutes.

---

## 📦 Installation

### Requirements
- Python 3.12 or later
- PEC mailbox (required to deliver invoices to SDI)
- Digital signature certificate (optional but recommended)

```bash
# Install uv (if it is not already available)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/gianlucamazza/openfatture.git
cd openfatture

# Install dependencies
uv sync

# Verify the installation
uv run python -c "from openfatture import __version__; print(f'OpenFatture v{__version__}')"
```

---

## ⚙️ Configuration

### 1. Create the `.env` File

```bash
# Copy the template
cp .env.example .env

# Edit with your favourite editor
nano .env
# or
code .env
```

### 2. Provide the Required Company Data

Update `.env` with your details:

```env
# ==========================================
# COMPANY DETAILS (REQUIRED)
# ==========================================
CEDENTE_DENOMINAZIONE=Your Company SRL
CEDENTE_PARTITA_IVA=12345678901
CEDENTE_CODICE_FISCALE=12345678901
CEDENTE_INDIRIZZO=Via Roma 123
CEDENTE_CAP=00100
CEDENTE_COMUNE=Rome
CEDENTE_PROVINCIA=RM
CEDENTE_EMAIL=info@yourcompany.it

# Tax regime
# RF01 = Ordinary regime
# RF19 = Flat-tax (5%)
CEDENTE_REGIME_FISCALE=RF19

# ==========================================
# PEC (REQUIRED for SDI delivery)
# ==========================================
PEC_ADDRESS=yourcompany@pec.it
PEC_PASSWORD=your_pec_password

# SMTP server for your PEC provider
# Aruba: smtp.pec.aruba.it
# Register: smtps.pec.register.it
PEC_SMTP_SERVER=smtp.pec.aruba.it
PEC_SMTP_PORT=465

# ==========================================
# EMAIL NOTIFICATIONS (REQUIRED)
# ==========================================
NOTIFICATION_EMAIL=admin@yourcompany.it
NOTIFICATION_ENABLED=true
LOCALE=it
```

### 3. Initialise the Database

```bash
uv run python -c "
from openfatture.storage.database.session import init_db
init_db()
print('✅ Database initialised!')
"
```

### 4. Test the PEC Configuration

Before issuing invoices, confirm the PEC credentials work:

```bash
# Using uv
uv run python -c "
from openfatture.utils.config import get_settings
from openfatture.utils.email.sender import TemplatePECSender

settings = get_settings()
sender = TemplatePECSender(settings=settings)

print('📧 Sending PEC test email...')
success, error = sender.send_test_email()

if success:
    print('✅ PEC configured correctly!')
    print(f'   Check the inbox: {settings.notification_email}')
else:
    print(f'❌ Error: {error}')
    print('   Double-check PEC credentials in .env')
"
```

If the test email lands in your inbox you are ready to go! 🎉

---

## ⚡ Enable Lightning Network Payments (Optional)

OpenFatture supports instant Bitcoin payments via the Lightning Network. This is completely optional and requires a Lightning node.

### Prerequisites

1. **LND Node**: Install Lightning Network Daemon
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install lnd

   # Or download from https://github.com/lightningnetwork/lnd/releases
   ```

2. **Channel Funding**: Open channels with inbound capacity
   ```bash
   # Start LND and create wallet
   lnd

   # Open a channel (replace with real peer)
   lncli openchannel --node_key=<peer_pubkey> --local_amt=500000 --push_amt=250000
   ```

### Quick Lightning Setup

```bash
# 1. Enable Lightning in configuration
openfatture config set lightning_enabled true

# 2. Configure LND connection
openfatture config set lightning_host localhost:10009
openfatture config set lightning_cert_path ~/.lnd/tls.cert
openfatture config set lightning_macaroon_path ~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon

# 3. Test connection
openfatture lightning status

# Expected output:
# ✅ LND Connection: OK
# 📊 Channels: 1 active, 500k sats capacity
# 💰 Balance: 250k sats local, 250k sats remote
```

### Create Your First Lightning Invoice

```bash
# Create Lightning invoice for €100
openfatture lightning invoice create --amount 100.00 --description "Quick test payment"

# Output:
# ⚡ Lightning Invoice Created
# 💰 Amount: 100.00 EUR (2,222 sats @ 45,000 EUR/BTC)
# ⏰ Expires: 2025-01-16 10:30:00
# 🔗 Payment Request: lnbc22220n1...

# Share the payment request with your customer
# They can pay instantly using any Lightning wallet!
```

**Why Lightning?**
- ⚡ **Instant settlement** (seconds vs hours for traditional payments)
- 💰 **Low fees** (0.1-1 EUR vs 2-3% for card payments)
- 🌍 **Global** (works worldwide, no currency conversion needed)
- 🔒 **Secure** (built on Bitcoin's cryptography)

See [Lightning Network Guide](../docs/LIGHTNING_NETWORK.md) for complete setup instructions.

---

## 📄 Create Your First Invoice

### 1. Add the First Customer

```python
# save as: create_customer.py
from openfatture.storage.database.models import Cliente
from openfatture.storage.database.session import get_session

# Initialise the database session
session = next(get_session())

# Create a new customer
cliente = Cliente(
    denominazione="Acme Corporation SRL",
    partita_iva="98765432100",
    codice_fiscale="98765432100",
    codice_destinatario="ABCDEFG",  # Codice SDI del cliente
    indirizzo="Via Milano 1",
    cap="20100",
    comune="Milano",
    provincia="MI",
    nazione="IT",
    email="amministrazione@acme.it",
)

session.add(cliente)
session.commit()

print(f"✅ Customer created: {cliente.denominazione} (ID: {cliente.id})")
```

Run:
```bash
uv run python create_customer.py
```

### 2. Create the First Invoice

```python
# save as: create_invoice.py
from datetime import date
from decimal import Decimal
from openfatture.storage.database.models import Cliente, Fattura, LineaFattura, StatoFattura
from openfatture.storage.database.session import get_session

session = next(get_session())

# Retrieve the customer (use the ID printed earlier)
cliente = session.query(Cliente).filter_by(id=1).first()

# Create the invoice
fattura = Fattura(
    numero="001",
    anno=2025,
    data_emissione=date.today(),
    cliente_id=cliente.id,
    cliente=cliente,
    stato=StatoFattura.DA_INVIARE,
    imponibile=Decimal("0"),
    iva=Decimal("0"),
    totale=Decimal("0"),
)

# Aggiungi linea fattura
linea = LineaFattura(
    numero_linea=1,
    descrizione="Consulenza sviluppo software",
    quantita=Decimal("10.0"),
    unita_misura="ore",
    prezzo_unitario=Decimal("50.00"),
    aliquota_iva=Decimal("22.00"),
)

# Calculate line totals
linea.imponibile = linea.quantita * linea.prezzo_unitario  # 500.00
linea.iva = linea.imponibile * (linea.aliquota_iva / 100)  # 110.00
linea.totale = linea.imponibile + linea.iva  # 610.00

# Attach the line to the invoice
fattura.linee = [linea]

# Recalculate invoice totals
fattura.imponibile = sum(l.imponibile for l in fattura.linee)
fattura.iva = sum(l.iva for l in fattura.linee)
fattura.totale = sum(l.totale for l in fattura.linee)

session.add(fattura)
session.commit()

print(f"✅ Invoice created: {fattura.numero}/{fattura.anno}")
print(f"   Customer: {fattura.cliente.denominazione}")
print(f"   Total: €{fattura.totale}")
```

Run:
```bash
uv run python create_invoice.py
```

---

## 📤 Send the Invoice to SDI

### 1. Generate the FatturaPA XML

```python
# save as: generate_xml.py
from pathlib import Path
from openfatture.storage.database.models import Fattura
from openfatture.storage.database.session import get_session
from openfatture.core.xml.generator import FatturaXMLGenerator

session = next(get_session())

# Retrieve the invoice
fattura = session.query(Fattura).filter_by(numero="001", anno=2025).first()

# Generate the XML
generator = FatturaXMLGenerator(fattura)
xml_tree = generator.generate()

# Save the XML
xml_filename = f"IT{fattura.cliente.partita_iva}_{int(fattura.numero):05d}.xml"
xml_path = Path(f"/tmp/{xml_filename}")
xml_tree.write(str(xml_path), encoding="utf-8", xml_declaration=True)

print(f"✅ XML generato: {xml_path}")
print(f"   Dimensione: {xml_path.stat().st_size} bytes")

# Display a preview (for debugging only)
print(f"\n📄 XML content:")
print(xml_tree.read_text())
```

Run:
```bash
uv run python generate_xml.py
```

### 2. Deliver the Invoice to SDI with the Professional Email Template

```python
# save as: send_to_sdi.py
from pathlib import Path
from openfatture.storage.database.models import Fattura
from openfatture.storage.database.session import get_session
from openfatture.utils.config import get_settings
from openfatture.utils.email.sender import TemplatePECSender

session = next(get_session())
settings = get_settings()

# Retrieve the invoice
fattura = session.query(Fattura).filter_by(numero="001", anno=2025).first()

# XML path generated earlier
xml_filename = f"IT{fattura.cliente.partita_iva}_{int(fattura.numero):05d}.xml"
xml_path = Path(f"/tmp/{xml_filename}")

# Send using the professional template
sender = TemplatePECSender(settings=settings)

print(f"📧 Sending invoice {fattura.numero}/{fattura.anno} to SDI...")

success, error = sender.send_invoice_to_sdi(
    fattura=fattura,
    xml_path=xml_path,
    signed=False  # Set to True if the XML was digitally signed
)

if success:
    print("✅ Invoice delivered successfully!")
    print(f"   Status: {fattura.stato.value}")
    print("   Email sent using the professional template")
    print(f"   Recipient: {settings.sdi_pec_address}")

    # The invoice status is now INVIATA
    session.commit()
else:
    print(f"❌ Delivery error: {error}")
```

Run:
```bash
uv run python send_to_sdi.py
```

**Behind the scenes:**
1. ✅ The XML is attached to the PEC email
2. ✅ OpenFatture renders a professional HTML template
3. ✅ The invoice status changes to `INVIATA`
4. ✅ The NOTIFICATION_EMAIL receives a confirmation

---

## 📬 Receive SDI Notifications Automatically

When SDI replies (typically within five days), OpenFatture sends you automatic updates via email.

### Notification Types

| Code | Description | Automatic Email |
|------|-------------|-----------------|
| **AT** | Transmission receipt | ✅ Email sent |
| **RC** | Delivery receipt | ✅ Email sent |
| **NS** | Rejection notice | ❌ Email sent with errors |
| **MC** | Failed delivery | ⚠️ Email sent |
| **NE** | Outcome notice (accepted/rejected) | ✅/❌ Email sent |

### Process Notifications Manually

If you download PEC notifications manually:

```python
# save as: process_notification.py
from pathlib import Path
from openfatture.sdi.notifiche.processor import NotificationProcessor
from openfatture.storage.database.session import get_session
from openfatture.utils.config import get_settings
from openfatture.utils.email.sender import TemplatePECSender

session = next(get_session())
settings = get_settings()

# Configure automatic emails for notifications
sender = TemplatePECSender(settings=settings)
processor = NotificationProcessor(
    db_session=session,
    email_sender=sender  # ← Enables automatic emails!
)

# Process the SDI notification file
notification_file = Path("RC_IT12345678901_00001.xml")

success, error, notification = processor.process_file(notification_file)

if success:
    print(f"✅ Notification processed: {notification.tipo_notifica.value}")
    print(f"   Invoice: {notification.fattura.numero}/{notification.fattura.anno}")
    print(f"   New status: {notification.fattura.stato.value}")
    print(f"📧 Automatic email sent to: {settings.notification_email}")
else:
    print(f"❌ Errore: {error}")
```

---

## 🎨 Customise Email Templates

### Preview the Email Before Sending

```python
# save as: preview_email.py
from pathlib import Path
from datetime import date
from decimal import Decimal
from openfatture.storage.database.models import Cliente, Fattura
from openfatture.utils.config import get_settings
from openfatture.utils.email.renderer import TemplateRenderer
from openfatture.utils.email.models import FatturaInvioContext

settings = get_settings()
renderer = TemplateRenderer(settings=settings, locale="it")

# Mock data for the preview
cliente = Cliente(denominazione="Cliente Test SRL", partita_iva="12345678901")
fattura = Fattura(
    numero="001",
    anno=2025,
    data_emissione=date.today(),
    cliente=cliente,
    totale=Decimal("610.00"),
)

# Build the template context
context = FatturaInvioContext(
    fattura=fattura,
    cedente={
        "denominazione": settings.cedente_denominazione,
        "partita_iva": settings.cedente_partita_iva,
        "indirizzo": settings.cedente_indirizzo,
        "cap": settings.cedente_cap,
        "comune": settings.cedente_comune,
    },
    destinatario="sdi01@pec.fatturapa.it",
    is_signed=False,
    xml_filename="IT12345678901_00001.xml",
)

# Genera anteprima HTML
preview_path = renderer.preview(
    template_name="sdi/invio_fattura.html",
    context=context,
    output_path=Path("/tmp/email_preview.html"),
)

print(f"📧 Anteprima generata: file://{preview_path}")
print("   Open the file in your browser to review the email")
```

### Customise Colours and Logo

In the `.env` file:

```env
EMAIL_LOGO_URL=https://tuosito.com/logo.png
EMAIL_PRIMARY_COLOR=#FF5722  # Orange
EMAIL_SECONDARY_COLOR=#212121  # Dark grey
EMAIL_FOOTER_TEXT=© 2025 My Company - VAT 12345678901
```

Restart the application to apply the changes.

---

## 🔍 Final Verification

### Final Checklist

```bash
# 1. PEC test
uv run python -c "
from openfatture.utils.config import get_settings
from openfatture.utils.email.sender import TemplatePECSender
sender = TemplatePECSender(settings=get_settings())
success, _ = sender.send_test_email()
print('✅ PEC OK' if success else '❌ PEC ERROR')
"

# 2. Database test
uv run python -c "
from openfatture.storage.database.session import get_session
from openfatture.storage.database.models import Cliente
session = next(get_session())
count = session.query(Cliente).count()
print(f'✅ Database OK ({count} customers)')
"

# 3. Configuration test
uv run python -c "
from openfatture.utils.config import get_settings
s = get_settings()
print(f'✅ Cedente: {s.cedente_denominazione}')
print(f'✅ PEC: {s.pec_address}')
print(f'✅ Notifiche: {s.notification_email}')
"
```

---

## 📚 Next Steps

Now that OpenFatture is configured:

1. **Explore the examples**: `examples/email_templates_example.py`
2. **Read the email documentation**: `docs/EMAIL_TEMPLATES.md`
3. **Configure the digital signature**: `docs/CONFIGURATION.md`
4. **Try batch operations**: import invoices from CSV
5. **Enable AI features**: configure your preferred provider for smarter suggestions

---

## 🆘 Troubleshooting

### Issue: Email Not Sent

```bash
# Check credentials
uv run python -c "
from openfatture.utils.config import get_settings
s = get_settings()
print(f'PEC: {s.pec_address}')
print(f'SMTP: {s.pec_smtp_server}:{s.pec_smtp_port}')
print(f'Password set: {\"Yes\" if s.pec_password else \"No\"}')
"
```

**Common fixes:**
- Double-check PEC username/password
- Verify the provider SMTP server details
- Ensure the firewall allows port 465
- Try sending with a PEC test account

### Issue: Database Not Initialised

```bash
# Recreate the database
uv run python -c "
from openfatture.storage.database.session import init_db
init_db()
print('✅ Database ricreato')
"
```

### Issue: Template Not Found

```bash
# Inspect available templates
ls -la openfatture/utils/email/templates/
```

---

## 💡 Tips & Best Practices

1. **Always run a test first:** call `send_test_email()` before sending real invoices.
2. **Back up the database:** `cp openfatture.db openfatture.db.backup`.
3. **Archive the XML files:** keep every invoice XML for the mandatory 10-year period.
4. **Monitor notifications:** check `NOTIFICATION_EMAIL` daily to catch SDI updates.
5. **Use digital signatures:** they improve trust and reduce rejection risk.

---

**Congratulations! 🎉 OpenFatture is now configured.**

For questions and support: [GitHub Issues](https://github.com/gianlucamazza/openfatture/issues)
