# 🚀 Quick Start Guide - OpenFatture

Guida pratica per iniziare ad usare OpenFatture in 15 minuti.

---

## 📦 Installazione

### Requisiti
- Python 3.12 o superiore
- Account PEC (per invio fatture a SDI)
- Certificato firma digitale (opzionale, ma raccomandato)

```bash
# Installa uv (se non già installato)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clona il repository
git clone https://github.com/gianlucamazza/openfatture.git
cd openfatture

# Installa dipendenze
uv sync

# Verifica installazione
uv run python -c "from openfatture import __version__; print(f'OpenFatture v{__version__}')"
```

---

## ⚙️ Configurazione

### 1. Crea il file `.env`

```bash
# Copia il template
cp .env.example .env

# Modifica con il tuo editor preferito
nano .env
# oppure
code .env
```

### 2. Configura i Dati Obbligatori

Modifica `.env` con i tuoi dati:

```env
# ==========================================
# DATI AZIENDALI (OBBLIGATORI)
# ==========================================
CEDENTE_DENOMINAZIONE=La Tua Azienda SRL
CEDENTE_PARTITA_IVA=12345678901
CEDENTE_CODICE_FISCALE=12345678901
CEDENTE_INDIRIZZO=Via Roma 123
CEDENTE_CAP=00100
CEDENTE_COMUNE=Roma
CEDENTE_PROVINCIA=RM
CEDENTE_EMAIL=info@tuaazienda.it

# Regime fiscale
# RF01 = Regime ordinario
# RF19 = Regime forfettario (5%)
CEDENTE_REGIME_FISCALE=RF19

# ==========================================
# PEC (OBBLIGATORIO per invio fatture)
# ==========================================
PEC_ADDRESS=tuaazienda@pec.it
PEC_PASSWORD=la_tua_password_pec

# SMTP del tuo provider PEC
# Aruba: smtp.pec.aruba.it
# Register: smtps.pec.register.it
PEC_SMTP_SERVER=smtp.pec.aruba.it
PEC_SMTP_PORT=465

# ==========================================
# EMAIL NOTIFICATIONS (OBBLIGATORIO)
# ==========================================
NOTIFICATION_EMAIL=admin@tuaazienda.it
NOTIFICATION_ENABLED=true
LOCALE=it
```

### 3. Inizializza il Database

```bash
uv run python -c "
from openfatture.storage.database.session import init_db
init_db()
print('✅ Database inizializzato!')
"
```

### 4. Test Configurazione PEC

Prima di creare fatture, testa che la PEC funzioni:

```bash
# Con uv
uv run python -c "
from openfatture.utils.config import get_settings
from openfatture.utils.email.sender import TemplatePECSender

settings = get_settings()
sender = TemplatePECSender(settings=settings)

print('📧 Invio email di test...')
success, error = sender.send_test_email()

if success:
    print('✅ PEC configurata correttamente!')
    print(f'   Controlla la casella: {settings.notification_email}')
else:
    print(f'❌ Errore: {error}')
    print('   Controlla le credenziali PEC in .env')
"
```

Se ricevi l'email di test, sei pronto! 🎉

---

## 📄 Prima Fattura

### 1. Crea il Primo Cliente

```python
# salva come: crea_cliente.py
from openfatture.storage.database.models import Cliente
from openfatture.storage.database.session import get_session

# Inizializza sessione database
session = next(get_session())

# Crea cliente
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

print(f"✅ Cliente creato: {cliente.denominazione} (ID: {cliente.id})")
```

Esegui:
```bash
uv run python crea_cliente.py
```

### 2. Crea la Prima Fattura

```python
# salva come: crea_fattura.py
from datetime import date
from decimal import Decimal
from openfatture.storage.database.models import Cliente, Fattura, LineaFattura, StatoFattura
from openfatture.storage.database.session import get_session

session = next(get_session())

# Recupera il cliente (usa l'ID stampato prima)
cliente = session.query(Cliente).filter_by(id=1).first()

# Crea fattura
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

# Calcola totali linea
linea.imponibile = linea.quantita * linea.prezzo_unitario  # 500.00
linea.iva = linea.imponibile * (linea.aliquota_iva / 100)  # 110.00
linea.totale = linea.imponibile + linea.iva  # 610.00

# Aggiungi linea alla fattura
fattura.linee = [linea]

# Ricalcola totali fattura
fattura.imponibile = sum(l.imponibile for l in fattura.linee)
fattura.iva = sum(l.iva for l in fattura.linee)
fattura.totale = sum(l.totale for l in fattura.linee)

session.add(fattura)
session.commit()

print(f"✅ Fattura creata: {fattura.numero}/{fattura.anno}")
print(f"   Cliente: {fattura.cliente.denominazione}")
print(f"   Totale: €{fattura.totale}")
```

Esegui:
```bash
uv run python crea_fattura.py
```

---

## 📤 Invia Fattura a SDI

### 1. Genera XML FatturaPA

```python
# salva come: genera_xml.py
from pathlib import Path
from openfatture.storage.database.models import Fattura
from openfatture.storage.database.session import get_session
from openfatture.core.xml.generator import FatturaXMLGenerator

session = next(get_session())

# Recupera fattura
fattura = session.query(Fattura).filter_by(numero="001", anno=2025).first()

# Genera XML
generator = FatturaXMLGenerator(fattura)
xml_tree = generator.generate()

# Salva XML
xml_filename = f"IT{fattura.cliente.partita_iva}_{int(fattura.numero):05d}.xml"
xml_path = Path(f"/tmp/{xml_filename}")
xml_tree.write(str(xml_path), encoding="utf-8", xml_declaration=True)

print(f"✅ XML generato: {xml_path}")
print(f"   Dimensione: {xml_path.stat().st_size} bytes")

# Mostra contenuto (per debug)
print(f"\n📄 Contenuto XML:")
print(xml_tree.read_text())
```

Esegui:
```bash
uv run python genera_xml.py
```

### 2. Invia a SDI con Email Template Professionale

```python
# salva come: invia_sdi.py
from pathlib import Path
from openfatture.storage.database.models import Fattura
from openfatture.storage.database.session import get_session
from openfatture.utils.config import get_settings
from openfatture.utils.email.sender import TemplatePECSender

session = next(get_session())
settings = get_settings()

# Recupera fattura
fattura = session.query(Fattura).filter_by(numero="001", anno=2025).first()

# Percorso XML (generato prima)
xml_filename = f"IT{fattura.cliente.partita_iva}_{int(fattura.numero):05d}.xml"
xml_path = Path(f"/tmp/{xml_filename}")

# Invia con template professionale
sender = TemplatePECSender(settings=settings)

print(f"📧 Invio fattura {fattura.numero}/{fattura.anno} a SDI...")

success, error = sender.send_invoice_to_sdi(
    fattura=fattura,
    xml_path=xml_path,
    signed=False  # True se hai firmato digitalmente il file
)

if success:
    print(f"✅ Fattura inviata con successo!")
    print(f"   Status: {fattura.stato.value}")
    print(f"   Email inviata con template professionale")
    print(f"   Destinatario: {settings.sdi_pec_address}")

    # La fattura ora è in stato INVIATA
    session.commit()
else:
    print(f"❌ Errore nell'invio: {error}")
```

Esegui:
```bash
uv run python invia_sdi.py
```

**Cosa succede dietro le quinte:**
1. ✅ XML allegato alla PEC
2. ✅ Email professionale con template HTML
3. ✅ Fattura marcata come INVIATA nel database
4. ✅ Notifica inviata a NOTIFICATION_EMAIL

---

## 📬 Ricevi Notifiche SDI Automatiche

Quando il SDI risponde (entro 5 giorni), riceverai notifiche automatiche via email!

### Tipi di Notifiche

| Codice | Descrizione | Email Automatica |
|--------|-------------|------------------|
| **AT** | Attestazione di trasmissione | ✅ Email inviata |
| **RC** | Ricevuta di consegna | ✅ Email inviata |
| **NS** | Notifica di scarto | ❌ Email inviata con errori |
| **MC** | Mancata consegna | ⚠️ Email inviata |
| **NE** | Notifica esito (accettata/rifiutata) | ✅/❌ Email inviata |

### Processa Notifiche Manualmente

Se scarichi le notifiche PEC manualmente:

```python
# salva come: processa_notifica.py
from pathlib import Path
from openfatture.sdi.notifiche.processor import NotificationProcessor
from openfatture.storage.database.session import get_session
from openfatture.utils.config import get_settings
from openfatture.utils.email.sender import TemplatePECSender

session = next(get_session())
settings = get_settings()

# Inizializza con email sender per notifiche automatiche
sender = TemplatePECSender(settings=settings)
processor = NotificationProcessor(
    db_session=session,
    email_sender=sender  # ← Abilita email automatiche!
)

# Processa file notifica SDI
notification_file = Path("RC_IT12345678901_00001.xml")

success, error, notification = processor.process_file(notification_file)

if success:
    print(f"✅ Notifica processata: {notification.tipo_notifica.value}")
    print(f"   Fattura: {notification.fattura.numero}/{notification.fattura.anno}")
    print(f"   Nuovo stato: {notification.fattura.stato.value}")
    print(f"📧 Email automatica inviata a: {settings.notification_email}")
else:
    print(f"❌ Errore: {error}")
```

---

## 🎨 Personalizza Email Templates

### Anteprima Email Prima dell'Invio

```python
# salva come: preview_email.py
from pathlib import Path
from datetime import date
from decimal import Decimal
from openfatture.storage.database.models import Cliente, Fattura
from openfatture.utils.config import get_settings
from openfatture.utils.email.renderer import TemplateRenderer
from openfatture.utils.email.models import FatturaInvioContext

settings = get_settings()
renderer = TemplateRenderer(settings=settings, locale="it")

# Mock data per preview
cliente = Cliente(denominazione="Cliente Test SRL", partita_iva="12345678901")
fattura = Fattura(
    numero="001",
    anno=2025,
    data_emissione=date.today(),
    cliente=cliente,
    totale=Decimal("610.00"),
)

# Crea context
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
print(f"   Apri il file nel browser per vedere l'email")
```

### Personalizza Colori e Logo

Nel file `.env`:

```env
EMAIL_LOGO_URL=https://tuosito.com/logo.png
EMAIL_PRIMARY_COLOR=#FF5722  # Arancione
EMAIL_SECONDARY_COLOR=#212121  # Grigio scuro
EMAIL_FOOTER_TEXT=© 2025 Mia Azienda - P.IVA 12345678901
```

Riavvia l'applicazione per applicare le modifiche.

---

## 🔍 Verifica Tutto Funzioni

### Checklist Finale

```bash
# 1. Test PEC
uv run python -c "
from openfatture.utils.config import get_settings
from openfatture.utils.email.sender import TemplatePECSender
sender = TemplatePECSender(settings=get_settings())
success, _ = sender.send_test_email()
print('✅ PEC OK' if success else '❌ PEC ERROR')
"

# 2. Test Database
uv run python -c "
from openfatture.storage.database.session import get_session
from openfatture.storage.database.models import Cliente
session = next(get_session())
count = session.query(Cliente).count()
print(f'✅ Database OK ({count} clienti)')
"

# 3. Test Configurazione
uv run python -c "
from openfatture.utils.config import get_settings
s = get_settings()
print(f'✅ Cedente: {s.cedente_denominazione}')
print(f'✅ PEC: {s.pec_address}')
print(f'✅ Notifiche: {s.notification_email}')
"
```

---

## 📚 Prossimi Passi

Ora che hai configurato OpenFatture:

1. **Esplora gli esempi**: `examples/email_templates_example.py`
2. **Leggi la documentazione completa**: `docs/EMAIL_TEMPLATES.md`
3. **Configura firma digitale**: `docs/CONFIGURATION.md`
4. **Operazioni batch**: Importa CSV con fatture multiple
5. **Integra AI**: Configura LangChain per suggerimenti intelligenti

---

## 🆘 Troubleshooting

### Problema: Email non inviata

```bash
# Verifica credenziali
uv run python -c "
from openfatture.utils.config import get_settings
s = get_settings()
print(f'PEC: {s.pec_address}')
print(f'SMTP: {s.pec_smtp_server}:{s.pec_smtp_port}')
print(f'Password impostata: {\"Sì\" if s.pec_password else \"No\"}')
"
```

**Soluzioni comuni:**
- Controlla username/password PEC
- Verifica SMTP server del provider
- Controlla firewall (porta 465)
- Prova con PEC di test

### Problema: Database non inizializzato

```bash
# Reinizializza database
uv run python -c "
from openfatture.storage.database.session import init_db
init_db()
print('✅ Database ricreato')
"
```

### Problema: Template non trovato

```bash
# Verifica templates
ls -la openfatture/utils/email/templates/
```

---

## 💡 Tips & Best Practices

1. **Testa sempre prima**: Usa `send_test_email()` prima di inviare fatture vere
2. **Backup database**: `cp openfatture.db openfatture.db.backup`
3. **Salva XML**: Conserva sempre le fatture XML per 10 anni (obbligo di legge)
4. **Monitora notifiche**: Controlla NOTIFICATION_EMAIL quotidianamente
5. **Usa firma digitale**: Aumenta la sicurezza e riduce i rischi di scarto

---

**Congratulazioni! 🎉 Hai configurato OpenFatture correttamente!**

Per domande e supporto: [GitHub Issues](https://github.com/gianlucamazza/openfatture/issues)
